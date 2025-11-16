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
    """Factory for Advertiser User with profile"""
    role = 'advertiser'

    @factory.post_generation
    def advertiser_profile(obj, create, extracted, **kwargs):
        """Create advertiser profile after user creation"""
        if not create:
            return

        if not hasattr(obj, 'advertiser_profile'):
            AdvertiserProfile.objects.create(
                user=obj,
                company_name=kwargs.get('company_name', f'{obj.name}의 회사'),
                business_registration_number=kwargs.get('business_registration_number', '123-45-67890')
            )


class InfluencerFactory(UserFactory):
    """Factory for Influencer User with profile"""
    role = 'influencer'

    @factory.post_generation
    def influencer_profile(obj, create, extracted, **kwargs):
        """Create influencer profile after user creation"""
        if not create:
            return

        if not hasattr(obj, 'influencer_profile'):
            import datetime
            InfluencerProfile.objects.create(
                user=obj,
                birth_date=kwargs.get('birth_date', datetime.date(1990, 1, 1)),
                sns_link=kwargs.get('sns_link', 'https://blog.naver.com/test')
            )


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
