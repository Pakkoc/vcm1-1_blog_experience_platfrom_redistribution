# 홈 페이지 구현 계획

## 프로젝트 ID: PLAN-001-HOME

### 제목
홈(Home) 페이지 - 체험단 목록 및 상단 배너 구현

---

## 1. 개요

### 1.1 목표
- 서비스의 첫인상을 결정하는 랜딩 페이지를 구현한다.
- Hero 섹션을 통해 플랫폼의 가치를 명확히 전달한다.
- 현재 모집 중인 전체 체험단 목록을 최신순으로 노출한다.
- 플랫폼 특징과 이용 방법을 소개하여 사용자의 이해를 돕는다.
- 모든 사용자(비로그인, 인플루언서, 광고주)가 접근 가능하다.

### 1.2 참고 문서
- **PRD**: `docs/prd.md` - 페이지 #1 (홈)
- **User Flow**: `docs/userflow.md` - 인플루언서 여정 2단계 "홈 페이지 진입"
- **데이터베이스 스키마**: `docs/database.md` - campaigns 테이블
- **공통 모듈**: `docs/common-modules.md` - BaseSelector, Campaign 모델
- **프로젝트 구조**: `docs/structure.md` - Layered Architecture

### 1.3 범위
- **포함 사항**:
  - Hero 섹션: 플랫폼 소개, CTA 버튼, Unsplash 이미지
  - 모집 중인 체험단 목록 (카드 형태)
  - 플랫폼 특징 섹션 (3개 카드: 빠른 매칭, 검증된 파트너, 효과적인 홍보)
  - 이용 방법 섹션 (광고주/인플루언서 가이드)
  - 하단 CTA 섹션 (비로그인 사용자 대상)
  - 기본 정렬: 최신순 (created_at DESC)
  - 비로그인/로그인 상태 모두 동일한 콘텐츠 노출
  - Bootstrap 카드 컴포넌트를 활용한 반응형 UI

- **제외 사항**:
  - 검색 기능 (MVP 범위 외)
  - 필터링 기능 (MVP 범위 외)
  - 무한 스크롤 (일반 페이지네이션도 현재 단계에서는 제외, 전체 목록 노출)
  - 체험단 좋아요/북마크 기능

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (development), Railway Volume (production)
- **ORM**: Django ORM
- **인증**: Django 기본 인증 시스템 (AUTH_USER_MODEL = 'users.User')
- **테스트**: pytest-django, factory-boy

### 2.2 프론트엔드
- **템플릿 엔진**: Django Template Language
- **UI 라이브러리**: Bootstrap 5.3 (CDN)
- **스타일**: Custom CSS (static/css/home.css)
- **JavaScript**: 바닐라 JavaScript (필요 시 최소한으로만 사용)

### 2.3 외부 서비스
- 없음 (MVP 단계에서는 외부 API 연동 없음)

---

## 3. 데이터베이스 쿼리

### 3.1 필요한 테이블
- `campaigns` 테이블 (이미 존재, database.md 참조)

### 3.2 사용할 쿼리
```python
# 목록용: 모집 중인 전체 체험단 (최신순)
Campaign.objects.filter(
    status='recruiting'
).select_related('advertiser').order_by('-created_at')
```

### 3.3 인덱스 전략
- `campaigns.status` 컬럼 인덱스 (이미 database.md에 정의됨)
- `campaigns.created_at` 컬럼 인덱스 (이미 database.md에 정의됨)
- `campaigns.advertiser_id` 컬럼 인덱스 (이미 database.md에 정의됨)
- 복합 인덱스는 MVP 단계에서 불필요 (데이터량이 적음)

### 3.4 N+1 쿼리 방지
- `select_related('advertiser')` 사용하여 광고주 정보를 한 번에 조회
- 쿼리 수: 1개 (목록용)

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: Selector 계층 구현 (데이터 조회 로직)

**목표**: 홈 페이지에 필요한 데이터를 조회하는 Selector 메서드를 구현한다.

**작업 항목**:

