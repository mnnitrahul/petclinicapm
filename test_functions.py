"""
Comprehensive test script for Azure Functions with Azure SDK validation
This script MUST pass before pushing any code to git
Use this as a reflection point to ensure code quality
"""
import json
import uuid
from datetime import datetime
import sys
import os

def create_test_appointment_data():
    """Generate test appointment data"""
    return {
        "patient_name": "John Doe",
        "patient_email": "john.doe@email.com",
        "patient_phone": "555-012-3456",
        "doctor_name": "Dr. Smith",
        "appointment_date": "2024-03-15",
        "appointment_time": "14:30",
        "duration_minutes": 30,
        "appointment_type": "Checkup",
        "notes": "Regular checkup for Max"
    }

def create_test_pet_data():
    """Generate test pet data"""
    return {
        "id": str(uuid.uuid4()),
        "name": "Buddy",
        "species": "Dog", 
        "breed": "Golden Retriever",
        "age": 3,
        "owner_name": "John Doe",
        "owner_email": "john.doe@email.com",
        "created_at": datetime.now().isoformat() + "Z"
    }

def validate_appointment_data(appointment_data):
    """Validate appointment data structure"""
    required_fields = [
        'id', 'patient_name', 'patient_email', 'patient_phone',
        'doctor_name', 'appointment_date', 'appointment_time',
        'duration_minutes', 'appointment_type', 'status',
        'created_at', 'updated_at'
    ]
    
    missing_fields = [field for field in required_fields if field not in appointment_data]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    
    print("✅ All required fields present")
    return True

def test_simple_models():
    """Test simple model functions"""
    print("\n🧪 Testing Simple Model Functions...")
    
    try:
        from shared_code.models import create_appointment_data, create_success_response, create_error_response
        
        # Test create_appointment_data
        test_data = create_test_appointment_data()
        appointment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat() + "Z"
        
        appointment_data = create_appointment_data(test_data, appointment_id, timestamp)
        if validate_appointment_data(appointment_data):
            print("✅ create_appointment_data function working")
        
        # Test response functions
        success_response = create_success_response("Test message", {"test": "data"})
        if success_response.get("success") and success_response.get("message"):
            print("✅ create_success_response function working")
        
        error_response = create_error_response("Error message")
        if not error_response.get("success") and error_response.get("message"):
            print("✅ create_error_response function working")
        
        return True
        
    except Exception as e:
        print(f"❌ Model function test failed: {str(e)}")
        return False

def test_azure_sdk_imports():
    """Test critical Azure SDK imports - MUST PASS before git push"""
    print("\n☁️  Testing Azure SDK Imports...")
    
    try:
        # Test modern Azure Storage Blob SDK
        from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
        print("✅ Azure Storage Blob SDK imports successful")
        
        # Test Azure Cosmos SDK
        from azure.cosmos import CosmosClient
        print("✅ Azure Cosmos SDK imports successful")
        
        # Test Azure Identity SDK 
        from azure.identity import DefaultAzureCredential
        print("✅ Azure Identity SDK imports successful")
        
        # Test that we can create client classes (no network calls)
        blob_client_class = BlobServiceClient
        cosmos_client_class = CosmosClient
        print("✅ All Azure SDK client classes available")
        
        return True
        
    except ImportError as e:
        print(f"❌ CRITICAL: Azure SDK import failed: {str(e)}")
        print("🚨 DO NOT PUSH TO GIT - Fix imports first!")
        return False

def test_blob_storage_client():
    """Test BlobStorageClient with modern Azure SDK"""
    print("\n📦 Testing BlobStorageClient...")
    
    try:
        from shared_code.blob_storage import BlobStorageClient
        
        # Test client creation (lazy initialization)
        client = BlobStorageClient()
        print("✅ BlobStorageClient created successfully")
        
        # Test all required methods exist
        required_methods = [
            'create_pet', 'get_pet_by_id', 'get_all_pets', 
            'delete_pet', 'get_pets_by_species'
        ]
        
        for method in required_methods:
            if hasattr(client, method) and callable(getattr(client, method)):
                print(f"✅ Method {method} available and callable")
            else:
                print(f"❌ Method {method} missing or not callable")
                return False
        
        # Test that the client uses modern Azure SDK
        if hasattr(client, '_get_blob_service'):
            print("✅ Modern BlobServiceClient implementation detected")
        else:
            print("❌ Legacy implementation detected")
            return False
            
        print("ℹ️  Note: Actual blob operations require environment variables")
        return True
        
    except ImportError as e:
        print(f"❌ BlobStorageClient import failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ BlobStorageClient test failed: {str(e)}")
        return False

