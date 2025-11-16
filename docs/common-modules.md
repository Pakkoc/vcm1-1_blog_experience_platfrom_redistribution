# 공통 모듈 작업 계획

## 1. 문서 분석 요약

### 프로젝트 개요
- **제품명**: 체험단 매칭 플랫폼 (광고주-인플루언서 연결)
- **기술 스택**: Django + Django Template + Bootstrap + SQLite + Railway
- **개발 철학**: MVP 신속 개발, 오버엔지니어링 지양, 간결하고 확장 가능한 구조

### 핵심 도메인
1. **Users**: 사용자 인증 및 역할 관리 (광고주/인플루언서)
2. **Campaigns**: 체험단 생성 및 관리
3. **Proposals**: 체험단 지원 및 선정

### 아키텍처 원칙
- Layered Architecture (Presentation → Business Logic → Data Access)
- Use Case 중심 설계
- DTO 기반 명시적 데이터 계약
- Service 계층을 통한 비즈니스 로직 캡슐화
- Selector 패턴을 통한 복잡한 조회 로직 분리

---

## 2. 공통 모듈 목록 및 우선순위

### 2.1 프로젝트 초기 설정 (Priority: Critical)

#### 2.1.1 Django 프로젝트 구조 생성
**목적**: Layered Architecture를 반영한 프로젝트 디렉토리 구조 생성

```
experiencer-platform/
├── manage.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── users/
│   ├── campaigns/
│   └── proposals/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── templates/
    ├── base.html
    ├── _navbar.html
    └── _messages.html
```

**검증 방법**:
- 테스트: 수동 확인 (디렉토리 구조 존재 여부)
- 실행: `python manage.py check`가 에러 없이 통과

#### 2.1.2 Dependencies 설치
**requirements.txt 내용**:
```
Django==5.1.3
python-decouple==3.8
pytest==8.3.3
pytest-django==4.9.0
pytest-cov==5.0.0
factory-boy==3.3.1
```

**검증 방법**:
- 테스트: `pip install -r requirements.txt` 성공
- 실행: `python -c "import django; print(django.VERSION)"` 출력 확인

#### 2.1.3 Settings 분리
**목적**: 개발/프로덕션 환경 설정 분리 및 Railway 배포 준비

**config/settings/base.py**:
- SECRET_KEY는 환경변수로 관리
- SQLite 기본 설정 (Railway Volume 경로 고려)
- INSTALLED_APPS: users, campaigns, proposals 포함
- MIDDLEWARE: 기본 Django 미들웨어
- TEMPLATES: 템플릿 디렉토리 설정
- AUTH_USER_MODEL = 'users.User'

**config/settings/development.py**:
- DEBUG = True
- ALLOWED_HOSTS = ['*']

**config/settings/production.py**:
- DEBUG = False
- ALLOWED_HOSTS from environment variable
- DATABASES 경로를 Railway Volume 경로로 설정

**검증 방법**:
- 테스트: Unit test로 settings import 및 주요 값 검증
- 실행: `DJANGO_SETTINGS_MODULE=config.settings.development python manage.py check`

---

### 2.2 인증 및 권한 시스템 (Priority: Critical)

#### 2.2.1 커스텀 User 모델
**경로**: `apps/users/models.py`

**요구사항** (database.md 기반):
- AbstractBaseUser 상속
- 필드: email (unique), password, name, contact (unique), role (ENUM: advertiser/influencer)
- created_at, updated_at (auto_now_add, auto_now)

**관련 모델**:
- `AdvertiserProfile` (1:1 with User): company_name, business_registration_number
- `InfluencerProfile` (1:1 with User): birth_date, sns_link

**테스트 계획** (TDD):
1. RED: User 생성 테스트 작성 → FAIL
2. GREEN: User 모델 최소 구현
3. REFACTOR: 필드 검증 로직 추가
4. RED: Email uniqueness 테스트 → FAIL
5. GREEN: unique constraint 추가
6. 반복: role validation, password hashing 등

**검증 방법**:
- 단위 테스트: `tests/test_models.py`
  - 사용자 생성 성공
  - Email 중복 시 IntegrityError 발생
  - Role이 advertiser/influencer 외 값일 때 ValidationError
