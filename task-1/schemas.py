import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class EducationItem(BaseModel):
    institution: Optional[str] = Field(default=None, description="University, college, or school name")
    degree: Optional[str] = Field(default=None, description="Degree or qualification earned")
    graduation_year: Optional[str] = Field(default=None, description="Year or date of graduation")


class WorkExperienceItem(BaseModel):
    company: Optional[str] = Field(default=None, description="Company or organization name")
    role: Optional[str] = Field(default=None, description="Job title or role")
    duration: Optional[str] = Field(default=None, description="Employment period")
    responsibilities: List[str] = Field(default_factory=list, description="Key duties or achievements")


class Resume(BaseModel):
    full_name: Optional[str] = Field(default=None, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="List of skills and tools")
    education: List[EducationItem] = Field(default_factory=list, description="Education history")
    work_experience: List[WorkExperienceItem] = Field(default_factory=list, description="Job experience history")
    years_of_experience: Optional[float] = Field(default=None, description="Total years of work experience")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
                raise ValueError(f"Invalid email format: '{v}'")
        return v

    @field_validator("years_of_experience")
    @classmethod
    def validate_experience(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"years_of_experience cannot be negative: {v}")
        return v


class InvoiceItem(BaseModel):
    description: Optional[str] = Field(default=None, description="Item or service description")
    quantity: Optional[float] = Field(default=None, description="Number of units")
    unit_price: Optional[float] = Field(default=None, description="Price per unit")
    total_amount: Optional[float] = Field(default=None, description="Total price for this line item")

    @field_validator("quantity", "unit_price", "total_amount")
    @classmethod
    def validate_non_negative_item(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"Item quantity/price cannot be negative: {v}")
        return v


class Invoice(BaseModel):
    invoice_number: Optional[str] = Field(default=None, description="Invoice or reference number")
    vendor_name: Optional[str] = Field(default=None, description="Vendor or seller name")
    invoice_date: Optional[str] = Field(default=None, description="Invoice date")
    currency: Optional[str] = Field(default=None, description="Currency code or symbol (USD, EUR, etc.)")
    items: List[InvoiceItem] = Field(default_factory=list, description="List of line items")
    quantity: Optional[float] = Field(default=None, description="Total quantity of items")
    unit_price: Optional[float] = Field(default=None, description="Unit price (if single item)")
    total_amount: Optional[float] = Field(default=None, description="Grand total invoice amount")

    @field_validator("quantity", "unit_price", "total_amount")
    @classmethod
    def validate_non_negative_invoice(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"Invoice amount/quantity cannot be negative: {v}")
        return v

    @model_validator(mode="after")
    def populate_quantity_and_unit_price(self) -> "Invoice":
        # Fall back to item values if top-level fields are missing
        if self.items:
            if self.quantity is None:
                if len(self.items) == 1 and self.items[0].quantity is not None:
                    self.quantity = self.items[0].quantity
                elif all(item.quantity is not None for item in self.items):
                    self.quantity = sum(item.quantity for item in self.items if item.quantity is not None)

            if self.unit_price is None and len(self.items) == 1 and self.items[0].unit_price is not None:
                self.unit_price = self.items[0].unit_price

        return self
