"""
Service layer for proposal business logic.
"""

from apps.common.services.base import BaseService
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    DuplicateActionException
)
from apps.proposals.models import Proposal
from apps.proposals.dto import ProposalCreateDTO
from apps.campaigns.models import Campaign


class ProposalCreationService(BaseService[ProposalCreateDTO, Proposal]):
    """Service for creating a new proposal"""

    def execute(self, dto: ProposalCreateDTO, user=None) -> Proposal:
        """
        Create a new proposal.

        Args:
            dto: Proposal creation data
            user: User creating the proposal (must be influencer)

        Returns:
            Created Proposal instance

        Raises:
            PermissionDeniedException: If user is not an influencer
            InvalidStateException: If campaign is not accepting applications
            DuplicateActionException: If user already applied to this campaign
        """
        # Validate user permission
        if not user or not user.is_authenticated:
            raise PermissionDeniedException("User must be authenticated to apply to a campaign")

        if user.role != 'influencer':
            raise PermissionDeniedException("Only influencers can apply to campaigns")

        # Get campaign
        try:
            campaign = Campaign.objects.get(id=dto.campaign_id)
        except Campaign.DoesNotExist:
            raise InvalidStateException("Campaign does not exist")

        # Check if campaign accepts applications
        if not campaign.can_apply():
            raise InvalidStateException("This campaign is not currently accepting applications")

        # Check for duplicate application
        if Proposal.objects.filter(campaign=campaign, influencer=user).exists():
            raise DuplicateActionException("You have already applied to this campaign")

        # Create proposal
        proposal = Proposal.objects.create(
            campaign=campaign,
            influencer=user,
            cover_letter=dto.cover_letter,
            desired_visit_date=dto.desired_visit_date,
            status='submitted'
        )

        return proposal
