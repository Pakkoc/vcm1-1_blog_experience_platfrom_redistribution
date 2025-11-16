# 구현 계획: 체험단 관리 (광고주)

## 프로젝트 ID: PLAN-006

### 제목
광고주용 체험단 관리 대시보드 및 신규 체험단 등록

---

## 1. 개요

### 1.1 목표
광고주가 자신이 등록한 모든 체험단 캠페인을 한눈에 조회하고, 각 캠페인의 상태를 확인하며, 신규 체험단을 다이얼로그 폼을 통해 손쉽게 등록할 수 있는 대시보드를 구현합니다.

### 1.2 참고 문서
- **PRD**: `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\prd.md` (4.2. 광고주 여정)
- **유스케이스**: `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\usecases\05-create-campaign\spec.md`
- **데이터베이스 스키마**: `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\database.md`
- **공통 모듈**: `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\common-modules.md`
- **유저플로우**: `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\userflow.md` (2.2. 신규 체험단 등록)

### 1.3 범위

**포함 사항**:
- 광고주가 등록한 체험단 목록 조회 (카드 형태)
- 각 체험단의 기본 정보 표시 (체험단명, 모집 기간, 상태, 지원자 수)
- '신규 체험단 등록' 버튼 및 다이얼로그 폼
- 체험단 생성 비즈니스 로직 (CampaignCreationService 활용)
- 광고주 전용 권한 검증
- 체험단 카드 클릭 시 광고주용 체험단 상세 페이지로 이동

**제외 사항** (MVP 범위 외):
- 체험단 검색 및 필터링 기능
- 체험단 수정/삭제 기능
- 통계 대시보드 (총 지원자 수, 선정률 등)
- 일괄 작업 (대량 삭제, 상태 일괄 변경 등)
- 체험단 임시저장 기능
- 이미지 업로드 기능

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (Railway Volume 경로)
- **ORM**: Django ORM
- **인증**: Django Session-based Authentication
- **테스트**: pytest + pytest-django
- **아키텍처**: Layered Architecture (View → Service → Model)

### 2.2 프론트엔드
- **프레임워크**: Django Template
- **UI 라이브러리**: Bootstrap 5.3
- **스타일링**: Bootstrap CSS + 커스텀 CSS (필요 시)
- **JavaScript**: Vanilla JS (다이얼로그 제어, 폼 검증)

### 2.3 외부 서비스
- 없음 (MVP 단계)

---

## 3. 데이터베이스 마이그레이션

### 3.1 새로운 테이블
이 페이지는 기존 `campaigns` 테이블을 사용하므로 신규 테이블 생성은 없습니다.

### 3.2 기존 테이블 수정
없음. `campaigns` 테이블은 이미 `database.md`에 정의되어 있습니다.

### 3.3 인덱스 추가/삭제
`database.md`의 마이그레이션 SQL에 이미 포함되어 있습니다:
```sql
CREATE INDEX idx_campaigns_advertiser_id ON campaigns(advertiser_id);
```

### 3.4 마이그레이션 실행 순서
1. 공통 모듈 개발 완료 후 `campaigns` 앱의 모델 정의 확인
2. `python manage.py makemigrations campaigns`
3. `python manage.py migrate`

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: 데이터 조회 계층 (Selector 구현)

**목표**: 광고주별 체험단 목록을 효율적으로 조회하는 Selector 구현

**작업 항목**:

1. **CampaignSelector 구현**
   - 파일: `apps/campaigns/selectors/campaign_selectors.py`
   - 설명:
     - `get_campaigns_by_advertiser(advertiser_id: int)` 메서드 구현
     - QuerySet에 `annotate(proposal_count=Count('proposals'))`를 사용하여 각 캠페인의 지원자 수를 함께 조회
     - `select_related('advertiser')`로 N+1 쿼리 방지
     - 최신순 정렬 (`-created_at`)
   - 의존성: `campaigns` 모델 정의 완료

```python
# apps/campaigns/selectors/campaign_selectors.py
from typing import List
from django.db.models import QuerySet, Count
from ..models import Campaign

class CampaignSelector:
    @staticmethod
    def get_campaigns_by_advertiser(advertiser_id: int) -> QuerySet[Campaign]:
        """
        특정 광고주가 등록한 모든 체험단을 조회합니다.

        - 지원자 수(proposal_count)를 함께 조회
        - 최신순 정렬
        - N+1 쿼리 방지
        """
        return Campaign.objects.filter(
            advertiser_id=advertiser_id
        ).select_related('advertiser').annotate(
            proposal_count=Count('proposals')
        ).order_by('-created_at')
```

2. **CampaignSelector 단위 테스트**
   - 파일: `apps/campaigns/tests/test_selectors.py`
   - 설명:
     - 광고주별 필터링 정확성 검증
     - proposal_count 어노테이션 검증
     - N+1 쿼리 없음 검증 (django-debug-toolbar 또는 assertNumQueries)
   - 의존성: CampaignSelector 구현 완료

**Acceptance Tests**:
- [ ] 광고주 A가 등록한 캠페인만 조회됨 (다른 광고주 캠페인은 제외)
- [ ] 각 캠페인 객체에 `proposal_count` 속성이 존재하고 정확한 값을 가짐
- [ ] 최신 등록 순으로 정렬됨
- [ ] 단일 쿼리로 모든 캠페인과 지원자 수 조회 (N+1 쿼리 없음)

---

### Phase 2: 비즈니스 로직 계층 (Service 구현)

**목표**: 체험단 생성 비즈니스 로직을 Service 계층에서 처리

**작업 항목**:

1. **CampaignCreateDTO 정의**
   - 파일: `apps/campaigns/dto.py`
   - 설명:
     - 체험단 생성에 필요한 모든 필드를 불변 데이터 클래스로 정의
     - `@dataclass(frozen=True)` 사용
   - 의존성: 없음

