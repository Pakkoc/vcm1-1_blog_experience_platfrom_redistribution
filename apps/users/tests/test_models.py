"""
Test cases for User model following TDD approach.
"""

import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.users.models import User, AdvertiserProfile, InfluencerProfile


@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model"""

    def test_create_user_with_valid_data_succeeds(self):
        """Valid user creation should succeed"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            contact='010-1234-5678',
            role='influencer'
        )

        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.contact == '010-1234-5678'
        assert user.role == 'influencer'
        assert user.check_password('testpass123')
        assert user.is_active is True

    def test_create_user_with_duplicate_email_raises_integrity_error(self):
        """Creating user with duplicate email should raise IntegrityError"""
        User.objects.create_user(
            email='duplicate@example.com',
            password='testpass123',
            name='First User',
            contact='010-1111-1111',
            role='influencer'
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='duplicate@example.com',
                password='testpass123',
                name='Second User',
                contact='010-2222-2222',
                role='influencer'
            )

    def test_create_user_with_duplicate_contact_raises_integrity_error(self):
        """Creating user with duplicate contact should raise IntegrityError"""
        User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='First User',
            contact='010-1234-5678',
            role='influencer'
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='user2@example.com',
                password='testpass123',
                name='Second User',
                contact='010-1234-5678',
                role='influencer'
            )

    def test_create_advertiser_user(self):
        """Creating advertiser user should work"""
        user = User.objects.create_user(
            email='advertiser@example.com',
            password='testpass123',
            name='Advertiser User',
            contact='010-9999-9999',
            role='advertiser'
        )

        assert user.role == 'advertiser'

    def test_user_str_returns_email(self):
        """User __str__ should return email"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            contact='010-1234-5678',
            role='influencer'
        )

        assert str(user) == 'test@example.com'

    def test_email_is_normalized(self):
        """Email should be normalized"""
        user = User.objects.create_user(
            email='Test@EXAMPLE.COM',
            password='testpass123',
            name='Test User',
            contact='010-1234-5678',
            role='influencer'
        )

        assert user.email == 'Test@example.com'


@pytest.mark.django_db
class TestAdvertiserProfile:
    """Test cases for AdvertiserProfile model"""

    def test_create_advertiser_profile(self):
        """Creating advertiser profile should succeed"""
        user = User.objects.create_user(
            email='advertiser@example.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        profile = AdvertiserProfile.objects.create(
            user=user,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        assert profile.user == user
        assert profile.company_name == 'Test Company'
        assert profile.business_registration_number == '123-45-67890'

    def test_advertiser_profile_str(self):
        """AdvertiserProfile __str__ should return company name"""
        user = User.objects.create_user(
            email='advertiser@example.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        profile = AdvertiserProfile.objects.create(
            user=user,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        assert str(profile) == 'Test Company'


@pytest.mark.django_db
class TestInfluencerProfile:
    """Test cases for InfluencerProfile model"""

    def test_create_influencer_profile(self):
        """Creating influencer profile should succeed"""
        user = User.objects.create_user(
            email='influencer@example.com',
            password='testpass123',
            name='Influencer',
            contact='010-1234-5678',
            role='influencer'
        )

        from datetime import date
        profile = InfluencerProfile.objects.create(
            user=user,
            birth_date=date(1990, 1, 1),
            sns_link='https://instagram.com/testuser'
        )

        assert profile.user == user
        assert profile.birth_date == date(1990, 1, 1)
        assert profile.sns_link == 'https://instagram.com/testuser'

    def test_influencer_profile_str(self):
        """InfluencerProfile __str__ should return user name"""
        user = User.objects.create_user(
            email='influencer@example.com',
            password='testpass123',
            name='Influencer',
            contact='010-1234-5678',
            role='influencer'
        )

        from datetime import date
        profile = InfluencerProfile.objects.create(
            user=user,
            birth_date=date(1990, 1, 1),
            sns_link='https://instagram.com/testuser'
        )

        assert str(profile) == 'Influencer'