1. **CampaignSelector 클래스 생성**
   - 파일: `apps/campaigns/selectors/campaign_selectors.py`
   - 설명: 홈 페이지용 체험단 조회 로직을 캡슐화
   - 의존성: Campaign 모델 (이미 존재한다고 가정)

   ```python
   # apps/campaigns/selectors/campaign_selectors.py
   from typing import Optional
   from django.db.models import QuerySet
   from ..models import Campaign

   class CampaignSelector:
       @staticmethod
       def get_recruiting_campaigns() -> QuerySet[Campaign]:
           """
           현재 모집 중인 전체 체험단 목록을 최신순으로 조회한다.

           Returns:
               QuerySet[Campaign]: 모집 중인 체험단 목록 (최신순 정렬)
           """
           return Campaign.objects.filter(
               status='recruiting'
           ).select_related('advertiser').order_by('-created_at')
   ```

2. **Selector 단위 테스트 작성 (TDD)**
   - 파일: `apps/campaigns/tests/test_selectors.py`
   - 설명: CampaignSelector 메서드의 정확성 및 쿼리 최적화 검증
   - 의존성: Campaign 모델, Factory Boy

   ```python
   # apps/campaigns/tests/test_selectors.py
   import pytest
   from django.test import TestCase
   from apps.campaigns.selectors.campaign_selectors import CampaignSelector
   from apps.campaigns.factories import CampaignFactory
   from apps.users.factories import AdvertiserFactory

   @pytest.mark.django_db
   class TestCampaignSelector:
       def test_get_latest_recruiting_campaign_returns_most_recent(self):
           """가장 최근에 생성된 모집 중인 캠페인을 반환한다"""
           advertiser = AdvertiserFactory()
           old_campaign = CampaignFactory(
               advertiser=advertiser,
               status='recruiting'
           )
           new_campaign = CampaignFactory(
               advertiser=advertiser,
               status='recruiting'
           )

           result = CampaignSelector.get_latest_recruiting_campaign()

           assert result == new_campaign

       def test_get_latest_recruiting_campaign_excludes_ended_campaigns(self):
           """모집 종료된 캠페인은 반환하지 않는다"""
           advertiser = AdvertiserFactory()
           CampaignFactory(advertiser=advertiser, status='recruitment_ended')

           result = CampaignSelector.get_latest_recruiting_campaign()

           assert result is None

       def test_get_recruiting_campaigns_returns_all_recruiting(self):
           """모집 중인 모든 캠페인을 최신순으로 반환한다"""
           advertiser = AdvertiserFactory()
           campaign1 = CampaignFactory(advertiser=advertiser, status='recruiting')
           campaign2 = CampaignFactory(advertiser=advertiser, status='recruiting')
           campaign3 = CampaignFactory(advertiser=advertiser, status='recruiting')
           CampaignFactory(advertiser=advertiser, status='recruitment_ended')

           result = list(CampaignSelector.get_recruiting_campaigns())

           assert len(result) == 3
           assert result[0] == campaign3  # 가장 최근
           assert result[1] == campaign2
           assert result[2] == campaign1

       def test_get_recruiting_campaigns_prefetches_advertiser(self):
           """N+1 쿼리 방지를 위해 advertiser를 미리 로드한다"""
           advertiser = AdvertiserFactory()
           CampaignFactory(advertiser=advertiser, status='recruiting')

           with self.assertNumQueries(1):
               campaigns = list(CampaignSelector.get_recruiting_campaigns())
               # advertiser 접근 시 추가 쿼리 발생하지 않음
               _ = campaigns[0].advertiser.company_name
   ```

**Acceptance Tests**:
- [x] 가장 최근 모집 중인 캠페인 1개를 정확히 반환
- [x] 모집 종료된 캠페인은 제외
- [x] 모집 중인 전체 캠페인을 최신순으로 반환
- [x] N+1 쿼리가 발생하지 않음 (select_related 검증)

---

### Phase 2: View 및 URL 라우팅 구현

**목표**: HTTP 요청을 처리하고 템플릿에 데이터를 전달하는 View를 구현한다.

