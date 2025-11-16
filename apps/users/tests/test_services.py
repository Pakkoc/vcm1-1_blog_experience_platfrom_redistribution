"""
Test cases for user services following TDD approach.
"""

import pytest
from datetime import date
from django.db import IntegrityError, transaction
from apps.users.models import User, AdvertiserProfile, InfluencerProfile
from apps.users.dto import SignupDTO
from apps.users.services.signup_service import SignupService
from apps.common.exceptions import DuplicateActionException


@pytest.mark.django_db
class TestSignupService:
    """Test cases for SignupService"""

    def test_signup_service_creates_influencer_user_and_profile(self):
        """SignupService should create influencer user and profile"""
        dto = SignupDTO(
            email='influencer@test.com',
            password='Password123',
            name='인플루언서',
            contact='010-1234-5678',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://blog.naver.com/test'
        )

        service = SignupService()
        user = service.execute(dto)

        assert user.email == 'influencer@test.com'
        assert user.name == '인플루언서'
        assert user.contact == '010-1234-5678'
        assert user.role == 'influencer'
        assert user.check_password('Password123')

        # Check profile is created
        assert hasattr(user, 'influencer_profile')
        profile = user.influencer_profile
        assert profile.birth_date == date(1990, 1, 1)
        assert profile.sns_link == 'https://blog.naver.com/test'

    def test_signup_service_creates_advertiser_user_and_profile(self):
        """SignupService should create advertiser user and profile"""
        dto = SignupDTO(
            email='advertiser@test.com',
            password='Password123',
            name='광고주',
            contact='010-9999-8888',
            role='advertiser',
            company_name='테스트 회사',
            business_registration_number='123-45-67890'
        )

        service = SignupService()
        user = service.execute(dto)

        assert user.email == 'advertiser@test.com'
        assert user.name == '광고주'
        assert user.contact == '010-9999-8888'
        assert user.role == 'advertiser'
        assert user.check_password('Password123')

        # Check profile is created
        assert hasattr(user, 'advertiser_profile')
        profile = user.advertiser_profile
        assert profile.company_name == '테스트 회사'
        assert profile.business_registration_number == '123-45-67890'

    def test_signup_service_with_duplicate_email_raises_exception(self):
        """SignupService should raise DuplicateActionException for duplicate email"""
        User.objects.create_user(
            email='existing@test.com',
            password='testpass123',
            name='Existing User',
            contact='010-0000-0000',
            role='influencer'
        )

        dto = SignupDTO(
            email='existing@test.com',
            password='Password123',
            name='New User',
            contact='010-1111-1111',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://test.com'
        )

        service = SignupService()
        with pytest.raises(DuplicateActionException) as exc_info:
            service.execute(dto)

        assert '이메일' in str(exc_info.value)

    def test_signup_service_with_duplicate_contact_raises_exception(self):
        """SignupService should raise DuplicateActionException for duplicate contact"""
        User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            name='User 1',
            contact='010-1234-5678',
            role='influencer'
        )

        dto = SignupDTO(
            email='user2@test.com',
            password='Password123',
            name='User 2',
            contact='010-1234-5678',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://test.com'
        )

        service = SignupService()
        with pytest.raises(DuplicateActionException) as exc_info:
            service.execute(dto)

        assert '연락처' in str(exc_info.value)

    def test_signup_service_transaction_rollback_on_profile_error(self):
        """SignupService should rollback user creation if profile creation fails"""
        # Create DTO with invalid data that will cause profile creation to fail
        dto = SignupDTO(
            email='test@test.com',
            password='Password123',
            name='테스트',
            contact='010-1234-5678',
            role='advertiser',
            company_name=None,  # This will cause an error
            business_registration_number=None
        )

        service = SignupService()

        # Expect an exception to be raised
        with pytest.raises(Exception):
            service.execute(dto)

        # Verify that User was NOT created (transaction rolled back)
        assert not User.objects.filter(email='test@test.com').exists()

    def test_signup_service_password_is_hashed(self):
        """SignupService should hash the password"""
        dto = SignupDTO(
            email='test@test.com',
            password='PlainPassword123',
            name='테스트',
            contact='010-1234-5678',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://test.com'
        )

        service = SignupService()
        user = service.execute(dto)

        # Password should be hashed, not stored as plain text
        assert user.password != 'PlainPassword123'
        # But check_password should work
        assert user.check_password('PlainPassword123')

    def test_signup_service_returns_user_object(self):
        """SignupService should return User object"""
        dto = SignupDTO(
            email='test@test.com',
            password='Password123',
            name='테스트',
            contact='010-1234-5678',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://test.com'
        )

        service = SignupService()
        user = service.execute(dto)

        assert isinstance(user, User)
        assert user.id is not None
        assert user.pk is not None
