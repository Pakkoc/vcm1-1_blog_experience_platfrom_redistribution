# 유스케이스 07: 체험단 선정

## 1. 유스케이스 개요

### 1.1. 기능 명칭
체험단 선정 (Influencer Selection)

### 1.2. 액터 (Actor)
- 주 액터: 광고주 (Advertiser)
- 부 액터: 인플루언서 (Influencer) - 선정 결과를 확인하는 수동적 역할

### 1.3. 목적 (Purpose)
광고주가 모집이 종료된 체험단 캠페인에 지원한 인플루언서 목록을 검토하고, 캠페인 목적에 가장 적합한 인원을 최종 선정하여 체험단 활동을 시작할 수 있도록 합니다.

### 1.4. 사전 조건 (Preconditions)
- 광고주가 로그인된 상태여야 합니다.
- 대상 캠페인이 존재하며, 현재 상태가 '모집 종료(recruitment_ended)'여야 합니다.
- 광고주가 해당 캠페인의 소유자여야 합니다.
- 캠페인에 1명 이상의 지원자(Proposal)가 존재해야 합니다.

### 1.5. 사후 조건 (Postconditions)
- 선정된 인플루언서의 지원 상태가 '선정(selected)'으로 변경됩니다.
- 선정되지 않은 인플루언서의 지원 상태가 '반려(rejected)'로 변경됩니다.
- 캠페인의 최종 상태가 '선정 완료(selection_complete)'로 변경됩니다.
- 인플루언서들은 '내 지원 목록' 페이지에서 변경된 상태를 확인할 수 있습니다.

---

## 2. 기본 플로우 (Main Flow)

### 2.1. 트리거
광고주가 '광고주용 체험단 상세' 페이지에서 '체험단 선정' 버튼을 클릭합니다.

### 2.2. 단계별 프로세스

#### 단계 1: 선정 다이얼로그 표시
- **액터 행동**: 광고주가 '모집 종료' 상태인 캠페인의 상세 페이지에서 '체험단 선정' 버튼을 클릭합니다.
- **시스템 응답**:
  - 지원자 목록이 표시된 선정 다이얼로그(모달)를 화면에 노출합니다.
  - 지원자 목록에는 각 인플루언서의 기본 정보(이름, SNS 채널, 각오 한마디, 방문 희망일 등)가 표시됩니다.
  - 각 지원자 옆에 선택할 수 있는 체크박스가 제공됩니다.

#### 단계 2: 선정 인원 선택
- **액터 행동**: 광고주가 선정할 인플루언서를 체크박스로 선택합니다.
- **시스템 응답**:
  - 선택된 인원 수를 실시간으로 표시합니다.
  - 모집 인원 대비 현재 선택 인원을 시각적으로 안내합니다 (예: "3/5명 선택됨").

#### 단계 3: 선정 완료 요청
- **액터 행동**: 광고주가 '선정 완료' 버튼을 클릭합니다.
- **시스템 응답**:
  - 선정 처리를 진행하기 전 최종 확인 메시지를 표시합니다.
  - "선정된 N명에게 선정 알림이 전달되며, 나머지는 반려 처리됩니다. 계속하시겠습니까?"

#### 단계 4: 권한 및 상태 검증
- **시스템 처리**:
  - 현재 로그인된 사용자가 해당 캠페인의 소유자(advertiser_id)인지 확인합니다.
  - 캠페인의 현재 상태가 '모집 종료(recruitment_ended)'인지 확인합니다.

#### 단계 5: 선정 인원 유효성 검증
- **시스템 처리**:
  - 광고주가 선택한 인원 수를 확인합니다.
  - 선택한 인원이 1명 이상인지 검증합니다.
  - 선택한 인원이 캠페인의 '모집 인원(recruitment_count)'을 초과하지 않는지 검증합니다.

