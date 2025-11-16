"""
Campaign selectors for complex query logic.
"""

from datetime import date
from typing import Dict, Any, Optional
from django.db.models import QuerySet
from apps.campaigns.models import Campaign


class CampaignSelector:
    """Selector for campaign queries and business rule validation"""

    @staticmethod
    def get_latest_recruiting_campaign() -> Optional[Campaign]:
        """
        상단 배너에 노출할 가장 최근 등록된 모집 중인 체험단 1개를 조회한다.

        Returns:
            Campaign 인스턴스 또는 None (모집 중인 캠페인이 없는 경우)
        """
        return Campaign.objects.filter(
            status='recruiting'
        ).select_related('advertiser').order_by('-created_at').first()

    @staticmethod
    def get_recruiting_campaigns() -> QuerySet[Campaign]:
        """
        현재 모집 중인 전체 체험단 목록을 최신순으로 조회한다.

        Returns:
            QuerySet[Campaign]: 모집 중인 체험단 목록 (최신순 정렬)
        """
        return Campaign.objects.filter(
            status='recruiting'
        ).select_related('advertiser').order_by('-created_at')

    @staticmethod
    def get_campaign_detail(campaign_id: int) -> Campaign:
        """
        Retrieve campaign detail with related advertiser information.

        Args:
            campaign_id: Campaign ID to retrieve

        Returns:
            Campaign object with advertiser and profile loaded

        Raises:
            Campaign.DoesNotExist: If campaign with given ID doesn't exist
        """
        return Campaign.objects.select_related(
            'advertiser',
            'advertiser__advertiser_profile'
        ).get(id=campaign_id)

    @staticmethod
    def check_user_can_apply(campaign: Campaign, user) -> Dict[str, Any]:
        """
        Check if a user can apply to the given campaign.

        This method validates all business rules for campaign application:
        - User must be authenticated
        - User must be an influencer (not advertiser)
        - Campaign must be in 'recruiting' status
        - Current date must be within recruitment period
        - User must not have already applied

        Args:
            campaign: Campaign to check
            user: User object (can be AnonymousUser)

        Returns:
            Dictionary with:
                - can_apply (bool): Whether user can apply
                - reason (str|None): Reason if cannot apply
                - already_applied (bool): Whether user has already applied
        """
        # Check 1: User must be authenticated
        if not user.is_authenticated:
            return {
                'can_apply': False,
                'reason': 'login_required',
                'already_applied': False
            }

        # Check 2: User must be an influencer
        if user.role == 'advertiser':
            return {
                'can_apply': False,
                'reason': 'advertiser_not_allowed',
                'already_applied': False
            }

        # Check 3: Campaign must be in recruiting status
        if campaign.status != 'recruiting':
            return {
                'can_apply': False,
                'reason': 'recruitment_ended',
                'already_applied': False
            }

        # Check 4: Current date must be within recruitment period
        today = date.today()
        if today > campaign.recruitment_end_date:
            return {
                'can_apply': False,
                'reason': 'deadline_passed',
                'already_applied': False
            }

        # Check 5: User must not have already applied
        from apps.proposals.models import Proposal
        already_applied = Proposal.objects.filter(
            campaign_id=campaign.id,
            influencer_id=user.id
        ).exists()

        if already_applied:
            return {
                'can_apply': False,
                'reason': 'already_applied',
                'already_applied': True
            }

        # All checks passed
        return {
            'can_apply': True,
            'reason': None,
            'already_applied': False
        }
