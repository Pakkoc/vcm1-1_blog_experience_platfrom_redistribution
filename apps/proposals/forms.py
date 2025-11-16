"""
Forms for proposal application.
"""

from django import forms
from datetime import date


class ProposalCreateForm(forms.Form):
    """Form for creating a new proposal"""

    cover_letter = forms.CharField(
        label="각오 한마디",
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '이 체험단에 선정되어야 하는 이유를 간단히 작성해주세요.',
            'maxlength': 500,
        }),
        error_messages={
            'required': '각오 한마디를 입력해주세요.',
            'max_length': '500자 이내로 입력해주세요.',
        }
    )

    desired_visit_date = forms.DateField(
        label="방문 희망일",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': date.today().isoformat(),
        }),
        error_messages={
            'required': '방문 희망일을 선택해주세요.',
            'invalid': '올바른 날짜를 입력해주세요.',
        }
    )

    def clean_cover_letter(self):
        """Validate cover letter"""
        cover_letter = self.cleaned_data.get('cover_letter')

        if not cover_letter or not cover_letter.strip():
            raise forms.ValidationError('각오 한마디를 입력해주세요.')

        if len(cover_letter) > 500:
            raise forms.ValidationError('500자 이내로 입력해주세요.')

        return cover_letter.strip()

    def clean_desired_visit_date(self):
        """Validate desired visit date"""
        visit_date = self.cleaned_data.get('desired_visit_date')

        if not visit_date:
            raise forms.ValidationError('방문 희망일을 선택해주세요.')

        if visit_date < date.today():
            raise forms.ValidationError('오늘 이후 날짜를 선택해주세요.')

        return visit_date
