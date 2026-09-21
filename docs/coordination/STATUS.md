# OSMU Coordinator 상태 보고

최종 갱신: 2026-09-21

## 기준선

- MODULE_SPEC: v23 사본 고정
- Workflow: v19 사본 고정
- 멀티채널 v2 명세: 미확정
- 요구사항 원자화: 시작 전
- 기준선 해시 검증: `0.1A` 완료

## 작업자

| 작업자 | 활성 작업 | Usage 확인 | 수동 계획 예산 | 상태 |
|---|---|---|---:|---|
| Chung Yurim / yurim-agent | 없음 | 99% 잔여(Worker C와 공유) | 미입력 | available / primary hold |
| LeeSoMyoung / leesomyoung-agent | 없음 | 미입력 | 미입력 | unavailable |
| Worker C / worker-c-agent | 없음 | 마지막 확인 99% 잔여(Worker A와 공유) | 미입력 | unavailable / 연락 두절 |
| Worker D / worker-d-claude | 0.1B-R1 | 시작 전 확인 필요 | 미입력 | assigned / governance merge 대기 |

## 현재 판정

- `0.1A 기준 문서 식별·해시·우선순위 기록`은 PR #1로 병합됐다.
- 병합 커밋 `a6be97a02583848420817de7f939ae626919a375`의 `main`에서 기준 문서 두 개의 SHA-256과 파일 크기를 다시 확인했고, manifest와 일치했다.
- `docs/baseline/**`에는 `0.1A` 기준 revision 이후 변경이 없다.
- `0.1A`는 `done`이다.
- Worker B는 사용자 전달에 따라 접속이 어려운 상태로 신규 배정을 보류했다.
- Worker C를 Windows worktree 작업자로 등록하고 `0.1B 버전 변경·결정 절차 확정`을 배정했다.
- Worker A와 C는 동일 Codex 계정의 Usage를 공유한다. 현재 주간 창은 1% 사용·99% 잔여지만 수동 토큰 예산이 없으므로 두 작업자에게 병렬 주 작업을 배정하지 않는다.
- `0.1B`는 최대 10K·60분의 짧은 문서 작업으로 제한하며 기준 사본과 기존 결정 기록은 읽기 전용이다.
- `0.1B 버전 변경·결정 절차 확정`은 PR #4로 병합됐고 main 재검증을 마쳐 `done`으로 확정했다.
- PR #3 운영 지침 병합 커밋은 `06913adeada511aadb8a946813d266b2f0d07b20`, PR #4 병합 커밋은 `7a7ff85030b879530b8078be1bbbfd24ee71ad2c`다.
- 2026-09-21 owner 보고에 따라 연락 두절된 Worker C의 활성 배정을 종료했다. 기존 작업 이력은 보존한다.
- Worker D (`worker-d-claude`)를 등록하고 기존 결과를 독립 재검증하는 교정 Task `0.1B-R1`을 배정했다.
- `0.1B-R1` 운영 기록이 main에 병합될 때까지 D는 작업을 시작하지 않으며, 시작 전 context/usage와 observed branch/base를 보고해야 한다.

## 2026-09-16 운영 모델 확정

- 운영환경은 작업자의 호스트 OS가 아니라 저장소의 GitHub Codespaces dev container를 기준으로 통일한다. Branch는 결과 분리용이다.
- 계획 계층은 `MODULE_SPEC → WORK_ORDER → TASK_BOARD.yaml`이며 `TRACEABILITY.md`가 요구사항·작업·검사·증거를 연결한다.
- 상태 흐름은 `planned → ready → claimed → working → review → pr → verified → done`이다. 실행 장애는 `blocked`, 명세·범위 판단은 `decision_required`로 기록한다.
- 작업자는 `review`/`pr`까지 제출하고, M은 diff·검사·증거를 확인한 뒤 `verified`, 병합 후 main 재검증 뒤 `done`을 확정한다.
- 프로젝트 owner는 Module Spec 범위 변경과 필요한 병합 승인을 담당한다. 기존 baseline은 직접 수정하지 않고 결정 기록과 새 버전을 만든다.
- 상세 운영 근거: `docs/decisions/20260916-operation-model.md`

## 2026-09-17 Agent Workforce 스킬 계약 확정

- Agent Workforce는 프로젝트 기획과 분리된 실행·추적·검증 스킬로 확정했다.
- 발동 전 승인된 MODULE_SPEC과 최소 입력 계약을 검증하며, 미흡하면 `decision_required`로 보류한다.
- 상세 계약: `docs/decisions/20260917-agent-workforce-skill-contract.md`
- `.github/workflows/agent-workforce-monitor.yml`이 push·PR·review 이벤트를 캡처한다. `MONITOR_WEBHOOK_URL` 미설정 시 artifact만 보존하며 M 자동 호출은 아직 비활성이다.

## 다음 병렬화 후보

현재 활성 후보는 Worker D의 `0.1B-R1`뿐이다. 이 작업이 verified/done이 될 때까지 `0.2 MODULE_SPEC 전 요구사항 원자화`는 시작하지 않는다. 이후 `0.2`의 예상 상한 65K가 크므로 사용 가능한 작업자 예산을 확인하거나 독립 하위 작업으로 분할한 뒤 배정한다.

## 최신 증거

- PR: https://github.com/O-S-M-U/osmu-v2/pull/1
- 작업 커밋: `62853c23e6b24764c3f23a2c0b71f42e5edba134`
- M 검토 커밋: `9506c4e10c9c2c5ce9d6611986b9d84ac55be093`
- 병합 커밋: `a6be97a02583848420817de7f939ae626919a375`
- 기준선 기록: `docs/requirements/BASELINE.md`
- Worker C 작업지시서: `.agent/tasks/T-0.1B.md`
- PR #3: https://github.com/O-S-M-U/osmu-v2/pull/3
- PR #4: https://github.com/O-S-M-U/osmu-v2/pull/4
- Worker D 작업지시서: `.agent/tasks/T-0.1B-R1.md`
- 교정 재배정 결정: `docs/decisions/20260921-worker-d-corrective-reassignment.md`
