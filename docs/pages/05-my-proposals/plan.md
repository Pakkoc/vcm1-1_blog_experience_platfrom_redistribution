# 구현 계획: 내 지원 목록 (인플루언서)

## 프로젝트 ID: PLAN-005

### 제목
인플루언서 전용 - 내 지원 목록 조회 페이지

---

## 1. 개요

### 1.1 목표
인플루언서가 자신이 지원한 모든 체험단의 목록과 각 지원 건의 현재 상태(신청완료, 선정, 반려)를 한눈에 확인할 수 있는 페이지를 구현한다. 이를 통해 지원 현황을 투명하게 관리하고 선정 결과를 빠르게 파악할 수 있도록 한다.

### 1.2 참고 문서
- **PRD**: `docs/prd.md` - 섹션 5: 내 지원 목록 (인플루언서)
- **유스케이스**: `docs/usecases/03-my-applications/spec.md`
- **유저플로우**: `docs/userflow.md` - 섹션 1.3: 내 지원 목록 확인
- **데이터베이스 스키마**: `docs/database.md` - proposals 테이블
- **공통 모듈**: `docs/common-modules.md` - Selector 패턴, 권한 관리

### 1.3 범위

**포함 사항**:
- 본인의 지원 내역 조회 (proposals 테이블)
- 상태별 자동 정렬 (신청완료 → 선정 → 반려 순)
- 동일 상태 내 최신순 정렬
- 빈 상태(Empty State) UI 처리
- 각 지원 건 클릭 시 체험단 상세 페이지로 이동
- 인플루언서 역할 권한 체크

**제외 사항** (MVP 범위 외):
- 지원 건 수정/취소 기능
- 실시간 알림 기능
- 상세 필터링 UI (자동 정렬만 제공)
- 페이지네이션 (초기에는 전체 목록 노출)
- 검색 기능

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (Railway Volume 마운트)
- **ORM**: Django ORM
- **인증**: Django Session 기반 인증 (`@login_required`)
- **권한**: 커스텀 Mixin (`InfluencerRequiredMixin`)
- **테스트**: pytest + pytest-django

### 2.2 프론트엔드
- **템플릿 엔진**: Django Template
- **UI 프레임워크**: Bootstrap 5
- **JavaScript**: 선택적 사용 (기본 기능은 템플릿만으로 구현)
- **반응형 디자인**: Bootstrap Grid System

### 2.3 외부 서비스
- 없음 (순수 Django 내부 기능만 사용)

---

## 3. 데이터베이스 마이그레이션

### 3.1 새로운 테이블
없음 (기존 `proposals`, `campaigns`, `users` 테이블 사용)

### 3.2 기존 테이블 수정
없음 (기존 스키마 그대로 사용)

### 3.3 인덱스 추가/삭제

**확인 사항**: 이미 `database.md`에 정의된 인덱스가 존재하는지 확인
```sql
-- 성능 최적화를 위한 인덱스 (이미 존재해야 함)
CREATE INDEX IF NOT EXISTS idx_proposals_influencer_id ON proposals(influencer_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON proposals(created_at);
```

**추가 인덱스** (필요 시):
```sql
-- 복합 인덱스로 정렬 성능 향상 (선택사항)
CREATE INDEX IF NOT EXISTS idx_proposals_influencer_status_created
ON proposals(influencer_id, status, created_at DESC);
```

### 3.4 마이그레이션 실행 순서
1. 인덱스 확인 (기존 migration 파일에 포함 여부 체크)
2. 필요 시 새로운 migration 생성: `python manage.py makemigrations proposals`
3. Migration 적용: `python manage.py migrate proposals`

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: 데이터 조회 계층 구현 (Selector)

**목표**: proposals 테이블에서 인플루언서의 지원 내역을 효율적으로 조회하는 Selector 구현

**작업 항목**:

