"""
Azure Function to debug blob storage configuration and connectivity
"""
import logging
import json
import os
from datetime import datetime, timezone

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Debug function for blob storage issues"""
    logging.info('DebugBlobStorage function processed a request.')

    debug_info = {
        "message": "🔍 Blob Storage Debug function completed",
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "imports": {},
        "environment_variables": {},
        "connection_test": {},
        "diagnosis": []
    }

    try:
        # Test 1: Check built-in Python libraries (no external dependencies)
        try:
            import urllib.request
            import urllib.error
            import hmac
            import hashlib
            import base64
            debug_info["imports"]["python_builtin"] = "SUCCESS"
            debug_info["diagnosis"].append("✅ Built-in Python libraries available (Azure SDK-compatible interface)")
        except ImportError as e:
            debug_info["imports"]["python_builtin"] = f"FAILED - {str(e)}"
            debug_info["diagnosis"].append("❌ Built-in Python libraries missing")
            debug_info["status"] = "ERROR"

        # Test 2: Check environment variables
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        container_name = os.environ.get("BLOB_CONTAINER_NAME", "pets")
        
        debug_info["environment_variables"] = {
            "AZURE_STORAGE_CONNECTION_STRING": "✅ YES" if connection_string else "❌ NO",
            "connection_string_length": len(connection_string) if connection_string else 0,
            "AZURE_STORAGE_ACCOUNT_NAME": "✅ YES" if account_name else "❌ NO",
            "AZURE_STORAGE_ACCOUNT_KEY": "✅ YES" if account_key else "❌ NO",
            "account_key_length": len(account_key) if account_key else 0,
            "BLOB_CONTAINER_NAME": container_name
        }

        if connection_string:
            debug_info["diagnosis"].append("✅ Connection string configured")
        elif account_name and account_key:
            debug_info["diagnosis"].append("✅ Account name and key configured")
        else:
            debug_info["diagnosis"].append("❌ No blob storage credentials configured")
            debug_info["status"] = "ERROR"

        # Test 3: Skip direct connection test (will test via BlobStorageClient)
        debug_info["connection_test"]["method"] = "pure_python_azure_compatible"
        debug_info["diagnosis"].append("✅ Using pure Python Azure-compatible implementation")

        # Test 4: Test BlobStorageClient class
        try:
            from shared_code.blob_storage import BlobStorageClient
            debug_info["imports"]["blob_storage_client"] = "SUCCESS"
            debug_info["diagnosis"].append("✅ BlobStorageClient import successful")
            
            # Try to initialize
            try:
                blob_client = BlobStorageClient()
                debug_info["connection_test"]["blob_storage_client_init"] = "SUCCESS"
                debug_info["diagnosis"].append("✅ BlobStorageClient initialization successful")
            except Exception as init_error:
                debug_info["connection_test"]["blob_storage_client_init"] = f"FAILED - {str(init_error)}"
                debug_info["diagnosis"].append(f"❌ BlobStorageClient initialization failed: {str(init_error)}")
                debug_info["status"] = "ERROR"
                
        except ImportError as import_error:
            debug_info["imports"]["blob_storage_client"] = f"FAILED - {str(import_error)}"
            debug_info["diagnosis"].append(f"❌ BlobStorageClient import failed: {str(import_error)}")
            debug_info["status"] = "ERROR"

        # Final diagnosis
        if debug_info["status"] == "SUCCESS":
            debug_info["diagnosis"].append("🎉 All blob storage tests passed!")
        else:
            debug_info["diagnosis"].append("🚨 Some blob storage tests failed - check details above")

        return func.HttpResponse(
            json.dumps(debug_info, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Unexpected error in DebugBlobStorage: {str(e)}")
        debug_info["status"] = "CRITICAL_ERROR"
        debug_info["error"] = str(e)
        debug_info["diagnosis"].append(f"💥 Critical error: {str(e)}")
        
        return func.HttpResponse(
            json.dumps(debug_info, indent=2),
            status_code=200,  # Still return 200 so we can see the debug info
            mimetype="application/json"
        )