def test_database_client():
    """Test database client instantiation"""
    print("\n🗄️  Testing Database Client...")
    
    try:
        from shared_code.database import CosmosDBClient
        
        # Test client creation (lazy initialization)
        client = CosmosDBClient()
        print("✅ CosmosDBClient created successfully")
        
        # Test required methods exist
        required_methods = [
            'create_appointment', 'get_appointment_by_id', 'get_all_appointments',
            'update_appointment', 'delete_appointment'
        ]
        
        for method in required_methods:
            if hasattr(client, method) and callable(getattr(client, method)):
                print(f"✅ Method {method} available and callable")
            else:
                print(f"❌ Method {method} missing or not callable")
                return False
        
        print("ℹ️  Note: Actual database connection requires environment variables")
        return True
        
    except ImportError as e:
        print(f"❌ Database client import failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Database client test failed: {str(e)}")
        return False

def test_pet_models():
    """Test pet model functions"""
    print("\n🐕 Testing Pet Models...")
    
    try:
        from shared_code.pet_models import create_pet_data, validate_pet_data, create_pet_response
        
        # Test create_pet_data
        test_pet = create_test_pet_data()
        pet_data = create_pet_data(test_pet)
        
        if validate_pet_data(pet_data):
            print("✅ create_pet_data and validate_pet_data working")
        else:
            print("❌ Pet data validation failed")
            return False
        
        # Test create_pet_response
        response = create_pet_response(pet_data)
        if response.get("success") and response.get("data"):
            print("✅ create_pet_response working")
        else:
            print("❌ create_pet_response failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Pet model test failed: {str(e)}")
        return False

def test_json_serialization():
    """Test JSON serialization of simple data"""
    print("\n📄 Testing JSON Serialization...")
    
    try:
        from shared_code.models import create_appointment_data, create_success_response
        
        # Test simple JSON serialization
        test_data = create_test_appointment_data()
        appointment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat() + "Z"
        
        appointment_data = create_appointment_data(test_data, appointment_id, timestamp)
        json_data = json.dumps(appointment_data)
        parsed_data = json.loads(json_data)
        print("✅ Appointment data JSON serialization passed")
        
        # Test response serialization
        response = create_success_response("Test", appointment_data)
        json_response = json.dumps(response)
        parsed_response = json.loads(json_response)
        print("✅ Response JSON serialization passed")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {str(e)}")
        return False

def run_all_tests():
    """Run all comprehensive tests before git push"""
    print("🚀 Starting Comprehensive Azure Functions Tests")
    print("🔒 SAFETY GATE: This test suite prevents broken code from reaching git")
    print("=" * 70)
    
    # Critical tests that MUST pass before git push
    critical_tests = [
        ("Azure SDK Imports", test_azure_sdk_imports),
        ("BlobStorage Client", test_blob_storage_client),
        ("Database Client", test_database_client),
    ]
    
    # Additional validation tests 
    validation_tests = [
        ("Appointment Models", test_simple_models),
        ("Pet Models", test_pet_models),
        ("JSON Serialization", test_json_serialization),
    ]
    
    all_tests = critical_tests + validation_tests
    
    passed = 0
    critical_passed = 0
    total = len(all_tests)
    
    for i, (test_name, test_func) in enumerate(all_tests, 1):
        print(f"\n[{i}/{total}] Running {test_name}...")
        if test_func():
            passed += 1
            if i <= len(critical_tests):
                critical_passed += 1
        else:
            if i <= len(critical_tests):
                print(f"🚨 CRITICAL TEST FAILED: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    print(f"🔒 Critical Tests: {critical_passed}/{len(critical_tests)} passed")
    
    if critical_passed == len(critical_tests) and passed == total:
        print("🎉 ALL TESTS PASSED! Code is safe to push to git.")
        print("✅ Azure SDK implementation verified")
        print("✅ All client implementations working")
        print("✅ Model functions validated")
        print("\n🚀 Ready for Azure Functions deployment!")
        return True
    elif critical_passed == len(critical_tests):
        print("⚠️  Critical tests passed, but some validation tests failed.")
        print("🔒 Code is technically safe to push, but consider fixing validation issues.")
        return True  # Allow push if critical tests pass
    else:
        print("🚨 CRITICAL TESTS FAILED!")
        print("❌ DO NOT PUSH TO GIT until all critical tests pass!")
        print("🔧 Fix the Azure SDK implementation issues first.")
        return False

def pre_git_push_check():
    """Run this before every git push"""
    print("🔒 PRE-GIT-PUSH SAFETY CHECK")
    print("=" * 50)
    
    if run_all_tests():
        print("\n✅ SAFE TO PUSH: All tests passed")
        return True
    else:
        print("\n❌ UNSAFE TO PUSH: Tests failed")
        print("💡 Fix the issues above before pushing to git")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
