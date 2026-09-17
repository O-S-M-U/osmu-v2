# 2026-09-17 Agent Workforce 스킬 계약 확정

## 목적

`Agent Workforce`는 프로젝트 기획 스킬이 아니라, owner가 승인한 프로젝트 계약을 실행·추적·검증하는 재사용 운영 스킬이다.

## 경계

- 프로젝트 기획 논의, 요구사항 우선순위, 범위 결정은 Agent Workforce 밖에서 수행한다.
- 최종 기획은 승인된 `MODULE_SPEC`과 `docs/decisions/` 기록으로 저장한다.
- Agent Workforce는 승인된 명세를 임의로 작성·해석·확정하지 않는다.
- 명세가 없거나 필수 항목이 부족하면 작업 배정 대신 `decision_required`와 보완 목록을 반환한다.

## 발동 입력 계약

### 필수

- `MODULE_SPEC` 파일과 버전
- owner 승인 상태·승인자·승인일
- 프로젝트 목적과 기대 결과물
- 포함 범위와 제외 범위
- 고유 요구사항 ID
- 요구사항별 완료 조건
- 기술·예산·시간·보안 제약
- 외부 서비스·계정·승인 의존성
- 명세 변경과 새 버전 작성 규칙

### 선택

- 기존 저장소·코드
- 기존 `WORK_ORDER`
- 기존 `TASK_BOARD.yaml`
- 작업자/에이전트 목록과 Usage 정보
- 공통 Codespaces 설정

## 실행 계층

```text
MODULE_SPEC (무엇을 만족해야 하는가)
        ↓
WORK_ORDER (어떤 작업으로 실현할 것인가)
        ↓
TASK_BOARD.yaml (현재 누가 어디까지 했는가)
```

`TRACEABILITY.md`는 요구사항 ID와 작업·구현·검사·증거·결정의 연결을 유지한다.

## 에이전트 단위

작업 단위는 사람이 아니라 에이전트 인스턴스다. 한 사람이 여러 에이전트를 실행하더라도 각 인스턴스는 별도 task, Codespace, branch, progress/evidence, PR을 사용한다.

## Monitor 경계

M Monitor는 PR·push·TASK_BOARD 변화의 감지기다. 명세·작업·상태의 권위자가 아니며, 변화가 생기면 새 M 검토 실행을 요청하고 변화가 없으면 조용히 있는다. 실제 검토와 `verified`/`done` 판정은 M이 수행한다.

## 변경 절차

```text
기획 변경 논의(외부)
→ owner 승인
→ docs/decisions 기록
→ 새 MODULE_SPEC 버전
→ WORK_ORDER 영향 분석
→ TASK_BOARD 재계산·재배정
```

기존 baseline은 직접 수정하지 않는다.
