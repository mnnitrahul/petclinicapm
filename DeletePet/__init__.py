"""
Azure Function to delete a pet by ID from blob storage
"""
import logging
import json
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
    """Main function to handle pet deletion"""
    logging.info('DeletePet function processed a request.')

    try:
        # Get pet ID from route parameter
        pet_id = req.route_params.get('id')
        
        if not pet_id:
            return func.HttpResponse(
                json.dumps(create_error_response("Pet ID is required")),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"Attempting to delete pet with ID: {pet_id}")

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

        # Check if pet exists before deletion (optional verification)
        try:
            existing_pet = blob_client.get_pet_by_id(pet_id)
            if not existing_pet:
                logging.warning(f"Pet with ID {pet_id} not found")
                return func.HttpResponse(
                    json.dumps(create_error_response(f"Pet with ID {pet_id} not found")),
                    status_code=404,
                    mimetype="application/json"
                )

            # Delete the pet
            deleted = blob_client.delete_pet(pet_id)
            
            if deleted:
                logging.info(f"Successfully deleted pet with ID: {pet_id}")
                
                response = create_success_response(
                    f"Pet with ID {pet_id} deleted successfully",
                    {"id": pet_id, "name": existing_pet.get("name", "")}
                )
                
                return func.HttpResponse(
                    json.dumps(response),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                # This shouldn't happen since we found it above, but handle it gracefully
                logging.warning(f"Failed to delete pet {pet_id} - not found during deletion")
                return func.HttpResponse(
                    json.dumps(create_error_response(f"Pet with ID {pet_id} not found")),
                    status_code=404,
                    mimetype="application/json"
                )

        except Exception as e:
            logging.error(f"Failed to delete pet {pet_id}: {str(e)}")
            return func.HttpResponse(
                json.dumps(create_error_response("Failed to delete pet. Please try again.")),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Unexpected error in DeletePet: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "An unexpected error occurred"
            }),
            status_code=500,
            mimetype="application/json"
        )
