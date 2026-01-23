#!/usr/bin/env python3
"""
Local test script for petstore blob storage functionality
Run this before deployment to verify everything works
"""
import os
import sys
import json
import uuid
from datetime import datetime, timezone

# Add the current directory to Python path so we can import shared_code
sys.path.append('.')

def test_blob_storage():
    """Test blob storage functionality locally"""
    print("🧪 Starting Local Blob Storage Tests")
    print("=" * 50)
    
    # Check environment variables
    print("1️⃣ Checking Environment Variables...")
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not set!")
        print("Set it with: export AZURE_STORAGE_CONNECTION_STRING='your_connection_string'")
        return False
    
    print(f"✅ Connection string found (length: {len(connection_string)})")
    
    # Test imports
    print("\n2️⃣ Testing Imports...")
    try:
        from azure.storage.blob import BlobServiceClient
        print("✅ Azure SDK import successful")
    except ImportError as e:
        print(f"❌ Azure SDK import failed: {e}")
        print("Install with: pip install azure-storage-blob==12.19.0")
        return False
    
    try:
        from shared_code.blob_storage import BlobStorageClient
        from shared_code.pet_models import PetModel
        print("✅ Shared code imports successful")
    except ImportError as e:
        print(f"❌ Shared code import failed: {e}")
        return False
    
    # Test BlobStorageClient initialization
    print("\n3️⃣ Testing BlobStorageClient Initialization...")
    try:
        blob_client = BlobStorageClient()
        print("✅ BlobStorageClient initialized successfully")
    except Exception as e:
        print(f"❌ BlobStorageClient initialization failed: {e}")
        return False
    
    # Test pet operations
    print("\n4️⃣ Testing Pet Operations...")
    
    # Create a test pet
    test_pet_id = str(uuid.uuid4())
    test_pet_data = {
        "id": test_pet_id,
        "name": "Test Dog",
        "species": "Dog",
        "breed": "Golden Retriever", 
        "age": 3,
        "color": "Golden",
        "weight": 65.5,
        "owner_name": "Test Owner",
        "owner_email": "test@example.com",
        "owner_phone": "+1-555-123-4567",
        "medical_notes": "Healthy dog",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    
    # Validate pet data
    try:
        validated_pet = PetModel.validate_pet_data(test_pet_data)
        print("✅ Pet data validation successful")
    except Exception as e:
        print(f"❌ Pet data validation failed: {e}")
        return False
    
    # Test CREATE operation
    print(f"\n   Creating pet with ID: {test_pet_id}")
    try:
        created_pet = blob_client.create_pet(validated_pet)
        print("✅ Pet creation successful")
    except Exception as e:
        print(f"❌ Pet creation failed: {e}")
        return False
    
    # Test GET operation
    print(f"\n   Retrieving pet with ID: {test_pet_id}")
    try:
        retrieved_pet = blob_client.get_pet_by_id(test_pet_id)
        if retrieved_pet and retrieved_pet['id'] == test_pet_id:
            print("✅ Pet retrieval successful")
        else:
            print("❌ Pet retrieval failed - data mismatch")
            return False
    except Exception as e:
        print(f"❌ Pet retrieval failed: {e}")
        return False
    
    # Test GET ALL operation
    print(f"\n   Getting all pets...")
    try:
        all_pets = blob_client.get_all_pets(limit=10)
        print(f"✅ Retrieved {len(all_pets)} pets")
        
        # Check if our test pet is in the list
        found_test_pet = any(pet['id'] == test_pet_id for pet in all_pets)
        if found_test_pet:
            print("✅ Test pet found in all pets list")
        else:
            print("❌ Test pet not found in all pets list")
            return False
    except Exception as e:
        print(f"❌ Get all pets failed: {e}")
        return False
    
    # Test DELETE operation
    print(f"\n   Deleting pet with ID: {test_pet_id}")
    try:
        delete_result = blob_client.delete_pet(test_pet_id)
        if delete_result:
            print("✅ Pet deletion successful")
        else:
            print("❌ Pet deletion failed")
            return False
    except Exception as e:
        print(f"❌ Pet deletion failed: {e}")
        return False
    
    # Verify deletion
    print(f"\n   Verifying deletion...")
    try:
        deleted_pet = blob_client.get_pet_by_id(test_pet_id)
        if deleted_pet is None:
            print("✅ Pet deletion verified - pet not found")
        else:
            print("❌ Pet deletion verification failed - pet still exists")
            return False
    except Exception as e:
        print(f"❌ Pet deletion verification failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Blob storage is working correctly.")
    print("✅ Ready for deployment!")
    return True

def test_json_serialization():
    """Test that our data can be serialized/deserialized properly"""
    print("\n5️⃣ Testing JSON Serialization...")
    
    test_data = {
        "id": "test-123",
        "name": "Fluffy",
        "age": 2,
        "weight": 15.5,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Test serialization
        json_str = json.dumps(test_data, indent=2)
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        
        if parsed_data == test_data:
            print("✅ JSON serialization/deserialization successful")
            return True
        else:
            print("❌ JSON data mismatch after serialization")
            return False
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Local Petstore Blob Storage Test Suite")
    print("This will test all blob storage functionality locally")
    print("Make sure AZURE_STORAGE_CONNECTION_STRING is set in your environment")
    print()
    
    # Run tests
    success = True
    
    success &= test_json_serialization()
    success &= test_blob_storage()
    
    if success:
        print("\n🎯 RESULT: All tests passed! Ready to deploy.")
        sys.exit(0)
    else:
        print("\n❌ RESULT: Some tests failed. Fix issues before deploying.")
        sys.exit(1)
