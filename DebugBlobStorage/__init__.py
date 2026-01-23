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
        # Test 1: Check azure-storage import
        try:
            from azure.storage import CloudStorageAccount
            from azure.storage.blob import BlockBlobService
            debug_info["imports"]["azure_storage"] = "SUCCESS"
            debug_info["diagnosis"].append("✅ azure-storage package available")
        except ImportError as e:
            debug_info["imports"]["azure_storage"] = f"FAILED - {str(e)}"
            debug_info["diagnosis"].append("❌ azure-storage package missing")
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

        # Test 3: Test blob storage connection
        if debug_info["imports"]["azure_storage"] == "SUCCESS":
            try:
                if connection_string:
                    # Test connection string method using legacy API
                    account = CloudStorageAccount(is_emulated=False, connection_string=connection_string)
                    block_blob_service = account.create_block_blob_service()
                    debug_info["connection_test"]["method"] = "connection_string"
                elif account_name and account_key:
                    # Test account name + key method using legacy API
                    block_blob_service = BlockBlobService(account_name=account_name, account_key=account_key)
                    debug_info["connection_test"]["method"] = "account_name_key"
                else:
                    raise ValueError("No valid authentication method found")

                # Test basic connectivity using legacy API
                try:
                    container_created = block_blob_service.create_container(container_name)
                    if container_created:
                        debug_info["connection_test"]["container_creation"] = "SUCCESS - Created new container"
                    else:
                        debug_info["connection_test"]["container_creation"] = "SUCCESS - Container already exists"
                except Exception as create_error:
                    debug_info["connection_test"]["container_creation"] = f"FAILED - {str(create_error)}"

                # Test listing blobs using legacy API
                try:
                    blobs = list(block_blob_service.list_blobs(container_name))
                    debug_info["connection_test"]["list_blobs"] = f"SUCCESS - Found {len(blobs)} blobs"
                    debug_info["connection_test"]["blob_count"] = len(blobs)
                except Exception as list_error:
                    debug_info["connection_test"]["list_blobs"] = f"FAILED - {str(list_error)}"

                debug_info["diagnosis"].append("✅ Blob storage connection working")
                
            except Exception as conn_error:
                debug_info["connection_test"]["error"] = str(conn_error)
                debug_info["diagnosis"].append(f"❌ Blob storage connection failed: {str(conn_error)}")
                debug_info["status"] = "ERROR"

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
