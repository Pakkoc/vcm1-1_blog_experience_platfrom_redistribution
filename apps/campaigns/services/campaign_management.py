"""
Campaign management services for closing recruitment and selecting influencers.
"""

from django.db import transaction
from django.utils import timezone
from ..models import Campaign
from ..dto import CampaignCloseDTO
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException
)


class CampaignCloseService:
    """Service for closing campaign recruitment"""

    def execute(self, user, dto: CampaignCloseDTO) -> Campaign:
        """
        Close campaign recruitment.

        Args:
            user: Current authenticated advertiser user
            dto: Campaign close input data

        Returns:
            Updated Campaign object

        Raises:
            PermissionDeniedException: If user lacks permission
            InvalidStateException: If campaign status is not 'recruiting'
        """
        # 1. Fetch campaign
        try:
            campaign = Campaign.objects.select_for_update().get(
                id=dto.campaign_id
            )
        except Campaign.DoesNotExist:
            raise InvalidStateException("존재하지 않는 캠페인입니다.")

        # 2. Verify permission
        if campaign.advertiser_id != user.id:
            raise PermissionDeniedException(
                "이 체험단에 접근할 권한이 없습니다."
            )

        # 3. Verify state
        if campaign.status != 'recruiting':
            raise InvalidStateException(
                "이미 모집이 종료되었거나 선정이 완료된 체험단입니다."
            )

        # 4. Update status
        campaign.status = 'recruitment_ended'
        campaign.updated_at = timezone.now()
        campaign.save(update_fields=['status', 'updated_at'])

        return campaign