- E2E 테스트: 회원가입 폼 제출 → DB에 User 레코드 생성 확인

#### 2.2.2 인증 폼 (Form Validation)
**경로**: `apps/users/forms.py`

**폼 목록**:
1. `SignUpCommonForm`: email, password, password_confirm, name, contact, terms_agreed
2. `AdvertiserSignUpForm`: company_name, business_registration_number
3. `InfluencerSignUpForm`: birth_date, sns_link

**검증 로직**:
- Email 형식 및 중복 검증
- Password 확인 일치 여부
- 사업자등록번호 형식 (XXX-XX-XXXXX)
- SNS 링크 URL 형식

**테스트 계획**:
1. RED: SignUpCommonForm 유효성 테스트 → FAIL
2. GREEN: Form 클래스 생성 및 clean 메서드 구현
3. RED: Email 중복 시 ValidationError → FAIL
4. GREEN: clean_email 메서드 구현

**검증 방법**:
- 단위 테스트: `tests/test_forms.py`
  - 유효한 데이터 입력 시 is_valid() == True
  - Email 중복 시 form.errors['email'] 존재
  - Password 불일치 시 ValidationError

#### 2.2.3 권한 관리 시스템
**경로**: `apps/users/permissions.py`

**Decorator/Mixin**:
```python
# Decorator
@require_role('advertiser')
def advertiser_only_view(request):
    pass

# Mixin
class AdvertiserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'advertiser'
```

**테스트 계획**:
1. RED: Advertiser가 아닌 사용자 접근 시 403 테스트 → FAIL
2. GREEN: Mixin 구현
3. RED: 비로그인 사용자 접근 시 로그인 페이지 리다이렉트 → FAIL
4. GREEN: LoginRequiredMixin과 조합

**검증 방법**:
- 단위 테스트: `tests/test_permissions.py`
  - Advertiser 사용자는 통과
  - Influencer 사용자는 403
  - 비로그인 사용자는 302 (로그인 페이지)

---

### 2.3 Service Layer 기반 클래스 (Priority: High)

#### 2.3.1 BaseService 추상 클래스
**경로**: `apps/common/services/base.py`

**목적**: 모든 서비스 클래스가 상속할 기본 인터페이스 제공

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputDTO = TypeVar('InputDTO')
OutputType = TypeVar('OutputType')

class BaseService(ABC, Generic[InputDTO, OutputType]):
    @abstractmethod
    def execute(self, dto: InputDTO, user=None) -> OutputType:
        """
        비즈니스 로직 실행

        Args:
            dto: 입력 데이터 전송 객체
            user: 현재 요청 사용자 (선택)

        Returns:
            실행 결과 (모델 인스턴스 또는 DTO)
        """
        pass
```

**테스트 계획**:
- 이 클래스는 추상 클래스이므로 직접 테스트하지 않음
- 하위 클래스 (예: CampaignCreationService)에서 간접 검증

#### 2.3.2 예외 처리 클래스
**경로**: `apps/common/exceptions.py`

**커스텀 예외**:
```python
class ServiceException(Exception):
    """서비스 계층에서 발생하는 비즈니스 로직 예외"""
    pass

class PermissionDeniedException(ServiceException):
    """권한 부족 예외"""
    pass

class InvalidStateException(ServiceException):
    """잘못된 상태 전이 예외 (예: 이미 종료된 캠페인에 지원)"""
    pass

class DuplicateActionException(ServiceException):
    """중복 행동 예외 (예: 이미 지원한 캠페인에 재지원)"""
    pass
```

**테스트 계획**:
1. RED: Service에서 예외 발생 테스트 → FAIL
2. GREEN: 예외 클래스 정의
3. View에서 예외를 catch하여 적절한 HTTP 응답 반환 테스트

**검증 방법**:
- 단위 테스트: 각 Service 메서드에서 예외 발생 시나리오 테스트
- 통합 테스트: View에서 예외 catch 후 400/403 응답 확인

---

### 2.4 DTO (Data Transfer Object) 기반 클래스 (Priority: High)

#### 2.4.1 BaseDTO
**경로**: `apps/common/dto/base.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BaseDTO:
    """
    모든 DTO의 기반 클래스

    - frozen=True로 불변성 보장
    - dataclass 자동 생성 기능 활용
    """
    pass
