"""
Campaign forms - Phase 3
"""

from django import forms
from django.core.exceptions import ValidationError
from apps.campaigns.models import Campaign


class CampaignCreateForm(forms.ModelForm):
    """체험단 생성 폼"""

    class Meta:
        model = Campaign
        fields = [
            'name',
            'recruitment_start_date',
            'recruitment_end_date',
            'recruitment_count',
            'benefits',
            'mission'
        ]
        widgets = {
            'recruitment_start_date': forms.DateInput(attrs={'type': 'date'}),
            'recruitment_end_date': forms.DateInput(attrs={'type': 'date'}),
            'benefits': forms.Textarea(attrs={'rows': 4}),
            'mission': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        """날짜 논리 검증"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('recruitment_start_date')
        end_date = cleaned_data.get('recruitment_end_date')

        if start_date and end_date and end_date < start_date:
            raise ValidationError("모집 종료일은 시작일과 같거나 이후여야 합니다.")

        return cleaned_data
