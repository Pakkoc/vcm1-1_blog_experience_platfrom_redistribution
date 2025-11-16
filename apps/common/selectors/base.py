"""
Base Selector class for query optimization.
"""

from typing import List, Optional
from django.db.models import QuerySet


class BaseSelector:
    """
    Base class for selector classes.

    Selectors encapsulate complex query logic and optimization.
    They are read-only and focus on data retrieval with proper joins/prefetches.

    Usage:
        class CampaignSelector(BaseSelector):
            @staticmethod
            def get_recruiting_campaigns():
                return Campaign.objects.filter(status='recruiting').select_related('advertiser')
    """
    pass
