"""
Data Transfer Objects for campaigns app.
"""

from dataclasses import dataclass
from datetime import date
from typing import List
from apps.common.dto.base import BaseDTO


@dataclass(frozen=True)
class CampaignCreateDTO(BaseDTO):
    """DTO for creating a new campaign"""
    name: str
    recruitment_start_date: date
    recruitment_end_date: date
    recruitment_count: int
    benefits: str
    mission: str


@dataclass(frozen=True)
class CampaignCloseDTO(BaseDTO):
    """DTO for closing campaign recruitment"""
    campaign_id: int


@dataclass(frozen=True)
class InfluencerSelectionDTO(BaseDTO):
    """DTO for selecting influencers for a campaign"""
    campaign_id: int
    selected_proposal_ids: List[int]


@dataclass(frozen=True)
class InfluencerSelectionResultDTO(BaseDTO):
    """DTO for influencer selection result"""
    campaign_id: int
    selected_count: int
    rejected_count: int
    campaign_status: str


@dataclass(frozen=True)
class ProposalDetailDTO(BaseDTO):
    """DTO for proposal details (for display purposes)"""
    proposal_id: int
    influencer_name: str
    influencer_email: str
    influencer_contact: str
    sns_link: str
    cover_letter: str
    desired_visit_date: date
    status: str
    created_at: str
