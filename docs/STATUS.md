# 현재 상태

최종 갱신: 2026-09-21

| 작업 | 상태 | 증거/다음 단계 |
|---|---|---|
| 독립 작업 공간 | 준비 완료 | README, 기준 사본, 진행 기록 |
| 기존 평가 보존 | 완료 | docs/reviews |
| 공통 샘플·대상별 패키지 | 로컬 검증 통과 | scripts/prepare_sample.py |
| 티스토리 | 이전 HTML 입력 증거만 존재 | 새 샘플 임시저장 후 재열기 검증 |
| 워드프레스 | 미검증 | 유형·대상 확인 후 초안 저장 검증 |
| 네이버 | 미검증 | 대상 확인 후 블록·이미지 입력 및 재열기 |
| Slack | 미검증 | 테스트 대상과 범위 확정 후 전송→수정 |
| 멀티채널 명세 | 검토안 | docs/reviews의 체크리스트 확정 필요 |
| 새 GitHub | 공개 동기화 완료 | https://github.com/O-S-M-U/osmu-v2, commit 25e0768 |
| 협업 운영 구조 | 운영 중 | `0.1B-R1` 완료, 이후 모든 작업에 GitHub Codespaces 필수 |

다음: `0.2 MODULE_SPEC 전 요구사항 원자화`가 ready다. 작업자를 배정할 때 Codespaces 시작 증거를 필수로 포함하고, 임의 주제로 자동 생성기를 먼저 만들지 않는다.

원격 파일 업로드: 사용자가 기준 문서와 협업 운영 자료를 포함한 현재 35개 파일 전체의 공개 업로드를 명시 승인했다. commit `25e0768`까지 `osmu-v2/main` 반영 완료.

`0.1A 기준 문서 식별·해시·우선순위 기록`은 PR #1, 병합 커밋 `a6be97a`로 완료됐다. 후속 `0.1B`는 Windows worktree의 Worker C에게 배정했다. Worker A와 C는 Usage를 공유하므로 수동 예산 분할 전에는 병렬 주 작업을 실행하지 않는다.

`0.1B`는 PR #4로 병합된 이력을 보존한다. 2026-09-21 owner 결정에 따라 Worker C는 `unavailable`로 전환했고, Worker D (`worker-d-claude`)가 교정 Task `0.1B-R1`을 별도 branch에서 수행한다.

`0.1B-R1`은 PR #8, merge commit `4295a2e`로 병합되고 main 재검증까지 완료됐다. 이 작업은 owner가 승인한 마지막 1회 로컬 host 예외다. 이후 작업은 사전 승인된 예외가 없는 한 GitHub Codespaces에서만 수행한다.
