"""
Service layer for campaign business logic.
"""

from apps.common.services.base import BaseService
from apps.common.exceptions import PermissionDeniedException, ValidationException
from apps.campaigns.models import Campaign
from apps.campaigns.dto import CampaignCreateDTO


class CampaignCreationService(BaseService[CampaignCreateDTO, Campaign]):
    """Service for creating a new campaign"""

    def execute(self, dto: CampaignCreateDTO, user=None) -> Campaign:
        """
        Create a new campaign.

        Args:
            dto: Campaign creation data
            user: User creating the campaign (must be advertiser)

        Returns:
            Created Campaign instance

        Raises:
            PermissionDeniedException: If user is not an advertiser
            ValidationException: If data validation fails
        """
        # Validate user permission
        if not user or not user.is_authenticated:
            raise PermissionDeniedException("User must be authenticated to create a campaign")

        if user.role != 'advertiser':
            raise PermissionDeniedException("Only advertisers can create campaigns")

        # Validate date range
        if dto.recruitment_start_date > dto.recruitment_end_date:
            raise ValidationException("Recruitment start date must be before end date")

        # Validate recruitment count
        if dto.recruitment_count <= 0:
            raise ValidationException("Recruitment count must be greater than 0")

        # Create campaign
        campaign = Campaign.objects.create(
            advertiser=user,
            name=dto.name,
            recruitment_start_date=dto.recruitment_start_date,
            recruitment_end_date=dto.recruitment_end_date,
            recruitment_count=dto.recruitment_count,
            benefits=dto.benefits,
            mission=dto.mission,
            status='recruiting'
        )

        return campaign
