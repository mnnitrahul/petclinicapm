"""
Cosmos DB database configuration and utilities with OpenTelemetry tracing
"""
import os
import logging
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from typing import Optional, Dict, Any, List

# Import OpenTelemetry for manual tracing (optional)
try:
    from opentelemetry import trace
    _tracer = trace.get_tracer(__name__)
    _OTEL_AVAILABLE = True
except ImportError:
    _tracer = None
    _OTEL_AVAILABLE = False


def _create_cosmos_span(operation_name: str, database: str = None, container: str = None, item_id: str = None):
    """Create an OpenTelemetry span for Cosmos DB operations"""
    if not _OTEL_AVAILABLE or not _tracer:
        # Return a no-op context manager
        class NoOpSpan:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def set_attribute(self, key, value): pass
            def set_status(self, status): pass
            def record_exception(self, exc): pass
        return NoOpSpan()
    
    span = _tracer.start_span(
        f"Cosmos DB {operation_name}",
        kind=trace.SpanKind.CLIENT
    )
    
    # Set Cosmos DB specific attributes
    span.set_attribute("db.system", "cosmosdb")
    span.set_attribute("db.name", database or "unknown")
    span.set_attribute("db.operation", operation_name)
    span.set_attribute("db.cosmosdb.container", container or "unknown")
    span.set_attribute("net.peer.name", os.environ.get("COSMOS_DB_ENDPOINT", "").replace("https://", "").replace(":443/", ""))
    
    if item_id:
        span.set_attribute("db.cosmosdb.item_id", item_id)
    
    return span


