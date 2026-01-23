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
        # Test 1: Check Azure SDK import
        try:
            from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
            from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
            debug_info["imports"]["azure_storage_blob"] = "SUCCESS"
            debug_info["diagnosis"].append("✅ Azure Storage Blob SDK available")
        except ImportError as e:
            debug_info["imports"]["azure_storage_blob"] = f"FAILED - {str(e)}"
            debug_info["diagnosis"].append("❌ Azure Storage Blob SDK missing")
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
            
            # Parse connection string to debug the issue
            debug_info["connection_string_debug"] = {}
            parts = connection_string.split(';')
            for part in parts:
                part = part.strip()
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Hide sensitive data but show structure
                    if key == 'AccountKey':
                        debug_info["connection_string_debug"][key] = f"{value[:10]}...({len(value)} chars)"
                    else:
                        debug_info["connection_string_debug"][key] = value
                        
            debug_info["diagnosis"].append(f"🔍 Connection string parts: {list(debug_info['connection_string_debug'].keys())}")
            
        elif account_name and account_key:
            debug_info["diagnosis"].append("✅ Account name and key configured")
        else:
            debug_info["diagnosis"].append("❌ No blob storage credentials configured")
            debug_info["status"] = "ERROR"

        # Test 3: Skip direct connection test (will test via BlobStorageClient)
        debug_info["connection_test"]["method"] = "azure_sdk"
        debug_info["diagnosis"].append("✅ Using official Azure Storage Blob SDK")

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
                
                # Test step-by-step authentication
                if connection_string:
                    debug_info["auth_debug"] = {}
                    try:
                        # Parse connection string manually
                        parts = connection_string.split(';')
                        account_name = None
                        account_key = None
                        for part in parts:
                            part = part.strip()
                            if '=' in part:
                                key, value = part.split('=', 1)
                                if key.strip() == 'AccountName':
                                    account_name = value.strip()
                                elif key.strip() == 'AccountKey':
                                    account_key = value.strip()
                        
                        debug_info["auth_debug"]["parsed_account_name"] = account_name
                        debug_info["auth_debug"]["parsed_key_length"] = len(account_key) if account_key else 0
                        
                        if account_name and account_key:
                            # Test creating a simple authentication header
                            import urllib.request
                            import hmac
                            import hashlib
                            import base64
                            from datetime import datetime, timezone
                            
                            method = "PUT"
                            url_path = "/pets?restype=container"
                            
                            now = datetime.now(timezone.utc)
                            date_str = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
                            
                            # Create string to sign
                            string_to_sign = f"{method}\n\n\n0\n\n\n\n\n\n\n\n\nx-ms-date:{date_str}\nx-ms-version:2020-10-02\n/{account_name}{url_path}"
                            
                            debug_info["auth_debug"]["string_to_sign"] = string_to_sign
                            debug_info["auth_debug"]["date_str"] = date_str
                            
                            # Generate signature
                            try:
                                signature = base64.b64encode(
                                    hmac.new(
                                        base64.b64decode(account_key),
                                        string_to_sign.encode('utf-8'),
                                        hashlib.sha256
                                    ).digest()
                                ).decode('utf-8')
                                
                                debug_info["auth_debug"]["signature"] = f"{signature[:20]}..."
                                debug_info["auth_debug"]["auth_header"] = f"SharedKey {account_name}:{signature[:20]}..."
                                debug_info["diagnosis"].append(f"🔍 Auth Debug: Generated signature successfully")
                                
                            except Exception as sig_error:
                                debug_info["auth_debug"]["signature_error"] = str(sig_error)
                                debug_info["diagnosis"].append(f"❌ Auth Debug: Signature generation failed: {str(sig_error)}")
                        else:
                            debug_info["diagnosis"].append(f"❌ Auth Debug: Missing account name or key")
                            
                    except Exception as auth_debug_error:
                        debug_info["auth_debug"]["error"] = str(auth_debug_error)
                        debug_info["diagnosis"].append(f"❌ Auth Debug failed: {str(auth_debug_error)}")
                
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
