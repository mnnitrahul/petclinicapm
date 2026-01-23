"""
OpenTelemetry configuration for Azure Monitor dependency tracking.
Import this module once to enable automatic instrumentation of:
- Azure SDK calls (Blob Storage, Cosmos DB)
- HTTP requests
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
        from opentelemetry.instrumentation.azure_sdk import AzureSDKInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        
        # Configure Azure Monitor with OpenTelemetry
        configure_azure_monitor()
        
        # Instrument Azure SDK (Blob Storage, Cosmos DB, etc.)
        AzureSDKInstrumentor().instrument()
        
        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
        
        logging.info("✅ OpenTelemetry dependency tracking configured successfully")
        logging.info("📊 Tracking: Azure SDK (Blob Storage, Cosmos DB) + HTTP requests")
        
    except ImportError as e:
        logging.warning(f"⚠️ OpenTelemetry packages not available: {e}")
    except Exception as e:
        logging.warning(f"⚠️ OpenTelemetry configuration failed: {e}")
else:
    logging.info("ℹ️ Application Insights not configured - OpenTelemetry tracking disabled")
