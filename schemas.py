"""
Database Schemas for Hospital Management

Each Pydantic model maps to a MongoDB collection using the lowercase
class name as the collection name (e.g., Appointment -> "appointment").
"""
from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class Patient(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80, description="Patient first name")
    last_name: str = Field(..., min_length=1, max_length=80, description="Patient last name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, min_length=7, max_length=20, description="Contact phone")
    dob: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    blood_group: Optional[str] = Field(None, description="Blood group e.g., O+, A-")


class Doctor(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    department: str = Field(..., min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    on_duty: bool = Field(True, description="Whether the doctor is currently on duty")


class Appointment(BaseModel):
    name: str = Field(..., min_length=1, max_length=160, description="Patient full name (quick booking)")
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=20)
    department: str = Field(..., min_length=2, max_length=120)
    date: str = Field(..., description="Preferred date YYYY-MM-DD")
    notes: Optional[str] = Field(None, max_length=500)
    status: str = Field("requested", description="requested|confirmed|completed|cancelled")
    created_for: Optional[datetime] = Field(None, description="Planned datetime if allocated")