```python
# apps/campaigns/dto.py
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class CampaignCreateDTO:
    """체험단 생성 입력 데이터"""
    name: str
    recruitment_start_date: date
    recruitment_end_date: date
    recruitment_count: int
    benefits: str
    mission: str
```

2. **CampaignCreationService 구현**
   - 파일: `apps/campaigns/services/campaign_creation.py`
   - 설명:
     - `execute(user: User, dto: CampaignCreateDTO) -> Campaign` 메서드 구현
     - 권한 확인 (user.role == 'advertiser')
     - 비즈니스 규칙 검증 (모집 종료일 >= 모집 시작일)
     - Campaign 객체 생성 및 반환
   - 의존성: CampaignCreateDTO 정의 완료

```python
# apps/campaigns/services/campaign_creation.py
from django.core.exceptions import PermissionDenied, ValidationError
from ..models import Campaign
from ..dto import CampaignCreateDTO
from apps.users.models import User

class CampaignCreationService:
    def execute(self, user: User, dto: CampaignCreateDTO) -> Campaign:
        """
        체험단을 생성합니다.

        Args:
            user: 현재 로그인된 광고주
            dto: 체험단 생성 데이터

        Returns:
            생성된 Campaign 객체

        Raises:
            PermissionDenied: 광고주가 아닌 경우
            ValidationError: 비즈니스 규칙 위반 시
        """
        # 1. 권한 확인
        if user.role != 'advertiser':
            raise PermissionDenied("광고주만 체험단을 등록할 수 있습니다.")

        # 2. 비즈니스 규칙 검증
        if dto.recruitment_end_date < dto.recruitment_start_date:
            raise ValidationError("모집 종료일은 시작일과 같거나 이후여야 합니다.")

        if dto.recruitment_count < 1:
            raise ValidationError("모집 인원은 최소 1명 이상이어야 합니다.")

        # 3. 체험단 생성
        campaign = Campaign.objects.create(
            advertiser=user,
            name=dto.name,
            recruitment_start_date=dto.recruitment_start_date,
            recruitment_end_date=dto.recruitment_end_date,
            recruitment_count=dto.recruitment_count,
            benefits=dto.benefits,
            mission=dto.mission,
            status='recruiting'  # 초기 상태는 항상 '모집 중'
        )

        return campaign
```

3. **CampaignCreationService 단위 테스트**
   - 파일: `apps/campaigns/tests/test_services.py`
   - 설명:
     - 정상 체험단 생성 시나리오
     - 인플루언서가 생성 시도 시 PermissionDenied 발생
     - 날짜 오류 시 ValidationError 발생
     - 모집 인원 0명 이하 시 ValidationError 발생
   - 의존성: CampaignCreationService 구현 완료

**Acceptance Tests**:
- [ ] 광고주가 유효한 데이터로 체험단 생성 시 DB에 저장됨
- [ ] 인플루언서가 생성 시도 시 PermissionDenied 예외 발생
- [ ] 모집 종료일이 시작일보다 이전이면 ValidationError 발생
- [ ] 모집 인원이 0명이면 ValidationError 발생
- [ ] 생성된 체험단의 status는 'recruiting'

---

### Phase 3: 프레젠테이션 계층 (Form 및 View 구현)

**목표**: 사용자 입력 검증 및 HTTP 요청/응답 처리

**작업 항목**:

1. **CampaignCreateForm 구현**
   - 파일: `apps/campaigns/forms.py`
   - 설명:
     - ModelForm 상속 또는 일반 Form 클래스 사용
     - 모든 필드 유효성 검증 (required, max_length 등)
     - `clean()` 메서드에서 날짜 논리 검증
   - 의존성: Campaign 모델 정의 완료

```python
# apps/campaigns/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Campaign

class CampaignCreateForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            'name',
            'recruitment_start_date',
            'recruitment_end_date',
            'recruitment_count',
            'benefits',
            'mission'
        ]
        widgets = {
            'recruitment_start_date': forms.DateInput(attrs={'type': 'date'}),
            'recruitment_end_date': forms.DateInput(attrs={'type': 'date'}),
            'benefits': forms.Textarea(attrs={'rows': 4}),
            'mission': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('recruitment_start_date')
        end_date = cleaned_data.get('recruitment_end_date')

        if start_date and end_date and end_date < start_date:
            raise ValidationError("모집 종료일은 시작일과 같거나 이후여야 합니다.")

        return cleaned_data
```

2. **CampaignManagementView (목록 조회) 구현**
   - 파일: `apps/campaigns/views.py`
   - URL: `/manage/campaigns/`
   - 설명:
     - LoginRequiredMixin + AdvertiserRequiredMixin 사용
     - GET 요청 시 현재 광고주의 체험단 목록 조회 (CampaignSelector 활용)
     - 템플릿 렌더링: `campaigns/campaign_management.html`
   - 의존성: CampaignSelector 구현 완료

```python
# apps/campaigns/views.py
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.users.permissions import AdvertiserRequiredMixin
from .selectors.campaign_selectors import CampaignSelector

class CampaignManagementView(LoginRequiredMixin, AdvertiserRequiredMixin, ListView):
    template_name = 'campaigns/campaign_management.html'
    context_object_name = 'campaigns'

    def get_queryset(self):
        """현재 광고주의 체험단 목록 조회"""
        return CampaignSelector.get_campaigns_by_advertiser(
            advertiser_id=self.request.user.id
        )
```

3. **CampaignCreateView 구현**
   - 파일: `apps/campaigns/views.py`
   - URL: `/manage/campaigns/create/`
   - 설명:
     - POST 요청만 처리 (GET은 다이얼로그에서 제공하므로 불필요)
     - CampaignCreateForm으로 유효성 검증
     - 유효한 경우: DTO 생성 → CampaignCreationService 호출 → 성공 메시지 → 리디렉션
     - 유효하지 않은 경우: 폼 오류와 함께 다시 렌더링
   - 의존성: CampaignCreateForm, CampaignCreationService 구현 완료

