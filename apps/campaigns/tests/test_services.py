"""
Tests for campaign services - Phase 2 and Phase 7 Requirements
"""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from datetime import date, timedelta
from apps.campaigns.services.campaign_creation import CampaignCreationService
from apps.campaigns.services.campaign_management import CampaignCloseService
from apps.campaigns.services.influencer_selection import InfluencerSelectionService
from apps.campaigns.dto import (
    CampaignCreateDTO,
    CampaignCloseDTO,
    InfluencerSelectionDTO
)
from apps.campaigns.models import Campaign
from apps.proposals.models import Proposal
from apps.users.models import User, AdvertiserProfile, InfluencerProfile
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    ServiceException
)


@pytest.mark.django_db
class TestCampaignCreationService:
    """Tests for CampaignCreationService - Phase 2 Acceptance Tests"""

    def test_execute_creates_campaign_successfully(self):
        """광고주가 유효한 데이터로 체험단 생성 시 DB에 저장됨"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 유효한 DTO
        dto = CampaignCreateDTO(
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Free product',
            mission='Write review'
        )

        # When: 서비스 실행
        service = CampaignCreationService()
        campaign = service.execute(user=advertiser, dto=dto)

        # Then: Campaign 객체 반환 및 DB 저장 확인
        assert campaign.id is not None
        assert campaign.name == 'Test Campaign'
        assert campaign.advertiser == advertiser
        assert campaign.recruitment_count == 5
        assert campaign.status == 'recruiting'

        # DB에 실제 저장되었는지 확인
        assert Campaign.objects.filter(id=campaign.id).exists()

    def test_execute_raises_permission_denied_for_influencer(self):
        """인플루언서가 생성 시도 시 PermissionDenied 예외 발생"""
        # Given: 인플루언서 생성
        influencer = User.objects.create_user(
            email='influencer@test.com',
            password='testpass123',
            name='Test Influencer',
            contact='010-9876-5432',
            role='influencer'
        )
        InfluencerProfile.objects.create(
            user=influencer,
            birth_date=date(1990, 1, 1),
            sns_link='https://instagram.com/test'
        )

        # Given: 유효한 DTO
        dto = CampaignCreateDTO(
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Free product',
            mission='Write review'
        )

        # When & Then: 인플루언서가 생성 시도 시 PermissionDenied 발생
        service = CampaignCreationService()
        with pytest.raises(PermissionDenied) as exc_info:
            service.execute(user=influencer, dto=dto)

        assert "광고주만" in str(exc_info.value)

    def test_execute_raises_validation_error_for_invalid_date_range(self):
        """모집 종료일이 시작일보다 이전이면 ValidationError 발생"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 잘못된 날짜 범위 DTO (종료일 < 시작일)
        dto = CampaignCreateDTO(
            name='Test Campaign',
            recruitment_start_date=date.today() + timedelta(days=7),
            recruitment_end_date=date.today(),  # 시작일보다 이전
            recruitment_count=5,
            benefits='Free product',
            mission='Write review'
        )

        # When & Then: ValidationError 발생
        service = CampaignCreationService()
        with pytest.raises(ValidationError) as exc_info:
            service.execute(user=advertiser, dto=dto)

        assert "모집 종료일" in str(exc_info.value)

    def test_execute_raises_validation_error_for_zero_recruitment_count(self):
        """모집 인원이 0명이면 ValidationError 발생"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 모집 인원 0명 DTO
        dto = CampaignCreateDTO(
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=0,  # 0명
            benefits='Free product',
            mission='Write review'
        )

        # When & Then: ValidationError 발생
        service = CampaignCreationService()
        with pytest.raises(ValidationError) as exc_info:
            service.execute(user=advertiser, dto=dto)

        assert "모집 인원" in str(exc_info.value)

    def test_execute_sets_initial_status_to_recruiting(self):
        """생성된 체험단의 status는 'recruiting'"""
        # Given: 광고주 생성
        advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Test Advertiser',
            contact='010-1234-5678',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=advertiser,
            company_name='Test Company',
            business_registration_number='123-45-67890'
        )

        # Given: 유효한 DTO
        dto = CampaignCreateDTO(
            name='Test Campaign',
            recruitment_start_date=date.today(),
            recruitment_end_date=date.today() + timedelta(days=7),
            recruitment_count=5,
            benefits='Free product',
            mission='Write review'
        )

        # When: 서비스 실행
        service = CampaignCreationService()
        campaign = service.execute(user=advertiser, dto=dto)

        # Then: status가 'recruiting'
        assert campaign.status == 'recruiting'


@pytest.mark.django_db
class TestCampaignCloseService:
    """Tests for CampaignCloseService - Phase 7"""

    def test_close_recruitment_successfully(
        self,
        recruiting_campaign,
        advertiser_user
    ):
        """모집 중인 캠페인 정상 마감"""
        # Given
        dto = CampaignCloseDTO(campaign_id=recruiting_campaign.id)
        service = CampaignCloseService()

        # When
        result = service.execute(user=advertiser_user, dto=dto)

        # Then
        assert result.status == 'recruitment_ended'

        # DB 확인
        campaign = Campaign.objects.get(id=recruiting_campaign.id)
        assert campaign.status == 'recruitment_ended'

    def test_close_recruitment_permission_denied(
        self,
        recruiting_campaign,
        other_advertiser_user
    ):
        """권한 없는 사용자의 모집 마감 시도"""
        # Given
        dto = CampaignCloseDTO(campaign_id=recruiting_campaign.id)
        service = CampaignCloseService()

        # When & Then
        with pytest.raises(PermissionDeniedException):
            service.execute(user=other_advertiser_user, dto=dto)

    def test_close_already_ended_campaign(
        self,
        ended_campaign,
        advertiser_user
    ):
        """이미 종료된 캠페인 재마감 시도"""
        # Given
        dto = CampaignCloseDTO(campaign_id=ended_campaign.id)
        service = CampaignCloseService()

        # When & Then
        with pytest.raises(InvalidStateException):
            service.execute(user=advertiser_user, dto=dto)


@pytest.mark.django_db
class TestInfluencerSelectionService:
    """Tests for InfluencerSelectionService - Phase 7"""

    def test_select_influencers_successfully(
        self,
        ended_campaign_with_proposals,
        advertiser_user
    ):
        """정상적인 체험단 선정"""
        # Given
        campaign = ended_campaign_with_proposals
        proposals = list(Proposal.objects.filter(
            campaign=campaign,
            status='submitted'
        )[:3])

        dto = InfluencerSelectionDTO(
            campaign_id=campaign.id,
            selected_proposal_ids=[p.id for p in proposals]
        )
        service = InfluencerSelectionService()

        # When
        result = service.execute(user=advertiser_user, dto=dto)

        # Then
        assert result.selected_count == 3
        assert result.rejected_count == 7
        assert result.campaign_status == 'selection_complete'

        # DB 확인
        selected = Proposal.objects.filter(
            campaign=campaign,
            status='selected'
        ).count()
        assert selected == 3

    def test_select_exceeds_recruitment_count(
        self,
        ended_campaign_with_proposals,
        advertiser_user
    ):
        """모집 인원 초과 선택"""
        # Given
        campaign = ended_campaign_with_proposals
        campaign.recruitment_count = 2
        campaign.save()

        proposals = list(Proposal.objects.filter(
            campaign=campaign,
            status='submitted'
        )[:5])

        dto = InfluencerSelectionDTO(
            campaign_id=campaign.id,
            selected_proposal_ids=[p.id for p in proposals]
        )
        service = InfluencerSelectionService()

        # When & Then
        with pytest.raises(ServiceException) as exc_info:
            service.execute(user=advertiser_user, dto=dto)

        assert "초과" in str(exc_info.value)

    def test_select_no_proposals(
        self,
        ended_campaign_with_proposals,
        advertiser_user
    ):
        """선정 인원 없음"""
        # Given
        campaign = ended_campaign_with_proposals

        dto = InfluencerSelectionDTO(
            campaign_id=campaign.id,
            selected_proposal_ids=[]
        )
        service = InfluencerSelectionService()

        # When & Then
        with pytest.raises(ServiceException) as exc_info:
            service.execute(user=advertiser_user, dto=dto)

        assert "최소 1명" in str(exc_info.value)
