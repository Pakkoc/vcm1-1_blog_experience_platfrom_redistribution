"""
Campaign creation service - Phase 2
"""

from django.core.exceptions import PermissionDenied, ValidationError
from apps.campaigns.models import Campaign
from apps.campaigns.dto import CampaignCreateDTO
from apps.users.models import User


class CampaignCreationService:
    """체험단 생성 비즈니스 로직"""

    def execute(self, user: User, dto: CampaignCreateDTO) -> Campaign:
        """
        체험단을 생성합니다.

        Args:
            user: 현재 로그인된 광고주
            dto: 체험단 생성 데이터

        Returns:
            생성된 Campaign 객체

        Raises:
            PermissionDenied: 광고주가 아닌 경우
            ValidationError: 비즈니스 규칙 위반 시
        """
        # 1. 권한 확인
        if user.role != 'advertiser':
            raise PermissionDenied("광고주만 체험단을 등록할 수 있습니다.")

        # 2. 비즈니스 규칙 검증
        if dto.recruitment_end_date < dto.recruitment_start_date:
            raise ValidationError("모집 종료일은 시작일과 같거나 이후여야 합니다.")

        if dto.recruitment_count < 1:
            raise ValidationError("모집 인원은 최소 1명 이상이어야 합니다.")

        # 3. 체험단 생성
        campaign = Campaign.objects.create(
            advertiser=user,
            name=dto.name,
            recruitment_start_date=dto.recruitment_start_date,
            recruitment_end_date=dto.recruitment_end_date,
            recruitment_count=dto.recruitment_count,
            benefits=dto.benefits,
            mission=dto.mission,
            status='recruiting'  # 초기 상태는 항상 '모집 중'
        )

        return campaign
