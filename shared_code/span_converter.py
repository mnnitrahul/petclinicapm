import base64
import gzip
import json
import os
import boto3
import requests
from datetime import datetime

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span, Status
from opentelemetry.proto.common.v1.common_pb2 import KeyValue, AnyValue
from opentelemetry.proto.resource.v1.resource_pb2 import Resource


def otel_span_converter(event, context):
    print('Starting Azure to X-Ray OTLP conversion')
    
    # Decode and decompress CloudWatch Logs data
    compressed = base64.b64decode(event['awslogs']['data'])
    decompressed = gzip.decompress(compressed)
    log_data = json.loads(decompressed)
    
    # Process each span independently - no batch dependencies
    spans_by_service = {}
    
    for log_event in log_data['logEvents']:
        try:
            azure_data = json.loads(log_event['message'])
            
            # Debug logging for each span
            operation_id = azure_data.get('OperationId', '')
            span_id = azure_data.get('Id', '')
            parent_id = azure_data.get('ParentId', '')
            cloud_role = azure_data.get('AppRoleName', '')
            span_name = azure_data.get('Name', '')
            span_type = azure_data.get('Type', '')
            dependency_type = azure_data.get('DependencyType', '')
            
            # Compute transformed values for logging
            target = azure_data.get('Target', '')
            url = azure_data.get('Url') or azure_data.get('Data') or target
            result_code = azure_data.get('ResultCode', '')
            
            # Build original fields dict
            original = {
                'OperationId': operation_id,
                'Id': span_id,
                'ParentId': parent_id,
                'AppRoleName': cloud_role,
                'Type': span_type,
                'DependencyType': dependency_type,
                'Name': span_name,
                'Target': target,
                'Url': azure_data.get('Url', ''),
                'Data': azure_data.get('Data', ''),
                'ResultCode': result_code
            }
            
            # Build transformed fields dict
            transformed = {
                'aws.local.service': cloud_role or 'unknown-service',
                'aws.local.environment': 'generic:default',
                'aws.local.operation': span_name,
                'PlatformType': 'Generic',
                'kind': 'SERVER' if span_type == 'AppRequests' else ('INTERNAL' if dependency_type == 'InProc' else 'CLIENT'),
                'aws.span.kind': 'SERVER' if span_type == 'AppRequests' else ('INTERNAL' if dependency_type == 'InProc' else 'CLIENT'),
                'http.status_code': int(result_code) if result_code.isdigit() else None,
                'http.response.status_code': int(result_code) if result_code.isdigit() else None,
                'http.url': url
            }
            
            # Add remote fields for CLIENT spans
            if span_type == 'AppDependencies' and dependency_type != 'InProc':
                remote_service = derive_remote_service(dependency_type, target, span_name)
                resource_type, resource_id = get_remote_resource(dependency_type, target, azure_data)
                transformed['aws.remote.service'] = remote_service
                transformed['aws.remote.operation'] = span_name
                transformed['aws.remote.environment'] = 'generic:default'
                transformed['aws.remote.resource.type'] = resource_type
                transformed['aws.remote.resource.identifier'] = resource_id
            
            # Convert span independently (no lookups to other spans)
            span = convert_to_otlp_span(azure_data)
            
            # Flat JSON for CloudWatch Log Insights compatibility
            flat_log = {
                'log_type': 'SpanConversion',
                'original_OperationId': original['OperationId'],
                'original_Id': original['Id'],
                'original_ParentId': original['ParentId'],
                'original_AppRoleName': original['AppRoleName'],
                'original_Type': original['Type'],
                'original_DependencyType': original['DependencyType'],
                'original_Name': original['Name'],
                'original_Target': original['Target'],
                'original_Url': original['Url'],
                'original_Data': original['Data'],
                'original_ResultCode': original['ResultCode'],
                'transformed_aws_local_service': transformed['aws.local.service'],
                'transformed_aws_local_environment': transformed['aws.local.environment'],
                'transformed_aws_local_operation': transformed['aws.local.operation'],
                'transformed_PlatformType': transformed['PlatformType'],
                'transformed_aws_span_kind': transformed['aws.span.kind'],
                'transformed_http_status_code': transformed['http.status_code'],
                'transformed_http_response_status_code': transformed['http.response.status_code'],
                'transformed_http_url': transformed['http.url'],
                'transformed_aws_remote_service': transformed.get('aws.remote.service'),
                'transformed_aws_remote_operation': transformed.get('aws.remote.operation'),
                'transformed_aws_remote_environment': transformed.get('aws.remote.environment'),
                'transformed_aws_remote_resource_type': transformed.get('aws.remote.resource.type'),
                'transformed_aws_remote_resource_identifier': transformed.get('aws.remote.resource.identifier'),
                # Final span fields
                'final_trace_id': span.trace_id.hex() if span else None,
                'final_span_id': span.span_id.hex() if span else None,
                'final_parent_span_id': span.parent_span_id.hex() if span and span.parent_span_id else None,
                'final_name': span.name if span else None,
                'final_kind': span.kind if span else None,
                'final_start_time_unix_nano': span.start_time_unix_nano if span else None,
                'final_end_time_unix_nano': span.end_time_unix_nano if span else None,
                'final_status_code': span.status.code if span else None,
                'final_attributes': {kv.key: (kv.value.string_value if kv.value.HasField('string_value') else kv.value.int_value) for kv in span.attributes} if span else None
            }
            print(json.dumps(flat_log))
            
            if span:
                service_name = cloud_role or 'unknown-service'
                if service_name not in spans_by_service:
                    spans_by_service[service_name] = {
                        'azure_data': azure_data,
                        'spans': []
                    }
                spans_by_service[service_name]['spans'].append(span)
        except Exception as e:
            print(f'Error processing log event: {e}')
    
    # Build and send protobuf payload
    if spans_by_service:
        resource_spans = build_resource_spans(spans_by_service)
        send_to_xray_otlp(resource_spans)
    
    total_spans = sum(len(s['spans']) for s in spans_by_service.values())
    print(f'Processed {total_spans} spans')
    return {'statusCode': 200}


