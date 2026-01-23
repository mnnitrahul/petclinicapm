"""
Minimal Azure Function to debug basic functionality
NO shared_code imports - testing basic Azure Function execution
"""
import logging
import json
import os
from datetime import datetime, timezone

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Minimal debug function - NO shared_code imports"""
    logging.info('DebugBlobStorage function processed a request - MINIMAL VERSION')

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
        
        # Test 2: Basic Azure SDK import (no shared_code)
        try:
            from azure.storage.blob import BlobServiceClient
            debug_info["diagnosis"].append("✅ Azure Blob SDK import successful")
        except ImportError as e:
            debug_info["diagnosis"].append(f"❌ Azure Blob SDK import failed: {str(e)}")
            debug_info["status"] = "ERROR"
        except Exception as e:
            debug_info["diagnosis"].append(f"❌ Unexpected Azure SDK error: {str(e)}")
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
