# Codespaces 필수 실행환경 결정

- 결정일: 2026-09-21
- 승인자: Project owner
- 적용 시점: Task `0.1B-R1` 병합 이후 생성·착수하는 모든 작업

## 결정

모든 작업자와 에이전트 인스턴스는 GitHub Codespaces에서 저장소의 `.devcontainer/devcontainer.json`을 사용한다. 로컬 host clone은 작업 파일 운반이나 Git 조회에 사용할 수 있지만 구현·검사 환경으로 사용할 수 없다.

작업자는 편집 전에 Codespaces 이름, `CODESPACES=true`, branch와 HEAD, devcontainer 경로 및 주요 도구 버전을 progress/evidence에 기록한다. 이 증거가 없으면 `working`으로 전환하지 않고 `blocked`로 보고한다.

## 예외

로컬 실행 예외는 작업 시작 전에 owner가 승인하고 이 디렉터리의 결정 기록과 TASK_BOARD에 사유·기간·동등성 검사를 기록한 경우에만 유효하다. 사후 예외 승인은 허용하지 않는다.

Task `0.1B-R1`은 이 정책 확정 전에 로컬 macOS에서 완료됐다. owner가 PR #8의 diff·evidence를 M이 재검증한 뒤 병합하도록 명시 승인했으므로 이 작업에 한해 마지막 1회 예외로 인정한다. PR #8 이후 작업에는 이 예외가 적용되지 않는다.

## 완료 게이트

M은 환경 증거 또는 사전 승인된 예외가 없는 결과를 `verified`나 `done`으로 확정하지 않는다. M Monitor는 active task의 환경 필드 누락을 경고한다.
