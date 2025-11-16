"""
Integration tests for campaign views.
"""

import pytest
from datetime import date, timedelta
from django.urls import reverse
from apps.proposals.models import Proposal


@pytest.mark.django_db
class TestCampaignDetailView:
    """Test suite for CampaignDetailView"""

    def test_get_campaign_detail_anonymous_user(self, client, campaign_factory):
        """Test anonymous user can view campaign detail but cannot apply"""
        campaign = campaign_factory()
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        assert response.status_code == 200
        assert 'campaign' in response.context
        assert response.context['campaign'].id == campaign.id
        assert response.context['can_apply'] is False
        assert response.context['cannot_apply_reason'] == 'login_required'
        assert response.context['already_applied'] is False

    def test_get_campaign_detail_influencer_can_apply(
        self, client, campaign_factory, influencer_user
    ):
        """Test influencer can apply to valid recruiting campaign"""
        client.force_login(influencer_user)
        tomorrow = date.today() + timedelta(days=1)
        campaign = campaign_factory(
            status='recruiting',
            recruitment_end_date=tomorrow
        )
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_apply'] is True
        assert response.context['cannot_apply_reason'] is None
        assert response.context['already_applied'] is False

    def test_get_campaign_detail_advertiser(self, client, campaign_factory, advertiser_user):
        """Test advertiser cannot apply to campaigns"""
        client.force_login(advertiser_user)
        campaign = campaign_factory(status='recruiting')
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_apply'] is False
        assert response.context['cannot_apply_reason'] == 'advertiser_not_allowed'
        assert response.context['already_applied'] is False

    def test_get_campaign_detail_already_applied(
        self, client, campaign_factory, influencer_user
    ):
        """Test influencer who already applied sees already_applied status"""
        client.force_login(influencer_user)
        campaign = campaign_factory(status='recruiting')

        # Create existing proposal
        Proposal.objects.create(
            campaign=campaign,
            influencer=influencer_user,
            cover_letter="Test",
            desired_visit_date=date.today() + timedelta(days=1)
        )

        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_apply'] is False
        assert response.context['cannot_apply_reason'] == 'already_applied'
        assert response.context['already_applied'] is True

    def test_get_campaign_detail_recruitment_ended(
        self, client, campaign_factory, influencer_user
    ):
        """Test influencer cannot apply to ended campaign"""
        client.force_login(influencer_user)
        campaign = campaign_factory(status='recruitment_ended')
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_apply'] is False
        assert response.context['cannot_apply_reason'] == 'recruitment_ended'
        assert response.context['already_applied'] is False

    def test_get_campaign_detail_not_found(self, client):
        """Test 404 when campaign does not exist"""
        url = reverse('campaigns:detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404
