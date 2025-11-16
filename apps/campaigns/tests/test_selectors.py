"""
Unit tests for CampaignSelector - Phase 1 Requirements
"""

import pytest
from datetime import date, timedelta
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.contrib.auth.models import AnonymousUser
from apps.campaigns.models import Campaign
from apps.campaigns.selectors.campaign_selector import CampaignSelector
from apps.proposals.models import Proposal
from apps.users.models import User, AdvertiserProfile, InfluencerProfile


@pytest.mark.django_db
class TestCampaignSelector:
    """Test suite for CampaignSelector - Phase 1 Acceptance Tests"""

    def test_get_campaigns_by_advertiser_returns_only_own_campaigns(self):
        """광고주 A가 등록한 캠페인만 조회됨 (다른 광고주 캠페인은 제외)"""
        # Given: 두 명의 광고주 생성
        advertiser1 = User.objects.create_user(
            email='advertiser1@test.com',
            password='testpass123',
            name='Advertiser 1',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser1,
            company_name='Company 1',
            business_registration_number='123-45-67890'
        )

        advertiser2 = User.objects.create_user(
            email='advertiser2@test.com',
            password='testpass123',
            name='Advertiser 2',
            contact='010-9876-5432',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser2,
            company_name='Company 2',
            business_registration_number='098-76-54321'
        )

        # Given: 각 광고주의 캠페인 생성
        campaign1 = Campaign.objects.create(
            advertiser=advertiser1,
            name='Campaign 1',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Free product',
            mission='Write review',
            status='recruiting'
        )

        campaign2 = Campaign.objects.create(
            advertiser=advertiser2,
            name='Campaign 2',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=10,
            benefits='Free meal',
            mission='Post on Instagram',
            status='recruiting'
        )

        # When: advertiser1의 캠페인 조회
        campaigns = CampaignSelector.get_campaigns_by_advertiser(advertiser1.id)

        # Then: advertiser1의 캠페인만 반환
        assert campaigns.count() == 1
        assert campaigns.first().id == campaign1.id
        assert campaigns.first().advertiser_id == advertiser1.id

    def test_get_campaigns_includes_proposal_count(self):
        """각 캠페인 객체에 proposal_count 속성이 존재하고 정확한 값을 가짐"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 캠페인 생성
        campaign = Campaign.objects.create(
            advertiser=advertiser,
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Free product',
            mission='Write review',
            status='recruiting'
        )

        # Given: 인플루언서 3명 생성 및 지원
        for i in range(3):
            influencer = User.objects.create_user(
                email=f'influencer{i}@test.com',
                password='testpass123',
                name=f'Influencer {i}',
                contact=f'010-1111-{i:04d}',
                role='influencer'
            )
            InfluencerProfile.objects.create(
                user=influencer,
                birth_date=date(1990, 1, 1),
                sns_link='https://instagram.com/test'
            )
            Proposal.objects.create(
                campaign=campaign,
                influencer=influencer,
                cover_letter='Test cover letter',
                desired_visit_date=date.today() + timedelta(days=3),
                status='submitted'
            )

        # When: 캠페인 조회
        campaigns = CampaignSelector.get_campaigns_by_advertiser(advertiser.id)

        # Then: proposal_count가 3
        assert campaigns.first().proposal_count == 3

    def test_get_campaigns_ordered_by_latest(self):
        """최신 등록 순으로 정렬됨"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 여러 캠페인 생성 (순서대로)
        campaign1 = Campaign.objects.create(
            advertiser=advertiser,
            name='Campaign 1',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Benefit 1',
            mission='Mission 1'
        )

        campaign2 = Campaign.objects.create(
            advertiser=advertiser,
            name='Campaign 2',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Benefit 2',
            mission='Mission 2'
        )

        campaign3 = Campaign.objects.create(
            advertiser=advertiser,
            name='Campaign 3',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Benefit 3',
            mission='Mission 3'
        )

        # When: 캠페인 조회
        campaigns = list(CampaignSelector.get_campaigns_by_advertiser(advertiser.id))

        # Then: 최신순 (created_at 내림차순)
        assert len(campaigns) == 3
        # created_at이 최신 순으로 정렬되어 있는지 확인
        assert campaigns[0].created_at >= campaigns[1].created_at
        assert campaigns[1].created_at >= campaigns[2].created_at

    def test_get_campaigns_no_n_plus_1_queries(self):
        """단일 쿼리로 모든 캠페인과 지원자 수 조회 (N+1 쿼리 없음)"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 10개 캠페인 생성
        for i in range(10):
            Campaign.objects.create(
                advertiser=advertiser,
                name=f'Campaign {i}',
                recruitment_start_date=date.today(),
                recruitment_end_date=date.today() + timedelta(days=7),
                recruitment_count=5,
                benefits=f'Benefit {i}',
                mission=f'Mission {i}'
            )

        # When & Then: 쿼리 수 확인 (2개 이하)
        with CaptureQueriesContext(connection) as context:
            campaigns = CampaignSelector.get_campaigns_by_advertiser(advertiser.id)
            # QuerySet을 평가하여 실제 쿼리 실행
            list(campaigns)

        # 쿼리 수가 2개 이하인지 확인 (SELECT + annotate)
        assert len(context.captured_queries) <= 2

    # 기존 테스트들도 유지
    def test_get_campaign_detail_success(self):
        """Test successful campaign detail retrieval"""
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        campaign = Campaign.objects.create(
            advertiser=advertiser,
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Free product',
            mission='Write review'
        )

        result = CampaignSelector.get_campaign_detail(campaign.id)

        assert result.id == campaign.id
        assert result.name == campaign.name
        assert hasattr(result, 'advertiser')
        assert result.advertiser is not None

    def test_get_campaign_detail_not_found(self):
        """Test campaign detail retrieval with invalid ID raises DoesNotExist"""
        with pytest.raises(Campaign.DoesNotExist):
            CampaignSelector.get_campaign_detail(99999)
