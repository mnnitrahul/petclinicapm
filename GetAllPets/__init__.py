"""
Azure Function to get all pets from blob storage
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
    """Main function to handle getting all pets"""
    logging.info('GetAllPets function processed a request.')

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

        # Get pets from Blob Storage
        try:
            if species:
                # Get pets filtered by species
                pets = blob_client.get_pets_by_species(species)
                message = f"Retrieved {len(pets)} pets of species '{species}' successfully"
            else:
                # Get all pets
                pets = blob_client.get_all_pets(limit=limit_int)
                message = f"Retrieved {len(pets)} pets successfully"

            logging.info(f"Successfully retrieved {len(pets)} pets")

            # Create success response
            response = create_success_response(
                message,
                pets,
                count=len(pets)
            )

            return func.HttpResponse(
                json.dumps(response),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Failed to get pets: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to retrieve pets. Please try again."
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
