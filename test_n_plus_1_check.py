"""Quick N+1 query check"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from apps.campaigns.selectors.campaign_selectors import CampaignSelector
from apps.campaigns.models import Campaign
from apps.users.models import User, AdvertiserProfile
from datetime import date, timedelta

# Create test data
advertiser = User.objects.create_user(
    email='test@example.com',
    password='test',
    name='Test',
    contact='010-1234-5678',
    role='advertiser'
)
AdvertiserProfile.objects.create(
    user=advertiser,
    company_name='Test Company',
    business_registration_number='123-45-67890'
)

campaign = Campaign.objects.create(
    advertiser=advertiser,
    name='Test Campaign',
    recruitment_start_date=date.today(),
    recruitment_end_date=date.today() + timedelta(days=7),
    recruitment_count=10,
    benefits='Free',
    mission='Review',
    status='recruiting'
)

print("Testing N+1 query prevention...")
with CaptureQueriesContext(connection) as context:
    result = CampaignSelector.get_campaign_detail(campaign.id)
    # Access related objects
    _ = result.advertiser.name
    _ = result.advertiser.advertiser_profile.company_name

num_queries = len(context.captured_queries)
print(f"Number of queries: {num_queries}")

if num_queries == 1:
    print("✓ PASS: select_related working correctly (1 query)")
else:
    print(f"✗ FAIL: Expected 1 query, got {num_queries}")
    for i, query in enumerate(context.captured_queries, 1):
        print(f"\nQuery {i}:")
        print(query['sql'][:200])

# Cleanup
campaign.delete()
advertiser.delete()
