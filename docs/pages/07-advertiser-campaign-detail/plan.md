# 구현 계획: 광고주용 체험단 상세 페이지

## 프로젝트 ID: PLAN-007

### 제목
광고주용 체험단 상세 및 지원자 관리 페이지 구현

---

## 1. 개요

### 1.1 목표
광고주가 자신이 등록한 체험단 캠페인의 상세 정보를 확인하고, 지원자 목록을 관리하며, 모집 마감 및 체험단 선정을 수행할 수 있는 관리 페이지를 구현합니다.

### 1.2 참고 문서
- **PRD**: `/docs/prd.md` - 7. 광고주용 체험단 상세 섹션
- **유스케이스**:
  - `/docs/usecases/06-close-recruitment/spec.md` - 모집 마감 처리
  - `/docs/usecases/07-select-influencers/spec.md` - 체험단 선정
- **데이터베이스 스키마**: `/docs/database.md`
- **유저플로우**: `/docs/userflow.md` - 2.3, 2.4 섹션
- **공통 모듈**: `/docs/common-modules.md`
- **코드베이스 구조**: `/docs/structure.md`

### 1.3 범위

**포함 사항**:
1. 광고주 전용 체험단 상세 정보 표시
2. 지원자 목록 조회 및 표시 (Table 형태)
3. 캠페인 상태별 액션 버튼 제공
   - 모집 중: '모집 종료' 버튼
   - 모집 종료: '체험단 선정' 버튼
4. 모집 마감 처리 기능
5. 체험단 선정 기능 (선정 다이얼로그 포함)
6. 권한 검증 (소유자만 접근 가능)
7. 상태별 UI 분기 처리

**제외 사항**:
- 실시간 지원자 알림 (페이지 새로고침으로 갱신)
- 자동 모집 마감 기능
- 지원자와의 메시징 기능
- 상세 필터링/검색 기능
- 선정 취소 기능 (선정 완료 후 상태 불가역)

---

## 2. 기술 스택

### 2.1 백엔드
- **프레임워크**: Django 5.1.3
- **데이터베이스**: SQLite (개발 및 배포)
- **ORM**: Django ORM
- **인증**: Django Session-based Authentication
- **템플릿 엔진**: Django Template Engine
- **테스트**: pytest-django

### 2.2 프론트엔드
- **템플릿**: Django Template (Server-Side Rendering)
- **UI 프레임워크**: Bootstrap 5.3
- **JavaScript**: Vanilla JS (모달 제어, 폼 검증)
- **스타일링**: Bootstrap CSS + 커스텀 CSS

### 2.3 외부 서비스
- 없음 (MVP 단계)

---

## 3. 데이터베이스 요구사항

### 3.1 사용할 테이블
본 페이지는 기존 스키마를 사용하며, 새로운 테이블 생성 없음.

**campaigns 테이블** (조회 및 수정):
- 상태 필드: `status` ('recruiting', 'recruitment_ended', 'selection_complete')
- 소유자 확인: `advertiser_id`

**proposals 테이블** (조회 및 수정):
- 지원자 목록 조회
- 상태 업데이트: `status` ('submitted', 'selected', 'rejected')

**users 테이블** (조회):
- 지원자 정보 표시용 (인플루언서 이름, 연락처)

**influencer_profiles 테이블** (조회):
- 지원자 SNS 정보 표시용 (sns_link)

### 3.2 필요한 쿼리 최적화

**N+1 쿼리 방지**:
```python
# 지원자 목록 조회 시
proposals = Proposal.objects.filter(
    campaign_id=campaign_id
).select_related(
    'influencer',  # User 정보
    'influencer__influencer_profile'  # Influencer Profile 정보
).order_by('-created_at')
```

**트랜잭션 처리** (체험단 선정 시):
```python
from django.db import transaction

@transaction.atomic
def select_influencers(campaign_id, selected_proposal_ids):
    # 선정, 반려, 캠페인 상태 변경을 원자적으로 실행
    pass
```

---

## 4. 구현 단계 (Implementation Steps)

### Phase 1: 모델 및 DTO 정의

**목표**: 데이터 계약 및 비즈니스 로직 인터페이스 정의

**작업 항목**:

1. **DTO 정의**
   - 파일: `apps/campaigns/dto.py`
   - 설명: 모집 마감 및 선정을 위한 DTO 추가
   - 의존성: 없음

```python
# apps/campaigns/dto.py

from dataclasses import dataclass
from typing import List
from datetime import date

# 기존 DTO들...

@dataclass(frozen=True)
class CampaignCloseDTO:
    """모집 마감 입력 데이터"""
    campaign_id: int

@dataclass(frozen=True)
class InfluencerSelectionDTO:
    """체험단 선정 입력 데이터"""
    campaign_id: int
    selected_proposal_ids: List[int]

@dataclass(frozen=True)
class InfluencerSelectionResultDTO:
    """체험단 선정 결과 데이터"""
    campaign_id: int
    selected_count: int
    rejected_count: int
    campaign_status: str

@dataclass(frozen=True)
class ProposalDetailDTO:
    """지원자 상세 정보 (페이지 표시용)"""
    proposal_id: int
    influencer_name: str
    influencer_email: str
    influencer_contact: str
    sns_link: str
    cover_letter: str
    desired_visit_date: date
    status: str
    created_at: str
```

**Acceptance Tests**:
- [ ] DTO 인스턴스 생성 성공
- [ ] DTO 불변성 확인 (frozen=True)
- [ ] 잘못된 타입 전달 시 에러 발생

---

### Phase 2: Service Layer 구현

**목표**: 비즈니스 로직을 Service 계층에 캡슐화

**작업 항목**:

1. **모집 마감 서비스**
   - 파일: `apps/campaigns/services/campaign_management.py`
   - 설명: 모집 종료 로직 구현
   - 의존성: Phase 1 완료