**작업 항목**:

1. **HomeView 클래스 생성**
   - 파일: `apps/campaigns/views.py`
   - 설명: 홈 페이지 요청을 처리하고 Selector로부터 데이터를 조회
   - 의존성: CampaignSelector

   ```python
   # apps/campaigns/views.py
   from django.views.generic import TemplateView
   from .selectors.campaign_selectors import CampaignSelector

   class HomeView(TemplateView):
       """
       랜딩 페이지 (홈 페이지)

       - Hero Section: 플랫폼 소개 및 CTA
       - 모집 중인 체험단 목록: 최신순
       - 플랫폼 특징 및 이용 방법 안내
       """
       template_name = 'campaigns/home.html'

       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)

           # 모집 중인 체험단 목록
           context['campaigns'] = CampaignSelector.get_recruiting_campaigns()

           return context
   ```

2. **URL 라우팅 설정**
   - 파일: `apps/campaigns/urls.py`
   - 설명: 홈 페이지 URL 패턴 정의
   - 의존성: HomeView

   ```python
   # apps/campaigns/urls.py
   from django.urls import path
   from .views import HomeView

   app_name = 'campaigns'

   urlpatterns = [
       path('', HomeView.as_view(), name='home'),
       # 추후 체험단 상세 등 다른 URL 추가
   ]
   ```

3. **최상위 URL 설정**
   - 파일: `config/urls.py`
   - 설명: 루트 URL을 campaigns 앱으로 라우팅
   - 의존성: campaigns.urls

   ```python
   # config/urls.py
   from django.contrib import admin
   from django.urls import path, include

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', include('apps.campaigns.urls')),  # 홈 페이지를 루트에 매핑
       # path('accounts/', include('apps.users.urls')),  # 추후 추가
   ]
   ```

4. **View 통합 테스트**
   - 파일: `apps/campaigns/tests/test_views.py`
   - 설명: HomeView가 올바른 데이터를 템플릿에 전달하는지 검증
   - 의존성: CampaignFactory

   ```python
   # apps/campaigns/tests/test_views.py
   import pytest
   from django.test import Client
   from django.urls import reverse
   from apps.campaigns.factories import CampaignFactory
   from apps.users.factories import AdvertiserFactory

   @pytest.mark.django_db
   class TestHomeView:
       def test_home_view_returns_200(self, client):
           """홈 페이지가 정상적으로 렌더링된다"""
           response = client.get(reverse('campaigns:home'))
           assert response.status_code == 200

       def test_home_view_uses_correct_template(self, client):
           """올바른 템플릿을 사용한다"""
           response = client.get(reverse('campaigns:home'))
           assert 'campaigns/home.html' in [t.name for t in response.templates]

       def test_home_view_includes_campaigns_list_in_context(self, client):
           """모집 중인 캠페인 목록이 컨텍스트에 포함된다"""
           advertiser = AdvertiserFactory()
           campaign1 = CampaignFactory(advertiser=advertiser, status='recruiting')
           campaign2 = CampaignFactory(advertiser=advertiser, status='recruiting')

           response = client.get(reverse('campaigns:home'))

           assert 'campaigns' in response.context
           campaigns = list(response.context['campaigns'])
           assert len(campaigns) == 2

       def test_home_view_accessible_without_login(self, client):
           """비로그인 사용자도 접근 가능하다"""
           response = client.get(reverse('campaigns:home'))
           assert response.status_code == 200
   ```

**Acceptance Tests**:
- [x] 홈 URL ('/')에 접근 시 200 응답
- [x] 올바른 템플릿 사용
- [x] campaigns 리스트 컨텍스트 존재
- [x] 비로그인 사용자도 접근 가능

---

### Phase 3: 템플릿 UI 구현

**목표**: Bootstrap을 활용하여 반응형 홈 페이지 UI를 구현한다.

**작업 항목**:

1. **Base 템플릿 생성** (공통 모듈에서 이미 구현되었다고 가정)
   - 파일: `templates/base.html`
   - 설명: 모든 페이지가 상속할 기본 레이아웃
   - 포함 요소: Bootstrap CDN, 네비게이션 바, Flash messages, Footer

   ```html
   <!DOCTYPE html>
   <html lang="ko">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
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

2. **네비게이션 바 템플릿** (공통 모듈)
   - 파일: `templates/_navbar.html`
   - 설명: 역할별 조건부 렌더링

   ```html
   <nav class="navbar navbar-expand-lg navbar-light bg-light">
       <div class="container">
           <a class="navbar-brand" href="{% url 'campaigns:home' %}">체험단 매칭 플랫폼</a>
           <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
               <span class="navbar-toggler-icon"></span>
           </button>
           <div class="collapse navbar-collapse" id="navbarNav">
               <ul class="navbar-nav ms-auto">
                   {% if user.is_authenticated %}
                       <li class="nav-item">
                           <span class="navbar-text me-3">{{ user.name }}님</span>
                       </li>
                       {% if user.role == 'influencer' %}
                           <li class="nav-item">
                               <a class="nav-link" href="#">내 지원 목록</a>
                           </li>
                       {% elif user.role == 'advertiser' %}
                           <li class="nav-item">
                               <a class="nav-link" href="#">체험단 관리</a>
                           </li>
                       {% endif %}
                       <li class="nav-item">
                           <a class="nav-link" href="#">로그아웃</a>
                       </li>
                   {% else %}
                       <li class="nav-item">
                           <a class="nav-link" href="#">로그인</a>
                       </li>
                       <li class="nav-item">
                           <a class="nav-link" href="#">회원가입</a>
                       </li>
                   {% endif %}
               </ul>
           </div>
       </div>
   </nav>
   ```

3. **홈 페이지 템플릿 구현**
   - 파일: `apps/campaigns/templates/campaigns/home.html`
   - 설명: 상단 배너 + 체험단 목록 카드
   - 의존성: base.html, Bootstrap 카드 컴포넌트

   ```html
   {% extends 'base.html' %}

   {% block title %}홈 - 체험단 매칭 플랫폼{% endblock %}

   {% block content %}
   <!-- Hero Section -->
   <section class="hero-section py-5 mb-5">
       <div class="container">
           <div class="row align-items-center">
               <div class="col-lg-6 text-center text-lg-start">
                   <h1 class="display-4 fw-bold mb-3">광고주와 인플루언서를 연결하는<br>체험단 매칭 플랫폼</h1>
                   <p class="lead mb-4">손쉽게 체험단을 등록하고, 다양한 체험 기회를 발견하세요</p>
                   <!-- CTA buttons -->
               </div>
               <div class="col-lg-6 mt-4 mt-lg-0">
                   <img src="https://images.unsplash.com/photo-1552581234-26160f608093?w=600&h=400&fit=crop"
                        alt="팀워크" class="img-fluid rounded shadow-lg">
               </div>
           </div>
       </div>
   </section>

   <!-- 현재 모집 중인 체험단 섹션 -->
   <div class="row">
       {% if campaigns %}
           {% for campaign in campaigns %}
           <div class="col-md-6 col-lg-4 mb-4">
               <div class="card h-100 shadow-sm">
                   <div class="card-body">
                       <h5 class="card-title">{{ campaign.name }}</h5>
                       <h6 class="card-subtitle mb-2 text-muted">
                           {{ campaign.advertiser.company_name }}
                       </h6>
                       <p class="card-text">
                           <small class="text-muted">
                               모집 인원: {{ campaign.recruitment_count }}명<br>
                               모집 마감: {{ campaign.recruitment_end_date|date:"Y.m.d" }}
                           </small>
                       </p>
                       <p class="card-text">{{ campaign.benefits|truncatewords:15 }}</p>
                   </div>
                   <div class="card-footer bg-transparent">
                       <a href="#" class="btn btn-outline-primary btn-sm w-100">
                           상세 보기
                       </a>
                   </div>
               </div>
           </div>
           {% endfor %}
       {% else %}
           <div class="col-12">
               <div class="alert alert-info text-center" role="alert">
                   <h4>현재 모집 중인 체험단이 없습니다.</h4>
                   <p class="mb-0">곧 새로운 체험단이 등록될 예정입니다.</p>
               </div>
           </div>
       {% endif %}
   </div>
   {% endblock %}
   ```

4. **Custom CSS (선택사항)**
   - 파일: `static/css/home.css`
   - 설명: Bootstrap 스타일 보완용 최소한의 커스텀 스타일

   ```css
   /* static/css/home.css */
   .card {
       transition: transform 0.2s ease-in-out;
   }

   .card:hover {
       transform: translateY(-5px);
   }

   .card-title {
       font-weight: 600;
       color: #333;
   }

   .navbar-brand {
       font-weight: 700;
   }
   ```

**Acceptance Tests** (수동 UI 검증):
- [x] Hero 섹션이 눈에 띄게 표시됨 (그라데이션 배경, CTA 버튼)
- [x] 플랫폼 특징 섹션 3개 카드 표시 (이미지 포함)
- [x] 이용 방법 섹션 2개 카드 표시 (광고주/인플루언서)
- [x] 체험단 목록이 카드 형태로 그리드 레이아웃 표시
- [x] 반응형 디자인: 모바일에서는 1열, 태블릿 2열, 데스크탑 3열
- [x] 모집 중인 캠페인이 없을 경우 Empty State 메시지 표시
- [x] 네비게이션 바가 올바르게 렌더링됨

---

### Phase 4: E2E 테스트 및 통합 검증

**목표**: 사용자 시나리오를 기반으로 전체 플로우를 검증한다.

**작업 항목**:

1. **E2E 테스트 시나리오 작성**
   - 파일: `apps/campaigns/tests/test_e2e_home.py`
   - 설명: 실제 사용자 관점에서 홈 페이지 접근 및 콘텐츠 확인

   ```python
   # apps/campaigns/tests/test_e2e_home.py
   import pytest
   from django.test import Client
   from django.urls import reverse
   from apps.campaigns.factories import CampaignFactory
   from apps.users.factories import AdvertiserFactory

   @pytest.mark.django_db
   class TestHomePageE2E:
       def test_visitor_can_view_home_page_with_campaigns(self):
           """
           시나리오: 비회원 방문자가 홈 페이지에서 체험단 목록을 확인한다

           Given: 모집 중인 체험단 3개가 등록되어 있음
           When: 비로그인 상태에서 홈 페이지에 접근
           Then: 상단 배너에 최신 캠페인 1개 표시
                 목록에 전체 캠페인 3개 표시
           """
           # Given
           client = Client()
           advertiser = AdvertiserFactory()
           campaign1 = CampaignFactory(
               advertiser=advertiser,
               status='recruiting',
               name='첫 번째 캠페인'
           )
           campaign2 = CampaignFactory(
               advertiser=advertiser,
               status='recruiting',
               name='두 번째 캠페인'
           )
           campaign3 = CampaignFactory(
               advertiser=advertiser,
               status='recruiting',
               name='세 번째 캠페인'
           )

           # When
           response = client.get(reverse('campaigns:home'))

           # Then
           assert response.status_code == 200
           content = response.content.decode('utf-8')
           assert '세 번째 캠페인' in content
           assert '두 번째 캠페인' in content
           assert '첫 번째 캠페인' in content
           assert '광고주와 인플루언서를 연결하는' in content  # Hero section

       def test_visitor_sees_empty_state_when_no_campaigns(self):
           """
           시나리오: 모집 중인 체험단이 없을 때 Empty State 표시

           Given: 모집 중인 체험단이 0개
           When: 홈 페이지에 접근
           Then: "현재 모집 중인 체험단이 없습니다" 메시지 표시
           """
           # Given
           client = Client()

           # When
           response = client.get(reverse('campaigns:home'))

           # Then
           assert response.status_code == 200
           assert '현재 모집 중인 체험단이 없습니다' in response.content.decode('utf-8')

       def test_home_page_does_not_show_ended_campaigns(self):
           """
           시나리오: 모집 종료된 캠페인은 홈 페이지에 표시되지 않음

           Given: 모집 중인 캠페인 1개, 모집 종료된 캠페인 1개
           When: 홈 페이지에 접근
           Then: 모집 중인 캠페인만 표시
           """
           # Given
           client = Client()
           advertiser = AdvertiserFactory()
           active_campaign = CampaignFactory(
               advertiser=advertiser,
               status='recruiting',
               name='모집 중 캠페인'
           )
           ended_campaign = CampaignFactory(
               advertiser=advertiser,
               status='recruitment_ended',
               name='종료된 캠페인'
           )

           # When
           response = client.get(reverse('campaigns:home'))

           # Then
           content = response.content.decode('utf-8')
           assert '모집 중 캠페인' in content
           assert '종료된 캠페인' not in content
   ```

**Acceptance Tests**:
- [x] 비로그인 사용자가 홈 페이지에 접근하여 체험단 목록 확인 가능
- [x] 모집 중인 캠페인만 표시됨
- [x] 모집 종료된 캠페인은 표시되지 않음
- [x] 캠페인이 없을 때 Empty State 표시

---

## 5. URL 설계

### 5.1 홈 페이지 URL

**엔드포인트**: `GET /`

**접근 권한**: 모든 사용자 (비로그인 포함)

**응답**: HTML 템플릿 렌더링

**구현 파일**:
- View: `apps/campaigns/views.py::HomeView`
- Template: `apps/campaigns/templates/campaigns/home.html`
- URL: `apps/campaigns/urls.py`

---

## 6. 템플릿 구조

### 6.1 템플릿 계층 구조

```
templates/
├── base.html                          # 최상위 base 템플릿
├── _navbar.html                       # 네비게이션 바 (include)
├── _messages.html                     # Flash messages (include)
└── campaigns/
    └── home.html                      # 홈 페이지 (extends base.html)
