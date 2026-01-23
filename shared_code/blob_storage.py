"""
Azure Blob Storage client using older azure-storage-blob==2.1.0
Hopefully no cffi dependency - Azure Functions compatible
"""
import os
import logging
import json
from typing import Optional, Dict, Any, List
from azure.storage.blob import BlockBlobService


class BlobStorageClient:
    """
    Legacy Azure Storage implementation - No cffi dependency
    Uses BlockBlobService from azure-storage package
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
        """Lazy initialization of BlockBlobService"""
        if self._blob_service is None:
            if self.connection_string:
                # Use connection string directly with older BlockBlobService
                self._blob_service = BlockBlobService(connection_string=self.connection_string)
            elif self.account_name and self.account_key:
                self._blob_service = BlockBlobService(account_name=self.account_name, account_key=self.account_key)
            else:
                raise ValueError("Missing Azure Storage credentials: need AZURE_STORAGE_CONNECTION_STRING or (AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY)")
        return self._blob_service
    
    def _ensure_container_exists(self):
        """Ensure container exists - only called when first operation happens"""
        if not self._container_initialized:
            try:
                blob_service = self._get_blob_service()
                # Create container if it doesn't exist
                blob_service.create_container(self.container_name, fail_on_exist=False)
                logging.info(f"Container '{self.container_name}' ready")
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
            
            # Upload blob using BlockBlobService (legacy API)
            blob_service = self._get_blob_service()
            blob_service.create_blob_from_text(
                self.container_name, 
                blob_name, 
                pet_json,
                metadata=metadata
            )
            
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
            
            # Download blob content using BlockBlobService (legacy API)
            if blob_service.exists(self.container_name, blob_name):
                blob_data = blob_service.get_blob_to_text(self.container_name, blob_name)
                pet_data = json.loads(blob_data.content)
                
                logging.info(f"Retrieved pet with ID: {pet_id}")
                return pet_data
            else:
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
            blob_service = self._get_blob_service()
            
            # List blobs using BlockBlobService (legacy API)
            blob_list = blob_service.list_blobs(self.container_name, include='metadata')
            
            count = 0
            for blob in blob_list:
                if count >= limit:
                    break
                    
                try:
                    # Download each pet blob
                    blob_data = blob_service.get_blob_to_text(self.container_name, blob.name)
                    pet_data = json.loads(blob_data.content)
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
            blob_service = self._get_blob_service()
            
            # Check if blob exists and delete using BlockBlobService (legacy API)
            if blob_service.exists(self.container_name, blob_name):
                blob_service.delete_blob(self.container_name, blob_name)
                logging.info(f"Deleted pet with ID: {pet_id}")
                return True
            else:
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
            blob_service = self._get_blob_service()
            
            # List blobs with metadata using BlockBlobService (legacy API)
            blob_list = blob_service.list_blobs(self.container_name, include='metadata')
            
            for blob in blob_list:
                # Check metadata first for efficiency
                if blob.metadata and blob.metadata.get('species', '').lower() == species.lower():
                    try:
                        blob_data = blob_service.get_blob_to_text(self.container_name, blob.name)
                        pet_data = json.loads(blob_data.content)
                        pets.append(pet_data)
                    except Exception as e:
                        logging.warning(f"Failed to read pet blob {blob.name}: {str(e)}")
                        continue
            
            logging.info(f"Retrieved {len(pets)} pets of species {species}")
            return pets
            
        except Exception as e:
            logging.error(f"Failed to get pets by species {species}: {str(e)}")
            raise