```python
# apps/campaigns/services/campaign_management.py

from django.db import transaction
from django.utils import timezone
from ..models import Campaign
from ..dto import CampaignCloseDTO
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException
)

class CampaignCloseService:
    """캠페인 모집 마감 서비스"""

    def execute(self, user, dto: CampaignCloseDTO) -> Campaign:
        """
        모집 마감 처리

        Args:
            user: 현재 로그인된 광고주
            dto: 모집 마감 입력 데이터

        Returns:
            업데이트된 Campaign 객체

        Raises:
            PermissionDeniedException: 권한이 없는 경우
            InvalidStateException: 캠페인 상태가 'recruiting'이 아닌 경우
        """
        # 1. 캠페인 조회
        try:
            campaign = Campaign.objects.select_for_update().get(
                id=dto.campaign_id
            )
        except Campaign.DoesNotExist:
            raise InvalidStateException("존재하지 않는 캠페인입니다.")

        # 2. 권한 검증
        if campaign.advertiser_id != user.id:
            raise PermissionDeniedException(
                "이 체험단에 접근할 권한이 없습니다."
            )

        # 3. 상태 검증
        if campaign.status != 'recruiting':
            raise InvalidStateException(
                "이미 모집이 종료되었거나 선정이 완료된 체험단입니다."
            )

        # 4. 상태 업데이트
        campaign.status = 'recruitment_ended'
        campaign.updated_at = timezone.now()
        campaign.save(update_fields=['status', 'updated_at'])

        return campaign
```

2. **체험단 선정 서비스**
   - 파일: `apps/campaigns/services/influencer_selection.py`
   - 설명: 인플루언서 선정 로직 구현
   - 의존성: Phase 1 완료

```python
# apps/campaigns/services/influencer_selection.py

from django.db import transaction
from django.utils import timezone
from ..models import Campaign, Proposal
from ..dto import InfluencerSelectionDTO, InfluencerSelectionResultDTO
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    ServiceException
)

class InfluencerSelectionService:
    """인플루언서 선정 서비스"""

    @transaction.atomic
    def execute(
        self,
        user,
        dto: InfluencerSelectionDTO
    ) -> InfluencerSelectionResultDTO:
        """
        체험단 선정 처리

        Args:
            user: 현재 로그인된 광고주
            dto: 선정 입력 데이터

        Returns:
            InfluencerSelectionResultDTO: 선정 결과

        Raises:
            PermissionDeniedException: 권한이 없는 경우
            InvalidStateException: 캠페인 상태가 적절하지 않은 경우
            ServiceException: 선정 인원 관련 검증 실패
        """
        # 1. 캠페인 조회 및 락
        try:
            campaign = Campaign.objects.select_for_update().get(
                id=dto.campaign_id
            )
        except Campaign.DoesNotExist:
            raise InvalidStateException("존재하지 않는 캠페인입니다.")

        # 2. 권한 검증
        if campaign.advertiser_id != user.id:
            raise PermissionDeniedException(
                "이 체험단에 접근할 권한이 없습니다."
            )

        # 3. 상태 검증
        if campaign.status != 'recruitment_ended':
            raise InvalidStateException(
                "모집이 종료된 캠페인만 선정할 수 있습니다."
            )

        # 4. 선정 인원 검증
        selected_count = len(dto.selected_proposal_ids)

        if selected_count == 0:
            raise ServiceException(
                "최소 1명 이상의 지원자를 선택해야 합니다."
            )

        if selected_count > campaign.recruitment_count:
            raise ServiceException(
                f"모집 인원({campaign.recruitment_count}명)을 "
                f"초과하여 선택할 수 없습니다. "
                f"현재 {selected_count}명이 선택되었습니다."
            )

        # 5. 선정된 지원자 확인 (해당 캠페인의 지원자인지 검증)
        valid_proposals = Proposal.objects.filter(
            id__in=dto.selected_proposal_ids,
            campaign=campaign,
            status='submitted'
        ).count()

        if valid_proposals != selected_count:
            raise ServiceException(
                "선택한 지원자 중 유효하지 않은 항목이 있습니다."
            )

        # 6. 선정 처리
        selected = Proposal.objects.filter(
            id__in=dto.selected_proposal_ids,
            campaign=campaign
        ).update(
            status='selected',
            updated_at=timezone.now()
        )

        # 7. 반려 처리
        rejected = Proposal.objects.filter(
            campaign=campaign,
            status='submitted'
        ).exclude(
            id__in=dto.selected_proposal_ids
        ).update(
            status='rejected',
            updated_at=timezone.now()
        )

        # 8. 캠페인 상태 업데이트
        campaign.status = 'selection_complete'
        campaign.updated_at = timezone.now()
        campaign.save(update_fields=['status', 'updated_at'])

        # 9. 결과 DTO 반환
        return InfluencerSelectionResultDTO(
            campaign_id=campaign.id,
            selected_count=selected,
            rejected_count=rejected,
            campaign_status=campaign.status
        )
```

**Acceptance Tests**:
- [ ] 모집 마감 서비스 정상 동작
- [ ] 권한 없는 사용자 접근 시 PermissionDeniedException 발생
- [ ] 잘못된 상태의 캠페인 처리 시 InvalidStateException 발생
- [ ] 체험단 선정 서비스 정상 동작
- [ ] 모집 인원 초과 선택 시 ServiceException 발생
- [ ] 선택 인원 없을 시 ServiceException 발생
- [ ] 트랜잭션 롤백 테스트 (DB 오류 발생 시)

---

### Phase 3: Selector Layer 구현

**목표**: 복잡한 조회 로직을 Selector로 분리

**작업 항목**:

1. **캠페인 및 지원자 조회 Selector**
   - 파일: `apps/campaigns/selectors/campaign_selectors.py`
   - 설명: 광고주용 상세 조회 로직
   - 의존성: Phase 1 완료

