"""
Admin configuration for campaigns app.
"""

from django.contrib import admin
from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin for Campaign model"""

    list_display = ['name', 'advertiser', 'status', 'recruitment_start_date', 'recruitment_end_date', 'recruitment_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'advertiser__name', 'advertiser__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