```python
# apps/campaigns/views.py (계속)
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CampaignCreateForm
from .dto import CampaignCreateDTO
from .services.campaign_creation import CampaignCreationService

class CampaignCreateView(LoginRequiredMixin, AdvertiserRequiredMixin, View):
    def post(self, request):
        form = CampaignCreateForm(request.POST)

        if not form.is_valid():
            # 폼 오류를 세션에 저장하여 다이얼로그에서 표시
            messages.error(request, "입력 정보를 확인해주세요.")
            return redirect('campaigns:manage')

        # DTO 생성
        dto = CampaignCreateDTO(
            name=form.cleaned_data['name'],
            recruitment_start_date=form.cleaned_data['recruitment_start_date'],
            recruitment_end_date=form.cleaned_data['recruitment_end_date'],
            recruitment_count=form.cleaned_data['recruitment_count'],
            benefits=form.cleaned_data['benefits'],
            mission=form.cleaned_data['mission']
        )

        # 서비스 실행
        try:
            service = CampaignCreationService()
            campaign = service.execute(user=request.user, dto=dto)

            messages.success(request, f"'{campaign.name}' 체험단이 성공적으로 등록되었습니다.")
            return redirect('campaigns:manage')

        except Exception as e:
            messages.error(request, f"체험단 등록 중 오류가 발생했습니다: {str(e)}")
            return redirect('campaigns:manage')
```

4. **URL 라우팅 설정**
   - 파일: `apps/campaigns/urls.py`
   - 설명:
     - `/manage/campaigns/` → CampaignManagementView
     - `/manage/campaigns/create/` → CampaignCreateView
     - `/manage/campaigns/<int:pk>/` → (Phase 4에서 구현할 상세 페이지)
   - 의존성: View 구현 완료

```python
# apps/campaigns/urls.py
from django.urls import path
from .views import CampaignManagementView, CampaignCreateView

app_name = 'campaigns'

urlpatterns = [
    path('manage/campaigns/', CampaignManagementView.as_view(), name='manage'),
    path('manage/campaigns/create/', CampaignCreateView.as_view(), name='create'),
]
```

5. **통합 테스트 (View)**
   - 파일: `apps/campaigns/tests/test_views.py`
   - 설명:
     - 광고주 로그인 후 `/manage/campaigns/` 접근 시 200 응답
     - 인플루언서 접근 시 403 Forbidden
     - 비로그인 접근 시 로그인 페이지로 리디렉션
     - POST `/manage/campaigns/create/` 성공 시 DB에 캠페인 생성 및 리디렉션
     - 잘못된 데이터 전송 시 오류 메시지 표시
   - 의존성: View 구현 완료

**Acceptance Tests**:
- [ ] 광고주가 `/manage/campaigns/` 접근 시 자신의 체험단 목록만 표시됨
- [ ] 인플루언서가 접근 시 403 Forbidden 응답
- [ ] 비로그인 사용자가 접근 시 로그인 페이지로 리디렉션
- [ ] 유효한 데이터로 체험단 생성 시 DB에 저장되고 성공 메시지 표시
- [ ] 날짜 오류가 있는 데이터 전송 시 폼 오류 메시지 표시

---

### Phase 4: 템플릿 구현 (UI/UX)

**목표**: Bootstrap을 활용한 직관적이고 반응형 UI 구현

**작업 항목**:

1. **base.html 상속 구조 확인**
   - 파일: `templates/base.html`
   - 설명:
     - Bootstrap 5 CDN이 포함되어 있는지 확인
     - `{% block content %}` 블록이 정의되어 있는지 확인
     - 네비게이션 바에 "체험단 관리" 링크가 광고주에게만 표시되는지 확인
   - 의존성: 공통 모듈 템플릿 구현 완료

2. **campaign_management.html 작성**
   - 파일: `apps/campaigns/templates/campaigns/campaign_management.html`
   - 설명:
     - 페이지 제목: "내 체험단 관리"
     - '신규 체험단 등록' 버튼 (오른쪽 상단)
     - 체험단 카드 그리드 (Bootstrap Grid: `col-md-6 col-lg-4`)
     - 각 카드에 표시할 정보:
       - 체험단명 (링크: 광고주용 상세 페이지)
       - 모집 기간 (YYYY-MM-DD ~ YYYY-MM-DD)
       - 상태 뱃지 (모집 중 / 모집 종료 / 선정 완료)
       - 지원자 수 / 모집 인원
     - 빈 상태 처리: 등록된 체험단이 없을 경우 "등록된 체험단이 없습니다." 메시지
   - 의존성: base.html 확인 완료