1. **ProposalSelector 클래스 생성**
   - 파일: `apps/proposals/selectors/proposal_selectors.py`
   - 설명: 인플루언서별 지원 목록 조회 로직 캡슐화
   - 의존성: 없음 (신규 생성)

   ```python
   # apps/proposals/selectors/proposal_selectors.py
   from typing import Optional
   from django.db.models import QuerySet, Case, When, IntegerField
   from ..models import Proposal

   class ProposalSelector:
       @staticmethod
       def get_influencer_proposals(influencer_id: int) -> QuerySet[Proposal]:
           """
           특정 인플루언서의 모든 지원 내역 조회

           정렬 순서:
           1. 상태별 (신청완료 → 선정 → 반려)
           2. 동일 상태 내에서 최신순

           N+1 쿼리 방지를 위해 select_related 사용
           """
           return Proposal.objects.filter(
               influencer_id=influencer_id
           ).select_related(
               'campaign',
               'campaign__advertiser'
           ).annotate(
               status_order=Case(
                   When(status='submitted', then=1),
                   When(status='selected', then=2),
                   When(status='rejected', then=3),
                   default=4,
                   output_field=IntegerField()
               )
           ).order_by('status_order', '-created_at')

       @staticmethod
       def get_proposal_count_by_status(influencer_id: int) -> dict:
           """
           인플루언서의 상태별 지원 건수 조회 (선택적 기능)
           """
           from django.db.models import Count

           counts = Proposal.objects.filter(
               influencer_id=influencer_id
           ).values('status').annotate(count=Count('id'))

           return {item['status']: item['count'] for item in counts}
   ```

2. **Selector 단위 테스트 작성**
   - 파일: `apps/proposals/tests/test_selectors.py`
   - 설명: ProposalSelector의 정확성 및 쿼리 최적화 검증
   - 의존성: ProposalSelector 클래스

   ```python
   # apps/proposals/tests/test_selectors.py
   import pytest
   from django.test import TestCase
   from apps.proposals.selectors.proposal_selectors import ProposalSelector
   from apps.proposals.models import Proposal
   # Factory 활용 (conftest.py에서 정의)

   @pytest.mark.django_db
   class TestProposalSelector:
       def test_get_influencer_proposals_returns_correct_order(
           self, influencer_user, sample_campaigns
       ):
           # Given: 다양한 상태의 지원 건 생성
           # submitted, selected, rejected 각 1건씩

           # When: Selector 호출
           proposals = ProposalSelector.get_influencer_proposals(
               influencer_id=influencer_user.id
           )

           # Then: 정렬 순서 검증
           statuses = [p.status for p in proposals]
           assert statuses == ['submitted', 'selected', 'rejected']

       def test_get_influencer_proposals_prevents_n_plus_1(
           self, influencer_user, django_assert_num_queries
       ):
           # Given: 지원 건 5개 생성

           # When: Selector 호출 및 campaign 정보 접근
           with django_assert_num_queries(1):  # 단 1번의 쿼리만 실행되어야 함
               proposals = list(
                   ProposalSelector.get_influencer_proposals(influencer_user.id)
               )
               for proposal in proposals:
                   _ = proposal.campaign.name  # N+1 발생하지 않아야 함

           # Then: 쿼리 수 제한 통과
   ```

**Acceptance Tests**:
- [x] 인플루언서의 지원 내역을 상태별로 올바르게 정렬
- [x] N+1 쿼리 문제 없이 단일 쿼리로 데이터 조회
- [x] 빈 결과 시 빈 QuerySet 반환

---

### Phase 2: View 및 URL 라우팅 구현

**목표**: HTTP 요청을 처리하고 Selector를 호출하여 템플릿에 데이터 전달

**작업 항목**:

1. **MyProposalsListView 클래스 생성**
   - 파일: `apps/proposals/views.py`
   - 설명: 인플루언서 전용 지원 목록 View
   - 의존성: ProposalSelector, InfluencerRequiredMixin (공통 모듈)

   ```python
   # apps/proposals/views.py
   from django.views.generic import ListView
   from django.contrib.auth.mixins import LoginRequiredMixin
   from apps.users.permissions import InfluencerRequiredMixin
   from .selectors.proposal_selectors import ProposalSelector
   from .models import Proposal

   class MyProposalsListView(LoginRequiredMixin, InfluencerRequiredMixin, ListView):
       """
       인플루언서 전용 - 내 지원 목록 페이지

       권한:
       - 로그인 필수
       - 인플루언서 역할만 접근 가능
       """
       template_name = 'proposals/my_proposals_list.html'
       context_object_name = 'proposals'

       def get_queryset(self):
           """Selector를 통해 지원 목록 조회"""
           return ProposalSelector.get_influencer_proposals(
               influencer_id=self.request.user.id
           )

       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)

           # 빈 상태 플래그
           context['has_proposals'] = self.get_queryset().exists()

           # 상태별 건수 (선택적)
           # context['status_counts'] = ProposalSelector.get_proposal_count_by_status(
           #     influencer_id=self.request.user.id
           # )

           return context
   ```

