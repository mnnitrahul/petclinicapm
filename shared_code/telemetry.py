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
        from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
        
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
        
        def _is_cosmos_http_span(span: ReadableSpan) -> bool:
            """Check if span is an HTTP call to Cosmos DB"""
            attrs = dict(span.attributes) if span.attributes else {}
            url = attrs.get("http.url", "") or attrs.get("url.full", "")
            peer = attrs.get("net.peer.name", "") or attrs.get("server.address", "")
            name = span.name or ""
            return "documents.azure.com" in str(url) or "documents.azure.com" in str(peer) or "documents.azure.com" in name
        
        # Custom span processor that drops Cosmos DB HTTP spans
        class FilteringSpanProcessor(SpanProcessor):
            """Span processor that filters out Cosmos DB HTTP spans"""
            def __init__(self, next_processor):
                self._next = next_processor
            
            def on_start(self, span, parent_context):
                if self._next:
                    self._next.on_start(span, parent_context)
            
            def on_end(self, span):
                # Only forward non-Cosmos HTTP spans
                if not _is_cosmos_http_span(span):
                    if self._next:
                        self._next.on_end(span)
            
            def shutdown(self):
                if self._next:
                    self._next.shutdown()
            
            def force_flush(self, timeout_millis=None):
                if self._next:
                    return self._next.force_flush(timeout_millis)
                return True
        
        # Configure Azure Monitor with OpenTelemetry
        configure_azure_monitor(
            resource=resource,
            enable_live_metrics=True,
            instrumentation_options={
                "azure_sdk": {
                    "enabled": True,
                },
                "requests": {"enabled": False},
                "urllib3": {"enabled": False},
                "urllib": {"enabled": False},
                "httpx": {"enabled": False},
            },
        )
        
        # Wrap existing span processors with our filter
        provider = trace.get_tracer_provider()
        if hasattr(provider, '_active_span_processor'):
            original_processor = provider._active_span_processor
            provider._active_span_processor = FilteringSpanProcessor(original_processor)
        
        logging.info(f"✅ OpenTelemetry configured for service: {service_name}")
        logging.info("📊 Tracking: Azure SDK (Blob Storage) + Manual Cosmos DB spans")
        logging.info("ℹ️ Cosmos DB HTTP spans filtered out")
        
        # Helper function to extract trace context from incoming request
        def get_trace_context(req):
            """Extract W3C trace context from incoming HTTP request headers."""
            carrier = {
                "traceparent": req.headers.get("traceparent"),
                "tracestate": req.headers.get("tracestate"),
            }
            return extract(carrier)
        
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