```django
{# apps/campaigns/templates/campaigns/campaign_management.html #}
{% extends 'base.html' %}

{% block title %}내 체험단 관리{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>내 체험단 관리</h1>
    <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createCampaignModal">
        <i class="bi bi-plus-circle"></i> 신규 체험단 등록
    </button>
</div>

{% if campaigns %}
<div class="row g-4">
    {% for campaign in campaigns %}
    <div class="col-md-6 col-lg-4">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">
                    <a href="{% url 'campaigns:detail' campaign.id %}" class="text-decoration-none">
                        {{ campaign.name }}
                    </a>
                </h5>

                <p class="text-muted small mb-2">
                    <i class="bi bi-calendar-range"></i>
                    {{ campaign.recruitment_start_date|date:"Y-m-d" }} ~ {{ campaign.recruitment_end_date|date:"Y-m-d" }}
                </p>

                <div class="mb-2">
                    {% if campaign.status == 'recruiting' %}
                        <span class="badge bg-success">모집 중</span>
                    {% elif campaign.status == 'recruitment_ended' %}
                        <span class="badge bg-secondary">모집 종료</span>
                    {% elif campaign.status == 'selection_complete' %}
                        <span class="badge bg-primary">선정 완료</span>
                    {% endif %}
                </div>

                <p class="mb-0">
                    <i class="bi bi-people"></i>
                    <strong>{{ campaign.proposal_count }}</strong> / {{ campaign.recruitment_count }}명 지원
                </p>
            </div>

            <div class="card-footer">
                <a href="{% url 'campaigns:detail' campaign.id %}" class="btn btn-sm btn-outline-primary w-100">
                    상세 보기
                </a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-info text-center" role="alert">
    <i class="bi bi-info-circle"></i> 등록된 체험단이 없습니다.
    <br>
    <button type="button" class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#createCampaignModal">
        첫 번째 체험단 등록하기
    </button>
</div>
{% endif %}

<!-- 신규 체험단 등록 다이얼로그 -->
{% include 'campaigns/_create_campaign_modal.html' %}

{% endblock %}
```

3. **_create_campaign_modal.html 작성**
   - 파일: `apps/campaigns/templates/campaigns/_create_campaign_modal.html`
   - 설명:
     - Bootstrap Modal 컴포넌트
     - CampaignCreateForm 렌더링
     - 각 필드에 Bootstrap 폼 스타일 적용
     - CSRF 토큰 포함
     - 클라이언트 사이드 기본 검증 (HTML5 required 속성)
   - 의존성: campaign_management.html 작성 완료

```django
{# apps/campaigns/templates/campaigns/_create_campaign_modal.html #}
<div class="modal fade" id="createCampaignModal" tabindex="-1" aria-labelledby="createCampaignModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="{% url 'campaigns:create' %}">
                {% csrf_token %}

                <div class="modal-header">
                    <h5 class="modal-title" id="createCampaignModalLabel">신규 체험단 등록</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>

                <div class="modal-body">
                    <div class="mb-3">
                        <label for="id_name" class="form-label">체험단명 <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="id_name" name="name" maxlength="255" required>
                    </div>

                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="id_recruitment_start_date" class="form-label">모집 시작일 <span class="text-danger">*</span></label>
                            <input type="date" class="form-control" id="id_recruitment_start_date" name="recruitment_start_date" required>
                        </div>
                        <div class="col-md-6">
                            <label for="id_recruitment_end_date" class="form-label">모집 종료일 <span class="text-danger">*</span></label>
                            <input type="date" class="form-control" id="id_recruitment_end_date" name="recruitment_end_date" required>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="id_recruitment_count" class="form-label">모집 인원 <span class="text-danger">*</span></label>
                        <input type="number" class="form-control" id="id_recruitment_count" name="recruitment_count" min="1" required>
                    </div>

                    <div class="mb-3">
                        <label for="id_benefits" class="form-label">제공 혜택 <span class="text-danger">*</span></label>
                        <textarea class="form-control" id="id_benefits" name="benefits" rows="4" required></textarea>
                        <small class="form-text text-muted">예: 무료 식사 제공, 리뷰 작성비 지급 등</small>
                    </div>

                    <div class="mb-3">
                        <label for="id_mission" class="form-label">미션 <span class="text-danger">*</span></label>
                        <textarea class="form-control" id="id_mission" name="mission" rows="4" required></textarea>
                        <small class="form-text text-muted">예: 인스타그램 스토리 2개 이상 업로드, 블로그 리뷰 작성 등</small>
                    </div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                    <button type="submit" class="btn btn-primary">등록하기</button>
                </div>
            </form>
        </div>
    </div>
</div>
```

4. **E2E 테스트 시나리오 작성**
   - 파일: `apps/campaigns/tests/test_e2e.py` (또는 수동 테스트 체크리스트)
   - 설명:
     - 광고주 로그인 → 체험단 관리 페이지 접속 → 신규 등록 → 목록에서 확인
     - 오류 시나리오: 잘못된 날짜 입력 후 제출 → 오류 메시지 확인
   - 의존성: 템플릿 구현 완료

**Acceptance Tests**:
- [ ] 페이지에 "내 체험단 관리" 제목이 표시됨
- [ ] "신규 체험단 등록" 버튼이 오른쪽 상단에 표시됨
- [ ] 버튼 클릭 시 다이얼로그 모달이 올바르게 열림
- [ ] 체험단 목록이 카드 형태로 그리드 레이아웃으로 표시됨
- [ ] 각 카드에 체험단명, 기간, 상태 뱃지, 지원자 수가 표시됨
- [ ] 체험단이 없을 경우 빈 상태 메시지가 표시됨
- [ ] 다이얼로그 폼에서 유효한 데이터 입력 후 제출 시 체험단이 생성되고 목록에 즉시 반영됨
- [ ] 모바일, 태블릿, 데스크톱에서 반응형으로 올바르게 표시됨 (Bootstrap Grid)

---

### Phase 5: 권한 관리 및 보안

**목표**: 광고주 전용 기능 보호 및 보안 강화

**작업 항목**:

1. **AdvertiserRequiredMixin 구현**
   - 파일: `apps/users/permissions.py`
   - 설명:
     - UserPassesTestMixin 상속
     - `test_func()`에서 `self.request.user.is_authenticated and self.request.user.role == 'advertiser'` 검증
     - 실패 시 403 Forbidden 또는 로그인 페이지 리디렉션
   - 의존성: User 모델의 role 필드 구현 완료

```python
# apps/users/permissions.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class AdvertiserRequiredMixin(UserPassesTestMixin):
    """광고주 전용 View를 위한 Mixin"""

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.role == 'advertiser'
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            # 비로그인 → 로그인 페이지로 리디렉션
            return super().handle_no_permission()
        else:
            # 로그인은 했지만 광고주가 아님 → 403
            raise PermissionDenied("광고주만 접근할 수 있는 페이지입니다.")
```

