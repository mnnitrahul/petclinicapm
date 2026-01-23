"""
Azure Blob Storage client using official Azure SDK
Proper implementation with correct canonicalization and authentication
"""
import os
import logging
import json
from typing import Optional, Dict, Any, List
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


class BlobStorageClient:
    """
    Azure SDK implementation - Azure Functions compatible
    Uses lazy initialization to avoid cold start failures
    """
    
    def __init__(self):
        # NO logging, NO network calls, NO Azure SDK calls in __init__
        # Store configuration only
        self.connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME") 
        self.account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.environ.get("BLOB_CONTAINER_NAME", "pets")
        
        # Lazy initialization - clients created only when needed
        self._blob_service_client = None
        self._container_client = None
        self._container_initialized = False
        
    def _get_blob_service_client(self):
        """Lazy initialization of blob service client"""
        if self._blob_service_client is None:
            if self.connection_string:
                self._blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            elif self.account_name and self.account_key:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self._blob_service_client = BlobServiceClient(account_url=account_url, credential=self.account_key)
            else:
                raise ValueError("Missing Azure Storage credentials: need AZURE_STORAGE_CONNECTION_STRING or (AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY)")
        return self._blob_service_client
    
    def _get_container_client(self):
        """Lazy initialization of container client"""
        if self._container_client is None:
            blob_service_client = self._get_blob_service_client()
            self._container_client = blob_service_client.get_container_client(self.container_name)
        return self._container_client
    
    def _ensure_container_exists(self):
        """Ensure container exists - only called when first operation happens"""
        if not self._container_initialized:
            try:
                container_client = self._get_container_client()
                container_client.create_container()
                logging.info(f"Created new container: {self.container_name}")
            except ResourceExistsError:
                logging.info(f"Container already exists: {self.container_name}")
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
            
            # Upload blob using lazy initialized container client
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(blob_name)
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
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(blob_name)
            
            # Download blob content using Azure SDK
            blob_data = blob_client.download_blob().readall()
            pet_data = json.loads(blob_data.decode('utf-8'))
            
            logging.info(f"Retrieved pet with ID: {pet_id}")
            return pet_data
            
        except ResourceNotFoundError:
            logging.warning(f"Pet with ID {pet_id} not found")
            return None
        except Exception as e:
            logging.error(f"Failed to get pet {pet_id}: {str(e)}")
            raise
    
    def get_all_pets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pets with optional limit"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            pets = []
            container_client = self._get_container_client()
            blob_list = container_client.list_blobs(name_starts_with="", include=['metadata'])
            
            count = 0
            for blob in blob_list:
                if count >= limit:
                    break
                    
                try:
                    # Download each pet blob using Azure SDK
                    blob_client = container_client.get_blob_client(blob.name)
                    blob_data = blob_client.download_blob().readall()
                    pet_data = json.loads(blob_data.decode('utf-8'))
                    pets.append(pet_data)
                    count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to read pet blob {blob.name}: {str(e)}")
                    continue
            
            # Sort by created_at descending
            pets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logging.info(f"Retrieved {len(pets)} pets")
            return pets
            
        except Exception as e:
            logging.error(f"Failed to get all pets: {str(e)}")
            raise
    
    def delete_pet(self, pet_id: str) -> bool:
        """Delete a pet"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            blob_name = f"{pet_id}.json"
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(blob_name)
            
            # Delete the blob using Azure SDK
            blob_client.delete_blob()
            
            logging.info(f"Deleted pet with ID: {pet_id}")
            return True
            
        except ResourceNotFoundError:
            logging.warning(f"Pet with ID {pet_id} not found")
            return False
        except Exception as e:
            logging.error(f"Failed to delete pet {pet_id}: {str(e)}")
            raise
    
    def get_pets_by_species(self, species: str) -> List[Dict[str, Any]]:
        """Get all pets of a specific species"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            pets = []
            container_client = self._get_container_client()
            blob_list = container_client.list_blobs(name_starts_with="", include=['metadata'])
            
            for blob in blob_list:
                # Check metadata first for efficiency
                if blob.metadata and blob.metadata.get('species', '').lower() == species.lower():
                    try:
                        blob_client = container_client.get_blob_client(blob.name)
                        blob_data = blob_client.download_blob().readall()
                        pet_data = json.loads(blob_data.decode('utf-8'))
                        pets.append(pet_data)
                    except Exception as e:
                        logging.warning(f"Failed to read pet blob {blob.name}: {str(e)}")
                        continue
            
            logging.info(f"Retrieved {len(pets)} pets of species {species}")
            return pets
            
        except Exception as e:
            logging.error(f"Failed to get pets by species {species}: {str(e)}")
            raise
