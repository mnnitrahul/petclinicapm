"""
Debug function to test pure REST API approach for Azure Blob Storage
NO Azure SDK dependencies - only uses requests library
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

# Import our pure REST client
try:
    from shared_code.blob_storage_rest import BlobStorageRestClient
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared_code.blob_storage_rest import BlobStorageRestClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Debug function using pure REST API - NO Azure SDK dependencies"""
    logging.info('DebugRestAPI function processed a request.')

    # Use trace_context_manager to ensure all Azure SDK calls inherit APIM trace context
    with trace_context_manager(req, "DebugRestAPI"):
        debug_info = {
            "message": "🔍 REST API Debug function completed",
            "status": "SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "approach": "pure_rest_api",
            "diagnosis": []
        }

        try:
            debug_info["diagnosis"].append("✅ Function main() executed successfully")
            debug_info["diagnosis"].append("✅ Using pure HTTP REST API approach")
            debug_info["diagnosis"].append("✅ No Azure SDK dependencies required")
            
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
            
            # Test 2: Test REST client import and creation
            try:
                client = BlobStorageRestClient()
                debug_info["diagnosis"].append("✅ BlobStorageRestClient created successfully")
                debug_info["diagnosis"].append("✅ Pure REST API client - no cffi, no Azure SDK!")
            except Exception as e:
                debug_info["diagnosis"].append(f"❌ REST client creation failed: {str(e)}")
                debug_info["status"] = "ERROR"
            
            # Test 3: Test requests library
            try:
                import requests
                debug_info["diagnosis"].append("✅ Requests library available")
            except ImportError as e:
                debug_info["diagnosis"].append(f"❌ Requests library missing: {str(e)}")
                debug_info["status"] = "ERROR"
            
            # Test 4: Test connection string parsing
            try:
                if connection_string:
                    client = BlobStorageRestClient()
                    if client.account_name and client.account_key:
                        debug_info["diagnosis"].append("✅ Connection string parsed successfully")
                        debug_info["account_info"] = {
                            "account_name": client.account_name,
                            "account_key_length": len(client.account_key) if client.account_key else 0
                        }
                    else:
                        debug_info["diagnosis"].append("❌ Connection string parsing failed")
                        debug_info["status"] = "ERROR"
                else:
                    debug_info["diagnosis"].append("⚠️ No connection string to parse")
            except Exception as e:
                debug_info["diagnosis"].append(f"❌ Connection string parsing error: {str(e)}")
                debug_info["status"] = "ERROR"
            
            debug_info["diagnosis"].append("🎉 REST API debug completed successfully!")

            return func.HttpResponse(
                json.dumps(debug_info, indent=2),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Critical error in REST API debug: {str(e)}")
            
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