```

#### 2.4.2 앱별 DTO 예시
**apps/campaigns/dto.py**:
```python
from dataclasses import dataclass
from datetime import date
from apps.common.dto.base import BaseDTO

@dataclass(frozen=True)
class CampaignCreateDTO(BaseDTO):
    name: str
    recruitment_start_date: date
    recruitment_end_date: date
    recruitment_count: int
    benefits: str
    mission: str
```

**apps/proposals/dto.py**:
```python
@dataclass(frozen=True)
class ProposalCreateDTO(BaseDTO):
    campaign_id: int
    cover_letter: str
    desired_visit_date: date
```

**테스트 계획**:
1. RED: DTO 생성 및 불변성 테스트 → FAIL
2. GREEN: DTO 클래스 작성
3. RED: DTO에서 잘못된 타입 전달 시 TypeError → FAIL
4. GREEN: Type hint 명시

**검증 방법**:
- 단위 테스트:
  - DTO 인스턴스 생성 성공
  - DTO 필드 수정 시 FrozenInstanceError 발생
  - 잘못된 타입 전달 시 에러 (mypy로 정적 검사)

---

### 2.5 Selector 패턴 (Priority: Medium)

#### 2.5.1 BaseSelector
**경로**: `apps/common/selectors/base.py`

**목적**: 복잡한 조회 쿼리를 View/Service에서 분리

```python
from typing import List, Optional
from django.db.models import QuerySet

class BaseSelector:
    """
    복잡한 데이터 조회 로직을 캡슐화하는 기본 클래스

    - 읽기 전용 연산만 수행
    - Prefetch/Select related 최적화
    """
    pass
```

#### 2.5.2 앱별 Selector 예시
**apps/campaigns/selectors/campaign_selectors.py**:
```python
from typing import List
from django.db.models import QuerySet, Count
from ..models import Campaign

class CampaignSelector:
    @staticmethod
    def get_recruiting_campaigns() -> QuerySet[Campaign]:
        """모집 중인 체험단 목록 조회 (최신순)"""
        return Campaign.objects.filter(
            status='recruiting'
        ).select_related('advertiser').order_by('-created_at')

    @staticmethod
    def get_campaigns_by_advertiser(advertiser_id: int) -> QuerySet[Campaign]:
        """특정 광고주의 체험단 목록 조회"""
        return Campaign.objects.filter(
            advertiser_id=advertiser_id
        ).annotate(proposal_count=Count('proposals')).order_by('-created_at')
```

**테스트 계획**:
1. RED: get_recruiting_campaigns() 테스트 → FAIL
2. GREEN: Selector 메서드 구현
3. RED: 쿼리 최적화 검증 (N+1 쿼리 방지) → FAIL
4. GREEN: select_related 추가

**검증 방법**:
- 단위 테스트:
  - Selector 메서드가 올바른 QuerySet 반환
  - Filter 조건 정확성
- 성능 테스트:
  - django-debug-toolbar로 쿼리 수 확인
  - N+1 쿼리 없음 검증

---

### 2.6 템플릿 공통 컴포넌트 (Priority: Medium)

#### 2.6.1 Base Template
**경로**: `templates/base.html`

**포함 요소**:
- Bootstrap 5 CDN
- 네비게이션 바 (로그인/비로그인 상태 분기)
- Flash messages 영역
- Footer
- {% block content %} 정의

**구조**:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}체험단 매칭 플랫폼{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% include '_navbar.html' %}

    <main class="container my-4">
        {% include '_messages.html' %}
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### 2.6.2 네비게이션 바
**경로**: `templates/_navbar.html`

**조건부 렌더링**:
- 비로그인: 로그인, 회원가입 링크
- 인플루언서 로그인: 홈, 내 지원 목록, 로그아웃
- 광고주 로그인: 홈, 체험단 관리, 로그아웃

**검증 방법**:
- E2E 테스트:
  - 비로그인 상태에서 네비게이션 바 렌더링 확인
  - 광고주 로그인 후 "체험단 관리" 링크 존재 확인
  - 인플루언서 로그인 후 "체험단 관리" 링크 미존재 확인

#### 2.6.3 Flash Messages
**경로**: `templates/_messages.html`

```html
{% if messages %}
<div class="messages">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