2. **URL 패턴 추가**
   - 파일: `apps/proposals/urls.py` (신규 생성 또는 기존 수정)
   - 설명: `/my/proposals/` 경로 라우팅
   - 의존성: MyProposalsListView

   ```python
   # apps/proposals/urls.py
   from django.urls import path
   from .views import MyProposalsListView

   app_name = 'proposals'

   urlpatterns = [
       path('proposals/', MyProposalsListView.as_view(), name='my_list'),
       # 향후 추가될 URL 패턴
   ]
   ```

3. **루트 URL에 연결**
   - 파일: `config/urls.py`
   - 설명: `/my/` 네임스페이스에 proposals 앱 연결
   - 의존성: apps.proposals.urls

   ```python
   # config/urls.py
   from django.urls import path, include

   urlpatterns = [
       # ... 기존 패턴
       path('my/', include('apps.proposals.urls', namespace='proposals')),
   ]
   ```

4. **View 통합 테스트 작성**
   - 파일: `apps/proposals/tests/test_views.py`
   - 설명: View의 권한 체크 및 템플릿 렌더링 검증
   - 의존성: MyProposalsListView, 테스트 Fixture

   ```python
   # apps/proposals/tests/test_views.py
   import pytest
   from django.urls import reverse
   from django.test import Client

   @pytest.mark.django_db
   class TestMyProposalsListView:
       def test_unauthenticated_user_redirects_to_login(self, client: Client):
           # Given: 비로그인 상태

           # When: 페이지 접근
           response = client.get(reverse('proposals:my_list'))

           # Then: 로그인 페이지로 리디렉션
           assert response.status_code == 302
           assert '/accounts/login/' in response.url

       def test_advertiser_user_gets_403(self, client: Client, advertiser_user):
           # Given: 광고주로 로그인
           client.force_login(advertiser_user)

           # When: 인플루언서 전용 페이지 접근
           response = client.get(reverse('proposals:my_list'))

           # Then: 403 Forbidden
           assert response.status_code == 403

       def test_influencer_sees_own_proposals(
           self, client: Client, influencer_user, sample_proposals
       ):
           # Given: 인플루언서로 로그인, 지원 내역 3건 존재
           client.force_login(influencer_user)

           # When: 페이지 접근
           response = client.get(reverse('proposals:my_list'))

           # Then: 200 OK 및 proposals 컨텍스트 포함
           assert response.status_code == 200
           assert 'proposals' in response.context
           assert len(response.context['proposals']) == 3

       def test_influencer_with_no_proposals_sees_empty_state(
           self, client: Client, influencer_user
       ):
           # Given: 인플루언서로 로그인, 지원 내역 없음
           client.force_login(influencer_user)

           # When: 페이지 접근
           response = client.get(reverse('proposals:my_list'))

           # Then: has_proposals = False
           assert response.status_code == 200
           assert response.context['has_proposals'] is False
   ```

**Acceptance Tests**:
- [x] 비로그인 사용자는 로그인 페이지로 리디렉션
- [x] 광고주 계정은 403 Forbidden 응답
- [x] 인플루언서는 본인의 지원 내역만 조회
- [x] 지원 내역 없을 시 빈 상태 플래그 설정

---

### Phase 3: 템플릿 구현

**목표**: 지원 목록을 사용자 친화적으로 표시하는 HTML 템플릿 작성

**작업 항목**:

