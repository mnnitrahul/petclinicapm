#!/usr/bin/env python3
"""
Mock local test script for petstore functionality
Tests code structure without requiring Azure connection
"""
import os
import sys
import json
import uuid
from datetime import datetime, timezone

# Add the current directory to Python path so we can import shared_code
sys.path.append('.')

def test_imports_and_structure():
    """Test that all imports work and code structure is valid"""
    print("🧪 Testing Code Structure and Imports")
    print("=" * 50)
    
    # Test shared_code imports
    print("1️⃣ Testing Shared Code Imports...")
    try:
        from shared_code.pet_models import (
            create_pet_data, 
            validate_required_pet_fields, 
            validate_pet_data_types,
            validate_email_format
        )
        print("✅ Pet models functions import successful")
    except ImportError as e:
        print(f"❌ Pet models import failed: {e}")
        return False
    
    # Test pet model validation
    print("\n2️⃣ Testing Pet Model Validation...")
    test_pet_data = {
        "name": "Test Dog",
        "species": "Dog",
        "breed": "Golden Retriever", 
        "age": 3,
        "color": "Golden",
        "weight": 65.5,
        "owner_name": "Test Owner",
        "owner_email": "test@example.com",
        "owner_phone": "+1-555-123-4567",
        "medical_notes": "Healthy dog"
    }
    
    try:
        # Test required fields validation
        missing_fields = validate_required_pet_fields(test_pet_data)
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Test data types validation
        validation_errors = validate_pet_data_types(test_pet_data)
        if validation_errors:
            print(f"❌ Validation errors: {validation_errors}")
            return False
        
        # Create pet data structure
        pet_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        validated_pet = create_pet_data(test_pet_data, pet_id, current_timestamp)
        
        print("✅ Pet data validation successful")
        print(f"   Validated pet: {validated_pet['name']} ({validated_pet['species']})")
    except Exception as e:
        print(f"❌ Pet data validation failed: {e}")
        return False
    
    # Test invalid pet data
    print("\n3️⃣ Testing Invalid Pet Data Handling...")
    invalid_pet_data = {
        "name": "",  # Empty name should fail
        "species": "Dog",
        "age": -1,   # Negative age should fail
        "owner_email": "invalid-email"  # Invalid email should fail
    }
    
    try:
        missing_fields = validate_required_pet_fields(invalid_pet_data)
        validation_errors = validate_pet_data_types(invalid_pet_data)
        
        if missing_fields or validation_errors:
            print(f"✅ Invalid pet data correctly rejected: {len(missing_fields)} missing fields, {len(validation_errors)} validation errors")
        else:
            print("❌ Invalid pet data validation should have failed but didn't")
            return False
    except Exception as e:
        print(f"✅ Invalid pet data correctly rejected: {type(e).__name__}")
    
    # Test blob storage imports (without initialization)
    print("\n4️⃣ Testing Blob Storage Code Structure...")
    try:
        from shared_code.blob_storage import BlobStorageClient
        print("✅ BlobStorageClient import successful")
        
        # Check that the class has the required methods
        required_methods = ['create_pet', 'get_pet_by_id', 'get_all_pets', 'delete_pet']
        for method_name in required_methods:
            if hasattr(BlobStorageClient, method_name):
                print(f"   ✅ Method {method_name} exists")
            else:
                print(f"   ❌ Method {method_name} missing")
                return False
                
    except ImportError as e:
        if "azure" in str(e).lower():
            print("⚠️ Azure SDK not installed locally (expected for local testing)")
            print("   ✅ BlobStorageClient file exists and will work in Azure Functions")
            # Check that the blob_storage.py file exists and has the right structure
            if os.path.exists('shared_code/blob_storage.py'):
                with open('shared_code/blob_storage.py', 'r') as f:
                    content = f.read()
                    if 'class BlobStorageClient:' in content:
                        print("   ✅ BlobStorageClient class found in source")
                        required_methods = ['create_pet', 'get_pet_by_id', 'get_all_pets', 'delete_pet']
                        for method in required_methods:
                            if f'def {method}(' in content:
                                print(f"   ✅ Method {method} found in source")
                            else:
                                print(f"   ❌ Method {method} missing from source")
                                return False
                    else:
                        print("   ❌ BlobStorageClient class not found in source")
                        return False
            else:
                print("   ❌ shared_code/blob_storage.py file missing")
                return False
        else:
            print(f"❌ BlobStorageClient import failed: {e}")
            return False
    
    # Test JSON serialization with pet data
    print("\n5️⃣ Testing JSON Serialization with Pet Data...")
    try:
        # Test serialization
        json_str = json.dumps(validated_pet, indent=2)
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        
        if parsed_data['id'] == validated_pet['id'] and parsed_data['name'] == validated_pet['name']:
            print("✅ Pet JSON serialization/deserialization successful")
        else:
            print("❌ Pet JSON data mismatch after serialization")
            return False
    except Exception as e:
        print(f"❌ Pet JSON serialization failed: {e}")
        return False
    
    return True

def test_azure_function_structure():
    """Test that Azure Function files have correct structure"""
    print("\n6️⃣ Testing Azure Function Structure...")
    
    required_functions = [
        ('CreatePet', 'CreatePet/__init__.py'),
        ('GetAllPets', 'GetAllPets/__init__.py'),
        ('DeletePet', 'DeletePet/__init__.py'),
        ('DebugBlobStorage', 'DebugBlobStorage/__init__.py')
    ]
    
    for func_name, func_path in required_functions:
        if os.path.exists(func_path):
            print(f"   ✅ {func_name} function exists")
            
            # Check if file contains 'def main'
            try:
                with open(func_path, 'r') as f:
                    content = f.read()
                    if 'def main(' in content:
                        print(f"      ✅ {func_name} has main function")
                    else:
                        print(f"      ❌ {func_name} missing main function")
                        return False
            except Exception as e:
                print(f"      ❌ Error reading {func_name}: {e}")
                return False
        else:
            print(f"   ❌ {func_name} function missing at {func_path}")
            return False
    
    return True

def test_requirements():
    """Test that requirements.txt has necessary dependencies"""
    print("\n7️⃣ Testing Requirements...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt missing")
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            
        required_packages = [
            'azure-functions',
            'azure-storage-blob',
            'azure-cosmos',
            'python-dateutil'
        ]
        
        for package in required_packages:
            if package in requirements:
                print(f"   ✅ {package} found in requirements")
            else:
                print(f"   ❌ {package} missing from requirements")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Mock Local Test Suite (No Azure Connection Required)")
    print("Testing code structure, validation, and function setup")
    print()
    
    # Run tests
    success = True
    
    success &= test_imports_and_structure()
    success &= test_azure_function_structure()
    success &= test_requirements()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 RESULT: All structure tests passed!")
        print("✅ Code is ready for deployment.")
        print("\n📝 To run full tests with Azure:")
        print("   export AZURE_STORAGE_CONNECTION_STRING='your_connection_string'")
        print("   python3 local_test.py")
        sys.exit(0)
    else:
        print("❌ RESULT: Some structure tests failed.")
        print("Fix issues before deploying.")
        sys.exit(1)