**검증 방법**:
- 통합 테스트:
  - View에서 messages.success 호출 후 템플릿에 메시지 렌더링 확인

---

### 2.7 테스트 환경 설정 (Priority: Critical)

#### 2.7.1 pytest 설정
**경로**: `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
python_classes = Test* *Tests
python_functions = test_*
addopts =
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --reuse-db
```

#### 2.7.2 Conftest (Fixture 공통 정의)
**경로**: `apps/conftest.py`

```python
import pytest
from django.test import Client
from apps.users.models import User

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def advertiser_user(db):
    """광고주 사용자 Fixture"""
    user = User.objects.create_user(
        email='advertiser@test.com',
        password='testpass123',
        name='Test Advertiser',
        contact='010-1234-5678',
        role='advertiser'
    )
    return user

@pytest.fixture
def influencer_user(db):
    """인플루언서 사용자 Fixture"""
    user = User.objects.create_user(
        email='influencer@test.com',
        password='testpass123',
        name='Test Influencer',
        contact='010-9876-5432',
        role='influencer'
    )
    return user
```

#### 2.7.3 Factory Boy 설정
**경로**: `apps/users/factories.py`

```python
import factory
from factory.django import DjangoModelFactory
from .models import User, AdvertiserProfile, InfluencerProfile

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@test.com')
    name = factory.Faker('name')
    contact = factory.Sequence(lambda n: f'010-{n:04d}-5678')
    role = 'influencer'

class AdvertiserFactory(UserFactory):
    role = 'advertiser'

class InfluencerFactory(UserFactory):
    role = 'influencer'
```

**검증 방법**:
- 테스트 실행: `pytest apps/users/tests/`
- Coverage 확인: `pytest --cov=apps --cov-report=html`

---

## 3. 구현 순서 및 의존성 관계

### Phase 1: 기반 인프라 (필수 선행)
1. Django 프로젝트 생성 및 디렉토리 구조 셋업
2. Settings 분리 (base, development, production)
3. pytest 환경 설정
4. requirements.txt 작성 및 의존성 설치

**완료 조건**:
- `python manage.py check` 통과
- `pytest` 실행 가능 (테스트 0개 상태)

---

### Phase 2: 인증 시스템 (Core Domain)
5. 커스텀 User 모델 생성 (TDD)
   - 테스트 작성 → 모델 구현 → Migration
6. AdvertiserProfile, InfluencerProfile 모델 (TDD)
7. 회원가입 폼 (SignUpCommonForm, AdvertiserSignUpForm, InfluencerSignUpForm) (TDD)
8. 권한 관리 Mixin/Decorator (TDD)

**완료 조건**:
- 단위 테스트 커버리지 80% 이상
- Migration 실행 후 DB 스키마 생성 확인
- 회원가입 E2E 테스트 통과

---

### Phase 3: 공통 추상화 계층
9. BaseDTO 정의
10. BaseService 추상 클래스 정의
11. BaseSelector 정의
12. 커스텀 예외 클래스 (ServiceException 계열)

**완료 조건**:
- 각 Base 클래스를 상속한 예시 구현 1개 이상
- 예외 처리 단위 테스트 통과

---

### Phase 4: 템플릿 공통 컴포넌트
13. base.html 템플릿 작성
14. _navbar.html (조건부 렌더링)
15. _messages.html (Flash messages)

**완료 조건**:
- 간단한 View에서 base.html 상속 확인
- 네비게이션 바 역할별 렌더링 E2E 테스트

---

### Phase 5: 도메인별 DTO/Service/Selector (병렬 가능)
16. campaigns 앱: CampaignCreateDTO, CampaignCreationService, CampaignSelector
17. proposals 앱: ProposalCreateDTO, ProposalCreationService, ProposalSelector

