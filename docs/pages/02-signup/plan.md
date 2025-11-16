# 회원가입 & 온보딩 페이지 구현 계획

## 프로젝트 ID: PLAN-002

### 제목
회원가입 & 온보딩 페이지 (광고주 / 인플루언서)

---

## 1. 개요

### 1.1 목표
광고주와 인플루언서가 각자의 역할에 맞는 정보를 입력하여 회원가입하고, 자동 로그인 후 각 역할에 맞는 페이지로 리디렉션되는 온보딩 프로세스를 구현한다.

### 1.2 참고 문서
- **유스케이스**:
  - `docs/usecases/01-influencer-signup/spec.md`
  - `docs/usecases/04-advertiser-signup/spec.md`
- **데이터베이스 스키마**: `docs/database.md`
- **유저 플로우**: `docs/userflow.md`
- **공통 모듈**: `docs/common-modules.md`

### 1.3 범위

**포함 사항**:
- 공통 정보 입력 폼 (이름, 이메일, 연락처, 비밀번호, 약관동의)
- 역할 선택 (광고주 / 인플루언서) 라디오 버튼
- 역할별 조건부 필드 표시
  - 광고주: 업체명, 사업자등록번호
  - 인플루언서: 생년월일, SNS 링크
- 서버 측 유효성 검증 및 중복 확인
- 트랜잭션 기반 User + Profile 생성
- 자동 로그인 및 역할별 리디렉션
  - 광고주 → 체험단 관리 페이지
  - 인플루언서 → 홈 페이지
- 에러 처리 및 사용자 피드백

**제외 사항**:
- 이메일 인증 프로세스 (MVP 범위 외)
- SNS 채널 실제 검증 (URL 형식 검증만)
- 사업자등록번호 국세청 API 검증 (형식 검증만)
- 소셜 로그인 (MVP 범위 외)
- 프로필 사진 업로드

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (Railway Volume 경로)
- **인증**: Django Authentication System (AbstractBaseUser)
- **트랜잭션**: `transaction.atomic()`
- **테스트**: pytest-django

### 2.2 프론트엔드
- **템플릿 엔진**: Django Template
- **UI 프레임워크**: Bootstrap 5.3
- **JavaScript**: Vanilla JS (역할 선택 시 조건부 필드 표시)
- **폼 검증**: HTML5 Validation + Django Form Validation

### 2.3 아키텍처 패턴
- Layered Architecture
  - Presentation: Views, Forms, Templates
  - Business Logic: Services
  - Data Access: Models, Selectors (필요시)
- DTO 패턴 활용

---

## 3. 데이터베이스 마이그레이션

### 3.1 기존 테이블 (이미 정의됨)

**users 테이블**:
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(20) UNIQUE NOT NULL,
    role user_role NOT NULL,  -- 'advertiser' or 'influencer'
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**advertiser_profiles 테이블**:
```sql
CREATE TABLE advertiser_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    business_registration_number VARCHAR(50) UNIQUE NOT NULL
);
```

**influencer_profiles 테이블**:
```sql
CREATE TABLE influencer_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    birth_date DATE NOT NULL,
    sns_link VARCHAR(2048) NOT NULL
);
```

### 3.2 마이그레이션 실행 순서
1. `apps/users/models.py`에 모델 정의 (Phase 1에서 완료)
2. `python manage.py makemigrations users`
3. `python manage.py migrate users`

**확인 사항**:
- SQLite에서는 ENUM 타입이 없으므로 CharField with choices 사용
- Django에서는 BIGSERIAL 대신 AutoField 사용
- TIMESTAMPTZ 대신 DateTimeField(auto_now_add=True, auto_now=True) 사용

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: 모델 및 폼 정의 (TDD)

**목표**: User 모델과 Profile 모델, 회원가입 폼의 기본 구조 완성

**작업 항목**:

1. **User 모델 정의**
   - 파일: `apps/users/models.py`
   - 설명:
     - AbstractBaseUser를 상속한 커스텀 User 모델 생성
     - 필드: email (unique), password, name, contact (unique), role (choices)
     - USERNAME_FIELD = 'email'
     - UserManager 정의 (create_user, create_superuser)
   - 의존성: 없음
   - 테스트:
     ```python
     # apps/users/tests/test_models.py
     def test_create_user_with_valid_data_succeeds(db):
         user = User.objects.create_user(
             email='test@example.com',
             password='Password123',
             name='홍길동',
             contact='010-1234-5678',
             role='influencer'
         )
         assert user.email == 'test@example.com'
         assert user.check_password('Password123')

     def test_create_user_with_duplicate_email_raises_error(db):
         User.objects.create_user(email='test@example.com', ...)
         with pytest.raises(IntegrityError):
             User.objects.create_user(email='test@example.com', ...)
     ```

