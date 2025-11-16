"""
Proposal models for campaign applications.
"""

from django.db import models
from django.conf import settings
from apps.campaigns.models import Campaign


class Proposal(models.Model):
    """Proposal model for influencer campaign applications"""

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    influencer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='proposals',
        limit_choices_to={'role': 'influencer'}
    )
    cover_letter = models.TextField()
    desired_visit_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proposals'
        verbose_name = 'proposal'
        verbose_name_plural = 'proposals'
        ordering = ['-created_at']
        unique_together = [['campaign', 'influencer']]

    def __str__(self):
        return f"{self.influencer.name} - {self.campaign.name}"

    def is_submitted(self):
        """Check if proposal is in submitted state"""
        return self.status == 'submitted'

    def is_selected(self):
        """Check if proposal is selected"""
        return self.status == 'selected'