#### 단계 6: 데이터베이스 트랜잭션 실행
- **시스템 처리** (단일 트랜잭션으로 원자적 실행):

  **6.1. 선정된 지원자 상태 업데이트**
  ```
  UPDATE proposals
  SET status = 'selected', updated_at = NOW()
  WHERE id IN (선택된 지원자 ID 목록)
  AND campaign_id = (현재 캠페인 ID)
  ```

  **6.2. 반려된 지원자 상태 업데이트**
  ```
  UPDATE proposals
  SET status = 'rejected', updated_at = NOW()
  WHERE campaign_id = (현재 캠페인 ID)
  AND status = 'submitted'
  AND id NOT IN (선택된 지원자 ID 목록)
  ```

  **6.3. 캠페인 상태 업데이트**
  ```
  UPDATE campaigns
  SET status = 'selection_complete', updated_at = NOW()
  WHERE id = (현재 캠페인 ID)
  ```

#### 단계 7: 성공 응답
- **시스템 응답**:
  - 선정 다이얼로그를 닫습니다.
  - 페이지를 새로고침하여 최신 상태를 반영합니다.
  - 성공 피드백 메시지를 표시합니다: "체험단 선정이 완료되었습니다."
  - '체험단 선정' 버튼을 비활성화하거나 숨김 처리합니다.
  - 지원자 목록의 각 항목에 최종 상태('선정' 또는 '반려')를 표시합니다.

---

## 3. 대체 플로우 (Alternative Flows)

### 3.1. AF-01: 모집 인원 초과 선택
**트리거**: 단계 5에서 선택한 인원이 모집 인원을 초과한 경우

**처리 절차**:
1. 시스템은 선정 절차를 중단합니다.
2. 오류 메시지를 표시합니다: "모집 인원(N명)을 초과하여 선택할 수 없습니다. 현재 M명이 선택되었습니다."
3. 광고주는 선정 다이얼로그에 머물며, 선택 인원을 조정할 수 있습니다.
4. 기본 플로우 단계 2로 복귀합니다.

### 3.2. AF-02: 선정 인원 없음
**트리거**: 단계 5에서 아무도 선택하지 않고 '선정 완료' 버튼을 클릭한 경우

**처리 절차**:
1. 시스템은 선정 절차를 중단합니다.
2. 오류 메시지를 표시합니다: "최소 1명 이상의 지원자를 선택해야 합니다."
3. 광고주는 선정 다이얼로그에 머물며, 지원자를 선택할 수 있습니다.
4. 기본 플로우 단계 2로 복귀합니다.

### 3.3. AF-03: 권한 없는 접근
**트리거**: 단계 4에서 현재 로그인된 사용자가 캠페인 소유자가 아닌 경우

**처리 절차**:
1. 시스템은 즉시 선정 절차를 중단합니다.
2. HTTP 403 Forbidden 오류를 반환합니다.
3. 오류 페이지를 표시하거나 이전 페이지로 리디렉션합니다.
4. 오류 메시지를 표시합니다: "해당 작업을 수행할 권한이 없습니다."
5. 유스케이스가 종료됩니다.

### 3.4. AF-04: 잘못된 캠페인 상태
**트리거**: 단계 4에서 캠페인 상태가 '모집 종료'가 아닌 경우

**상황별 처리**:
- **상태가 '모집 중'인 경우**:
  - 오류 메시지: "모집이 아직 진행 중인 캠페인입니다. 먼저 모집을 종료해주세요."
  - '모집 종료' 버튼을 안내합니다.

- **상태가 '선정 완료'인 경우**:
  - 정보 메시지: "이미 체험단 선정이 완료된 캠페인입니다."
  - 선정 버튼을 비활성화하고 선정된 인원 목록을 표시합니다.

**공통 처리**:
- 선정 다이얼로그가 열리지 않습니다.
- 광고주는 캠페인 상세 페이지에 머뭅니다.
- 유스케이스가 종료됩니다.

### 3.5. AF-05: 트랜잭션 실패
**트리거**: 단계 6에서 데이터베이스 트랜잭션 실행 중 오류 발생

**처리 절차**:
1. 시스템은 전체 트랜잭션을 롤백(Rollback)합니다.
2. 모든 데이터는 선정 시도 이전 상태로 복원됩니다.
3. 오류 로그를 기록합니다.
4. 사용자에게 일반적인 오류 메시지를 표시합니다: "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
5. 선정 다이얼로그를 닫고 페이지를 새로고침합니다.
6. 유스케이스가 종료됩니다.

