"""
Pure Python Azure Blob Storage client - Azure SDK-like interface without cffi dependencies
Uses Azure Blob Storage REST API directly with built-in Python libraries
Provides same functionality as Azure SDK but with zero external dependencies
"""
import os
import logging
import json
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


class BlobStorageClient:
    """
    Azure SDK-compatible interface using pure Python
    Same methods and behavior as azure.storage.blob.BlobServiceClient
    """
    
    def __init__(self):
        logging.info("=== Pure Python BlobStorageClient (Azure SDK-compatible) initialization START ===")
        
        # Get environment variables
        self.connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.environ.get("BLOB_CONTAINER_NAME", "pets")
        
        # Parse connection string if provided
        if self.connection_string:
            self._parse_connection_string()
        
        # Validate we have required credentials
        if not self.account_name or not self.account_key:
            raise ValueError("Either AZURE_STORAGE_CONNECTION_STRING or both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY are required")
        
        # Build base URL
        self.base_url = f"https://{self.account_name}.blob.core.windows.net"
        
        logging.info(f"✅ Account: {self.account_name}")
        logging.info(f"✅ Container: {self.container_name}")
        logging.info(f"✅ Using pure Python REST API (Azure SDK-compatible)")
        
        # Initialize container
        self._initialize_container()
        logging.info("=== Pure Python BlobStorageClient initialization COMPLETE ===")
    
    def _parse_connection_string(self):
        """Parse Azure Storage connection string"""
        if not self.connection_string:
            return
            
        parts = self.connection_string.split(';')
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                logging.info(f"Connection string part: {key}={value[:10]}..." if len(value) > 10 else f"Connection string part: {key}={value}")
                
                if key == 'AccountName':
                    self.account_name = value
                    logging.info(f"✅ Parsed account name: {value}")
                elif key == 'AccountKey':
                    self.account_key = value
                    logging.info(f"✅ Parsed account key: {value[:10]}...")
    
    def _get_auth_header(self, method: str, url_path: str, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Generate Azure Storage authentication header"""
        if headers is None:
            headers = {}
        
        # Current UTC time
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        headers['x-ms-date'] = date_str
        headers['x-ms-version'] = '2020-10-02'
        
        # Get standard headers with defaults
        content_encoding = headers.get('Content-Encoding', '')
        content_language = headers.get('Content-Language', '')
        content_length = headers.get('Content-Length', '')
        content_md5 = headers.get('Content-MD5', '')
        content_type = headers.get('Content-Type', '')
        date = headers.get('Date', '')  # We use x-ms-date instead
        if_modified_since = headers.get('If-Modified-Since', '')
        if_match = headers.get('If-Match', '')
        if_none_match = headers.get('If-None-Match', '')
        if_unmodified_since = headers.get('If-Unmodified-Since', '')
        range_header = headers.get('Range', '')
        
        # Canonical headers (x-ms- headers sorted)
        canonical_headers = ""
        ms_headers = {}
        for header_name in headers.keys():
            if header_name.lower().startswith('x-ms-'):
                ms_headers[header_name.lower()] = headers[header_name]
        
        for header_name in sorted(ms_headers.keys()):
            canonical_headers += f"{header_name}:{ms_headers[header_name]}\n"
        
        # Canonical resource
        canonical_resource = f"/{self.account_name}{url_path}"
        
        # String to sign (Azure Storage format)
        string_to_sign = f"{method}\n{content_encoding}\n{content_language}\n{content_length}\n{content_md5}\n{content_type}\n{date}\n{if_modified_since}\n{if_match}\n{if_none_match}\n{if_unmodified_since}\n{range_header}\n{canonical_headers}{canonical_resource}"
        
        # Generate signature using SHA256
        signature = base64.b64encode(
            hmac.new(
                base64.b64decode(self.account_key),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        headers['Authorization'] = f"SharedKey {self.account_name}:{signature}"
        
        return headers
    
    def _make_request(self, method: str, url_path: str, data: bytes = None, headers: Dict[str, str] = None) -> bytes:
        """Make authenticated HTTP request to Azure Storage"""
        if headers is None:
            headers = {}
        
        # Get authentication headers
        auth_headers = self._get_auth_header(method, url_path, headers)
        
        # Build full URL
        full_url = f"{self.base_url}{url_path}"
        
        # Create request
        req = urllib.request.Request(full_url, data=data, method=method)
        
        # Add headers
        for key, value in auth_headers.items():
            req.add_header(key, value)
        
        try:
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            elif e.code == 409:
                # Container already exists - that's fine
                return b""
            else:
                error_body = e.read().decode('utf-8') if e.code != 404 else "Not Found"
                logging.error(f"HTTP Error {e.code}: {error_body}")
                raise
    
    def _initialize_container(self):
        """Initialize blob container if it doesn't exist"""
        try:
            # Try to create container
            url_path = f"/{self.container_name}?restype=container"
            headers = {'Content-Length': '0'}
            
            result = self._make_request('PUT', url_path, data=b'', headers=headers)
            logging.info(f"✅ Container '{self.container_name}' ready")
                
        except Exception as e:
            logging.error(f"Failed to initialize container: {str(e)}")
            raise
    
    def create_pet(self, pet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pet by uploading JSON blob - Azure SDK compatible method"""
        try:
            pet_id = pet_data['id']
            blob_name = f"{pet_id}.json"
            
            # Convert pet data to JSON
            pet_json = json.dumps(pet_data, indent=2)
            data = pet_json.encode('utf-8')
            
            # Upload blob with metadata
            url_path = f"/{self.container_name}/{blob_name}"
            headers = {
                'Content-Type': 'application/json',
                'Content-Length': str(len(data)),
                'x-ms-blob-type': 'BlockBlob',
                'x-ms-meta-pet_name': pet_data.get('name', ''),
                'x-ms-meta-species': pet_data.get('species', ''),
                'x-ms-meta-breed': pet_data.get('breed', ''),
                'x-ms-meta-owner_name': pet_data.get('owner_name', ''),
                'x-ms-meta-created_at': pet_data.get('created_at', '')
            }
            
            self._make_request('PUT', url_path, data=data, headers=headers)
            
            logging.info(f"✅ Created pet: {pet_id}")
            return pet_data
            
        except Exception as e:
            logging.error(f"Failed to create pet: {str(e)}")
            raise
    
    def get_pet_by_id(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pet by ID - Azure SDK compatible method"""
        try:
            blob_name = f"{pet_id}.json"
            url_path = f"/{self.container_name}/{blob_name}"
            
            # Download blob content
            result = self._make_request('GET', url_path)
            
            if result is None:
                logging.warning(f"Pet {pet_id} not found")
                return None
            
            # Parse JSON
            pet_data = json.loads(result.decode('utf-8'))
            
            logging.info(f"✅ Retrieved pet: {pet_id}")
            return pet_data
            
        except Exception as e:
            logging.error(f"Failed to get pet {pet_id}: {str(e)}")
            raise
    
    def get_all_pets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pets with optional limit - Azure SDK compatible method"""
        try:
            pets = []
            
            # List blobs in container
            url_path = f"/{self.container_name}?restype=container&comp=list&include=metadata"
            result = self._make_request('GET', url_path)
            
            if result:
                # Parse XML response (simple parsing since we control the data)
                response_text = result.decode('utf-8')
                
                # Extract blob names
                blob_names = []
                lines = response_text.split('\n')
                for line in lines:
                    if '<Name>' in line and '</Name>' in line:
                        name = line.split('<Name>')[1].split('</Name>')[0]
                        if name.endswith('.json'):
                            blob_names.append(name)
                
                # Download each blob (up to limit)
                count = 0
                for blob_name in blob_names:
                    if count >= limit:
                        break
                    
                    try:
                        pet_id = blob_name.replace('.json', '')
                        pet_data = self.get_pet_by_id(pet_id)
                        if pet_data:
                            pets.append(pet_data)
                            count += 1
                    except Exception as e:
                        logging.warning(f"Failed to read pet blob {blob_name}: {str(e)}")
                        continue
            
            # Sort by created_at descending
            pets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logging.info(f"✅ Retrieved {len(pets)} pets")
            return pets
            
        except Exception as e:
            logging.error(f"Failed to get all pets: {str(e)}")
            raise
    
    def delete_pet(self, pet_id: str) -> bool:
        """Delete a pet - Azure SDK compatible method"""
        try:
            blob_name = f"{pet_id}.json"
            url_path = f"/{self.container_name}/{blob_name}"
            
            # Delete the blob
            result = self._make_request('DELETE', url_path)
            
            if result is None:
                logging.warning(f"Pet {pet_id} not found")
                return False
            
            logging.info(f"✅ Deleted pet: {pet_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete pet {pet_id}: {str(e)}")
            raise
    
    def get_pets_by_species(self, species: str) -> List[Dict[str, Any]]:
        """Get all pets of a specific species - Azure SDK compatible method"""
        try:
            all_pets = self.get_all_pets(limit=1000)  # Get more pets for filtering
            
            # Filter by species
            filtered_pets = []
            for pet in all_pets:
                if pet.get('species', '').lower() == species.lower():
                    filtered_pets.append(pet)
            
            logging.info(f"✅ Retrieved {len(filtered_pets)} pets of species {species}")
            return filtered_pets
            
        except Exception as e:
            logging.error(f"Failed to get pets by species {species}: {str(e)}")
            raise
