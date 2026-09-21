# Task 0.1B-R1 — 범위·읽기전용 경로 독립 검증

실행 환경: 로컬 macOS host, git CLI. 실행 시각: 2026-09-21 18:30–18:55 KST 경.

## 1. 작업 branch가 현재 main과 일치하는지 확인

```sh
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

결과: 둘 다 `c7fd647b242ef36df68a7c80f420b00ebaf7e46a`로 일치. `agent/worker-d/0.1b-r1-version-procedure`는 이 SHA로 fast-forward된 상태에서 작업을 시작했다. (T-0.1B-R1.md에 기록된 배정 도출 기준 `90685947baed2c0cdbbab7f02bc7cd7ff4b48189`은 PR #6/#7 병합 이전 값이며, `branch_start_policy: fast_forward_to_current_main_before_work`에 따라 최신 main으로 갱신한 뒤 시작했다.)

## 2. 0.1B가 실제로 병합한 diff의 정확한 범위

병합 커밋 `7a7ff85030b879530b8078be1bbbfd24ee71ad2c`의 두 부모:

```sh
git log -1 --format='%P' 7a7ff85030b879530b8078be1bbbfd24ee71ad2c
# => 06913adeada511aadb8a946813d266b2f0d07b20 cd88ac67ed0a1665e8bda27a1f0dba7b3879035a
```

`06913ad`는 PR #4가 rebase된 실제 main 기준점(PR #3 병합 직후), `cd88ac6`는 0.1B 작업 branch의 마지막 커밋이다. 이 두 지점 사이의 diff만이 0.1B 작업이 실제로 만든 변경이다.

```sh
git diff --name-only 06913adeada511aadb8a946813d266b2f0d07b20 cd88ac67ed0a1665e8bda27a1f0dba7b3879035a
```

결과:
```
docs/progress/20260915.md
docs/requirements/BASELINE.md
project/TASK_BOARD.yaml
```

`T-0.1B.md`의 `allowed_paths`(`docs/requirements/BASELINE.md`, `docs/progress/20260915.md`, `project/TASK_BOARD.yaml`)와 정확히 일치하고 그 외 경로는 없다.

주의: `357adfea34226f3141d7bb17a70daf629ad95660`(0.1B의 원래 claim 시점 기준 revision)를 직접 기준점으로 diff를 뜨면 그 사이에 병합된 PR #2·#3(운영 문서, devcontainer, Agent Workforce Monitor 등 무관한 변경)까지 섞여 나와 범위를 과대평가하게 된다. 위와 같이 0.1B 자신의 실제 rebase 기준(`06913ad`)을 써야 정확하다.

## 3. 읽기 전용 경로 변경 여부

```sh
git diff --exit-code 06913adeada511aadb8a946813d266b2f0d07b20 cd88ac67ed0a1665e8bda27a1f0dba7b3879035a -- docs/baseline docs/decisions .agent
```

종료 코드 0 (diff 없음) — `docs/baseline/**`, `docs/decisions/**`, `.agent/**` 모두 0.1B 작업 범위에서 변경되지 않았다.

## 4. BASELINE.md 변경이 순수 추가(append)인지 확인

```sh
git diff 06913adeada511aadb8a946813d266b2f0d07b20 cd88ac67ed0a1665e8bda27a1f0dba7b3879035a -- docs/requirements/BASELINE.md | grep -c '^-[^-]'
```

결과: `0` — 제거되거나 수정된 줄이 없다. 0.1A가 고정한 `## 기준 파일`, `## 기준 우선순위` 절은 그대로이고 `### 버전 변경·결정 절차` 이하가 새로 추가됐다.

## 5. docs/progress/20260915.md 변경이 순수 추가인지 확인

동일 커밋 범위에서 해당 파일 diff를 확인한 결과, 기존 "Worker C 도입과 TASK 0.1B 배정" 절은 그대로이고 `## TASK 0.1B — 버전 변경·결정 절차 확정` 절이 새로 추가됐다(기존 줄 삭제 없음).

## 6. Task 0.1B-R1 자신의 읽기 전용 준수 확인 (작업 완료 직전 재확인)

```sh
git status --porcelain
```

`docs/baseline/`, `docs/decisions/`, `.agent/`, `docs/requirements/TRACEABILITY.md` 경로에 대한 수정이 없음을 커밋 직전에 다시 확인했다(아래 progress 기록의 검사 절 참조).
