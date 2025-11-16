"""
Test cases for user DTOs.
"""

import pytest
from datetime import date
from dataclasses import FrozenInstanceError
from apps.users.dto import SignupDTO


class TestSignupDTO:
    """Test cases for SignupDTO"""

    def test_signup_dto_creation_with_influencer_data(self):
        """SignupDTO should be created with influencer data"""
        dto = SignupDTO(
            email='influencer@test.com',
            password='Password123',
            name='인플루언서',
            contact='010-1234-5678',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://blog.naver.com/test'
        )

        assert dto.email == 'influencer@test.com'
        assert dto.password == 'Password123'
        assert dto.name == '인플루언서'
        assert dto.contact == '010-1234-5678'
        assert dto.role == 'influencer'
        assert dto.birth_date == date(1990, 1, 1)
        assert dto.sns_link == 'https://blog.naver.com/test'
        assert dto.company_name is None
        assert dto.business_registration_number is None

    def test_signup_dto_creation_with_advertiser_data(self):
        """SignupDTO should be created with advertiser data"""
        dto = SignupDTO(
            email='advertiser@test.com',
            password='Password123',
            name='광고주',
            contact='010-9999-8888',
            role='advertiser',
            company_name='테스트 회사',
            business_registration_number='123-45-67890'
        )

        assert dto.email == 'advertiser@test.com'
        assert dto.password == 'Password123'
        assert dto.name == '광고주'
        assert dto.contact == '010-9999-8888'
        assert dto.role == 'advertiser'
        assert dto.company_name == '테스트 회사'
        assert dto.business_registration_number == '123-45-67890'
        assert dto.birth_date is None
        assert dto.sns_link is None

    def test_signup_dto_immutability(self):
        """SignupDTO should be immutable"""
        dto = SignupDTO(
            email='test@test.com',
            password='Password123',
            name='테스트',
            contact='010-0000-0000',
            role='influencer',
            birth_date=date(1990, 1, 1),
            sns_link='https://test.com'
        )

        with pytest.raises(FrozenInstanceError):
            dto.email = 'new@test.com'

        with pytest.raises(FrozenInstanceError):
            dto.role = 'advertiser'

    def test_signup_dto_from_form_cleaned_data(self):
        """SignupDTO should be created from form cleaned_data"""
        # Simulating form.cleaned_data
        cleaned_data = {
            'email': 'formdata@test.com',
            'password': 'FormPass123',
            'name': '폼 데이터',
            'contact': '010-1111-2222',
            'role': 'influencer',
            'birth_date': date(1995, 5, 15),
            'sns_link': 'https://instagram.com/formdata'
        }

        dto = SignupDTO(**cleaned_data)

        assert dto.email == 'formdata@test.com'
        assert dto.password == 'FormPass123'
        assert dto.name == '폼 데이터'
        assert dto.contact == '010-1111-2222'
        assert dto.role == 'influencer'
        assert dto.birth_date == date(1995, 5, 15)
        assert dto.sns_link == 'https://instagram.com/formdata'
