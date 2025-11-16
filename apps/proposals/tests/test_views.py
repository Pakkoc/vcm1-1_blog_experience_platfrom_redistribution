"""
Integration tests for proposal views.
"""

import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from apps.proposals.models import Proposal
from apps.campaigns.models import Campaign
from apps.users.models import InfluencerProfile, AdvertiserProfile

User = get_user_model()


@pytest.mark.django_db
class TestMyProposalsListView:
    """Test suite for MyProposalsListView"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return Client()

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
    def sample_campaign(self, advertiser_user):
        """Create a sample campaign"""
        return Campaign.objects.create(
            advertiser=advertiser_user,
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=30),
            recruitment_count=5,
            benefits='Free product testing',
            mission='Write a review',
            status='recruiting'
        )

    @pytest.fixture
    def sample_proposals(self, influencer_user, advertiser_user):
        """Create sample proposals for testing"""
        campaigns = []
        proposals = []

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

            proposal = Proposal.objects.create(
                campaign=campaign,
                influencer=influencer_user,
                cover_letter=f'Test cover letter {i+1}',
                desired_visit_date=date.today() + timedelta(days=7),
                status='submitted'
            )
            proposals.append(proposal)

        return proposals

    def test_unauthenticated_user_redirects_to_login(self, client):
        """Verify that unauthenticated users are redirected to login page"""
        # When: Access the page without logging in
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_advertiser_user_gets_403(self, client, advertiser_user):
        """Verify that advertiser users receive 403 Forbidden"""
        # Given: Login as advertiser
        client.force_login(advertiser_user)

        # When: Try to access influencer-only page
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Should get 403 Forbidden
        assert response.status_code == 403

    def test_influencer_sees_own_proposals(
        self, client, influencer_user, sample_proposals
    ):
        """Verify that influencer can see their own proposals"""
        # Given: Login as influencer with 3 proposals
        client.force_login(influencer_user)

        # When: Access the my proposals page
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Should return 200 OK with proposals in context
        assert response.status_code == 200
        assert 'proposals' in response.context
        assert len(response.context['proposals']) == 3

    def test_influencer_with_no_proposals_sees_empty_state(
        self, client, influencer_user
    ):
        """Verify that influencer without proposals sees empty state"""
        # Given: Login as influencer with no proposals
        client.force_login(influencer_user)

        # When: Access the page
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Should set has_proposals flag to False
        assert response.status_code == 200
        assert response.context['has_proposals'] is False

    def test_proposals_are_sorted_by_status(
        self, client, influencer_user, advertiser_user
    ):
        """Verify that proposals are sorted by status order"""
        # Given: Create proposals with different statuses
        campaigns = []
        for i in range(3):
            campaign = Campaign.objects.create(
                advertiser=advertiser_user,
                name=f'Campaign {i+1}',
                recruitment_start_date=date.today(),
                recruitment_end_date=date.today() + timedelta(days=30),
                recruitment_count=5,
                benefits='Test',
                mission='Test',
                status='recruiting'
            )
            campaigns.append(campaign)

        # Create in reverse order to test sorting
        Proposal.objects.create(
            campaign=campaigns[2],
            influencer=influencer_user,
            cover_letter='Rejected',
            desired_visit_date=date.today() + timedelta(days=7),
            status='rejected'
        )
        Proposal.objects.create(
            campaign=campaigns[1],
            influencer=influencer_user,
            cover_letter='Selected',
            desired_visit_date=date.today() + timedelta(days=7),
            status='selected'
        )
        Proposal.objects.create(
            campaign=campaigns[0],
            influencer=influencer_user,
            cover_letter='Submitted',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )

        client.force_login(influencer_user)

        # When: Access the page
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Proposals should be sorted by status
        proposals = response.context['proposals']
        statuses = [p.status for p in proposals]
        assert statuses == ['submitted', 'selected', 'rejected']

    def test_view_uses_correct_template(self, client, influencer_user):
        """Verify that correct template is used"""
        # Given: Login as influencer
        client.force_login(influencer_user)

        # When: Access the page
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Should use the correct template
        assert response.status_code == 200
        assert 'proposals/my_proposals_list.html' in [t.name for t in response.templates]

    def test_influencer_only_sees_own_proposals(
        self, client, influencer_user, advertiser_user, sample_campaign
    ):
        """Verify that influencer only sees their own proposals, not others'"""
        # Given: Create another influencer with proposals
        from apps.users.models import InfluencerProfile

        other_influencer = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            name='Other Influencer',
            contact='010-1111-2222',
            role='influencer'
        )
        InfluencerProfile.objects.create(
            user=other_influencer,
            birth_date=date(1995, 1, 1),
            sns_link='https://instagram.com/other'
        )

        # Create proposals for both influencers
        Proposal.objects.create(
            campaign=sample_campaign,
            influencer=influencer_user,
            cover_letter='My proposal',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )

        campaign2 = Campaign.objects.create(
            advertiser=advertiser_user,
            name='Another Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=30),
            recruitment_count=5,
            benefits='Test',
            mission='Test',
            status='recruiting'
        )

        Proposal.objects.create(
            campaign=campaign2,
            influencer=other_influencer,
            cover_letter='Other proposal',
            desired_visit_date=date.today() + timedelta(days=7),
            status='submitted'
        )

        client.force_login(influencer_user)

        # When: Access the page
        response = client.get(reverse('proposals:my_proposals'))

        # Then: Should only see own proposal
        proposals = response.context['proposals']
        assert len(proposals) == 1
        assert proposals[0].influencer.id == influencer_user.id


