"""
OpenTelemetry configuration for Azure Monitor.
Import this module to enable Azure SDK auto-instrumentation.

Environment Variables:
- APPLICATIONINSIGHTS_CONNECTION_STRING: Required (set automatically by Azure)
- ENABLE_OPENTELEMETRY: Set to "false" to disable (default: true)
"""
import os
import logging

_enable_otel = os.environ.get("ENABLE_OPENTELEMETRY", "true").lower()
_connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

if _enable_otel == "false":
    logging.info("OpenTelemetry disabled via ENABLE_OPENTELEMETRY=false")
elif _connection_string:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor()
        logging.info("OpenTelemetry configured for Azure Monitor")
    except Exception as e:
        logging.warning(f"OpenTelemetry configuration failed: {e}")
else:
    logging.info("Application Insights not configured - skipping OpenTelemetry")
