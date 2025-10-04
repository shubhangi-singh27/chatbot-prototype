from pydantic import BaseModel, Field, EmailStr, field_validator
import phonenumbers
from typing import Optional

class Customer(BaseModel):
    id: str = Field(..., alias="_id")
    phone_number: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

    @field_validator("phone_number", mode="before")
    def validate_phone_number(cls, v: str) -> str:
        """
        Validate and normalize phone numbers to E.164 (e.g., +919876543210).
        Raises ValueError if invalid.
        """
        try:
            parsed = phonenumbers.parse(v, "IN")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Invalid phone number format")