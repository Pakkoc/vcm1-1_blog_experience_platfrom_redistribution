"""
Factory Boy factories for Campaign models.
"""

import factory
from factory.django import DjangoModelFactory
from datetime import date, timedelta
from .models import Campaign
from apps.users.factories import AdvertiserFactory


class CampaignFactory(DjangoModelFactory):
    """Factory for Campaign model"""

    class Meta:
        model = Campaign

    advertiser = factory.SubFactory(AdvertiserFactory)
    name = factory.Sequence(lambda n: f'체험단 {n}')
    recruitment_start_date = date.today()
    recruitment_end_date = date.today() + timedelta(days=14)
    recruitment_count = 10
    benefits = '제품 무료 제공 + 소정의 원고료'
    mission = '방문 후 블로그 리뷰 작성'
    status = 'recruiting'
