"""
Azure Blob Storage configuration and utilities for petstore using Azure SDK
"""
import os
import logging
import json
from typing import Optional, Dict, Any, List
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


class BlobStorageClient:
    def __init__(self):
        logging.info("=== BlobStorageClient initialization START ===")
        
        # Get environment variables
        self.connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.environ.get("BLOB_CONTAINER_NAME", "pets")
        
        # Log environment variable status (without exposing sensitive data)
        logging.info(f"AZURE_STORAGE_CONNECTION_STRING present: {bool(self.connection_string)}")
        logging.info(f"AZURE_STORAGE_ACCOUNT_NAME present: {bool(self.account_name)}")
        logging.info(f"AZURE_STORAGE_ACCOUNT_KEY present: {bool(self.account_key)}")
        logging.info(f"BLOB_CONTAINER_NAME: {self.container_name}")
        
        # Initialize blob service client
        if self.connection_string:
            # Preferred method: connection string
            logging.info("Using connection string for Blob Storage authentication")
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        elif self.account_name and self.account_key:
            # Alternative method: account name + key
            logging.info("Using account name and key for Blob Storage authentication")
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url=account_url, credential=self.account_key)
        else:
            logging.error("Missing required Blob Storage environment variables!")
            raise ValueError("Either AZURE_STORAGE_CONNECTION_STRING or both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY are required")
        
        # Initialize container
        self.container_client = None
        self._initialize_container()
        logging.info("=== BlobStorageClient initialization COMPLETE ===")
        
    def _initialize_container(self):
        """Initialize blob container if it doesn't exist"""
        try:
            # Get or create container
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Create container if it doesn't exist
            try:
                self.container_client.create_container()
                logging.info(f"Created new container: {self.container_name}")
            except ResourceExistsError:
                logging.info(f"Container already exists: {self.container_name}")
                
        except Exception as e:
            logging.error(f"Failed to initialize blob container: {str(e)}")
            raise

    def create_pet(self, pet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pet by uploading JSON blob"""
        try:
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
            
            # Upload blob
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(pet_json, overwrite=True, metadata=metadata)
            
            logging.info(f"Successfully created pet with ID: {pet_id}")
            return pet_data
            
        except Exception as e:
            logging.error(f"Failed to create pet: {str(e)}")
            raise
    
    def get_pet_by_id(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pet by ID"""
        try:
            blob_name = f"{pet_id}.json"
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Download blob content
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
            pets = []
            blob_list = self.container_client.list_blobs(name_starts_with="", include=['metadata'])
            
            count = 0
            for blob in blob_list:
                if count >= limit:
                    break
                    
                try:
                    # Download each pet blob
                    blob_client = self.container_client.get_blob_client(blob.name)
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
            blob_name = f"{pet_id}.json"
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Delete the blob
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
            pets = []
            blob_list = self.container_client.list_blobs(name_starts_with="", include=['metadata'])
            
            for blob in blob_list:
                # Check metadata first for efficiency
                if blob.metadata and blob.metadata.get('species', '').lower() == species.lower():
                    try:
                        blob_client = self.container_client.get_blob_client(blob.name)
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