**완료 조건**:
- 각 Service 단위 테스트 통과
- Selector N+1 쿼리 없음 검증

---

## 4. 테스트 전략 상세

### 4.1 단위 테스트 (Unit Tests)
**대상**: Models, Forms, Services, Selectors, DTOs

**작성 위치**: `apps/{app_name}/tests/`

**예시 파일 구조**:
```
apps/users/tests/
├── __init__.py
├── test_models.py
├── test_forms.py
├── test_services.py
└── test_permissions.py
```

**테스트 명명 규칙**:
```python
class TestUserModel:
    def test_create_user_with_valid_data_succeeds(self):
        pass

    def test_create_user_with_duplicate_email_raises_integrity_error(self):
        pass
```

### 4.2 통합 테스트 (Integration Tests)
**대상**: View → Service → Model 전체 플로우

**작성 위치**: `apps/{app_name}/tests/test_views.py`

**예시**:
```python
def test_signup_advertiser_creates_user_and_profile(client, db):
    # Arrange
    data = {
        'email': 'new@test.com',
        'password': 'securepass',
        'password_confirm': 'securepass',
        'name': 'New User',
        'contact': '010-1111-2222',
        'role': 'advertiser',
        'company_name': 'Test Company',
        'business_registration_number': '123-45-67890'
    }

    # Act
    response = client.post('/accounts/signup/', data)

    # Assert
    assert response.status_code == 302  # Redirect after success
    assert User.objects.filter(email='new@test.com').exists()
    assert AdvertiserProfile.objects.filter(user__email='new@test.com').exists()
```

### 4.3 E2E 테스트 (Acceptance Tests)
**대상**: 사용자 시나리오 (userflow.md 기반)

**작성 위치**: `apps/tests/e2e/`

**예시 시나리오**:
1. 인플루언서 회원가입 → 로그인 → 체험단 목록 조회 → 체험단 상세 → 지원 → 내 지원 목록 확인
2. 광고주 회원가입 → 로그인 → 체험단 생성 → 지원자 목록 조회 → 모집 마감 → 선정

**도구**: pytest + Django TestClient 또는 Selenium (필요 시)

---

## 5. 코드 충돌 방지 전략

### 5.1 명확한 경계 설정
- **Users 앱**: 인증, 권한, 프로필 관리만 담당
- **Campaigns 앱**: 체험단 CRUD 및 상태 관리만 담당
- **Proposals 앱**: 지원/선정 로직만 담당
- **Common 모듈**: 추상 클래스, DTO, 예외만 정의 (구체적 비즈니스 로직 없음)

### 5.2 네이밍 규칙 통일
- **Service 클래스**: `{UseCase}Service` (예: CampaignCreationService)
- **DTO 클래스**: `{Entity}{Action}DTO` (예: CampaignCreateDTO)
- **Selector 클래스**: `{Entity}Selector` (예: CampaignSelector)
- **Form 클래스**: `{Entity}{Action}Form` (예: CampaignCreateForm)

### 5.3 URL 네임스페이스 사전 정의
```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('apps.users.urls', 'users'), namespace='users')),
    path('campaigns/', include(('apps.campaigns.urls', 'campaigns'), namespace='campaigns')),
    path('my/', include(('apps.proposals.urls', 'proposals'), namespace='proposals')),
]
```

### 5.4 Database Migration 순서
1. Users 앱 Migration 먼저 실행 (AUTH_USER_MODEL 참조 필요)
2. Campaigns, Proposals Migration 동시 실행 가능 (서로 참조 없음)

---

## 6. 구현 완료 체크리스트

### Phase 1: 기반 인프라
- [ ] Django 프로젝트 생성 완료
- [ ] 디렉토리 구조 (config, apps, static, templates) 생성
- [ ] requirements.txt 작성 및 설치
- [ ] pytest.ini 설정
- [ ] settings 분리 (base, development, production)
- [ ] `python manage.py check` 통과
- [ ] `pytest` 실행 가능 (빈 테스트 스위트)

