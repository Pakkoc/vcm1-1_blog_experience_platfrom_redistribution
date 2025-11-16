"""
Unit tests for proposal services.
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model

from apps.proposals.services.proposal_service import ProposalCreationService
from apps.proposals.dto import ProposalCreateDTO
from apps.proposals.models import Proposal
from apps.campaigns.models import Campaign
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    DuplicateActionException
)

User = get_user_model()


@pytest.mark.django_db
class TestProposalCreationService:
    """Test ProposalCreationService"""

    def test_create_proposal_success(self, influencer_user, db):
        """Test successful proposal creation"""
        # Create a campaign
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        today = date.today()
        campaign = Campaign.objects.create(
            advertiser=advertiser,
            name='Test Campaign',
            recruitment_start_date=today,
            recruitment_end_date=today + timedelta(days=7),
            recruitment_count=10,
            benefits='Free product',
            mission='Write a review',
            status='recruiting'
        )

        # Create DTO
        dto = ProposalCreateDTO(
            campaign_id=campaign.id,
            influencer_id=influencer_user.id,
            cover_letter='I want to participate!',
            desired_visit_date=today + timedelta(days=3)
        )

        # Execute service
        service = ProposalCreationService()
        proposal = service.execute(dto, user=influencer_user)

        # Assert
        assert proposal.id is not None
        assert proposal.campaign == campaign
        assert proposal.influencer == influencer_user
        assert proposal.cover_letter == 'I want to participate!'
        assert proposal.status == 'submitted'

    def test_create_proposal_unauthenticated_user(self, db):
        """Test that unauthenticated user cannot create proposal"""
        dto = ProposalCreateDTO(
            campaign_id=1,
            influencer_id=1,
            cover_letter='Test',
            desired_visit_date=date.today()
        )

        service = ProposalCreationService()

        with pytest.raises(PermissionDeniedException) as exc_info:
            service.execute(dto, user=None)

        assert "must be authenticated" in str(exc_info.value)

    def test_create_proposal_advertiser_user(self, db):
        """Test that advertiser cannot create proposal"""
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        dto = ProposalCreateDTO(
            campaign_id=1,
            influencer_id=advertiser.id,
            cover_letter='Test',
            desired_visit_date=date.today()
        )

        service = ProposalCreationService()

        with pytest.raises(PermissionDeniedException) as exc_info:
            service.execute(dto, user=advertiser)

        assert "Only influencers" in str(exc_info.value)

    def test_create_proposal_campaign_not_exist(self, influencer_user, db):
        """Test proposal creation with non-existent campaign"""
        dto = ProposalCreateDTO(
            campaign_id=99999,
            influencer_id=influencer_user.id,
            cover_letter='Test',
            desired_visit_date=date.today()
        )

        service = ProposalCreationService()

        with pytest.raises(InvalidStateException) as exc_info:
            service.execute(dto, user=influencer_user)

        assert "does not exist" in str(exc_info.value)

    def test_create_proposal_campaign_not_recruiting(self, influencer_user, db):
        """Test proposal creation when campaign is not recruiting"""
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        today = date.today()
        campaign = Campaign.objects.create(
            advertiser=advertiser,
            name='Test Campaign',
            recruitment_start_date=today,
            recruitment_end_date=today + timedelta(days=7),
            recruitment_count=10,
            benefits='Free product',
            mission='Write a review',
            status='recruitment_ended'  # Not recruiting
        )

        dto = ProposalCreateDTO(
            campaign_id=campaign.id,
            influencer_id=influencer_user.id,
            cover_letter='Test',
            desired_visit_date=today + timedelta(days=3)
        )

        service = ProposalCreationService()

        with pytest.raises(InvalidStateException) as exc_info:
            service.execute(dto, user=influencer_user)

        assert "not currently accepting" in str(exc_info.value)

    def test_create_proposal_duplicate_application(self, influencer_user, db):
        """Test duplicate proposal creation"""
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        today = date.today()
        campaign = Campaign.objects.create(
            advertiser=advertiser,
            name='Test Campaign',
            recruitment_start_date=today,
            recruitment_end_date=today + timedelta(days=7),
            recruitment_count=10,
            benefits='Free product',
            mission='Write a review',
            status='recruiting'
        )

        # Create first proposal
        Proposal.objects.create(
            campaign=campaign,
            influencer=influencer_user,
            cover_letter='First application',
            desired_visit_date=today + timedelta(days=3),
            status='submitted'
        )

        # Try to create duplicate
        dto = ProposalCreateDTO(
            campaign_id=campaign.id,
            influencer_id=influencer_user.id,
            cover_letter='Second application',
            desired_visit_date=today + timedelta(days=5)
        )

        service = ProposalCreationService()

        with pytest.raises(DuplicateActionException) as exc_info:
            service.execute(dto, user=influencer_user)

        assert "already applied" in str(exc_info.value)
