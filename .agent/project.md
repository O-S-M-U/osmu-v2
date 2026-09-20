# O.S.M.U v2 프로젝트 계약

## 목표

하나의 키워드에서 검증 가능한 근거 묶음을 만들고, 이를 티스토리·워드프레스·네이버 블로그용 콘텐츠로 변환해 검사·승인·발행·원격 재확인한다.

## 기준선

1. `docs/baseline/MODULE_SPEC_20260522_v23.md`
2. `docs/baseline/워크플로우_시각화_20260522_v19.html`
3. 사용자가 승인한 `docs/decisions/` 기록

기준 문서가 충돌하면 임의로 하나를 선택하지 않는다. `decision_required` 상태로 올리고 결정 기록이 생길 때까지 관련 구현을 멈춘다.

## 완료 정의

2단계 완료는 다음 조건을 모두 만족한 상태다.

- MODULE_SPEC의 모든 규범 요구사항에 고유 ID가 있다.
- 각 요구사항이 구현, 검사, 증거 또는 명시적 보류 결정에 연결된다.
- 티스토리·워드프레스·네이버 블로그에서 같은 원천의 채널별 결과를 확인한다.
- 승인된 revision만 발행되고, 발행 결과를 원격에서 다시 읽어 확인한다.
- 부분 실패, 재개, 중복 방지, 시크릿 제외가 검증된다.
- 요구사항 추적표의 미충족 항목이 0개다.

## 작업 단위

모든 작업은 `docs/planning/OSMU_V2_WORK_ORDER.md`의 ID를 사용한다. 한 작업에는 한 명의 주 담당자와 한 개의 작업 브랜치만 둔다. 예상 토큰 상한이 담당자의 안전 할당량보다 크면 작업을 시작하기 전에 하위 작업으로 나눈다.

## 계획·상태 계층

```text
MODULE_SPEC → WORK_ORDER → TASK_BOARD.yaml
```

`MODULE_SPEC`은 제품 요구사항과 품질 기준, `WORK_ORDER`는 요구사항을 실현하는 작업 분할·의존성·예상량, `TASK_BOARD.yaml`은 담당자·브랜치·상태·PR·증거를 기록한다. `docs/requirements/TRACEABILITY.md`는 요구사항 ID와 작업·검사·증거를 연결한다.

## 공통 실행환경

작업자는 GitHub Codespaces의 저장소 공통 dev container를 우선 사용한다. Codespace는 실행환경을 통일하고 branch는 작업 결과를 분리한다. `.devcontainer/` 설정이 없거나 불완전하면 작업을 임의로 시작하지 않고 환경 준비 변경을 별도 작업으로 요청한다.

## 상태 전이

기본 흐름은 `planned → ready → claimed → working → review → pr → verified → done`이다. 작업 중 실행 장애는 `blocked`, 명세·범위 판단은 `decision_required`로 기록한다. `verified`와 `done`은 M만 증거 조건을 확인한 뒤 확정하며, 공식 상태는 병합된 `main`의 TASK_BOARD가 결정한다.

## 공유 기록

Git의 `main`과 아래 파일이 유일한 공유 기준이다. 에이전트 대화 기억은 기준이 아니다.

- `project/TASK_BOARD.yaml`: 작업 상태와 배정
- `.agent/workers.yaml`: 작업자와 할당량 현황
- `docs/requirements/TRACEABILITY.md`: MODULE_SPEC 전수 추적
- `docs/coordination/STATUS.md`: 관리자 에이전트의 통합 보고
- `docs/progress/`: 작업자별 진행 기록
- `evidence/`: 검사와 외부 검증 증거