1. **메인 템플릿 생성**
   - 파일: `apps/proposals/templates/proposals/my_proposals_list.html`
   - 설명: 지원 목록 UI 렌더링 (카드 형태)
   - 의존성: base.html (전역 템플릿)

   ```django
   {# apps/proposals/templates/proposals/my_proposals_list.html #}
   {% extends 'base.html' %}
   {% load static %}

   {% block title %}내 지원 목록 - 체험단 매칭 플랫폼{% endblock %}

   {% block content %}
   <div class="container my-5">
       <div class="row mb-4">
           <div class="col">
               <h2 class="fw-bold">내 지원 목록</h2>
               {% if has_proposals %}
                   <p class="text-muted">총 {{ proposals|length }}건</p>
               {% endif %}
           </div>
       </div>

       {% if has_proposals %}
           <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
               {% for proposal in proposals %}
                   <div class="col">
                       <div class="card h-100 shadow-sm">
                           <div class="card-body">
                               {# 상태 배지 #}
                               <div class="mb-2">
                                   {% if proposal.status == 'submitted' %}
                                       <span class="badge bg-primary">신청완료</span>
                                   {% elif proposal.status == 'selected' %}
                                       <span class="badge bg-success">선정</span>
                                   {% elif proposal.status == 'rejected' %}
                                       <span class="badge bg-secondary">반려</span>
                                   {% endif %}
                               </div>

                               {# 체험단명 #}
                               <h5 class="card-title">
                                   <a href="{% url 'campaigns:detail' proposal.campaign.id %}"
                                      class="text-decoration-none text-dark">
                                       {{ proposal.campaign.name }}
                                   </a>
                               </h5>

                               {# 지원 정보 #}
                               <div class="card-text text-muted small">
                                   <p class="mb-1">
                                       <i class="bi bi-calendar-event"></i>
                                       지원일: {{ proposal.created_at|date:"Y년 m월 d일" }}
                                   </p>
                                   <p class="mb-1">
                                       <i class="bi bi-calendar-check"></i>
                                       방문 희망일: {{ proposal.desired_visit_date|date:"Y년 m월 d일" }}
                                   </p>
                               </div>

                               {# 각오 한마디 미리보기 #}
                               <p class="card-text mt-2">
                                   <small class="text-muted">
                                       {{ proposal.cover_letter|truncatewords:10 }}
                                   </small>
                               </p>
                           </div>

                           <div class="card-footer bg-white border-0">
                               <a href="{% url 'campaigns:detail' proposal.campaign.id %}"
                                  class="btn btn-sm btn-outline-primary w-100">
                                   체험단 상세 보기
                               </a>
                           </div>
                       </div>
                   </div>
               {% endfor %}
           </div>
       {% else %}
           {# 빈 상태 UI #}
           <div class="text-center py-5">
               <i class="bi bi-inbox display-1 text-muted"></i>
               <h4 class="mt-4 text-muted">아직 지원한 체험단이 없습니다</h4>
               <p class="text-muted">다양한 체험단에 지원하고 새로운 경험을 시작해보세요!</p>
               <a href="{% url 'campaigns:list' %}" class="btn btn-primary mt-3">
                   체험단 둘러보기
               </a>
           </div>
       {% endif %}
   </div>
   {% endblock %}

   {% block extra_css %}
   <style>
       .card {
           transition: transform 0.2s, box-shadow 0.2s;
       }
       .card:hover {
           transform: translateY(-5px);
           box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
       }
   </style>
   {% endblock %}
   ```

2. **네비게이션 바에 링크 추가**
   - 파일: `templates/_navbar.html`
   - 설명: 인플루언서 로그인 시 '내 지원 목록' 링크 노출
   - 의존성: base.html

   ```django
   {# templates/_navbar.html #}
   {# 기존 코드에 추가 #}
   {% if user.is_authenticated and user.role == 'influencer' %}
       <li class="nav-item">
           <a class="nav-link" href="{% url 'proposals:my_list' %}">
               내 지원 목록
           </a>
       </li>
   {% endif %}
   ```