2. **CSRF 보호 확인**
   - 파일: `config/settings/base.py`
   - 설명:
     - Django의 기본 CSRF 미들웨어가 활성화되어 있는지 확인
     - 모든 POST 요청에 `{% csrf_token %}` 포함 확인
   - 의존성: 프로젝트 초기 설정 완료

3. **권한 관리 단위 테스트**
   - 파일: `apps/users/tests/test_permissions.py`
   - 설명:
     - 광고주 사용자는 Mixin 통과
     - 인플루언서 사용자는 403 Forbidden
     - 비로그인 사용자는 로그인 페이지로 리디렉션
   - 의존성: AdvertiserRequiredMixin 구현 완료

**Acceptance Tests**:
- [ ] 광고주 로그인 후 체험단 관리 페이지 접근 시 200 응답
- [ ] 인플루언서 로그인 후 체험단 관리 페이지 접근 시 403 Forbidden
- [ ] 비로그인 상태에서 체험단 관리 페이지 접근 시 로그인 페이지로 리디렉션
- [ ] POST 요청 시 CSRF 토큰 누락 시 403 Forbidden

---

## 5. 데이터 흐름 다이어그램

### 5.1 체험단 목록 조회 플로우

```
[광고주 사용자]
    ↓
[GET /manage/campaigns/]
    ↓
[CampaignManagementView]
    ↓ (권한 확인: LoginRequiredMixin + AdvertiserRequiredMixin)
    ↓
[CampaignSelector.get_campaigns_by_advertiser(user.id)]
    ↓
[Database: SELECT * FROM campaigns WHERE advertiser_id = ? (+ COUNT proposals)]
    ↓
[campaigns QuerySet 반환]
    ↓
[Template: campaign_management.html 렌더링]
    ↓
[HTML 응답 → 브라우저]
```

### 5.2 체험단 생성 플로우

```
[광고주 사용자]
    ↓ (다이얼로그 폼 작성 후 제출)
[POST /manage/campaigns/create/]
    ↓
[CampaignCreateView]
    ↓ (권한 확인)
    ↓
[CampaignCreateForm 유효성 검증]
    ↓ (is_valid() == True)
    ↓
[CampaignCreateDTO 생성]
    ↓
[CampaignCreationService.execute(user, dto)]
    ↓ (권한 확인, 비즈니스 규칙 검증)
    ↓
[Database: INSERT INTO campaigns (...)]
    ↓
[Campaign 객체 반환]
    ↓
[messages.success("체험단 등록 성공")]
    ↓
[Redirect → /manage/campaigns/]
    ↓
[목록 페이지에서 새로 생성된 체험단 확인]
```

---

## 6. 에러 처리

### 6.1 백엔드 에러

| 에러 코드 | HTTP 상태 | 발생 조건 | 사용자 메시지 | 처리 방법 |
|----------|----------|----------|--------------|----------|
| PERMISSION_DENIED | 403 | 광고주가 아닌 사용자가 접근 | "광고주만 접근할 수 있는 페이지입니다." | 403 페이지 렌더링 또는 메시지 표시 |
| VALIDATION_ERROR | 400 | 폼 검증 실패 (날짜 오류, 필수값 누락 등) | "입력 정보를 확인해주세요." | 폼 오류와 함께 다시 표시 |
| DATE_RANGE_ERROR | 400 | 모집 종료일 < 모집 시작일 | "모집 종료일은 시작일과 같거나 이후여야 합니다." | Form clean() 메서드에서 검증 |
| INVALID_COUNT | 400 | 모집 인원 < 1 | "모집 인원은 최소 1명 이상이어야 합니다." | Service 또는 Form에서 검증 |
| DATABASE_ERROR | 500 | DB 저장 실패 | "체험단 등록 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요." | 로깅 후 일반 오류 메시지 표시 |

### 6.2 프론트엔드 에러 핸들링

- **Django Messages Framework 사용**:
  - `messages.success()`: 성공 메시지 (녹색)
  - `messages.error()`: 오류 메시지 (빨간색)
  - `messages.warning()`: 경고 메시지 (노란색)

- **폼 오류 표시**:
  - `{{ form.field_name.errors }}` → 각 필드 아래 오류 메시지 표시
  - `{{ form.non_field_errors }}` → 전체 폼 오류 (날짜 범위 오류 등)

- **클라이언트 사이드 검증**:
  - HTML5 `required` 속성으로 필수 필드 검증
  - `type="date"` 속성으로 날짜 형식 자동 검증
  - `min="1"` 속성으로 모집 인원 최소값 검증

---

## 7. 테스트 계획

### 7.1 단위 테스트

**파일**: `apps/campaigns/tests/test_selectors.py`

| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-SEL-001 | 광고주별 필터링 | advertiser_id=1 | 광고주 1의 캠페인만 반환 |
| UT-SEL-002 | proposal_count 어노테이션 | 지원자 3명인 캠페인 | proposal_count=3 |
| UT-SEL-003 | 최신순 정렬 | 여러 캠페인 | created_at 내림차순 정렬 |
| UT-SEL-004 | N+1 쿼리 방지 | 10개 캠페인 조회 | 쿼리 2개 이하 (1개는 캠페인, 1개는 COUNT) |

**파일**: `apps/campaigns/tests/test_services.py`

| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-SVC-001 | 정상 체험단 생성 | 유효한 DTO + 광고주 | Campaign 객체 반환, DB 저장 확인 |
| UT-SVC-002 | 권한 없음 | 유효한 DTO + 인플루언서 | PermissionDenied 예외 |
| UT-SVC-003 | 날짜 오류 | end_date < start_date | ValidationError 예외 |
| UT-SVC-004 | 모집 인원 0 | recruitment_count=0 | ValidationError 예외 |
| UT-SVC-005 | 초기 상태 확인 | 정상 생성 | campaign.status == 'recruiting' |

