"""
E2E tests for home page.
"""

import pytest
from django.test import Client
from django.urls import reverse
from apps.campaigns.factories import CampaignFactory
from apps.users.factories import AdvertiserFactory


@pytest.mark.django_db
class TestHomePageE2E:
    """End-to-end test suite for home page"""

    def test_visitor_can_view_home_page_with_campaigns(self):
        """
        시나리오: 비회원 방문자가 홈 페이지에서 체험단 목록을 확인한다

        Given: 모집 중인 체험단 3개가 등록되어 있음
        When: 비로그인 상태에서 홈 페이지에 접근
        Then: 상단 배너에 최신 캠페인 1개 표시
              목록에 전체 캠페인 3개 표시
        """
        # Given
        client = Client()
        advertiser = AdvertiserFactory()
        campaign1 = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            name='첫 번째 캠페인'
        )
        campaign2 = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            name='두 번째 캠페인'
        )
        campaign3 = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            name='세 번째 캠페인'
        )

        # When
        response = client.get(reverse('campaigns:home'))

        # Then
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert '세 번째 캠페인' in content
        assert '두 번째 캠페인' in content
        assert '첫 번째 캠페인' in content

    def test_visitor_sees_empty_state_when_no_campaigns(self):
        """
        시나리오: 모집 중인 체험단이 없을 때 Empty State 표시

        Given: 모집 중인 체험단이 0개
        When: 홈 페이지에 접근
        Then: "현재 모집 중인 체험단이 없습니다" 메시지 표시
        """
        # Given
        client = Client()

        # When
        response = client.get(reverse('campaigns:home'))

        # Then
        assert response.status_code == 200
        assert '현재 모집 중인 체험단이 없습니다' in response.content.decode('utf-8')

    def test_home_page_does_not_show_ended_campaigns(self):
        """
        시나리오: 모집 종료된 캠페인은 홈 페이지에 표시되지 않음

        Given: 모집 중인 캠페인 1개, 모집 종료된 캠페인 1개
        When: 홈 페이지에 접근
        Then: 모집 중인 캠페인만 표시
        """
        # Given
        client = Client()
        advertiser = AdvertiserFactory()
        active_campaign = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            name='모집 중 캠페인'
        )
        ended_campaign = CampaignFactory(
            advertiser=advertiser,
            status='recruitment_ended',
            name='종료된 캠페인'
        )

        # When
        response = client.get(reverse('campaigns:home'))

        # Then
        content = response.content.decode('utf-8')
        assert '모집 중 캠페인' in content
        assert '종료된 캠페인' not in content

    def test_home_page_shows_advertiser_name(self):
        """
        시나리오: 체험단 카드에 광고주 이름이 표시된다

        Given: 광고주가 등록한 체험단 1개
        When: 홈 페이지에 접근
        Then: 광고주 이름이 표시됨
        """
        # Given
        client = Client()
        advertiser = AdvertiserFactory()
        campaign = CampaignFactory(
            advertiser=advertiser,
            status='recruiting'
        )

        # When
        response = client.get(reverse('campaigns:home'))

        # Then
        content = response.content.decode('utf-8')
        assert advertiser.name in content

    def test_home_page_shows_recruitment_info(self):
        """
        시나리오: 체험단 카드에 모집 정보가 표시된다

        Given: 모집 인원 10명인 체험단 1개
        When: 홈 페이지에 접근
        Then: "모집 인원: 10명" 텍스트가 표시됨
        """
        # Given
        client = Client()
        advertiser = AdvertiserFactory()
        campaign = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            recruitment_count=10
        )

        # When
        response = client.get(reverse('campaigns:home'))

        # Then
        content = response.content.decode('utf-8')
        assert '모집 인원: 10명' in content
