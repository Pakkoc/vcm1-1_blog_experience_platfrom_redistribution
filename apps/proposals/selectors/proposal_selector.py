"""
Selector layer for proposal queries.
"""

from typing import List, Dict
from django.db.models import QuerySet, Case, When, IntegerField, Count
from apps.proposals.models import Proposal
from apps.common.selectors.base import BaseSelector


class ProposalSelector(BaseSelector):
    """Selector for proposal queries with optimizations"""

    @staticmethod
    def get_influencer_proposals(influencer_id: int) -> QuerySet[Proposal]:
        """
        Get all proposals submitted by a specific influencer with custom ordering.

        Sorting order:
        1. By status (submitted -> selected -> rejected)
        2. Within same status, by latest created first

        Uses select_related to prevent N+1 queries.

        Args:
            influencer_id: ID of the influencer

        Returns:
            QuerySet of proposals ordered by status and creation date
        """
        return Proposal.objects.filter(
            influencer_id=influencer_id
        ).select_related(
            'campaign',
            'campaign__advertiser'
        ).annotate(
            status_order=Case(
                When(status='submitted', then=1),
                When(status='selected', then=2),
                When(status='rejected', then=3),
                default=4,
                output_field=IntegerField()
            )
        ).order_by('status_order', '-created_at')

    @staticmethod
    def get_proposal_count_by_status(influencer_id: int) -> Dict[str, int]:
        """
        Get proposal count grouped by status for a specific influencer.

        Args:
            influencer_id: ID of the influencer

        Returns:
            Dictionary with status as key and count as value
        """
        counts = Proposal.objects.filter(
            influencer_id=influencer_id
        ).values('status').annotate(count=Count('id'))

        return {item['status']: item['count'] for item in counts}

    @staticmethod
    def get_proposals_by_influencer(influencer_id: int) -> QuerySet[Proposal]:
        """
        Get all proposals submitted by a specific influencer.
        (Legacy method - use get_influencer_proposals for sorted results)

        Args:
            influencer_id: ID of the influencer

        Returns:
            QuerySet of proposals with campaign and advertiser data
        """
        return Proposal.objects.filter(
            influencer_id=influencer_id
        ).select_related(
            'campaign',
            'campaign__advertiser'
        ).order_by('-created_at')

    @staticmethod
    def get_proposals_by_campaign(campaign_id: int) -> QuerySet[Proposal]:
        """
        Get all proposals for a specific campaign.

        Args:
            campaign_id: ID of the campaign

        Returns:
            QuerySet of proposals with influencer data
        """
        return Proposal.objects.filter(
            campaign_id=campaign_id
        ).select_related('influencer').order_by('-created_at')

    @staticmethod
    def get_selected_proposals(campaign_id: int) -> QuerySet[Proposal]:
        """
        Get selected proposals for a campaign.

        Args:
            campaign_id: ID of the campaign

        Returns:
            QuerySet of selected proposals
        """
        return Proposal.objects.filter(
            campaign_id=campaign_id,
            status='selected'
        ).select_related('influencer')
