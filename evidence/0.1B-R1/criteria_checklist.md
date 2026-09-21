# Task 0.1B-R1 — 독립 수용 기준 재검증

Worker D가 기존 PR #4의 결론을 전제하지 않고, `.agent/tasks/T-0.1B.md`에 적힌 원래 `0.1B` 통과 기준을 현재 `main`(`c7fd647b242ef36df68a7c80f420b00ebaf7e46a`)의 `docs/requirements/BASELINE.md`에 대해 항목별로 독립 도출·대조한 기록이다.

## 원래 0.1B 통과 기준과 대조 결과

1. **"BASELINE.md에 새 버전 생성, 결정 기록 연결, 승인 게이트, 기준선 교체, 이전 기준선 보존 절차가 순서대로 적혀 있다."**
   - `docs/requirements/BASELINE.md`의 `### 버전 변경·결정 절차`는 다음 7단계로 되어 있다: `1. 변경 제안 등록`, `2. 제안본 생성`, `3. 결정 기록 연결`, `4. 승인 게이트`, `5. 새 기준선 검증`, `6. 기준선 교체`, `7. 이전 기준선 보존`.
   - 기준의 5개 필수 절차(새 버전 생성=2, 결정 기록 연결=3, 승인 게이트=4, 기준선 교체=6, 이전 기준선 보존=7)가 요구된 순서 그대로 나타난다. 사이에 추가된 `1. 변경 제안 등록`과 `5. 새 기준선 검증`은 필수 순서를 깨지 않는 보완 단계다.
   - 판정: **충족**.

2. **"충돌·모호성은 구현자가 임의 해석하지 않고 decision_required로 올리도록 명시한다."**
   - 절차 1단계: "기준 문서와의 충돌, 모호성 또는 변경 필요성을 발견한 작업자는 관련 작업을 `decision_required`로 바꾸고 ... 구현자는 이 단계에서 어느 해석도 임의로 선택하지 않는다."
   - 문서 상단 `## 기준 우선순위` 3항에도 동일 원칙이 별도로 명시되어 있어 이중으로 확인된다.
   - 판정: **충족**.

3. **"승인 전 제안 문서와 승인된 새 기준 문서를 구분한다."**
   - 2단계: "승인 전 파일에는 `proposal` 상태를 명시하며 기준 문서로 인용하지 않는다."
   - 4단계: "사용자 승인과 결정 기록이 모두 확인되기 전에는 제안본을 승인된 기준 문서로 표시하거나 구현·검사의 기준으로 사용하지 않는다. 반려 또는 미결인 제안은 `proposal` 또는 `decision_required` 상태를 유지한다."
   - 판정: **충족**.

4. **"기준 사본과 기존 결정 기록을 변경하지 않았음을 검사한다."**
   - 독립 재검증(`scope_verification.md` 참조): 0.1B의 실제 병합 diff(`06913adeada511aadb8a946813d266b2f0d07b20` → `cd88ac67ed0a1665e8bda27a1f0dba7b3879035a`)는 `docs/requirements/BASELINE.md`, `docs/progress/20260915.md`, `project/TASK_BOARD.yaml` 세 파일만 건드렸고 `docs/baseline/**`, `docs/decisions/**`, `.agent/**`는 0바이트 diff다.
   - `BASELINE.md` diff는 제거된 줄이 0줄인 순수 추가(append)였다 — 0.1A가 고정한 `## 기준 파일`, `## 기준 우선순위` 표를 수정하지 않았다.
   - 판정: **충족** (Worker D가 원본 diff를 재계산해 독립적으로 확인).

5. **"Windows에서 실행한 검사 명령과 경로 차이가 있으면 진행 기록에 남긴다."**
   - `docs/progress/20260915.md`의 `### 검사와 증거`에 PowerShell `Get-FileHash`, CRLF 변환으로 인한 파일 크기·해시 차이(96,244/88,939 bytes vs Git blob 원시 94,946/87,841 bytes), 한글 경로 콘솔 출력 깨짐, PyYAML 부재로 인한 대체 검사 방법이 모두 기록되어 있다.
   - 판정: **충족**.

6. **"docs/progress/20260915.md에 결과·증거·다음 시작점을 기록한다."**
   - 해당 파일의 `## TASK 0.1B — 버전 변경·결정 절차 확정` 절에 결과, 검사와 증거, 남은 위험과 다음 시작점(Task 0.2 시작 위치)이 모두 있다.
   - 판정: **충족**.

7. **"작업 보드 상태와 evidence를 갱신하고 commit한다."**
   - `project/TASK_BOARD.yaml`의 `0.1B` 항목은 `status: done`, `merged_at`, `merge_commit: 7a7ff85030b879530b8078be1bbbfd24ee71ad2c`, `evidence: [docs/requirements/BASELINE.md, docs/progress/20260915.md]`가 기록되어 있고 상위 `0.1`도 동일 병합 커밋으로 `done` 처리됐다.
   - 판정: **충족**.

## 결론

원래 `0.1B` 수용 기준 7개 항목을 기존 PR #4의 결론을 가정하지 않고 문서 원문과 git 이력에서 독립적으로 재도출한 결과, **7개 항목 모두 충족**하며 Worker C가 남긴 결과와 Worker D의 독립 결론 사이에 실질적 차이가 없다. `docs/requirements/BASELINE.md`, `docs/decisions/`, `docs/baseline/`에 대한 내용 수정은 이번 재검증에서 발생하지 않았다.
