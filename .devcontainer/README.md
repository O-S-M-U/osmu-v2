# O.S.M.U v2 공통 Codespace

모든 작업자는 호스트 OS와 관계없이 이 dev container를 기준으로 작업한다.

## 제공 환경

- Ubuntu 24.04 기반 컨테이너
- Python 3.12
- Node.js 20
- GitHub CLI
- UTF-8 및 Asia/Seoul 시간대
- LF 줄바꿈과 공백 들여쓰기

## 사용 규칙

1. Codespace는 담당 task의 branch에서 생성한다.
2. 작업 전 `git pull --ff-only origin main`으로 기준 revision을 확인한다.
3. 각 에이전트 인스턴스는 별도 branch와 Codespace를 사용한다.
4. Codespaces Secrets를 제외한 비밀값·쿠키·브라우저 프로필은 컨테이너나 저장소에 넣지 않는다.
5. 컨테이너 설정 변경은 환경 영향이 있으므로 별도 PR에서 검토한다.

외부 플랫폼 로그인이나 브라우저 UI의 결과는 컨테이너가 같아도 별도 원격 검증 증거로 기록한다.
