"""
Pytest fixtures for campaigns tests.
"""

import pytest
from django.utils import timezone
from datetime import date, timedelta
from apps.campaigns.models import Campaign
from apps.proposals.models import Proposal
from apps.users.models import User


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
    return user


@pytest.fixture
def other_advertiser_user(db):
    """Another advertiser user fixture"""
    user = User.objects.create_user(
        email='other_advertiser@test.com',
        password='testpass123',
        name='Other Advertiser',
        contact='010-9999-8888',
        role='advertiser'
    )
    return user


@pytest.fixture
def influencer_users(db):
    """Multiple influencer users fixture"""
    users = []
    for i in range(10):
        user = User.objects.create_user(
            email=f'influencer{i}@test.com',
            password='testpass123',
            name=f'Influencer {i}',
            contact=f'010-{i:04d}-0000',
            role='influencer'
        )
        # Create influencer profile
        from apps.users.models import InfluencerProfile
        InfluencerProfile.objects.create(
            user=user,
            birth_date=date(1990, 1, 1),
            sns_link=f'https://instagram.com/influencer{i}'
        )
        users.append(user)
    return users


@pytest.fixture
def recruiting_campaign(advertiser_user):
    """Campaign in recruiting status"""
    return Campaign.objects.create(
        advertiser=advertiser_user,
        name='Test Campaign',
        recruitment_start_date=date.today(),
        recruitment_end_date=date.today() + timedelta(days=7),
        recruitment_count=5,
        benefits='Test benefits',
        mission='Test mission',
        status='recruiting'
    )


@pytest.fixture
def ended_campaign(advertiser_user):
    """Campaign in recruitment_ended status"""
    return Campaign.objects.create(
        advertiser=advertiser_user,
        name='Ended Campaign',
        recruitment_start_date=date.today() - timedelta(days=7),
        recruitment_end_date=date.today(),
        recruitment_count=5,
        benefits='Test benefits',
        mission='Test mission',
        status='recruitment_ended'
    )


@pytest.fixture
def ended_campaign_with_proposals(advertiser_user, influencer_users):
    """Campaign with proposals in recruitment_ended status"""
    campaign = Campaign.objects.create(
        advertiser=advertiser_user,
        name='Campaign with Proposals',
        recruitment_start_date=date.today() - timedelta(days=7),
        recruitment_end_date=date.today(),
        recruitment_count=5,
        benefits='Test benefits',
        mission='Test mission',
        status='recruitment_ended'
    )

    # Create 10 proposals
    for i, influencer in enumerate(influencer_users):
        Proposal.objects.create(
            campaign=campaign,
            influencer=influencer,
            cover_letter=f'Cover letter {i}',
            desired_visit_date=date.today() + timedelta(days=i),
            status='submitted'
        )

    return campaign