def convert_to_otlp_span(azure_data):
    """Convert Azure telemetry to OTLP Span protobuf - self-contained, no batch dependencies."""
    
    operation_id = azure_data.get('OperationId', '')
    span_id = azure_data.get('Id', '')
    parent_id = azure_data.get('ParentId', '')
    telemetry_type = azure_data.get('Type', '')
    dependency_type = azure_data.get('DependencyType', '')
    
    if not operation_id or not span_id:
        return None
    
    # Timing (nanoseconds)
    start_time_ns = convert_timestamp_to_nano(azure_data.get('time', ''))
    duration_ms = azure_data.get('DurationMs', 0)
    end_time_ns = start_time_ns + int(duration_ms * 1_000_000)
    
    # Span kind determination
    if telemetry_type == 'AppRequests':
        kind = Span.SPAN_KIND_SERVER
    elif telemetry_type == 'AppDependencies':
        if dependency_type == 'InProc':
            kind = Span.SPAN_KIND_INTERNAL
        else:
            kind = Span.SPAN_KIND_CLIENT
    else:
        kind = Span.SPAN_KIND_INTERNAL
    
    # Status
    success = azure_data.get('Success', True)
    if isinstance(success, int):
        success = success == 1
    
    status_code = Status.STATUS_CODE_UNSET
    if not success:
        status_code = Status.STATUS_CODE_ERROR
    
    # Use Name for span name
    span_name = azure_data.get('Name', telemetry_type)
    
    # Build span
    span = Span(
        trace_id=bytes.fromhex(convert_trace_id(operation_id)),
        span_id=bytes.fromhex(convert_span_id(span_id)),
        name=span_name,
        kind=kind,
        start_time_unix_nano=start_time_ns,
        end_time_unix_nano=end_time_ns,
        status=Status(code=status_code)
    )
    
    # Add parent span ID
    if parent_id and parent_id != span_id:
        span.parent_span_id = bytes.fromhex(convert_span_id(parent_id))
    
    # Add attributes
    add_span_attributes(span, azure_data)
    
    return span


def add_span_attributes(span, azure_data):
    """Add attributes to span for Application Signals compatibility - all derived from span's own data."""
    
    telemetry_type = azure_data.get('Type', '')
    dependency_type = azure_data.get('DependencyType', '')
    target = azure_data.get('Target', '')
    name = azure_data.get('Name', '')
    
    def add_string(key, value):
        if value:
            span.attributes.append(
                KeyValue(key=key, value=AnyValue(string_value=str(value)))
            )
    
    def add_int(key, value):
        if value is not None:
            span.attributes.append(
                KeyValue(key=key, value=AnyValue(int_value=int(value)))
            )
    
    # AWS Application Signals attributes - common to all spans
    app_role_name = azure_data.get('AppRoleName', 'unknown-service')
    add_string('aws.local.service', app_role_name)
    add_string('aws.local.environment', 'generic:default')
    add_string('PlatformType', 'Generic')
    add_string('telemetry.extended', 'true')
    
    if telemetry_type == 'AppDependencies':
        if dependency_type == 'InProc':
            # InProc spans are internal - no aws.local.operation
            add_string('aws.span.kind', 'INTERNAL')
        else:
            # CLIENT spans - no aws.local.operation
            add_string('aws.span.kind', 'CLIENT')
            
            # Derive remote service from target and dependency type
            remote_service = derive_remote_service(dependency_type, target, name)
            add_string('aws.remote.service', remote_service)
            
            # Use Name as remote operation
            add_string('aws.remote.operation', name)
            
            # Remote environment
            add_string('aws.remote.environment', 'generic:default')
            
            # Remote resource type and identifier
            resource_type, resource_id = get_remote_resource(dependency_type, target, azure_data)
            if resource_type:
                add_string('aws.remote.resource.type', resource_type)
            if resource_id:
                add_string('aws.remote.resource.identifier', resource_id)
        
    elif telemetry_type == 'AppRequests':
        add_string('aws.local.operation', name)
        add_string('aws.span.kind', 'SERVER')
    
    # HTTP attributes
    parts = name.split(' ', 1)
    if parts[0] in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
        add_string('http.method', parts[0])
        if len(parts) > 1:
            add_string('http.route', parts[1])
    
    url = azure_data.get('Url') or azure_data.get('Data') or target
    add_string('http.url', url)
    
    result_code = azure_data.get('ResultCode', '')
    if result_code:
        try:
            status_code_int = int(result_code)
            add_int('http.status_code', status_code_int)
            add_int('http.response.status_code', status_code_int)
        except ValueError:
            pass


