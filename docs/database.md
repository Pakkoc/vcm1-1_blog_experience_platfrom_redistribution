### 데이터베이스 관점의 데이터플로우

사용자의 행동이 데이터베이스에서 어떻게 기록되고 변경되는지에 대한 흐름입니다.

1.  회원가입 (공통)
    *   `users` 테이블에 새로운 레코드 1건이 생성됩니다. `role` 필드에는 'advertiser' 또는 'influencer'가 저장됩니다.
    *   선택한 `role`에 따라, 생성된 `user`의 ID를 참조하는 레코드가 `advertiser_profiles` 또는 `influencer_profiles` 테이블에 각각 1건씩 생성됩니다.

2.  체험단 등록 (광고주)
    *   `campaigns` 테이블에 새로운 레코드 1건이 생성됩니다.
    *   이때, `advertiser_id`에는 현재 로그인한 광고주의 `user` ID가 저장되며, `status`는 'recruiting'(모집 중)으로 초기 설정됩니다.

3.  체험단 지원 (인플루언서)
    *   `proposals` 테이블에 새로운 레코드 1건이 생성됩니다.
    *   이 레코드는 어떤 인플루언서(`influencer_id`)가 어떤 캠페인(`campaign_id`)에 지원했는지 연결하는 역할을 합니다. `status`는 'submitted'(신청완료)로 초기 설정됩니다.

4.  모집 마감 (광고주)
    *   특정 `campaigns` 레코드의 `status` 필드가 'recruiting'에서 'recruitment_ended'(모집 종료)로 UPDATE 됩니다. 이 시점부터 해당 캠페인에 대한 신규 지원(Proposal 생성)은 시스템 로직상 차단되어야 합니다.

5.  체험단 선정 (광고주)
    *   하나의 캠페인에 대해 다수의 레코드가 동시에 변경되는 트랜잭션(Transaction)이 발생합니다.
    *   선정된 지원 건: `proposals` 테이블에서 해당 캠페인에 연결된 레코드 중, 선정된 인플루언서의 레코드 `status`가 'submitted'에서 'selected'(선정)로 UPDATE 됩니다.
    *   반려된 지원 건: 선정되지 않은 나머지 지원자들의 `proposals` 레코드 `status`는 'submitted'에서 'rejected'(반려)로 UPDATE 됩니다.
    *   캠페인 최종 상태 변경: `campaigns` 테이블에서 해당 캠페인의 `status`가 'recruitment_ended'에서 'selection_complete'(선정 완료)로 UPDATE 됩니다.

---

### 최소 스펙 데이터베이스 스키마 (PostgreSQL)

유저플로우에 명시된 데이터를 기반으로, 5개의 핵심 테이블로 구성된 스키마입니다.

*   `users`: 공통 사용자 정보와 역할을 관리합니다.
*   `advertiser_profiles`: 광고주 역할의 추가 정보를 저장합니다.
*   `influencer_profiles`: 인플루언서 역할의 추가 정보를 저장합니다.
*   `campaigns`: 광고주가 등록한 체험단 정보를 관리합니다.
*   `proposals`: 인플루언서의 체험단 지원 정보를 관리합니다.

#### 테이블 상세 구조

1. `users`
*   사용자 계정의 핵심 정보를 담는 테이블.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BIGSERIAL` | `PRIMARY KEY` | 사용자 고유 ID |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | 로그인 ID로 사용될 이메일 |
| `password` | `VARCHAR(255)` | `NOT NULL` | 해싱하여 저장된 비밀번호 |
| `name` | `VARCHAR(100)` | `NOT NULL` | 이름 |
| `contact` | `VARCHAR(20)` | `UNIQUE, NOT NULL` | 연락처 |
| `role` | `user_role` | `NOT NULL` | 사용자 역할 ('advertiser', 'influencer') |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | 계정 생성일 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | 계정 정보 수정일 |

2. `advertiser_profiles`
*   `users` 테이블과 1:1 관계를 가지며, 광고주 전용 정보를 저장.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `BIGINT` | `PRIMARY KEY`, `FOREIGN KEY (users.id)` | `users` 테이블의 ID |
| `company_name` | `VARCHAR(255)` | `NOT NULL` | 업체명 |
| `business_registration_number` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | 사업자등록번호 |

3. `influencer_profiles`
*   `users` 테이블과 1:1 관계를 가지며, 인플루언서 전용 정보를 저장.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `BIGINT` | `PRIMARY KEY`, `FOREIGN KEY (users.id)` | `users` 테이블의 ID |
| `birth_date` | `DATE` | `NOT NULL` | 생년월일 |
| `sns_link` | `VARCHAR(2048)` | `NOT NULL` | SNS 채널 링크 |

4. `campaigns`
*   광고주가 생성하는 체험단(캠페인) 정보를 담는 테이블.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BIGSERIAL` | `PRIMARY KEY` | 캠페인 고유 ID |
| `advertiser_id` | `BIGINT` | `NOT NULL`, `FOREIGN KEY (users.id)` | 캠페인을 등록한 광고주의 ID |
| `name` | `VARCHAR(255)` | `NOT NULL` | 체험단명 |
| `recruitment_start_date` | `DATE` | `NOT NULL` | 모집 시작일 |
| `recruitment_end_date` | `DATE` | `NOT NULL` | 모집 종료일 |
| `recruitment_count` | `INTEGER` | `NOT NULL` | 모집 인원 |
| `benefits` | `TEXT` | `NOT NULL` | 제공 혜택 |
| `mission` | `TEXT` | `NOT NULL` | 미션 |
| `status` | `campaign_status` | `NOT NULL, DEFAULT 'recruiting'` | 캠페인 상태 ('recruiting', 'recruitment_ended', 'selection_complete') |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | 캠페인 생성일 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | 캠페인 정보 수정일 |

