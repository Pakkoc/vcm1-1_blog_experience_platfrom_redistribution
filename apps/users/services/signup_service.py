"""
Service for user signup business logic.
"""

from django.db import transaction
from django.contrib.auth import get_user_model
from typing import Optional

from apps.common.services.base import BaseService
from apps.common.exceptions import DuplicateActionException
from ..dto import SignupDTO
from ..models import AdvertiserProfile, InfluencerProfile

User = get_user_model()


class SignupService(BaseService[SignupDTO, User]):
    """
    Service for handling user signup.

    Creates a new user and associated profile based on role.
    Uses transaction to ensure data consistency.
    """

    @transaction.atomic
    def execute(self, dto: SignupDTO, user: Optional[object] = None) -> User:
        """
        Execute user signup.

        Args:
            dto: SignupDTO containing user data
            user: Not used in this service (signup doesn't require authentication)

        Returns:
            Created User instance

        Raises:
            DuplicateActionException: If email or contact already exists
            ValueError: If required role-specific fields are missing
        """
        # 1. Check for duplicates (additional safety layer)
        if User.objects.filter(email=dto.email).exists():
            raise DuplicateActionException("이미 가입된 이메일입니다.")

        if User.objects.filter(contact=dto.contact).exists():
            raise DuplicateActionException("이미 가입된 연락처입니다.")

        # 2. Create User
        new_user = User.objects.create_user(
            email=dto.email,
            password=dto.password,
            name=dto.name,
            contact=dto.contact,
            role=dto.role
        )

        # 3. Create role-specific Profile
        if dto.role == 'advertiser':
            if not dto.company_name or not dto.business_registration_number:
                raise ValueError("광고주는 업체명과 사업자등록번호가 필요합니다.")

            AdvertiserProfile.objects.create(
                user=new_user,
                company_name=dto.company_name,
                business_registration_number=dto.business_registration_number
            )

        elif dto.role == 'influencer':
            if not dto.birth_date or not dto.sns_link:
                raise ValueError("인플루언서는 생년월일과 SNS 링크가 필요합니다.")

            InfluencerProfile.objects.create(
                user=new_user,
                birth_date=dto.birth_date,
                sns_link=dto.sns_link
            )

        return new_user
