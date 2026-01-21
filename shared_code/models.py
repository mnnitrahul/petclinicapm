"""
Pydantic models for appointment management
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class CreateAppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=100)
    patient_email: str = Field(..., min_length=5, max_length=100)
    patient_phone: str = Field(..., min_length=10, max_length=15)
    doctor_name: str = Field(..., min_length=2, max_length=100)
    appointment_date: str = Field(..., description="YYYY-MM-DD format")
    appointment_time: str = Field(..., description="HH:MM format (24-hour)")
    duration_minutes: int = Field(default=30, ge=15, le=240)
    appointment_type: str = Field(..., min_length=3, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class Appointment(BaseModel):
    id: str = Field(..., description="Unique appointment ID")
    patient_name: str
    patient_email: str
    patient_phone: str
    doctor_name: str
    appointment_date: str
    appointment_time: str
    duration_minutes: int
    appointment_type: str
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        use_enum_values = True


class AppointmentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Appointment] = None


class AppointmentListResponse(BaseModel):
    success: bool
    message: str
    data: Optional[List[Appointment]] = None
    count: int = 0
