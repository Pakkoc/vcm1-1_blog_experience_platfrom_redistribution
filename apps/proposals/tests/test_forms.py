"""
Unit tests for proposal forms.
"""

import pytest
from datetime import date, timedelta
from apps.proposals.forms import ProposalCreateForm


class TestProposalCreateForm:
    """Test ProposalCreateForm"""

    def test_form_valid_data(self):
        """Test form with valid data"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'cover_letter': 'I really want to participate in this campaign!',
            'desired_visit_date': tomorrow.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['cover_letter'] == 'I really want to participate in this campaign!'
        assert form.cleaned_data['desired_visit_date'] == tomorrow

    def test_form_missing_cover_letter(self):
        """Test form without cover letter"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'desired_visit_date': tomorrow.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert not form.is_valid()
        assert 'cover_letter' in form.errors

    def test_form_empty_cover_letter(self):
        """Test form with empty cover letter"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'cover_letter': '   ',  # Only whitespace
            'desired_visit_date': tomorrow.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert not form.is_valid()
        assert 'cover_letter' in form.errors

    def test_form_cover_letter_too_long(self):
        """Test form with cover letter exceeding max length"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'cover_letter': 'A' * 501,  # 501 characters
            'desired_visit_date': tomorrow.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert not form.is_valid()
        assert 'cover_letter' in form.errors

    def test_form_cover_letter_exactly_max_length(self):
        """Test form with cover letter at max length (500 chars)"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'cover_letter': 'A' * 500,  # Exactly 500 characters
            'desired_visit_date': tomorrow.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert form.is_valid()

    def test_form_missing_desired_visit_date(self):
        """Test form without desired visit date"""
        data = {
            'cover_letter': 'I want to participate!'
        }

        form = ProposalCreateForm(data=data)
        assert not form.is_valid()
        assert 'desired_visit_date' in form.errors

    def test_form_past_desired_visit_date(self):
        """Test form with past desired visit date"""
        yesterday = date.today() - timedelta(days=1)
        data = {
            'cover_letter': 'I want to participate!',
            'desired_visit_date': yesterday.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert not form.is_valid()
        assert 'desired_visit_date' in form.errors
        assert '오늘 이후 날짜를 선택해주세요' in str(form.errors['desired_visit_date'])

    def test_form_today_desired_visit_date(self):
        """Test form with today as desired visit date"""
        today = date.today()
        data = {
            'cover_letter': 'I want to participate!',
            'desired_visit_date': today.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert form.is_valid()

    def test_form_future_desired_visit_date(self):
        """Test form with future desired visit date"""
        future_date = date.today() + timedelta(days=30)
        data = {
            'cover_letter': 'I want to participate!',
            'desired_visit_date': future_date.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert form.is_valid()

    def test_form_invalid_date_format(self):
        """Test form with invalid date format"""
        data = {
            'cover_letter': 'I want to participate!',
            'desired_visit_date': 'invalid-date'
        }

        form = ProposalCreateForm(data=data)
        assert not form.is_valid()
        assert 'desired_visit_date' in form.errors

    def test_form_whitespace_trimming(self):
        """Test that cover letter whitespace is trimmed"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'cover_letter': '  I want to participate!  ',
            'desired_visit_date': tomorrow.isoformat()
        }

        form = ProposalCreateForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['cover_letter'] == 'I want to participate!'
