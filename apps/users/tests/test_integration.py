"""
Integration tests for complete signup flow.
"""

import pytest
from django.test import Client
from apps.users.models import User, AdvertiserProfile, InfluencerProfile


@pytest.mark.django_db
class TestSignupIntegration:
    """Integration tests for full signup flow"""

    def test_full_signup_flow_influencer(self, client: Client):
        """Full influencer signup flow from GET to successful login"""
        # 1. Access signup page
        response = client.get('/accounts/signup/')
        assert response.status_code == 200
        assert 'form' in response.context

        # 2. Submit signup form
        form_data = {
            'email': 'influencer@integration.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '통합테스트 인플루언서',
            'contact': '010-1111-2222',
            'role': 'influencer',
            'birth_date': '1990-01-01',
            'sns_link': 'https://blog.naver.com/integration',
            'terms_agreed': True
        }
        response = client.post('/accounts/signup/', form_data, follow=True)

        # 3. Verify redirection
        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == '/'

        # 4. Verify database records
        user = User.objects.get(email='influencer@integration.com')
        assert user.role == 'influencer'
        assert user.name == '통합테스트 인플루언서'
        assert user.contact == '010-1111-2222'
        assert user.check_password('Password123')

        # Verify profile
        assert hasattr(user, 'influencer_profile')
        profile = user.influencer_profile
        assert profile.sns_link == 'https://blog.naver.com/integration'
        assert str(profile.birth_date) == '1990-01-01'

        # 5. Verify auto-login
        assert '_auth_user_id' in client.session
        assert int(client.session['_auth_user_id']) == user.id

    def test_full_signup_flow_advertiser(self, client: Client):
        """Full advertiser signup flow from GET to successful login"""
        # 1. Access signup page
        response = client.get('/accounts/signup/')
        assert response.status_code == 200

        # 2. Submit signup form
        form_data = {
            'email': 'advertiser@integration.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '통합테스트 광고주',
            'contact': '010-3333-4444',
            'role': 'advertiser',
            'company_name': '통합테스트 회사',
            'business_registration_number': '123-45-67890',
            'terms_agreed': True
        }
        response = client.post('/accounts/signup/', form_data, follow=True)

        # 3. Verify redirection
        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == '/'

        # 4. Verify database records
        user = User.objects.get(email='advertiser@integration.com')
        assert user.role == 'advertiser'
        assert user.name == '통합테스트 광고주'
        assert user.check_password('Password123')

        # Verify profile
        assert hasattr(user, 'advertiser_profile')
        profile = user.advertiser_profile
        assert profile.company_name == '통합테스트 회사'
        assert profile.business_registration_number == '123-45-67890'

        # 5. Verify auto-login
        assert '_auth_user_id' in client.session
        assert int(client.session['_auth_user_id']) == user.id

    def test_signup_with_duplicate_email_shows_error_on_form(self, client: Client):
        """Signup with duplicate email should show error on the form"""
        # Create existing user
        User.objects.create_user(
            email='existing@integration.com',
            password='testpass123',
            name='Existing User',
            contact='010-0000-0000',
            role='influencer'
        )

        # Attempt to signup with same email
        form_data = {
            'email': 'existing@integration.com',
            'password': 'Password123',
            'password_confirm': 'Password123',
            'name': '새 사용자',
            'contact': '010-5555-5555',
            'role': 'influencer',
            'birth_date': '1995-05-05',
            'sns_link': 'https://test.com',
            'terms_agreed': True
        }
        response = client.post('/accounts/signup/', form_data)

        # Should stay on signup page with errors
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'email' in response.context['form'].errors

        # Should not create duplicate user
        assert User.objects.filter(email='existing@integration.com').count() == 1

    def test_signup_form_validation_errors_displayed(self, client: Client):
        """Form validation errors should be displayed correctly"""
        form_data = {
            'email': 'invalid@test.com',
            'password': 'short',  # Too short
            'password_confirm': 'different',  # Mismatch
            'name': '테스트',
            'contact': '010-9999-9999',
            'role': 'influencer',
            'birth_date': '2015-01-01',  # Under 14
            'sns_link': 'not-a-url',  # Invalid URL
            'terms_agreed': False  # Not agreed
        }
        response = client.post('/accounts/signup/', form_data)

        assert response.status_code == 200
        form = response.context['form']

        # Multiple validation errors should exist
        assert not form.is_valid()
        assert form.errors  # Has errors

        # No user should be created
        assert not User.objects.filter(email='invalid@test.com').exists()
