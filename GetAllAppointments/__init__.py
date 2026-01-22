"""
Azure Function to get all appointments
"""
import logging
import json
from datetime import datetime

import azure.functions as func

# Import shared modules (Azure Functions compatible way)
try:
    from shared_code.models import create_list_response, create_error_response
    from shared_code.database import CosmosDBClient
except ImportError:
    # Fallback for Azure Functions runtime
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared_code.models import create_list_response, create_error_response
    from shared_code.database import CosmosDBClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function to handle getting all appointments"""
    logging.info('GetAllAppointments function processed a request.')

    try:
        # Get query parameters for pagination and filtering
        limit = int(req.params.get('limit', 100))
        offset = int(req.params.get('offset', 0))
        appointment_date = req.params.get('date')  # Optional date filter
        
        # Validate pagination parameters
        if limit < 1 or limit > 1000:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Limit must be between 1 and 1000"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        if offset < 0:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Offset must be non-negative"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Initialize Cosmos DB client
        try:
            cosmos_client = CosmosDBClient()
        except ValueError as e:
            logging.error(f"Database configuration error: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Database configuration error. Please check environment variables."
                }),
                status_code=500,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Database connection error: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Database connection error"
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Get appointments based on whether date filter is provided
        try:
            if appointment_date:
                # Validate date format if provided
                from datetime import datetime
                try:
                    datetime.strptime(appointment_date, "%Y-%m-%d")
                except ValueError:
                    return func.HttpResponse(
                        json.dumps({
                            "success": False,
                            "message": "Invalid date format. Use YYYY-MM-DD"
                        }),
                        status_code=400,
                        mimetype="application/json"
                    )
                
                # Get appointments for specific date
                appointments_data = cosmos_client.get_appointments_by_date(appointment_date)
                logging.info(f"Retrieved {len(appointments_data)} appointments for date {appointment_date}")
                
            else:
                # Get all appointments with pagination
                appointments_data = cosmos_client.get_all_appointments(limit=limit, offset=offset)
                logging.info(f"Retrieved {len(appointments_data)} appointments with limit={limit}, offset={offset}")

            # Create response with simple data
            response = create_list_response(
                f"Retrieved {len(appointments_data)} appointments successfully",
                appointments_data,
                len(appointments_data)
            )

            return func.HttpResponse(
                json.dumps(response),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Failed to retrieve appointments: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to retrieve appointments. Please try again."
                }),
                status_code=500,
                mimetype="application/json"
            )

    except ValueError as e:
        logging.error(f"Invalid query parameter: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "Invalid query parameters. Limit and offset must be integers."
            }),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Unexpected error in GetAllAppointments: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "An unexpected error occurred"
            }),
            status_code=500,
            mimetype="application/json"
        )