**파일**: `apps/campaigns/tests/test_forms.py`

| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-FORM-001 | 유효한 데이터 | 모든 필드 올바름 | is_valid() == True |
| UT-FORM-002 | 필수 필드 누락 | name="" | is_valid() == False, 오류 메시지 존재 |
| UT-FORM-003 | 날짜 논리 오류 | end < start | is_valid() == False, clean() 오류 |

### 7.2 통합 테스트

**파일**: `apps/campaigns/tests/test_views.py`

| ID | 테스트 내용 | 사전 조건 | 실행 | 기대 결과 |
|----|-----------|----------|------|----------|
| IT-VIEW-001 | 광고주 목록 조회 | 광고주 로그인 | GET /manage/campaigns/ | 200 응답, 자신의 캠페인 목록 표시 |
| IT-VIEW-002 | 인플루언서 접근 차단 | 인플루언서 로그인 | GET /manage/campaigns/ | 403 Forbidden |
| IT-VIEW-003 | 비로그인 리디렉션 | 로그아웃 상태 | GET /manage/campaigns/ | 302 Redirect to login |
| IT-VIEW-004 | 체험단 생성 성공 | 광고주 로그인, 유효한 데이터 | POST /manage/campaigns/create/ | 302 Redirect, DB에 캠페인 생성, 성공 메시지 |
| IT-VIEW-005 | 체험단 생성 실패 | 광고주 로그인, 잘못된 날짜 | POST /manage/campaigns/create/ | 오류 메시지 표시 |

### 7.3 E2E 테스트 (수동 테스트 체크리스트)

- [ ] **시나리오 1: 체험단 목록 조회**
  1. 광고주로 로그인
  2. 네비게이션 바에서 "체험단 관리" 클릭
  3. `/manage/campaigns/` 페이지 로드 확인
  4. 기존 체험단 목록이 카드 형태로 표시되는지 확인
  5. 각 카드에 체험단명, 기간, 상태, 지원자 수가 올바르게 표시되는지 확인

- [ ] **시나리오 2: 신규 체험단 등록 (성공)**
  1. "신규 체험단 등록" 버튼 클릭
  2. 다이얼로그 모달이 열리는지 확인
  3. 모든 필드에 유효한 데이터 입력
  4. "등록하기" 버튼 클릭
  5. 다이얼로그가 닫히고 목록 페이지로 돌아오는지 확인
  6. 방금 등록한 체험단이 목록 최상단에 표시되는지 확인
  7. 성공 메시지 토스트가 표시되는지 확인

- [ ] **시나리오 3: 신규 체험단 등록 (날짜 오류)**
  1. "신규 체험단 등록" 버튼 클릭
  2. 모집 종료일을 시작일보다 이전으로 설정
  3. "등록하기" 버튼 클릭
  4. 오류 메시지가 표시되는지 확인
  5. 다이얼로그가 열린 상태로 유지되는지 확인

- [ ] **시나리오 4: 권한 검증**
  1. 인플루언서 계정으로 로그인
  2. `/manage/campaigns/` URL 직접 입력
  3. 403 Forbidden 페이지 또는 권한 없음 메시지 확인

---

## 8. 성능 고려사항

### 8.1 최적화 목표
- 페이지 로드 시간: 2초 이내
- 체험단 생성 처리 시간: 1초 이내
- N+1 쿼리 제거: 체험단 목록 조회 시 쿼리 수 2개 이하

### 8.2 쿼리 최적화

**CampaignSelector에서 적용**:
- `select_related('advertiser')`: 광고주 정보를 함께 조회하여 N+1 쿼리 방지
- `annotate(proposal_count=Count('proposals'))`: 각 캠페인의 지원자 수를 단일 쿼리로 조회

**확인 방법**:
```python
# 테스트 코드에서 쿼리 수 확인
from django.test.utils import override_settings
from django.db import connection

with self.assertNumQueries(2):  # 2개 이하의 쿼리만 허용
    campaigns = CampaignSelector.get_campaigns_by_advertiser(advertiser_id=1)
    list(campaigns)  # QuerySet을 평가하여 실제 쿼리 실행
```

### 8.3 인덱스 전략

`database.md`에 이미 정의된 인덱스 활용:
```sql
CREATE INDEX idx_campaigns_advertiser_id ON campaigns(advertiser_id);
```

이 인덱스는 `WHERE advertiser_id = ?` 조건의 조회 성능을 크게 향상시킵니다.

### 8.4 캐싱 전략 (향후 고려)

MVP 단계에서는 캐싱 없이 진행하지만, 향후 고려사항:
- Django 템플릿 프래그먼트 캐싱: `{% cache 300 campaign_list user.id %}`
- QuerySet 캐싱: 동일 요청 내에서 재사용

---

## 9. 보안 고려사항

### 9.1 인증/인가
- **LoginRequiredMixin**: 모든 체험단 관리 View에 적용하여 비로그인 접근 차단
- **AdvertiserRequiredMixin**: 광고주 역할 검증, 인플루언서 접근 차단
- **소유권 검증** (향후 상세 페이지에서): 광고주가 자신의 체험단만 관리하도록 확인

### 9.2 데이터 보호
- **CSRF 보호**: Django의 기본 CSRF 미들웨어 활성화, 모든 POST 요청에 토큰 포함
- **SQL Injection 방지**: Django ORM 사용으로 자동 방어
- **XSS 방지**: Django 템플릿의 자동 이스케이프 활용

### 9.3 입력 검증
- **서버 사이드 검증**: Form 클래스에서 모든 필드 유효성 검증
- **비즈니스 규칙 검증**: Service 계층에서 추가 검증 (권한, 날짜 논리 등)
- **클라이언트 사이드 검증**: HTML5 속성으로 기본 UX 향상 (단, 서버 검증이 주된 방어선)

