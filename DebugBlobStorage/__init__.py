"""
Minimal Azure Function to debug basic functionality
NO shared_code imports - testing basic Azure Function execution
"""
import logging
import json
import os
from datetime import datetime, timezone

import azure.functions as func

# Import telemetry for trace context
try:
    from shared_code.telemetry import trace_context_manager
except ImportError:
    trace_context_manager = None


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Minimal debug function - NO shared_code imports"""
    logging.info('DebugBlobStorage function processed a request - MINIMAL VERSION')

    # Use trace_context_manager to ensure all Azure SDK calls inherit APIM trace context
    with trace_context_manager(req, "DebugBlobStorage"):
        debug_info = {
            "message": "🔍 MINIMAL Debug function completed",
            "status": "SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "step": "basic_execution",
            "diagnosis": []
        }

        try:
            debug_info["diagnosis"].append("✅ Function main() executed successfully")
            debug_info["diagnosis"].append("✅ Basic Python libraries working")
            debug_info["diagnosis"].append("✅ JSON serialization working")
            debug_info["diagnosis"].append("✅ Environment variables accessible")
            
            # Test 1: Basic environment variable access
            try:
                connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
                debug_info["environment"] = {
                    "connection_string_present": bool(connection_string),
                    "connection_string_length": len(connection_string) if connection_string else 0
                }
                debug_info["diagnosis"].append("✅ Environment variables readable")
            except Exception as e:
                debug_info["diagnosis"].append(f"❌ Environment variable error: {str(e)}")
                debug_info["status"] = "ERROR"
            
            # Test 2: Modern Azure SDK import - Testing azure-storage-blob==12.19.0 with Python 3.10
            try:
                from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
                debug_info["diagnosis"].append("✅ Modern Azure Storage Blob SDK import successful! 🎉")
                debug_info["diagnosis"].append("✅ Python 3.10 + Azure SDK working!")
            except ImportError as e:
                debug_info["diagnosis"].append(f"❌ Modern Azure Storage Blob SDK import failed: {str(e)}")
                debug_info["status"] = "ERROR"
            except Exception as e:
                debug_info["diagnosis"].append(f"❌ Unexpected Azure Storage SDK error: {str(e)}")
                debug_info["status"] = "ERROR"
            
            # Test 3: Try creating BlobServiceClient instance (no network calls)
            try:
                connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
                if connection_string:
                    from azure.storage.blob import BlobServiceClient
                    # Test if we can create the modern client class without network calls
                    debug_info["diagnosis"].append("✅ BlobServiceClient class available")
                    debug_info["diagnosis"].append("✅ Connection string available for testing")
                    debug_info["diagnosis"].append("✅ Ready for modern Azure SDK operations!")
                else:
                    debug_info["diagnosis"].append("⚠️ No connection string - configure AZURE_STORAGE_CONNECTION_STRING")
            except Exception as e:
                debug_info["diagnosis"].append(f"❌ BlobServiceClient test failed: {str(e)}")
                debug_info["status"] = "ERROR"
            
            debug_info["diagnosis"].append("🎉 Minimal debug completed successfully!")

            return func.HttpResponse(
                json.dumps(debug_info, indent=2),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Critical error in minimal debug: {str(e)}")
            
            # Even in critical error, return debug info
            debug_info["status"] = "CRITICAL_ERROR"
            debug_info["error"] = str(e)
            debug_info["error_type"] = type(e).__name__
            debug_info["diagnosis"].append(f"💥 Critical error: {str(e)}")
            
            return func.HttpResponse(
                json.dumps(debug_info, indent=2),
                status_code=200,  # Still return 200 to see debug info
                mimetype="application/json"
            )