2. **Profile 모델 정의**
   - 파일: `apps/users/models.py`
   - 설명:
     - AdvertiserProfile: user (OneToOne), company_name, business_registration_number (unique)
     - InfluencerProfile: user (OneToOne), birth_date, sns_link
   - 의존성: User 모델
   - 테스트:
     ```python
     def test_create_advertiser_profile_succeeds(db):
         user = UserFactory(role='advertiser')
         profile = AdvertiserProfile.objects.create(
             user=user,
             company_name='테스트 업체',
             business_registration_number='123-45-67890'
         )
         assert profile.user == user

     def test_duplicate_business_number_raises_error(db):
         user1 = UserFactory(role='advertiser')
         user2 = UserFactory(role='advertiser')
         AdvertiserProfile.objects.create(user=user1, business_registration_number='123-45-67890', ...)
         with pytest.raises(IntegrityError):
             AdvertiserProfile.objects.create(user=user2, business_registration_number='123-45-67890', ...)
     ```

3. **회원가입 폼 정의**
   - 파일: `apps/users/forms.py`
   - 설명:
     - SignupForm: 모든 필드 포함
     - clean_email(): 이메일 중복 검증
     - clean_contact(): 연락처 중복 검증
     - clean_business_registration_number(): 사업자번호 형식 및 중복 검증
     - clean(): 비밀번호 일치 검증, 생년월일 만 14세 이상 검증
   - 의존성: User, AdvertiserProfile, InfluencerProfile 모델
   - 테스트:
     ```python
     # apps/users/tests/test_forms.py
     def test_signup_form_with_valid_data_succeeds():
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
         assert form.is_valid()

     def test_signup_form_with_duplicate_email_fails(db):
         UserFactory(email='existing@example.com')
         form_data = {..., 'email': 'existing@example.com'}
         form = SignupForm(data=form_data)
         assert not form.is_valid()
         assert 'email' in form.errors

     def test_signup_form_password_mismatch_fails():
         form_data = {..., 'password': 'Pass123', 'password_confirm': 'Different123'}
         form = SignupForm(data=form_data)
         assert not form.is_valid()
         assert 'password_confirm' in form.errors

     def test_signup_form_invalid_business_number_format_fails():
         form_data = {..., 'role': 'advertiser', 'business_registration_number': '12345'}
         form = SignupForm(data=form_data)
         assert not form.is_valid()
         assert 'business_registration_number' in form.errors

     def test_signup_form_under_14_age_fails():
         today = date.today()
         birth_date = today - timedelta(days=14*365 - 1)  # 만 14세 미만
         form_data = {..., 'birth_date': birth_date}
         form = SignupForm(data=form_data)
         assert not form.is_valid()
         assert 'birth_date' in form.errors
     ```

**Acceptance Tests**:
- [ ] User 모델 생성 및 조회 성공
- [ ] Email, Contact 중복 시 IntegrityError 발생
- [ ] Profile 모델 생성 및 User와 1:1 연결 확인
- [ ] Form 유효성 검증이 모든 규칙 통과
- [ ] Form 오류 메시지가 적절히 반환됨

---

### Phase 2: DTO 및 Service 구현 (TDD)

**목표**: 비즈니스 로직을 Service 계층으로 분리하고 DTO 기반 데이터 계약 정의

**작업 항목**:

1. **SignupDTO 정의**
   - 파일: `apps/users/dto.py`
   - 설명:
     ```python
     from dataclasses import dataclass
     from datetime import date
     from typing import Optional
     from apps.common.dto.base import BaseDTO

     @dataclass(frozen=True)
     class SignupDTO(BaseDTO):
         email: str
         password: str
         name: str
         contact: str
         role: str  # 'advertiser' or 'influencer'

         # 광고주 전용 (Optional)
         company_name: Optional[str] = None
         business_registration_number: Optional[str] = None

         # 인플루언서 전용 (Optional)
         birth_date: Optional[date] = None
         sns_link: Optional[str] = None
     ```
   - 의존성: BaseDTO
   - 테스트:
     ```python
     # apps/users/tests/test_dto.py
     def test_signup_dto_immutability():
         dto = SignupDTO(email='test@example.com', password='pass', ...)
         with pytest.raises(FrozenInstanceError):
             dto.email = 'new@example.com'

     def test_signup_dto_advertiser_fields():
         dto = SignupDTO(role='advertiser', company_name='회사', business_registration_number='123-45-67890', ...)
         assert dto.company_name == '회사'

     def test_signup_dto_influencer_fields():
         dto = SignupDTO(role='influencer', birth_date=date(1990, 1, 1), sns_link='https://...', ...)
         assert dto.birth_date.year == 1990
     ```

