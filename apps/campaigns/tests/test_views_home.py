"""
Integration tests for HomeView.
"""

import pytest
from django.urls import reverse
from apps.campaigns.factories import CampaignFactory
from apps.users.factories import AdvertiserFactory


@pytest.mark.django_db
class TestHomeView:
    """Test suite for HomeView"""

    def test_home_view_returns_200(self, client):
        """홈 페이지가 정상적으로 렌더링된다"""
        response = client.get(reverse('campaigns:home'))
        assert response.status_code == 200

    def test_home_view_uses_correct_template(self, client):
        """올바른 템플릿을 사용한다"""
        response = client.get(reverse('campaigns:home'))
        assert 'campaigns/home.html' in [t.name for t in response.templates]

    def test_home_view_includes_featured_campaign_in_context(self, client):
        """상단 배너용 featured_campaign이 컨텍스트에 포함된다"""
        advertiser = AdvertiserFactory()
        campaign = CampaignFactory(advertiser=advertiser, status='recruiting')

        response = client.get(reverse('campaigns:home'))

        assert 'featured_campaign' in response.context
        assert response.context['featured_campaign'] == campaign

    def test_home_view_includes_campaigns_list_in_context(self, client):
        """모집 중인 캠페인 목록이 컨텍스트에 포함된다"""
        advertiser = AdvertiserFactory()
        campaign1 = CampaignFactory(advertiser=advertiser, status='recruiting')
        campaign2 = CampaignFactory(advertiser=advertiser, status='recruiting')

        response = client.get(reverse('campaigns:home'))

        assert 'campaigns' in response.context
        campaigns = list(response.context['campaigns'])
        assert len(campaigns) == 2

    def test_home_view_accessible_without_login(self, client):
        """비로그인 사용자도 접근 가능하다"""
        response = client.get(reverse('campaigns:home'))
        assert response.status_code == 200

    def test_home_view_with_no_campaigns(self, client):
        """모집 중인 캠페인이 없을 때도 정상 작동한다"""
        response = client.get(reverse('campaigns:home'))

        assert response.status_code == 200
        assert response.context['featured_campaign'] is None
        assert len(list(response.context['campaigns'])) == 0

    def test_home_view_excludes_ended_campaigns(self, client):
        """모집 종료된 캠페인은 목록에 표시되지 않는다"""
        advertiser = AdvertiserFactory()
        active_campaign = CampaignFactory(advertiser=advertiser, status='recruiting')
        ended_campaign = CampaignFactory(advertiser=advertiser, status='recruitment_ended')

        response = client.get(reverse('campaigns:home'))

        campaigns = list(response.context['campaigns'])
        assert active_campaign in campaigns
        assert ended_campaign not in campaigns
        assert response.context['featured_campaign'] == active_campaign
