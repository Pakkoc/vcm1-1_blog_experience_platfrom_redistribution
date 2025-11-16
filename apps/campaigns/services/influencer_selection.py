"""
Influencer selection service for campaigns.
"""

from django.db import transaction
from django.utils import timezone
from ..models import Campaign
from apps.proposals.models import Proposal
from ..dto import InfluencerSelectionDTO, InfluencerSelectionResultDTO
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    ServiceException
)


class InfluencerSelectionService:
    """Service for selecting influencers for a campaign"""

    @transaction.atomic
    def execute(
        self,
        user,
        dto: InfluencerSelectionDTO
    ) -> InfluencerSelectionResultDTO:
        """
        Select influencers for a campaign.

        Args:
            user: Current authenticated advertiser user
            dto: Selection input data

        Returns:
            InfluencerSelectionResultDTO: Selection result

        Raises:
            PermissionDeniedException: If user lacks permission
            InvalidStateException: If campaign status is not appropriate
            ServiceException: If selection validation fails
        """
        # 1. Fetch campaign with lock
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
        if campaign.status != 'recruitment_ended':
            raise InvalidStateException(
                "모집이 종료된 캠페인만 선정할 수 있습니다."
            )

        # 4. Validate selection count
        selected_count = len(dto.selected_proposal_ids)

        if selected_count == 0:
            raise ServiceException(
                "최소 1명 이상의 지원자를 선택해야 합니다."
            )

        if selected_count > campaign.recruitment_count:
            raise ServiceException(
                f"모집 인원({campaign.recruitment_count}명)을 "
                f"초과하여 선택할 수 없습니다. "
                f"현재 {selected_count}명이 선택되었습니다."
            )

        # 5. Validate selected proposals (belong to this campaign and submitted)
        valid_proposals = Proposal.objects.filter(
            id__in=dto.selected_proposal_ids,
            campaign=campaign,
            status='submitted'
        ).count()

        if valid_proposals != selected_count:
            raise ServiceException(
                "선택한 지원자 중 유효하지 않은 항목이 있습니다."
            )

        # 6. Select proposals
        selected = Proposal.objects.filter(
            id__in=dto.selected_proposal_ids,
            campaign=campaign
        ).update(
            status='selected',
            updated_at=timezone.now()
        )

        # 7. Reject unselected proposals
        rejected = Proposal.objects.filter(
            campaign=campaign,
            status='submitted'
        ).exclude(
            id__in=dto.selected_proposal_ids
        ).update(
            status='rejected',
            updated_at=timezone.now()
        )

        # 8. Update campaign status
        campaign.status = 'selection_complete'
        campaign.updated_at = timezone.now()
        campaign.save(update_fields=['status', 'updated_at'])

        # 9. Return result DTO
        return InfluencerSelectionResultDTO(
            campaign_id=campaign.id,
            selected_count=selected,
            rejected_count=rejected,
            campaign_status=campaign.status
        )