2. **SignupService 구현**
   - 파일: `apps/users/services/signup_service.py`
   - 설명:
     ```python
     from django.db import transaction
     from django.contrib.auth import get_user_model
     from apps.common.services.base import BaseService
     from apps.common.exceptions import DuplicateActionException
     from ..dto import SignupDTO
     from ..models import AdvertiserProfile, InfluencerProfile

     User = get_user_model()

     class SignupService(BaseService[SignupDTO, User]):
         @transaction.atomic
         def execute(self, dto: SignupDTO, user=None) -> User:
             # 1. 중복 확인 (추가 안전장치)
             if User.objects.filter(email=dto.email).exists():
                 raise DuplicateActionException("이미 가입된 이메일입니다.")

             if User.objects.filter(contact=dto.contact).exists():
                 raise DuplicateActionException("이미 가입된 연락처입니다.")

             # 2. User 생성
             user = User.objects.create_user(
                 email=dto.email,
                 password=dto.password,
                 name=dto.name,
                 contact=dto.contact,
                 role=dto.role
             )

             # 3. 역할별 Profile 생성
             if dto.role == 'advertiser':
                 AdvertiserProfile.objects.create(
                     user=user,
                     company_name=dto.company_name,
                     business_registration_number=dto.business_registration_number
                 )
             elif dto.role == 'influencer':
                 InfluencerProfile.objects.create(
                     user=user,
                     birth_date=dto.birth_date,
                     sns_link=dto.sns_link
                 )

             return user
     ```
   - 의존성: SignupDTO, User 모델, Profile 모델
   - 테스트:
     ```python
     # apps/users/tests/test_services.py
     def test_signup_service_creates_user_and_profile(db):
         dto = SignupDTO(
             email='test@example.com',
             password='Password123',
             name='홍길동',
             contact='010-1234-5678',
             role='influencer',
             birth_date=date(1990, 1, 1),
             sns_link='https://blog.naver.com/test'
         )

         service = SignupService()
         user = service.execute(dto)

         assert user.email == 'test@example.com'
         assert user.role == 'influencer'
         assert hasattr(user, 'influencerprofile')
         assert user.influencerprofile.birth_date == date(1990, 1, 1)

     def test_signup_service_with_duplicate_email_raises_exception(db):
         UserFactory(email='existing@example.com')
         dto = SignupDTO(email='existing@example.com', ...)

         service = SignupService()
         with pytest.raises(DuplicateActionException):
             service.execute(dto)

     def test_signup_service_transaction_rollback_on_profile_error(db):
         # advertiser_profiles INSERT 실패 시뮬레이션
         dto = SignupDTO(role='advertiser', business_registration_number=None, ...)  # NOT NULL 위반

         service = SignupService()
         with pytest.raises(Exception):
             service.execute(dto)

         # User도 생성되지 않았는지 확인 (트랜잭션 롤백)
         assert not User.objects.filter(email=dto.email).exists()
     ```

**Acceptance Tests**:
- [ ] SignupService가 User와 Profile을 동시에 생성
- [ ] 중복 이메일/연락처 시 DuplicateActionException 발생
- [ ] 트랜잭션 실패 시 모든 변경사항 롤백
- [ ] DTO 불변성 보장

---

### Phase 3: View 및 URL 라우팅 구현

**목표**: HTTP 요청을 처리하고 Service를 호출하는 View 구현

**작업 항목**:

1. **SignupView 구현**
   - 파일: `apps/users/views.py`
   - 설명:
     ```python
     from django.shortcuts import render, redirect
     from django.views import View
     from django.contrib.auth import login
     from django.contrib import messages
     from apps.common.exceptions import DuplicateActionException
     from .forms import SignupForm
     from .dto import SignupDTO
     from .services.signup_service import SignupService

     class SignupView(View):
         template_name = 'users/signup.html'

         def get(self, request):
             # 이미 로그인한 사용자는 홈으로 리디렉션
             if request.user.is_authenticated:
                 return redirect('home')

             form = SignupForm()
             return render(request, self.template_name, {'form': form})

         def post(self, request):
             form = SignupForm(request.POST)

             if not form.is_valid():
                 return render(request, self.template_name, {'form': form})

             # DTO 생성
             cleaned_data = form.cleaned_data
             dto = SignupDTO(
                 email=cleaned_data['email'],
                 password=cleaned_data['password'],
                 name=cleaned_data['name'],
                 contact=cleaned_data['contact'],
                 role=cleaned_data['role'],
                 company_name=cleaned_data.get('company_name'),
                 business_registration_number=cleaned_data.get('business_registration_number'),
                 birth_date=cleaned_data.get('birth_date'),
                 sns_link=cleaned_data.get('sns_link')
             )

             # Service 실행
             try:
                 service = SignupService()
                 user = service.execute(dto)

                 # 자동 로그인
                 login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                 messages.success(request, '회원가입이 완료되었습니다.')

                 # 역할별 리디렉션
                 if user.role == 'advertiser':
                     return redirect('campaigns:manage_list')  # 체험단 관리 페이지
                 else:
                     return redirect('home')  # 홈 페이지

             except DuplicateActionException as e:
                 form.add_error(None, str(e))
                 return render(request, self.template_name, {'form': form})
             except Exception as e:
                 messages.error(request, '회원가입 처리 중 오류가 발생했습니다.')
                 return render(request, self.template_name, {'form': form})
     ```
   - 의존성: SignupForm, SignupDTO, SignupService
   - 테스트:
     ```python
     # apps/users/tests/test_views.py
     def test_signup_view_get_renders_form(client):
         response = client.get('/accounts/signup/')
         assert response.status_code == 200
         assert 'form' in response.context

     def test_signup_view_post_with_valid_data_creates_user_and_redirects(client, db):
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

         response = client.post('/accounts/signup/', form_data)

         assert response.status_code == 302  # Redirect
         assert response.url == '/'  # 홈 페이지
         assert User.objects.filter(email='new@example.com').exists()

     def test_signup_view_post_with_invalid_data_returns_errors(client, db):
         form_data = {..., 'password_confirm': 'Different123'}  # 비밀번호 불일치

         response = client.post('/accounts/signup/', form_data)

         assert response.status_code == 200
         assert 'form' in response.context
         assert response.context['form'].errors

     def test_signup_view_advertiser_redirects_to_campaign_manage(client, db):
         form_data = {..., 'role': 'advertiser', ...}

         response = client.post('/accounts/signup/', form_data)

         assert response.status_code == 302
         assert 'campaigns/manage' in response.url

     def test_authenticated_user_accessing_signup_redirects_to_home(client, influencer_user):
         client.force_login(influencer_user)
         response = client.get('/accounts/signup/')
         assert response.status_code == 302
         assert response.url == '/'
     ```

