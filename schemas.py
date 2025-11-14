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

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Real Estate specific schemas

class Property(BaseModel):
    """
    Properties collection schema
    Collection name: "property"
    """
    title: str = Field(..., description="Listing title")
    location: str = Field(..., description="District and city, e.g., Miraflores, Lima")
    price_usd: float = Field(..., ge=0, description="Price in USD")
    beds: Optional[int] = Field(None, ge=0)
    baths: Optional[float] = Field(None, ge=0)
    area_m2: Optional[float] = Field(None, ge=0, description="Built area in square meters")
    type: Optional[str] = Field(None, description="Apartment, House, Penthouse, Lot, etc.")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    featured: bool = Field(default=False, description="Show in featured section")
    description: Optional[str] = Field(None, description="Short description")
    views: Optional[int] = Field(0, ge=0, description="View counter for analytics")

class Inquiry(BaseModel):
    """
    Inquiries collection schema
    Collection name: "inquiry"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="WhatsApp or phone number")
    message: str = Field(..., description="Message from prospect")
    property_id: Optional[str] = Field(None, description="Related property ObjectId as string")
