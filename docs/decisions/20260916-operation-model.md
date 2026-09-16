# 2026-09-16 운영 모델 확정

## 사용자 승인 방향

### 1. 공통 개발환경

- 작업자는 운영체제와 노트북이 달라도 GitHub Codespaces의 저장소 공통 dev container에서 작업한다.
- Branch는 작업 결과를 분리하고, Codespace/dev container는 실행 도구·런타임·셸 환경을 통일한다.
- `.devcontainer/` 설정, 버전 고정 파일, 재현 가능한 설치·검사 명령은 저장소에서 관리한다.
- 계정, 토큰, 쿠키, 브라우저 프로필, `.env`와 같은 비밀값은 저장소에 넣지 않고 Codespaces Secrets 또는 승인된 로컬 보안 저장소를 사용한다.
- 외부 서비스의 로그인·브라우저 UI 검증은 공통 컨테이너만으로 완전히 재현된다고 간주하지 않으며, 채널별 원격 증거를 별도로 기록한다.

### 2. 계획과 상태의 계층

```text
MODULE_SPEC (무엇을 만족해야 하는가)
        ↓
WORK_ORDER (어떤 작업으로 실현할 것인가)
        ↓
TASK_BOARD.yaml (현재 누가 어디까지 했는가)
```

- `MODULE_SPEC`은 제품 요구사항·품질 기준·범위를 정의한다.
- `WORK_ORDER`는 요구사항을 작업 ID로 분할하고 의존성·담당 경계·예상량을 기록한다.
- `TASK_BOARD.yaml`은 작업의 현재 상태·담당자·브랜치·PR·증거 위치를 기록하는 운영 원장이다.
- `TRACEABILITY.md`는 MODULE_SPEC 요구사항 ID와 작업·검사·증거의 연결을 유지한다.

### 3. 상태 전이와 권한

```text
planned → ready → claimed → working → review → pr → verified → done
```

- `planned`: 작업은 정의됐지만 선행 조건이 충족되지 않았다.
- `ready`: 선행 조건이 충족되어 배정할 수 있다.
- `claimed`: M이 담당자·범위·브랜치를 배정했다. 실제 착수와 다르다.
- `working`: 작업자가 착수했고 시작 시각·기준 revision을 기록했다.
- `review`: 작업자가 커밋·검사·증거를 제출하고 검토를 요청했다.
- `pr`: 원격 브랜치에 PR이 생성되어 검토 대기 중이다.
- `verified`: M이 요구사항·diff·검사·증거를 확인했다.
- `done`: 승인된 PR이 main에 병합되고 main에서 재검증됐다.

`blocked`는 실행을 막는 외부 조건, `decision_required`는 명세·범위·정책 판단이 필요한 경우에 사용한다. 작업 중 문제가 있다는 이유만으로 `review`를 사용하지 않는다.

작업자는 자기 브랜치에서 상태와 보고를 제안할 수 있지만 `verified`와 `done`을 확정할 수 없다. M은 검토와 상태 통합을 담당하고, 프로젝트 owner는 범위·기획 변경과 필요한 병합 승인을 담당한다. 병합된 `main`의 TASK_BOARD가 공식 상태다.

### 4. Module Spec 변경

기존 baseline을 직접 수정하지 않는다. 새 요구사항이나 큰 기획 변경은 다음 순서를 따른다.

```text
변경 요청 → owner 범위 승인 → docs/decisions 기록
→ 새 Module Spec 버전 → WORK_ORDER 영향 갱신
→ TASK_BOARD 의존성·배정 재검토
```

## 적용 범위

이 결정은 이후 모든 작업자 A/B/C 및 M의 작업지시·보고·검토에 적용한다.
