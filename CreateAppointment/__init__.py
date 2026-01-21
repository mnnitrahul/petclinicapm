"""
Azure Function to create a new appointment
"""
import logging
import json
import uuid
from datetime import datetime

import azure.functions as func

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_code.models import create_appointment_data, create_success_response, create_error_response
from shared_code.database import CosmosDBClient


def validate_required_fields(data):
    """Simple validation for required fields"""
    required_fields = [
        "patient_name", "patient_email", "patient_phone", 
        "doctor_name", "appointment_date", "appointment_time", 
        "appointment_type"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not data.get(field):
            missing_fields.append(field)
    
    return missing_fields


def validate_datetime_format(date_str, time_str):
    """Validate date and time format"""
    try:
        # Validate date format (YYYY-MM-DD)
        datetime.strptime(date_str, "%Y-%m-%d")
        # Validate time format (HH:MM)
        datetime.strptime(time_str, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function to handle appointment creation"""
    logging.info('CreateAppointment function processed a request.')

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

        # Simple validation for required fields
        missing_fields = validate_required_fields(req_body)
        if missing_fields:
            return func.HttpResponse(
                json.dumps(create_error_response(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )),
                status_code=400,
                mimetype="application/json"
            )

        # Validate date and time format
        if not validate_datetime_format(req_body.get("appointment_date"), req_body.get("appointment_time")):
            return func.HttpResponse(
                json.dumps(create_error_response(
                    "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time"
                )),
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

        # Generate appointment ID and timestamps
        appointment_id = str(uuid.uuid4())
        current_timestamp = datetime.utcnow().isoformat() + "Z"

        # Create appointment data using helper function
        appointment_data = create_appointment_data(req_body, appointment_id, current_timestamp)

        # Save to Cosmos DB
        try:
            created_appointment = cosmos_client.create_appointment(appointment_data)
            logging.info(f"Successfully created appointment with ID: {appointment_id}")

            # Create success response
            response = create_success_response(
                "Appointment created successfully", 
                created_appointment
            )

            return func.HttpResponse(
                json.dumps(response),
                status_code=201,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Failed to create appointment: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to create appointment. Please try again."
                }),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Unexpected error in CreateAppointment: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "An unexpected error occurred"
            }),
            status_code=500,
            mimetype="application/json"
        )
