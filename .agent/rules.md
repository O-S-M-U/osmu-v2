# 작업 및 검증 규칙

1. 작업 시작 전에 `AGENTS.md`, `.agent/project.md`, 작업 보드, 해당 작업지시서, 관련 요구사항을 읽는다.
2. 하나의 작업만 claim하고 담당자, 브랜치, 시작 시각, 기준 revision을 기록한다.
3. `allowed_paths` 밖의 변경이 필요하면 작업을 확대하지 말고 변경 요청을 남긴다.
4. 완료 보고에는 작업 ID, 요구사항 ID, commit/PR, 실행한 검사, 증거 경로, 실제 시간, 실제 토큰 또는 사용률, 남은 위험을 적는다.
5. 외부 플랫폼 결과는 저장·발행 요청의 성공 응답만으로 통과시키지 않는다. 다시 열어 제목, 본문 순서, 이미지, 링크, 공개 상태를 확인한다.
6. 한 채널의 실패가 다른 채널의 성공 기록을 지우지 않도록 채널별 결과를 보존한다.
7. 결과가 불명확하면 재시도 전에 원격 상태를 조회해 중복 발행을 막는다.
8. 시크릿, 쿠키, 계정 정보, 브라우저 프로필을 commit하지 않는다.
9. 기준 명세의 해석 변경은 코드에서 암묵적으로 처리하지 않는다. `docs/decisions/`에 승인을 기록한다.
10. 예상 토큰 상한이 작업자의 안전 잔량보다 크면 claim하지 않고 작업을 나눈다.

## 공통 실행환경

11. 작업자는 운영체제와 무관하게 GitHub Codespaces의 저장소 공통 dev container를 반드시 사용한다. Branch는 결과 분리용이고 Codespace/dev container는 도구·런타임·셸 통일용이다.
12. 작업 시작 보고에는 `CODESPACES=true`, Codespace 이름, branch/HEAD, devcontainer 경로와 주요 도구 버전을 evidence로 남긴다. 환경 증명 전에는 `working`으로 전환하지 않는다.
13. 로컬 host 실행은 시작 전 owner가 승인한 결정 기록과 TASK_BOARD의 `environment_exception`이 있을 때만 허용한다. 예외에는 사유, 기간, 동등성 검사와 승인자를 기록한다. 사후 예외 승인은 허용하지 않는다.
14. `.devcontainer/`와 버전 고정 설정이 없는 경우 작업자는 M에게 환경 준비 작업을 요청하고 `blocked`로 멈춘다.
15. 비밀값·쿠키·브라우저 프로필은 Codespace나 저장소에 복사하지 않는다. 외부 플랫폼 로그인 검증은 별도 원격 증거로 기록한다.

## 상태 권한

16. 상태 흐름은 `planned → ready → claimed → working → review → pr → verified → done`이다. `blocked`와 `decision_required`는 예외 상태다.
17. 작업자는 `review` 또는 `pr`까지 결과를 제출할 수 있다. `verified`와 `done`은 M이 환경 증명과 결과 증거를 확인한 뒤 확정한다.
18. 작업 중 장애는 `blocked`, 명세·범위 충돌은 `decision_required`로 기록한다. 단순히 검토가 필요하다는 뜻으로 `review`를 사용하지 않는다.
19. 작업자 대화는 실행 기록이고, 병합된 `main`의 `TASK_BOARD.yaml`, PR, progress/evidence가 공유 상태의 근거다.

## 완료 보고 형식

```text
Task:
Requirements:
Branch / PR:
Environment attestation:
Changed paths:
Checks:
Evidence:
Actual time:
Actual usage:
Remaining risks:
Next safe starting point:
```
