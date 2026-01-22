"""
Test version of GetAllAppointments that returns empty results if Cosmos DB is not configured
"""
import logging
import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """GetAllAppointments that returns empty results for testing"""
    logging.info('=== GetAllAppointmentsTest function START ===')
    logging.info(f'Request method: {req.method}')
    logging.info(f'Request URL: {req.url}')

    try:
        # Get query parameters
        limit = int(req.params.get('limit', 100))
        offset = int(req.params.get('offset', 0))
        appointment_date = req.params.get('date')
        
        logging.info(f'Parameters: limit={limit}, offset={offset}, date={appointment_date}')

        # Check if Cosmos DB is configured
        import os
        cosmos_endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        cosmos_key = os.environ.get("COSMOS_DB_KEY")
        
        logging.info(f'Cosmos DB configured: {bool(cosmos_endpoint and cosmos_key)}')
        
        if not cosmos_endpoint or not cosmos_key:
            # Return empty results for testing when Cosmos DB not configured
            logging.info('Cosmos DB not configured - returning empty test results')
            response = {
                "success": True,
                "message": "Retrieved 0 appointments successfully (test mode - no database)",
                "data": [],
                "count": 0,
                "test_mode": True,
                "cosmos_configured": False
            }
        else:
            # Try to connect to Cosmos DB
            try:
                from azure.cosmos import CosmosClient
                client = CosmosClient(cosmos_endpoint, cosmos_key)
                
                # Try to get actual data
                database_name = os.environ.get("COSMOS_DB_DATABASE", "petclinic")
                container_name = os.environ.get("COSMOS_DB_CONTAINER", "appointments")
                
                database = client.get_database_client(database_name)
                container = database.get_container_client(container_name)
                
                query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                response = {
                    "success": True,
                    "message": f"Retrieved {len(items)} appointments successfully",
                    "data": items,
                    "count": len(items),
                    "test_mode": False,
                    "cosmos_configured": True
                }
                
                logging.info(f'Successfully retrieved {len(items)} appointments from Cosmos DB')
                
            except Exception as e:
                logging.warning(f'Cosmos DB connection failed: {str(e)} - returning empty test results')
                response = {
                    "success": True,
                    "message": "Retrieved 0 appointments successfully (test mode - database error)",
                    "data": [],
                    "count": 0,
                    "test_mode": True,
                    "cosmos_configured": True,
                    "cosmos_error": str(e)
                }

        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
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
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "message": "Retrieved 0 appointments successfully (test mode - error fallback)",
                "data": [],
                "count": 0,
                "test_mode": True,
                "error": str(e)
            }),
            status_code=200,
            mimetype="application/json"
        )
