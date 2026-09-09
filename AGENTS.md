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
