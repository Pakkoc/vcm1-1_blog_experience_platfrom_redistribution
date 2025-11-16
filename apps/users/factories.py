"""
Factory Boy factories for User models.
"""

import factory
from factory.django import DjangoModelFactory
from .models import User, AdvertiserProfile, InfluencerProfile


class UserFactory(DjangoModelFactory):
    """Factory for User model"""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@test.com')
    name = factory.Faker('name')
    contact = factory.Sequence(lambda n: f'010-{n:04d}-5678')
    role = 'influencer'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use create_user method"""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class AdvertiserFactory(UserFactory):
    """Factory for Advertiser User"""
    role = 'advertiser'


class InfluencerFactory(UserFactory):
    """Factory for Influencer User"""
    role = 'influencer'


class AdvertiserProfileFactory(DjangoModelFactory):
    """Factory for AdvertiserProfile model"""

    class Meta:
        model = AdvertiserProfile

    user = factory.SubFactory(AdvertiserFactory)
    company_name = factory.Faker('company')
    business_registration_number = factory.Sequence(lambda n: f'{n:03d}-{n:02d}-{n:05d}')


class InfluencerProfileFactory(DjangoModelFactory):
    """Factory for InfluencerProfile model"""

    class Meta:
        model = InfluencerProfile

    user = factory.SubFactory(InfluencerFactory)
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=60)
    sns_link = factory.Faker('url')