```python
# apps/campaigns/selectors/campaign_selectors.py

from typing import List, Optional
from django.db.models import Count, Q
from ..models import Campaign, Proposal
from ..dto import ProposalDetailDTO

class CampaignDetailSelector:
    """광고주용 캠페인 상세 조회"""

    @staticmethod
    def get_campaign_with_proposals_count(
        campaign_id: int,
        advertiser_id: int
    ) -> Optional[Campaign]:
        """
        캠페인 조회 (지원자 수 포함)

        Args:
            campaign_id: 캠페인 ID
            advertiser_id: 광고주 ID (소유권 확인용)

        Returns:
            Campaign 객체 (지원자 수 annotated) 또는 None
        """
        return Campaign.objects.annotate(
            total_proposals=Count('proposals'),
            submitted_proposals=Count(
                'proposals',
                filter=Q(proposals__status='submitted')
            ),
            selected_proposals=Count(
                'proposals',
                filter=Q(proposals__status='selected')
            ),
            rejected_proposals=Count(
                'proposals',
                filter=Q(proposals__status='rejected')
            )
        ).select_related('advertiser').filter(
            id=campaign_id,
            advertiser_id=advertiser_id
        ).first()

    @staticmethod
    def get_proposals_by_campaign(
        campaign_id: int
    ) -> List[ProposalDetailDTO]:
        """
        캠페인의 지원자 목록 조회 (DTO 변환)

        Args:
            campaign_id: 캠페인 ID

        Returns:
            ProposalDetailDTO 리스트
        """
        proposals = Proposal.objects.filter(
            campaign_id=campaign_id
        ).select_related(
            'influencer',
            'influencer__influencer_profile'
        ).order_by('-created_at')

        return [
            ProposalDetailDTO(
                proposal_id=p.id,
                influencer_name=p.influencer.name,
                influencer_email=p.influencer.email,
                influencer_contact=p.influencer.contact,
                sns_link=p.influencer.influencer_profile.sns_link,
                cover_letter=p.cover_letter,
                desired_visit_date=p.desired_visit_date,
                status=p.status,
                created_at=p.created_at.strftime('%Y-%m-%d %H:%M')
            )
            for p in proposals
        ]
```

**Acceptance Tests**:
- [ ] 캠페인 조회 시 지원자 수가 정확히 계산됨
- [ ] 다른 광고주의 캠페인 조회 시 None 반환
- [ ] 지원자 목록이 최신순으로 정렬됨
- [ ] N+1 쿼리 발생하지 않음 (django-debug-toolbar로 확인)

---

### Phase 4: View Layer 구현

**목표**: HTTP 요청/응답 처리 및 Service/Selector 오케스트레이션

**작업 항목**:

1. **광고주용 체험단 상세 View**
   - 파일: `apps/campaigns/views.py`
   - 설명: 상세 페이지 렌더링 및 액션 처리
   - 의존성: Phase 2, 3 완료

```python
# apps/campaigns/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.users.permissions import AdvertiserRequiredMixin
from .models import Campaign
from .selectors.campaign_selectors import CampaignDetailSelector
from .services.campaign_management import CampaignCloseService
from .services.influencer_selection import InfluencerSelectionService
from .dto import (
    CampaignCloseDTO,
    InfluencerSelectionDTO
)
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    ServiceException
)


class AdvertiserCampaignDetailView(LoginRequiredMixin, AdvertiserRequiredMixin, View):
    """광고주용 체험단 상세 페이지"""

    template_name = 'campaigns/advertiser_campaign_detail.html'

    def get(self, request, pk):
        """
        체험단 상세 페이지 렌더링

        Args:
            request: HTTP 요청
            pk: 캠페인 ID
        """
        # 1. 캠페인 조회 (소유자 확인 포함)
        campaign = CampaignDetailSelector.get_campaign_with_proposals_count(
            campaign_id=pk,
            advertiser_id=request.user.id
        )

        if not campaign:
            messages.error(request, "존재하지 않거나 접근할 수 없는 체험단입니다.")
            return redirect('campaigns:advertiser_list')

        # 2. 지원자 목록 조회
        proposals = CampaignDetailSelector.get_proposals_by_campaign(
            campaign_id=pk
        )

        # 3. 상태별 액션 버튼 표시 여부 결정
        context = {
            'campaign': campaign,
            'proposals': proposals,
            'can_close': campaign.status == 'recruiting',
            'can_select': (
                campaign.status == 'recruitment_ended' and
                campaign.submitted_proposals > 0
            ),
            'is_complete': campaign.status == 'selection_complete',
        }

        return render(request, self.template_name, context)


@login_required
@require_POST
def close_recruitment(request, pk):
    """
    모집 마감 처리 (Ajax 요청)

    Args:
        request: HTTP POST 요청
        pk: 캠페인 ID
    """
    try:
        # 1. DTO 생성
        dto = CampaignCloseDTO(campaign_id=pk)

        # 2. 서비스 실행
        service = CampaignCloseService()
        campaign = service.execute(user=request.user, dto=dto)

        # 3. 성공 응답
        messages.success(request, "모집이 종료되었습니다.")
        return redirect('campaigns:advertiser_detail', pk=pk)

    except PermissionDeniedException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_list')

    except InvalidStateException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_detail', pk=pk)

    except Exception as e:
        messages.error(request, "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        return redirect('campaigns:advertiser_detail', pk=pk)


@login_required
@require_POST
def select_influencers(request, pk):
    """
    체험단 선정 처리 (Ajax 요청)

    Args:
        request: HTTP POST 요청
        pk: 캠페인 ID
    """
    try:
        # 1. 선택된 지원자 ID 목록 파싱
        selected_ids = request.POST.getlist('selected_proposals[]', [])
        selected_ids = [int(id) for id in selected_ids if id.isdigit()]

        # 2. DTO 생성
        dto = InfluencerSelectionDTO(
            campaign_id=pk,
            selected_proposal_ids=selected_ids
        )

        # 3. 서비스 실행
        service = InfluencerSelectionService()
        result = service.execute(user=request.user, dto=dto)

        # 4. 성공 응답
        messages.success(
            request,
            f"체험단 선정이 완료되었습니다. "
            f"선정: {result.selected_count}명, "
            f"반려: {result.rejected_count}명"
        )
        return redirect('campaigns:advertiser_detail', pk=pk)

    except PermissionDeniedException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_list')

    except InvalidStateException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_detail', pk=pk)

    except ServiceException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_detail', pk=pk)

    except ValueError:
        messages.error(request, "잘못된 요청입니다.")
        return redirect('campaigns:advertiser_detail', pk=pk)

    except Exception as e:
        messages.error(request, "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        return redirect('campaigns:advertiser_detail', pk=pk)
```

2. **URL 라우팅**
   - 파일: `apps/campaigns/urls.py`
   - 설명: 광고주용 URL 패턴 추가
   - 의존성: Phase 4-1 완료

```python
# apps/campaigns/urls.py

from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # ... 기존 URL 패턴들 ...

    # 광고주용 체험단 상세 및 관리
    path(
        'manage/<int:pk>/',
        views.AdvertiserCampaignDetailView.as_view(),
        name='advertiser_detail'
    ),
    path(
        'manage/<int:pk>/close/',
        views.close_recruitment,
        name='close_recruitment'
    ),
    path(
        'manage/<int:pk>/select/',
        views.select_influencers,
        name='select_influencers'
    ),
]
```