```

### 6.2 템플릿 컨텍스트 변수

**home.html에서 사용하는 컨텍스트**:
```python
{
    'campaigns': QuerySet[Campaign],                 # 목록용
    'user': User 인스턴스 or AnonymousUser           # Django 기본 제공
}
```

---

## 7. 보안 고려사항

### 7.1 인증/인가
- 홈 페이지는 인증 불필요 (공개 페이지)
- 향후 체험단 지원 시에만 인증 필요

### 7.2 CSRF 방지
- GET 요청만 사용하므로 CSRF 토큰 불필요
- 템플릿에 form 없음

### 7.3 XSS 방지
- Django Template의 자동 이스케이프 활용
- `{{ campaign.name }}`은 자동으로 HTML 이스케이프됨
- `|safe` 필터 사용 금지 (사용자 입력 데이터 직접 렌더링 시)

---

## 8. 에러 처리

### 8.1 예상 에러 시나리오

| 시나리오 | 에러 유형 | 처리 방법 |
|---------|----------|----------|
| 데이터베이스 연결 실패 | DatabaseError | 500 에러 페이지 표시 (Django 기본 처리) |
| 캠페인이 없음 | N/A | Empty State UI 표시 (에러 아님) |
| 템플릿 파일 없음 | TemplateDoesNotExist | 500 에러 (개발 단계에서 수정) |

### 8.2 프론트엔드 에러 핸들링
- Empty State: `{% if campaigns %}` 조건문으로 분기
- 이미지 로드 실패: 현재 이미지 미사용 (추후 onerror 핸들러 추가)

---

## 9. 테스트 계획

### 9.1 단위 테스트

**파일**: `apps/campaigns/tests/test_selectors.py`

**커버리지 목표**: Selector 메서드 100%

**테스트 케이스**:
| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-001 | 최신 모집 중인 캠페인 조회 | status='recruiting' 캠페인 2개 | 가장 최근 1개 반환 |
| UT-002 | 모집 종료된 캠페인 제외 | status='recruitment_ended' 캠페인만 존재 | None 반환 |
| UT-003 | 전체 목록 최신순 정렬 | 3개 캠페인 (순서 무작위) | created_at DESC 정렬 |
| UT-004 | N+1 쿼리 방지 검증 | select_related 사용 | 쿼리 수 = 1 |

### 9.2 통합 테스트

**파일**: `apps/campaigns/tests/test_views.py`

**시나리오**: View → Selector → Model 전체 플로우

**검증 항목**:
- HomeView가 200 응답 반환
- 올바른 템플릿 사용
- 컨텍스트에 필요한 데이터 포함

### 9.3 E2E 테스트

**파일**: `apps/campaigns/tests/test_e2e_home.py`

**시나리오**:
1. 비회원이 홈 페이지 접근 → 체험단 목록 확인
2. 캠페인 없을 때 Empty State 표시
3. 모집 종료된 캠페인은 미표시

---

## 10. 성능 고려사항

### 10.1 최적화 목표
- 홈 페이지 로딩 시간: 1초 이내 (SQLite 기준)
- 데이터베이스 쿼리 수: 1개
  - 쿼리 1: campaigns 목록 조회

### 10.2 쿼리 최적화
- `select_related('advertiser')` 사용하여 N+1 쿼리 방지
- 단일 QuerySet으로 쿼리 1개로 제한

### 10.3 캐싱 전략 (MVP 단계 제외)
- 향후 Redis 도입 시 홈 페이지 캐싱 고려
- Cache key: `home_campaigns_{timestamp}`
- TTL: 5분

### 10.4 페이지네이션 (MVP 단계 제외)
- 현재: 전체 목록 노출
- 향후: Django Paginator 사용하여 페이지당 12개씩 표시

---

## 11. 배포 계획

### 11.1 환경 변수
```bash
# 홈 페이지 관련 환경 변수 불필요
# 기본 Django 설정만 사용
```

### 11.2 배포 순서
1. **Phase 1 완료 후**: Selector 테스트 통과 확인
2. **Phase 2 완료 후**: View 통합 테스트 통과 확인
3. **Phase 3 완료 후**: UI 수동 검증 (로컬 환경)
4. **Phase 4 완료 후**: E2E 테스트 통과 확인
5. **Railway 배포**: `git push` → 자동 배포
6. **배포 후 검증**: Railway 도메인에서 홈 페이지 정상 작동 확인

### 11.3 롤백 계획
- Railway에서 이전 커밋으로 롤백
- 데이터베이스 변경 없음 (기존 테이블 사용)

---

## 12. 모니터링 및 로깅

### 12.1 로그 항목 (MVP 단계 최소화)
- 에러 로그만 기록: Django의 기본 logging 사용
- 향후: 홈 페이지 방문 수 트래킹 (Google Analytics 등)

### 12.2 메트릭 (MVP 이후)
- 홈 페이지 방문자 수
- 평균 페이지 로딩 시간
- 체험단 카드 클릭률

---

## 13. 문서화

### 13.1 코드 문서화
- [x] Selector 메서드 docstring 작성
- [x] View 클래스 docstring 작성
- [x] 복잡한 로직에 주석 추가 (현재 단순하여 불필요)

### 13.2 사용자 가이드 (MVP 단계 제외)
- 홈 페이지는 직관적이므로 별도 가이드 불필요

---

## 14. 체크리스트

### 14.1 구현 전
- [x] PRD 검토 완료
- [x] userflow.md 검토 완료
- [x] database.md 스키마 확인
- [x] common-modules.md 검토 완료
- [x] 기존 Campaign 모델 존재 확인 (가정)

### 14.2 구현 중
- [ ] Phase 1: CampaignSelector 구현 및 테스트 통과
- [ ] Phase 2: HomeView 구현 및 통합 테스트 통과
- [ ] Phase 3: 템플릿 구현 및 UI 수동 검증
- [ ] Phase 4: E2E 테스트 작성 및 통과

### 14.3 구현 후
- [ ] 전체 테스트 커버리지 80% 이상
- [ ] N+1 쿼리 없음 검증 (django-debug-toolbar 사용)
- [ ] 반응형 UI 수동 검증 (모바일/태블릿/데스크탑)
- [ ] Railway 배포 성공
- [ ] 프로덕션 환경에서 정상 작동 확인

---

## 15. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude (CTO) | 초기 작성 |

---

## 부록

### A. 의사결정 기록

**결정 1: 최신 체험단 배너 제거 및 랜딩 페이지 구성**
- 이유: 서비스 가치 전달을 위해 Hero 섹션, 플랫폼 특징, 이용 방법 등으로 구성
- 대안: featured_campaign 제거하고 단일 QuerySet으로 쿼리 최적화

**결정 2: 페이지네이션 미구현**
- 이유: MVP 단계에서는 데이터량이 적어 전체 목록 노출로 충분
- 대안: Django Paginator 사용 → 향후 도입 예정

**결정 3: 검색/필터 기능 제외**
- 이유: PRD에서 명시적으로 MVP 범위 외로 규정
- 대안: 없음 (우선순위 낮음)

**결정 4: Unsplash 이미지 사용**
- 이유: MVP 단계에서 빠른 프로토타입을 위해 무료 placeholder 이미지 사용
- 대안: 추후 실제 서비스 이미지로 교체 예정

### B. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| Campaign 모델이 아직 구현되지 않음 | 중 | 높음 | common-modules.md 우선 구현 또는 병렬 작업 |
| 템플릿이 복잡해져 유지보수 어려움 | 낮음 | 중 | 컴포넌트 분리 (include 활용) |
| Railway 배포 시 정적 파일 로딩 실패 | 낮음 | 중 | collectstatic 실행 및 WhiteNoise 설정 |
| N+1 쿼리 발생 | 낮음 | 중 | django-debug-toolbar로 모니터링 및 select_related 사용 |

### C. 참고 자료

- Django QuerySet API: https://docs.djangoproject.com/en/5.1/ref/models/querysets/
- Bootstrap 5 Cards: https://getbootstrap.com/docs/5.3/components/card/
- Django Template Language: https://docs.djangoproject.com/en/5.1/ref/templates/language/
- pytest-django: https://pytest-django.readthedocs.io/

---

## D. 코드 예시: CampaignFactory (Factory Boy)

홈 페이지 테스트에 필요한 Factory 클래스 예시입니다.

```python
# apps/campaigns/factories.py
import factory
from factory.django import DjangoModelFactory
from datetime import date, timedelta
from .models import Campaign
from apps.users.factories import AdvertiserFactory

