"""
Campaign models for managing experiencer campaigns.
"""

from django.db import models
from django.conf import settings


class Campaign(models.Model):
    """Campaign model for experiencer programs"""

    STATUS_CHOICES = [
        ('recruiting', 'Recruiting'),
        ('recruitment_ended', 'Recruitment Ended'),
        ('selection_complete', 'Selection Complete'),
    ]

    advertiser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='campaigns',
        limit_choices_to={'role': 'advertiser'}
    )
    name = models.CharField(max_length=255)
    recruitment_start_date = models.DateField()
    recruitment_end_date = models.DateField()
    recruitment_count = models.IntegerField()
    benefits = models.TextField()
    mission = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='recruiting'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        verbose_name = 'campaign'
        verbose_name_plural = 'campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_recruiting(self):
        """Check if campaign is currently recruiting"""
        return self.status == 'recruiting'

    def can_apply(self):
        """Check if campaign accepts applications"""
        from datetime import date
        today = date.today()
        return (
            self.status == 'recruiting' and
            self.recruitment_start_date <= today <= self.recruitment_end_date
        )
