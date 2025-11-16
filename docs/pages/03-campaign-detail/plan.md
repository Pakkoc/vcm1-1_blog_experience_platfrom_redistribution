# 구현 계획: 체험단 상세 페이지

## 프로젝트 ID: PLAN-003

### 제목
체험단 상세 페이지 (Campaign Detail Page)

---

## 1. 개요

### 1.1 목표
모든 사용자(비로그인, 인플루언서, 광고주)가 체험단의 상세 정보를 확인할 수 있는 페이지를 구현합니다. 인플루언서 사용자에게는 지원 가능 여부를 판단하여 적절한 액션 버튼을 노출합니다.

### 1.2 참고 문서
- **PRD**: `docs/prd.md` - 3. 체험단 상세 페이지 명세
- **유스케이스**: `docs/usecases/02-apply-campaign/spec.md` - 체험단 지원 프로세스 (Step 1-2)
- **유저플로우**: `docs/userflow.md` - 인플루언서 여정 Step 3
- **데이터베이스**: `docs/database.md` - campaigns, proposals 테이블
- **공통 모듈**: `docs/common-modules.md` - Selector 패턴, 템플릿 구조

### 1.3 범위
**포함 사항**:
- 체험단 기본 정보 조회 및 표시
- 역할 및 상태에 따른 조건부 지원 버튼 렌더링
- 중복 지원 확인 로직
- 모집 기간 및 상태 검증
- 반응형 UI (Bootstrap)

**제외 사항**:
- 체험단 지원 폼 제출 처리 (별도 페이지: 04-campaign-apply)
- 광고주용 체험단 상세 (별도 페이지: 07-advertiser-campaign-detail)
- 체험단 수정/삭제 기능
- 댓글 또는 Q&A 기능

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (ORM: Django ORM)
- **인증**: Django Authentication (Session-based)
- **테스트**: pytest-django

### 2.2 프론트엔드
- **템플릿 엔진**: Django Template Language
- **UI 라이브러리**: Bootstrap 5.3
- **스타일**: Bootstrap + 커스텀 CSS (최소한)
- **테스트**: Django TestClient (통합 테스트)

### 2.3 아키텍처 패턴
- **계층 구조**: Presentation (View) → Business Logic (Selector) → Data (Model)
- **Selector 패턴**: 복잡한 조회 로직 분리
- **템플릿 상속**: base.html 기반

---

## 3. 데이터베이스 접근

### 3.1 조회할 테이블
**campaigns**:
- 체험단 기본 정보 (id, name, recruitment_start_date, recruitment_end_date, recruitment_count, benefits, mission, status)
- 광고주 정보 (advertiser_id → users.id)

**proposals**:
- 현재 로그인 사용자의 지원 여부 확인 (campaign_id, influencer_id)

**users / advertiser_profiles**:
- 광고주 업체 정보 (company_name)

### 3.2 필요한 쿼리
```python
# 1. 체험단 상세 조회 (광고주 정보 포함)
Campaign.objects.select_related('advertiser').get(id=pk)

# 2. 로그인한 인플루언서의 중복 지원 확인
Proposal.objects.filter(campaign_id=pk, influencer_id=user.id).exists()

# 3. 지원자 수 집계 (선택적)
Proposal.objects.filter(campaign_id=pk).count()
```

### 3.3 인덱스 활용
- `campaigns.id` (PK, 자동 인덱스)
- `idx_proposals_campaign_id` (proposals.campaign_id)
- `idx_proposals_influencer_id` (proposals.influencer_id)
- UNIQUE 제약조건 `unique_campaign_influencer_proposal` 활용

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: Selector 계층 구현

**목표**: 체험단 상세 조회 및 지원 가능 여부 판단 로직을 Selector로 분리

**작업 항목**:

1. **CampaignSelector 클래스 생성**
   - 파일: `apps/campaigns/selectors/campaign_selectors.py`
   - 설명: 체험단 조회 및 비즈니스 규칙 검증을 담당하는 Selector 클래스
   - 의존성: None (신규 생성)

   **구현 메서드**:
   ```python
   class CampaignSelector:
       @staticmethod
       def get_campaign_detail(campaign_id: int) -> Campaign:
           """
           체험단 상세 정보 조회 (광고주 정보 포함)

           Raises:
               Campaign.DoesNotExist: 존재하지 않는 체험단
           """
           return Campaign.objects.select_related(
               'advertiser',
               'advertiser__advertiserprofile'
           ).get(id=campaign_id)

       @staticmethod
       def check_user_can_apply(campaign: Campaign, user) -> dict:
           """
           사용자의 지원 가능 여부를 종합 판단

           Returns:
               {
                   'can_apply': bool,
                   'reason': str | None,  # 불가 시 이유
                   'already_applied': bool
               }
           """
           from datetime import date

           # 비로그인 사용자
           if not user.is_authenticated:
               return {
                   'can_apply': False,
                   'reason': 'login_required',
                   'already_applied': False
               }

           # 광고주 계정
           if user.role == 'advertiser':
               return {
                   'can_apply': False,
                   'reason': 'advertiser_not_allowed',
                   'already_applied': False
               }

           # 모집 상태 확인
           if campaign.status != 'recruiting':
               return {
                   'can_apply': False,
                   'reason': 'recruitment_ended',
                   'already_applied': False
               }

           # 모집 기간 확인
           today = date.today()
           if today > campaign.recruitment_end_date:
               return {
                   'can_apply': False,
                   'reason': 'deadline_passed',
                   'already_applied': False
               }

           # 중복 지원 확인
           from apps.proposals.models import Proposal
           already_applied = Proposal.objects.filter(
               campaign_id=campaign.id,
               influencer_id=user.id
           ).exists()

           if already_applied:
               return {
                   'can_apply': False,
                   'reason': 'already_applied',
                   'already_applied': True
               }

           # 모든 검증 통과
           return {
               'can_apply': True,
               'reason': None,
               'already_applied': False
           }
   ```

