"""
Azure Blob Storage client using modern azure-storage-blob SDK
Python 3.10 compatible - matches Azure Functions runtime version
"""
import os
import logging
import json
from typing import Optional, Dict, Any, List
from azure.storage.blob import BlobServiceClient


class BlobStorageClient:
    """
    Modern Azure Storage implementation using BlobServiceClient
    Lazy initialization to avoid cold start issues in Azure Functions
    Python 3.10 compatible
    """
    
    def __init__(self):
        # NO logging, NO network calls, NO Azure SDK calls in __init__
        # Store configuration only
        self.connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME") 
        self.account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.environ.get("BLOB_CONTAINER_NAME", "pets")
        
        # Lazy initialization - clients created only when needed
        self._blob_service = None
        self._container_initialized = False
        
    def _get_blob_service(self):
        """Lazy initialization of BlobServiceClient"""
        if self._blob_service is None:
            if self.connection_string:
                # Use connection string directly with modern BlobServiceClient
                self._blob_service = BlobServiceClient.from_connection_string(self.connection_string)
            elif self.account_name and self.account_key:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                from azure.storage.blob import BlobServiceClient
                from azure.core.credentials import AzureKeyCredential
                # Create credential object for the modern SDK
                credential = AzureKeyCredential(self.account_key) 
                self._blob_service = BlobServiceClient(account_url=account_url, credential=credential)
            else:
                raise ValueError("Missing Azure Storage credentials: need AZURE_STORAGE_CONNECTION_STRING or (AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY)")
        return self._blob_service
    
    def _ensure_container_exists(self):
        """Ensure container exists - only called when first operation happens"""
        if not self._container_initialized:
            try:
                blob_service = self._get_blob_service()
                # Create container if it doesn't exist using modern API
                try:
                    blob_service.create_container(self.container_name)
                    logging.info(f"Created container '{self.container_name}'")
                except Exception as e:
                    if "ContainerAlreadyExists" in str(e):
                        logging.info(f"Container '{self.container_name}' already exists")
                    else:
                        raise
            except Exception as e:
                logging.error(f"Failed to create/verify container: {str(e)}")
                raise
            finally:
                self._container_initialized = True

    def create_pet(self, pet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pet by uploading JSON blob"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            pet_id = pet_data['id']
            blob_name = f"{pet_id}.json"
            
            # Convert pet data to JSON
            pet_json = json.dumps(pet_data, indent=2)
            
            # Upload as blob with metadata for searching
            metadata = {
                'pet_name': pet_data.get('name', ''),
                'species': pet_data.get('species', ''),
                'breed': pet_data.get('breed', ''),
                'owner_name': pet_data.get('owner_name', ''),
                'created_at': pet_data.get('created_at', '')
            }
            
            # Upload blob using modern BlobServiceClient API
            blob_service = self._get_blob_service()
            blob_client = blob_service.get_blob_client(container=self.container_name, blob=blob_name)
            blob_client.upload_blob(pet_json, overwrite=True, metadata=metadata)
            
            logging.info(f"Successfully created pet with ID: {pet_id}")
            return pet_data
            
        except Exception as e:
            logging.error(f"Failed to create pet: {str(e)}")
            raise
    
    def get_pet_by_id(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pet by ID"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            blob_name = f"{pet_id}.json"
            blob_service = self._get_blob_service()
            blob_client = blob_service.get_blob_client(container=self.container_name, blob=blob_name)
            
            # Download blob content using modern BlobServiceClient API
            try:
                blob_data = blob_client.download_blob()
                pet_json = blob_data.readall().decode('utf-8')
                pet_data = json.loads(pet_json)
                
                logging.info(f"Retrieved pet with ID: {pet_id}")
                return pet_data
            except Exception as e:
                if "BlobNotFound" in str(e):
                    logging.warning(f"Pet with ID {pet_id} not found")
                    return None
                else:
                    raise
            
        except Exception as e:
            logging.error(f"Failed to get pet {pet_id}: {str(e)}")
            raise
    
    def get_all_pets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pets with optional limit"""
        try:
            logging.info(f"Starting get_all_pets with limit: {limit}")
            
            # Ensure container exists before first operation
            self._ensure_container_exists()
            logging.info(f"Container '{self.container_name}' verified/created successfully")
            
            pets = []
            blob_service = self._get_blob_service()
            container_client = blob_service.get_container_client(self.container_name)
            
            # List blobs using modern BlobServiceClient API
            logging.info(f"Attempting to list blobs in container '{self.container_name}'")
            try:
                blob_list = container_client.list_blobs(include=['metadata'])
                logging.info("Successfully called list_blobs()")
            except Exception as e:
                logging.error(f"Failed to list blobs: {str(e)}")
                # Check if it's an authorization error
                if "authorization" in str(e).lower() or "forbidden" in str(e).lower():
                    raise ValueError(f"Authorization failed for blob storage. Check credentials and permissions: {str(e)}")
                elif "not found" in str(e).lower() or "does not exist" in str(e).lower():
                    raise ValueError(f"Container '{self.container_name}' not found: {str(e)}")
                else:
                    raise ValueError(f"Failed to access blob storage: {str(e)}")
            
            # Process blobs
            count = 0
            blob_count = 0
            for blob in blob_list:
                blob_count += 1
                if count >= limit:
                    break
                    
                logging.info(f"Processing blob: {blob.name}")
                try:
                    # Download each pet blob using modern API
                    blob_client = blob_service.get_blob_client(container=self.container_name, blob=blob.name)
                    blob_data = blob_client.download_blob()
                    pet_json = blob_data.readall().decode('utf-8')
                    pet_data = json.loads(pet_json)
                    pets.append(pet_data)
                    count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to read pet blob {blob.name}: {str(e)}")
                    continue
            
            logging.info(f"Found {blob_count} total blobs, processed {count} successfully")
            
            # Sort by created_at descending
            pets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logging.info(f"Retrieved {len(pets)} pets successfully")
            return pets
            
        except Exception as e:
            logging.error(f"Failed to get all pets: {str(e)}")
            # Re-raise with more specific error message
            raise
    
    def delete_pet(self, pet_id: str) -> bool:
        """Delete a pet"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            blob_name = f"{pet_id}.json"
            blob_service = self._get_blob_service()
            blob_client = blob_service.get_blob_client(container=self.container_name, blob=blob_name)
            
            # Check if blob exists and delete using modern BlobServiceClient API
            try:
                blob_client.delete_blob()
                logging.info(f"Deleted pet with ID: {pet_id}")
                return True
            except Exception as e:
                if "BlobNotFound" in str(e):
                    logging.warning(f"Pet with ID {pet_id} not found")
                    return False
                else:
                    raise
            
        except Exception as e:
            logging.error(f"Failed to delete pet {pet_id}: {str(e)}")
            raise

    def get_pets_by_species(self, species: str) -> List[Dict[str, Any]]:
        """Get all pets of a specific species"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            pets = []
            blob_service = self._get_blob_service()
            container_client = blob_service.get_container_client(self.container_name)
            
            # List blobs with metadata using modern BlobServiceClient API
            blob_list = container_client.list_blobs(include=['metadata'])
            
            for blob in blob_list:
                # Check metadata first for efficiency
                if blob.metadata and blob.metadata.get('species', '').lower() == species.lower():
                    try:
                        # Download each pet blob using modern API
                        blob_client = blob_service.get_blob_client(container=self.container_name, blob=blob.name)
                        blob_data = blob_client.download_blob()
                        pet_json = blob_data.readall().decode('utf-8')
                        pet_data = json.loads(pet_json)
                        pets.append(pet_data)
                    except Exception as e:
                        logging.warning(f"Failed to read pet blob {blob.name}: {str(e)}")
                        continue
            
            logging.info(f"Retrieved {len(pets)} pets of species {species}")
            return pets
            
        except Exception as e:
            logging.error(f"Failed to get pets by species {species}: {str(e)}")
            raise