---

## 10. 배포 계획

### 10.1 환경 변수

`config/settings/production.py`에서 확인:
```python
# Railway Volume 경로 설정 (이미 common-modules.md에서 정의됨)
VOLUME_MOUNT_PATH = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', BASE_DIR)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(VOLUME_MOUNT_PATH, 'db.sqlite3'),
    }
}
```

추가 환경 변수 없음 (MVP 단계).

### 10.2 배포 순서

1. **로컬 개발 환경 테스트**
   - `python manage.py runserver`로 모든 기능 동작 확인
   - 단위 테스트 및 통합 테스트 실행: `pytest apps/campaigns/tests/`

2. **Migration 실행**
   - `python manage.py makemigrations`
   - `python manage.py migrate`

3. **정적 파일 수집**
   - `python manage.py collectstatic`

4. **Railway 배포**
   - GitHub에 푸시: `git push origin main`
   - Railway 자동 배포 확인
   - Railway 로그에서 오류 확인

5. **배포 후 검증**
   - 프로덕션 URL에 접속하여 체험단 관리 페이지 동작 확인
   - 신규 체험단 등록 테스트

### 10.3 롤백 계획

- Git 이전 커밋으로 롤백: `git revert <commit-hash>`
- Railway에서 이전 배포 버전으로 롤백 (대시보드에서 클릭)
- 데이터베이스 마이그레이션 롤백: `python manage.py migrate campaigns <previous_migration_name>`

---

## 11. 모니터링 및 로깅

### 11.1 로그 항목

**Django 기본 로깅 설정**:
```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps.campaigns': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**주요 로그 항목**:
- 체험단 생성 성공: `logger.info(f"Campaign created: {campaign.id} by user {user.id}")`
- 체험단 생성 실패: `logger.error(f"Campaign creation failed: {str(e)}")`
- 권한 거부: `logger.warning(f"Permission denied for user {user.id} on campaign management")`

### 11.2 메트릭 (향후 고려)

MVP 단계에서는 Railway의 기본 메트릭만 활용:
- CPU 사용률
- 메모리 사용률
- 요청 응답 시간

향후 추가 메트릭:
- 일별 체험단 생성 수
- 광고주당 평균 체험단 수
- 페이지 로드 시간

---

## 12. 문서화

### 12.1 API 문서
MVP 단계에서는 별도의 API 문서 없음 (Django Template 기반).
향후 DRF 도입 시 OpenAPI/Swagger 자동 생성 예정.

### 12.2 코드 문서화

**Docstring 작성 규칙**:
- 모든 Service 클래스의 `execute()` 메서드에 docstring 작성
- Selector 클래스의 public 메서드에 docstring 작성
- 복잡한 비즈니스 로직에 주석 추가

**예시**:
```python
def execute(self, user: User, dto: CampaignCreateDTO) -> Campaign:
    """
    체험단을 생성합니다.

    Args:
        user: 현재 로그인된 광고주
        dto: 체험단 생성 데이터

    Returns:
        생성된 Campaign 객체

    Raises:
        PermissionDenied: 광고주가 아닌 경우
        ValidationError: 비즈니스 규칙 위반 시
    """
```

---

## 13. 체크리스트

### 13.1 구현 전
- [ ] PRD 및 유스케이스 문서 검토 완료
- [ ] `campaigns` 모델 정의 완료 (database.md 기준)
- [ ] 공통 모듈 (BaseService, BaseDTO) 구현 완료
- [ ] User 모델 및 role 필드 구현 완료

### 13.2 구현 중
- [ ] **Phase 1**: CampaignSelector 구현 및 테스트 통과
- [ ] **Phase 2**: CampaignCreateDTO 및 CampaignCreationService 구현 및 테스트 통과
- [ ] **Phase 3**: CampaignCreateForm, Views, URL 라우팅 구현 및 통합 테스트 통과
- [ ] **Phase 4**: 템플릿 (campaign_management.html, _create_campaign_modal.html) 구현
- [ ] **Phase 5**: AdvertiserRequiredMixin 구현 및 권한 테스트 통과
- [ ] 모든 단위 테스트 커버리지 80% 이상
- [ ] 코드 리뷰 완료 (셀프 리뷰 또는 팀 리뷰)

### 13.3 구현 후
- [ ] 로컬 환경에서 E2E 테스트 시나리오 수동 검증
- [ ] N+1 쿼리 최적화 확인 (django-debug-toolbar 또는 assertNumQueries)
- [ ] Migration 파일 생성 및 실행
- [ ] 정적 파일 수집 (`collectstatic`)
- [ ] Railway 배포 및 프로덕션 환경 검증
- [ ] 보안 검토 (권한, CSRF, XSS 방어 확인)
- [ ] 문서 작성 완료 (Docstring, 주석)

---

## 14. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude | 초기 작성: PRD, 유스케이스, common-modules.md 기반 상세 계획 수립 |

---

## 부록

### A. 파일 구조 요약

```
apps/campaigns/
├── models.py                        # Campaign 모델 (database.md 기준)
├── dto.py                           # CampaignCreateDTO
├── forms.py                         # CampaignCreateForm
├── urls.py                          # URL 라우팅
├── views.py                         # CampaignManagementView, CampaignCreateView
├── selectors/
│   ├── __init__.py
│   └── campaign_selectors.py        # CampaignSelector
├── services/
│   ├── __init__.py
│   └── campaign_creation.py         # CampaignCreationService
├── templates/campaigns/
│   ├── campaign_management.html     # 메인 페이지
│   └── _create_campaign_modal.html  # 등록 다이얼로그
└── tests/
    ├── test_selectors.py            # Selector 단위 테스트
    ├── test_services.py             # Service 단위 테스트
    ├── test_forms.py                # Form 단위 테스트
    ├── test_views.py                # View 통합 테스트
    └── test_e2e.py                  # E2E 테스트 (선택)