---

## 4. 예외 플로우 (Exception Flows)

### 4.1. EF-01: 지원자가 없는 캠페인
**트리거**: 캠페인에 지원자(Proposal)가 1명도 없는 상태에서 '체험단 선정' 버튼에 접근

**처리 절차**:
1. 시스템은 '체험단 선정' 버튼을 비활성화하거나 숨김 처리합니다.
2. 안내 메시지를 표시합니다: "지원자가 없어 체험단을 선정할 수 없습니다."
3. 유스케이스가 시작되지 않습니다.

### 4.2. EF-02: 네트워크 타임아웃
**트리거**: 단계 3에서 '선정 완료' 요청 전송 후 네트워크 타임아웃 발생

**처리 절차**:
1. 시스템은 로딩 상태를 해제합니다.
2. 오류 메시지를 표시합니다: "네트워크 연결이 불안정합니다. 다시 시도해주세요."
3. 광고주는 선정 다이얼로그에 머물며, 다시 '선정 완료' 버튼을 클릭할 수 있습니다.
4. 기본 플로우 단계 3으로 복귀합니다.

### 4.3. EF-03: 동시 선정 요청 충돌
**트리거**: 여러 브라우저 탭 또는 세션에서 동일 캠페인에 대해 동시에 선정 요청이 발생한 경우

**처리 절차**:
1. 데이터베이스 레벨에서 캠페인 상태를 먼저 확인하는 쿼리에 락(Lock)을 설정합니다.
2. 먼저 도착한 요청만 처리하고, 나머지 요청은 AF-04(잘못된 캠페인 상태)로 처리됩니다.
3. 두 번째 요청은 "이미 체험단 선정이 완료된 캠페인입니다." 메시지를 받습니다.
4. 유스케이스가 종료됩니다.

---

## 5. 비즈니스 규칙 (Business Rules)

### 5.1. BR-01: 선정 인원 제한
- 선정 가능한 최소 인원: 1명
- 선정 가능한 최대 인원: 캠페인에 설정된 '모집 인원(recruitment_count)' 이하
- 위반 시: AF-01 또는 AF-02 플로우 실행

### 5.2. BR-02: 선정 가능 상태
- 체험단 선정은 캠페인 상태가 '모집 종료(recruitment_ended)'일 때만 가능합니다.
- '모집 중(recruiting)' 상태에서는 선정 기능에 접근할 수 없습니다.
- '선정 완료(selection_complete)' 상태에서는 재선정이 불가능합니다.

### 5.3. BR-03: 소유권 검증
- 체험단 선정은 해당 캠페인을 생성한 광고주만 수행할 수 있습니다.
- 다른 광고주는 URL을 직접 입력하더라도 접근이 차단됩니다.

### 5.4. BR-04: 원자적 트랜잭션
- 선정, 반려, 캠페인 상태 변경은 단일 트랜잭션으로 실행되어야 합니다.
- 트랜잭션 중 일부만 성공하는 경우를 방지하기 위해, 실패 시 전체 롤백을 보장해야 합니다.

### 5.5. BR-05: 상태 불가역성
- 한번 '선정 완료(selection_complete)' 상태가 된 캠페인은 다시 '모집 종료' 상태로 되돌릴 수 없습니다.
- 선정된 인플루언서의 상태('selected')는 변경할 수 없습니다.
- 잘못된 선정의 경우, 별도의 관리자 기능 또는 수동 데이터베이스 조작이 필요합니다.

---

## 6. 데이터 요구사항 (Data Requirements)

### 6.1. 입력 데이터 (Input Data)

| 데이터 항목 | 타입 | 필수 여부 | 검증 규칙 | 출처 |
|---|---|---|---|---|
| campaign_id | Integer | 필수 | 존재하는 캠페인 ID | URL 파라미터 |
| selected_proposal_ids | Array[Integer] | 필수 | 1개 이상, 모집 인원 이하 | 사용자 선택 (체크박스) |
| user_id (광고주) | Integer | 필수 | 로그인된 광고주 | 세션/인증 토큰 |

