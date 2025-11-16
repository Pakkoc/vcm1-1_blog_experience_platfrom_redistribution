"""
Admin configuration for proposals app.
"""

from django.contrib import admin
from .models import Proposal


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Admin for Proposal model"""

    list_display = ['influencer', 'campaign', 'status', 'desired_visit_date', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['influencer__name', 'influencer__email', 'campaign__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