3. **템플릿 E2E 테스트**
   - 파일: `apps/proposals/tests/test_templates.py`
   - 설명: 템플릿이 올바르게 렌더링되는지 검증
   - 의존성: 통합 테스트 환경

   ```python
   # apps/proposals/tests/test_templates.py
   import pytest
   from django.urls import reverse

   @pytest.mark.django_db
   class TestMyProposalsListTemplate:
       def test_template_renders_proposals_correctly(
           self, client, influencer_user, sample_proposals
       ):
           # Given: 인플루언서로 로그인, 지원 내역 3건
           client.force_login(influencer_user)

           # When: 페이지 렌더링
           response = client.get(reverse('proposals:my_list'))

           # Then: 각 지원 건의 정보가 포함되어 있음
           assert '신청완료' in response.content.decode()
           assert '체험단 상세 보기' in response.content.decode()

       def test_empty_state_renders_when_no_proposals(
           self, client, influencer_user
       ):
           # Given: 인플루언서로 로그인, 지원 내역 없음
           client.force_login(influencer_user)

           # When: 페이지 렌더링
           response = client.get(reverse('proposals:my_list'))

           # Then: 빈 상태 메시지 및 CTA 버튼 표시
           content = response.content.decode()
           assert '아직 지원한 체험단이 없습니다' in content
           assert '체험단 둘러보기' in content
   ```

**Acceptance Tests**:
- [x] 지원 목록이 카드 형태로 표시
- [x] 각 카드에 상태 배지, 체험단명, 지원일, 방문 희망일 표시
- [x] 빈 상태 시 안내 메시지 및 CTA 버튼 노출
- [x] 네비게이션 바에 '내 지원 목록' 링크 표시 (인플루언서만)

---

### Phase 4: 권한 관리 및 보안

**목표**: 인플루언서만 접근 가능하도록 권한 체크 강화

**작업 항목**:

1. **InfluencerRequiredMixin 구현 (공통 모듈 활용)**
   - 파일: `apps/users/permissions.py`
   - 설명: 인플루언서 역할 검증 Mixin
   - 의존성: Django UserPassesTestMixin

   ```python
   # apps/users/permissions.py
   from django.contrib.auth.mixins import UserPassesTestMixin
   from django.core.exceptions import PermissionDenied

   class InfluencerRequiredMixin(UserPassesTestMixin):
       """
       인플루언서 역할만 접근 가능하도록 제한하는 Mixin

       사용법:
           class MyView(LoginRequiredMixin, InfluencerRequiredMixin, View):
               ...
       """
       def test_func(self):
           return (
               self.request.user.is_authenticated and
               self.request.user.role == 'influencer'
           )

       def handle_no_permission(self):
           if not self.request.user.is_authenticated:
               # 비로그인 → 로그인 페이지로
               return super().handle_no_permission()
           else:
               # 로그인했지만 권한 없음 → 403
               raise PermissionDenied("인플루언서 계정으로 로그인해주세요.")
   ```

2. **권한 검증 단위 테스트**
   - 파일: `apps/users/tests/test_permissions.py`
   - 설명: Mixin의 권한 체크 로직 검증
   - 의존성: InfluencerRequiredMixin

   ```python
   # apps/users/tests/test_permissions.py
   import pytest
   from django.core.exceptions import PermissionDenied
   from django.test import RequestFactory
   from apps.users.permissions import InfluencerRequiredMixin
   from django.views import View

   class DummyView(InfluencerRequiredMixin, View):
       def get(self, request):
           return "OK"

   @pytest.mark.django_db
   class TestInfluencerRequiredMixin:
       def test_influencer_user_passes(self, rf: RequestFactory, influencer_user):
           # Given: 인플루언서 사용자
           request = rf.get('/')
           request.user = influencer_user

           # When: test_func 호출
           view = DummyView()
           view.request = request

           # Then: True 반환
           assert view.test_func() is True

       def test_advertiser_user_fails(self, rf: RequestFactory, advertiser_user):
           # Given: 광고주 사용자
           request = rf.get('/')
           request.user = advertiser_user

           # When: test_func 호출
           view = DummyView()
           view.request = request

           # Then: False 반환
           assert view.test_func() is False
   ```

**Acceptance Tests**:
- [x] 인플루언서 사용자만 페이지 접근 가능
- [x] 광고주 접근 시 403 에러
- [x] 비로그인 접근 시 로그인 페이지로 리디렉션

---

## 5. URL 라우팅 전체 구조

### 5.1 URL 패턴 정의

