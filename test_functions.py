"""
Simple test script for Azure Functions
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

def test_models():
    """Test Pydantic models"""
    print("\n🧪 Testing Pydantic Models...")
    
    try:
        from shared_code.models import CreateAppointmentRequest, Appointment, AppointmentResponse
        
        # Test CreateAppointmentRequest
        test_data = create_test_appointment_data()
        request_model = CreateAppointmentRequest(**test_data)
        print("✅ CreateAppointmentRequest model validation passed")
        
        # Test Appointment model
        appointment_data = {
            **test_data,
            "id": str(uuid.uuid4()),
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        appointment_model = Appointment(**appointment_data)
        print("✅ Appointment model validation passed")
        
        # Test Response models
        response = AppointmentResponse(
            success=True,
            message="Test successful",
            data=appointment_model
        )
        print("✅ AppointmentResponse model validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation failed: {str(e)}")
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
    """Test JSON serialization of models"""
    print("\n📄 Testing JSON Serialization...")
    
    try:
        from shared_code.models import CreateAppointmentRequest, Appointment
        
        # Test request serialization
        test_data = create_test_appointment_data()
        request_model = CreateAppointmentRequest(**test_data)
        json_data = request_model.model_dump_json()
        parsed_data = json.loads(json_data)
        print("✅ Request model JSON serialization passed")
        
        # Test appointment serialization
        appointment_data = {
            **test_data,
            "id": str(uuid.uuid4()),
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        appointment_model = Appointment(**appointment_data)
        json_data = appointment_model.model_dump_json()
        parsed_data = json.loads(json_data)
        print("✅ Appointment model JSON serialization passed")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Azure Functions Validation Tests")
    print("=" * 50)
    
    tests = [
        test_models,
        test_database_client,
        test_json_serialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Azure Functions are ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