class CosmosDBClient:
    """Azure Functions compatible Cosmos DB client with lazy initialization and OpenTelemetry tracing"""
    
    def __init__(self):
        # NO logging, NO network calls, NO Cosmos SDK calls in __init__
        # Store configuration only
        self.endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        self.key = os.environ.get("COSMOS_DB_KEY")
        self.database_name = os.environ.get("COSMOS_DB_DATABASE", "petclinic")
        self.container_name = os.environ.get("COSMOS_DB_CONTAINER", "appointments")
        
        # Lazy initialization - clients created only when needed
        self._client = None
        self._database = None
        self._container = None
        self._database_initialized = False
        
    def _get_client(self):
        """Lazy initialization of Cosmos client"""
        if self._client is None:
            if not self.endpoint or not self.key:
                raise ValueError("Missing Cosmos DB credentials: need COSMOS_DB_ENDPOINT and COSMOS_DB_KEY")
            self._client = CosmosClient(self.endpoint, self.key)
        return self._client
    
    def _get_database(self):
        """Lazy initialization of database"""
        if self._database is None:
            client = self._get_client()
            self._database = client.get_database_client(self.database_name)
        return self._database
    
    def _get_container(self):
        """Lazy initialization of container"""
        if self._container is None:
            database = self._get_database()
            self._container = database.get_container_client(self.container_name)
        return self._container
    
    def _ensure_database_exists(self):
        """Ensure database and container exist - only called when first operation happens"""
        if not self._database_initialized:
            span = _create_cosmos_span("Initialize", self.database_name, self.container_name)
            try:
                with span:
                    client = self._get_client()
                    # Create database if it doesn't exist
                    self._database = client.create_database_if_not_exists(id=self.database_name)
                    
                    # Create container if it doesn't exist
                    # Using appointment_date as partition key for better distribution
                    self._container = self._database.create_container_if_not_exists(
                        id=self.container_name,
                        partition_key=PartitionKey(path="/appointment_date"),
                        offer_throughput=400
                    )
                    
                    logging.info(f"Database '{self.database_name}' and container '{self.container_name}' initialized successfully")
                    if _OTEL_AVAILABLE:
                        span.set_attribute("db.cosmosdb.status", "initialized")
            except Exception as e:
                if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                    span.record_exception(e)
                logging.error(f"Failed to initialize database: {str(e)}")
                raise
            finally:
                self._database_initialized = True
    
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new appointment"""
        span = _create_cosmos_span("CreateItem", self.database_name, self.container_name, appointment_data.get('id'))
        try:
            with span:
                # Ensure database exists before first operation
                self._ensure_database_exists()
                
                container = self._get_container()
                created_item = container.create_item(body=appointment_data)
                logging.info(f"Created appointment with ID: {created_item['id']}")
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.cosmosdb.item_id", created_item['id'])
                    span.set_attribute("db.cosmosdb.status", "created")
                
                return created_item
        except Exception as e:
            if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                span.record_exception(e)
            logging.error(f"Failed to create appointment: {str(e)}")
            raise
    
    def get_appointment_by_id(self, appointment_id: str, appointment_date: str) -> Optional[Dict[str, Any]]:
        """Get a single appointment by ID"""
        span = _create_cosmos_span("ReadItem", self.database_name, self.container_name, appointment_id)
        try:
            with span:
                # Ensure database exists before first operation
                self._ensure_database_exists()
                
                container = self._get_container()
                item = container.read_item(
                    item=appointment_id,
                    partition_key=appointment_date
                )
                logging.info(f"Retrieved appointment with ID: {appointment_id}")
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.cosmosdb.partition_key", appointment_date)
                    span.set_attribute("db.cosmosdb.status", "found")
                
                return item
        except CosmosResourceNotFoundError:
            if _OTEL_AVAILABLE:
                span.set_attribute("db.cosmosdb.status", "not_found")
            logging.warning(f"Appointment with ID {appointment_id} not found")
            return None
        except Exception as e:
            if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                span.record_exception(e)
            logging.error(f"Failed to get appointment {appointment_id}: {str(e)}")
            raise
    
    def get_all_appointments(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all appointments with optional pagination"""
        span = _create_cosmos_span("Query", self.database_name, self.container_name)
        try:
            with span:
                # Ensure database exists before first operation
                self._ensure_database_exists()
                
                container = self._get_container()
                query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.statement", query)
                    span.set_attribute("db.cosmosdb.cross_partition", True)
                
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                logging.info(f"Retrieved {len(items)} appointments")
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.cosmosdb.item_count", len(items))
                
                return items
        except Exception as e:
            if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                span.record_exception(e)
            logging.error(f"Failed to get all appointments: {str(e)}")
            raise
    
    def get_appointments_by_date(self, appointment_date: str) -> List[Dict[str, Any]]:
        """Get all appointments for a specific date"""
        span = _create_cosmos_span("Query", self.database_name, self.container_name)
        try:
            with span:
                # Ensure database exists before first operation
                self._ensure_database_exists()
                
                container = self._get_container()
                query = "SELECT * FROM c WHERE c.appointment_date = @date ORDER BY c.appointment_time"
                parameters = [{"name": "@date", "value": appointment_date}]
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.statement", query)
                    span.set_attribute("db.cosmosdb.partition_key", appointment_date)
                
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key=appointment_date
                ))
                logging.info(f"Retrieved {len(items)} appointments for date {appointment_date}")
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.cosmosdb.item_count", len(items))
                
                return items
        except Exception as e:
            if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                span.record_exception(e)
            logging.error(f"Failed to get appointments for date {appointment_date}: {str(e)}")
            raise
    
    def update_appointment(self, appointment_id: str, appointment_date: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing appointment"""
        span = _create_cosmos_span("ReplaceItem", self.database_name, self.container_name, appointment_id)
        try:
            with span:
                # Ensure database exists before first operation
                self._ensure_database_exists()
                
                # First get the existing item
                existing_item = self.get_appointment_by_id(appointment_id, appointment_date)
                if not existing_item:
                    raise CosmosResourceNotFoundError("Appointment not found")
                
                # Update the item with new data
                existing_item.update(updated_data)
                
                container = self._get_container()
                updated_item = container.replace_item(
                    item=appointment_id,
                    body=existing_item
                )
                logging.info(f"Updated appointment with ID: {appointment_id}")
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.cosmosdb.partition_key", appointment_date)
                    span.set_attribute("db.cosmosdb.status", "updated")
                
                return updated_item
        except Exception as e:
            if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                span.record_exception(e)
            logging.error(f"Failed to update appointment {appointment_id}: {str(e)}")
            raise
    
    def delete_appointment(self, appointment_id: str, appointment_date: str) -> bool:
        """Delete an appointment"""
        span = _create_cosmos_span("DeleteItem", self.database_name, self.container_name, appointment_id)
        try:
            with span:
                # Ensure database exists before first operation
                self._ensure_database_exists()
                
                container = self._get_container()
                container.delete_item(
                    item=appointment_id,
                    partition_key=appointment_date
                )
                logging.info(f"Deleted appointment with ID: {appointment_id}")
                
                if _OTEL_AVAILABLE:
                    span.set_attribute("db.cosmosdb.partition_key", appointment_date)
                    span.set_attribute("db.cosmosdb.status", "deleted")
                
                return True
        except CosmosResourceNotFoundError:
            if _OTEL_AVAILABLE:
                span.set_attribute("db.cosmosdb.status", "not_found")
            logging.warning(f"Appointment with ID {appointment_id} not found")
            return False
        except Exception as e:
            if _OTEL_AVAILABLE and hasattr(span, 'record_exception'):
                span.record_exception(e)
            logging.error(f"Failed to delete appointment {appointment_id}: {str(e)}")
            raise
