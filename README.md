# O.S.M.U ver2

2026-09-09부터 시작한 독립 작업 공간입니다. 목표는 하나의 주제·근거 묶음에서 티스토리·워드프레스·네이버 블로그용 콘텐츠를 만들고 대상별 결과까지 확인하는 것입니다.

## 먼저 볼 파일

- `docs/STATUS.md`: 현재 검증 상태와 다음 작업
- `docs/decisions/20260909.md`: 오늘의 결정 및 미결 사항
- `docs/baseline/`: 이전 최신 MODULE_SPEC·워크플로우와 보조 명세의 원본 사본
- `docs/reviews/`: 구현 평가와 멀티채널 개선 제안
- `docs/validation/PLAN.md`: 플랫폼별 검증 순서와 통과 조건
- `docs/IMPORT_MANIFEST.json`: 가져온 파일의 출처·해시
- `docs/planning/OSMU_V2_WORK_ORDER.md`: 작업량·계획·예상 토큰·시간·추천 모델·thinking 표
- `project/TASK_BOARD.yaml`: 두 작업자 에이전트의 배정과 상태를 관리하는 공유 보드
- `.agent/`: 관리자·작업자 역할, 할당량 정책, 작업 템플릿
- `docs/requirements/TRACEABILITY.md`: MODULE_SPEC 전수 반영을 판정하는 요구사항 원장
- `docs/coordination/TEAM_START.md`: 작업자 A·중간관리자 M·작업자 B의 실제 시작 순서

## 바로 실행

Python 3만 있으면 됩니다. 프로젝트 루트에서 실행하세요.

```sh
python3 scripts/prepare_sample.py
```

`artifacts/sample/`에 공통 샘플 HTML, 플랫폼별 작업 패키지와 SHA-256 검증 결과를 만듭니다. HTML은 로컬 브라우저로 열어 비교할 수 있습니다. 이 실행은 외부 연결·로그인·메시지 전송·발행을 하지 않습니다. 네이버용 패키지는 블록 순서를 확인하는 자료이며 HTML 직접 입력을 지원한다고 가정하지 않습니다.

## 기준

기준 문서는 `docs/baseline/MODULE_SPEC_20260522_v23.md`와 `docs/baseline/워크플로우_시각화_20260522_v19.html`입니다. 멀티채널 변경은 아직 제안이며, 합의되면 새 버전 문서로 확정합니다. 기존 구현을 복사해 정답으로 삼지 않습니다.

`reference/tistory/`에는 이전 입력 실험 코드만 보존했습니다. 독립 실행 제품이 아니며 현행 편집기에서 재검증이 필요합니다. 이전 유료 이미지 샘플·세션·API 키·가상환경은 옮기지 않았습니다.

공개 저장소: https://github.com/O-S-M-U/osmu-v2

오늘 기록은 docs/progress/20260909.md에서 이어갑니다.

## 두 사람과 에이전트로 작업하기

1. 각자 작업 시작 전 Codex Settings → Usage를 보고 `.agent/workers.yaml`의 남은 비율과 수동 계획 예산을 갱신합니다.
2. OSMU Coordinator가 의존성, 파일 경계, 예상 토큰 상한을 비교해 각 작업자에게 한 개의 주 작업을 제안합니다.
3. 작업자는 별도 브랜치에서 작업하고 PR, 검사, 증거, 실제 사용량을 기록합니다.
4. Coordinator가 요구사항 추적표와 증거를 대조해 `verified`를 판정합니다.
5. `main` 병합 후 다시 검사된 작업만 `done`으로 처리합니다.

새 Codex 작업을 열 때는 `.agent/prompts/coordinator.md` 또는 `.agent/prompts/worker.md`를 시작 프롬프트로 사용합니다. 작업자 프롬프트의 `<worker-id>`와 `<task-id>`만 실제 값으로 바꿉니다.
