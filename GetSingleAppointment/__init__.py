    """
Azure Function to get a single appointment by ID
"""
import logging
import json
from datetime import datetime

import azure.functions as func

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_code.models import create_success_response, create_error_response
from shared_code.database import CosmosDBClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function to handle getting a single appointment"""
    logging.info('GetSingleAppointment function processed a request.')

    try:
        # Get appointment ID from route parameters
        appointment_id = req.route_params.get('id')
        if not appointment_id:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Appointment ID is required"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Get appointment date from query parameters (required for partition key)
        appointment_date = req.params.get('date')
        if not appointment_date:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Appointment date query parameter is required (format: YYYY-MM-DD)"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Validate date format
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

        # Get appointment by ID
        try:
            appointment_data = cosmos_client.get_appointment_by_id(appointment_id, appointment_date)
            
            if not appointment_data:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "message": f"Appointment with ID {appointment_id} not found for date {appointment_date}"
                    }),
                    status_code=404,
                    mimetype="application/json"
                )

            # Create simple success response
            response = create_success_response(
                "Appointment retrieved successfully",
                appointment_data
            )

            logging.info(f"Successfully retrieved appointment with ID: {appointment_id}")
            return func.HttpResponse(
                json.dumps(response),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Failed to retrieve appointment {appointment_id}: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to retrieve appointment. Please try again."
                }),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Unexpected error in GetSingleAppointment: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "An unexpected error occurred"
            }),
            status_code=500,
            mimetype="application/json"
        )
