"""
Forms for user authentication and registration.
"""

from django import forms
from django.core.exceptions import ValidationError
from datetime import date
import re
from .models import User, AdvertiserProfile


class SignupForm(forms.Form):
    """
    통합 회원가입 폼 (광고주/인플루언서 공통)

    역할 선택에 따라 조건부 필드 검증
    """

    # 공통 필드
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '최소 8자, 영문+숫자 조합'
        })
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호 확인'
        })
    )
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '홍길동'
        })
    )
    contact = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '010-1234-5678'
        })
    )
    role = forms.ChoiceField(
        choices=[
            ('advertiser', '광고주'),
            ('influencer', '인플루언서')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    terms_agreed = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # 광고주 전용 필드 (선택)
    company_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '업체명'
        })
    )
    business_registration_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123-45-67890'
        })
    )

    # 인플루언서 전용 필드 (선택)
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    sns_link = forms.URLField(
        max_length=2048,
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://blog.naver.com/username'
        })
    )

    def clean_email(self):
        """이메일 중복 검증"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('이미 가입된 이메일입니다.')
        return email

    def clean_contact(self):
        """연락처 중복 검증"""
        contact = self.cleaned_data.get('contact')
        if User.objects.filter(contact=contact).exists():
            raise ValidationError('이미 가입된 연락처입니다.')
        return contact

    def clean_password(self):
        """비밀번호 강도 검증"""
        password = self.cleaned_data.get('password')

        if len(password) < 8:
            raise ValidationError('비밀번호는 최소 8자 이상이어야 합니다.')

        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise ValidationError('비밀번호는 영문자와 숫자를 포함해야 합니다.')

        return password

    def clean_business_registration_number(self):
        """사업자등록번호 형식 및 중복 검증"""
        number = self.cleaned_data.get('business_registration_number')
        role = self.data.get('role')

        # 광고주가 아니면 검증 스킵
        if role != 'advertiser':
            return number

        if not number:
            raise ValidationError('사업자등록번호를 입력해주세요.')

        # 형식 검증 (XXX-XX-XXXXX)
        pattern = r'^\d{3}-\d{2}-\d{5}$'
        if not re.match(pattern, number):
            raise ValidationError('사업자등록번호는 XXX-XX-XXXXX 형식이어야 합니다.')

        # 중복 검증
        if AdvertiserProfile.objects.filter(business_registration_number=number).exists():
            raise ValidationError('이미 등록된 사업자등록번호입니다.')

        return number

    def clean_birth_date(self):
        """생년월일 만 14세 이상 검증"""
        birth_date = self.cleaned_data.get('birth_date')
        role = self.data.get('role')

        # 인플루언서가 아니면 검증 스킵
        if role != 'influencer':
            return birth_date

        if not birth_date:
            raise ValidationError('생년월일을 입력해주세요.')

        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        if age < 14:
            raise ValidationError('만 14세 이상만 가입 가능합니다.')

        return birth_date

    def clean_sns_link(self):
        """SNS 링크 검증 (인플루언서 전용)"""
        sns_link = self.cleaned_data.get('sns_link')
        role = self.data.get('role')

        if role == 'influencer' and not sns_link:
            raise ValidationError('SNS 채널 링크를 입력해주세요.')

        return sns_link

    def clean_company_name(self):
        """업체명 검증 (광고주 전용)"""
        company_name = self.cleaned_data.get('company_name')
        role = self.data.get('role')

        if role == 'advertiser' and not company_name:
            raise ValidationError('업체명을 입력해주세요.')

        return company_name

    def clean_terms_agreed(self):
        """약관 동의 검증"""
        terms_agreed = self.cleaned_data.get('terms_agreed')
        if not terms_agreed:
            raise ValidationError('이용약관 및 개인정보처리방침에 동의해주세요.')
        return terms_agreed

    def clean(self):
        """전체 폼 검증 (비밀번호 일치 확인)"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError('비밀번호가 일치하지 않습니다.')

        return cleaned_data
