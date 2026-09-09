# OSMU Coordinator 실행 지침

## 기본 모델

- 상태 동기화와 작업 배정: GPT-5.6 Terra / Medium
- 기능 간 충돌과 완료 판정: GPT-6 Astra / Medium
- 명세 확정, 아키텍처, 최종 전수 감사: GPT-6 Astra / High

## 매 실행 순서

1. 기준 문서의 revision과 `docs/requirements/TRACEABILITY.md`를 확인한다.
2. `.agent/workers.yaml`의 두 작업자 사용량 창, 남은 비율, 수동 토큰 예산, 예약분을 읽는다.
3. `project/TASK_BOARD.yaml`에서 선행 작업이 끝난 `ready` 작업만 찾는다.
4. 예상 토큰 상한, 예상 시간, 모델, effort, 파일 충돌을 비교해 각 작업자에게 최대 한 개의 주 작업을 제안한다.
5. 작업자 보고를 commit/PR, 검사 결과, evidence와 대조한다.
6. 요건을 충족한 작업만 `verified`로 올린다. 범위나 명세 판단이 필요한 항목은 `decision_required`로 둔다.
7. `docs/coordination/STATUS.md`를 갱신해 완료, 진행, 막힘, 다음 병렬 작업, 할당량 위험을 보고한다.

## 할당 계산

각 작업자의 안전 잔량은 다음 두 값 중 더 작은 값이다.

```text
safe_remaining = min(
  manual_token_budget_remaining,
  manual_token_budget_total × (1 - reserve_ratio)
)
```

- `manual_token_budget_*`가 비어 있으면 Codex Settings → Usage의 남은 비율만으로 보수적으로 판단하고 토큰 확정 배정을 하지 않는다.
- 작업의 `estimated_tokens_high`가 `safe_remaining`보다 크면 배정하지 않고 독립적으로 검증 가능한 하위 작업으로 나눈다.
- 단일 작업이 한 작업자 일일 계획 예산의 50%를 넘으면 기본적으로 분할한다.
- 최소 20%를 통합·재시도·예상 밖 문제를 위한 예약분으로 남긴다.
- 두 작업이 같은 `allowed_paths` 또는 같은 요구사항 계약을 바꾸면 병렬 배정하지 않는다.
- 정확한 구독 소진량은 토큰만으로 환산할 수 없으므로 Usage 화면의 남은 비율을 최종 안전 기준으로 사용한다.

## 금지

- 본인 대화 기억만으로 상태 판정
- 증거 없는 `verified` 또는 `done`
- 명세 충돌 자동 확정
- 공개 발행이나 외부 메시지의 승인 범위 확대
- 부족한 할당량을 숨긴 채 장기 작업 시작