5. `proposals`
*   인플루언서가 캠페인에 지원한 정보를 기록하는 테이블.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BIGSERIAL` | `PRIMARY KEY` | 지원 고유 ID |
| `campaign_id` | `BIGINT` | `NOT NULL`, `FOREIGN KEY (campaigns.id)` | 지원한 캠페인 ID |
| `influencer_id` | `BIGINT` | `NOT NULL`, `FOREIGN KEY (users.id)` | 지원한 인플루언서 ID |
| `cover_letter` | `TEXT` | `NOT NULL` | 각오 한마디 |
| `desired_visit_date` | `DATE` | `NOT NULL` | 방문 희망일 |
| `status` | `proposal_status` | `NOT NULL, DEFAULT 'submitted'` | 지원 상태 ('submitted', 'selected', 'rejected') |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | 지원일 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | 지원 정보 수정일 |
| `(UNIQUE)` | `(campaign_id, influencer_id)` | - | 인플루언서가 동일 캠페인에 중복 지원하는 것을 방지 |

---

### 최종 완성본: Migration SQL

아래 SQL 스크립트를 데이터베이스에 실행하면 위에서 설계한 모든 테이블과 관계가 생성됩니다.

```sql
-- migration.sql

-- ENUM 타입 정의: 특정 컬럼에 들어갈 수 있는 값을 명시적으로 제한하여 데이터 무결성을 높입니다.
CREATE TYPE user_role AS ENUM ('advertiser', 'influencer');
CREATE TYPE campaign_status AS ENUM ('recruiting', 'recruitment_ended', 'selection_complete');
CREATE TYPE proposal_status AS ENUM ('submitted', 'selected', 'rejected');

-- 자동 updated_at 갱신을 위한 트리거 함수
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. users: 공통 사용자 테이블
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(20) UNIQUE NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 2. advertiser_profiles: 광고주 프로필 테이블
CREATE TABLE advertiser_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    business_registration_number VARCHAR(50) UNIQUE NOT NULL
);

-- 3. influencer_profiles: 인플루언서 프로필 테이블
CREATE TABLE influencer_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    birth_date DATE NOT NULL,
    sns_link VARCHAR(2048) NOT NULL
);

-- 4. campaigns: 체험단 캠페인 테이블
CREATE TABLE campaigns (
    id BIGSERIAL PRIMARY KEY,
    advertiser_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    recruitment_start_date DATE NOT NULL,
    recruitment_end_date DATE NOT NULL,
    recruitment_count INTEGER NOT NULL,
    benefits TEXT NOT NULL,
    mission TEXT NOT NULL,
    status campaign_status NOT NULL DEFAULT 'recruiting',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON campaigns
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 5. proposals: 체험단 지원 정보 테이블
CREATE TABLE proposals (
    id BIGSERIAL PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    influencer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cover_letter TEXT NOT NULL,
    desired_visit_date DATE NOT NULL,
    status proposal_status NOT NULL DEFAULT 'submitted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- 한 명의 인플루언서는 하나의 캠페인에 한 번만 지원할 수 있도록 UNIQUE 제약조건 추가
    CONSTRAINT unique_campaign_influencer_proposal UNIQUE (campaign_id, influencer_id)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON proposals
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 성능 향상을 위한 인덱스 생성
CREATE INDEX idx_campaigns_advertiser_id ON campaigns(advertiser_id);
CREATE INDEX idx_proposals_campaign_id ON proposals(campaign_id);
CREATE INDEX idx_proposals_influencer_id ON proposals(influencer_id);

```