2. **URL 라우팅 설정**
   - 파일: `apps/users/urls.py`
   - 설명:
     ```python
     from django.urls import path
     from .views import SignupView

     app_name = 'users'

     urlpatterns = [
         path('signup/', SignupView.as_view(), name='signup'),
     ]
     ```
   - 파일: `config/urls.py` (기존 파일 수정)
   - 설명:
     ```python
     from django.urls import path, include

     urlpatterns = [
         path('accounts/', include('apps.users.urls', namespace='users')),
         ...
     ]
     ```
   - 의존성: SignupView

**Acceptance Tests**:
- [ ] GET /accounts/signup/ 접근 시 폼 렌더링
- [ ] POST 유효한 데이터로 제출 시 User 생성 및 리디렉션
- [ ] POST 무효한 데이터로 제출 시 에러 메시지 표시
- [ ] 광고주 가입 시 체험단 관리 페이지로 리디렉션
- [ ] 인플루언서 가입 시 홈 페이지로 리디렉션
- [ ] 로그인된 사용자 접근 시 홈으로 리디렉션

---

### Phase 4: 템플릿 구현 (Bootstrap 기반)

**목표**: 사용자 친화적인 회원가입 페이지 UI 구현

**작업 항목**:

1. **회원가입 템플릿 작성**
   - 파일: `apps/users/templates/users/signup.html`
   - 설명:
     ```django
     {% extends 'base.html' %}
     {% load static %}

     {% block title %}회원가입{% endblock %}

     {% block extra_css %}
     <style>
         .signup-container {
             max-width: 600px;
             margin: 50px auto;
         }
         .conditional-fields {
             display: none;
         }
         .conditional-fields.active {
             display: block;
         }
     </style>
     {% endblock %}

     {% block content %}
     <div class="signup-container">
         <h2 class="text-center mb-4">회원가입</h2>

         <form method="post" novalidate>
             {% csrf_token %}

             <!-- 공통 정보 섹션 -->
             <div class="card mb-3">
                 <div class="card-header">기본 정보</div>
                 <div class="card-body">
                     <!-- 이름 -->
                     <div class="mb-3">
                         <label for="id_name" class="form-label">이름 *</label>
                         {{ form.name }}
                         {% if form.name.errors %}
                             <div class="invalid-feedback d-block">{{ form.name.errors|first }}</div>
                         {% endif %}
                     </div>

                     <!-- 이메일 -->
                     <div class="mb-3">
                         <label for="id_email" class="form-label">이메일 *</label>
                         {{ form.email }}
                         {% if form.email.errors %}
                             <div class="invalid-feedback d-block">{{ form.email.errors|first }}</div>
                         {% endif %}
                     </div>

                     <!-- 연락처 -->
                     <div class="mb-3">
                         <label for="id_contact" class="form-label">연락처 *</label>
                         {{ form.contact }}
                         <small class="form-text text-muted">예: 010-1234-5678</small>
                         {% if form.contact.errors %}
                             <div class="invalid-feedback d-block">{{ form.contact.errors|first }}</div>
                         {% endif %}
                     </div>

                     <!-- 비밀번호 -->
                     <div class="mb-3">
                         <label for="id_password" class="form-label">비밀번호 *</label>
                         {{ form.password }}
                         <small class="form-text text-muted">최소 8자, 영문+숫자 조합</small>
                         {% if form.password.errors %}
                             <div class="invalid-feedback d-block">{{ form.password.errors|first }}</div>
                         {% endif %}
                     </div>

                     <!-- 비밀번호 확인 -->
                     <div class="mb-3">
                         <label for="id_password_confirm" class="form-label">비밀번호 확인 *</label>
                         {{ form.password_confirm }}
                         {% if form.password_confirm.errors %}
                             <div class="invalid-feedback d-block">{{ form.password_confirm.errors|first }}</div>
                         {% endif %}
                     </div>
                 </div>
             </div>

             <!-- 역할 선택 섹션 -->
             <div class="card mb-3">
                 <div class="card-header">역할 선택</div>
                 <div class="card-body">
                     <div class="mb-3">
                         {% for choice in form.role %}
                             <div class="form-check">
                                 {{ choice.tag }}
                                 <label class="form-check-label" for="{{ choice.id_for_label }}">
                                     {{ choice.choice_label }}
                                 </label>
                             </div>
                         {% endfor %}
                         {% if form.role.errors %}
                             <div class="invalid-feedback d-block">{{ form.role.errors|first }}</div>
                         {% endif %}
                     </div>
                 </div>
             </div>

             <!-- 광고주 전용 필드 -->
             <div class="card mb-3 conditional-fields" id="advertiser-fields">
                 <div class="card-header">광고주 정보</div>
                 <div class="card-body">
                     <!-- 업체명 -->
                     <div class="mb-3">
                         <label for="id_company_name" class="form-label">업체명 *</label>
                         {{ form.company_name }}
                         {% if form.company_name.errors %}
                             <div class="invalid-feedback d-block">{{ form.company_name.errors|first }}</div>
                         {% endif %}
                     </div>

                     <!-- 사업자등록번호 -->
                     <div class="mb-3">
                         <label for="id_business_registration_number" class="form-label">사업자등록번호 *</label>
                         {{ form.business_registration_number }}
                         <small class="form-text text-muted">예: 123-45-67890</small>
                         {% if form.business_registration_number.errors %}
                             <div class="invalid-feedback d-block">{{ form.business_registration_number.errors|first }}</div>
                         {% endif %}
                     </div>
                 </div>
             </div>

             <!-- 인플루언서 전용 필드 -->
             <div class="card mb-3 conditional-fields" id="influencer-fields">
                 <div class="card-header">인플루언서 정보</div>
                 <div class="card-body">
                     <!-- 생년월일 -->
                     <div class="mb-3">
                         <label for="id_birth_date" class="form-label">생년월일 *</label>
                         {{ form.birth_date }}
                         <small class="form-text text-muted">만 14세 이상만 가입 가능</small>
                         {% if form.birth_date.errors %}
                             <div class="invalid-feedback d-block">{{ form.birth_date.errors|first }}</div>
                         {% endif %}
                     </div>

                     <!-- SNS 링크 -->
                     <div class="mb-3">
                         <label for="id_sns_link" class="form-label">SNS 채널 링크 *</label>
                         {{ form.sns_link }}
                         <small class="form-text text-muted">예: https://blog.naver.com/username</small>
                         {% if form.sns_link.errors %}
                             <div class="invalid-feedback d-block">{{ form.sns_link.errors|first }}</div>
                         {% endif %}
                     </div>
                 </div>
             </div>

             <!-- 약관 동의 -->
             <div class="card mb-3">
                 <div class="card-body">
                     <div class="form-check">
                         {{ form.terms_agreed }}
                         <label class="form-check-label" for="id_terms_agreed">
                             이용약관 및 개인정보처리방침에 동의합니다 (필수)
                         </label>
                         {% if form.terms_agreed.errors %}
                             <div class="invalid-feedback d-block">{{ form.terms_agreed.errors|first }}</div>
                         {% endif %}
                     </div>
                 </div>
             </div>

             <!-- Non-field errors -->
             {% if form.non_field_errors %}
                 <div class="alert alert-danger">
                     {{ form.non_field_errors }}
                 </div>
             {% endif %}

             <!-- 제출 버튼 -->
             <div class="d-grid gap-2">
                 <button type="submit" class="btn btn-primary btn-lg">회원가입</button>
             </div>

             <div class="text-center mt-3">
                 <p>이미 계정이 있으신가요? <a href="{% url 'users:login' %}">로그인</a></p>
             </div>
         </form>
     </div>
     {% endblock %}

     {% block extra_js %}
     <script>
         document.addEventListener('DOMContentLoaded', function() {
             const roleRadios = document.querySelectorAll('input[name="role"]');
             const advertiserFields = document.getElementById('advertiser-fields');
             const influencerFields = document.getElementById('influencer-fields');

             function toggleRoleFields() {
                 const selectedRole = document.querySelector('input[name="role"]:checked');

                 if (selectedRole) {
                     if (selectedRole.value === 'advertiser') {
                         advertiserFields.classList.add('active');
                         influencerFields.classList.remove('active');

                         // 광고주 필드 required 활성화
                         document.getElementById('id_company_name').required = true;
                         document.getElementById('id_business_registration_number').required = true;

                         // 인플루언서 필드 required 비활성화
                         document.getElementById('id_birth_date').required = false;
                         document.getElementById('id_sns_link').required = false;
                     } else if (selectedRole.value === 'influencer') {
                         advertiserFields.classList.remove('active');
                         influencerFields.classList.add('active');

                         // 인플루언서 필드 required 활성화
                         document.getElementById('id_birth_date').required = true;
                         document.getElementById('id_sns_link').required = true;

                         // 광고주 필드 required 비활성화
                         document.getElementById('id_company_name').required = false;
                         document.getElementById('id_business_registration_number').required = false;
                     }
                 }
             }

             roleRadios.forEach(radio => {
                 radio.addEventListener('change', toggleRoleFields);
             });

             // 페이지 로드 시 초기 상태 설정
             toggleRoleFields();
         });
     </script>
     {% endblock %}
     ```
   - 의존성: base.html, Bootstrap 5
   - 테스트: E2E 테스트에서 UI 렌더링 확인