2. **Selector 단위 테스트 작성**
   - 파일: `apps/campaigns/tests/test_selectors.py`
   - 설명: TDD 방식으로 Selector 로직 검증
   - 의존성: CampaignSelector 구현 전 테스트 작성 (RED → GREEN)

   **테스트 케이스**:
   ```python
   import pytest
   from datetime import date, timedelta
   from apps.campaigns.selectors.campaign_selectors import CampaignSelector
   from apps.campaigns.models import Campaign
   from apps.users.models import User
   from apps.proposals.models import Proposal

   @pytest.mark.django_db
   class TestCampaignSelector:
       def test_get_campaign_detail_success(self, campaign_factory):
           """체험단 상세 조회 성공"""
           campaign = campaign_factory()
           result = CampaignSelector.get_campaign_detail(campaign.id)
           assert result.id == campaign.id
           assert result.advertiser is not None  # select_related 확인

       def test_get_campaign_detail_not_found(self):
           """존재하지 않는 체험단 조회 시 예외 발생"""
           with pytest.raises(Campaign.DoesNotExist):
               CampaignSelector.get_campaign_detail(99999)

       def test_check_user_can_apply_unauthenticated(self, campaign_factory):
           """비로그인 사용자는 지원 불가"""
           campaign = campaign_factory(status='recruiting')
           from django.contrib.auth.models import AnonymousUser
           result = CampaignSelector.check_user_can_apply(campaign, AnonymousUser())
           assert result['can_apply'] is False
           assert result['reason'] == 'login_required'

       def test_check_user_can_apply_advertiser(self, campaign_factory, advertiser_user):
           """광고주는 지원 불가"""
           campaign = campaign_factory(status='recruiting')
           result = CampaignSelector.check_user_can_apply(campaign, advertiser_user)
           assert result['can_apply'] is False
           assert result['reason'] == 'advertiser_not_allowed'

       def test_check_user_can_apply_recruitment_ended(self, campaign_factory, influencer_user):
           """모집 종료된 체험단은 지원 불가"""
           campaign = campaign_factory(status='recruitment_ended')
           result = CampaignSelector.check_user_can_apply(campaign, influencer_user)
           assert result['can_apply'] is False
           assert result['reason'] == 'recruitment_ended'

       def test_check_user_can_apply_deadline_passed(self, campaign_factory, influencer_user):
           """모집 기간이 지난 경우 지원 불가"""
           yesterday = date.today() - timedelta(days=1)
           campaign = campaign_factory(
               status='recruiting',
               recruitment_end_date=yesterday
           )
           result = CampaignSelector.check_user_can_apply(campaign, influencer_user)
           assert result['can_apply'] is False
           assert result['reason'] == 'deadline_passed'

       def test_check_user_can_apply_already_applied(self, campaign_factory, influencer_user):
           """이미 지원한 경우 지원 불가"""
           campaign = campaign_factory(status='recruiting')
           Proposal.objects.create(
               campaign=campaign,
               influencer=influencer_user,
               cover_letter="Test",
               desired_visit_date=date.today() + timedelta(days=1)
           )
           result = CampaignSelector.check_user_can_apply(campaign, influencer_user)
           assert result['can_apply'] is False
           assert result['reason'] == 'already_applied'
           assert result['already_applied'] is True

       def test_check_user_can_apply_success(self, campaign_factory, influencer_user):
           """모든 조건을 만족하면 지원 가능"""
           tomorrow = date.today() + timedelta(days=1)
           campaign = campaign_factory(
               status='recruiting',
               recruitment_end_date=tomorrow
           )
           result = CampaignSelector.check_user_can_apply(campaign, influencer_user)
           assert result['can_apply'] is True
           assert result['reason'] is None
           assert result['already_applied'] is False
   ```

**Acceptance Tests**:
- [ ] 체험단 조회 시 광고주 정보가 함께 조회됨 (N+1 쿼리 없음)
- [ ] 비로그인 사용자 접근 시 can_apply=False
- [ ] 광고주 계정 접근 시 can_apply=False
- [ ] 모집 종료/기간 만료 시 can_apply=False
- [ ] 중복 지원 확인 시 already_applied=True
- [ ] 모든 조건 만족 시 can_apply=True

---

### Phase 2: View 계층 구현

**목표**: 체험단 상세 정보를 조회하고 템플릿에 전달하는 View 구현

**작업 항목**:

1. **CampaignDetailView 클래스 생성**
   - 파일: `apps/campaigns/views.py`
   - 설명: 체험단 상세 페이지 렌더링을 담당하는 View
   - 의존성: CampaignSelector (Phase 1 완료 필요)

   **구현**:
   ```python
   from django.views.generic import DetailView
   from django.shortcuts import get_object_or_404
   from .models import Campaign
   from .selectors.campaign_selectors import CampaignSelector

   class CampaignDetailView(DetailView):
       """
       체험단 상세 페이지

       - 모든 사용자 접근 가능 (비로그인 포함)
       - 인플루언서 로그인 시 지원 가능 여부 판단
       """
       model = Campaign
       template_name = 'campaigns/campaign_detail.html'
       context_object_name = 'campaign'

       def get_object(self, queryset=None):
           """Selector를 통한 체험단 조회"""
           campaign_id = self.kwargs.get('pk')
           return CampaignSelector.get_campaign_detail(campaign_id)

       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)
           campaign = self.object

           # 지원 가능 여부 확인
           can_apply_info = CampaignSelector.check_user_can_apply(
               campaign,
               self.request.user
           )

           context.update({
               'can_apply': can_apply_info['can_apply'],
               'cannot_apply_reason': can_apply_info['reason'],
               'already_applied': can_apply_info['already_applied'],
           })

           return context
   ```

2. **URL 라우팅 설정**
   - 파일: `apps/campaigns/urls.py`
   - 설명: 체험단 상세 페이지 URL 패턴 추가
   - 의존성: CampaignDetailView 구현

   ```python
   from django.urls import path
   from .views import CampaignDetailView

   app_name = 'campaigns'

   urlpatterns = [
       path('<int:pk>/', CampaignDetailView.as_view(), name='detail'),
       # ... 기타 URL 패턴
   ]
   ```

3. **View 통합 테스트 작성**
   - 파일: `apps/campaigns/tests/test_views.py`
   - 설명: HTTP 요청/응답 레벨에서 View 동작 검증
   - 의존성: CampaignDetailView, URL 설정 완료

   **테스트 케이스**:
   ```python
   import pytest
   from django.urls import reverse
   from datetime import date, timedelta

   @pytest.mark.django_db
   class TestCampaignDetailView:
       def test_get_campaign_detail_anonymous_user(self, client, campaign_factory):
           """비로그인 사용자도 체험단 상세 조회 가능"""
           campaign = campaign_factory()
           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           assert response.status_code == 200
           assert 'campaign' in response.context
           assert response.context['can_apply'] is False
           assert response.context['cannot_apply_reason'] == 'login_required'

       def test_get_campaign_detail_influencer_can_apply(
           self, client, campaign_factory, influencer_user
       ):
           """인플루언서는 지원 가능한 체험단 접근 시 can_apply=True"""
           client.force_login(influencer_user)
           tomorrow = date.today() + timedelta(days=1)
           campaign = campaign_factory(
               status='recruiting',
               recruitment_end_date=tomorrow
           )
           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           assert response.status_code == 200
           assert response.context['can_apply'] is True
           assert response.context['cannot_apply_reason'] is None

       def test_get_campaign_detail_advertiser(self, client, campaign_factory, advertiser_user):
           """광고주는 can_apply=False"""
           client.force_login(advertiser_user)
           campaign = campaign_factory(status='recruiting')
           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           assert response.status_code == 200
           assert response.context['can_apply'] is False
           assert response.context['cannot_apply_reason'] == 'advertiser_not_allowed'

       def test_get_campaign_detail_already_applied(
           self, client, campaign_factory, influencer_user
       ):
           """이미 지원한 인플루언서는 already_applied=True"""
           from apps.proposals.models import Proposal

           client.force_login(influencer_user)
           campaign = campaign_factory(status='recruiting')
           Proposal.objects.create(
               campaign=campaign,
               influencer=influencer_user,
               cover_letter="Test",
               desired_visit_date=date.today() + timedelta(days=1)
           )

           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           assert response.status_code == 200
           assert response.context['can_apply'] is False
           assert response.context['already_applied'] is True

       def test_get_campaign_detail_not_found(self, client):
           """존재하지 않는 체험단 조회 시 404"""
           url = reverse('campaigns:detail', kwargs={'pk': 99999})
           response = client.get(url)
           assert response.status_code == 404
   ```

**Acceptance Tests**:
- [ ] GET /campaigns/<pk>/ 접근 시 200 OK 응답
- [ ] 체험단 정보가 context에 포함됨
- [ ] can_apply 플래그가 context에 포함됨
- [ ] 광고주 정보가 함께 렌더링됨 (N+1 쿼리 없음)
- [ ] 존재하지 않는 체험단 접근 시 404 응답

---

### Phase 3: 템플릿 구현

**목표**: 체험단 상세 정보를 표시하고 조건부로 지원 버튼을 렌더링하는 UI 구현

**작업 항목**:

1. **campaign_detail.html 템플릿 생성**
   - 파일: `apps/campaigns/templates/campaigns/campaign_detail.html`
   - 설명: 체험단 상세 페이지 템플릿
   - 의존성: base.html (공통 모듈)

   **템플릿 구조**:
   ```django
   {% extends 'base.html' %}
   {% load static %}

   {% block title %}{{ campaign.name }} - 체험단 상세{% endblock %}

   {% block content %}
   <div class="container my-4">
       <!-- 1. 페이지 헤더 -->
       <div class="row mb-4">
           <div class="col">
               <h1 class="display-5">{{ campaign.name }}</h1>
               <p class="text-muted">
                   {{ campaign.advertiser.advertiserprofile.company_name }}
               </p>
           </div>
       </div>

       <!-- 2. 체험단 기본 정보 카드 -->
       <div class="card mb-4">
           <div class="card-body">
               <h5 class="card-title">모집 정보</h5>
               <div class="row">
                   <div class="col-md-6">
                       <p><strong>모집 기간:</strong></p>
                       <p>
                           {{ campaign.recruitment_start_date|date:"Y년 m월 d일" }} ~
                           {{ campaign.recruitment_end_date|date:"Y년 m월 d일" }}
                       </p>
                   </div>
                   <div class="col-md-6">
                       <p><strong>모집 인원:</strong></p>
                       <p>{{ campaign.recruitment_count }}명</p>
                   </div>
               </div>

               <!-- 모집 상태 배지 -->
               <div class="mt-2">
                   {% if campaign.status == 'recruiting' %}
                       <span class="badge bg-success">모집 중</span>
                   {% elif campaign.status == 'recruitment_ended' %}
                       <span class="badge bg-secondary">모집 마감</span>
                   {% elif campaign.status == 'selection_complete' %}
                       <span class="badge bg-info">선정 완료</span>
                   {% endif %}
               </div>
           </div>
       </div>

       <!-- 3. 제공 혜택 -->
       <div class="card mb-4">
           <div class="card-body">
               <h5 class="card-title">제공 혜택</h5>
               <p class="card-text" style="white-space: pre-line;">{{ campaign.benefits }}</p>
           </div>
       </div>

       <!-- 4. 미션 내용 -->
       <div class="card mb-4">
           <div class="card-body">
               <h5 class="card-title">미션</h5>
               <p class="card-text" style="white-space: pre-line;">{{ campaign.mission }}</p>
           </div>
       </div>

       <!-- 5. 지원 액션 영역 (조건부 렌더링) -->
       <div class="card border-primary">
           <div class="card-body">
               {% if can_apply %}
                   <!-- 지원 가능 -->
                   <h5 class="card-title text-primary">이 체험단에 지원하세요!</h5>
                   <p class="card-text">
                       위 조건을 확인하셨다면 지원서를 작성하여 참여 의사를 전달해주세요.
                   </p>
                   <a href="{% url 'campaigns:apply' pk=campaign.id %}"
                      class="btn btn-primary btn-lg">
                       지원하기
                   </a>

               {% elif already_applied %}
                   <!-- 이미 지원 완료 -->
                   <h5 class="card-title text-muted">지원 완료</h5>
                   <p class="card-text">
                       이미 이 체험단에 지원하셨습니다.
                       선정 결과는 내 지원 목록에서 확인하실 수 있습니다.
                   </p>
                   <button type="button" class="btn btn-secondary btn-lg" disabled>
                       지원 완료
                   </button>
                   <a href="{% url 'proposals:my_list' %}" class="btn btn-outline-primary">
                       내 지원 목록 보기
                   </a>

               {% elif cannot_apply_reason == 'login_required' %}
                   <!-- 비로그인 -->
                   <h5 class="card-title text-info">로그인 후 지원 가능합니다</h5>
                   <p class="card-text">
                       이 체험단에 지원하려면 먼저 로그인해주세요.
                   </p>
                   <a href="{% url 'users:login' %}?next={{ request.path }}"
                      class="btn btn-info btn-lg">
                       로그인하기
                   </a>
                   <a href="{% url 'users:signup' %}" class="btn btn-outline-info">
                       회원가입
                   </a>

               {% elif cannot_apply_reason == 'advertiser_not_allowed' %}
                   <!-- 광고주 계정 -->
                   <h5 class="card-title text-muted">광고주는 체험단에 지원할 수 없습니다</h5>
                   <p class="card-text">
                       광고주 계정으로는 체험단 지원이 불가능합니다.
                   </p>

               {% elif cannot_apply_reason == 'recruitment_ended' or cannot_apply_reason == 'deadline_passed' %}
                   <!-- 모집 종료 -->
                   <h5 class="card-title text-danger">모집이 마감되었습니다</h5>
                   <p class="card-text">
                       이 체험단의 모집이 종료되어 더 이상 지원할 수 없습니다.
                   </p>
                   <button type="button" class="btn btn-secondary btn-lg" disabled>
                       모집 마감
                   </button>
                   <a href="{% url 'home' %}" class="btn btn-outline-primary">
                       다른 체험단 보기
                   </a>

               {% endif %}
           </div>
       </div>

       <!-- 6. 뒤로 가기 버튼 -->
       <div class="mt-3">
           <a href="{% url 'home' %}" class="btn btn-outline-secondary">
               목록으로 돌아가기
           </a>
       </div>
   </div>
   {% endblock %}
   ```