**Acceptance Tests**:
- [ ] 광고주 로그인 후 자신의 캠페인 상세 페이지 접근 가능
- [ ] 다른 광고주의 캠페인 접근 시 에러 메시지 및 리디렉션
- [ ] 비로그인 상태 접근 시 로그인 페이지로 리디렉션
- [ ] 인플루언서 계정 접근 시 403 에러
- [ ] 모집 마감 버튼 클릭 시 정상 동작
- [ ] 체험단 선정 버튼 클릭 시 정상 동작

---

### Phase 5: Template 구현

**목표**: Bootstrap 기반 UI 구현

**작업 항목**:

1. **광고주용 체험단 상세 템플릿**
   - 파일: `apps/campaigns/templates/campaigns/advertiser_campaign_detail.html`
   - 설명: 메인 페이지 템플릿
   - 의존성: Phase 4 완료

```django
{% extends "base.html" %}
{% load static %}

{% block title %}{{ campaign.name }} - 지원자 관리{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- 캠페인 상태 뱃지 -->
    <div class="row mb-3">
        <div class="col">
            <h2>{{ campaign.name }}</h2>
            {% if campaign.status == 'recruiting' %}
                <span class="badge bg-success">모집 중</span>
            {% elif campaign.status == 'recruitment_ended' %}
                <span class="badge bg-secondary">모집 종료</span>
            {% elif campaign.status == 'selection_complete' %}
                <span class="badge bg-primary">선정 완료</span>
            {% endif %}
        </div>
    </div>

    <!-- 캠페인 기본 정보 -->
    <div class="card mb-4">
        <div class="card-header">
            <h5 class="mb-0">캠페인 정보</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <p><strong>모집 기간:</strong> {{ campaign.recruitment_start_date }} ~ {{ campaign.recruitment_end_date }}</p>
                    <p><strong>모집 인원:</strong> {{ campaign.recruitment_count }}명</p>
                </div>
                <div class="col-md-6">
                    <p><strong>전체 지원자:</strong> {{ campaign.total_proposals }}명</p>
                    <p><strong>신청 완료:</strong> {{ campaign.submitted_proposals }}명</p>
                    {% if campaign.status == 'selection_complete' %}
                        <p><strong>선정:</strong> {{ campaign.selected_proposals }}명</p>
                        <p><strong>반려:</strong> {{ campaign.rejected_proposals }}명</p>
                    {% endif %}
                </div>
            </div>
            <hr>
            <p><strong>제공 혜택:</strong></p>
            <p>{{ campaign.benefits|linebreaks }}</p>
            <p><strong>미션:</strong></p>
            <p>{{ campaign.mission|linebreaks }}</p>
        </div>
    </div>

    <!-- 액션 버튼 영역 -->
    <div class="mb-3">
        {% if can_close %}
            <button type="button" class="btn btn-warning" data-bs-toggle="modal" data-bs-target="#closeModal">
                모집 종료
            </button>
        {% endif %}

        {% if can_select %}
            <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#selectModal">
                체험단 선정
            </button>
        {% endif %}

        {% if is_complete %}
            <button type="button" class="btn btn-secondary" disabled>
                선정 완료됨
            </button>
        {% endif %}

        <a href="{% url 'campaigns:advertiser_list' %}" class="btn btn-outline-secondary">
            목록으로
        </a>
    </div>

    <!-- 지원자 목록 테이블 -->
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">지원자 목록 ({{ proposals|length }}명)</h5>
        </div>
        <div class="card-body">
            {% if proposals %}
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>No</th>
                                <th>이름</th>
                                <th>연락처</th>
                                <th>SNS</th>
                                <th>각오 한마디</th>
                                <th>방문 희망일</th>
                                <th>지원일</th>
                                <th>상태</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for proposal in proposals %}
                                <tr>
                                    <td>{{ forloop.counter }}</td>
                                    <td>{{ proposal.influencer_name }}</td>
                                    <td>{{ proposal.influencer_contact }}</td>
                                    <td>
                                        <a href="{{ proposal.sns_link }}" target="_blank" class="btn btn-sm btn-outline-primary">
                                            SNS 보기
                                        </a>
                                    </td>
                                    <td>
                                        <span class="d-inline-block text-truncate" style="max-width: 200px;" title="{{ proposal.cover_letter }}">
                                            {{ proposal.cover_letter }}
                                        </span>
                                    </td>
                                    <td>{{ proposal.desired_visit_date }}</td>
                                    <td>{{ proposal.created_at }}</td>
                                    <td>
                                        {% if proposal.status == 'submitted' %}
                                            <span class="badge bg-info">신청완료</span>
                                        {% elif proposal.status == 'selected' %}
                                            <span class="badge bg-success">선정</span>
                                        {% elif proposal.status == 'rejected' %}
                                            <span class="badge bg-secondary">반려</span>
                                        {% endif %}
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <div class="text-center py-5">
                    <p class="text-muted">아직 지원자가 없습니다.</p>
                </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- 모집 종료 확인 모달 -->
<div class="modal fade" id="closeModal" tabindex="-1" aria-labelledby="closeModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="closeModalLabel">모집 종료 확인</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p>모집을 종료하시겠습니까?</p>
                <p class="text-danger small">
                    종료 후에는 추가 지원자를 받을 수 없습니다.
                </p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                <form method="POST" action="{% url 'campaigns:close_recruitment' campaign.id %}">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-warning">확인</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- 체험단 선정 모달 -->
<div class="modal fade" id="selectModal" tabindex="-1" aria-labelledby="selectModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="selectModalLabel">
                    체험단 선정 (모집인원: {{ campaign.recruitment_count }}명)
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="selectionForm" method="POST" action="{% url 'campaigns:select_influencers' campaign.id %}">
                    {% csrf_token %}

                    <div class="alert alert-info">
                        현재 <strong id="selectedCount">0</strong>/{{ campaign.recruitment_count }}명 선택됨
                    </div>

                    {% if proposals %}
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>
                                            <input type="checkbox" id="selectAll" class="form-check-input">
                                        </th>
                                        <th>이름</th>
                                        <th>SNS</th>
                                        <th>각오 한마디</th>
                                        <th>방문 희망일</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for proposal in proposals %}
                                        {% if proposal.status == 'submitted' %}
                                            <tr>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        name="selected_proposals[]"
                                                        value="{{ proposal.proposal_id }}"
                                                        class="form-check-input proposal-checkbox"
                                                    >
                                                </td>
                                                <td>{{ proposal.influencer_name }}</td>
                                                <td>
                                                    <a href="{{ proposal.sns_link }}" target="_blank" class="btn btn-sm btn-link">
                                                        보기
                                                    </a>
                                                </td>
                                                <td>
                                                    <span class="d-inline-block text-truncate" style="max-width: 150px;" title="{{ proposal.cover_letter }}">
                                                        {{ proposal.cover_letter }}
                                                    </span>
                                                </td>
                                                <td>{{ proposal.desired_visit_date }}</td>
                                            </tr>
                                        {% endif %}
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-muted">선택 가능한 지원자가 없습니다.</p>
                    {% endif %}
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                <button
                    type="button"
                    class="btn btn-primary"
                    id="confirmSelection"
                    onclick="confirmAndSubmit()"
                >
                    선정 완료
                </button>
            </div>
        </div>
    </div>
</div>

<script>
// 선택 인원 카운트 업데이트
function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.proposal-checkbox:checked');
    const count = checkboxes.length;
    const maxCount = {{ campaign.recruitment_count }};

    document.getElementById('selectedCount').textContent = count;

    const alertDiv = document.querySelector('#selectModal .alert');
    if (count > maxCount) {
        alertDiv.classList.remove('alert-info');
        alertDiv.classList.add('alert-danger');
        alertDiv.innerHTML = `<strong>경고:</strong> 현재 ${count}명 선택됨 (모집 인원 ${maxCount}명 초과)`;
    } else {
        alertDiv.classList.remove('alert-danger');
        alertDiv.classList.add('alert-info');
        alertDiv.innerHTML = `현재 <strong>${count}</strong>/${maxCount}명 선택됨`;
    }
}

// 체크박스 이벤트 리스너
document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('.proposal-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });

    // 전체 선택/해제
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedCount();
        });
    }
});

// 선정 확인 및 제출
function confirmAndSubmit() {
    const checkboxes = document.querySelectorAll('.proposal-checkbox:checked');
    const count = checkboxes.length;
    const maxCount = {{ campaign.recruitment_count }};

    if (count === 0) {
        alert('최소 1명 이상의 지원자를 선택해야 합니다.');
        return;
    }

    if (count > maxCount) {
        alert(`모집 인원(${maxCount}명)을 초과하여 선택할 수 없습니다.\n현재 ${count}명이 선택되었습니다.`);
        return;
    }

    const message = `선정된 ${count}명에게 선정 알림이 전달되며, 나머지는 반려 처리됩니다.\n계속하시겠습니까?`;

    if (confirm(message)) {
        document.getElementById('selectionForm').submit();
    }
}
</script>
{% endblock %}
```

