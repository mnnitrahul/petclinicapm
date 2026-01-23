"""
Pet data models and validation utilities
"""
from datetime import datetime, timezone
from typing import Dict, Any


def create_pet_data(request_data: Dict[str, Any], pet_id: str, current_timestamp: str) -> Dict[str, Any]:
    """Create structured pet data from request"""
    return {
        "id": pet_id,
        "name": request_data.get("name"),
        "species": request_data.get("species"),
        "breed": request_data.get("breed", ""),
        "age": request_data.get("age"),
        "color": request_data.get("color", ""),
        "weight": request_data.get("weight"),
        "owner_name": request_data.get("owner_name"),
        "owner_email": request_data.get("owner_email"),
        "owner_phone": request_data.get("owner_phone"),
        "medical_notes": request_data.get("medical_notes", ""),
        "created_at": current_timestamp,
        "updated_at": current_timestamp
    }


def validate_required_pet_fields(data: Dict[str, Any]) -> list:
    """Validate required fields for pet creation"""
    required_fields = [
        "name", "species", "age", "owner_name", "owner_email", "owner_phone"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not data.get(field):
            missing_fields.append(field)
    
    return missing_fields


def validate_pet_data_types(data: Dict[str, Any]) -> list:
    """Validate data types for pet fields"""
    validation_errors = []
    
    # Age should be a positive integer
    age = data.get("age")
    if age is not None:
        try:
            age_int = int(age)
            if age_int < 0:
                validation_errors.append("Age must be a positive number")
        except (ValueError, TypeError):
            validation_errors.append("Age must be a valid number")
    
    # Weight should be a positive number (optional)
    weight = data.get("weight")
    if weight is not None and weight != "":
        try:
            weight_float = float(weight)
            if weight_float < 0:
                validation_errors.append("Weight must be a positive number")
        except (ValueError, TypeError):
            validation_errors.append("Weight must be a valid number")
    
    # Email validation (basic)
    email = data.get("owner_email")
    if email and "@" not in email:
        validation_errors.append("Owner email must be a valid email address")
    
    # Name length validation
    name = data.get("name")
    if name and len(name) > 100:
        validation_errors.append("Pet name must be 100 characters or less")
    
    # Species validation (common pets)
    species = data.get("species")
    if species:
        valid_species = ["dog", "cat", "bird", "fish", "rabbit", "hamster", "guinea pig", "reptile", "other"]
        if species.lower() not in valid_species:
            # Don't error, just log a note
            pass
    
    return validation_errors


def validate_email_format(email: str) -> bool:
    """Basic email format validation"""
    if not email:
        return False
    return "@" in email and "." in email.split("@")[1]
