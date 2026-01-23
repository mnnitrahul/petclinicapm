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
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
        
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
        
        # Configure Azure Monitor with OpenTelemetry
        # This automatically instruments Azure SDK (Blob Storage, Cosmos DB) and HTTP requests
        configure_azure_monitor(
            resource=resource,
            enable_live_metrics=True,
            instrumentation_options={
                "azure_sdk": {"enabled": True},
                "requests": {"enabled": True},
                "urllib3": {"enabled": True},
            }
        )
        
        logging.info(f"✅ OpenTelemetry configured for service: {service_name}")
        logging.info("📊 Tracking: Azure SDK (Blob Storage, Cosmos DB) + HTTP requests")
        
    except ImportError as e:
        logging.warning(f"⚠️ OpenTelemetry packages not available: {e}")
    except Exception as e:
        logging.warning(f"⚠️ OpenTelemetry configuration failed: {e}")
else:
    logging.info("ℹ️ Application Insights not configured - OpenTelemetry tracking disabled")
