"""
Data Transfer Objects for user operations.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from apps.common.dto.base import BaseDTO


@dataclass(frozen=True)
class SignupDTO(BaseDTO):
    """
    Data transfer object for user signup.

    Immutable object containing all necessary data for user registration.
    """
    # Common fields
    email: str
    password: str
    name: str
    contact: str
    role: str  # 'advertiser' or 'influencer'

    # Advertiser-specific fields (Optional)
    company_name: Optional[str] = None
    business_registration_number: Optional[str] = None

    # Influencer-specific fields (Optional)
    birth_date: Optional[date] = None
    sns_link: Optional[str] = None