### 6.2. 출력 데이터 (Output Data)

#### 6.2.1. 성공 응답
```json
{
  "success": true,
  "message": "체험단 선정이 완료되었습니다.",
  "data": {
    "campaign_id": 123,
    "selected_count": 3,
    "rejected_count": 7,
    "campaign_status": "selection_complete"
  }
}
```

#### 6.2.2. 실패 응답
```json
{
  "success": false,
  "error_code": "EXCEEDS_RECRUITMENT_COUNT",
  "message": "모집 인원(5명)을 초과하여 선택할 수 없습니다. 현재 7명이 선택되었습니다.",
  "data": {
    "recruitment_count": 5,
    "selected_count": 7
  }
}
```

### 6.3. 데이터베이스 변경사항

#### 6.3.1. proposals 테이블 업데이트

**선정된 지원자**:
- `status`: 'submitted' → 'selected'
- `updated_at`: 현재 시각으로 갱신

**반려된 지원자**:
- `status`: 'submitted' → 'rejected'
- `updated_at`: 현재 시각으로 갱신

#### 6.3.2. campaigns 테이블 업데이트

**캠페인 상태 변경**:
- `status`: 'recruitment_ended' → 'selection_complete'
- `updated_at`: 현재 시각으로 갱신

---

## 7. UI/UX 요구사항

### 7.1. UI 컴포넌트

#### 7.1.1. 체험단 선정 버튼
- **위치**: 광고주용 체험단 상세 페이지, 지원자 목록 상단
- **표시 조건**:
  - 캠페인 상태가 '모집 종료'일 때만 표시
  - 지원자가 1명 이상 존재할 때만 활성화
- **스타일**: Primary 버튼 (강조 색상)
- **레이블**: "체험단 선정"

#### 7.1.2. 선정 다이얼로그 (모달)
- **크기**: 중간 크기 (최대 너비 800px)
- **제목**: "체험단 선정 (모집인원: N명)"
- **본문**:
  - 지원자 목록 테이블
    - 체크박스 (전체 선택/해제 기능 포함)
    - 인플루언서 이름
    - SNS 채널 링크 (클릭 가능)
    - 각오 한마디 (요약, 전체 보기 옵션)
    - 방문 희망일
  - 하단 정보: "현재 N/M명 선택됨"
- **액션 버튼**:
  - "취소" (보조 버튼)
  - "선정 완료" (주 버튼)

#### 7.1.3. 확인 다이얼로그
- **제목**: "체험단 선정 확인"
- **메시지**: "선정된 N명에게 선정 알림이 전달되며, 나머지는 반려 처리됩니다. 계속하시겠습니까?"
- **액션 버튼**:
  - "아니오" (보조 버튼)
  - "예, 선정합니다" (주 버튼, 위험 색상)

#### 7.1.4. 성공/오류 피드백
- **타입**: Toast 메시지 또는 Alert
- **표시 시간**: 3-5초 자동 사라짐
- **위치**: 화면 상단 중앙
- **성공 예시**: "체험단 선정이 완료되었습니다." (녹색)
- **오류 예시**: "모집 인원을 초과하여 선택할 수 없습니다." (빨간색)

### 7.2. UX 플로우

#### 7.2.1. 로딩 상태 표시
- '선정 완료' 버튼 클릭 시 즉시 로딩 상태로 전환
- 버튼 레이블: "선정 완료" → "처리 중..."
- 버튼 비활성화 및 로딩 스피너 표시
- 중복 클릭 방지

#### 7.2.2. 선택 인원 실시간 안내
- 체크박스 선택/해제 시 즉시 선택 인원 카운트 업데이트
- 모집 인원 초과 시 시각적 경고 표시 (빨간색 텍스트)
- 예: "현재 7/5명 선택됨 (초과)"

#### 7.2.3. 선정 완료 후 상태
- 페이지 새로고침으로 최신 상태 반영
- '체험단 선정' 버튼 → 비활성화 또는 "선정 완료됨" 레이블로 변경
- 지원자 목록에 각 상태 뱃지 표시:
  - 선정: 녹색 뱃지 "선정됨"
  - 반려: 회색 뱃지 "반려됨"

