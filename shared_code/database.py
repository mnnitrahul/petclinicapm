"""
Cosmos DB database configuration and utilities
"""
import os
import logging
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from typing import Optional, Dict, Any, List


class CosmosDBClient:
    def __init__(self):
        logging.info("=== CosmosDBClient initialization START ===")
        
        # Get environment variables
        self.endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        self.key = os.environ.get("COSMOS_DB_KEY")
        self.database_name = os.environ.get("COSMOS_DB_DATABASE", "petclinic")
        self.container_name = os.environ.get("COSMOS_DB_CONTAINER", "appointments")
        
        # Log environment variable status (without exposing sensitive data)
        logging.info(f"COSMOS_DB_ENDPOINT present: {bool(self.endpoint)}")
        logging.info(f"COSMOS_DB_KEY present: {bool(self.key)}")
        logging.info(f"COSMOS_DB_DATABASE: {self.database_name}")
        logging.info(f"COSMOS_DB_CONTAINER: {self.container_name}")
        
        if self.endpoint:
            # Log endpoint (safe to log)
            logging.info(f"Cosmos DB Endpoint: {self.endpoint}")
        
        if not self.endpoint or not self.key:
            logging.error("Missing required environment variables!")
            logging.error(f"COSMOS_DB_ENDPOINT missing: {not self.endpoint}")
            logging.error(f"COSMOS_DB_KEY missing: {not self.key}")
            raise ValueError("COSMOS_DB_ENDPOINT and COSMOS_DB_KEY environment variables are required")
        
        # Initialize Cosmos client
        logging.info("Creating CosmosClient...")
        try:
            self.client = CosmosClient(self.endpoint, self.key)
            logging.info("CosmosClient created successfully")
        except Exception as e:
            logging.error(f"Failed to create CosmosClient: {str(e)}")
            raise
        
        self.database = None
        self.container = None
        
        # Initialize database and container
        logging.info("Initializing database and container...")
        self._initialize_database()
        logging.info("=== CosmosDBClient initialization COMPLETE ===")
        
    def _initialize_database(self):
        """Initialize database and container if they don't exist"""
        try:
            # Create database if it doesn't exist
            self.database = self.client.create_database_if_not_exists(
                id=self.database_name
            )
            
            # Create container if it doesn't exist
            # Using appointment_date as partition key for better distribution
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/appointment_date"),
                offer_throughput=400
            )
            
            logging.info(f"Database '{self.database_name}' and container '{self.container_name}' initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new appointment"""
        try:
            created_item = self.container.create_item(body=appointment_data)
            logging.info(f"Created appointment with ID: {created_item['id']}")
            return created_item
        except Exception as e:
            logging.error(f"Failed to create appointment: {str(e)}")
            raise
    
    def get_appointment_by_id(self, appointment_id: str, appointment_date: str) -> Optional[Dict[str, Any]]:
        """Get a single appointment by ID"""
        try:
            item = self.container.read_item(
                item=appointment_id,
                partition_key=appointment_date
            )
            logging.info(f"Retrieved appointment with ID: {appointment_id}")
            return item
        except CosmosResourceNotFoundError:
            logging.warning(f"Appointment with ID {appointment_id} not found")
            return None
        except Exception as e:
            logging.error(f"Failed to get appointment {appointment_id}: {str(e)}")
            raise
    
    def get_all_appointments(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all appointments with optional pagination"""
        try:
            query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            logging.info(f"Retrieved {len(items)} appointments")
            return items
        except Exception as e:
            logging.error(f"Failed to get all appointments: {str(e)}")
            raise
    
    def get_appointments_by_date(self, appointment_date: str) -> List[Dict[str, Any]]:
        """Get all appointments for a specific date"""
        try:
            query = "SELECT * FROM c WHERE c.appointment_date = @date ORDER BY c.appointment_time"
            parameters = [{"name": "@date", "value": appointment_date}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=appointment_date
            ))
            logging.info(f"Retrieved {len(items)} appointments for date {appointment_date}")
            return items
        except Exception as e:
            logging.error(f"Failed to get appointments for date {appointment_date}: {str(e)}")
            raise
    
    def update_appointment(self, appointment_id: str, appointment_date: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing appointment"""
        try:
            # First get the existing item
            existing_item = self.get_appointment_by_id(appointment_id, appointment_date)
            if not existing_item:
                raise CosmosResourceNotFoundError("Appointment not found")
            
            # Update the item with new data
            existing_item.update(updated_data)
            
            updated_item = self.container.replace_item(
                item=appointment_id,
                body=existing_item
            )
            logging.info(f"Updated appointment with ID: {appointment_id}")
            return updated_item
        except Exception as e:
            logging.error(f"Failed to update appointment {appointment_id}: {str(e)}")
            raise
    
    def delete_appointment(self, appointment_id: str, appointment_date: str) -> bool:
        """Delete an appointment"""
        try:
            self.container.delete_item(
                item=appointment_id,
                partition_key=appointment_date
            )
            logging.info(f"Deleted appointment with ID: {appointment_id}")
            return True
        except CosmosResourceNotFoundError:
            logging.warning(f"Appointment with ID {appointment_id} not found")
            return False
        except Exception as e:
            logging.error(f"Failed to delete appointment {appointment_id}: {str(e)}")
            raise
