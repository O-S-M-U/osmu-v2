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

## 완료 보고 형식

```text
Task:
Requirements:
Branch / PR:
Changed paths:
Checks:
Evidence:
Actual time:
Actual usage:
Remaining risks:
Next safe starting point:
```