**Acceptance Tests**:
- [ ] 캠페인 정보가 올바르게 표시됨
- [ ] 상태별 뱃지가 올바르게 표시됨
- [ ] 지원자 목록이 테이블 형태로 표시됨
- [ ] SNS 링크 클릭 시 새 창에서 열림
- [ ] 모집 종료 모달이 올바르게 동작
- [ ] 체험단 선정 모달이 올바르게 동작
- [ ] 선택 인원 카운트가 실시간으로 업데이트됨
- [ ] 모집 인원 초과 시 경고 표시
- [ ] 전체 선택 체크박스 동작
- [ ] 확인 다이얼로그 표시

---

### Phase 6: 권한 관리 Mixin 구현

**목표**: 광고주 전용 접근 제어

**작업 항목**:

1. **AdvertiserRequiredMixin**
   - 파일: `apps/users/permissions.py`
   - 설명: 광고주만 접근 가능하도록 제한
   - 의존성: 없음

```python
# apps/users/permissions.py

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

class AdvertiserRequiredMixin(UserPassesTestMixin):
    """광고주 역할만 접근 가능"""

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.role == 'advertiser'
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "광고주만 접근할 수 있는 페이지입니다."
        )
        return redirect('campaigns:home')
```

**Acceptance Tests**:
- [ ] 광고주 계정으로 접근 시 통과
- [ ] 인플루언서 계정으로 접근 시 403 에러 및 리디렉션
- [ ] 비로그인 상태 접근 시 로그인 페이지로 리디렉션

---

## 5. 에러 처리

### 5.1 백엔드 에러

| 에러 클래스 | HTTP 상태 | 발생 조건 | 처리 방법 |
|----------|----------|----------|----------|
| PermissionDeniedException | 403 | 권한 없는 사용자 접근 | 에러 메시지 + 캠페인 목록으로 리디렉션 |
| InvalidStateException | 400 | 잘못된 캠페인 상태 | 에러 메시지 + 상세 페이지로 리디렉션 |
| ServiceException | 400 | 비즈니스 규칙 위반 (인원 초과 등) | 에러 메시지 + 상세 페이지로 리디렉션 |
| Campaign.DoesNotExist | 404 | 존재하지 않는 캠페인 | 에러 메시지 + 캠페인 목록으로 리디렉션 |
| ValueError | 400 | 잘못된 요청 파라미터 | 에러 메시지 + 상세 페이지로 리디렉션 |

### 5.2 프론트엔드 에러 핸들링

**JavaScript 검증**:
- 선정 인원 0명 선택 시: `alert()` 경고 표시
- 모집 인원 초과 시: `alert()` 경고 표시 + 제출 차단
- 확인 다이얼로그: `confirm()` 사용자 의사 재확인

**Django Messages Framework**:
- 성공: `messages.success()` - 녹색 토스트
- 에러: `messages.error()` - 빨간색 토스트
- 경고: `messages.warning()` - 노란색 토스트

---

## 6. 테스트 계획

### 6.1 단위 테스트

**파일**: `apps/campaigns/tests/test_services.py`

**테스트 케이스**:

