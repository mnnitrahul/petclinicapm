"""
Simplified CreateAppointment function without shared_code imports
"""
import logging
import json
import uuid
from datetime import datetime, timezone
import azure.functions as func

# Direct import without shared_code
try:
    from azure.cosmos import CosmosClient, PartitionKey
    import os
    COSMOS_IMPORT_SUCCESS = True
except ImportError as e:
    COSMOS_IMPORT_SUCCESS = False
    COSMOS_IMPORT_ERROR = str(e)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Simplified CreateAppointment function"""
    logging.info('=== CreateAppointmentSimple function START ===')
    
    # Test basic functionality first
    if not COSMOS_IMPORT_SUCCESS:
        logging.error(f"Cosmos import failed: {COSMOS_IMPORT_ERROR}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": f"Import error: {COSMOS_IMPORT_ERROR}"
            }),
            status_code=500,
            mimetype="application/json"
        )
    
    # Check environment variables
    endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
    key = os.environ.get("COSMOS_DB_KEY")
    
    logging.info(f"Environment check - Endpoint present: {bool(endpoint)}")
    logging.info(f"Environment check - Key present: {bool(key)}")
    
    if not endpoint or not key:
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "Missing Cosmos DB environment variables",
                "endpoint_present": bool(endpoint),
                "key_present": bool(key)
            }),
            status_code=500,
            mimetype="application/json"
        )
    
    return func.HttpResponse(
        json.dumps({
            "success": True,
            "message": "CreateAppointmentSimple is working!",
            "cosmos_import": "SUCCESS",
            "env_vars_present": True
        }),
        status_code=200,
        mimetype="application/json"
    )
