"""
Azure Blob Storage client using pure HTTP REST API
No Azure SDK dependencies - completely Azure Functions compatible
"""
import os
import logging
import json
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import requests


class BlobStorageRestClient:
    """
    Pure REST API implementation - No Azure SDK dependencies
    Uses direct HTTP calls to Azure Blob Storage REST API
    """
    
    def __init__(self):
        # NO logging, NO network calls, NO Azure SDK calls in __init__
        # Store configuration only
        self.connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME") 
        self.account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.environ.get("BLOB_CONTAINER_NAME", "pets")
        
        # Parse connection string if provided
        if self.connection_string:
            self._parse_connection_string()
        
        # Lazy initialization flag
        self._container_initialized = False
        
    def _parse_connection_string(self):
        """Parse Azure Storage connection string to extract account name and key"""
        parts = {}
        for part in self.connection_string.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                parts[key] = value
        
        self.account_name = parts.get('AccountName')
        self.account_key = parts.get('AccountKey')
        
    def _get_auth_header(self, method: str, url_path: str, content_length: int = 0, content_type: str = '', date_header: str = '') -> str:
        """Generate Authorization header for Azure Storage requests"""
        if not self.account_name or not self.account_key:
            raise ValueError("Missing Azure Storage credentials")
        
        # Construct string to sign
        string_to_sign = f"{method}\n\n\n{content_length}\n\n{content_type}\n\n\n\n\n\n\nx-ms-date:{date_header}\nx-ms-version:2020-04-08\n/{self.account_name}{url_path}"
        
        # Sign the string
        key = base64.b64decode(self.account_key)
        signed_string = hmac.new(key, string_to_sign.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(signed_string).decode('utf-8')
        
        return f"SharedKey {self.account_name}:{signature}"
    
    def _make_request(self, method: str, url_path: str, data: bytes = None, headers: Dict[str, str] = None) -> requests.Response:
        """Make HTTP request to Azure Storage REST API"""
        base_url = f"https://{self.account_name}.blob.core.windows.net"
        url = base_url + url_path
        
        # Default headers
        req_headers = {
            'x-ms-version': '2020-04-08',
            'x-ms-date': datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        
        if headers:
            req_headers.update(headers)
        
        # Add content length
        content_length = len(data) if data else 0
        if content_length > 0:
            req_headers['Content-Length'] = str(content_length)
        
        # Generate auth header
        content_type = req_headers.get('Content-Type', '')
        auth_header = self._get_auth_header(method, url_path, content_length, content_type, req_headers['x-ms-date'])
        req_headers['Authorization'] = auth_header
        
        # Make request
        response = requests.request(method, url, data=data, headers=req_headers, timeout=30)
        return response
    
    def _ensure_container_exists(self):
        """Ensure container exists - only called when first operation happens"""
        if not self._container_initialized:
            try:
                # Try to create container
                url_path = f"/{self.container_name}?restype=container"
                response = self._make_request('PUT', url_path)
                
                if response.status_code in [201, 409]:  # Created or already exists
                    logging.info(f"Container '{self.container_name}' ready")
                else:
                    logging.error(f"Failed to create container: {response.status_code} {response.text}")
                    response.raise_for_status()
                    
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
            data = pet_json.encode('utf-8')
            
            # Upload blob using REST API
            url_path = f"/{self.container_name}/{blob_name}"
            headers = {
                'Content-Type': 'application/json',
                'x-ms-blob-type': 'BlockBlob',
                'x-ms-meta-pet_name': pet_data.get('name', ''),
                'x-ms-meta-species': pet_data.get('species', ''),
                'x-ms-meta-breed': pet_data.get('breed', ''),
                'x-ms-meta-owner_name': pet_data.get('owner_name', ''),
                'x-ms-meta-created_at': pet_data.get('created_at', '')
            }
            
            response = self._make_request('PUT', url_path, data, headers)
            
            if response.status_code == 201:
                logging.info(f"Successfully created pet with ID: {pet_id}")
                return pet_data
            else:
                logging.error(f"Failed to create pet: {response.status_code} {response.text}")
                response.raise_for_status()
            
        except Exception as e:
            logging.error(f"Failed to create pet: {str(e)}")
            raise
    
    def get_pet_by_id(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pet by ID"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            blob_name = f"{pet_id}.json"
            url_path = f"/{self.container_name}/{blob_name}"
            
            response = self._make_request('GET', url_path)
            
            if response.status_code == 200:
                pet_data = response.json()
                logging.info(f"Retrieved pet with ID: {pet_id}")
                return pet_data
            elif response.status_code == 404:
                logging.warning(f"Pet with ID {pet_id} not found")
                return None
            else:
                logging.error(f"Failed to get pet: {response.status_code} {response.text}")
                response.raise_for_status()
            
        except Exception as e:
            logging.error(f"Failed to get pet {pet_id}: {str(e)}")
            raise
    
    def get_all_pets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pets with optional limit"""
        try:
            # Ensure container exists before first operation
            self._ensure_container_exists()
            
            # List blobs using REST API
            url_path = f"/{self.container_name}?restype=container&comp=list&include=metadata"
            response = self._make_request('GET', url_path)
            
            if response.status_code != 200:
                logging.error(f"Failed to list blobs: {response.status_code} {response.text}")
                response.raise_for_status()
            
            pets = []
            # Parse XML response (simplified - would need proper XML parsing for production)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            count = 0
            for blob in root.findall('.//Blob'):
                if count >= limit:
                    break
                    
                name_elem = blob.find('Name')
                if name_elem is not None and name_elem.text.endswith('.json'):
                    try:
                        # Download each pet blob
                        pet_data = self.get_pet_by_id(name_elem.text.replace('.json', ''))
                        if pet_data:
                            pets.append(pet_data)
                            count += 1
                    except Exception as e:
                        logging.warning(f"Failed to read pet blob {name_elem.text}: {str(e)}")
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
            url_path = f"/{self.container_name}/{blob_name}"
            
            response = self._make_request('DELETE', url_path)
            
            if response.status_code == 202:
                logging.info(f"Deleted pet with ID: {pet_id}")
                return True
            elif response.status_code == 404:
                logging.warning(f"Pet with ID {pet_id} not found")
                return False
            else:
                logging.error(f"Failed to delete pet: {response.status_code} {response.text}")
                response.raise_for_status()
            
        except Exception as e:
            logging.error(f"Failed to delete pet {pet_id}: {str(e)}")
            raise