| ID | 테스트 내용 | 입력 | 기대 결과 |
|----|-----------|------|----------|
| UT-007-01 | 모집 마감 정상 처리 | 모집 중 캠페인 + 소유자 | status='recruitment_ended' |
| UT-007-02 | 권한 없는 사용자 모집 마감 시도 | 다른 광고주 | PermissionDeniedException |
| UT-007-03 | 이미 마감된 캠페인 재마감 시도 | 모집 종료 캠페인 | InvalidStateException |
| UT-007-04 | 체험단 선정 정상 처리 | 5명 모집에 3명 선택 | 3명 selected, 나머지 rejected |
| UT-007-05 | 모집 인원 초과 선택 | 5명 모집에 7명 선택 | ServiceException |
| UT-007-06 | 선정 인원 없음 | 0명 선택 | ServiceException |
| UT-007-07 | 유효하지 않은 proposal_id 포함 | 다른 캠페인의 proposal_id | ServiceException |

**코드 예시**:
```python
# apps/campaigns/tests/test_services.py

import pytest
from django.utils import timezone
from apps.campaigns.services.campaign_management import CampaignCloseService
from apps.campaigns.services.influencer_selection import InfluencerSelectionService
from apps.campaigns.dto import CampaignCloseDTO, InfluencerSelectionDTO
from apps.campaigns.models import Campaign, Proposal
from apps.users.models import User
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    ServiceException
)

@pytest.mark.django_db
class TestCampaignCloseService:
    """모집 마감 서비스 테스트"""

    def test_close_recruitment_successfully(
        self,
        advertiser_user,
        recruiting_campaign
    ):
        """정상적인 모집 마감 처리"""
        # Given
        dto = CampaignCloseDTO(campaign_id=recruiting_campaign.id)
        service = CampaignCloseService()

        # When
        result = service.execute(user=advertiser_user, dto=dto)

        # Then
        assert result.status == 'recruitment_ended'

        # DB 확인
        campaign = Campaign.objects.get(id=recruiting_campaign.id)
        assert campaign.status == 'recruitment_ended'

    def test_close_recruitment_permission_denied(
        self,
        other_advertiser_user,
        recruiting_campaign
    ):
        """권한 없는 사용자의 모집 마감 시도"""
        # Given
        dto = CampaignCloseDTO(campaign_id=recruiting_campaign.id)
        service = CampaignCloseService()

        # When & Then
        with pytest.raises(PermissionDeniedException):
            service.execute(user=other_advertiser_user, dto=dto)

    def test_close_already_ended_campaign(
        self,
        advertiser_user,
        ended_campaign
    ):
        """이미 종료된 캠페인 재마감 시도"""
        # Given
        dto = CampaignCloseDTO(campaign_id=ended_campaign.id)
        service = CampaignCloseService()

        # When & Then
        with pytest.raises(InvalidStateException):
            service.execute(user=advertiser_user, dto=dto)


@pytest.mark.django_db
class TestInfluencerSelectionService:
    """체험단 선정 서비스 테스트"""

    def test_select_influencers_successfully(
        self,
        advertiser_user,
        ended_campaign_with_proposals
    ):
        """정상적인 체험단 선정"""
        # Given
        campaign = ended_campaign_with_proposals
        proposals = list(Proposal.objects.filter(
            campaign=campaign,
            status='submitted'
        )[:3])

        dto = InfluencerSelectionDTO(
            campaign_id=campaign.id,
            selected_proposal_ids=[p.id for p in proposals]
        )
        service = InfluencerSelectionService()

        # When
        result = service.execute(user=advertiser_user, dto=dto)

        # Then
        assert result.selected_count == 3
        assert result.rejected_count > 0
        assert result.campaign_status == 'selection_complete'

        # DB 확인
        selected = Proposal.objects.filter(
            campaign=campaign,
            status='selected'
        ).count()
        assert selected == 3

    def test_select_exceeds_recruitment_count(
        self,
        advertiser_user,
        ended_campaign_with_proposals
    ):
        """모집 인원 초과 선택"""
        # Given
        campaign = ended_campaign_with_proposals
        campaign.recruitment_count = 2
        campaign.save()

        proposals = list(Proposal.objects.filter(
            campaign=campaign,
            status='submitted'
        )[:5])

        dto = InfluencerSelectionDTO(
            campaign_id=campaign.id,
            selected_proposal_ids=[p.id for p in proposals]
        )
        service = InfluencerSelectionService()

        # When & Then
        with pytest.raises(ServiceException) as exc_info:
            service.execute(user=advertiser_user, dto=dto)

        assert "초과" in str(exc_info.value)

    def test_select_no_proposals(
        self,
        advertiser_user,
        ended_campaign_with_proposals
    ):
        """선정 인원 없음"""
        # Given
        campaign = ended_campaign_with_proposals

        dto = InfluencerSelectionDTO(
            campaign_id=campaign.id,
            selected_proposal_ids=[]
        )
        service = InfluencerSelectionService()

        # When & Then
        with pytest.raises(ServiceException) as exc_info:
            service.execute(user=advertiser_user, dto=dto)

        assert "최소 1명" in str(exc_info.value)
```

**Fixtures** (conftest.py):
```python
# apps/campaigns/tests/conftest.py

import pytest
from django.utils import timezone
from datetime import date, timedelta
from apps.campaigns.models import Campaign, Proposal
from apps.users.models import User

@pytest.fixture
def recruiting_campaign(advertiser_user):
    """모집 중인 캠페인"""
    return Campaign.objects.create(
        advertiser=advertiser_user,
        name="테스트 캠페인",
        recruitment_start_date=date.today(),
        recruitment_end_date=date.today() + timedelta(days=7),
        recruitment_count=5,
        benefits="테스트 혜택",
        mission="테스트 미션",
        status='recruiting'
    )

@pytest.fixture
def ended_campaign(advertiser_user):
    """모집 종료된 캠페인"""
    return Campaign.objects.create(
        advertiser=advertiser_user,
        name="종료된 캠페인",
        recruitment_start_date=date.today() - timedelta(days=7),
        recruitment_end_date=date.today(),
        recruitment_count=5,
        benefits="테스트 혜택",
        mission="테스트 미션",
        status='recruitment_ended'
    )

@pytest.fixture
def ended_campaign_with_proposals(advertiser_user, influencer_users):
    """지원자가 있는 모집 종료 캠페인"""
    campaign = Campaign.objects.create(
        advertiser=advertiser_user,
        name="지원자 있는 캠페인",
        recruitment_start_date=date.today() - timedelta(days=7),
        recruitment_end_date=date.today(),
        recruitment_count=5,
        benefits="테스트 혜택",
        mission="테스트 미션",
        status='recruitment_ended'
    )

    # 지원자 10명 생성
    for i, influencer in enumerate(influencer_users[:10]):
        Proposal.objects.create(
            campaign=campaign,
            influencer=influencer,
            cover_letter=f"테스트 각오 {i}",
            desired_visit_date=date.today() + timedelta(days=i),
            status='submitted'
        )

    return campaign

@pytest.fixture
def influencer_users(db):
    """인플루언서 사용자 10명"""
    users = []
    for i in range(10):
        user = User.objects.create_user(
            email=f'influencer{i}@test.com',
            password='testpass123',
            name=f'인플루언서{i}',
            contact=f'010-{i:04d}-0000',
            role='influencer'
        )
        users.append(user)
    return users
```

