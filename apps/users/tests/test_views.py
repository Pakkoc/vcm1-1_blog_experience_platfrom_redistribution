"""
Test cases for user views following TDD approach.
"""

import pytest
from django.urls import reverse
from django.test import Client
from apps.users.models import User, AdvertiserProfile, InfluencerProfile


@pytest.mark.django_db
class TestSignupView:
    """Test cases for SignupView"""

    def test_signup_view_get_renders_form(self, client: Client):
        """GET /accounts/signup/ should render signup form"""
        response = client.get('/accounts/signup/')

        assert response.status_code == 200
        assert 'form' in response.context
        assert b'signup' in response.content.lower() or '회원가입'.encode('utf-8') in response.content

    def test_signup_view_post_with_valid_influencer_data_creates_user_and_redirects(self, client: Client):
        """POST with valid influencer data should create user and redirect to home"""
        form_data = {
            'email': 'influencer@test.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '인플루언서',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/test',
            'terms_agreed': True
        }

        response = client.post('/accounts/signup/', form_data)

        assert response.status_code == 302  # Redirect
        assert response.url == '/'  # Home page

        # Verify user was created
        assert User.objects.filter(email='influencer@test.com').exists()
        user = User.objects.get(email='influencer@test.com')
        assert user.role == 'influencer'
        assert hasattr(user, 'influencer_profile')

    def test_signup_view_post_with_valid_advertiser_data_redirects_to_home(self, client: Client):
        """POST with valid advertiser data should redirect to home"""
        form_data = {
            'email': 'advertiser@test.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '광고주',
            'contact': '010-9999-8888',
            'role': 'advertiser',
            'company_name': '테스트 회사',
            'business_registration_number': '123-45-67890',
            'terms_agreed': True
        }

        response = client.post('/accounts/signup/', form_data)

        assert response.status_code == 302  # Redirect
        assert response.url == '/'

        # Verify user was created
        assert User.objects.filter(email='advertiser@test.com').exists()
        user = User.objects.get(email='advertiser@test.com')
        assert user.role == 'advertiser'
        assert hasattr(user, 'advertiser_profile')

    def test_signup_view_post_with_invalid_data_returns_errors(self, client: Client):
        """POST with invalid data should return form with errors"""
        form_data = {
            'email': 'invalid@test.com',
            'password': 'Password123',
            'password_confirm': 'DifferentPassword123',  # Password mismatch
            'name': '테스트',
            'contact': '010-1234-5678',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://test.com',
            'terms_agreed': True
        }

        response = client.post('/accounts/signup/', form_data)

        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
        assert not User.objects.filter(email='invalid@test.com').exists()

    def test_authenticated_user_accessing_signup_redirects_to_home(self, client: Client):
        """Authenticated user accessing signup should be redirected to home"""
        # Create and login user
        user = User.objects.create_user(
            email='existing@test.com',
            password='testpass123',
            name='Existing User',
            contact='010-0000-0000',
            role='influencer'
        )
        client.force_login(user)

        response = client.get('/accounts/signup/')

        assert response.status_code == 302
        assert response.url == '/'

    def test_signup_view_auto_login_after_successful_signup(self, client: Client):
        """User should be automatically logged in after successful signup"""
        form_data = {
            'email': 'autologin@test.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '자동로그인',
            'contact': '010-5555-5555',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://test.com',
            'terms_agreed': True
        }

        response = client.post('/accounts/signup/', form_data, follow=True)

        assert response.status_code == 200
        # Check if user is logged in (session contains auth user id)
        assert '_auth_user_id' in client.session

    def test_signup_view_duplicate_email_shows_error(self, client: Client):
        """Signup with duplicate email should show error"""
        # Create existing user
        User.objects.create_user(
            email='existing@test.com',
            password='testpass123',
            name='Existing User',
            contact='010-0000-0000',
            role='influencer'
        )

        form_data = {
            'email': 'existing@test.com',  # Duplicate
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '새 사용자',
            'contact': '010-1111-1111',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://test.com',
            'terms_agreed': True
        }

        response = client.post('/accounts/signup/', form_data)

        assert response.status_code == 200
        assert 'form' in response.context
        assert 'email' in response.context['form'].errors