**앱 레벨 URL** (`apps/proposals/urls.py`):
```python
from django.urls import path
from .views import MyProposalsListView

app_name = 'proposals'

urlpatterns = [
    path('proposals/', MyProposalsListView.as_view(), name='my_list'),
    # 향후 추가 가능:
    # path('proposals/<int:pk>/', ProposalDetailView.as_view(), name='detail'),
]
```

**루트 URL** (`config/urls.py`):
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.campaigns.urls', namespace='campaigns')),  # 홈 및 체험단
    path('accounts/', include('apps.users.urls', namespace='users')),  # 회원가입/로그인
    path('my/', include('apps.proposals.urls', namespace='proposals')),  # 내 지원 목록
    path('manage/', include('apps.manage.urls', namespace='manage')),  # 광고주 관리
]
```

### 5.2 URL 이름 규칙
- 네임스페이스: `proposals`
- URL 이름: `my_list`
- 전체 참조: `{% url 'proposals:my_list' %}` 또는 `reverse('proposals:my_list')`

---

## 6. 보안 고려사항

### 6.1 인증/인가
- **인증**: Django Session 기반 인증 (`LoginRequiredMixin`)
- **인가**: 인플루언서 역할 검증 (`InfluencerRequiredMixin`)
- **데이터 격리**: Selector에서 `filter(influencer_id=request.user.id)` 필터링으로 본인 데이터만 조회

### 6.2 데이터 보호
- **개인정보**: 본인의 지원 내역만 조회 가능 (다른 인플루언서 데이터 차단)
- **XSS 방지**: Django 템플릿 자동 이스케이핑 활용
- **CSRF 보호**: Django 기본 CSRF 미들웨어 사용

### 6.3 SQL Injection 방지
- Django ORM의 파라미터화된 쿼리 사용 (자동 방어)
- 사용자 입력을 직접 쿼리에 포함하지 않음

---

## 7. 에러 처리

### 7.1 백엔드 에러

| 에러 상황 | HTTP 상태 | 설명 | 처리 방법 |
|----------|----------|------|----------|
| 비로그인 접근 | 302 | 로그인되지 않은 사용자 | `/accounts/login/?next=/my/proposals/`로 리디렉션 |
| 광고주 접근 | 403 | 인플루언서 전용 페이지에 광고주 접근 | 403 에러 페이지 표시 및 안내 메시지 |
| DB 조회 실패 | 500 | 데이터베이스 연결 오류 | 에러 로그 기록 및 사용자에게 일시적 오류 안내 |

### 7.2 프론트엔드 에러 핸들링
- **403 에러 페이지**: `templates/403.html` 생성하여 권한 없음 안내
- **500 에러 페이지**: `templates/500.html` 생성하여 일시적 오류 안내
- **빈 상태**: 지원 내역 없을 시 Empty State UI 표시 (에러 아님)

---

## 8. 테스트 계획

### 8.1 단위 테스트

**파일**: `apps/proposals/tests/test_selectors.py`

**커버리지 목표**: 80% 이상

**테스트 케이스**:

| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-001 | 인플루언서 지원 목록 조회 성공 | influencer_id | 해당 인플루언서의 모든 지원 건 반환 |
| UT-002 | 상태별 정렬 검증 | 다양한 상태의 지원 건 | submitted → selected → rejected 순서 |
| UT-003 | 최신순 정렬 검증 | 동일 상태 지원 건 | created_at DESC 정렬 |
| UT-004 | N+1 쿼리 방지 검증 | 지원 건 5개 | 단 1번의 쿼리로 조회 |
| UT-005 | 빈 결과 처리 | 지원 내역 없는 인플루언서 | 빈 QuerySet 반환 (에러 없음) |

### 8.2 통합 테스트

**파일**: `apps/proposals/tests/test_views.py`

**시나리오**:
1. 비로그인 사용자 접근 → 로그인 페이지 리디렉션
2. 광고주 접근 → 403 Forbidden
3. 인플루언서 접근 → 본인의 지원 목록만 조회
4. 지원 내역 없는 인플루언서 → 빈 상태 플래그 설정

**검증 항목**:
- HTTP 상태 코드 정확성
- 리디렉션 URL 정확성
- 컨텍스트 데이터 포함 여부
- 권한 체크 로직 동작 여부

### 8.3 E2E 테스트

**파일**: `apps/proposals/tests/test_e2e.py` (선택사항)

**시나리오**:
1. 인플루언서 로그인
2. 홈 페이지에서 체험단 지원
3. '내 지원 목록' 클릭
4. 지원한 체험단이 목록에 표시되는지 확인
5. 광고주가 선정 처리
6. 새로고침 후 상태가 '선정'으로 변경되었는지 확인

**도구**: Django TestClient 또는 Selenium (필요 시)

---

## 9. 성능 고려사항

### 9.1 최적화 목표
- **페이지 로드 시간**: 2초 이내 (일반적인 네트워크 환경)
- **동시 접속자**: 100명까지 안정적 처리 (MVP 목표)
- **쿼리 최적화**: 페이지당 최대 3개 이하의 DB 쿼리

### 9.2 쿼리 최적화 전략
- **select_related**: `campaign`, `campaign__advertiser` 미리 로딩
- **인덱스 활용**: `influencer_id`, `status`, `created_at` 컬럼 인덱싱
- **복합 인덱스 고려**: `(influencer_id, status, created_at)` 복합 인덱스로 정렬 성능 향상

### 9.3 캐싱 전략
MVP 단계에서는 캐싱 제외 (향후 확장 시 고려):
- Django 캐싱 프레임워크 활용 가능
- 인플루언서별 지원 목록을 세션 또는 메모리 캐시에 저장

---

## 10. 배포 계획

### 10.1 환경 변수
추가 환경 변수 없음 (기존 Django 설정 사용)

### 10.2 배포 순서
1. **코드 배포**:
   - `git push origin main` → Railway 자동 배포 트리거
2. **Migration 실행**:
   - Railway 콘솔에서 `python manage.py migrate proposals` 실행
3. **정적 파일 수집** (필요 시):
   - `python manage.py collectstatic --noinput`
4. **헬스 체크**:
   - `/my/proposals/` 접근하여 페이지 정상 로드 확인
5. **내부 베타 테스트**:
   - 인플루언서 계정으로 로그인 후 지원 목록 확인

### 10.3 롤백 계획
- Railway에서 이전 배포 버전으로 롤백
- Migration 롤백: `python manage.py migrate proposals [이전 migration 번호]`

---

## 11. 모니터링 및 로깅

### 11.1 로그 항목
- **접근 로그**: 인플루언서의 '내 지원 목록' 페이지 접근 기록
- **에러 로그**: 403/500 에러 발생 시 사용자 정보 및 스택 트레이스 기록
- **쿼리 로그** (개발 환경): N+1 쿼리 발생 여부 모니터링

```python
# settings.py에 로깅 설정 추가
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/data/django.log',  # Railway Volume 경로
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

