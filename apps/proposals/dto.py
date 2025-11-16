"""
Data Transfer Objects for proposals app.
"""

from dataclasses import dataclass
from datetime import date
from apps.common.dto.base import BaseDTO


@dataclass(frozen=True)
class ProposalCreateDTO(BaseDTO):
    """DTO for creating a new proposal"""
    campaign_id: int
    influencer_id: int
    cover_letter: str
    desired_visit_date: date