2. **Form 위젯 커스터마이징**
   - 파일: `apps/users/forms.py` (수정)
   - 설명:
     ```python
     class SignupForm(forms.Form):
         name = forms.CharField(
             max_length=100,
             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '홍길동'})
         )
         email = forms.EmailField(
             widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'})
         )
         # ... 나머지 필드들도 동일하게 Bootstrap 클래스 추가
     ```
   - 의존성: Bootstrap 5

**Acceptance Tests**:
- [ ] 회원가입 페이지가 정상적으로 렌더링됨
- [ ] 역할 선택 시 조건부 필드가 동적으로 표시/숨김됨
- [ ] 폼 제출 시 유효성 검증 오류가 인라인으로 표시됨
- [ ] 성공 시 성공 메시지가 Toast로 표시됨

---

### Phase 5: 통합 테스트 및 E2E 테스트

**목표**: 전체 회원가입 플로우가 정상 작동하는지 검증

**작업 항목**:

1. **통합 테스트 작성**
   - 파일: `apps/users/tests/test_integration.py`
   - 설명:
     ```python
     def test_full_signup_flow_influencer(client, db):
         # 1. 회원가입 페이지 접속
         response = client.get('/accounts/signup/')
         assert response.status_code == 200

         # 2. 폼 제출
         form_data = {
             'email': 'influencer@test.com',
             'password': 'Password123',
             'password_confirm': 'Password123',
             'name': '인플루언서',
             'contact': '010-1111-2222',
             'role': 'influencer',
             'birth_date': '1990-01-01',
             'sns_link': 'https://blog.naver.com/test',
             'terms_agreed': True
         }
         response = client.post('/accounts/signup/', form_data, follow=True)

         # 3. 리디렉션 확인
         assert response.status_code == 200
         assert response.redirect_chain[-1][0] == '/'

         # 4. DB 확인
         user = User.objects.get(email='influencer@test.com')
         assert user.role == 'influencer'
         assert hasattr(user, 'influencerprofile')
         assert user.influencerprofile.sns_link == 'https://blog.naver.com/test'

         # 5. 로그인 상태 확인
         assert '_auth_user_id' in client.session

     def test_full_signup_flow_advertiser(client, db):
         form_data = {
             'email': 'advertiser@test.com',
             'password': 'Password123',
             'password_confirm': 'Password123',
             'name': '광고주',
             'contact': '010-3333-4444',
             'role': 'advertiser',
             'company_name': '테스트 회사',
             'business_registration_number': '123-45-67890',
             'terms_agreed': True
         }
         response = client.post('/accounts/signup/', form_data, follow=True)

         assert response.status_code == 200
         assert '/campaigns/manage' in response.redirect_chain[-1][0]

         user = User.objects.get(email='advertiser@test.com')
         assert user.role == 'advertiser'
         assert user.advertiserprofile.company_name == '테스트 회사'
     ```