### 6.2 통합 테스트

**파일**: `apps/campaigns/tests/test_views.py`

**테스트 시나리오**:
1. 광고주 로그인 → 자신의 캠페인 상세 페이지 접근 → 200 OK
2. 광고주 로그인 → 다른 광고주의 캠페인 접근 → 에러 메시지 + 리디렉션
3. 인플루언서 로그인 → 광고주 페이지 접근 → 403 Forbidden
4. 모집 중 캠페인 → 모집 종료 POST → 성공 메시지 + 상태 변경
5. 모집 종료 캠페인 → 체험단 선정 POST → 성공 메시지 + 지원자 상태 변경

### 6.3 E2E 테스트

**시나리오**: 광고주 체험단 관리 전체 플로우

1. 광고주 로그인
2. 체험단 관리 페이지 접속
3. 특정 캠페인 상세 페이지 접속
4. 지원자 목록 확인
5. '모집 종료' 버튼 클릭 → 확인 모달 → 확인
6. 성공 메시지 확인 및 페이지 새로고침
7. '체험단 선정' 버튼 표시 확인
8. '체험단 선정' 버튼 클릭 → 선정 모달 표시
9. 지원자 3명 선택 → 선택 카운트 업데이트 확인
10. '선정 완료' 버튼 클릭 → 확인 다이얼로그 → 확인
11. 성공 메시지 확인
12. 지원자 상태 뱃지 변경 확인 (선정/반려)

---

## 7. 보안 고려사항

### 7.1 인증/인가

**인증 (Authentication)**:
- Django의 Session-based 인증 사용
- `LoginRequiredMixin`으로 비로그인 접근 차단
- 로그인 페이지: `/accounts/login/`

**권한 (Authorization)**:
- `AdvertiserRequiredMixin`으로 광고주 역할만 접근 허용
- 캠페인 소유권 검증: `campaign.advertiser_id == request.user.id`
- URL 직접 접근 시에도 권한 검증 수행

### 7.2 데이터 보호

**입력 검증**:
- Django Form/ORM의 자동 검증 활용
- `selected_proposal_ids`: 정수 배열 형식 검증
- SQL Injection 방지: ORM 사용 (Raw SQL 사용 금지)

**CSRF 보호**:
- Django CSRF 미들웨어 활성화
- 모든 POST 요청에 `{% csrf_token %}` 포함

### 7.3 XSS 방지

**템플릿 자동 이스케이프**:
- Django Template Engine의 자동 HTML 이스케이프 활용
- 사용자 입력 데이터 표시 시 `{{ variable }}` 사용
- HTML 허용 시에만 `{{ variable|safe }}` 사용 (주의)

**JavaScript 인젝션 방지**:
- 사용자 입력을 JavaScript에 직접 삽입하지 않음
- 필요 시 JSON.stringify() 사용

---

## 8. 성능 고려사항

### 8.1 최적화 목표

- 페이지 로드 시간: 2초 이내
- 모집 마감 처리 시간: 1초 이내
- 체험단 선정 처리 시간: 3초 이내 (지원자 100명 기준)

### 8.2 쿼리 최적화

**select_related 사용**:
```python
# 지원자 조회 시 User, InfluencerProfile JOIN
proposals = Proposal.objects.filter(
    campaign_id=campaign_id
).select_related(
    'influencer',
    'influencer__influencer_profile'
)
```

**annotate로 집계**:
```python
# 캠페인 조회 시 지원자 수 함께 계산
campaign = Campaign.objects.annotate(
    total_proposals=Count('proposals'),
    submitted_proposals=Count('proposals', filter=Q(proposals__status='submitted'))
).get(id=campaign_id)
```

**벌크 업데이트**:
```python
# 개별 save() 대신 update() 사용
Proposal.objects.filter(
    id__in=selected_ids
).update(status='selected', updated_at=timezone.now())
```

### 8.3 데이터베이스 인덱스

기존 인덱스 활용:
- `campaigns.advertiser_id` (INDEX)
- `proposals.campaign_id` (INDEX)
- `proposals.influencer_id` (INDEX)

추가 인덱스 불필요 (지원자 수가 많지 않음)

### 8.4 캐싱 전략

MVP 단계에서는 캐싱 없음:
- 페이지 새로고침으로 최신 데이터 확인
- 실시간 동기화 불필요
- 추후 필요 시 Redis 도입 고려

---

## 9. 배포 계획

### 9.1 환경 변수

추가할 환경 변수 없음 (기존 설정 사용)

### 9.2 배포 순서

1. **로컬 개발 및 테스트**
   - pytest 전체 테스트 통과 확인
   - 로컬 서버에서 수동 테스트

2. **Git 커밋 및 푸시**
   ```bash
   git add .
   git commit -m "feat: 광고주용 체험단 상세 페이지 구현"
   git push origin main
   ```

3. **Railway 자동 배포**
   - GitHub 푸시 시 자동 배포 트리거
   - 빌드 로그 확인

4. **배포 후 검증**
   - Railway 대시보드에서 로그 확인
   - 배포된 URL로 접속하여 기능 테스트

### 9.3 롤백 계획

**Git 롤백**:
```bash
git revert HEAD
git push origin main
```

**데이터베이스 롤백**:
- 마이그레이션 없음 (기존 스키마 사용)
- 필요 시 Railway Volume 백업 복원

---

## 10. 모니터링 및 로깅

### 10.1 로그 항목

