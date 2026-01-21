"""
Azure Function to create a new appointment
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any

import azure.functions as func
from pydantic import ValidationError

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_code.models import CreateAppointmentRequest, Appointment, AppointmentResponse
from shared_code.database import CosmosDBClient


def validate_datetime_format(date_str: str, time_str: str) -> bool:
    """Validate date and time format"""
    try:
        # Validate date format (YYYY-MM-DD)
        datetime.strptime(date_str, "%Y-%m-%d")
        # Validate time format (HH:MM)
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
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

        # Validate request data using Pydantic model
        try:
            appointment_request = CreateAppointmentRequest(**req_body)
        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": f"Validation error: {str(e)}"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Additional validation for date and time format
        if not validate_datetime_format(appointment_request.appointment_date, appointment_request.appointment_time):
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time"
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

        # Generate appointment ID and timestamps
        appointment_id = str(uuid.uuid4())
        current_timestamp = datetime.utcnow().isoformat() + "Z"

        # Create appointment data
        appointment_data = {
            "id": appointment_id,
            "patient_name": appointment_request.patient_name,
            "patient_email": appointment_request.patient_email,
            "patient_phone": appointment_request.patient_phone,
            "doctor_name": appointment_request.doctor_name,
            "appointment_date": appointment_request.appointment_date,
            "appointment_time": appointment_request.appointment_time,
            "duration_minutes": appointment_request.duration_minutes,
            "appointment_type": appointment_request.appointment_type,
            "status": "scheduled",
            "notes": appointment_request.notes,
            "created_at": current_timestamp,
            "updated_at": current_timestamp
        }

        # Save to Cosmos DB
        try:
            created_appointment = cosmos_client.create_appointment(appointment_data)
            logging.info(f"Successfully created appointment with ID: {appointment_id}")

            # Create response using Pydantic model
            appointment = Appointment(**created_appointment)
            response = AppointmentResponse(
                success=True,
                message="Appointment created successfully",
                data=appointment
            )

            return func.HttpResponse(
                response.model_dump_json(),
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
