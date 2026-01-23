"""
Azure Function to create a new pet in blob storage
"""
import logging
import json
import uuid
from datetime import datetime, timezone

import azure.functions as func

# Import shared modules (Azure Functions compatible way)
try:
    from shared_code.models import create_success_response, create_error_response
    from shared_code.blob_storage import BlobStorageClient
    from shared_code.pet_models import create_pet_data, validate_required_pet_fields, validate_pet_data_types
except ImportError:
    # Fallback for Azure Functions runtime
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared_code.models import create_success_response, create_error_response
    from shared_code.blob_storage import BlobStorageClient
    from shared_code.pet_models import create_pet_data, validate_required_pet_fields, validate_pet_data_types


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function to handle pet creation"""
    logging.info('CreatePet function processed a request.')

    try:
        # Get request body
        try:
            req_body = req.get_json()
            if not req_body:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "message": "Request body is required"
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
        except ValueError as e:
            logging.error(f"Invalid JSON in request body: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Invalid JSON format in request body"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Validate required fields
        missing_fields = validate_required_pet_fields(req_body)
        if missing_fields:
            return func.HttpResponse(
                json.dumps(create_error_response(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )),
                status_code=400,
                mimetype="application/json"
            )

        # Validate data types
        validation_errors = validate_pet_data_types(req_body)
        if validation_errors:
            return func.HttpResponse(
                json.dumps(create_error_response(
                    f"Validation errors: {'; '.join(validation_errors)}"
                )),
                status_code=400,
                mimetype="application/json"
            )

        # Initialize Blob Storage client
        try:
            blob_client = BlobStorageClient()
        except ValueError as e:
            logging.error(f"Blob Storage configuration error: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Blob Storage configuration error. Please check environment variables."
                }),
                status_code=500,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Blob Storage connection error: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Blob Storage connection error"
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Generate pet ID and timestamps
        pet_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # Create pet data using helper function
        pet_data = create_pet_data(req_body, pet_id, current_timestamp)

        # Save to Blob Storage
        try:
            created_pet = blob_client.create_pet(pet_data)
            logging.info(f"Successfully created pet with ID: {pet_id}")

            # Create success response
            response = create_success_response(
                "Pet created successfully", 
                created_pet
            )

            return func.HttpResponse(
                json.dumps(response),
                status_code=201,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Failed to create pet: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to create pet. Please try again."
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