2. **E2E 테스트 작성 (선택)**
   - 파일: `apps/tests/e2e/test_signup_e2e.py`
   - 설명: Playwright 또는 Selenium을 사용한 E2E 테스트
   - 시나리오:
     1. 회원가입 페이지 접속
     2. 광고주 라디오 버튼 클릭
     3. 광고주 전용 필드 표시 확인
     4. 모든 필드 입력
     5. 회원가입 버튼 클릭
     6. 체험단 관리 페이지로 이동 확인
     7. 성공 메시지 Toast 표시 확인

**Acceptance Tests**:
- [ ] 인플루언서 회원가입 전체 플로우 성공
- [ ] 광고주 회원가입 전체 플로우 성공
- [ ] 각 역할에 맞는 페이지로 리디렉션
- [ ] 자동 로그인 확인
- [ ] E2E 테스트 모든 시나리오 통과

---

## 5. 에러 처리

### 5.1 백엔드 에러

| 에러 코드 | HTTP 상태 | 설명 | 처리 방법 |
|----------|----------|------|----------|
| DUPLICATE_EMAIL | 400 | 이미 가입된 이메일 | Form clean_email()에서 ValidationError 발생 |
| DUPLICATE_CONTACT | 400 | 이미 가입된 연락처 | Form clean_contact()에서 ValidationError 발생 |
| DUPLICATE_BUSINESS_NUMBER | 400 | 이미 등록된 사업자번호 | Form clean_business_registration_number()에서 ValidationError 발생 |
| PASSWORD_MISMATCH | 400 | 비밀번호 불일치 | Form clean()에서 ValidationError 발생 |
| INVALID_BUSINESS_NUMBER_FORMAT | 400 | 잘못된 사업자번호 형식 | RegexValidator 사용 |
| INVALID_URL_FORMAT | 400 | 잘못된 SNS 링크 형식 | URLValidator 사용 |
| UNDER_AGE | 400 | 만 14세 미만 | Form clean()에서 생년월일 검증 |
| TERMS_NOT_AGREED | 400 | 약관 미동의 | Form clean_terms_agreed() 검증 |
| TRANSACTION_FAILED | 500 | DB 트랜잭션 실패 | Service에서 트랜잭션 롤백, 일반 오류 메시지 반환 |

