"""
Azure Function to get all pets from blob storage
"""
import logging
import json
import requests
import azure.functions as func

# Import telemetry first for dependency tracking
try:
    from shared_code.telemetry import trace_context_manager
    from opentelemetry.propagate import inject
except ImportError:
    trace_context_manager = None
    inject = None

AWS_API_ENDPOINT = "https://nzqxctynsd.execute-api.us-east-1.amazonaws.com/dev/lambda"

# Import shared modules (Azure Functions compatible way)
try:
    from shared_code.models import create_success_response, create_error_response
    from shared_code.blob_storage import BlobStorageClient
except ImportError:
    # Fallback for Azure Functions runtime
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared_code.models import create_success_response, create_error_response
    from shared_code.blob_storage import BlobStorageClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function to handle getting all pets"""
    logging.info('GetAllPets function processed a request.')
    
    # Use trace_context_manager to ensure all Azure SDK calls inherit APIM trace context
    with trace_context_manager(req, "GetAllPets"):
        try:
            # Get optional query parameters
            limit = req.params.get('limit')
            species = req.params.get('species')
            
            # Validate limit parameter
            limit_int = 100  # default limit
            if limit:
                try:
                    limit_int = int(limit)
                    if limit_int < 1:
                        limit_int = 100
                    elif limit_int > 1000:  # max limit for performance
                        limit_int = 1000
                except ValueError:
                    logging.warning(f"Invalid limit parameter: {limit}, using default 100")
                    limit_int = 100

            # Initialize Blob Storage client with detailed logging
            logging.info("🔧 Initializing BlobStorageClient...")
            try:
                blob_client = BlobStorageClient()
                logging.info("✅ BlobStorageClient created successfully")
                
                # Log configuration details (without sensitive info)
                logging.info(f"📋 Configuration - Account: {blob_client.account_name}, Container: {blob_client.container_name}")
                logging.info(f"📋 Has connection string: {bool(blob_client.connection_string)}")
                logging.info(f"📋 Has account key: {bool(blob_client.account_key)}")
                
            except ValueError as e:
                logging.error(f"❌ Blob Storage configuration error: {str(e)}")
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "message": f"Blob Storage configuration error: {str(e)}"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )
            except Exception as e:
                logging.error(f"❌ Blob Storage connection error: {str(e)}")
                logging.error(f"❌ Error type: {type(e).__name__}")
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "message": f"Blob Storage connection error: {str(e)}"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )

            # Get pets from Blob Storage with detailed logging
            logging.info("🔍 Starting blob storage operation...")
            try:
                if species:
                    logging.info(f"🔍 Getting pets filtered by species: {species}")
                    pets = blob_client.get_pets_by_species(species)
                    message = f"Retrieved {len(pets)} pets of species '{species}' successfully"
                else:
                    logging.info(f"🔍 Getting all pets with limit: {limit_int}")
                    pets = blob_client.get_all_pets(limit=limit_int)
                    message = f"Retrieved {len(pets)} pets successfully"

                logging.info(f"✅ Blob storage operation completed successfully - got {len(pets)} pets")

                # Create success response
                response = create_success_response(
                    message,
                    pets,
                    count=len(pets)
                )

                logging.info(f"✅ Returning success response with {len(pets)} pets")
                
                # Call AWS API Gateway with trace context
                aws_response = None
                try:
                    headers = {"Content-Type": "application/json"}
                    if inject:
                        inject(headers)
                        logging.info(f"Injected traceparent: {headers.get('traceparent')}")
                    else:
                        logging.warning("inject is None - trace context not propagated")
                    resp = requests.get(AWS_API_ENDPOINT, headers=headers, timeout=30)
                    aws_response = {"status": resp.status_code, "body": resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text}
                except Exception as e:
                    aws_response = {"error": str(e)}
                
                response["aws_call"] = aws_response
                response["trace_headers_sent"] = {"traceparent": headers.get("traceparent"), "tracestate": headers.get("tracestate")}
                
                return func.HttpResponse(
                    json.dumps(response),
                    status_code=200,
                    mimetype="application/json"
                )

            except ValueError as ve:
                logging.error(f"❌ Blob storage ValueError: {str(ve)}")
                logging.error(f"❌ ValueError type: {type(ve).__name__}")
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "message": f"Blob storage error: {str(ve)}"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )
            except Exception as e:
                logging.error(f"❌ Blob storage operation failed: {str(e)}")
                logging.error(f"❌ Exception type: {type(e).__name__}")
                logging.error(f"❌ Exception details: {repr(e)}")
                import traceback
                logging.error(f"❌ Full traceback: {traceback.format_exc()}")
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "message": f"Failed to retrieve pets: {str(e)}"
                    }),
                    status_code=500,
                    mimetype="application/json"
                )

        except Exception as e:
            logging.error(f"Unexpected error in GetAllPets: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "An unexpected error occurred"
                }),
                status_code=500,
                mimetype="application/json"
            )
