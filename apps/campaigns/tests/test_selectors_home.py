"""
Unit tests for CampaignSelector - Home Page specific tests.
"""

import pytest
from apps.campaigns.selectors.campaign_selectors import CampaignSelector
from apps.campaigns.factories import CampaignFactory
from apps.users.factories import AdvertiserFactory


@pytest.mark.django_db
class TestCampaignSelectorHome:
    """Test suite for CampaignSelector home page methods"""

    def test_get_latest_recruiting_campaign_returns_most_recent(self):
        """가장 최근에 생성된 모집 중인 캠페인을 반환한다"""
        from apps.campaigns.models import Campaign
        import time

        # 기존 캠페인 모두 삭제
        Campaign.objects.all().delete()

        advertiser = AdvertiserFactory()
        campaign1 = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            name='첫 번째 캠페인'
        )
        time.sleep(0.01)  # 시간차를 두어 created_at이 확실히 다르게
        campaign2 = CampaignFactory(
            advertiser=advertiser,
            status='recruiting',
            name='두 번째 캠페인'
        )

        result = CampaignSelector.get_latest_recruiting_campaign()

        # 가장 최근에 생성된 캠페인이 반환됨
        assert result is not None
        assert result.status == 'recruiting'
        # 최신 캠페인이므로 '두 번째 캠페인'이 반환되어야 함
        assert result.name == '두 번째 캠페인'

    def test_get_latest_recruiting_campaign_excludes_ended_campaigns(self):
        """모집 종료된 캠페인은 반환하지 않는다"""
        advertiser = AdvertiserFactory()
        CampaignFactory(advertiser=advertiser, status='recruitment_ended')

        result = CampaignSelector.get_latest_recruiting_campaign()

        assert result is None

    def test_get_recruiting_campaigns_returns_all_recruiting(self):
        """모집 중인 모든 캠페인을 최신순으로 반환한다"""
        advertiser = AdvertiserFactory()
        campaign1 = CampaignFactory(advertiser=advertiser, status='recruiting')
        campaign2 = CampaignFactory(advertiser=advertiser, status='recruiting')
        campaign3 = CampaignFactory(advertiser=advertiser, status='recruiting')
        ended_campaign = CampaignFactory(advertiser=advertiser, status='recruitment_ended')

        result = list(CampaignSelector.get_recruiting_campaigns())

        assert len(result) == 3
        # 모집 종료 캠페인은 포함되지 않음
        assert ended_campaign not in result
        # 모집 중인 캠페인들만 포함
        assert campaign1 in result
        assert campaign2 in result
        assert campaign3 in result
        # 최신순으로 정렬되어 있는지 확인 (created_at DESC)
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i+1].created_at

    def test_get_recruiting_campaigns_prefetches_advertiser(self, django_assert_num_queries):
        """N+1 쿼리 방지를 위해 advertiser를 미리 로드한다"""
        advertiser = AdvertiserFactory()
        CampaignFactory(advertiser=advertiser, status='recruiting')

        with django_assert_num_queries(1):
            campaigns = list(CampaignSelector.get_recruiting_campaigns())
            # advertiser 접근 시 추가 쿼리 발생하지 않음
            _ = campaigns[0].advertiser.name

    def test_get_latest_recruiting_campaign_returns_none_when_no_campaigns(self):
        """모집 중인 캠페인이 없으면 None을 반환한다"""
        result = CampaignSelector.get_latest_recruiting_campaign()

        assert result is None

    def test_get_recruiting_campaigns_returns_empty_queryset_when_no_campaigns(self):
        """모집 중인 캠페인이 없으면 빈 QuerySet을 반환한다"""
        result = list(CampaignSelector.get_recruiting_campaigns())

        assert len(result) == 0
