"""
Azure Function to create a pet in blob storage for testing
"""
import logging
import json
import uuid
from datetime import datetime
import azure.functions as func

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
    """Main function to handle creating a pet"""
    logging.info('CreatePet function processed a request.')

    try:
        # Get request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Invalid JSON in request body"
                }),
                status_code=400,
                mimetype="application/json"
            )

        if not req_body:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Request body is required"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Validate required fields
        required_fields = ['name', 'species']
        missing_fields = [field for field in required_fields if not req_body.get(field)]
        
        if missing_fields:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Create pet data with defaults
        pet_data = {
            "id": str(uuid.uuid4()),
            "name": req_body['name'],
            "species": req_body['species'],
            "breed": req_body.get('breed', ''),
            "age": req_body.get('age', 0),
            "owner_name": req_body.get('owner_name', ''),
            "owner_email": req_body.get('owner_email', ''),
            "created_at": datetime.now().isoformat() + "Z"
        }

        # Initialize Blob Storage client with detailed logging
        logging.info("🔧 Initializing BlobStorageClient for CreatePet...")
        try:
            blob_client = BlobStorageClient()
            logging.info("✅ BlobStorageClient created successfully for CreatePet")
            
        except Exception as e:
            logging.error(f"❌ Blob Storage connection error in CreatePet: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": f"Blob Storage connection error: {str(e)}"
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Create pet in Blob Storage
        logging.info(f"🔍 Creating pet with ID: {pet_data['id']}")
        try:
            created_pet = blob_client.create_pet(pet_data)
            logging.info(f"✅ Pet created successfully: {created_pet['id']}")

            # Create success response
            response = create_success_response(
                f"Pet '{created_pet['name']}' created successfully",
                created_pet
            )

            return func.HttpResponse(
                json.dumps(response),
                status_code=201,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"❌ Failed to create pet: {str(e)}")
            import traceback
            logging.error(f"❌ Full traceback: {traceback.format_exc()}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": f"Failed to create pet: {str(e)}"
                }),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Unexpected error in CreatePet: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "An unexpected error occurred"
            }),
            status_code=500,
            mimetype="application/json"
        )
