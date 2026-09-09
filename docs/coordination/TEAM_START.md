# A·M·B 협업 시작 안내

## 역할

- 작업자 A: Yurim (`yurim-agent`)
- 중간관리자 M: OSMU Coordinator
- 작업자 B: LeeSoMyoung (`leesomyoung-agent`)

M은 상시 실행되는 서버가 아니다. A 또는 B가 Codex에서 `.agent/prompts/coordinator.md`를 읽혀 호출하는 역할이다. M의 기억 대신 GitHub `main`, 작업 보드, PR, evidence를 공유 상태로 사용한다.

초기에는 A가 M의 운영자를 맡는다. B는 M이 `main`의 작업 보드에 배정한 작업을 확인한 뒤 작업자 에이전트를 실행한다. A가 없는 동안 B가 M을 호출할 수 있지만, 먼저 최신 `main`을 받아 다른 M 실행이나 새 배정이 없는지 확인한다.

## 1. 작업 전 Usage 체크인

각 작업자는 자기 계정의 Codex Settings → Usage를 확인한다. M은 다른 사람 계정의 잔량을 자동으로 볼 수 없으므로 다음 값을 직접 전달해야 한다.

```text
작업자: A 또는 B
5시간 창 잔여 비율:
주간 잔여 비율:
다음 reset 시각:
오늘 작업 가능 시간:
이번 할당에 사용할 최대 계획 토큰:
```

정확한 계획 토큰을 정하기 어렵다면 비워 두고 잔여 비율과 가능 시간만 전달한다. 이 경우 M은 짧은 작업을 제안하고 큰 작업을 나눈다.

## 2. A가 M을 호출하는 방법

현재 프로젝트에 연결된 전용 Codex 작업에서 다음과 같이 요청한다.

```text
M을 호출해. 구현은 시작하지 말고 현재 main과 작업 보드, 요구사항 추적표,
두 작업자의 Usage 체크인을 읽어서 다음 작업을 배정해줘.

A 체크인: <값>
B 체크인: <B가 전달한 값>
```

M은 최신 `main`과 기준 revision, 완료된 의존성, 파일 충돌을 확인한다. 각 작업자의 안전 잔량 안에서 최대 한 개의 주 작업을 골라 작업 보드의 담당자, 에이전트, 상태, 브랜치, 작업 경계를 갱신하고 두 작업자용 지시문을 만든다.

배정이 `main`에 반영된 뒤 작업을 시작한다. 긴 작업은 예상 토큰 상한이 안전 잔량 안에 들어오도록 하위 작업으로 먼저 나눈다.

## 3. 작업자 A의 시작 방법

배정 후 A는 M에게 구현을 계속 시키기보다 별도 작업자 Codex 작업을 사용한다.

```text
나는 작업자 A(yurim)다. AGENTS.md, .agent/project.md, .agent/rules.md,
.agent/prompts/worker.md, project/TASK_BOARD.yaml을 읽어라.
main에 배정된 TASK <ID> 하나만 allowed_paths 안에서 수행하고,
검사·evidence·추적표·실제 시간과 Usage 변화까지 기록해 PR을 준비해라.
```

브랜치 이름은 `agent/yurim/<task-id>-<short-name>`을 사용한다.

## 4. 작업자 B의 최초 준비

B는 GitHub 계정 `LeeSoMyoung`으로 아래 공개 저장소에 접근한다.

https://github.com/O-S-M-U/osmu-v2

Codespace를 쓰는 경우 저장소의 `Code → Codespaces → Create codespace on main`으로 만든다. 로컬에서 작업하면 다음과 같이 준비한다.

```sh
git clone https://github.com/O-S-M-U/osmu-v2.git
cd osmu-v2
git pull --ff-only origin main
```

B가 자기 Codex 작업에 전달할 시작 지시문은 다음과 같다.

```text
나는 작업자 B(leesomyoung)다. AGENTS.md, .agent/project.md, .agent/rules.md,
.agent/prompts/worker.md, project/TASK_BOARD.yaml을 읽어라.
main에서 assignee가 leesomyoung인 TASK <ID> 하나만 allowed_paths 안에서 수행하고,
검사·evidence·추적표·실제 시간과 Usage 변화까지 기록해 PR을 준비해라.
```

브랜치 이름은 `agent/leesomyoung/<task-id>-<short-name>`을 사용한다. B는 `main`에 직접 구현 commit을 올리지 않고 자기 브랜치와 PR을 사용한다.

## 5. 완료와 다음 배정

1. 작업자 에이전트가 코드, 검사, evidence, 추적표와 진행 기록을 commit한다.
2. 작업자가 GitHub PR을 만든다.
3. A가 M을 다시 호출해 PR과 MODULE_SPEC 요구사항을 대조한다.
4. M은 부족한 증거를 `review`로 돌려보내거나 통과 작업을 `verified`로 판정한다.
5. 병합 후 기준 브랜치에서 다시 검사해 `done`으로 바꾼다.
6. 두 작업자가 새 Usage 체크인을 전달하면 M이 다음 작업을 배정한다.

## 첫 실행 권장 순서

1. A가 `0.1 기준 문서 원본 고정·버전 규칙 확정`의 주 담당자가 된다.
2. B는 A의 `0.1` 결과를 독립 검토한다. 같은 파일을 동시에 수정하지 않는다.
3. `0.1` 병합 후 A는 `0.2 MODULE_SPEC 전 요구사항 원자화`, B는 `1.1 티스토리 최소 검증`을 병렬 후보로 검토한다.
4. 실제 배정은 두 작업자의 그날 Usage 잔량과 가능 시간을 받은 뒤 M이 확정한다.

이 첫 실행을 통과한 뒤에는 `project/TASK_BOARD.yaml`의 의존성에 따라 같은 절차를 반복한다.