---

## 8. 기술 명세 (Technical Specifications)

### 8.1. API 엔드포인트

#### 8.1.1. 체험단 선정 API

**요청**:
```
POST /manage/campaigns/{campaign_id}/select-influencers/
Content-Type: application/json

{
  "selected_proposal_ids": [12, 34, 56]
}
```

**응답 (성공)**:
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "체험단 선정이 완료되었습니다.",
  "data": {
    "campaign_id": 123,
    "selected_count": 3,
    "rejected_count": 7,
    "campaign_status": "selection_complete"
  }
}
```

**응답 (실패 - 모집 인원 초과)**:
```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "success": false,
  "error_code": "EXCEEDS_RECRUITMENT_COUNT",
  "message": "모집 인원(5명)을 초과하여 선택할 수 없습니다.",
  "data": {
    "recruitment_count": 5,
    "selected_count": 7
  }
}
```

**응답 (실패 - 권한 없음)**:
```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "success": false,
  "error_code": "PERMISSION_DENIED",
  "message": "해당 작업을 수행할 권한이 없습니다."
}
```

### 8.2. 서비스 계층 구현 가이드

#### 8.2.1. InfluencerSelectionService

**파일 위치**: `apps/campaigns/services/influencer_selection.py`

**주요 메서드**:
```python
class InfluencerSelectionService:
    def execute(
        self,
        user: User,
        campaign_id: int,
        selected_proposal_ids: List[int]
    ) -> InfluencerSelectionResultDTO:
        """
        체험단 선정 비즈니스 로직 실행

        Args:
            user: 현재 로그인된 광고주
            campaign_id: 대상 캠페인 ID
            selected_proposal_ids: 선정할 지원자 ID 목록

        Returns:
            InfluencerSelectionResultDTO: 선정 결과

        Raises:
            PermissionDenied: 권한이 없는 경우
            InvalidCampaignStatus: 캠페인 상태가 '모집 종료'가 아닌 경우
            ExceedsRecruitmentCount: 모집 인원을 초과한 경우
            NoProposalSelected: 선택된 지원자가 없는 경우
        """
```

**검증 로직 순서**:
1. 권한 검증: 캠페인 소유자 확인
2. 상태 검증: 캠페인 상태가 'recruitment_ended'인지 확인
3. 선정 인원 검증:
   - 최소 1명 이상 선택되었는지 확인
   - 모집 인원 이하인지 확인
   - 선택된 proposal_id가 모두 해당 캠페인의 지원자인지 확인

**트랜잭션 처리**:
```python
from django.db import transaction

@transaction.atomic
def execute(self, user, campaign_id, selected_proposal_ids):
    # 1. 캠페인 조회 및 검증
    campaign = Campaign.objects.select_for_update().get(id=campaign_id)

    # 2. 권한 및 상태 검증
    self._validate_permissions(user, campaign)
    self._validate_campaign_status(campaign)
    self._validate_selection_count(campaign, selected_proposal_ids)

    # 3. 선정 처리
    selected_count = Proposal.objects.filter(
        id__in=selected_proposal_ids,
        campaign=campaign
    ).update(status='selected', updated_at=timezone.now())

    # 4. 반려 처리
    rejected_count = Proposal.objects.filter(
        campaign=campaign,
        status='submitted'
    ).exclude(
        id__in=selected_proposal_ids
    ).update(status='rejected', updated_at=timezone.now())

    # 5. 캠페인 상태 업데이트
    campaign.status = 'selection_complete'
    campaign.save()

    # 6. 결과 DTO 반환
    return InfluencerSelectionResultDTO(
        campaign_id=campaign.id,
        selected_count=selected_count,
        rejected_count=rejected_count,
        campaign_status=campaign.status
    )
