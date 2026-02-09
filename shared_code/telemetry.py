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

_enable_otel = os.environ.get("ENABLE_OPENTELEMETRY", "true").lower()
_connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

# Initialize exports with None defaults
get_trace_context = None

if _enable_otel == "false":
    logging.info("OpenTelemetry disabled via ENABLE_OPENTELEMETRY=false")
elif _connection_string:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.propagate import extract
        
        # Get service name from Azure (WEBSITE_SITE_NAME is set by Azure Functions runtime)
        service_name = os.environ.get("WEBSITE_SITE_NAME", "unknown_service")
        
        configure_azure_monitor(
            resource=Resource.create({SERVICE_NAME: service_name})
        )
        logging.info(f"OpenTelemetry configured for service: {service_name}")
        
        # Helper function to extract trace context from incoming request (APIM)
        def get_trace_context(req):
            """Extract W3C trace context from incoming HTTP request headers.
            
            API Management sends traceparent header. Use this to propagate
            the trace context so downstream calls share the same trace ID.
            
            Usage in function:
                from shared_code.telemetry import get_trace_context
                from opentelemetry import context
                
                ctx = get_trace_context(req)
                context.attach(ctx)
            """
            carrier = {
                "traceparent": req.headers.get("traceparent"),
                "tracestate": req.headers.get("tracestate"),
            }
            return extract(carrier)
        
    except Exception as e:
        logging.warning(f"OpenTelemetry configuration failed: {e}")
else:
    logging.info("Application Insights not configured - skipping OpenTelemetry")
