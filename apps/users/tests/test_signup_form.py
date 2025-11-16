"""
Test cases for SignupForm following TDD approach.
"""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from apps.users.models import User, AdvertiserProfile
from apps.users.forms import SignupForm


@pytest.mark.django_db
class TestSignupFormValidation:
    """Test cases for SignupForm validation"""

    def test_signup_form_with_valid_influencer_data_succeeds(self):
        """SignupForm with valid influencer data should be valid"""
        form_data = {
            'email': 'new@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '홍길동',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_signup_form_with_valid_advertiser_data_succeeds(self):
        """SignupForm with valid advertiser data should be valid"""
        form_data = {
            'email': 'advertiser@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '광고주',
            'contact': '010-9999-8888',
            'role': 'advertiser',
            'company_name': '테스트 회사',
            'business_registration_number': '123-45-67890',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_signup_form_with_duplicate_email_fails(self):
        """SignupForm with duplicate email should fail"""
        User.objects.create_user(
            email='existing@example.com',
            password='testpass123',
            name='Existing User',
            contact='010-0000-0000',
            role='influencer'
        )

        form_data = {
            'email': 'existing@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '새 사용자',
            'contact': '010-1111-1111',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_signup_form_with_duplicate_contact_fails(self):
        """SignupForm with duplicate contact should fail"""
        User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User 1',
            contact='010-1234-5678',
            role='influencer'
        )

        form_data = {
            'email': 'user2@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': 'User 2',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'contact' in form.errors

    def test_signup_form_password_mismatch_fails(self):
        """SignupForm with password mismatch should fail"""
        form_data = {
            'email': 'test@example.com',
            'password': 'Password123',
            'password_confirm': 'Different123',
            'name': '홍길동',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert '__all__' in form.errors or 'password_confirm' in form.errors

    def test_signup_form_invalid_business_number_format_fails(self):
        """SignupForm with invalid business number format should fail"""
        form_data = {
            'email': 'advertiser@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '광고주',
            'contact': '010-9999-8888',
            'role': 'advertiser',
            'company_name': '테스트 회사',
            'business_registration_number': '12345',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'business_registration_number' in form.errors

    def test_signup_form_under_14_age_fails(self):
        """SignupForm with under 14 age should fail"""
        today = date.today()
        birth_date = today - timedelta(days=14*365 - 1)

        form_data = {
            'email': 'minor@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '미성년자',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': birth_date.strftime('%Y-%m-%d'),
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'birth_date' in form.errors

    def test_signup_form_password_min_length_validation(self):
        """SignupForm password should have minimum 8 characters"""
        form_data = {
            'email': 'test@example.com',
            'password': 'Pass1',
            'password_confirm': 'Pass1',
            'name': '홍길동',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_signup_form_password_must_contain_letter_and_number(self):
        """SignupForm password should contain both letter and number"""
        form_data = {
            'email': 'test@example.com',
            'password': 'onlyletters',
            'password_confirm': 'onlyletters',
            'name': '홍길동',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_signup_form_terms_not_agreed_fails(self):
        """SignupForm without terms agreement should fail"""
        form_data = {
            'email': 'test@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '홍길동',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': False
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'terms_agreed' in form.errors

    def test_signup_form_duplicate_business_number_fails(self):
        """SignupForm with duplicate business registration number should fail"""
        user = User.objects.create_user(
            email='existing@example.com',
            password='testpass123',
            name='Existing Advertiser',
            contact='010-0000-0000',
            role='advertiser'
        )
        AdvertiserProfile.objects.create(
            user=user,
            company_name='기존 회사',
            business_registration_number='123-45-67890'
        )

        form_data = {
            'email': 'new@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '새 광고주',
            'contact': '010-1111-1111',
            'role': 'advertiser',
            'company_name': '새 회사',
            'business_registration_number': '123-45-67890',
            'terms_agreed': True
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'business_registration_number' in form.errors