2. **템플릿 E2E 테스트**
   - 파일: `apps/campaigns/tests/test_templates.py`
   - 설명: 템플릿 렌더링 및 UI 요소 검증
   - 의존성: 템플릿 파일 작성 완료

   **테스트 케이스**:
   ```python
   import pytest
   from django.urls import reverse
   from bs4 import BeautifulSoup

   @pytest.mark.django_db
   class TestCampaignDetailTemplate:
       def test_template_renders_campaign_info(self, client, campaign_factory):
           """체험단 정보가 올바르게 렌더링됨"""
           campaign = campaign_factory(
               name="테스트 체험단",
               benefits="무료 제공",
               mission="리뷰 작성"
           )
           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           html = response.content.decode('utf-8')
           assert "테스트 체험단" in html
           assert "무료 제공" in html
           assert "리뷰 작성" in html

       def test_template_shows_apply_button_for_influencer(
           self, client, campaign_factory, influencer_user
       ):
           """인플루언서에게 지원하기 버튼이 표시됨"""
           from datetime import date, timedelta

           client.force_login(influencer_user)
           campaign = campaign_factory(
               status='recruiting',
               recruitment_end_date=date.today() + timedelta(days=1)
           )
           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           soup = BeautifulSoup(response.content, 'html.parser')
           apply_button = soup.find('a', text='지원하기')
           assert apply_button is not None
           assert 'btn-primary' in apply_button.get('class', [])

       def test_template_shows_login_button_for_anonymous(
           self, client, campaign_factory
       ):
           """비로그인 사용자에게 로그인 버튼이 표시됨"""
           campaign = campaign_factory(status='recruiting')
           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           soup = BeautifulSoup(response.content, 'html.parser')
           login_button = soup.find('a', text='로그인하기')
           assert login_button is not None

       def test_template_shows_applied_status_for_existing_proposal(
           self, client, campaign_factory, influencer_user
       ):
           """이미 지원한 경우 '지원 완료' 버튼이 표시됨"""
           from apps.proposals.models import Proposal
           from datetime import date, timedelta

           client.force_login(influencer_user)
           campaign = campaign_factory(status='recruiting')
           Proposal.objects.create(
               campaign=campaign,
               influencer=influencer_user,
               cover_letter="Test",
               desired_visit_date=date.today() + timedelta(days=1)
           )

           url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(url)

           soup = BeautifulSoup(response.content, 'html.parser')
           completed_button = soup.find('button', text='지원 완료')
           assert completed_button is not None
           assert 'disabled' in completed_button.attrs
   ```

**Acceptance Tests**:
- [ ] 체험단 이름, 모집 기간, 인원, 혜택, 미션이 모두 표시됨
- [ ] 광고주 업체명이 표시됨
- [ ] 모집 상태에 따라 배지 색상이 다름 (모집 중: 초록, 마감: 회색)
- [ ] 인플루언서 로그인 + 지원 가능 시 "지원하기" 버튼 활성화
- [ ] 비로그인 시 "로그인하기" 버튼 표시
- [ ] 이미 지원한 경우 "지원 완료" 버튼 비활성화 + "내 지원 목록 보기" 링크
- [ ] 모집 마감 시 "모집 마감" 버튼 비활성화 + "다른 체험단 보기" 링크

---

### Phase 4: 통합 및 E2E 테스트

**목표**: 전체 사용자 시나리오를 시뮬레이션하여 End-to-End 동작 검증

**작업 항목**:

1. **E2E 시나리오 테스트**
   - 파일: `apps/campaigns/tests/test_e2e.py`
   - 설명: 실제 사용자 플로우를 시뮬레이션
   - 의존성: 모든 Phase 완료

   **테스트 시나리오**:
   ```python
   import pytest
   from django.urls import reverse
   from datetime import date, timedelta

   @pytest.mark.django_db
   class TestCampaignDetailE2E:
       def test_influencer_journey_view_and_apply(
           self, client, campaign_factory, influencer_user
       ):
           """
           E2E 시나리오: 인플루언서가 체험단 상세를 보고 지원하기 버튼 클릭
           """
           # Given: 모집 중인 체험단 존재
           tomorrow = date.today() + timedelta(days=1)
           campaign = campaign_factory(
               name="맛집 체험단",
               status='recruiting',
               recruitment_end_date=tomorrow
           )

           # When: 인플루언서가 로그인 후 체험단 상세 페이지 접속
           client.force_login(influencer_user)
           detail_url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(detail_url)

           # Then: 페이지가 정상 렌더링되고 지원 버튼 표시
           assert response.status_code == 200
           assert "맛집 체험단" in response.content.decode('utf-8')
           assert response.context['can_apply'] is True

           # When: 지원하기 버튼의 링크 확인
           from bs4 import BeautifulSoup
           soup = BeautifulSoup(response.content, 'html.parser')
           apply_link = soup.find('a', text='지원하기')
           assert apply_link is not None

           expected_apply_url = reverse('campaigns:apply', kwargs={'pk': campaign.id})
           assert apply_link['href'] == expected_apply_url

           # Then: 지원 페이지로 이동 가능
           apply_response = client.get(expected_apply_url)
           assert apply_response.status_code == 200

       def test_anonymous_user_journey_redirected_to_login(
           self, client, campaign_factory
       ):
           """
           E2E 시나리오: 비로그인 사용자가 로그인 버튼 클릭
           """
           # Given: 체험단 존재
           campaign = campaign_factory(status='recruiting')

           # When: 비로그인 상태로 체험단 상세 접속
           detail_url = reverse('campaigns:detail', kwargs={'pk': campaign.id})
           response = client.get(detail_url)

           # Then: 로그인 버튼 표시
           assert response.status_code == 200
           assert response.context['can_apply'] is False
           assert response.context['cannot_apply_reason'] == 'login_required'

           # When: 로그인 버튼 클릭 시뮬레이션
           from bs4 import BeautifulSoup
           soup = BeautifulSoup(response.content, 'html.parser')
           login_link = soup.find('a', text='로그인하기')
           assert login_link is not None

           # Then: 로그인 페이지로 리디렉션 (next 파라미터 포함)
           login_url = login_link['href']
           assert '/accounts/login/' in login_url
           assert f'next={detail_url}' in login_url
   ```