### Phase 2: 인증 시스템
- [ ] User 모델 테스트 작성 (RED)
- [ ] User 모델 구현 (GREEN)
- [ ] Migration 생성 및 실행
- [ ] AdvertiserProfile, InfluencerProfile 모델 및 테스트
- [ ] SignUpCommonForm 테스트 및 구현
- [ ] Advertiser/InfluencerSignUpForm 테스트 및 구현
- [ ] AdvertiserRequiredMixin, InfluencerRequiredMixin 구현
- [ ] 권한 관리 단위 테스트 통과
- [ ] 회원가입 E2E 테스트 통과

### Phase 3: 공통 추상화 계층
- [ ] BaseDTO 정의
- [ ] BaseService 정의
- [ ] BaseSelector 정의
- [ ] ServiceException, PermissionDeniedException 등 예외 클래스 정의
- [ ] 예외 처리 단위 테스트 작성 및 통과

### Phase 4: 템플릿 공통 컴포넌트
- [ ] base.html 작성 (Bootstrap CDN 포함)
- [ ] _navbar.html 작성 (역할별 조건부 렌더링)
- [ ] _messages.html 작성
- [ ] 네비게이션 바 E2E 테스트 통과

### Phase 5: 도메인별 구체화
- [ ] CampaignCreateDTO 정의
- [ ] CampaignCreationService 테스트 및 구현
- [ ] CampaignSelector 테스트 및 구현
- [ ] ProposalCreateDTO 정의
- [ ] ProposalCreationService 테스트 및 구현
- [ ] ProposalSelector 테스트 및 구현

### Phase 6: 테스트 커버리지 검증
- [ ] 전체 단위 테스트 커버리지 80% 이상
- [ ] 모든 Service 메서드 테스트 작성
- [ ] N+1 쿼리 검증 (Selector)
- [ ] E2E 테스트 주요 시나리오 커버

---

## 7. 위험 요소 및 대응 방안

### 7.1 SQLite Concurrent Write Issue
**문제**: Railway 배포 시 여러 요청이 동시에 Write할 경우 Database Locked 에러 발생 가능

**대응**:
- 내부 베타테스트 단계에서는 동시 접속자 수가 적어 문제 없음
- Volume 설정으로 데이터 유실 방지 (techstack.md 참고)
- 향후 PostgreSQL 마이그레이션 계획 수립 (MVP 이후)

### 7.2 Template 중복 코드
**문제**: 각 앱에서 base.html을 상속하지만 개별 컴포넌트 중복 가능

**대응**:
- 재사용 가능한 컴포넌트는 templates/ 최상위에 배치
- 앱 고유 템플릿만 apps/{app}/templates/{app}/ 에 배치

### 7.3 DTO 변경 시 영향 범위
**문제**: DTO 필드 추가/변경 시 Service, Form, View 모두 수정 필요

**대응**:
- DTO 변경 시 관련 테스트가 실패하도록 강제 (TDD)
- mypy 등 정적 타입 체커 활용 (선택)

---

## 8. 다음 단계 (페이지 단위 개발 시작 전)

1. 이 문서를 팀원들과 리뷰
2. Phase 1~4까지 완료 (약 1주일 예상)
3. Phase 5는 페이지 개발과 병렬 진행 가능
4. 각 Phase 완료 시 체크리스트 업데이트 및 커밋
5. 공통 모듈 완료 후 페이지별 개발 브랜치 분리 가능

---

## 9. 참고 문서

- `docs/requirement.md`: 타겟 유저 및 페이지 목록
- `docs/persona.md`: CTO 역할 및 개발 철학
- `docs/techstack.md`: 기술 스택 선정 이유 및 Railway 설정
- `docs/structure.md`: Layered Architecture 설계
- `docs/prd.md`: 제품 요구사항 및 사용자 여정
- `docs/userflow.md`: 기능별 입력-처리-출력 흐름
- `docs/database.md`: 데이터베이스 스키마 및 마이그레이션 SQL
- `docs/rules/tdd.md`: TDD 프로세스 가이드라인

---

## 10. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-11-16 | 1.0.0 | 최초 작성 | Claude (CTO) |