### 5.2 프론트엔드 에러 핸들링

**인라인 오류 표시**:
- 각 필드 하단에 빨간색 오류 메시지 표시
- Bootstrap의 `is-invalid` 클래스 활용

**Toast 메시지**:
- 성공 시: 녹색 Toast "회원가입이 완료되었습니다."
- 시스템 오류 시: 빨간색 Toast "일시적인 오류가 발생했습니다."

**폴백 UI**:
- 네트워크 오류 시 재시도 버튼 표시
- 입력 데이터는 비밀번호 제외하고 유지

---

## 6. 테스트 계획

### 6.1 단위 테스트

**파일**: `apps/users/tests/test_*.py`

**커버리지 목표**: 80% 이상

**테스트 케이스**:

| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-001 | User 생성 성공 | 유효한 데이터 | User 객체 생성 |
| UT-002 | 이메일 중복 | 기존 이메일 | IntegrityError |
| UT-003 | 연락처 중복 | 기존 연락처 | IntegrityError |
| UT-004 | Form 유효성 검증 성공 | 유효한 데이터 | is_valid() == True |
| UT-005 | 비밀번호 불일치 | 다른 비밀번호 | ValidationError |
| UT-006 | 만 14세 미만 | 13세 생년월일 | ValidationError |
| UT-007 | 잘못된 사업자번호 형식 | "12345" | ValidationError |
| UT-008 | SignupService 성공 | 유효한 DTO | User + Profile 생성 |
| UT-009 | SignupService 중복 오류 | 중복 이메일 DTO | DuplicateActionException |
| UT-010 | 트랜잭션 롤백 | Profile 생성 실패 | User도 생성 안됨 |

### 6.2 통합 테스트

**시나리오**:
1. 인플루언서 전체 회원가입 플로우
2. 광고주 전체 회원가입 플로우
3. 중복 이메일로 가입 시도
4. 로그인 상태에서 회원가입 페이지 접근

### 6.3 E2E 테스트 (선택)

**파일**: `apps/tests/e2e/test_signup_e2e.py`

**시나리오**: 위 통합 테스트와 동일하나 실제 브라우저에서 실행

---

## 7. 성능 고려사항

### 7.1 최적화 목표
- 회원가입 처리 시간: 3초 이내
- 중복 확인 쿼리: 각 100ms 이내

### 7.2 데이터베이스 인덱스
- `users.email`: UNIQUE 인덱스 (Django 자동 생성)
- `users.contact`: UNIQUE 인덱스 (Django 자동 생성)
- `advertiser_profiles.business_registration_number`: UNIQUE 인덱스

### 7.3 쿼리 최적화
- 중복 확인 시 `.exists()` 사용 (전체 데이터 로드하지 않음)
- 트랜잭션 사용으로 일관성 보장

---

## 8. 보안 고려사항

### 8.1 인증/인가
- Django Authentication System 활용
- 비밀번호 PBKDF2 해싱
- 세션 기반 인증

### 8.2 데이터 보호
- 비밀번호 평문 저장 금지
- HTTPS 통신 (Railway 자동 제공)
- 환경 변수로 SECRET_KEY 관리

### 8.3 CSRF/XSS 방지
- Django CSRF 미들웨어 활성화
- 템플릿 자동 이스케이핑
- POST 요청에 CSRF 토큰 필수

---

## 9. 배포 계획

### 9.1 환경 변수

```bash
# .env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.railway.app
RAILWAY_VOLUME_MOUNT_PATH=/data
```

### 9.2 배포 순서

1. **로컬 테스트**:
   ```bash
   pytest apps/users/tests/ --cov=apps.users --cov-report=html
   ```
   - 모든 테스트 통과 확인
   - 커버리지 80% 이상 확인

2. **마이그레이션 준비**:
   ```bash
   python manage.py makemigrations users
   python manage.py migrate --check
   ```

3. **Git 커밋 및 푸시**:
   ```bash
   git add .
   git commit -m "Implement signup and onboarding pages"
   git push origin main
   ```

4. **Railway 배포**:
   - GitHub 연동으로 자동 배포
   - 환경 변수 설정 확인
   - Volume 마운트 경로 확인

5. **배포 후 마이그레이션**:
   ```bash
   # Railway Console에서 실행
   python manage.py migrate
   ```

6. **배포 검증**:
   - 회원가입 페이지 접속 확인
   - 테스트 계정 생성 확인
   - 자동 로그인 확인

### 9.3 롤백 계획

**문제 발생 시**:
1. Railway에서 이전 배포 버전으로 롤백
2. 마이그레이션 롤백 (필요 시):
   ```bash
   python manage.py migrate users <previous_migration_number>
   ```

