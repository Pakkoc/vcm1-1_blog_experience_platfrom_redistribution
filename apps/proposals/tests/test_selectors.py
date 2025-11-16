"""
Unit tests for ProposalSelector.
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from apps.proposals.selectors.proposal_selector import ProposalSelector
from apps.proposals.models import Proposal
from apps.campaigns.models import Campaign

User = get_user_model()


@pytest.mark.django_db
class TestProposalSelector:
    """Test suite for ProposalSelector class"""

    @pytest.fixture
    def influencer_user(self):
        """Create influencer user for testing"""
        from apps.users.models import InfluencerProfile

        user = User.objects.create_user(
            email='influencer@test.com',
            password='testpass123',
            name='Test Influencer',
            contact='010-1234-5678',
            role='influencer'
        )
        InfluencerProfile.objects.create(
            user=user,
            birth_date=date(1990, 1, 1),
            sns_link='https://instagram.com/test'
        )
        return user

    @pytest.fixture
    def advertiser_user(self):
        """Create advertiser user for testing"""
        from apps.users.models import AdvertiserProfile

        user = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-9876-5432',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=user,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )
        return user

    @pytest.fixture
    def sample_campaigns(self, advertiser_user):
        """Create sample campaigns for testing"""
        campaigns = []
        for i in range(3):
            campaign = Campaign.objects.create(
                advertiser=advertiser_user,
                name=f'Test Campaign {i+1}',
                recruitment_start_date=date.today(),
                recruitment_end_date=date.today() + timedelta(days=30),
                recruitment_count=5,
                benefits='Free product testing',
                mission='Write a review',
                status='recruiting'
            )
            campaigns.append(campaign)
        return campaigns

    def test_get_influencer_proposals_returns_correct_order(
        self, influencer_user, sample_campaigns
    ):
        """Test that proposals are returned in correct status order"""
        # Given: Create proposals with different statuses
        # Create in reverse order to test sorting
        Proposal.objects.create(
            campaign=sample_campaigns[2],
            influencer=influencer_user,
            cover_letter='Test 3',
            desired_visit_date=date.today() + timedelta(days=7),
            status='rejected'
        )
        Proposal.objects.create(
            campaign=sample_campaigns[1],
            influencer=influencer_user,
            cover_letter='Test 2',
            desired_visit_date=date.today() + timedelta(days=7),
            status='selected'
        )
        Proposal.objects.create(
            campaign=sample_campaigns[0],
            influencer=influencer_user,
            cover_letter='Test 1',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )

        # When: Call selector method
        proposals = ProposalSelector.get_influencer_proposals(
            influencer_id=influencer_user.id
        )

        # Then: Verify sorting order (submitted -> selected -> rejected)
        statuses = [p.status for p in proposals]
        assert statuses == ['submitted', 'selected', 'rejected']

    def test_get_influencer_proposals_sorts_by_created_at_within_status(
        self, influencer_user, sample_campaigns
    ):
        """Test that proposals with same status are sorted by created_at DESC"""
        # Given: Create multiple proposals with same status
        import time

        proposal1 = Proposal.objects.create(
            campaign=sample_campaigns[0],
            influencer=influencer_user,
            cover_letter='First',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )

        time.sleep(0.01)  # Ensure different timestamps

        proposal2 = Proposal.objects.create(
            campaign=sample_campaigns[1],
            influencer=influencer_user,
            cover_letter='Second',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )

        # When: Retrieve proposals
        proposals = list(ProposalSelector.get_influencer_proposals(
            influencer_id=influencer_user.id
        ))

        # Then: Most recent should be first
        assert proposals[0].id == proposal2.id
        assert proposals[1].id == proposal1.id

    def test_get_influencer_proposals_prevents_n_plus_1(
        self, influencer_user, sample_campaigns, django_assert_num_queries
    ):
        """Test that N+1 query problem is prevented with select_related"""
        # Given: Create 5 proposals
        for campaign in sample_campaigns:
            Proposal.objects.create(
                campaign=campaign,
                influencer=influencer_user,
                cover_letter='Test',
                desired_visit_date=date.today() + timedelta(days=7),
                status='submitted'
            )

        # When: Retrieve proposals and access related data
        with django_assert_num_queries(1):
            proposals = list(
                ProposalSelector.get_influencer_proposals(influencer_user.id)
            )
            # Access related campaign data - should not trigger additional queries
            for proposal in proposals:
                _ = proposal.campaign.name
                _ = proposal.campaign.advertiser.name

    def test_get_influencer_proposals_returns_empty_queryset_when_no_proposals(
        self, influencer_user
    ):
        """Test that empty queryset is returned when influencer has no proposals"""
        # When: Call selector for influencer with no proposals
        proposals = ProposalSelector.get_influencer_proposals(
            influencer_id=influencer_user.id
        )

        # Then: Should return empty queryset
        assert proposals.count() == 0
        assert list(proposals) == []

    def test_get_proposal_count_by_status_returns_correct_counts(
        self, influencer_user, sample_campaigns
    ):
        """Test that proposal count by status is correctly calculated"""
        # Given: Create proposals with different statuses
        Proposal.objects.create(
            campaign=sample_campaigns[0],
            influencer=influencer_user,
            cover_letter='Test 1',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )
        Proposal.objects.create(
            campaign=sample_campaigns[1],
            influencer=influencer_user,
            cover_letter='Test 2',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )
        Proposal.objects.create(
            campaign=sample_campaigns[2],
            influencer=influencer_user,
            cover_letter='Test 3',
            desired_visit_date=date.today() + timedelta(days=7),
            status='selected'
        )

        # When: Get count by status
        counts = ProposalSelector.get_proposal_count_by_status(
            influencer_id=influencer_user.id
        )

        # Then: Verify counts
        assert counts.get('submitted') == 2
        assert counts.get('selected') == 1
        assert counts.get('rejected') is None

    def test_get_proposal_count_by_status_returns_empty_dict_when_no_proposals(
        self, influencer_user
    ):
        """Test that empty dict is returned when influencer has no proposals"""
        # When: Get count for influencer with no proposals
        counts = ProposalSelector.get_proposal_count_by_status(
            influencer_id=influencer_user.id
        )

        # Then: Should return empty dict
        assert counts == {}
