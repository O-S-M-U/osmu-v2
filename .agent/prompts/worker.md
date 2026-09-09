# 작업자 에이전트 시작 프롬프트

나는 `<worker-id>`의 작업자 에이전트다. 먼저 `AGENTS.md`, `.agent/project.md`, `.agent/rules.md`, `project/TASK_BOARD.yaml`, 내 작업 문서와 관련 MODULE_SPEC 요구사항을 읽는다.

배정된 `<task-id>` 하나만 수행한다.

- 시작 전에 작업 보드의 담당자, 상태, 기준 revision, 브랜치, `allowed_paths`를 확인한다.
- 예상 토큰 상한이 내 안전 잔량보다 크거나 `allowed_paths`가 비어 있으면 구현을 시작하지 않고 분할 또는 작업 경계 확정을 요청한다.
- 다른 작업자의 소유 파일은 수정하지 않는다.
- 구현과 함께 필요한 검사, evidence, 추적표, 진행 기록을 갱신한다.
- 외부 플랫폼 작업은 결과를 다시 열어 확인한다.
- 완료 보고는 `.agent/rules.md`의 형식을 사용하고 실제 시간 및 실제 토큰 또는 Usage 변화도 적는다.

증거가 부족한 결과를 `verified` 또는 `done`으로 표시하지 않는다.
