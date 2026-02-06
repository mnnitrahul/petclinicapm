"""
OpenTelemetry configuration for Azure Monitor dependency tracking.
Import this module once to enable automatic instrumentation of:
- Azure SDK calls (Blob Storage)
- HTTP requests (except Cosmos DB which has manual tracing)
- Application Insights integration

Usage: Simply import this module at the top of your Azure Function:
    from shared_code import telemetry  # Triggers OpenTelemetry setup
"""
import os
import logging

# Only configure if running in Azure (has App Insights connection string)
_connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

if _connection_string:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
        from opentelemetry import trace
        from opentelemetry.propagate import extract
        
        # Get the function app name from environment variables
        # Azure Functions provides WEBSITE_SITE_NAME which is the function app name
        service_name = os.environ.get("WEBSITE_SITE_NAME", "petclinic-apm-function-app")
        
        # Get Cosmos DB endpoint to exclude from HTTP auto-tracking
        cosmos_endpoint = os.environ.get("COSMOS_DB_ENDPOINT", "")
        cosmos_host = cosmos_endpoint.replace("https://", "").replace(":443/", "").replace("/", "") if cosmos_endpoint else ""
        
        # Create a resource with proper service identification (no namespace prefix)
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: "1.0.0",
            "service.instance.id": os.environ.get("WEBSITE_INSTANCE_ID", "local"),
            "cloud.provider": "azure",
            "cloud.platform": "azure_functions",
        })
        
        # Configure Azure Monitor with OpenTelemetry
        # Cosmos DB has manual tracing in database.py with proper db.system=cosmosdb attributes
        # We disable auto-instrumentation that would create duplicate/generic HTTP spans
        configure_azure_monitor(
            resource=resource,
            enable_live_metrics=True,
            instrumentation_options={
                "azure_sdk": {
                    "enabled": True,
                },
                # Disable HTTP auto-tracking to avoid generic HTTP spans for Cosmos DB
                # The azure-cosmos SDK uses azure-core which makes HTTP calls internally
                "requests": {"enabled": False},
                "urllib3": {"enabled": False},
                "urllib": {"enabled": False},
                "httpx": {"enabled": False},
            },
            # Exclude Cosmos DB endpoints from HTTP dependency tracking
            # Manual spans in database.py provide better Cosmos DB-specific attributes
            exclude_urls=[
                cosmos_host,
                "documents.azure.com",
            ] if cosmos_host else ["documents.azure.com"],
        )
        
        logging.info(f"✅ OpenTelemetry configured for service: {service_name}")
        logging.info("📊 Tracking: Azure SDK (Blob Storage) + Manual Cosmos DB spans")
        logging.info(f"ℹ️ Excluded from HTTP tracking: {cosmos_host or 'documents.azure.com'}")
        
        # Helper function to extract trace context from incoming request
        def get_trace_context(req):
            """Extract W3C trace context from incoming HTTP request headers.
            Use this to propagate trace context from APIM to downstream calls.
            
            Usage in function:
                from shared_code.telemetry import get_trace_context
                ctx = get_trace_context(req)
                with tracer.start_as_current_span("my-operation", context=ctx):
                    # downstream calls will inherit this context
            """
            carrier = {
                "traceparent": req.headers.get("traceparent"),
                "tracestate": req.headers.get("tracestate"),
            }
            return extract(carrier)
        
        # Export for use in functions
        _tracer = trace.get_tracer(__name__)
        
    except ImportError as e:
        logging.warning(f"⚠️ OpenTelemetry packages not available: {e}")
        get_trace_context = None
        _tracer = None
    except Exception as e:
        logging.warning(f"⚠️ OpenTelemetry configuration failed: {e}")
        get_trace_context = None
        _tracer = None
else:
    logging.info("ℹ️ Application Insights not configured - OpenTelemetry tracking disabled")
    get_trace_context = None
    _tracer = None
