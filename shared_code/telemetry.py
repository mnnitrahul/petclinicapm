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
        # Disable urllib/urllib3/requests auto-instrumentation to avoid duplicate Cosmos DB tracking
        # Cosmos DB has manual tracing in database.py with proper db.system=cosmosdb attributes
        configure_azure_monitor(
            resource=resource,
            enable_live_metrics=True,
            instrumentation_options={
                "azure_sdk": {
                    "enabled": True,
                },
                # Disable HTTP auto-tracking to avoid duplicate entries with Cosmos DB
                # Our manual Cosmos DB spans provide better detail anyway
                "requests": {"enabled": False},
                "urllib3": {"enabled": False},
                "urllib": {"enabled": False},
            }
        )
        
        logging.info(f"✅ OpenTelemetry configured for service: {service_name}")
        logging.info("📊 Tracking: Azure SDK (Blob Storage) + Manual Cosmos DB spans")
        logging.info("ℹ️ HTTP auto-tracking disabled to avoid duplicate Cosmos DB entries")
        
    except ImportError as e:
        logging.warning(f"⚠️ OpenTelemetry packages not available: {e}")
    except Exception as e:
        logging.warning(f"⚠️ OpenTelemetry configuration failed: {e}")
else:
    logging.info("ℹ️ Application Insights not configured - OpenTelemetry tracking disabled")