**Acceptance Tests**:
- [ ] 인플루언서가 체험단 상세 → 지원하기 → 지원 페이지 이동 플로우 정상 작동
- [ ] 비로그인 사용자가 로그인 버튼 클릭 시 로그인 페이지로 이동 (next 파라미터 포함)
- [ ] 이미 지원한 인플루언서가 "내 지원 목록 보기" 클릭 시 정상 이동
- [ ] 모집 마감된 체험단 접근 시 "다른 체험단 보기" 클릭 시 홈으로 이동

---

## 5. URL 설계

### 5.1 엔드포인트: GET /campaigns/<int:pk>/

**URL 패턴**:
```python
path('<int:pk>/', CampaignDetailView.as_view(), name='detail')
```

**URL 예시**:
- `/campaigns/1/` - ID가 1인 체험단 상세
- `/campaigns/42/` - ID가 42인 체험단 상세

**쿼리 파라미터**: 없음

**URL 네임스페이스**: `campaigns:detail`

**역방향 URL 생성**:
```django
{% url 'campaigns:detail' pk=campaign.id %}
```

**응답 형식**: HTML (Django Template 렌더링)

---

## 6. 프론트엔드 컴포넌트

### 6.1 템플릿 파일: campaign_detail.html

**경로**: `apps/campaigns/templates/campaigns/campaign_detail.html`

**상속**: `base.html`

**Context 변수**:
```python
{
    'campaign': Campaign,           # 체험단 객체
    'can_apply': bool,              # 지원 가능 여부
    'cannot_apply_reason': str | None,  # 불가 사유
    'already_applied': bool,        # 중복 지원 여부
}
```

**Bootstrap 컴포넌트 사용**:
- Card: 정보 섹션 구분
- Badge: 모집 상태 표시
- Button: 액션 버튼 (지원하기, 로그인하기 등)
- Grid System: 반응형 레이아웃

**접근성 고려**:
- 버튼 비활성화 시 `disabled` 속성 추가
- 상태 배지에 적절한 색상 사용 (bg-success, bg-secondary 등)
- 링크에 명확한 텍스트 제공

---

## 7. 보안 고려사항

### 7.1 인증/인가
- **공개 페이지**: 모든 사용자 접근 가능 (비로그인 포함)
- **권한 검증**: 지원 가능 여부는 Selector에서 명시적으로 검증
- **세션 기반 인증**: Django Session Authentication 사용

### 7.2 데이터 보호
- **개인정보 노출 제한**: 광고주 이메일, 연락처 등 민감 정보는 상세 페이지에 노출하지 않음
- **광고주 정보**: 업체명만 공개

### 7.3 CSRF/XSS 방지
- **XSS 방지**: Django Template Auto-Escaping 활용
  - `{{ campaign.name }}` 등 사용자 입력 데이터 자동 이스케이프
  - `white-space: pre-line` CSS로 줄바꿈 유지하되 HTML 태그는 렌더링하지 않음
- **CSRF**: GET 요청이므로 CSRF 토큰 불필요

### 7.4 SQL Injection 방지
- **Django ORM 사용**: 모든 쿼리는 Django ORM을 통해 실행되어 자동 방지
- **파라미터화된 쿼리**: `get(id=pk)` 형태로 안전하게 처리

---

## 8. 에러 처리

### 8.1 백엔드 에러

| 에러 상황 | HTTP 상태 | 처리 방법 | 사용자 메시지 |
|----------|----------|----------|-------------|
| 존재하지 않는 체험단 ID | 404 Not Found | Django의 기본 404 페이지 또는 커스텀 404 템플릿 | "요청하신 체험단을 찾을 수 없습니다." |
| 데이터베이스 연결 오류 | 500 Internal Server Error | 로그 기록 후 일반 에러 페이지 | "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요." |
| 광고주 정보 조회 실패 (외래키 무결성) | 500 | 로그 기록 및 관리자 알림 | 일반 에러 메시지 |

### 8.2 프론트엔드 에러 핸들링

**404 페이지 커스터마이징** (선택적):
- 파일: `templates/404.html`
- 내용: "체험단을 찾을 수 없습니다. 홈으로 돌아가기 버튼 제공"

**버튼 상태 관리**:
- 지원 불가 시 버튼 비활성화 또는 숨김 처리
- 명확한 안내 메시지 표시

---

## 9. 테스트 계획

### 9.1 단위 테스트 (Selector)

**파일**: `apps/campaigns/tests/test_selectors.py`

**커버리지 목표**: 90% 이상

**테스트 케이스**:
| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-001 | 체험단 상세 조회 성공 | valid campaign_id | Campaign 객체 반환 |
| UT-002 | 체험단 상세 조회 실패 | invalid campaign_id | Campaign.DoesNotExist 예외 |
| UT-003 | 비로그인 사용자 지원 불가 | AnonymousUser | can_apply=False, reason='login_required' |
| UT-004 | 광고주 지원 불가 | advertiser_user | can_apply=False, reason='advertiser_not_allowed' |
| UT-005 | 모집 종료 체험단 지원 불가 | status='recruitment_ended' | can_apply=False, reason='recruitment_ended' |
| UT-006 | 모집 기간 만료 지원 불가 | recruitment_end_date < today | can_apply=False, reason='deadline_passed' |
| UT-007 | 중복 지원 확인 | existing Proposal | can_apply=False, already_applied=True |
| UT-008 | 정상 지원 가능 | valid influencer + valid campaign | can_apply=True, reason=None |

### 9.2 통합 테스트 (View)