class CampaignFactory(DjangoModelFactory):
    class Meta:
        model = Campaign

    advertiser = factory.SubFactory(AdvertiserFactory)
    name = factory.Sequence(lambda n: f'체험단 {n}')
    recruitment_start_date = date.today()
    recruitment_end_date = date.today() + timedelta(days=14)
    recruitment_count = 10
    benefits = '제품 무료 제공 + 소정의 원고료'
    mission = '방문 후 블로그 리뷰 작성'
    status = 'recruiting'
```

---

## E. DRY 원칙 준수 전략

### 중복 방지 체크리스트

1. **Selector 로직**:
   - ✅ `get_recruiting_campaigns()` 메서드를 다른 페이지에서도 재사용 가능
   - ✅ View에서 직접 ORM 쿼리 작성하지 않음

2. **템플릿 컴포넌트**:
   - ✅ base.html, _navbar.html은 다른 페이지에서도 재사용
   - ✅ 체험단 카드 레이아웃도 include 파일로 분리 가능 (추후 고려)

3. **테스트 Fixture**:
   - ✅ CampaignFactory는 다른 테스트에서도 재사용
   - ✅ conftest.py에 공통 fixture 정의

### 코드베이스 구조 엄수

- ✅ Layered Architecture 준수: View → Selector → Model
- ✅ 비즈니스 로직은 Service 계층 (현재 홈 페이지는 조회만 있어 Selector만 사용)
- ✅ DTO 불필요 (조회 전용 페이지)
