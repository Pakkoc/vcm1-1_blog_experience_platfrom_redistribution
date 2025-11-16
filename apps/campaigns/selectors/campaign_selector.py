"""
Selector layer for campaign queries.
"""

from typing import List, Optional
from django.db.models import QuerySet, Count, Q
from apps.campaigns.models import Campaign
from apps.proposals.models import Proposal
from apps.common.selectors.base import BaseSelector
from apps.campaigns.dto import ProposalDetailDTO


class CampaignSelector(BaseSelector):
    """Selector for campaign queries with optimizations"""

    @staticmethod
    def get_recruiting_campaigns() -> QuerySet[Campaign]:
        """
        Get all campaigns that are currently recruiting.

        Returns:
            QuerySet of recruiting campaigns ordered by newest first
        """
        return Campaign.objects.filter(
            status='recruiting'
        ).select_related('advertiser').order_by('-created_at')

    @staticmethod
    def get_campaigns_by_advertiser(advertiser_id: int) -> QuerySet[Campaign]:
        """
        특정 광고주가 등록한 모든 체험단을 조회합니다.

        - 지원자 수(proposal_count)를 함께 조회
        - 최신순 정렬
        - N+1 쿼리 방지

        Args:
            advertiser_id: ID of the advertiser

        Returns:
            QuerySet of campaigns with proposal counts
        """
        return Campaign.objects.filter(
            advertiser_id=advertiser_id
        ).select_related('advertiser').annotate(
            proposal_count=Count('proposals')
        ).order_by('-created_at')

    @staticmethod
    def get_campaign_detail(campaign_id: int) -> Campaign:
        """
        Get campaign detail with related data.

        Args:
            campaign_id: ID of the campaign

        Returns:
            Campaign instance

        Raises:
            Campaign.DoesNotExist: If campaign not found
        """
        return Campaign.objects.select_related('advertiser').get(id=campaign_id)

    @staticmethod
    def get_campaign_with_proposals_count(
        campaign_id: int,
        advertiser_id: int
    ) -> Optional[Campaign]:
        """
        Fetch campaign with proposal counts for advertiser detail view.

        Args:
            campaign_id: Campaign ID
            advertiser_id: Advertiser ID (for ownership verification)

        Returns:
            Campaign object with proposal counts annotated, or None
        """
        return Campaign.objects.annotate(
            total_proposals=Count('proposals'),
            submitted_proposals=Count(
                'proposals',
                filter=Q(proposals__status='submitted')
            ),
            selected_proposals=Count(
                'proposals',
                filter=Q(proposals__status='selected')
            ),
            rejected_proposals=Count(
                'proposals',
                filter=Q(proposals__status='rejected')
            )
        ).select_related('advertiser').filter(
            id=campaign_id,
            advertiser_id=advertiser_id
        ).first()

    @staticmethod
    def get_proposals_by_campaign(
        campaign_id: int
    ) -> List[ProposalDetailDTO]:
        """
        Fetch proposals for a campaign (converted to DTOs).

        Args:
            campaign_id: Campaign ID

        Returns:
            List of ProposalDetailDTO
        """
        proposals = Proposal.objects.filter(
            campaign_id=campaign_id
        ).select_related(
            'influencer',
            'influencer__influencer_profile'
        ).order_by('-created_at')

        return [
            ProposalDetailDTO(
                proposal_id=p.id,
                influencer_name=p.influencer.name,
                influencer_email=p.influencer.email,
                influencer_contact=p.influencer.contact,
                sns_link=p.influencer.influencer_profile.sns_link,
                cover_letter=p.cover_letter,
                desired_visit_date=p.desired_visit_date,
                status=p.status,
                created_at=p.created_at.strftime('%Y-%m-%d %H:%M')
            )
            for p in proposals
        ]