**Django 기본 로깅**:
```python
import logging

logger = logging.getLogger(__name__)

# Service 계층에서 에러 로깅
try:
    # ...
except Exception as e:
    logger.error(f"Campaign close failed: {campaign_id}, {str(e)}")
    raise
```

**주요 로그 포인트**:
- 모집 마감 성공/실패
- 체험단 선정 성공/실패
- 권한 검증 실패
- 데이터베이스 트랜잭션 오류

### 10.2 메트릭

MVP 단계에서는 별도 메트릭 수집 없음:
- Railway 대시보드의 기본 메트릭 활용
- 응답 시간, 에러율, 메모리 사용량

---

## 11. 체크리스트

### 11.1 구현 전
- [x] PRD 검토 완료
- [x] 유스케이스 문서 검토 완료
- [x] 데이터베이스 스키마 확인
- [x] 공통 모듈 확인
- [x] 코드베이스 구조 확인

### 11.2 구현 중
- [ ] DTO 정의 (Phase 1)
- [ ] Service Layer 구현 (Phase 2)
- [ ] Service 단위 테스트 작성 및 통과
- [ ] Selector Layer 구현 (Phase 3)
- [ ] View Layer 구현 (Phase 4)
- [ ] 권한 Mixin 구현 (Phase 6)
- [ ] Template 구현 (Phase 5)
- [ ] 통합 테스트 작성 및 통과

### 11.3 구현 후
- [ ] E2E 테스트 통과
- [ ] 수동 테스트 체크리스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서 업데이트 (README 등)
- [ ] Railway 배포 완료
- [ ] 배포 후 검증 완료

---

## 12. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-16 | Claude | 초기 작성 |

---

## 부록

### A. 주요 로직 의사코드

**모집 마감 로직**:
```
function close_recruitment(user, campaign_id):
    campaign = get_campaign(campaign_id)

    if campaign.advertiser_id != user.id:
        raise PermissionDenied

    if campaign.status != 'recruiting':
        raise InvalidState

    campaign.status = 'recruitment_ended'
    campaign.save()

    return campaign
```

**체험단 선정 로직**:
```
function select_influencers(user, campaign_id, selected_ids):
    BEGIN TRANSACTION

    campaign = get_campaign_with_lock(campaign_id)

    if campaign.advertiser_id != user.id:
        raise PermissionDenied

    if campaign.status != 'recruitment_ended':
        raise InvalidState

    if len(selected_ids) == 0:
        raise ServiceException("최소 1명 선택")

    if len(selected_ids) > campaign.recruitment_count:
        raise ServiceException("모집 인원 초과")

    # 선정
    update_proposals(
        where: id IN selected_ids,
        set: status='selected'
    )

    # 반려
    update_proposals(
        where: campaign_id=campaign_id AND status='submitted' AND id NOT IN selected_ids,
        set: status='rejected'
    )

    # 캠페인 상태 변경
    campaign.status = 'selection_complete'
    campaign.save()

    COMMIT TRANSACTION

    return result
```

### B. 의사결정 기록

**결정 1: Django Template vs React**
- **선택**: Django Template + Bootstrap
- **이유**:
  - MVP 신속 개발에 집중
  - 별도 빌드 과정 불필요
  - Server-Side Rendering으로 SEO 유리
  - 오버엔지니어링 방지
- **대안**: React (향후 고도화 시 고려)

**결정 2: Service Layer 패턴 적용**
- **선택**: Service + DTO 패턴 사용
- **이유**:
  - 비즈니스 로직을 View에서 분리
  - 테스트 용이성 향상
  - 향후 API 서버 전환 시 재사용 가능
  - 코드 가독성 및 유지보수성 향상
- **대안**: Fat View 패턴 (Django 전통 방식)

**결정 3: 실시간 알림 제외**
- **선택**: 페이지 새로고침으로 갱신
- **이유**:
  - MVP 범위 최소화
  - WebSocket/Polling 인프라 불필요
  - 내부 베타테스트 단계에서 충분
- **대안**: WebSocket 실시간 알림 (향후 고려)

### C. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| 동시 선정 요청 충돌 | 중 | 높음 | `select_for_update()`로 행 레벨 락 적용 |
| 대량 지원자 처리 성능 저하 | 낮 | 중 | 벌크 업데이트 사용, 필요 시 Celery 비동기 처리 도입 |
| 권한 우회 접근 시도 | 중 | 높음 | 모든 View에서 권한 검증, URL 직접 접근 차단 |
| CSRF 공격 | 중 | 높음 | Django CSRF 미들웨어 활성화, 모든 POST에 토큰 포함 |
| 선정 후 잘못된 선정 발견 | 중 | 중 | 선정 완료 상태 불가역, Django Admin으로 수동 수정 |

### D. Django Admin 백업 관리 기능

선정 완료 후 수정이 필요한 경우를 대비하여 Django Admin에 관리 기능 추가:

```python
# apps/campaigns/admin.py

from django.contrib import admin
from .models import Campaign, Proposal

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'advertiser', 'status', 'recruitment_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'advertiser__name']
    readonly_fields = ['created_at', 'updated_at']

    # 선정 완료 상태를 다시 모집 종료로 되돌리기 (긴급 시에만)
    actions = ['revert_to_recruitment_ended']

    def revert_to_recruitment_ended(self, request, queryset):
        updated = queryset.filter(
            status='selection_complete'
        ).update(status='recruitment_ended')

        self.message_user(
            request,
            f"{updated}개 캠페인이 '모집 종료' 상태로 되돌려졌습니다."
        )

    revert_to_recruitment_ended.short_description = "선정 완료 → 모집 종료로 되돌리기"

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'influencer', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['campaign__name', 'influencer__name']
    readonly_fields = ['created_at', 'updated_at']
```

---

## 13. 다음 단계

1. **Phase 1-6 순차적 구현**
   - 각 Phase별로 TDD 방식 적용
   - 단위 테스트 먼저 작성 후 구현

2. **통합 테스트 작성**
   - View 레벨 테스트
   - 전체 플로우 검증

3. **수동 테스트**
   - 로컬 환경에서 UI/UX 검증
   - Edge Case 확인

4. **배포 및 베타테스트**
   - Railway 배포
   - 내부 테스터 피드백 수집

5. **피드백 반영 및 개선**
   - 버그 수정
   - UX 개선
