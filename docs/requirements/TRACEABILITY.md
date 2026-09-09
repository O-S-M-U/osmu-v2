# MODULE_SPEC 요구사항 추적표

기준: `docs/baseline/MODULE_SPEC_20260522_v23.md`

이 문서는 작업 `0.2`에서 전수 작성한다. 제목 단위 요약이 아니라 입력, 출력, 로직, DB 갱신 시점, 오류·fallback, 정책 게이트, 오픈 이슈까지 원자화한다.

## 상태 값

- `unmapped`: 원문 위치만 확인
- `specified`: v2 동작이 확정됨
- `implemented`: 구현 연결됨
- `tested`: 검사 연결됨
- `verified`: 증거까지 확인됨
- `deferred`: 승인된 보류 결정이 있음
- `decision_required`: 충돌 또는 모호성으로 결정 필요

## 추적표

| Requirement ID | 원문 위치 | 규범 요구사항 | v2 적용 방식 | 작업 ID | 구현 | 검사 | 증거 | 상태 | 결정 기록 |
|---|---|---|---|---|---|---|---|---|---|
| 예: REQ-KR-001 | §1.2 | 입력 계약을 충족한다 | 미작성 | 2.1, 3.1 |  |  |  | unmapped |  |

## 전수 감사

| 항목 | 값 |
|---|---:|
| 전체 요구사항 | 0 |
| specified | 0 |
| implemented | 0 |
| tested | 0 |
| verified | 0 |
| deferred | 0 |
| decision_required | 0 |
| 미연결 | 0 |

완료 조건은 `verified + deferred = 전체 요구사항`, `decision_required = 0`, `미연결 = 0`이다. `deferred`에는 반드시 사용자가 승인한 결정 기록을 연결한다.
