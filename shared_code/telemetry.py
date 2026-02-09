"""
OpenTelemetry configuration for Azure Monitor.
Import this module to enable Azure SDK auto-instrumentation.

Environment Variables:
- APPLICATIONINSIGHTS_CONNECTION_STRING: Required (set automatically by Azure)
- ENABLE_OPENTELEMETRY: Set to "false" to disable (default: true)
- WEBSITE_SITE_NAME: Azure provides this automatically (used for cloud_RoleName)
"""
import os
import logging
from contextlib import contextmanager

_enable_otel = os.environ.get("ENABLE_OPENTELEMETRY", "true").lower()
_connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

# Initialize exports with None defaults
get_trace_context = None
trace_context_manager = None

if _enable_otel == "false":
    logging.info("OpenTelemetry disabled via ENABLE_OPENTELEMETRY=false")
elif _connection_string:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry import trace, context as otel_context
        from opentelemetry.propagate import extract
        
        # Get service name from Azure (WEBSITE_SITE_NAME is set by Azure Functions runtime)
        service_name = os.environ.get("WEBSITE_SITE_NAME", "unknown_service")
        
        configure_azure_monitor(
            resource=Resource.create({SERVICE_NAME: service_name})
        )
        logging.info(f"OpenTelemetry configured for service: {service_name}")
        
        # Get tracer for creating spans
        _tracer = trace.get_tracer(__name__)
        
        def get_trace_context(req):
            """Extract W3C trace context from incoming HTTP request headers.
            
            API Management sends traceparent header. This extracts it into
            an OpenTelemetry context object.
            
            Returns:
                Context object that can be used with context.attach() or trace_context_manager()
            """
            carrier = {
                "traceparent": req.headers.get("traceparent"),
                "tracestate": req.headers.get("tracestate"),
            }
            return extract(carrier)
        
        @contextmanager
        def trace_context_manager(req, span_name="FunctionExecution"):
            """Context manager that creates a child span under Azure Functions' request span.
            
            Azure Functions runtime already extracts traceparent from APIM and creates
            a request span. This creates a CHILD span under that request span, ensuring:
            - Proper parent-child hierarchy: APIM → Function Request → This Span → SDK calls
            - All Azure SDK calls (Cosmos DB, Blob Storage) inherit the trace context
            
            Usage:
                from shared_code.telemetry import trace_context_manager
                
                def main(req):
                    with trace_context_manager(req, "GetAllAppointments"):
                        # All Azure SDK calls here will have same operation_id
                        result = cosmos_client.get_all_appointments()
            """
            # Create a child span of the current context (Azure Functions request span)
            # Do NOT use context=parent_ctx - that would make this a sibling of the Function Request
            with _tracer.start_as_current_span(span_name) as span:
                # Log trace info for debugging
                span_context = span.get_span_context()
                if span_context.is_valid:
                    logging.info(f"Trace context: trace_id={format(span_context.trace_id, '032x')}, span_id={format(span_context.span_id, '016x')}")
                yield span
        
    except Exception as e:
        logging.warning(f"OpenTelemetry configuration failed: {e}")
else:
    logging.info("Application Insights not configured - skipping OpenTelemetry")

# Provide a no-op context manager when OTel is disabled
if trace_context_manager is None:
    @contextmanager
    def trace_context_manager(req, span_name="FunctionExecution"):
        """No-op context manager when OpenTelemetry is disabled."""
        yield None