---

## 10. 모니터링 및 로깅

### 10.1 로그 항목
- 회원가입 성공: `INFO - User {email} signed up successfully as {role}`
- 중복 오류: `WARNING - Duplicate signup attempt: {email}`
- 시스템 오류: `ERROR - Signup failed: {error_message}`

### 10.2 메트릭
- 일별 회원가입 수 (광고주/인플루언서 분리)
- 가입 실패율
- 평균 가입 처리 시간

---

## 11. 문서화

### 11.1 코드 문서화
- 모든 Service 클래스에 docstring 작성
- DTO 클래스에 필드 설명 주석 추가

### 11.2 사용자 가이드
- 회원가입 프로세스 스크린샷 포함 가이드 작성 (선택)

---

## 12. 체크리스트

### 12.1 구현 전
- [x] PRD 검토 완료
- [x] 유스케이스 검토 완료
- [x] 데이터베이스 스키마 확정
- [x] 공통 모듈 (BaseDTO, BaseService) 구현 완료
- [x] 보안 요구사항 확인

### 12.2 구현 중
- [ ] TDD 방식으로 개발 진행
- [ ] 각 Phase별 단위 테스트 작성 및 통과
- [ ] 코드 리뷰 완료 (셀프 리뷰)
- [ ] DRY 원칙 준수 확인

### 12.3 구현 후
- [ ] 통합 테스트 통과
- [ ] E2E 테스트 통과 (선택)
- [ ] 코드 커버리지 80% 이상
- [ ] 보안 체크리스트 검증
- [ ] 문서 작성 완료
- [ ] 배포 준비 완료

---

## 13. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude (CTO) | 초기 작성 - PRD, userflow.md, UC-001, UC-004 기반 상세 구현 계획 수립 |

---

## 부록

### A. 참고 코드 예시

**비밀번호 검증 예시**:
```python
# apps/users/forms.py
import re

def clean_password(self):
    password = self.cleaned_data.get('password')

    if len(password) < 8:
        raise ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")

    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        raise ValidationError("비밀번호는 영문자와 숫자를 포함해야 합니다.")

    return password
```

**생년월일 만 14세 검증 예시**:
```python
# apps/users/forms.py
from datetime import date

def clean_birth_date(self):
    birth_date = self.cleaned_data.get('birth_date')

    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    if age < 14:
        raise ValidationError("만 14세 이상만 가입 가능합니다.")

    return birth_date
```

### B. 의사결정 기록

**결정 1**: Form 유효성 검증을 Django Form에서 수행
- 이유: Django Form의 강력한 유효성 검증 기능 활용, Service 계층은 순수 비즈니스 로직만 담당
- 대안: Service 계층에서 모든 검증 수행 → 불필요한 중복 코드 발생

**결정 2**: 역할별 필드를 하나의 Form에 통합
- 이유: 사용자 경험 향상 (페이지 이동 없이 역할 선택), URL 구조 단순화
- 대안: 역할별 별도 Form 및 URL → 코드 중복 증가

**결정 3**: 자동 로그인 구현
- 이유: 사용자 편의성 향상, 타 플랫폼 관행
- 대안: 수동 로그인 요구 → 이탈률 증가 가능성

### C. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| 사업자번호 중복 가입 시도 | 낮음 | 중간 | UNIQUE 제약조건으로 DB 레벨 방어 |
| 트랜잭션 실패로 인한 부분 데이터 생성 | 낮음 | 높음 | `transaction.atomic()` 사용, 롤백 보장 |
| 비밀번호 평문 노출 | 낮음 | 높음 | Django 기본 해싱, 로그에 평문 비밀번호 기록 금지 |
| 중복 제출 (Double Submit) | 중간 | 낮음 | 프론트엔드에서 버튼 비활성화, 서버에서 중복 검증 |
| SQLite 동시 쓰기 제한 | 낮음 | 중간 | MVP 베타테스트 규모에서는 문제 없음, 향후 PostgreSQL 마이그레이션 계획 |

---

## 추가 고려사항

### 기존 공통 모듈 활용

이 구현은 `docs/common-modules.md`에서 정의한 공통 모듈들을 활용합니다:

**Phase 2 이전에 완료되어야 할 공통 모듈**:
- [x] BaseDTO (`apps/common/dto/base.py`)
- [x] BaseService (`apps/common/services/base.py`)
- [x] CustomException 클래스들 (`apps/common/exceptions.py`)
  - DuplicateActionException
  - PermissionDeniedException
- [x] base.html 템플릿
- [x] _navbar.html (로그인 상태 반영)
- [x] _messages.html (Flash messages)

**공통 모듈 의존성 확인**:
- User 모델은 `common-modules.md` Phase 2에서 정의한 구조를 따름
- SignupForm은 `common-modules.md`의 Form 검증 패턴을 따름
- SignupService는 BaseService를 상속하여 execute() 메서드 구현
- 예외 처리는 공통 예외 클래스 활용

이 계획서는 공통 모듈이 먼저 구현된 후 실행 가능합니다.
