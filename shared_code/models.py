"""
Simple data models for appointment management
"""

# Simple appointment statuses
APPOINTMENT_STATUSES = [
    "scheduled",
    "confirmed", 
    "completed",
    "cancelled",
    "no_show"
]

def create_appointment_data(request_data, appointment_id, timestamp):
    """Create appointment data from request"""
    return {
        "id": appointment_id,
        "patient_name": request_data.get("patient_name", ""),
        "patient_email": request_data.get("patient_email", ""),
        "patient_phone": request_data.get("patient_phone", ""),
        "doctor_name": request_data.get("doctor_name", ""),
        "appointment_date": request_data.get("appointment_date", ""),
        "appointment_time": request_data.get("appointment_time", ""),
        "duration_minutes": request_data.get("duration_minutes", 30),
        "appointment_type": request_data.get("appointment_type", ""),
        "status": "scheduled",
        "notes": request_data.get("notes", ""),
        "created_at": timestamp,
        "updated_at": timestamp
    }

def create_success_response(message, data=None):
    """Create success response"""
    response = {
        "success": True,
        "message": message
    }
    if data:
        response["data"] = data
    return response

def create_error_response(message):
    """Create error response"""
    return {
        "success": False,
        "message": message
    }

def create_list_response(message, data, count):
    """Create list response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "count": count
    }