def derive_remote_service(dependency_type, target, name):
    """Pass through target as remote service - no specific transformations."""
    return target or name or 'unknown-service'


def get_remote_resource(dependency_type, target, azure_data):
    """Pass through dependency type and target as resource info - no specific transformations."""
    if dependency_type:
        return dependency_type, target
    return None, None


def build_resource_spans(spans_by_service):
    """Build ResourceSpans list for protobuf."""
    
    resource_spans_list = []
    
    for service_name, data in spans_by_service.items():
        azure_data = data['azure_data']
        properties = azure_data.get('Properties', {})
        
        # Build resource attributes
        resource_attrs = [
            KeyValue(key='service.name', value=AnyValue(string_value=service_name)),
            KeyValue(key='cloud.provider', value=AnyValue(string_value='azure')),
            KeyValue(key='cloud.region', value=AnyValue(string_value=properties.get('Region', ''))),
        ]
        
        resource = Resource(attributes=resource_attrs)
        scope_spans = ScopeSpans(spans=data['spans'])
        resource_spans = ResourceSpans(
            resource=resource,
            scope_spans=[scope_spans]
        )
        
        resource_spans_list.append(resource_spans)
    
    return resource_spans_list


def convert_trace_id(operation_id):
    """Azure operation_Id → 32 hex chars."""
    if not operation_id:
        return '0' * 32
    
    # Remove dashes and lowercase
    op_id = operation_id.replace('-', '').lower()
    
    # Filter to only hex characters
    hex_chars = ''.join(c for c in op_id if c in '0123456789abcdef')
    
    if not hex_chars:
        # If no valid hex, generate from hash of original
        import hashlib
        hex_chars = hashlib.md5(operation_id.encode()).hexdigest()
    
    return hex_chars.ljust(32, '0')[:32]


def convert_span_id(span_id):
    """Ensure 16 hex chars."""
    if not span_id:
        return '0' * 16
    
    # Remove dashes and lowercase
    clean_id = span_id.replace('-', '').lower()
    
    # Filter to only hex characters
    hex_chars = ''.join(c for c in clean_id if c in '0123456789abcdef')
    
    if not hex_chars:
        # If no valid hex, generate from hash of original
        import hashlib
        hex_chars = hashlib.md5(span_id.encode()).hexdigest()[:16]
    
    return hex_chars.ljust(16, '0')[:16]


def convert_timestamp_to_nano(timestamp_str):
    """Azure ISO8601 → Unix nanoseconds."""
    if not timestamp_str:
        return int(datetime.utcnow().timestamp() * 1_000_000_000)
    
    try:
        clean_ts = timestamp_str.replace('Z', '')
        if '.' in clean_ts:
            date_part, frac_part = clean_ts.split('.')
            frac_part = frac_part[:6]
            clean_ts = f"{date_part}.{frac_part}"
        
        dt = datetime.fromisoformat(clean_ts)
        return int(dt.timestamp() * 1_000_000_000)
    except Exception as e:
        print(f'Error parsing timestamp: {e}')
        return int(datetime.utcnow().timestamp() * 1_000_000_000)


def send_to_xray_otlp(resource_spans):
    """Send protobuf payload to X-Ray OTLP endpoint."""
    
    region = os.environ.get('AWS_REGION', 'us-east-1')
    endpoint = f"https://xray.{region}.amazonaws.com/v1/traces"
    
    # Create protobuf request
    request_proto = ExportTraceServiceRequest(resource_spans=resource_spans)
    body = request_proto.SerializeToString()
    
    # Get credentials (matching working code pattern)
    session = boto3.Session()
    boto_creds = session.get_credentials()
    frozen_creds = boto_creds.get_frozen_credentials()
    
    creds = Credentials(
        access_key=frozen_creds.access_key,
        secret_key=frozen_creds.secret_key,
        token=frozen_creds.token
    )
    
    # Sign with SigV4
    headers = {'Content-Type': 'application/x-protobuf'}
    req = AWSRequest(method='POST', url=endpoint, data=body, headers=headers)
    SigV4Auth(creds, 'xray', region).add_auth(req)
    signed_headers = dict(req.headers.items())
    
    # Send request using requests library
    print(f'Sending {len(resource_spans)} resource spans to {endpoint}')
    try:
        response = requests.post(endpoint, data=body, headers=signed_headers)
        print(f'X-Ray OTLP response: {response.status_code}')
        if response.status_code != 200:
            print(f'X-Ray OTLP error: {response.text}')
    except Exception as e:
        print(f'Error sending to X-Ray OTLP: {e}')
        raise