### 11.2 메트릭
MVP 단계에서는 기본 Railway 메트릭만 사용:
- **페이지 응답 시간**
- **메모리 사용량**
- **에러 발생 빈도**

---

## 12. 문서화

### 12.1 코드 문서화
- [x] Selector 메서드에 Docstring 작성 (파라미터, 반환값, 정렬 규칙 명시)
- [x] View 클래스에 주석 추가 (권한, 템플릿 경로 설명)
- [x] 템플릿에 주석 추가 (각 UI 블록 설명)

### 12.2 사용자 가이드
MVP 단계에서는 제외 (향후 작성 시 `docs/user-guide.md` 생성)

---

## 13. 체크리스트

### 13.1 구현 전
- [x] 유스케이스 검토 완료 (`docs/usecases/03-my-applications/spec.md`)
- [x] 데이터베이스 스키마 확인 (`docs/database.md`)
- [x] 공통 모듈 확인 (`docs/common-modules.md` - Selector, Mixin)
- [x] URL 구조 설계 완료

### 13.2 구현 중
- [ ] TDD 방식으로 개발 진행 (Selector → View → Template 순)
- [ ] ProposalSelector 단위 테스트 작성 및 통과
- [ ] MyProposalsListView 통합 테스트 작성 및 통과
- [ ] 템플릿 렌더링 E2E 테스트 작성 및 통과
- [ ] InfluencerRequiredMixin 권한 테스트 통과
- [ ] 코드 리뷰 완료 (동료 검토 또는 셀프 리뷰)

