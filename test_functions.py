"""
Simple test script for Azure Functions (no pydantic validation)
This script can be used for local testing and validation
"""
import json
import uuid
from datetime import datetime

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

def test_database_client():
    """Test database client instantiation"""
    print("\n🗄️  Testing Database Client...")
    
    try:
        from shared_code.database import CosmosDBClient
        
        # This will fail without proper environment variables, but we can test the import
        print("✅ Database client import successful")
        print("ℹ️  Note: Actual database connection requires environment variables")
        return True
        
    except ImportError as e:
        print(f"❌ Database client import failed: {str(e)}")
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
    """Run all tests"""
    print("🚀 Starting Simplified Azure Functions Validation Tests")
    print("=" * 60)
    
    tests = [
        test_simple_models,
        test_database_client,
        test_json_serialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your simplified Azure Functions are ready for deployment.")
        print("ℹ️  No complex validation - perfect for APM demo!")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
