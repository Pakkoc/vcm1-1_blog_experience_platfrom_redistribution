"""
Common pytest fixtures for all apps.
"""

import pytest
from datetime import date, timedelta
from django.test import Client
from apps.users.models import User, AdvertiserProfile
from apps.campaigns.models import Campaign


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def advertiser_user(db):
    """Advertiser user fixture"""
    user = User.objects.create_user(
        email='advertiser@test.com',
        password='testpass123',
        name='Test Advertiser',
        contact='010-1234-5678',
        role='advertiser'
    )
    # Create advertiser profile
    AdvertiserProfile.objects.create(
        user=user,
        company_name='Test Company',
        business_registration_number='123-45-67890'
    )
    return user


@pytest.fixture
def influencer_user(db):
    """Influencer user fixture"""
    user = User.objects.create_user(
        email='influencer@test.com',
        password='testpass123',
        name='Test Influencer',
        contact='010-9876-5432',
        role='influencer'
    )
    return user


@pytest.fixture
def campaign_factory(db, advertiser_user):
    """Factory fixture for creating campaigns"""
    def create_campaign(**kwargs):
        defaults = {
            'advertiser': advertiser_user,
            'name': 'Test Campaign',
            'recruitment_start_date': date.today(),
            'recruitment_end_date': date.today() + timedelta(days=7),
            'recruitment_count': 10,
            'benefits': 'Free product',
            'mission': 'Write a review',
            'status': 'recruiting',
        }
        defaults.update(kwargs)
        return Campaign.objects.create(**defaults)
    return create_campaign
