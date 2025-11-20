"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Domain schemas for the booking app

class Sport(BaseModel):
    """
    Sports collection schema
    Collection name: "sport"
    """
    key: str = Field(..., description="Unique key, e.g., futsal, minisoccer, badminton")
    name: str = Field(..., description="Display name")
    courts: int = Field(..., ge=1, description="Number of available courts for this sport")
    price_per_hour: int = Field(..., ge=0, description="Price per hour in IDR")
    open_hour: int = Field(8, ge=0, le=23, description="Opening hour (24h format)")
    close_hour: int = Field(22, ge=1, le=24, description="Closing hour (24h format)")

class Booking(BaseModel):
    """
    Bookings collection schema
    Collection name: "booking"
    """
    customer_name: str = Field(..., description="Customer full name")
    phone: str = Field(..., description="WhatsApp/phone number")
    sport: str = Field(..., description="Sport key: futsal | minisoccer | badminton")
    court: int = Field(..., ge=1, description="Court number")
    date: str = Field(..., description="Booking date in YYYY-MM-DD")
    start_time: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):00$", description="Start time HH:00")
    end_time: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):00$", description="End time HH:00")
    status: str = Field("confirmed", description="Booking status")
    notes: Optional[str] = Field(None, description="Optional notes")
    total_price: Optional[int] = Field(None, ge=0, description="Computed total price in IDR")

# Example schemas kept for reference (not used by the app directly)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