@pytest.mark.django_db
class TestProposalCreateView:
    """Test suite for ProposalCreateView"""

    def test_get_proposal_form_authenticated_influencer(self, client, influencer_user):
        """Test GET request for authenticated influencer"""
        # Login
        client.force_login(influencer_user)

        # Create campaign
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

        # GET request
        url = reverse('proposals:apply', kwargs={'pk': campaign.id})
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'campaign' in response.context
        assert response.context['campaign'] == campaign

    def test_get_proposal_form_unauthenticated(self, client):
        """Test GET request for unauthenticated user redirects to login"""
        url = reverse('proposals:apply', kwargs={'pk': 1})
        response = client.get(url)

        # Should redirect to login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_get_proposal_form_advertiser_forbidden(self, client, db):
        """Test GET request for advertiser returns 403"""
        # Create advertiser
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )

        # Login as advertiser
        client.force_login(advertiser)

        # Try to access proposal form
        url = reverse('proposals:apply', kwargs={'pk': 1})
        response = client.get(url)

        # Should return 403
        assert response.status_code == 403

    def test_post_proposal_create_success(self, client, influencer_user, db):
        """Test POST request successfully creates proposal"""
        # Login
        client.force_login(influencer_user)

        # Create campaign
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

        # POST data
        url = reverse('proposals:apply', kwargs={'pk': campaign.id})
        data = {
            'cover_letter': 'I really want to participate!',
            'desired_visit_date': (today + timedelta(days=3)).isoformat()
        }

        response = client.post(url, data, follow=True)

        # Assert
        assert response.status_code == 200
        assert Proposal.objects.filter(
            campaign=campaign,
            influencer=influencer_user
        ).exists()

        # Check success message
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert '성공적으로 완료' in str(messages[0])

    def test_post_proposal_create_invalid_form(self, client, influencer_user, db):
        """Test POST request with invalid form data"""
        # Login
        client.force_login(influencer_user)

        # Create campaign
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

        # POST invalid data (missing cover_letter)
        url = reverse('proposals:apply', kwargs={'pk': campaign.id})
        data = {
            'desired_visit_date': (today + timedelta(days=3)).isoformat()
        }

        response = client.post(url, data)

        # Assert
        assert response.status_code == 200  # Re-renders form
        assert 'form' in response.context
        assert response.context['form'].errors
        assert not Proposal.objects.filter(
            campaign=campaign,
            influencer=influencer_user
        ).exists()

