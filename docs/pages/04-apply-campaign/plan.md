# 구현 계획: 체험단 지원 페이지 (Campaign Application Page)

## 프로젝트 ID: PLAN-004

### 제목
체험단 지원 페이지 구현 (PRD 페이지 #4: 체험단 지원)

---

## 1. 개요

### 1.1 목표
인플루언서가 관심 있는 체험단 캠페인에 지원서를 작성하고 제출할 수 있는 완전한 기능을 구현한다. 이를 통해 광고주는 자신의 체험단에 지원한 인플루언서 목록을 확보하고, 인플루언서는 체험단 참여 기회를 얻을 수 있다.

### 1.2 참고 문서
- **PRD**: `docs/prd.md` - 페이지 #4 (체험단 지원)
- **유스케이스**: `docs/usecases/02-apply-campaign/spec.md` - UC-002
- **유저플로우**: `docs/userflow.md` - 1.2. 체험단 지원
- **데이터베이스 스키마**: `docs/database.md` - proposals 테이블
- **공통 모듈**: `docs/common-modules.md` - ProposalCreationService

### 1.3 범위

**포함 사항**:
- 체험단 지원 페이지 UI/UX (`/campaigns/<int:pk>/apply/`)
- 지원서 입력 폼 (각오 한마디, 방문 희망일)
- 지원 자격 검증 (로그인, 역할, 모집 상태, 중복 여부)
- ProposalCreationService를 활용한 지원 로직
- 성공/실패 피드백 및 리디렉션
- 예외 상황 처리 (모집 종료, 중복 지원, 권한 오류 등)

**제외 사항**:
- 지원서 수정/취소 기능 (MVP 범위 외)
- 실시간 알림 (선정/반려 알림은 향후 기능)
- 체험단 상세 페이지 구현 (별도 페이지)
- 내 지원 목록 페이지 구현 (별도 페이지)

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (개발 및 배포)
- **ORM**: Django ORM
- **인증**: Django Authentication System (Session-based)
- **테스트**: pytest, pytest-django

### 2.2 프론트엔드
- **템플릿 엔진**: Django Template Language (DTL)
- **UI 프레임워크**: Bootstrap 5.3
- **폼 처리**: Django Forms
- **클라이언트 검증**: HTML5 validation + Bootstrap form validation

### 2.3 아키텍처 패턴
- **Layered Architecture**: Presentation (View) → Business Logic (Service) → Data Access (Model)
- **DTO 패턴**: 계층 간 데이터 전송은 ProposalCreateDTO 사용
- **Service 패턴**: ProposalCreationService를 통한 비즈니스 로직 캡슐화

---

## 3. 데이터베이스 마이그레이션

### 3.1 기존 테이블 활용
이 기능은 기존에 정의된 `proposals` 테이블을 사용하므로 **새로운 마이그레이션이 필요하지 않음**.

**참조: `proposals` 테이블 구조** (database.md)
```sql
CREATE TABLE proposals (
    id BIGSERIAL PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    influencer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cover_letter TEXT NOT NULL,
    desired_visit_date DATE NOT NULL,
    status proposal_status NOT NULL DEFAULT 'submitted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_campaign_influencer_proposal UNIQUE (campaign_id, influencer_id)
);
```

### 3.2 필요한 인덱스 (이미 존재)
```sql
CREATE INDEX idx_proposals_campaign_id ON proposals(campaign_id);
CREATE INDEX idx_proposals_influencer_id ON proposals(influencer_id);
```

### 3.3 데이터 무결성 검증
- UNIQUE 제약조건: `(campaign_id, influencer_id)` - 중복 지원 방지
- Foreign Key: `campaign_id` → `campaigns(id)`, `influencer_id` → `users(id)`
- NOT NULL: `cover_letter`, `desired_visit_date` - 필수 입력 보장

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: DTO 및 Service 구현 (공통 모듈 활용)

**목표**: 비즈니스 로직을 View에서 분리하고 재사용 가능한 Service 계층 구성

**작업 항목**:

1. **ProposalCreateDTO 정의**
   - 파일: `apps/proposals/dto.py`
   - 설명: 지원서 생성에 필요한 데이터 계약 정의
   - 의존성: 없음

   ```python
   # apps/proposals/dto.py
   from dataclasses import dataclass
   from datetime import date

   @dataclass(frozen=True)
   class ProposalCreateDTO:
       campaign_id: int
       influencer_id: int
       cover_letter: str
       desired_visit_date: date
   ```

2. **ProposalCreationService 구현**
   - 파일: `apps/proposals/services/proposal_creation.py`
   - 설명: 지원서 생성 비즈니스 로직 (공통 모듈 명세 기반)
   - 의존성: ProposalCreateDTO, Proposal 모델

   ```python
   # apps/proposals/services/proposal_creation.py
   from django.db import IntegrityError
   from ..models import Proposal
   from ..dto import ProposalCreateDTO
   from apps.common.exceptions import DuplicateActionException, InvalidStateException
   from apps.campaigns.models import Campaign

   class ProposalCreationService:
       def execute(self, dto: ProposalCreateDTO) -> Proposal:
           """
           체험단 지원서를 생성한다.

           Args:
               dto: ProposalCreateDTO - 지원서 생성 데이터

           Returns:
               Proposal - 생성된 지원서 객체

           Raises:
               InvalidStateException: 체험단이 모집 중이 아닌 경우
               DuplicateActionException: 이미 지원한 경우
           """
           # 1. 체험단 상태 확인
           try:
               campaign = Campaign.objects.get(id=dto.campaign_id)
           except Campaign.DoesNotExist:
               raise InvalidStateException("존재하지 않는 체험단입니다.")

           if campaign.status != 'recruiting':
               raise InvalidStateException("모집이 종료된 체험단입니다.")

           # 2. 모집 기간 확인
           from datetime import date
           if campaign.recruitment_end_date < date.today():
               raise InvalidStateException("모집 기간이 종료되었습니다.")

           # 3. 지원서 생성 (UNIQUE 제약조건으로 중복 방지)
           try:
               proposal = Proposal.objects.create(
                   campaign_id=dto.campaign_id,
                   influencer_id=dto.influencer_id,
                   cover_letter=dto.cover_letter,
                   desired_visit_date=dto.desired_visit_date,
                   status='submitted'
               )
               return proposal
           except IntegrityError:
               raise DuplicateActionException("이미 지원한 체험단입니다.")
   ```

**Acceptance Tests**:
- [ ] ProposalCreateDTO 생성 및 불변성 테스트
- [ ] ProposalCreationService.execute() 성공 시나리오 테스트
- [ ] 모집 종료 상태에서 InvalidStateException 발생 테스트
- [ ] 중복 지원 시 DuplicateActionException 발생 테스트

---

### Phase 2: Form 및 유효성 검증

**목표**: 사용자 입력 데이터의 유효성을 검증하는 Django Form 구현

**작업 항목**:

1. **ProposalCreateForm 구현**
   - 파일: `apps/proposals/forms.py`
   - 설명: 지원서 입력 폼 및 클라이언트/서버 검증
   - 의존성: Proposal 모델

   ```python
   # apps/proposals/forms.py
   from django import forms
   from datetime import date

   class ProposalCreateForm(forms.Form):
       cover_letter = forms.CharField(
           label="각오 한마디",
           max_length=500,
           widget=forms.Textarea(attrs={
               'class': 'form-control',
               'rows': 4,
               'placeholder': '이 체험단에 선정되어야 하는 이유를 간단히 작성해주세요.',
               'maxlength': 500,
           }),
           error_messages={
               'required': '각오 한마디를 입력해주세요.',
               'max_length': '500자 이내로 입력해주세요.',
           }
       )

       desired_visit_date = forms.DateField(
           label="방문 희망일",
           widget=forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date',
               'min': date.today().isoformat(),
           }),
           error_messages={
               'required': '방문 희망일을 선택해주세요.',
               'invalid': '올바른 날짜를 입력해주세요.',
           }
       )

       def clean_desired_visit_date(self):
           visit_date = self.cleaned_data['desired_visit_date']
           if visit_date < date.today():
               raise forms.ValidationError("오늘 이후 날짜를 선택해주세요.")
           return visit_date
   ```

**Acceptance Tests**:
- [ ] 유효한 데이터 입력 시 form.is_valid() == True
- [ ] cover_letter 공백 시 ValidationError
- [ ] cover_letter 501자 입력 시 ValidationError
- [ ] desired_visit_date 과거 날짜 입력 시 ValidationError

---

### Phase 3: View 구현 (Presentation Layer)

**목표**: HTTP 요청/응답 처리 및 Service 계층 오케스트레이션

**작업 항목**:

1. **ProposalCreateView (CBV) 구현**
   - 파일: `apps/proposals/views.py`
   - 설명: GET (폼 표시), POST (폼 제출 및 Service 호출)
   - 의존성: ProposalCreateForm, ProposalCreationService, ProposalCreateDTO

   ```python
   # apps/proposals/views.py
   from django.shortcuts import render, redirect, get_object_or_404
   from django.contrib.auth.mixins import LoginRequiredMixin
   from django.contrib import messages
   from django.views import View
   from django.core.exceptions import PermissionDenied

   from apps.campaigns.models import Campaign
   from .forms import ProposalCreateForm
   from .dto import ProposalCreateDTO
   from .services.proposal_creation import ProposalCreationService
   from apps.common.exceptions import InvalidStateException, DuplicateActionException

   class ProposalCreateView(LoginRequiredMixin, View):
       template_name = 'proposals/proposal_create.html'

       def dispatch(self, request, *args, **kwargs):
           # 인플루언서 역할 확인
           if request.user.role != 'influencer':
               raise PermissionDenied("체험단에 지원할 권한이 없습니다.")
           return super().dispatch(request, *args, **kwargs)

       def get(self, request, pk):
           # 체험단 조회 및 지원 가능 여부 확인
           campaign = get_object_or_404(Campaign, pk=pk)

           # 이미 지원했는지 확인
           from .models import Proposal
           already_applied = Proposal.objects.filter(
               campaign_id=pk,
               influencer_id=request.user.id
           ).exists()

           if already_applied:
               messages.warning(request, "이미 지원한 체험단입니다.")
               return redirect('proposals:my_proposals')

           # 모집 상태 확인
           if campaign.status != 'recruiting':
               messages.error(request, "모집이 종료된 체험단입니다.")
               return redirect('campaigns:detail', pk=pk)

           form = ProposalCreateForm()
           context = {
               'campaign': campaign,
               'form': form,
           }
           return render(request, self.template_name, context)

       def post(self, request, pk):
           campaign = get_object_or_404(Campaign, pk=pk)
           form = ProposalCreateForm(request.POST)

           if not form.is_valid():
               context = {
                   'campaign': campaign,
                   'form': form,
               }
               return render(request, self.template_name, context)

           # DTO 생성
           dto = ProposalCreateDTO(
               campaign_id=pk,
               influencer_id=request.user.id,
               cover_letter=form.cleaned_data['cover_letter'],
               desired_visit_date=form.cleaned_data['desired_visit_date'],
           )

           # Service 실행
           try:
               service = ProposalCreationService()
               service.execute(dto)

               messages.success(request, "지원이 성공적으로 완료되었습니다.")
               return redirect('proposals:my_proposals')

           except InvalidStateException as e:
               messages.error(request, str(e))
               return redirect('campaigns:detail', pk=pk)

           except DuplicateActionException as e:
               messages.warning(request, str(e))
               return redirect('proposals:my_proposals')
   ```

2. **URL 라우팅 설정**
   - 파일: `apps/proposals/urls.py`
   - 설명: 체험단 지원 URL 패턴 정의

   ```python
   # apps/proposals/urls.py
   from django.urls import path
   from .views import ProposalCreateView

   app_name = 'proposals'

   urlpatterns = [
       path('campaigns/<int:pk>/apply/', ProposalCreateView.as_view(), name='apply'),
       # ... 다른 URL 패턴
   ]
   ```

3. **프로젝트 URL 연결**
   - 파일: `config/urls.py`
   - 설명: proposals 앱 URL 포함

   ```python
   # config/urls.py
   urlpatterns = [
       # ...
       path('', include(('apps.proposals.urls', 'proposals'), namespace='proposals')),
   ]
   ```

**Acceptance Tests**:
- [ ] GET 요청 시 폼 페이지 정상 렌더링
- [ ] 비로그인 사용자 접근 시 로그인 페이지 리디렉션
- [ ] 광고주 계정 접근 시 403 Forbidden
- [ ] POST 요청 성공 시 proposals 테이블에 레코드 생성
- [ ] 중복 지원 시 경고 메시지 및 리디렉션
- [ ] 모집 종료된 체험단 지원 시 에러 메시지

---

### Phase 4: Template 구현 (UI)

**목표**: Bootstrap 기반 직관적이고 사용자 친화적인 UI 구현

**작업 항목**:

1. **지원서 작성 템플릿**
   - 파일: `apps/proposals/templates/proposals/proposal_create.html`
   - 설명: 지원서 입력 폼 UI

   ```html
   {% extends 'base.html' %}
   {% load static %}

   {% block title %}체험단 지원하기 - {{ campaign.name }}{% endblock %}

   {% block content %}
   <div class="container mt-4">
       <div class="row justify-content-center">
           <div class="col-md-8">
               <!-- 페이지 헤더 -->
               <h2 class="mb-4">체험단 지원하기</h2>

               <!-- 체험단 정보 카드 (읽기 전용) -->
               <div class="card mb-4">
                   <div class="card-body">
                       <h5 class="card-title">{{ campaign.name }}</h5>
                       <p class="card-text text-muted">{{ campaign.benefits|truncatewords:20 }}</p>
                       <div class="row">
                           <div class="col-md-6">
                               <small class="text-muted">
                                   <i class="bi bi-calendar"></i>
                                   모집기간: {{ campaign.recruitment_start_date }} ~ {{ campaign.recruitment_end_date }}
                               </small>
                           </div>
                           <div class="col-md-6">
                               <small class="text-muted">
                                   <i class="bi bi-people"></i>
                                   모집인원: {{ campaign.recruitment_count }}명
                               </small>
                           </div>
                       </div>
                   </div>
               </div>

               <!-- 지원서 입력 폼 -->
               <div class="card">
                   <div class="card-body">
                       <form method="post" novalidate>
                           {% csrf_token %}

                           <!-- 각오 한마디 -->
                           <div class="mb-3">
                               <label for="{{ form.cover_letter.id_for_label }}" class="form-label">
                                   {{ form.cover_letter.label }} <span class="text-danger">*</span>
                               </label>
                               {{ form.cover_letter }}
                               {% if form.cover_letter.errors %}
                                   <div class="invalid-feedback d-block">
                                       {{ form.cover_letter.errors.0 }}
                                   </div>
                               {% endif %}
                               <div class="form-text">
                                   이 체험단에 선정되어야 하는 이유를 간단히 작성해주세요. (최대 500자)
                               </div>
                           </div>

                           <!-- 방문 희망일 -->
                           <div class="mb-4">
                               <label for="{{ form.desired_visit_date.id_for_label }}" class="form-label">
                                   {{ form.desired_visit_date.label }} <span class="text-danger">*</span>
                               </label>
                               {{ form.desired_visit_date }}
                               {% if form.desired_visit_date.errors %}
                                   <div class="invalid-feedback d-block">
                                       {{ form.desired_visit_date.errors.0 }}
                                   </div>
                               {% endif %}
                               <div class="form-text">
                                   오늘 이후 날짜를 선택해주세요.
                               </div>
                           </div>

                           <!-- 액션 버튼 -->
                           <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                               <a href="{% url 'campaigns:detail' campaign.id %}" class="btn btn-secondary">
                                   취소
                               </a>
                               <button type="submit" class="btn btn-primary">
                                   제출하기
                               </button>
                           </div>
                       </form>
                   </div>
               </div>
           </div>
       </div>
   </div>
   {% endblock %}
   ```

2. **베이스 템플릿 메시지 표시 (이미 구현됨)**
   - 파일: `templates/_messages.html` (공통 모듈)
   - 설명: Django messages framework를 통한 피드백 표시

**Acceptance Tests**:
- [ ] 체험단 정보가 읽기 전용으로 정확히 표시됨
- [ ] 폼 필드에 Bootstrap 스타일 적용
- [ ] 유효성 검증 실패 시 에러 메시지가 필드 하단에 표시
- [ ] 제출 버튼 클릭 시 폼 제출 및 로딩 상태 표시 (optional)
- [ ] 취소 버튼 클릭 시 체험단 상세 페이지로 이동

---

### Phase 5: 예외 처리 및 보안

**목표**: 모든 예외 상황을 안전하게 처리하고 보안 취약점 제거

**작업 항목**:

1. **공통 예외 클래스 활용**
   - 파일: `apps/common/exceptions.py` (이미 정의됨)
   - 설명: InvalidStateException, DuplicateActionException 활용

2. **권한 검증 Mixin (재사용)**
   - 파일: `apps/users/permissions.py`
   - 설명: InfluencerRequiredMixin 활용 (이미 구현됨)

3. **CSRF 보호**
   - Django의 기본 CSRF 미들웨어 활용
   - 템플릿에 `{% csrf_token %}` 포함

4. **XSS 방지**
   - Django Template Auto-Escaping 활용
   - 사용자 입력 데이터 자동 이스케이프

5. **SQL Injection 방지**
   - Django ORM 사용으로 자동 방지
   - Raw Query 사용 금지

**Acceptance Tests**:
- [ ] CSRF 토큰 없이 POST 요청 시 403 Forbidden
- [ ] 비인증 사용자 접근 시 로그인 페이지 리디렉션
- [ ] 광고주 계정 접근 시 PermissionDenied 예외
- [ ] 악의적인 스크립트 입력 시 자동 이스케이프

---

## 5. URL 엔드포인트 구현

### 5.1 엔드포인트: GET /campaigns/<int:pk>/apply/

**목적**: 체험단 지원 페이지 렌더링 및 폼 표시

**요청**:
```http
GET /campaigns/1/apply/
Cookie: sessionid=<session_id>
```

**응답**:
- **200 OK**: 지원 폼 페이지 HTML
- **302 Found**: 이미 지원한 경우 → `/my/proposals/` (경고 메시지)
- **302 Found**: 모집 종료 → `/campaigns/1/` (에러 메시지)
- **403 Forbidden**: 광고주 계정 접근
- **404 Not Found**: 존재하지 않는 campaign_id

**구현 파일**:
- View: `apps/proposals/views.py` - `ProposalCreateView.get()`
- Template: `apps/proposals/templates/proposals/proposal_create.html`

**단위 테스트**:
- [ ] 유효한 인플루언서 접근 시 200 OK 및 폼 렌더링
- [ ] 이미 지원한 경우 302 리디렉션 및 경고 메시지
- [ ] 모집 종료 체험단 접근 시 302 리디렉션

---

### 5.2 엔드포인트: POST /campaigns/<int:pk>/apply/

**목적**: 지원서 제출 및 처리

**요청**:
```http
POST /campaigns/1/apply/
Content-Type: application/x-www-form-urlencoded
Cookie: sessionid=<session_id>

cover_letter=이+체험단에+꼭+참여하고+싶습니다!&desired_visit_date=2025-11-20
```

**응답**:
- **302 Found**: 성공 → `/my/proposals/` (성공 메시지)
- **200 OK**: 폼 검증 실패 → 에러 메시지와 함께 폼 재렌더링
- **302 Found**: 중복 지원 → `/my/proposals/` (경고 메시지)
- **302 Found**: 모집 종료 → `/campaigns/1/` (에러 메시지)

**구현 파일**:
- View: `apps/proposals/views.py` - `ProposalCreateView.post()`
- Form: `apps/proposals/forms.py` - `ProposalCreateForm`
- Service: `apps/proposals/services/proposal_creation.py`
- DTO: `apps/proposals/dto.py`

**단위 테스트**:
- [ ] 유효한 데이터 제출 시 proposals 테이블에 레코드 생성
- [ ] 폼 검증 실패 시 200 OK 및 에러 표시
- [ ] 중복 지원 시 DuplicateActionException 처리
- [ ] 모집 종료 체험단 제출 시 InvalidStateException 처리

---

## 6. 보안 고려사항

### 6.1 인증/인가
- **LoginRequiredMixin**: 모든 요청에 로그인 필수
- **역할 기반 접근 제어**: `request.user.role == 'influencer'` 검증
- **소유권 검증**: 인플루언서는 자신의 지원만 생성 가능 (user_id 자동 설정)

### 6.2 데이터 보호
- **CSRF 보호**: Django CSRF 미들웨어 활성화
- **Session 보안**: SESSION_COOKIE_SECURE=True (프로덕션)
- **HTTPS 강제**: Railway 배포 시 HTTPS 자동 적용

### 6.3 입력 검증
- **서버 검증**: Django Form을 통한 모든 입력 재검증
- **XSS 방지**: Django Template Auto-Escaping
- **SQL Injection 방지**: Django ORM Parameterized Query

### 6.4 에러 정보 노출 방지
- 프로덕션 환경: DEBUG=False
- Generic 에러 페이지 (400, 403, 404, 500)
- 상세 에러는 로그에만 기록

---

## 7. 에러 처리

### 7.1 백엔드 에러

| 에러 코드 | HTTP 상태 | 설명 | 처리 방법 |
|----------|----------|------|----------|
| InvalidStateException | 302 Redirect | 모집 종료/상태 변경 | 체험단 상세로 리디렉션 + 에러 메시지 |
| DuplicateActionException | 302 Redirect | 중복 지원 | 내 지원 목록으로 리디렉션 + 경고 메시지 |
| PermissionDenied | 403 Forbidden | 광고주 접근 | 403 에러 페이지 표시 |
| Campaign.DoesNotExist | 404 Not Found | 존재하지 않는 체험단 | 404 에러 페이지 표시 |
| ValidationError | 200 OK | 폼 검증 실패 | 폼 재렌더링 + 필드별 에러 메시지 |

### 7.2 프론트엔드 에러 핸들링
- **Django Messages Framework**: 성공/경고/에러 메시지 표시
- **Bootstrap Alert**: 자동으로 닫히는 알림 (3-5초)
- **Inline 에러**: 필드 하단에 빨간색 텍스트로 에러 표시
- **Empty State**: 조건부 렌더링으로 버튼 비활성화

---

## 8. 테스트 계획

### 8.1 단위 테스트

**파일**: `apps/proposals/tests/test_services.py`

**테스트 케이스**:
| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-004-01 | ProposalCreationService 성공 시나리오 | 유효한 DTO | Proposal 객체 생성, status='submitted' |
| UT-004-02 | 모집 종료 체험단 지원 | status='recruitment_ended' | InvalidStateException 발생 |
| UT-004-03 | 중복 지원 방지 | 이미 존재하는 (campaign_id, influencer_id) | DuplicateActionException 발생 |
| UT-004-04 | ProposalCreateForm 유효성 검증 | cover_letter 공백 | ValidationError, is_valid()=False |
| UT-004-05 | 방문 희망일 과거 날짜 | desired_visit_date < today | ValidationError |

**커버리지 목표**: 80% 이상

---

### 8.2 통합 테스트

**파일**: `apps/proposals/tests/test_views.py`

**시나리오**:
1. **성공 플로우**: 인플루언서 로그인 → GET 폼 페이지 → POST 유효한 데이터 → 302 리디렉션 → DB 레코드 생성 확인
2. **중복 지원 플로우**: 이미 지원한 체험단 → GET 요청 → 경고 메시지 + 리디렉션
3. **권한 오류 플로우**: 광고주 로그인 → GET 요청 → 403 Forbidden

**검증 항목**:
- HTTP 응답 코드 정확성
- 리디렉션 URL 정확성
- Django messages 존재 여부
- 데이터베이스 상태 변경 확인

---

### 8.3 E2E 테스트

**파일**: `tests/e2e/test_apply_campaign.py`

**시나리오**:
1. 인플루언서 로그인
2. 홈 페이지에서 모집 중 체험단 클릭
3. 체험단 상세 페이지에서 "지원하기" 버튼 클릭
4. 지원서 페이지에서 각오 한마디 입력
5. 방문 희망일 선택
6. 제출 버튼 클릭
7. 내 지원 목록 페이지로 리디렉션 확인
8. 성공 메시지 표시 확인
9. 방금 지원한 체험단이 목록에 있는지 확인

**도구**: pytest + Django TestClient

---

## 9. 성능 고려사항

### 9.1 최적화 목표
- 지원서 제출 후 리디렉션까지 **2초 이내** (일반 네트워크)
- 동시 지원 처리량: 초당 **10건 이상**

### 9.2 쿼리 최적화
- **중복 확인 쿼리**: `idx_proposals_campaign_id`, `idx_proposals_influencer_id` 인덱스 활용
- **UNIQUE 제약조건**: 데이터베이스 레벨 중복 방지로 애플리케이션 로직 단순화
- **N+1 방지**: Campaign 조회 시 select_related 불필요 (단일 객체 조회)

### 9.3 캐싱 전략
- MVP 단계에서는 캐싱 제외 (오버엔지니어링 방지)
- 향후 필요 시 Redis 도입 고려

---

## 10. 배포 계획

### 10.1 환경 변수
```bash
# 추가 환경 변수 없음
# 기존 Django 설정 활용
```

### 10.2 배포 순서
1. **단계 1**: 로컬 개발 환경에서 전체 기능 테스트 (`python manage.py runserver`)
2. **단계 2**: 단위/통합 테스트 실행 및 통과 확인 (`pytest`)
3. **단계 3**: Git commit 및 push (`git push origin main`)
4. **단계 4**: Railway 자동 배포 트리거
5. **단계 5**: 배포 로그 확인 및 Health Check
6. **단계 6**: 프로덕션 환경에서 E2E 테스트 수동 실행

### 10.3 롤백 계획
- Railway에서 이전 배포 버전으로 즉시 롤백
- 데이터베이스 마이그레이션 없으므로 데이터 일관성 유지

---

## 11. 모니터링 및 로깅

### 11.1 로그 항목
- **INFO**: 지원 성공 (`Proposal created: campaign_id={}, influencer_id={}`)
- **WARNING**: 중복 지원 시도 (`Duplicate proposal attempt: campaign_id={}, influencer_id={}`)
- **ERROR**: InvalidStateException (`Invalid campaign state: campaign_id={}, status={}`)

### 11.2 메트릭
- **지원 성공률**: (성공 건수 / 전체 시도) * 100
- **평균 응답 시간**: 지원 페이지 GET 요청 ~ POST 응답 시간
- **에러 발생률**: 예외 발생 건수 / 전체 요청

---

## 12. 체크리스트

### 12.1 구현 전
- [x] 유스케이스 검토 완료 (UC-002)
- [x] 데이터베이스 스키마 확인 (proposals 테이블)
- [x] 공통 모듈 검토 (ProposalCreationService)
- [x] URL 설계 완료 (`/campaigns/<int:pk>/apply/`)

### 12.2 구현 중
- [ ] ProposalCreateDTO 정의
- [ ] ProposalCreationService 구현 (TDD)
- [ ] ProposalCreateForm 구현 및 유효성 검증
- [ ] ProposalCreateView 구현 (GET, POST)
- [ ] 템플릿 구현 (proposal_create.html)
- [ ] URL 라우팅 설정
- [ ] 단위 테스트 작성 및 통과
- [ ] 통합 테스트 작성 및 통과

### 12.3 구현 후
- [ ] E2E 테스트 수동 실행 및 통과
- [ ] 보안 검토 (CSRF, XSS, 권한)
- [ ] 성능 테스트 (응답 시간 2초 이내)
- [ ] 코드 리뷰 완료
- [ ] 배포 준비 완료

---

## 13. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude | 초기 작성 - UC-002, userflow.md, common-modules.md 기반 구현 계획 수립 |

---

## 부록

### A. 주요 로직 의사코드

```python
# ProposalCreateView.post() 핵심 로직
def post(request, campaign_id):
    # 1. 폼 검증
    form = ProposalCreateForm(request.POST)
    if not form.is_valid():
        return render_with_errors(form)

    # 2. DTO 생성
    dto = ProposalCreateDTO(
        campaign_id=campaign_id,
        influencer_id=request.user.id,
        cover_letter=form.cleaned_data['cover_letter'],
        desired_visit_date=form.cleaned_data['desired_visit_date']
    )

    # 3. Service 실행
    try:
        service = ProposalCreationService()
        proposal = service.execute(dto)
        return redirect_with_success_message()
    except InvalidStateException:
        return redirect_with_error_message()
    except DuplicateActionException:
        return redirect_with_warning_message()
```

### B. 의사결정 기록

**결정 1**: ProposalCreationService 재사용
- **이유**: common-modules.md에서 이미 설계된 Service를 활용하여 DRY 원칙 준수
- **대안**: View에서 직접 Proposal.objects.create() 호출 (X - 비즈니스 로직 분리 원칙 위배)

**결정 2**: Django CBV (Class-Based View) 사용
- **이유**: LoginRequiredMixin, dispatch() 메서드를 활용한 권한 검증이 용이
- **대안**: FBV (Function-Based View) + 데코레이터 (가능하지만 코드 가독성 저하)

**결정 3**: 중복 확인을 GET 시점과 POST 시점 양쪽에서 수행
- **이유**: Race Condition 방지 및 사용자 경험 개선 (GET에서 미리 차단)
- **대안**: POST에서만 확인 (가능하지만 불필요한 폼 작성 유도)

### C. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| 동시 지원 시 Race Condition | 낮음 | 중 | UNIQUE 제약조건으로 데이터베이스 레벨 방지 |
| 모집 종료 직전 지원 시도 | 중 | 중 | POST 시점에 상태 재확인 로직 추가 |
| 악의적인 대량 지원 | 낮음 | 낮음 | MVP에서는 제외, 향후 Rate Limiting 도입 |
| 폼 검증 우회 시도 | 낮음 | 낮음 | 서버 검증 필수, 클라이언트 검증은 UX 목적만 |

---

## 참고: 페이지 간 연계

### 선행 페이지
- **페이지 #3**: 체험단 상세 페이지 (`/campaigns/<int:pk>/`)
  - "지원하기" 버튼 클릭 시 이 페이지로 이동
  - can_apply 플래그 기반 조건부 렌더링

### 후행 페이지
- **페이지 #5**: 내 지원 목록 (`/my/proposals/`)
  - 지원 성공 후 리디렉션 대상
  - 방금 지원한 체험단이 목록 최상단에 표시

### 연관 기능
- **공통 모듈**: ProposalCreationService (이미 구현 예정)
- **인증 시스템**: LoginRequiredMixin, InfluencerRequiredMixin
- **메시징 시스템**: Django messages framework