```

### 8.3. DTO 정의

**파일 위치**: `apps/campaigns/dto.py`

```python
from dataclasses import dataclass
from typing import List

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
```

### 8.4. 데이터베이스 쿼리 최적화

#### 8.4.1. 선정 가능 여부 확인 쿼리
```python
# 캠페인 조회 시 지원자 수도 함께 조회
campaign = Campaign.objects.annotate(
    total_proposals=Count('proposals')
).select_related('advertiser').get(id=campaign_id)
```

#### 8.4.2. 벌크 업데이트 사용
- 개별 `save()` 호출 대신 `update()` 메서드 사용
- 선정/반려 처리 시 단일 쿼리로 일괄 업데이트

#### 8.4.3. 락(Lock) 처리
- `select_for_update()`를 사용하여 동시성 이슈 방지
- 캠페인 조회 시 행(Row) 레벨 락 적용

---

## 9. 테스트 시나리오 (Test Scenarios)

### 9.1. 단위 테스트 (Unit Tests)

#### 9.1.1. InfluencerSelectionService 테스트

**테스트 케이스**:
1. **정상 선정 처리**
   - Given: 모집 종료 상태의 캠페인, 5명 모집에 10명 지원
   - When: 3명 선정
   - Then: 3명 'selected', 7명 'rejected', 캠페인 'selection_complete'

2. **모집 인원 정확히 선정**
   - Given: 5명 모집에 10명 지원
   - When: 정확히 5명 선정
   - Then: 정상 처리

3. **모집 인원 초과 선정**
   - Given: 5명 모집에 10명 지원
   - When: 7명 선정 시도
   - Then: ExceedsRecruitmentCount 예외 발생

4. **아무도 선정하지 않음**
   - Given: 10명 지원
   - When: 0명 선정
   - Then: NoProposalSelected 예외 발생

5. **권한 없는 광고주**
   - Given: 다른 광고주가 생성한 캠페인
   - When: 선정 시도
   - Then: PermissionDenied 예외 발생

6. **잘못된 캠페인 상태**
   - Given: '모집 중' 상태의 캠페인
   - When: 선정 시도
   - Then: InvalidCampaignStatus 예외 발생

7. **이미 선정 완료된 캠페인**
   - Given: '선정 완료' 상태의 캠페인
   - When: 재선정 시도
   - Then: InvalidCampaignStatus 예외 발생

### 9.2. 통합 테스트 (Integration Tests)

#### 9.2.1. API 엔드포인트 테스트

**테스트 케이스**:
1. **정상 선정 요청**
   - Given: 인증된 광고주, 모집 종료 캠페인, 유효한 선정 인원
   - When: POST /manage/campaigns/{id}/select-influencers/
   - Then: HTTP 200, 성공 응답, DB 상태 변경 확인

2. **잘못된 요청 데이터**
   - Given: 빈 selected_proposal_ids
   - When: POST 요청
   - Then: HTTP 400, 에러 메시지

3. **인증되지 않은 요청**
   - Given: 로그아웃 상태
   - When: POST 요청
   - Then: HTTP 401, 로그인 페이지로 리디렉션

4. **권한 없는 요청**
   - Given: 다른 광고주로 로그인
   - When: POST 요청
   - Then: HTTP 403

### 9.3. UI/UX 테스트

#### 9.3.1. 수동 테스트 체크리스트

- [ ] '체험단 선정' 버튼이 올바른 조건에서만 표시되는가?
- [ ] 선정 다이얼로그가 올바르게 열리고 지원자 목록이 표시되는가?
- [ ] 체크박스로 지원자를 선택/해제할 수 있는가?
- [ ] 선택 인원 카운트가 실시간으로 업데이트되는가?
- [ ] 모집 인원 초과 시 시각적 경고가 표시되는가?
- [ ] 확인 다이얼로그가 올바른 메시지로 표시되는가?
- [ ] 로딩 상태가 표시되고 중복 클릭이 방지되는가?
- [ ] 선정 완료 후 페이지가 올바르게 갱신되는가?
- [ ] 성공/오류 메시지가 올바르게 표시되는가?
- [ ] 선정 후 인플루언서의 '내 지원 목록'에서 상태 변경이 확인되는가?

---

## 10. 의존성 및 연관 기능 (Dependencies)

### 10.1. 선행 유스케이스
이 유스케이스를 실행하기 전에 완료되어야 하는 기능:

1. **UC-01: 광고주 회원가입** - 광고주 계정이 존재해야 함
2. **UC-05: 신규 체험단 등록** - 캠페인이 생성되어 있어야 함
3. **UC-06: 모집 마감 처리** - 캠페인 상태가 '모집 종료'여야 함
4. **UC-03: 체험단 지원** - 1명 이상의 지원자가 존재해야 함

### 10.2. 후속 유스케이스
이 유스케이스 실행 후 가능해지는 기능:

1. **UC-08: 인플루언서 지원 결과 확인** - 인플루언서가 '내 지원 목록'에서 선정/반려 상태 확인
2. **(향후) UC-09: 체험단 활동 관리** - 선정된 인플루언서의 체험 활동 추적
3. **(향후) UC-10: 리뷰 수집 및 리포팅** - 체험 후 리뷰 콘텐츠 수집

### 10.3. 외부 연동
현재 MVP 단계에서는 외부 연동이 없으나, 향후 고려사항:

- 알림 서비스: 선정/반려 시 이메일 또는 SMS 알림 발송
- 분석 서비스: 선정률, 평균 지원자 수 등 통계 데이터 수집

---

## 11. 성능 요구사항 (Performance Requirements)

### 11.1. 응답 시간
- 선정 다이얼로그 표시: 1초 이내
- 선정 처리 완료: 3초 이내 (지원자 100명 기준)
- 페이지 새로고침: 2초 이내

### 11.2. 동시성
- 동일 캠페인에 대한 동시 선정 요청 처리: 첫 요청만 성공, 나머지 거부
- 데이터베이스 락 대기 시간: 최대 5초

### 11.3. 확장성
- 지원자 수: 최대 1,000명까지 안정적 처리
- 벌크 업데이트 쿼리: 단일 트랜잭션으로 처리

---

## 12. 보안 요구사항 (Security Requirements)

### 12.1. 인증 (Authentication)
- 로그인된 사용자만 선정 기능에 접근 가능
- 세션 또는 토큰 기반 인증 필수

### 12.2. 권한 (Authorization)
- 캠페인 소유자만 선정 가능 (소유권 검증 필수)
- URL 직접 접근 시에도 권한 검증

### 12.3. 입력 검증 (Input Validation)
- selected_proposal_ids: 정수 배열 형식 검증
- campaign_id: 양의 정수 검증
- SQL Injection 방지: ORM 쿼리 사용

### 12.4. CSRF 보호
- Django CSRF 토큰 필수
- POST 요청에 CSRF 토큰 포함

### 12.5. 데이터 무결성
- 트랜잭션 원자성 보장
- 중복 선정 방지 (상태 검증)

---

## 13. 문서 변경 이력 (Revision History)

| 버전 | 날짜 | 작성자 | 변경 내용 |
|---|---|---|---|
| 1.0 | 2025-11-16 | System | 초안 작성 - userflow.md 기반 상세 명세 |

---

## 14. 부록 (Appendix)

### 14.1. 용어 정의 (Glossary)

- **체험단**: 특정 제품이나 서비스를 체험하고 홍보하는 인플루언서 그룹
- **선정 (Selection)**: 지원자 중 최종 체험단 멤버를 결정하는 행위
- **반려 (Rejection)**: 지원자를 체험단에 선정하지 않는 행위
- **모집 인원 (Recruitment Count)**: 캠페인에서 선정할 예정인 체험단 인원 수
- **트랜잭션 (Transaction)**: 여러 데이터베이스 작업을 하나의 단위로 묶어 원자성을 보장하는 처리 방식

### 14.2. 참고 자료 (References)

- `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\userflow.md`
- `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\database.md`
- `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\structure.md`
- `C:\Users\P\Desktop\Seongho\03_개인공부\vibecoding\커서맛피아\03_study\01_vcm1-1\docs\prd.md`

### 14.3. 상태 다이어그램

```
[모집 중]
   ↓ (모집 마감 - UC-06)
[모집 종료]
   ↓ (체험단 선정 - UC-07 ★현재 문서)
[선정 완료]
   → (더 이상 상태 변경 불가)

지원자 상태:
[신청 완료] → [선정] (선택된 지원자)
            → [반려] (선택되지 않은 지원자)
```