**파일**: `apps/campaigns/tests/test_views.py`

**시나리오**: HTTP 요청/응답 레벨 검증

**테스트 케이스**:
| ID | 테스트 내용 | 전제 조건 | 기대 결과 |
|----|-----------|----------|----------|
| IT-001 | GET /campaigns/<pk>/ 성공 | valid campaign exists | 200 OK, context에 campaign 포함 |
| IT-002 | GET /campaigns/<pk>/ 404 | invalid campaign_id | 404 Not Found |
| IT-003 | 비로그인 접근 | AnonymousUser | 200 OK, can_apply=False |
| IT-004 | 인플루언서 접근 | logged-in influencer | 200 OK, can_apply=True (조건 충족 시) |
| IT-005 | 광고주 접근 | logged-in advertiser | 200 OK, can_apply=False |
| IT-006 | 중복 지원자 접근 | existing Proposal | 200 OK, already_applied=True |

### 9.3 E2E 테스트

**파일**: `apps/campaigns/tests/test_e2e.py`

**시나리오**: 사용자 플로우 전체 검증

1. **시나리오 1**: 인플루언서가 체험단 상세 → 지원하기 클릭 → 지원 페이지 이동
   - Given: 모집 중인 체험단 존재
   - When: 인플루언서 로그인 후 상세 페이지 접속
   - Then: 지원하기 버튼 클릭 시 `/campaigns/<pk>/apply/`로 이동

2. **시나리오 2**: 비로그인 사용자가 로그인 버튼 클릭 → 로그인 페이지로 이동
   - Given: 체험단 존재
   - When: 비로그인 상태로 상세 페이지 접속
   - Then: 로그인 버튼 클릭 시 `/accounts/login/?next=/campaigns/<pk>/`로 이동

3. **시나리오 3**: 이미 지원한 인플루언서가 내 지원 목록 이동
   - Given: 인플루언서가 이미 지원한 체험단
   - When: 상세 페이지 접속
   - Then: "내 지원 목록 보기" 버튼 클릭 시 `/my/proposals/`로 이동

---

## 10. 성능 고려사항

### 10.1 최적화 목표
- **응답 시간**: 페이지 로드 1초 이내 (일반 네트워크 환경)
- **데이터베이스 쿼리**: N+1 쿼리 제거

### 10.2 쿼리 최적화

**select_related 사용**:
```python
Campaign.objects.select_related(
    'advertiser',
    'advertiser__advertiserprofile'
).get(id=pk)
```
- 1회 JOIN 쿼리로 체험단 + 광고주 + 광고주 프로필 정보 조회
- N+1 쿼리 방지

**중복 지원 확인 쿼리 최적화**:
```python
Proposal.objects.filter(
    campaign_id=pk,
    influencer_id=user.id
).exists()
```
- `exists()` 사용으로 레코드 전체를 가져오지 않고 존재 여부만 확인
- 인덱스 활용: `idx_proposals_campaign_id`, `idx_proposals_influencer_id`

### 10.3 캐싱 전략 (MVP 단계 제외)
- 추후 Redis를 활용한 체험단 상세 정보 캐싱 고려
- MVP에서는 구현하지 않음 (오버엔지니어링 방지)

---

## 11. 배포 고려사항

### 11.1 환경 변수
추가/수정할 환경 변수 없음

### 11.2 Static Files
- Bootstrap 5.3은 CDN 사용 (별도 빌드 불필요)
- 커스텀 CSS 파일이 필요한 경우 `static/css/campaigns.css` 추가 가능

### 11.3 마이그레이션
- 새로운 모델 추가 없음
- 기존 `campaigns` 테이블 스키마 사용

### 11.4 Railway 배포 시 확인 사항
- [ ] `ALLOWED_HOSTS` 설정에 Railway 도메인 추가
- [ ] Static files 경로 확인 (`python manage.py collectstatic`)
- [ ] SQLite Volume 마운트 경로 확인

---

## 12. 모니터링 및 로깅

### 12.1 로그 항목
- **INFO 레벨**: 체험단 상세 페이지 접근 (campaign_id, user_id)
- **WARNING 레벨**: 존재하지 않는 체험단 접근 시도
- **ERROR 레벨**: 데이터베이스 조회 실패

**로깅 예시**:
```python
import logging

logger = logging.getLogger(__name__)

class CampaignDetailView(DetailView):
    def get_object(self, queryset=None):
        try:
            campaign = CampaignSelector.get_campaign_detail(self.kwargs['pk'])
            logger.info(
                f"Campaign detail viewed: campaign_id={campaign.id}, "
                f"user_id={self.request.user.id if self.request.user.is_authenticated else 'anonymous'}"
            )
            return campaign
        except Campaign.DoesNotExist:
            logger.warning(f"Campaign not found: campaign_id={self.kwargs['pk']}")
            raise
```

### 12.2 메트릭 (선택적)
- 체험단 상세 페이지 조회 수 (향후 인기 체험단 분석 가능)
- 지원 버튼 클릭률 추적 (Google Analytics 등 활용)

---

## 13. 문서화

### 13.1 코드 주석
- **Docstring**: 모든 클래스 및 메서드에 Google Style Docstring 작성
- **Inline Comments**: 복잡한 비즈니스 로직에 한해 설명 추가

### 13.2 README 업데이트
- `README.md`에 체험단 상세 페이지 URL 패턴 추가
- 예시:
  ```markdown
  ## URL 목록
  - 체험단 상세: `/campaigns/<int:pk>/`
  ```

