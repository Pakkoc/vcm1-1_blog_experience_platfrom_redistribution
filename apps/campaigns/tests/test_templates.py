"""
Template rendering tests for campaign detail page.
"""

import pytest
from datetime import date, timedelta
from django.urls import reverse
from apps.proposals.models import Proposal


@pytest.mark.django_db
class TestCampaignDetailTemplate:
    """Test suite for campaign_detail.html template rendering"""

    def test_template_renders_campaign_info(self, client, campaign_factory):
        """Test campaign information is rendered correctly"""
        campaign = campaign_factory(
            name="테스트 체험단",
            benefits="무료 제공",
            mission="리뷰 작성"
        )
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        html = response.content.decode('utf-8')
        assert "테스트 체험단" in html
        assert "무료 제공" in html
        assert "리뷰 작성" in html
        assert campaign.advertiser.advertiser_profile.company_name in html

    def test_template_shows_apply_button_for_influencer(
        self, client, campaign_factory, influencer_user
    ):
        """Test apply button is displayed for eligible influencer"""
        client.force_login(influencer_user)
        campaign = campaign_factory(
            status='recruiting',
            recruitment_end_date=date.today() + timedelta(days=1)
        )
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        html = response.content.decode('utf-8')
        assert "지원하기" in html
        assert "btn-primary" in html

    def test_template_shows_login_button_for_anonymous(
        self, client, campaign_factory
    ):
        """Test login button is displayed for anonymous users"""
        campaign = campaign_factory(status='recruiting')
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        html = response.content.decode('utf-8')
        assert "로그인하기" in html
        assert "로그인 후 지원 가능합니다" in html

    def test_template_shows_applied_status_for_existing_proposal(
        self, client, campaign_factory, influencer_user
    ):
        """Test 'applied' button is displayed when user already applied"""
        client.force_login(influencer_user)
        campaign = campaign_factory(status='recruiting')
        Proposal.objects.create(
            campaign=campaign,
            influencer=influencer_user,
            cover_letter="Test",
            desired_visit_date=date.today() + timedelta(days=1)
        )

        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        html = response.content.decode('utf-8')
        assert "지원 완료" in html
        assert "내 지원 목록 보기" in html

    def test_template_shows_advertiser_warning_for_advertiser(
        self, client, campaign_factory, advertiser_user
    ):
        """Test advertiser sees appropriate message"""
        client.force_login(advertiser_user)
        campaign = campaign_factory(status='recruiting')
        url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
        response = client.get(url)

        html = response.content.decode('utf-8')
        assert "광고주는 체험단에 지원할 수 없습니다" in html