### 13.3 구현 후
- [ ] 모든 테스트 통과 (단위 + 통합 + E2E)
- [ ] N+1 쿼리 문제 없음 확인 (django-debug-toolbar 활용)
- [ ] 네비게이션 바 링크 정상 동작 확인
- [ ] 빈 상태 UI 정상 렌더링 확인
- [ ] 403/302 에러 핸들링 검증
- [ ] Railway 배포 및 헬스 체크 완료
- [ ] 내부 베타 테스터 피드백 수집 준비

---

## 14. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude (CTO) | 초기 작성 - UC-003 기반 구현 계획 수립 |

---

## 부록

### A. 주요 파일 경로 요약

```
apps/proposals/
├── selectors/
│   └── proposal_selectors.py         # ProposalSelector 클래스
├── views.py                           # MyProposalsListView 클래스
├── urls.py                            # URL 라우팅 (신규 생성)
├── templates/
│   └── proposals/
│       └── my_proposals_list.html     # 메인 템플릿
└── tests/
    ├── test_selectors.py              # Selector 단위 테스트
    ├── test_views.py                  # View 통합 테스트
    └── test_templates.py              # 템플릿 E2E 테스트

apps/users/
└── permissions.py                     # InfluencerRequiredMixin (공통)

config/
└── urls.py                            # 루트 URL 설정 (수정)

templates/
└── _navbar.html                       # 네비게이션 바 (수정)
```

### B. 의사결정 기록

**결정 1: Selector 패턴 사용**
- **이유**: 복잡한 정렬 로직(상태별 + 최신순)을 View와 분리하여 테스트 용이성 향상
- **대안**: View에서 직접 QuerySet 작성 → 코드 가독성 저하 및 재사용 불가

**결정 2: 카드 형태 UI 선택**
- **이유**: 각 지원 건의 정보가 많아 카드 형태가 시각적으로 더 직관적
- **대안**: 테이블 형태 → 모바일 환경에서 가독성 저하

**결정 3: 페이지네이션 제외**
- **이유**: MVP 단계에서는 지원 건수가 많지 않아 전체 목록 노출로 충분
- **대안**: 처음부터 페이지네이션 구현 → 오버엔지니어링

### C. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| N+1 쿼리 문제 | 중 | 높음 | select_related 사용 및 django-debug-toolbar로 검증 |
| 권한 체크 누락 | 낮 | 높음 | Mixin 단위 테스트 및 통합 테스트로 검증 |
| 빈 상태 UI 미처리 | 낮 | 중 | has_proposals 플래그 및 템플릿 분기 처리 |
| SQLite 동시성 문제 | 낮 | 중 | MVP 단계에서는 사용자 수 적어 무시, 향후 PostgreSQL 마이그레이션 계획 |

### D. 향후 확장 계획 (MVP 이후)

1. **페이지네이션 추가**
   - Django Paginator 사용
   - 페이지당 10건씩 표시

2. **필터링 UI**
   - 상태별 필터 (신청완료/선정/반려)
   - 날짜 범위 필터

3. **검색 기능**
   - 체험단명으로 검색
   - Django Q 객체 활용

4. **지원 취소 기능**
   - '신청완료' 상태만 취소 가능
   - 취소 시 proposals.status를 'cancelled'로 변경

5. **실시간 알림**
   - WebSocket 또는 Server-Sent Events
   - 선정/반려 시 실시간 알림

---

## 구현 우선순위 요약

1. **Phase 1 (필수)**: Selector 구현 및 단위 테스트
2. **Phase 2 (필수)**: View 및 URL 라우팅 구현
3. **Phase 3 (필수)**: 템플릿 구현 및 UI 테스트
4. **Phase 4 (필수)**: 권한 관리 및 보안 강화

**예상 개발 기간**: 2-3일 (TDD 방식, 테스트 포함)

---

이 구현 계획은 `docs/usecases/03-my-applications/spec.md`, `docs/prd.md`, `docs/database.md`, `docs/common-modules.md`를 모두 반영하여 작성되었으며, DRY 원칙과 Layered Architecture를 준수합니다.