---

## 14. 체크리스트

### 14.1 구현 전
- [x] PRD 및 유스케이스 문서 검토 완료
- [x] 데이터베이스 스키마 확인 (campaigns, proposals 테이블)
- [x] URL 설계 확정 (`/campaigns/<int:pk>/`)
- [x] Selector 패턴 구조 이해

### 14.2 구현 중
- [ ] Phase 1: CampaignSelector 구현 및 단위 테스트 통과
- [ ] Phase 2: CampaignDetailView 구현 및 통합 테스트 통과
- [ ] Phase 3: campaign_detail.html 템플릿 구현 및 UI 테스트 통과
- [ ] Phase 4: E2E 테스트 작성 및 통과
- [ ] 코드 리뷰 완료
- [ ] N+1 쿼리 확인 (django-debug-toolbar 활용)

### 14.3 구현 후
- [ ] 모든 단위 테스트 통과 (커버리지 90% 이상)
- [ ] 모든 통합 테스트 통과
- [ ] E2E 테스트 시나리오 통과
- [ ] 접근성 검토 (버튼 비활성화, 스크린 리더 대응)
- [ ] 반응형 디자인 확인 (모바일/태블릿/데스크톱)
- [ ] 로그 설정 확인
- [ ] 문서 업데이트 (README, 코드 주석)

---

## 15. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude | 초기 작성 - PRD 3. 체험단 상세 페이지 기반 구현 계획 수립 |

---

## 부록

### A. 주요 비즈니스 로직 의사코드

**Selector: check_user_can_apply**
```python
function check_user_can_apply(campaign, user):
    # 1. 인증 확인
    if user is not authenticated:
        return {can_apply: false, reason: 'login_required'}

    # 2. 역할 확인
    if user.role == 'advertiser':
        return {can_apply: false, reason: 'advertiser_not_allowed'}

    # 3. 모집 상태 확인
    if campaign.status != 'recruiting':
        return {can_apply: false, reason: 'recruitment_ended'}

    # 4. 모집 기간 확인
    if today > campaign.recruitment_end_date:
        return {can_apply: false, reason: 'deadline_passed'}

    # 5. 중복 지원 확인
    if Proposal.exists(campaign_id=campaign.id, influencer_id=user.id):
        return {can_apply: false, reason: 'already_applied', already_applied: true}

    # 6. 모든 조건 통과
    return {can_apply: true, reason: null, already_applied: false}
```

### B. 의사결정 기록

**결정 1**: Selector 패턴 사용
- **이유**: 복잡한 조회 및 검증 로직을 View에서 분리하여 재사용성과 테스트 용이성 향상
- **대안**: View에 모든 로직 작성 → 코드 중복 및 테스트 어려움 발생 가능성

**결정 2**: 조건부 렌더링을 템플릿에서 처리
- **이유**: Django Template Language의 `{% if %}` 문법으로 충분히 구현 가능하며, 별도 JavaScript 불필요
- **대안**: React 등 SPA 프레임워크 사용 → MVP 단계에서 오버엔지니어링

**결정 3**: 중복 지원 확인을 Selector에서 수행
- **이유**: 비즈니스 규칙 검증은 Selector의 책임 영역
- **대안**: View에서 직접 쿼리 → 로직 분산 및 재사용 어려움

### C. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| N+1 쿼리 발생 (광고주 정보 조회) | 중 | 높음 | select_related 사용으로 사전 방지, django-debug-toolbar로 검증 |
| 모집 기간 종료 체험단에 대한 경쟁 상태 (Race Condition) | 낮 | 중 | 지원 페이지에서 최종 재검증 수행 (이중 확인) |
| 템플릿 조건문 복잡도 증가 | 중 | 낮 | Selector에서 명확한 플래그 반환으로 템플릿 로직 단순화 |
| SQLite 동시성 문제 | 낮 | 중 | MVP 단계에서는 트래픽이 적어 문제 없음. 향후 PostgreSQL 마이그레이션 고려 |

### D. 참고 자료

- **Django Class-Based Views**: https://docs.djangoproject.com/en/stable/topics/class-based-views/
- **Django ORM select_related**: https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related
- **Bootstrap 5 Cards**: https://getbootstrap.com/docs/5.3/components/card/
- **Django Template Language**: https://docs.djangoproject.com/en/stable/ref/templates/language/

---

## 구현 우선순위 요약

1. **Phase 1 (Critical)**: Selector 구현 - 비즈니스 로직의 핵심
2. **Phase 2 (Critical)**: View 구현 - HTTP 요청 처리
3. **Phase 3 (High)**: 템플릿 구현 - 사용자 UI
4. **Phase 4 (Medium)**: E2E 테스트 - 전체 플로우 검증

**예상 작업 시간**: 약 6-8시간 (테스트 포함)

**의존성 확인**:
- `apps/users/models.py` (User 모델) - 사전 구현 필요
- `apps/campaigns/models.py` (Campaign 모델) - 사전 구현 필요
- `apps/proposals/models.py` (Proposal 모델) - 사전 구현 필요
- `templates/base.html` (공통 템플릿) - 사전 구현 필요

---

이 계획서에 따라 구현을 진행하면, PRD 및 유스케이스 요구사항을 모두 만족하는 체험단 상세 페이지를 안정적으로 완성할 수 있습니다.
