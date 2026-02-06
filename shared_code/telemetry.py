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
        from opentelemetry.sdk.trace import SpanProcessor
        
        # Get the function app name from environment variables
        # Azure Functions provides WEBSITE_SITE_NAME which is the function app name
        service_name = os.environ.get("WEBSITE_SITE_NAME", "petclinic-apm-function-app")
        
        # Create a resource with proper service identification (no namespace prefix)
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: "1.0.0",
            "service.instance.id": os.environ.get("WEBSITE_INSTANCE_ID", "local"),
            "cloud.provider": "azure",
            "cloud.platform": "azure_functions",
        })
        
        # Custom span processor to filter out Cosmos DB HTTP spans
        class CosmosDBHttpFilter(SpanProcessor):
            """Filter out HTTP spans to Cosmos DB endpoints (documents.azure.com)"""
            def on_start(self, span, parent_context):
                pass
            
            def on_end(self, span):
                # Check if this is an HTTP span to Cosmos DB
                attrs = span.attributes or {}
                url = attrs.get("http.url", "") or attrs.get("url.full", "")
                peer = attrs.get("net.peer.name", "") or attrs.get("server.address", "")
                
                if "documents.azure.com" in url or "documents.azure.com" in peer:
                    # Mark span as not sampled to prevent export
                    span._readable_span._context = trace.SpanContext(
                        trace_id=span.context.trace_id,
                        span_id=span.context.span_id,
                        is_remote=span.context.is_remote,
                        trace_flags=trace.TraceFlags(0),  # Not sampled
                        trace_state=span.context.trace_state,
                    )
            
            def shutdown(self):
                pass
            
            def force_flush(self, timeout_millis=None):
                pass
        
        # Configure Azure Monitor with OpenTelemetry
        # Cosmos DB has manual tracing in database.py with proper db.system=cosmosdb attributes
        configure_azure_monitor(
            resource=resource,
            enable_live_metrics=True,
            instrumentation_options={
                "azure_sdk": {
                    "enabled": True,
                },
                # Disable HTTP client auto-tracking
                "requests": {"enabled": False},
                "urllib3": {"enabled": False},
                "urllib": {"enabled": False},
                "httpx": {"enabled": False},
            },
        )
        
        # Add filter to remove Cosmos DB HTTP spans
        trace.get_tracer_provider().add_span_processor(CosmosDBHttpFilter())
        
        logging.info(f"✅ OpenTelemetry configured for service: {service_name}")
        logging.info("📊 Tracking: Azure SDK (Blob Storage) + Manual Cosmos DB spans")
        logging.info("ℹ️ Cosmos DB HTTP spans filtered out")
        
        # Helper function to extract trace context from incoming request
        def get_trace_context(req):
            """Extract W3C trace context from incoming HTTP request headers.
            Use this to propagate trace context from APIM to downstream calls.
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