```

### B. 의사결정 기록

**결정 1: 다이얼로그 폼 방식 채택**
- **이유**: PRD에서 "다이얼로그 폼"을 명시적으로 요구. 페이지 전환 없이 빠른 등록 UX 제공.
- **대안**: 별도의 체험단 등록 페이지 (/manage/campaigns/new/)
- **선택**: 다이얼로그 방식 (Bootstrap Modal)

**결정 2: 카드 그리드 레이아웃**
- **이유**: 각 체험단의 핵심 정보를 한눈에 파악하기 쉽고, 반응형 디자인에 적합.
- **대안**: 테이블 형태 (Table View)
- **선택**: 카드 그리드 (Bootstrap Grid: col-md-6 col-lg-4)

**결정 3: CampaignCreationService 활용**
- **이유**: common-modules.md에서 이미 설계된 Service 패턴을 따라 비즈니스 로직을 View에서 분리.
- **대안**: View에서 직접 Model.objects.create() 호출
- **선택**: Service 계층 사용 (유지보수성, 테스트 용이성 향상)

### C. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| N+1 쿼리 발생 | 중 | 높음 | select_related, annotate 사용으로 사전 방지. 테스트 코드에서 assertNumQueries로 검증. |
| 권한 우회 접근 | 중 | 높음 | View 레벨에서 Mixin으로 권한 검증. URL 직접 접근 시에도 차단. 단위 테스트로 검증. |
| 폼 검증 누락 | 낮 | 중 | Form 클래스와 Service 계층 이중 검증. 단위 테스트로 모든 검증 로직 커버. |
| 날짜 입력 UX 불편 | 중 | 낮 | HTML5 date input 사용으로 브라우저 기본 날짜 선택기 제공. 모바일 환경에서도 사용 편리. |
| 다이얼로그 폼 오류 시 데이터 손실 | 중 | 중 | 폼 검증 실패 시 입력 데이터를 세션에 저장하거나, Ajax로 처리하여 페이지 리로드 없이 오류 표시 (향후 개선). MVP는 단순 리디렉션. |

### D. 향후 개선 사항 (Post-MVP)

1. **Ajax 기반 폼 제출**: 페이지 리로드 없이 다이얼로그 내에서 성공/실패 피드백
2. **체험단 수정/삭제 기능**: 광고주가 등록한 체험단 정보 수정 및 삭제
3. **검색 및 필터링**: 체험단명, 상태, 날짜 범위로 필터링
4. **통계 대시보드**: 총 체험단 수, 평균 지원자 수, 선정률 등 시각화
5. **이미지 업로드**: 체험단 대표 이미지 등록
6. **임시저장**: 체험단 등록 도중 저장하여 나중에 이어서 작성

---

## E. 참고 코드 예시

### Selector 테스트 코드 예시
```python
# apps/campaigns/tests/test_selectors.py
import pytest
from django.db.models import Count
from apps.campaigns.selectors.campaign_selectors import CampaignSelector
from apps.campaigns.models import Campaign
from apps.users.models import User

@pytest.mark.django_db
class TestCampaignSelector:
    def test_get_campaigns_by_advertiser_returns_only_own_campaigns(self):
        # Given
        advertiser1 = User.objects.create(email='ad1@test.com', role='advertiser')
        advertiser2 = User.objects.create(email='ad2@test.com', role='advertiser')

        campaign1 = Campaign.objects.create(advertiser=advertiser1, name='Campaign 1', ...)
        campaign2 = Campaign.objects.create(advertiser=advertiser2, name='Campaign 2', ...)

        # When
        campaigns = CampaignSelector.get_campaigns_by_advertiser(advertiser1.id)

        # Then
        assert campaigns.count() == 1
        assert campaigns.first().id == campaign1.id

    def test_get_campaigns_includes_proposal_count(self):
        # Given
        advertiser = User.objects.create(email='ad@test.com', role='advertiser')
        campaign = Campaign.objects.create(advertiser=advertiser, name='Test', ...)

        # 지원자 3명 생성 (Proposal 모델 사용)
        # ... (Proposal 생성 로직)

        # When
        campaigns = CampaignSelector.get_campaigns_by_advertiser(advertiser.id)

        # Then
        assert campaigns.first().proposal_count == 3
```

### Service 테스트 코드 예시
```python
# apps/campaigns/tests/test_services.py
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from datetime import date
from apps.campaigns.services.campaign_creation import CampaignCreationService
from apps.campaigns.dto import CampaignCreateDTO
from apps.users.models import User

@pytest.mark.django_db
class TestCampaignCreationService:
    def test_execute_creates_campaign_successfully(self):
        # Given
        advertiser = User.objects.create(email='ad@test.com', role='advertiser')
        dto = CampaignCreateDTO(
            name='Test Campaign',
            recruitment_start_date=date(2025, 11, 20),
            recruitment_end_date=date(2025, 11, 30),
            recruitment_count=5,
            benefits='Free meal',
            mission='Write review'
        )
        service = CampaignCreationService()

        # When
        campaign = service.execute(user=advertiser, dto=dto)

        # Then
        assert campaign.id is not None
        assert campaign.name == 'Test Campaign'
        assert campaign.status == 'recruiting'
        assert campaign.advertiser == advertiser

    def test_execute_raises_permission_denied_for_influencer(self):
        # Given
        influencer = User.objects.create(email='inf@test.com', role='influencer')
        dto = CampaignCreateDTO(...)
        service = CampaignCreationService()

        # When / Then
        with pytest.raises(PermissionDenied):
            service.execute(user=influencer, dto=dto)
```

---

**구현 완료 후 이 문서를 바탕으로 개발을 진행하세요!**
