"""
Azure Function to delete an appointment by ID
"""
import logging
import json
import azure.functions as func

# Import shared modules (Azure Functions compatible way)
try:
    from shared_code.models import create_success_response, create_error_response
    from shared_code.database import CosmosDBClient
except ImportError:
    # Fallback for Azure Functions runtime
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared_code.models import create_success_response, create_error_response
    from shared_code.database import CosmosDBClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function to handle appointment deletion"""
    logging.info('DeleteAppointment function processed a request.')

    try:
        # Get appointment ID from route parameter
        appointment_id = req.route_params.get('id')
        
        if not appointment_id:
            return func.HttpResponse(
                json.dumps(create_error_response("Appointment ID is required")),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"Attempting to delete appointment with ID: {appointment_id}")

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

        # First, we need to find the appointment to get the partition key (appointment_date)
        # Since we don't know the appointment_date, we need to query for the appointment first
        try:
            # Query to find the appointment by ID across all partitions
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": appointment_id}]
            
            appointments = list(cosmos_client.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not appointments:
                logging.warning(f"Appointment with ID {appointment_id} not found")
                return func.HttpResponse(
                    json.dumps(create_error_response(f"Appointment with ID {appointment_id} not found")),
                    status_code=404,
                    mimetype="application/json"
                )
            
            appointment = appointments[0]  # Should only be one
            appointment_date = appointment.get('appointment_date')
            
            if not appointment_date:
                logging.error(f"Appointment {appointment_id} missing appointment_date field")
                return func.HttpResponse(
                    json.dumps(create_error_response("Invalid appointment data")),
                    status_code=500,
                    mimetype="application/json"
                )

            # Now delete the appointment using both ID and partition key
            deleted = cosmos_client.delete_appointment(appointment_id, appointment_date)
            
            if deleted:
                logging.info(f"Successfully deleted appointment with ID: {appointment_id}")
                
                response = create_success_response(
                    f"Appointment with ID {appointment_id} deleted successfully",
                    {"id": appointment_id, "appointment_date": appointment_date}
                )
                
                return func.HttpResponse(
                    json.dumps(response),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                # This shouldn't happen since we found it above, but handle it gracefully
                logging.warning(f"Failed to delete appointment {appointment_id} - not found during deletion")
                return func.HttpResponse(
                    json.dumps(create_error_response(f"Appointment with ID {appointment_id} not found")),
                    status_code=404,
                    mimetype="application/json"
                )

        except Exception as e:
            logging.error(f"Failed to delete appointment {appointment_id}: {str(e)}")
            return func.HttpResponse(
                json.dumps(create_error_response("Failed to delete appointment. Please try again.")),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Unexpected error in DeleteAppointment: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "An unexpected error occurred"
            }),
            status_code=500,
            mimetype="application/json"
        )
