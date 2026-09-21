# 작업 지침

- 현재 목표: 블로그 3개 플랫폼의 최소 검증. 영상 구현은 범위 밖.
- 사용자 합의와 docs/decisions를 읽고 작업한다. 기존 기준은 docs/baseline의 MODULE_SPEC v23과 워크플로우 v19. reviews는 제안이며 자동으로 확정 명세가 되지 않는다.
- 기준 문서 사본은 수정하지 않는다. 변경 합의 시 새 버전 명세를 만들고 변경 근거를 남긴다.
- 코드 존재, 로컬 검증, 외부 서비스 검증, 공개 발행 완료를 별도 상태로 기록한다.
- 작업 후 docs/STATUS.md와 docs/progress 날짜별 기록에 결과·증거·다음 단계를 남긴다.
- 원격 파일 변경·발행·메시지 전송은 사용자 요청 범위를 확인한다. 현재 샘플 준비만으로 외부 게시를 승인받은 것은 아니다.
- secrets, .env, 쿠키, 브라우저 프로필은 저장소에 넣지 않는다.
- 한 대상의 실패가 다른 대상의 성공 기록을 지우지 않도록 한다. 발행 결과가 불명확하면 재시도 전에 원격 결과를 확인한다.
- 기존 reference 코드는 검증된 제품 코드로 취급하지 않는다.
- 협업 작업 전 `.agent/project.md`, `.agent/rules.md`, `project/TASK_BOARD.yaml`을 읽는다.
- 작업은 한 번에 하나만 claim하고 `agent/<worker>/<task-id>-<short-name>` 브랜치를 사용한다.
- 예상 토큰 상한이 `.agent/workers.yaml`에 기록된 안전 잔량보다 크면 작업을 분할한다.
- `verified`와 `done`은 `.agent/manager.md`의 증거 조건을 충족할 때만 사용한다.
- 모든 신규 작업은 GitHub Codespaces의 저장소 공통 dev container에서 수행한다. Codespace는 환경 통일, branch는 결과 분리의 책임을 가진다. 로컬 host 작업은 시작 전에 owner가 승인하고 `docs/decisions/`와 TASK_BOARD에 예외·동등성 검증을 기록한 경우에만 허용한다.
- Codespaces 환경 증명 없이 시작한 작업은 `blocked`로 보고하며, M은 `review/pr` 결과를 `verified/done`으로 확정하지 않는다.
- 계획 계층은 `MODULE_SPEC → WORK_ORDER → TASK_BOARD.yaml`이며, `TRACEABILITY.md`가 요구사항·작업·검사·증거를 연결한다.
- 상태 흐름은 `planned → ready → claimed → working → review → pr → verified → done`이다. 작업 장애는 `blocked`, 명세·범위 판단은 `decision_required`로 기록한다.
- 작업자는 `review`/`pr`까지 제출할 수 있고, `verified`/`done`은 M이 증거를 확인한 뒤 확정한다. 병합된 `main`의 TASK_BOARD가 공식 상태다.
