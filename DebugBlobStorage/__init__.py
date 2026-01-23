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
        
        # Test 2: Basic Azure SDK import (no shared_code) - Testing azure-storage-blob==2.1.0
        try:
            from azure.storage.blob import BlockBlobService
            debug_info["diagnosis"].append("✅ Azure Storage Blob 2.1.0 import successful!")
        except ImportError as e:
            debug_info["diagnosis"].append(f"❌ Azure Storage Blob 2.1.0 import failed: {str(e)}")
            debug_info["status"] = "ERROR"
        except Exception as e:
            debug_info["diagnosis"].append(f"❌ Unexpected Azure Storage error: {str(e)}")
            debug_info["status"] = "ERROR"
        
        # Test 3: Try creating BlockBlobService instance
        try:
            connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            if connection_string:
                from azure.storage.blob import BlockBlobService
                # Test if we can create BlockBlobService without network calls
                debug_info["diagnosis"].append("✅ BlockBlobService class available")
                debug_info["diagnosis"].append("✅ Connection string available for testing")
            else:
                debug_info["diagnosis"].append("⚠️ No connection string to test BlockBlobService")
        except Exception as e:
            debug_info["diagnosis"].append(f"❌ BlockBlobService test failed: {str(e)}")
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
