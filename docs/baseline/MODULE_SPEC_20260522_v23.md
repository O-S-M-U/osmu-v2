# O.S.M.U 모듈 명세서

**최종 업데이트:** 2026-05-22
**버전:** v23 (수직 확장 최대 단계 2→1 하향 — 환각 최소화 원칙 적용. min(1, 청크수-1) 공식. vertical_expansion_level2 collection_type 제거. v1 운영 후 트래킹 기반 재검토 방침 추가.)
**대상 독자:** 공동 개발자, PM, 기획자
**선행 문서:** KEYWORD_SCORING_SPEC_20260517_v2.md, COLLECTOR_PHASE1A_SPEC_20260522_v4.md

---

## 0. 개요 (Overview)

### 0.1 시스템 미션
> "AI 에이전트를 활용한 콘텐츠 생성 및 발행 자동화로 지속적인 수익화가 가능한가?"
> 1차 타깃: **티스토리 블로그 자동 발행 + 수익화 검증**

### 0.2 모듈 파이프라인

```
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│ keyword_researcher │→ │     collector      │→ │   contents_maker   │→ │      checker       │→ │     publisher      │
│  키워드 수요/공급  │  │  글의 청사진 +    │  │ HTML 형태 글 생성 │  │ 시스템 검증 +     │  │ Tistory 자동 발행 │
│  황금 키워드 선정  │  │  원본 소스 정규화 │  │  + 이미지 통합    │  │  사람 검증        │  │  + 어뷰징 게이트  │
└────────────────────┘  └────────────────────┘  └────────────────────┘  └────────────────────┘  └────────────────────┘
```

### 0.3 모듈 책임 한 줄 정의

| 모듈 | 책임 | 핵심 산출물 |
|------|------|-------------|
| **keyword_researcher** | "어떤 키워드로 글을 써야 트래픽이 나올지 결정한다" | 황금 키워드 1개 + 키워드 풀 |
| **collector** | "정해진 키워드로 글을 쓸 때 어떤 구조와 사실로 채울지 청사진을 그린다" | 글 청사진 (구조 + 단락별 정규화 팩트) |
| **contents_maker** | "청사진을 HTML 형태의 완성된 글로 변환한다" | refined_post (HTML) + image_urls |
| **checker** | "발행 직전 글이 정책/품질을 만족하는지 게이트 통과시킨다" | 시스템 검증 결과 + 사람 승인 |
| **publisher** | "정책에 따라 Tistory에 자동 발행한다" | platform_url, published_at |

### 0.4 핵심 설계 원칙

- **단일 책임**: 한 모듈은 한 가지 일만. 모듈 간 책임이 흐려지면 분리 또는 재명명.
- **구조적 방어 우선**: 표절/저품질 같은 위험은 *사후 검증*보다 *사전 데이터 가공*으로 막는 게 비용 효율적.
- **Human-in-the-loop**: 자동화는 *판단*이 아닌 *작업*만. 마지막 결정은 사람.
- **결정적 검증 우선**: LLM은 결정적으로 풀 수 있는 검증에 쓰지 않는다 (글자 수, 구조, 키워드 존재 등은 코드로).

---

## 1. keyword_researcher

### 1.1 책임
씨드 키워드를 받아 *수요/공급/가치* 관점에서 평가, 황금 키워드 1개 선정 + 재활용 풀 관리.

### 1.2 입력
- `seed_keyword` (string) — 사용자 입력
- 또는 `--recommend` 모드: 풀에서 재심사로 후보 추천

### 1.2-A 출력 → collector 전달 페이로드 (v17 신규)

황금 키워드 선정 후 collector에 전달하는 인터페이스. v16까지는 `golden_keyword` 문자열만 전달했으나, v17부터 collector fallback 분기 판단에 필요한 raw_signals 일부를 함께 전달한다.

```json
{
  "keyword": "직장인 야간 홈트 무릎 부담 없는 루틴",
  "score": 72,
  "is_longtail": true,
  "raw_signals": {
    "monthly_search_volume": 1200,
    "datalab_slope": 0.8
  }
}
```

| 필드 | collector 사용 목적 |
|------|---------------------|
| `monthly_search_volume` | 블로그 수 부족 시 수요 있음/없음 구분 (이론상 하드컷 통과 = 수요 있음 보장) |
| `datalab_slope` | fallback 전략 선택 기준 (slope > 0: 수평 분해 / slope ≈ 0: 수직 확장) |

### 1.3 출력
- 황금 키워드 1개 (`golden_keyword`)
- 키워드 풀에 후보들 적재/갱신 (keywords 테이블, 최대 `pool_max_size`개)

### 1.4 내부 로직

#### 실행 시작 시 housekeeping (v13 신규)
씨드 입력 or `--recommend` 어떤 모드로 실행하든 **매 실행 시작 시** 자동 수행:

1. **이물질 스캔 (v15 신규)**: `last_evaluated_at IS NULL`인 키워드 탐지 → 로그/Slack에 "평가 이력 없는 키워드(이물질) 감지. 풀을 정리합니다." 출력 → `keywords`에서 즉시 DELETE. 트랜잭션 버그로만 발생 가능한 비정상 상태이므로 조용히 처리하지 않고 명시적으로 알림.
2. `last_evaluated_at` + `keyword.revival_days` 기준 재평가 대상 키워드 스캔
3. 해당 키워드 재평가 실행 (점수 갱신 → keyword_evaluations 기록)
4. 재평가 결과 저품질 판정 → `keywords.status = archived`
5. `pool_max_size` 초과 여부 체크 → 풀 삭제 정책 실행 (아래 1.5 참조)
6. 이후 원래 요청(씨드 확장 or 추천) 진행

> **설계 의도**: 별도 스케줄러나 백그라운드 데몬 없이 housekeeping을 보장. 하루 2회 keyword_researcher 실행 시 재평가·클리닝이 자연스럽게 함께 수행됨 (Option A 확정).

#### 씨드 입력 중복 확인 UX (v11 신규, v15 분기 명시)

사용자가 씨드 키워드를 입력하면 **씨드 임베딩을 즉석 생성**하고 keywords 테이블 `embedding` 전체와 유사도 비교:

유사도 ≥ `keyword.seed_duplicate_threshold` (기본 0.93)이면 유사 키워드 목록 노출:
```
비슷한 키워드가 이미 있어요:
  ✅ 홈카페 원두 추천   88점
  ⚠️ 원두 보관방법     82점  (어뷰징 쿨다운 2일)
  ✅ 핸드드립 원두     74점
→ 이 중에서 선택하시겠어요? 아니면 새 키워드로 진행할까요?
```

**노출 목록 정책 (v15 확정)**: 회피 신호(어뷰징 쿨다운, 자기잠식 위험)를 레이블로 표시하되 **사전 필터링은 하지 않음**. 회피 규칙 체크는 황금 키워드 선정 시점에 일괄 수행한다는 원칙 유지. 사용자가 상태를 인지하고 선택할 수 있으면 충분.

**이후 2분기 (v15 신규)**:

**Path A — "맞아요, 그거예요" 확인한 경우 (재평가 흐름)**
- 해당 키워드 1개만 재평가 (씨드 확장 없음)
- keyword_evaluations 기록 → 점수 갱신
- 기존 active 풀 전체 최근 점수 기준으로 Rank UI 표시

**Path B — "아니요, 다른 거예요" 또는 유사 키워드 없음 (신규 확장 흐름)**
- relKeyword 확장 → 무관 키워드 필터 → 평가 → pool 적재
- Path A와 동일한 Rank UI 표시

**씨드 임베딩 재사용**: 중복 확인 단계에서 생성한 씨드 임베딩을 무관 키워드 필터 anchor로 그대로 활용. 추가 임베딩 계산 없음.

#### 키워드 확장 (v15 — Naver 자동완성 → Search Ad API relKeyword 전환)

Search Ad API `/keywordstool` 호출 시 응답에 포함되는 `relKeyword` 배열을 씨드 확장 소스로 사용.

**전환 이유:**
- Naver 자동완성: 입력 패턴 기반, 5~10개 수준으로 적고 노이즈 多
- relKeyword: 실제 검색 행동 기반 연관어, 의미적으로 유의미한 확장 가능
- 결정적 장점: 월 검색량(①) 점수 계산을 위한 Search Ad API 호출(API 호출 ①)에서 relKeyword + 각 후보의 `monthlyPcQcCnt` · `monthlyMobileQcCnt` · `compIdx`를 **동시에** 취득 → 추가 API 호출 없음

**씨드 분해**: 공백 포함 구문은 hintKeywords에 직접 입력 불가 → 씨드 원본 구문을 단어 단위로 분해 후 호출 (오픈 이슈 #3)
```
씨드 "홈카페 원두 추천" → hintKeywords=홈카페,원두,추천
```

**relKeyword 최대 반환 수**: 1회 호출당 최대 약 100개. 필터 후 실제 평가 대상은 10~20개 수준 (아래 무관 키워드 필터 참조).

#### 무관 키워드 필터 (v15 신규)

relKeyword 후보를 평가(4회 API 호출)하기 전에 씨드와 의미적으로 무관한 키워드를 사전 제거.

**필터 방식**: 씨드 임베딩 vs 각 relKeyword 후보 임베딩 유사도 비교
- 유사도 < `keyword.irrelevant_filter_threshold` → 평가 대상에서 제외
- 유사도 ≥ 임계치 → 평가 진행

**씨드 임베딩 anchor**: 씨드 중복 확인(아래)에서 이미 생성한 임베딩을 재사용 — 추가 계산 없음
- anchor는 **원본 구문 전체** 임베딩 사용 ("홈카페 원두 추천"). 분해된 단어 임베딩 아님
- 이유: 단어 하나("원두")보다 구문 전체가 문맥을 정확히 표현 → 필터 정밀도 향상

**임계치**: `keyword.irrelevant_filter_threshold` = **0.55** (v1 초기값)
- 0.55 기준 예시: "에스프레소 원두"(~0.68) ✅ 통과 / "커피 머신 추천"(~0.57) ✅ 통과 / "홈카페 인테리어"(~0.52) ❌ 제외 / "요구르트"(~0.18) ❌ 제외
- v1 운영 후 실제 분포 보고 재보정 예정

#### 🚨 하드컷 선행 조건 (v17 신규 — 점수 계산 전 적용)

점수 모델 계산 전에 아래 3가지 조건을 순서대로 체크. **하나라도 해당하면 즉시 폐기 — 점수 계산 없음.**

**설계 배경**: 점수 모델에서 `blog_total_count`가 낮으면(경쟁 적음 = 좋은 신호) blog_competition 점수가 오히려 높게 나오는 구조적 허점이 있다. "아무도 검색 안 하고 아무도 글 안 쓴" 키워드가 낮은 경쟁도 덕분에 golden_threshold를 통과하는 역설을 방지하기 위해 선행 하드컷을 도입한다.

```python
# 하드컷 체크 (API 호출 후, 점수 계산 전 실행)

# ① 검색 수요 없음
if monthly_search_volume < config["keyword.min_search_volume"]:
    → 폐기 ("검색량 부족으로 폐기")

# ② 관심 하락 중 (에버그린 ≈0 은 허용, 명확한 음수만 차단)
if datalab_slope < 0:
    → 폐기 ("트렌드 하락으로 폐기")

# ③ collector 레퍼런스 수집 가능성 극히 낮음
if blog_total_count < config["keyword.min_blog_count"]:
    → 폐기 ("블로그 레퍼런스 부족으로 폐기")
```

| config 항목 | v1 초기값 | 조정 트리거 |
|---|---|---|
| `keyword.min_search_volume` | **500** | 폐기율 너무 높거나 낮으면 |
| `keyword.min_blog_count` | **30** | ⚠️ 케이스 발생 빈도 데이터 보고 |

> 상세 구현 명세 및 설계 근거: KEYWORD_SCORING_SPEC_20260517_v2.md Section 4 참조

#### 점수 모델 — 두 프로필 운용 (v14 전면 개정)

| 기준 | DEFAULT (일반) | LONGTAIL (롱테일/연금술) | 비고 |
|------|----------------|---------------------------|------|
| 월 검색량 (수요) | **30** | **15** | Search Ad API 절대값. DataLab 40점 폐지 |
| Blog 경쟁도 — 총량 | 15 | 22.5 | Naver Blog Search API `total` |
| Blog 경쟁도 — 최근 밀도 | 15 | 22.5 | 동일 API + 날짜 필터 (7일 primary) |
| 상업적 의도 | 20 | 25 | compIdx + 쇼핑 검색 + 패턴 룰 3단계 조합 |
| 발행 추세 (DataLab slope) | **10** | **10** | DataLab 8주 시계열 선형 회귀. Google Trends 폐지 |
| **합계** | **100** | **100** | |

> LONGTAIL Blog 경쟁도 45점 = 총량 22.5 + 최근 밀도 22.5 (동일 비율 분할)

**변경 배경 요약:**
- `DataLab 트렌드 40점` 폐지 → DataLab ratio는 상대값이라 절대 검색량 측정 불가
- `월 검색량 30점` 신규: Search Ad API `/keywordstool`이 실제 월간 절대 검색량 제공 (광고 미집행 계정으로도 무료 취득 가능, 2026-05-09 실 계정 확인)
- `Google Trends 10점` 폐지: pytrends 2025-04-17 archived, 실 트래픽 분석에서 네이버 99% · 구글 0.1% → 구글 트렌드 신호 기여도 없음
- `발행 추세 10점` 신규: DataLab 8주 slope로 대체 — 이미 slope 계산용으로 DataLab 호출하므로 **추가 API 호출 없음**

#### Blog 경쟁도의 시간 분할 (v4 신규, v14 기간 재정의)
기존 30점을 두 sub-axis로 분리:
- **총량 경쟁도** (15점) — 누적 발행 글 수 / 상위 노출 난이도
- **최근 발행 밀도** (15점) — 최근 **7일** 발행 밀도 (primary). 같은 총량이라도 *최근 폭발한 키워드는 과포화* 신호.
  - 30일 수치도 함께 수집 (`blog_recent_30d_count`) — 월간 추이 참고용

> v13까지 14일 단일 기간이었으나 v14에서 7일(단기 급격한 과포화 탐지)과 30일(월간 추이) 두 기간으로 세분화. config 항목도 분리됨 (6.1 참조).

#### API 호출 흐름 (v14 신규)

키워드 1개 평가 시 총 **4회 API 호출** (기존 DataLab + Google Trends 2회와 동일 횟수 유지):

```
① Search Ad API  /keywordstool  → monthly_search_volume + comp_idx + relKeyword 목록
② Blog Search    /blog          → blog_total_count (sort=sim, display=1)
③ Blog Search    /blog          → blog_recent_7d_count + blog_recent_30d_count (날짜 필터)
④ DataLab        /datalab/v1/search → datalab_slope 계산용 8주 시계열

(⑤ Shopping Search /shop → commercial_intent 보조, 선택적)
```

> ⚠️ **Search Ad API 핵심 제약**: `hintKeywords`에 공백 포함 구문 입력 시 오류 발생.
> 씨드 "홈카페 원두 추천" → 단어 분해 → `hintKeywords=홈카페,원두,추천` 으로 호출 (씨드 분해 로직 필요 — 오픈 이슈 #3)

#### 황금 키워드 회피 규칙 (collector와 협업)

네 가지 다른 목적의 회피를 분리해서 적용:

| 회피 목적 | 적용 단위 | 시작 임계치 | 비고 |
|-----------|-----------|-------------|------|
| (a) 어뷰징 회피 (계정 패턴 탐지) | account_id | 황금 키워드 후보 `embedding` vs 기발행 글의 황금 키워드 `embedding` (keywords 테이블) 비교. 유사도 ≥ 0.85 → 최소 3일 쿨다운 | publisher에서도 재확인 필요 (아래 설명) |
| (b) 자기 잠식 (검색 경쟁) | blog_id | 같은 황금 키워드 180일 내 재사용 금지 (사용자 강제 오버라이드 시 경고) | keyword_usages in_progress로 중복 진입 차단. **파이프라인이 어떤 이유로든 중단되면(사용자 거부·중단 요구·기술 오류) status = failed로 갱신 → in_progress 잠금 즉시 해제. 재선택 여부는 사용자가 결정** |
| (c) 외부 포화 (시장 환경) | 키워드 자체 | "최근 발행 밀도" 점수에 반영 (위 점수 모델) | 별도 로직 없음 |
| (d) 다양성 (UX) | blog_id | 최근 7일 5편 중 의미 유사도 ≥ 0.8 그룹이 3편 이상이면 경고 | **v1 미구현**. 도입 시 publisher에서 체크할 것 (발행 시점 기준이므로) |

> **⚠️ (a) 어뷰징 회피 — publisher 재확인이 필요한 이유**
>
> keyword_researcher의 쿨다운 체크는 "키워드 선정 시점에 이미 발행된 글들"과 비교한다.
> 그러나 여러 글이 checker Stage 2(사람 검증)에 동시에 대기 중일 때, 사용자가 한꺼번에 승인하면
> publisher가 A → B → C 순으로 발행하게 된다.
> A가 발행된 직후 B를 발행할 때, A와 B의 유사도는 keyword_researcher 시점에 비교된 적이 없다.
> 이 경우 publisher에서 직전 발행 글과 유사도를 재확인하지 않으면 어뷰징 패턴이 통과된다.
>
> **결론**: (a) 쿨다운은 keyword_researcher(키워드 품질 판단)와 publisher(발행 직전 실시간 확인) 양쪽에서 모두 체크한다.

#### Rank UI — 후보 제시 화면 (v15 명세)

씨드 입력(Path A/B) 및 `--recommend` 모드 공통으로 사용하는 후보 제시 UI.

**표시 방식**: 전체 active 풀 + 이번 세션 신규 평가 후보를 total_score 기준 내림차순 정렬, 상위 5위까지 표시.

```
순위   키워드               점수   상태
──────────────────────────────────────────
1위   원두 보관방법         91점   ✅ 안전
2위   핸드드립 원두 추천    88점   ✅ 안전   (new)
3위   홈카페 원두 추천      85점   ⚠️ 쿨다운 2일
4위   원두 그라인더 추천    79점   ✅ 안전
5위   커피 원두 종류        74점   ✅ 안전
──────────────────────────────────────────
(이번 씨드에서 생성된 후보 2개 포함)
```

- 이번 세션에서 새로 평가된 후보: **(new)** 레이블 + 다른 색상으로 구분
- 5위 안에 신규 후보 없을 경우 5위 아래 별도 표시:
```
...
5위   커피 원두 종류        74점
──────────────────────────────────────────
#12  홈카페 원두 입문       48점   (new) ← 5위권 밖 신규 후보
```

**기존 active 키워드 점수**: 이 단계에서 재평가 안 함. 각자의 keyword_evaluations 최근 레코드 점수 사용. 재평가는 housekeeping 전담.

#### `--recommend` 모드 (v15 명시)

- 씨드 입력 없음. relKeyword 확장·무관 키워드 필터·신규 평가 없음
- 기존 active 풀에서 최근 점수 기준 상위 5위를 Rank UI로 표시
- (new) 레이블 없음 (신규 후보 없으므로)
- 사용자가 원하는 키워드를 선택 → 황금 키워드 선정 흐름으로 진입

#### n개 pool 적재 방식 (v15 명시)

무관 키워드 필터 통과 후 평가된 n개 후보는 **전량 keywords 테이블에 적재**.

- 평가 전 등급(황금/강철/부스러기) 기준 사전 필터링 없음 — 평가해야 등급을 알 수 있으므로 논리적으로 불가
- pool_max_size 초과 시 eviction 정책이 자연스럽게 정리 (설계 의도대로)
- 0.55 임계치 기준 실제 적재 예상량: 10~20개/실행. pool_max_size=50 기준 3~5회 실행 후 eviction 발동 패턴

### 1.5 keyword_pool 관리 (keywords 테이블)

- **풀의 정체성**: 씨드 확장 후 황금으로 선정되지 않은 후보들을 *재심사 대기 상태*로 보관
- **재심사 트리거**: keyword_researcher 매 실행 시 housekeeping 단계에서 자동 처리 (v13 확정)
- **보관 개수 상한**: `config.keyword.pool_max_size` (v1 시작값 **50**)

#### 키워드 등급 체계 (v13 신규)

| 등급 | 점수 범위 | 설명 |
|------|-----------|------|
| 부스러기 | 0 ~ 45점 | 삭제 1순위 후보 기준 등급. 반복 평가에도 점수 개선 없으면 정리 대상 |
| 강철 | 46 ~ 59점 | 황금 미달이나 보존 가치 있음. 재평가 축적으로 황금 진입 가능 |
| 황금 | 60점 이상 | `keyword.golden_threshold` 이상. 발행 대상으로 선정되는 등급 |

> **등급 경계 조정**: v1 운영 데이터 축적 후 실제 점수 분포 기준으로 재검토 예정.

#### 풀 삭제 정책 (v13 확정)

`pool_max_size` 초과 시 트리거. 초과분만큼 삭제 후 신규 키워드 적재.

**1순위 — 저품질 반복 평가 키워드**
- 조건: `evaluation_count ≥ keyword.pool_eviction_eval_count(3)` AND `avg_score < keyword.pool_eviction_score_threshold(45)`
- 정렬: `last_evaluated_at` 오래된 순 (ASC)
- `evaluation_count`, `avg_score`: keyword_evaluations 테이블에서 실시간 집계 (별도 컬럼 불필요)

**2순위 fallback — 1순위 후보가 부족한 경우**
- 1순위로 초과분을 채우지 못했을 때 적용
- 정렬: `last_evaluated_at` 오래된 순 (ASC) → 동점 시 `total_score` 낮은 순 (ASC)
- `total_score`: keyword_evaluations의 **가장 최근 평가 레코드** 기준 (평균값 아님)
- 조건 없이 순차 삭제 (평균 점수 임계치 미적용)

> **설계 의도**: 초반에는 evaluation_count가 낮아 1순위 후보가 거의 없음. 2순위가 안전망 역할을 하며, 시간이 쌓일수록 1순위 정책이 주로 작동하게 됨.

**공통 예외**
- `status = archived` 키워드는 별도 처리 (풀 카운트에 포함 안 됨)
- 글이 발행된 키워드 (`keyword_usages.status = published` 연결)는 삭제 대상에서 제외

### 1.6 DB 업데이트 시점
- `keywords` 테이블: 씨드 확장 직후 후보 적재, 황금 키워드 선정 시 `status` 갱신
- `keyword_evaluations` 테이블: 평가 시마다 이벤트 기록 (raw_signals + score_breakdown). housekeeping 재평가 포함
- `keyword_usages` 테이블: 황금 키워드 선정 시 `in_progress` 레코드 생성
- `keyword_usages` 테이블: 파이프라인 중단 시(사용자 거부·중단 요구·기술 오류 포함) `status = failed`로 갱신 → in_progress 잠금 즉시 해제. `published_at`은 null 유지 (180일 재사용 카운트 미적용)
- `contents` 테이블: **업데이트 없음** (레코드 생성은 collector에서)

### 1.7 논의된 트레이드오프와 결정

- **DataLab 40점 → 폐지**: 실제 검색량(절대값)을 측정하려면 DataLab ratio(상대값)는 부적합. Search Ad API가 정확한 대안임을 실 계정 테스트로 확인 (2026-05-09).
- **Google Trends 10점 → DataLab slope**: pytrends archived + 실 트래픽 구글 비중 0.1% → 신호 기여도 없음. DataLab 호출을 slope 계산에 재활용하므로 추가 호출 비용 없음.
- **최근 밀도 14일 → 7일/30일**: 단기 과포화 탐지(7일)와 월간 추이(30일)를 분리해 더 정밀한 신호 획득. 14일은 두 기준 사이 어정쩡한 기간으로 판단.
- **점수 환산 구간 가설 기반**: v14 환산 구간은 초기 가설. v1 운영 후 실제 키워드 분포 사분위수 기준으로 재보정 예정.
- **DataLab 가중치 40점 → 폐지**: 일반론(Tistory는 구글 비중 큼)과 다르지만, *실제 운영 데이터로 네이버 유입이 더 큼을 확인*하여 방향 전환.
- **상대 정규화 vs 절대 정규화**: v1은 절대 정규화 (임계치 기반). 임계치는 *실제 데이터 분포 기준 사분위수*에 맞춰 보정 필요.
- **failed 시 이유 세분화 없음**: 파이프라인 중단 사유(사용자 거부 / 중단 요구 / 기술 오류)를 구분하지 않고 모두 failed로 처리. 시스템이 의도를 추론할 수 없으므로 재선택 여부는 항상 사용자에게 돌려줌.
- **evaluation_count 비정규화 미채택**: evaluation_count를 keywords 테이블에 컬럼으로 두지 않고 keyword_evaluations에서 실시간 COUNT 집계로 처리. v1 데이터량에서는 JOIN 계산이 충분하며, 정규화 상태를 유지하는 편이 버그 위험이 낮음. v2+ 데이터량 증가 시 재검토.
- **housekeeping Option A 채택**: keyword_researcher 매 실행 시 내재화. 별도 스케줄러/백그라운드 데몬 불필요. 하루 2회 실행 기준으로 revival_days 초과 키워드가 적시에 재평가됨.

### 1.8 오픈 이슈
- 롱테일 분류 자동 룰 정의 (어절 수? 검색량 임계? 수식어 패턴?)
- 황금 임계 점수 (총 100점 중 몇 점 이상이 황금인가?)
- 씨드 분해 로직 명세: "홈카페 원두 추천" → ["홈카페", "원두", "추천"] 규칙 (형태소 분석기 vs 공백 split)
- ~~무관 키워드 필터링: relKeyword에서 무관 키워드 필터 기준 (임베딩 유사도 threshold)~~ ✅ 완료 (v15, seed embedding 앵커 + threshold=0.55)
- Search Ad API 일일 호출 한도 — Naver Open API 25,000회/일과 별도 관리 여부 확인 필요
- 점수 환산 구간 재보정 — v1 운영 후 실제 키워드 분포 사분위수 기반으로 조정 예정

---

## 2. collector

### 2.1 책임
황금 키워드를 받아 (a) 경쟁 블로그 본문 분석으로 글의 *구조*를 결정하고 (b) 공신력 있는 원본 소스에서 *사실 단위로 정규화*하여 contents_maker가 환각/표절 없이 글을 쓸 수 있도록 청사진을 제공.

**핵심 전략**: 경쟁 블로그 → 구조 파악 / 뉴스·공공기관 → 사실·수치 추출 (두 역할 분리)

### 2.2 입력
- `golden_keyword` (string)

### 2.3 출력 스키마 (v6 개정)

```json
{
  "title": "h1으로 들어갈 제목",
  "intro": "도입문 — 글에서 다룰 내용을 제시해 사용자가 계속 읽도록 유도",
  "short_conclusion": "짧은 결론 — 답을 암시하되 본문 안 읽으면 손해라는 신호",
  "target_reader": {
    "persona": "홈카페 입문 1년 미만, 20-30대",
    "knowledge_level": "beginner | intermediate | expert",
    "primary_intent": "learn | buy | solve",
    "reader_awareness": "unaware | problem_aware | solution_aware | product_aware"
  },
  "tone_style": {
    "voice": "friendly | professional | analytical",
    "emotion": "neutral | persuasive | empathetic"
  },
  "content_template": {
    "type": "problem_solving | comparison | data_analysis | story",
    "flow": [
      "퇴근 후 운동하고 싶지만 무릎 통증이 반복되는 상황 공감",
      "야간 운동 특유의 피로 누적과 폼 무너짐이 무릎에 집중되는 메커니즘",
      "충격 최소화 동작 3가지 + 운동 순서 조정",
      "실제 2주 루틴 적용 후 통증 없이 유지한 경험"
    ]
  },
  "ending": {
    "style": "summary | cta | recommendation",
    "cta_strength": "soft | hard",
    "next_action": "마무리에서 유도할 행동/추천 방향 (자유 텍스트)"
  },
  "body_paragraphs": [
    {
      "paragraph_id": "p1",
      "type": "llm_generated",
      "h2_subtitle": "단락 소제목 (h2 태그)",
      "core_message": "이 단락이 다룰 핵심 주장/주제",
      "assigned_keywords": ["LLM이 단락 주제 분석으로 도출한 서브 키워드"],
      "image_search_keywords_en": ["english", "search", "terms"],
      "image_alt_text_ko": "한국어 alt text 초안"
    },
    {
      "paragraph_id": "p2",
      "type": "fact_based",
      "h2_subtitle": "단락 소제목 (h2 태그)",
      "core_message": "이 단락이 다룰 핵심 주장/주제",
      "assigned_keywords": ["LLM이 단락 주제 분석으로 도출한 서브 키워드"],
      "image_search_keywords_en": ["english", "search", "terms"],
      "image_alt_text_ko": "한국어 alt text 초안",
      "facts": [
        {
          "type": "statistic | claim | fact | definition",
          "content": "2023년 기준 1인가구 비율 34.9%",
          "entity": "통계청",
          "year": 2023,
          "source_url": "https://..."
        }
      ]
    }
  ]
}
```

### 2.4 내부 로직 (v5 전면 개정)

#### Phase 1-A — 상위 블로그 수집 (v18 역할 명확화)

Phase 1-A의 책임은 수집, 필터링, 태깅, 압축이다. LLM 분석은 하지 않는다.

1. Naver webdoc + Google Serper로 각 5개씩 요청 → 필터링 후 최대 5개 확정
2. 각 블로그에 `weight` 태깅 (양쪽 엔진 등장 시 `HIGH`, 단일 소스 `NORMAL`)
3. Firecrawl 본문에서 **압축** 수행 — H2 섹션별 leading_sentences 추출 (LLM 없이 규칙 기반)
4. Phase 1-B에 압축된 결과 + 메타데이터 전달

**압축 방식 (H2 + leading_sentences)**:

| 케이스 | leading_sentences 수 | 이유 |
|--------|---------------------|------|
| 정상 수집 | 첫 1문장 | 동일 키워드 블로그 → 구조 신호 일관. 1문장으로 방향 파악 충분 |
| 수평 분해 | 첫 2~3문장 (짧은 섹션은 전문) | 서로 다른 청크 블로그 합성 → 섹션 각도 파악에 더 많은 컨텍스트 필요 |
| 수직 확장 | 첫 1문장 | 단일 확장 키워드 검색 → 구조 신호 일관 |

> **압축을 LLM 없이 처리하는 이유**: "핵심 문장" 추출은 LLM이 필요하지만 "첫 문장" 추출은 텍스트 파싱으로 충분하다. 상위 블로그의 H2 하위 첫 문장이 섹션 방향을 소개하는 경우가 많으며, Post-fetch 필터(H2 4개 이상)를 통과한 글은 최소 구조 품질이 보장된다. Phase 1-A에서 LLM을 추가 호출하면 비용이 증가하고 Phase 1-B의 역할과 중복된다.

#### Phase 1-A → Phase 1-B 전달 포맷 (v18 신규)

```json
{
  "original_keyword": "직장인 야간 홈트 무릎 부담 없는 루틴",
  "collection_type": "horizontal_decomposition",
  "chunks": ["직장인 야간 홈트", "무릎 부담 없는 운동 루틴"],
  "datalab_slope": 0.8,
  "reference_blogs": [
    {
      "url": "https://...",
      "title": "블로그 제목",
      "weight": "HIGH",
      "source_chunk": "직장인 야간 홈트",
      "compressed_content": [
        {
          "h2": "직장인 야간 운동의 장점",
          "leading_sentences": "퇴근 후 30분 홈트는 수면의 질을 높이고 스트레스를 낮춘다."
        }
      ]
    }
  ]
}
```

| `collection_type` 값 | 설명 |
|----------------------|------|
| `normal` | 원본 키워드로 5개 정상 수집. `source_chunk: null` |
| `horizontal_decomposition` | 수평 분해 후 청크별 수집. 각 블로그에 `source_chunk` 명시 |
| `vertical_expansion_level1` | 수직 확장 1단계(앞 청크 1개 제거) 후 수집. `source_chunk: null` |

#### Phase 1-B — 구조 초안 생성 (v18 역할 명확화)

Phase 1-B의 책임은 압축된 레퍼런스 분석, 공통성 기반 합성, blueprint 생성이다. Slack 전송은 Phase 1-D가 담당한다.

1. Phase 1-A로부터 압축된 블로그 + 메타데이터 수신
2. LLM이 `collection_type`에 따라 분석 방식을 달리하여 구조 초안 생성:
   - `normal`: 5개 블로그 H2 패턴 분석 → blueprint
   - `horizontal_decomposition`: source_chunk 기준 그룹핑 → **공통성 분석 후 응집성 합성**
     - n개 청크 전체 공통 주제 → paragraph_blueprint 핵심 H2
     - 일부 청크 공통 주제 → subtheme 후보
     - 단일 청크 고유 주제 → assigned_keywords 수준
   - `vertical_expansion_*`: 확장된 키워드 기준 구조 분석, 원본 키워드 의도 보정
3. 구조 초안: 제목 / 5~7개 단락(주제+순서) / 도입부 / 결말 방향 / 각 단락 타입(`fact_based` / `llm_generated`) / 타겟 독자 추론 / `content_template` (`type` 고정 어휘 + `flow` 자유 텍스트 배열 — type별 유효 스텝 수 검증)
4. Phase 1-D로 구조 초안 + `summary_embedding` 유사도 계산 결과 전달

> **Phase 1-A / 1-B 역할 분리 원칙**: 공통성 분석을 Phase 1-A에서 수행하면 Phase 1-B 역할과 중복되고 Phase 1-A가 과중해진다. Phase 1-A는 수집·태깅·압축만 담당하고, Phase 1-B의 LLM이 synthesis 전체를 책임진다. Phase 1-A는 source_chunk 메타데이터를 통해 "이 블로그들이 어디서 왔는지"만 알려주는 역할에 집중한다.

#### Phase 1-D — 사용자 Slack 알림 + 검토 (v19 신규)

Phase 1-D의 책임은 Phase 1-B가 생성한 구조 초안을 Slack으로 사용자에게 전달하고, 조건에 따라 파라미터 수정 선택지를 제공하는 것이다.

**1. 기본 메시지 (항상 전송)**

```
📋 구조 초안이 완성되었습니다 — [키워드]

제목: {title}
대상 독자: {target_reader.persona} / {target_reader.knowledge_level} / {target_reader.primary_intent}
구조: {content_template.type} · 느낌: {tone_style.voice}
결말: {ending.style} — {ending.next_action}

단락 구성 ({n}개):
  p1 [llm_generated] — {h2_subtitle}
  p2 [fact_based]    — {h2_subtitle}
  ...

✅ 승인 버튼을 누르세요.
✏️ 세밀하게 편집하려면 → [대시보드 열기]({dashboard_url})
```

**2. 조건부 수정 선택 (similarity 경고 시만 추가 표시)**

`summary_embedding` 비교 결과 유사도 ≥ `collector.similarity_warning_threshold`(0.75)인 기존 글이 있을 경우, 기본 메시지에 아래 블록을 **추가**로 표시한다.

```
⚠️ 이전 글과 유사도 {score} — 방향을 바꾸면 더 다른 느낌의 글이 나올 수 있어요.
   가장 유사한 글: "{existing_title}" ({published_at})

구조 바꾸기:
  현재: {content_template.type}
  → problem_solving / comparison / data_analysis / story 중 선택

느낌 바꾸기:
  현재: {tone_style.voice}
  → friendly / professional / analytical 중 선택

선택 후 전송하면 같은 블로그 데이터로 재생성합니다 (추가 API 호출 없음).
단락 수준 편집은 → [대시보드 열기]({dashboard_url})
```

> **설계 의도**: Slack 선택지는 최종 글 느낌에 임팩트가 가장 큰 두 가지(구조·목소리)만 제공한다. 선택지가 많을수록 결정 피로도가 높아지므로, 실제 차별화가 필요한 케이스에서 빠르게 결정할 수 있는 항목만 노출한다. `tone_style.emotion`, `target_reader` 세부값, `ending`, `content_template.flow` 조정은 대시보드에서 가능하다.

**3. 파라미터 수정 시 처리 흐름**

```
사용자가 Slack에서 파라미터 조정 값 전송
  → Phase 1-B 재호출 (동일 블로그 압축 결과 재사용, API 재호출 없음)
     modified parameter를 프롬프트에 반영하여 blueprint 재생성
  → Phase 1-D 재전송 (수정된 초안 + 선택된 파라미터 표시)
  → 승인 시 Phase 2 진입
```

**4. 직접 수정 — 대시보드**

Slack 메시지의 "대시보드 열기" 링크를 통해 웹 대시보드에서 단락 수준까지 직접 편집 가능. 파라미터 선택이 아닌 h2_subtitle, core_message, 단락 순서 변경 등 세밀한 조정이 필요할 때 사용.

수정 완료 후 대시보드에서 승인하면 Slack에도 확인 알림 전송.

#### Phase 1 fallback — 상위 블로그 부족 시 (v17 재설계, v18 세부 보완)

keyword_researcher 하드컷(v17 신규)을 통과한 키워드는 `monthly_search_volume ≥ min_search_volume`이고 `datalab_slope ≥ 0`임이 보장된다. 따라서 블로그 수 부족은 "나쁜 키워드"가 아니라 "레퍼런스 공급이 부족한 유효한 키워드"를 의미한다.

```
필터 통과 블로그 수 ≥ 5  →  정상 진행

필터 통과 블로그 수 < 5  →  Fallback 진입

  datalab_slope > 0 (상승 중, rising keyword)
    →  수평 분해 전략
       LLM이 키워드를 의미 청크로 분해 → 청크별 독립 수집
       각 블로그에 source_chunk 태깅 → Phase 1-B에 전달
       Phase 1-B가 공통성 분석 + 응집성 합성 수행
       Phase 1-B 프롬프트에 "rising keyword" freshness 우선 컨텍스트 주입

  datalab_slope ≈ 0 (평탄, 에버그린)
    →  수직 확장 전략 (최대 단계: min(1, 청크수-1))
       LLM이 키워드를 의미 청크로 분해 → 앞 청크 1개 제거 후 재검색
       청크 1개: 0단계 → 즉시 ⚠️ 케이스
       청크 2개 이상: 최대 1단계 (Level 1만 허용)
       Level 1 이후 min_blogs 미달 → ⚠️ 케이스

  datalab_slope < 0  →  keyword_researcher 하드컷에서 이미 폐기. collector 도달 불가.
```

**⚠️ 케이스 처리 (단계 소진 또는 단일 청크 케이스)**:

| 처리 | 내용 |
|------|------|
| Slack 알림 | ⚠️ 레퍼런스 수집 실패 / 키워드 / 시도 이력 / 권고 조치 전송 |
| 파이프라인 중단 | Phase 2 진입 없음 |
| DB 갱신 | `keyword_usages.status = failed` → in_progress 잠금 해제 |

> **⚠️ 케이스에서 파이프라인을 중단하는 이유**: 레퍼런스 없이 LLM이 추상적 틀을 생성하면, Phase 2가 "어떤 소스를 찾아야 하는지" 알 수 없고 Checker의 원문 유사도 비교도 의미를 잃는다. v1에서는 자동화 강행보다 사용자 판단 요청이 더 안전하다.

> 상세 구현 명세: COLLECTOR_PHASE1A_SPEC_20260522_v4.md 참조

#### Phase 2 — 원본 매핑 (구조 확정 후에만 실행)

Phase 2는 두 단계 (2-A, 2-B)로 구분된다.

**Phase 2-A — 소스 탐색 (v19 쿼리 필드 명세)**

- **대상**: `fact_based` 단락만 (3~4개)
- **쿼리 생성 기반**: 단락의 `h2_subtitle` + `core_message` + `assigned_keywords`를 조합해 검색 쿼리 구성
  - `h2_subtitle`: 단락 주제 방향 (예: "1인가구 증가와 소비 트렌드 변화")
  - `core_message`: 이 단락에서 뒷받침해야 할 핵심 주장 (예: "1인가구 비율이 높아질수록 소형가전 수요가 상승한다")
  - `assigned_keywords`: 단락과 연관된 서브 키워드 (추가 쿼리 변형에 활용)
- **공신력 소스 범위 (v19 확정)**: 뉴스 · 매거진 · 칼럼. 공공기관 자료도 포함.
  - 수용: 언론사 기사(Naver News, Google News), 산업 매거진, 전문가 칼럼, 통계청/연구원 발표
  - 제외: 개인 블로그, 포럼, 무서명 게시물, 광고성 콘텐츠
- **검색 경로**: Naver News / Google Search → 1~2개 선별

**Phase 2-B — 팩트 정규화 + 소스 저장 (v19 다중 소스 명시)**

- **Firecrawl**: 선별된 소스 크롤링
- **LLM 추출**: 사실/수치/주장만 추출 (문장 그대로 아님 — 표절 방어 1차선)
- **정규화 저장**: facts 배열에 적재. **하나의 단락에 여러 소스의 팩트가 매핑될 수 있다.**
- **source_url 필수 저장**: 각 fact 항목에 `source_url` 저장. Checker 표절 검사(refined_post 문장 vs 원문 소스 문장 cross 비교) 대상 링크로 사용.

```json
"facts": [
  {
    "type": "statistic",
    "content": "2023년 1인가구 비율 34.9%",
    "entity": "통계청",
    "year": 2023,
    "source_url": "https://kostat.go.kr/..."   ← checker cross 비교 대상
  },
  {
    "type": "claim",
    "content": "1인가구 증가가 소형가전 시장 성장의 주요 원인",
    "entity": "한국경제매거진",
    "year": 2024,
    "source_url": "https://magazine.hankyung.com/..."   ← 다른 소스, 동일 단락
  }
]
```

> **다중 소스 매핑 설계 의도**: 단락 하나를 뒷받침하는 팩트가 여러 출처에서 올 수 있다. source_url을 facts 항목 단위로 저장하면 Checker가 어떤 원문과 비교해야 하는지 정확히 추적 가능하다. 나아가 추후 fact별 출처 표기(각주/링크)가 필요할 때도 이 구조로 자연스럽게 확장된다.

#### fact type 정의
| type | 설명 | 예시 |
|------|------|------|
| `statistic` | 수치/통계 | "2023년 1인가구 비율 34.9% (통계청)" |
| `claim` | 주장/의견 | "1인가구 증가가 소형 가전 시장 성장의 주요 원인" |
| `fact` | 사실/정보 | "서울시는 2025년부터 1인가구 지원센터를 확대 운영" |
| `definition` | 정의/개념 | "롱테일 키워드: 3단어 이상의 구체적 검색어" |

#### Firecrawl 사용량 예측
| 단계 | 횟수 | 용도 |
|------|------|------|
| Phase 1 | 5회 | 경쟁 블로그 본문 |
| Phase 2 | 3~4회 | 공신력 소스 (fact_based 단락당 1회) |
| **합계** | **8~9회/article** | 월 500페이지 무료 기준 약 55~60개 article 커버 |

### 2.5 DB 업데이트 시점
- **Phase 1 완료 후**: contents_db 레코드 생성, `status: 구조확정대기`, 구조 초안 저장
- **Phase 2 완료 후**: `paragraph_blueprint` (단락 구조), `normalized_sources` (정규화 팩트) 저장, `status: 생성대기`

### 2.6 논의된 트레이드오프와 결정

- **상위 블로그 전수 Firecrawl vs 제목+스니펫**: 전수 Firecrawl 확정. 스니펫만으로는 니치 키워드 구조 파악 불충분.
- **사용자 블로그 선별 단계 제거**: 기존 "10개 중 5개 선별" 제거. LLM이 5개 전체 분석 후 구조 초안 제시 → 사용자는 초안 검토/수정만.
- **경쟁 블로그 vs 공신력 소스 역할 분리**: 경쟁 블로그 → 구조 / 뉴스·공공기관 → 팩트. 두 역할을 섞지 않음.
- **팩트 추출 방식**: 문장 그대로 아닌 사실/수치/주장 단위로 추출. 유사도 낮추기 + 환각 방지.
- **Phase 2 타이밍**: 구조 확정 후에만 실행 (사용자가 구조 거절하면 Phase 2 Firecrawl 낭비 없음).
- **본문 전체 전달 vs 압축 전달 (v18 신규)**: 압축 전달 확정. 블로그 5개 전문은 15,000자 이상으로 토큰 비용 과다. H2 + leading_sentences 방식으로 규칙 기반 압축. Phase 1-B의 구조 분석 목적에는 H2 패턴 반복 신호가 핵심이며, 전문이 없어도 충분한 신호 확보 가능. 체험형 블로그 대응은 v1 운영 후 데이터 보고 재검토.
- **공통성 분석 위치 — Phase 1-A vs Phase 1-B (v18 신규)**: Phase 1-B 담당으로 확정. Phase 1-A에서 분석을 수행하면 Phase 1-B 역할과 중복되고 Phase 1-A에 LLM 호출이 추가된다. Phase 1-A는 source_chunk 메타데이터만 붙여서 전달하고, Phase 1-B LLM이 공통성 분석 + blueprint 합성을 일괄 수행.
- **수직 확장 단계 상한 — 고정 2단계 vs 청크 수 기반 동적 계산 (v18 신규)**: `min(2, 청크수-1)` 공식으로 확정. 청크 1개인 경우 제거하면 검색어가 사라지므로 즉시 ⚠️ 처리. 이 케이스는 현실적으로 극히 드물지만 공식 하나로 방어 가능 (YAGNI — 별도 분기 불필요).
- **수직 확장 최대 단계 2→1 하향 (v23 신규)**: `min(1, 청크수-1)` 공식으로 변경. Level 2는 앞 청크를 2개 제거하므로 "상황 맥락"(야간 홈트 등)을 나타내는 청크까지 사라질 수 있고, Phase 1-B가 해당 단락을 레퍼런스 없이 창작해야 하는 상황이 발생한다. 사실·수치 주장이 아니라 맥락·프레이밍이라도 환각 기반 콘텐츠를 허용하지 않는다는 파이프라인의 암묵적 원칙에 따라 Level 1으로 제한. Level 1은 타겟 독자 수식어(직장인 등)만 빠지는 수준으로, Phase 1-B가 original_keyword를 참조해 보완 가능하며 Phase 2 공신력 소스가 사실 주장을 커버한다. v1 운영 후 Level 1 글 성과(조회수, 체류시간) 데이터 기반으로 max_levels 재검토. 상세: COLLECTOR_PHASE1A_SPEC_20260522_v4.md Section 9.3.
- **Phase 1-D 파라미터 수정 선택 조건 (v19 신규)**: 수정 선택지를 항상 제공하지 않고 `summary_embedding` 유사도 ≥ 0.75일 때만 제공. 차별화 필요가 없는 케이스에서 선택 피로를 제거하고, 실제로 필요한 케이스에만 집중.
- **Phase 2 쿼리 필드 명세 (v19 신규)**: h2_subtitle + core_message + assigned_keywords 3개 필드 조합 → 검색 쿼리 구성. "단락 주제" 라는 추상적 표현 대신 명시적 필드 매핑으로 검색 쿼리의 정확도 확보.
- **공신력 소스 범위 (v19 확정)**: 뉴스 + 매거진 + 칼럼. "공공기관"만으로는 커버 범위가 좁고, 산업 매거진·전문 칼럼이 팩트 근거로 더 적합한 경우가 많음. 단, 개인 블로그·포럼·광고성 콘텐츠는 제외.
- **다중 소스 per 단락 (v19 신규)**: 단락 하나에 여러 소스의 팩트 매핑 허용. facts 배열이 이미 이 구조를 지원하지만, 의도가 명확하지 않아 명시적으로 확정. source_url per fact가 Checker의 cross 비교 기준이 됨.

### 2.7 오픈 이슈
- ~~상위 5개 미달 시 fallback 처리~~ ✅ 완료 (v17 slope 기반 분기, v18 수평·수직 세부 설계)
- ~~단락 구조 초안의 Slack 전송 UX 설계~~ ✅ 완료 (v19 Phase 1-D 명세)
- 공신력 소스 필터링 자동화 — LLM 판단으로 도메인 신뢰도 스크리닝할지, 도메인 화이트리스트로 처리할지 결정 필요
- Phase 2 쿼리 품질 검증 — h2_subtitle + core_message + assigned_keywords 조합 쿼리가 실제로 유의미한 소스를 반환하는지 v1 운영 데이터 보고 튜닝
- 수평 분해 leading_sentences 수 튜닝 — v1 운영 후 blueprint 품질 평가 후 조정
- 체험형 블로그 유입 비율 모니터링 — 비율 높으면 압축 방식 LLM 요약 전환 검토
- 대시보드 직접 수정 UX 구현 범위 — Phase 1-D 승인 링크로 이동하는 대시보드의 편집 항목 정의 필요
- Phase 1-D 파라미터 재주입 방식 — 사용자가 Slack에서 파라미터 선택(예: 템플릿 B) 시 Phase 1-B 재호출 프롬프트에 어떻게 변환·주입할지 (템플릿 → 구조 지시문 변환 방식, 파라미터별 프롬프트 템플릿 설계)

---

## 3. contents_maker

### 3.1 책임
collector가 만든 청사진을 받아 *HTML 형태의 완성된 글*로 변환. 이미지는 Unsplash에서 페치하여 본문에 통합.

### 3.2 입력
- collector의 출력 스키마 (전체)

### 3.3 출력
- `refined_post` (HTML, h1/h2/p/img 태그 포함)
- `image_urls` (Unsplash URL, paragraph_id별 매핑)
- 메타데이터 (글자 수, 사용 키워드 분포 등)

### 3.4 글 구조 (HTML — v5 확정)

```html
<h1>{title}</h1>
<p class="intro">{intro}</p>
<p class="short-conclusion">{short_conclusion}</p>

<!-- 본문 단락 반복 (5~7회) -->
<h2>{paragraph[i].h2_subtitle}</h2>
<img src="{image_url}" alt="{image_alt_text_ko}">
<p>{단락 본문}</p>
<!-- ... -->

<p class="ending">{결말}</p>
```

**Tistory 저장 시 자동 변환 (실측 확인)**
- `<strong>` → `<b>`, `<em>` → `<i>`
- `<p>` 태그에 `data-ke-size="size16"` 자동 추가
- `<ol>`에 `data-ke-list-type="decimal"` 자동 추가
- 외부 이미지 src는 변경 없이 그대로 저장 (CDN 자동 변환 없음)

### 3.5 내부 로직

#### 단락 타입별 처리 (v5 신규)

| 단락 타입 | 처리 방식 |
|-----------|-----------|
| `fact_based` | 정규화된 facts 목록을 컨텍스트로 받아 자연스러운 문장 생성 |
| `llm_generated` | 제목 + 전체 글 맥락 + core_message만으로 자유 생성 (도입·결말) |

#### Stage 1 — 이미지 페치 (Unsplash API)
- 단락별 `image_search_keywords_en`으로 Unsplash API 호출
- 각 단락당 1장
- **이미지 URL 정책**:
  - 외부 URL 그대로 사용 (Tistory CDN 자동 변환 없음 — 실측 확인)
  - `plus.unsplash.com` (Unsplash+) 유료 이미지 사용 금지
  - 무료 이미지(`unsplash.com`) 사용 시 사진작가 크레딧 필수

#### Stage 2 — 본문 글쓰기
- `fact_based` 단락: facts만 컨텍스트로 사용 (원본 소스 raw text 비노출 — 표절 방어)
- `llm_generated` 단락: 키워드 + core_message + 전체 글 맥락 + **`contents_maker.blogger_persona`** 컨텍스트 주입
- 최소 1500자 보장 (5~7개 단락 기준)

#### llm_generated 단락 작성 지침 (v16 신규 — AdSense AI 감지 대응)

**배경**: 과거 AdSense 심사에서 "AI 생성 느낌"으로 탈락한 경험이 있음. fact_based 단락은 원문 소스 팩트 기반이라 구체적이나, 도입부·결말은 순수 LLM 생성으로 전형적 AI 패턴에 노출될 위험이 있음. AdSense 통과가 v1 수익화 1단계 관문이므로 생성 단계에서 선제 대응.

**프롬프트 지침 (도입부·결말에 적용)**:
- 블로거 페르소나(`contents_maker.blogger_persona`)를 1인칭 목소리로 명시 (예: "홈카페 2년 차로서 직접 써보니...")
- 문장 길이를 의도적으로 불균일하게 — 긴 문장 뒤에 짧은 문장 혼용
- "~에 대해 알아보겠습니다", "이 글에서는 ~를 살펴볼 것입니다" 등 전형적 AI 도입 패턴 사용 금지
- 결말: 요약 나열 대신 블로거 개인 소감·다음 실험 예고 등 서술형으로 마무리

#### Stage 1·2 병렬화
- 이미지 페치는 글쓰기와 독립적이므로 백그라운드 병렬 실행 가능

### 3.6 DB 업데이트 시점
- 글쓰기 완료 후: `refined_post` (HTML), `image_urls` 저장, `status: 시스템검증대기`

### 3.7 논의된 트레이드오프와 결정
- **표절 방어 책임**: collector의 정규화로 1차 방어. contents_maker는 raw 소스 비노출.
- **이미지 호스팅**: 외부 URL 그대로 (Firebase 등 외부 호스팅 불필요). 멀티 플랫폼 발행 계획 시 재검토.
- **이미지 re-hosting**: Tistory가 자동으로 blog.kakaocdn.net에 올려주지 않음 (실측 확인). 외부 URL 원본이 살아있어야 함.

### 3.8 오픈 이슈
- Unsplash 크레딧 자동 삽입 위치 (글 하단 or alt text)
- 이미지 소스 대안 탐색 (Pexels, Pixabay — hot-linking 정책 비교 필요)
- `contents_maker.blogger_persona` 최초 설정 UX — 사용자가 1회 입력하면 config 테이블에 저장. 다중 계정 운영(v2) 시 계정별 페르소나 분리 필요 여부 검토

---

## 4. checker

### 4.1 책임
발행 직전, 글이 (a) 시스템 정합성/품질 기준을 만족하는지 (b) 사람의 최종 확인을 받는지 두 단계 게이트.

### 4.2 입력
- `refined_post` (HTML)
- `image_urls`
- collector의 청사진 (검증 기준값으로 사용 — 키워드 누락 검사 등)

### 4.3 출력
- 시스템 검증 통과 여부 + 항목별 결과
- 사람 검증 통과 여부 + 사용자 수정 반영본
- 발행 승인 시 `publishable: true` + 최종 HTML

### 4.4 내부 로직 — 두 단계 분리

#### Stage 1 — 시스템 검증

**원칙**: *결정적으로 풀 수 있는 검증은 LLM에 맡기지 않는다.*

**Tier A — 결정적 검증 (토큰 0)**
- 글자 수 ≥ 1500
- HTML 구조: h1×1, h2×3~7, p 태그 정상
- 이미지 개수 일치 + 모든 alt 비어있지 않음
- `assigned_keywords`가 본문에 실제 등장
- 외부 링크 유효성 (HEAD request)

**Tier B — 외부 API 검증**
- 표절 검사:
  - v1: 임베딩 기반 자기 소스 검사 (`jhgan/ko-sroberta-multitask` 로컬 실행) — refined_post 문장 vs collector 수집 원문 소스 문장 cross 비교
- 통과 게이트:
  - 전체 유사도 ≤ 15%
  - 문장 단위 최대 유사도 ≤ 30~40%

> **Google CSE 제거 (v16)**: 신규 계정 발급 불가 (2026년 현재 closed to new customers), 기존 계정 없음. 기능 중복 이유도 있음 — fact_based 단락은 collector 원문 소스 대조로 이미 커버되며, llm_generated 단락(도입부·결말)은 원문 직접 참조 없이 생성되어 외부 소스 표절 가능성 자체가 낮음. 광역 검사 필요성 재평가 결과 v1에서 불필요 판단.

**Tier C — LLM 검증**: v1에서 제외

#### Stage 2 — 사람 검증
- Slack에 미리보기 URL + 시스템 검증 결과 카드 발송 (HTML 포맷 기준)
- 대시보드에서 Before/After 인라인 편집
- 사용자 액션: ✅ 승인 / 🔄 수정 / ❌ 거절

**필수 검토 항목 (v16 신규 — AdSense AI 감지 대응)**:
- [ ] **도입부**: 전형적 AI 패턴 문장 없는지 확인. "~에 대해 알아보겠습니다" 류 → 블로거 목소리로 수정
- [ ] **결말**: 요약 나열형 아닌지 확인. 개인 소감 또는 다음 실험 예고형으로 수정
- [ ] **전체 톤**: 블로거 페르소나와 일치하는지 확인

> **배경**: AdSense 심사는 AI 생성 글을 감지하면 탈락시키는 것으로 알려져 있으며, 도입부·결말이 주요 감지 포인트일 가능성이 높음. 시스템 자동화로 1차 대응하되, Stage 2 사람 검토가 최종 방어선.
> **AI 감지 API 도입**: GPTZero·ZeroGPT 무료 티어로 한국어 정확도 실증 후 Tier B 추가 여부 결정 (현재 미결 — 오픈 이슈 참조)

### 4.5 DB 업데이트 시점
- 시스템 검증 완료 후: `system_check_result`, `plagiarism_overall`, `plagiarism_max_sentence` 저장, `status: 사용자검토중`
- 사용자 승인 후: 수정된 `refined_post` 저장, `status: 승인완료`

### 4.6 오픈 이슈
- Slack → 대시보드 인증 흐름 (deep link, OAuth?)
- 의심 문장 하이라이트 UI 디테일
- AI 감지 API 한국어 정확도 검증: GPTZero·ZeroGPT 무료 티어로 한국어 글 테스트 → 의미 있는 결과이면 Tier B에 추가. 영어 기반 도구라 정확도 불확실.

---

## 5. publisher

### 5.1 책임
승인된 글을 *어뷰징 정책 게이트*를 거쳐 Tistory에 자동 발행.

### 5.2 입력
- `publishable: true` 상태의 최종 HTML + 메타데이터
- 발행 정책 컨텍스트 (계정 발행 이력, 블로그 발행 이력)

### 5.3 출력
- `platform_url`, `published_at`
- 발행 실패 시 error_log + 재시도 결과

### 5.4 내부 로직

#### Tistory API 페이로드 (실측 확인)
```json
{
  "title": "황금 키워드 찾는 법",
  "content": "<p data-ke-size=\"size16\">...</p>",
  "tags": "",
  "draftSequence": null
}
```

#### Tistory Open API는 종료됨 → Playwright 우회
- Playwright headed 모드 또는 stealth (headless 금지 — bot 탐지 트리거)
- 사용자의 실제 로그인 세션 재사용 (쿠키/스토리지 보존)

#### 이미지 처리 (실측 확인)
- HTML에 박힌 외부 URL 이미지는 Tistory가 CDN으로 자동 변환하지 않음
- 외부 URL 그대로 저장/발행됨 → 원본 URL이 유효해야 이미지 표시
- alt text는 `<img alt="...">` 형태로 그대로 보존됨

#### 발행 정책 게이트 (어뷰징 회피)

| 정책 | v1 시작값 | 단위 | 비고 |
|------|-----------|------|------|
| 일일 발행 상한 | 2편 | 계정 | 발행 시점 실시간 카운트 |
| 발행 시간 분산 | 사용자 활동 시간대 안 랜덤 윈도우 | 계정 | 발행 직전 적용 |
| 연속 발행 유사도 쿨다운 | 직전 발행 글과 유사도 ≥ 0.85 → 3일 후 발행 예약 | 계정 | keyword_researcher와 별도로 재확인 (다중 큐 대기 시나리오 대응) |
| 작성-발행 텀 | 최소 30분 | 글 | 글 생성 완료 시각 기준 |

> **주제 연속 회피 항목 제거 이유**: keyword_researcher 회피 규칙 (a)(b)가 이미 키워드 선정 시점에 처리한다.
> publisher가 이를 재확인하는 건 중복이다. 단, (a) 쿨다운만 다중 큐 시나리오 대응을 위해 발행 직전 재확인한다.

### 5.5 DB 업데이트 시점
- 발행 완료 후: `platform_url`, `published_at` 저장, `status: 발행완료`
- 발행 실패 시: `error_log`, `publish_attempt_count` 업데이트, `status: 실패`

### 5.6 오픈 이슈
- Tistory 약관상 자동 발행 명시적 금지 조항 존재 여부 (확인 필요)
- Playwright 세션 만료/재로그인 처리 (캡차 회피)

---

## 6. 횡단 관심사 (Cross-Cutting)

### 6.1 데이터베이스 설계 (v7 accounts 테이블 추가)

#### 저장소 전략
- **v1**: PostgreSQL 로컬 (pgvector 확장 포함)
- **v2+**: PostgreSQL 클라우드 (Supabase 등)
- v1부터 pgvector 사용으로 `Vector(768)` 타입 그대로 적용 가능. v1 → v2 마이그레이션은 연결 문자열 교체 수준

#### 테이블 구조

**keywords** — 키워드 마스터 레지스트리
| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | String | 고유 ID |
| `keyword` | String | 키워드 텍스트 |
| `status` | Enum | active \| archived |
| `last_evaluated_at` | DateTime | 최근 평가 시각 (REVIVAL_DAYS 판단 기준, 풀 삭제 2순위 정렬 기준) |
| `embedding` | Vector(768) | 키워드 임베딩 (ko-sroberta, dim=768). 씨드 입력 중복 확인 및 어뷰징 쿨다운 체크에 사용. 키워드 등록 시 생성 |

**keyword_evaluations** — 평가 이벤트 로그 (keyword_history 역할)
| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | String | 고유 ID |
| `keyword_id` | String | keywords 참조 |
| `evaluated_at` | DateTime | 평가 시각 |
| `scoring_model_version` | String | 예: DEFAULT_v1, LONGTAIL_v1 |
| `raw_signals` | JSON | 원시 API 데이터. 필드명은 아래 참조 |
| `score_breakdown` | JSON | 항목별 환산 점수. 필드명은 아래 참조 |
| `total_score` | Float | 합산 점수. 풀 삭제 2순위 정렬 기준 (가장 최근 레코드 사용) |
| `profile` | Enum | DEFAULT \| LONGTAIL |
| `session_id` | String | 같은 세션에서 평가된 키워드 묶음 식별 |
| `result` | Enum | selected \| not_selected \| archived |

> evaluation_count, avg_score는 별도 컬럼 없이 이 테이블에서 실시간 집계 (COUNT, AVG). 풀 삭제 1순위 판단에 사용.

**raw_signals JSON 필드명 (v14 전면 변경)**

| 필드명 | 타입 | 설명 | 변경 이력 |
|---|---|---|---|
| `monthly_search_volume` | Int | PC + Mobile 합산 월간 검색량 | 🔄 `search_volume` → 신규명 |
| `blog_total_count` | Int | 블로그 검색 총 결과 수 (sort=sim) | 🔄 `competition_count` → 신규명 |
| `blog_recent_7d_count` | Int | 최근 7일 발행 수 | 🔄 `recent_density_14d` → 7일로 단축 |
| `blog_recent_30d_count` | Int | 최근 30일 발행 수 | 🆕 신규 (월간 추이용) |
| `comp_idx` | String | 광고 경쟁 지수 (낮음/중간/높음) | 🆕 신규 (상업적 의도 proxy ①) |
| `shopping_total` | Int | 쇼핑 검색 총 결과 수 | 🆕 신규 (상업적 의도 proxy ②) |
| `commercial_pattern_score` | Int | 구매 의도 패턴 룰 점수 (0~3) | 🆕 신규 (상업적 의도 proxy ③) |
| `datalab_slope` | Float | DataLab 8주 ratio 선형 회귀 기울기 | 🔄 `google_trend_score` → 신규명 |

**score_breakdown JSON 필드명 (v14 변경)**

| 필드명 | 타입 | 점수 범위 (DEFAULT) | 변경 이력 |
|---|---|---|---|
| `search_volume` | Int | 0~30 | 🔄 `datalab_trend` 대체 (30점으로 상향) |
| `blog_competition_volume` | Int | 0~15 | 🔄 `blog_competition` 분리 (구조는 v4 이후 동일) |
| `blog_competition_density` | Int | 0~15 | 🔄 `blog_competition` 분리 (구조는 v4 이후 동일) |
| `commercial_intent` | Int | 0~20 | ✅ 유지 (측정 방법 신규 확정) |
| `trend_slope` | Int | 0~10 | 🔄 `google_trends` 대체 |

**keyword_usages** — 블로그별 사용 이력
| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | String | 고유 ID |
| `keyword_id` | String | keywords 참조 |
| `account_id` | String | 사용자 계정 |
| `blog_id` | String | 블로그 식별자 (자기 잠식 체크 단위) |
| `contents_id` | String | contents 테이블 참조 |
| `published_at` | DateTime | 발행 시각 (null이면 발행 전) |
| `status` | Enum | in_progress \| published \| failed. **파이프라인이 어떤 이유로든 중단되면(사용자 거부·중단 요구·기술 오류) failed로 갱신 → in_progress 잠금 즉시 해제. published_at은 null 유지 (180일 카운트 없음). 재선택 여부는 사용자가 결정** |

**accounts** — 티스토리 계정 데이터 (v7 신규)
| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | String | 고유 ID |
| `platform` | String | "tistory" (v3 멀티 플랫폼 대비) |
| `blog_id` | String | 블로그 식별자 |
| `login_id` | String | 로그인 이메일/ID |
| `cookie_path` | String | 쿠키 파일 경로 (`./cookies/tistory_{blog_id}.json`) |
| `cookie_updated_at` | DateTime | 쿠키 마지막 갱신 시각 |
| `is_active` | Boolean | 계정 활성 여부 |

> Tistory 공식 API 종료로 Playwright 세션 우회 사용. 계정 정보는 앱 시크릿이 아닌 사용자 계정 데이터이므로 .env가 아닌 DB 관리.
> 쿠키 만료 시 v1: Slack 알림 → 담당자 수동 재로그인. v2: 자동 재로그인 전환 검토.

**contents** — 콘텐츠 파이프라인
| 필드 | 타입 | 설명 | 업데이트 모듈 |
|------|------|------|---------------|
| `id` | String | 고유 ID | collector (생성) |
| `keyword_id` | String | keywords 참조 | collector (생성) |
| `title` | String | 글 제목 (h1). Tistory 발행 시 본문과 별도 입력 필드에 사용 | collector Phase 1 |
| `status` | Enum | 파이프라인 상태 전이 | 각 모듈 |
| `paragraph_blueprint` | JSON | 단락별 구조 + 타입 + target_reader (persona, knowledge_level, primary_intent, reader_awareness) | collector Phase 1 |
| `collection_context` | JSONB | Phase 1-A 출력 원본 (collection_type, chunks, datalab_slope, reference_blogs). Phase 1-D에서 content_template.type 변경 시 Phase 1-B 재호출 재료로 사용 | collector Phase 1 |
| `normalized_sources` | JSON | 단락별 정규화 팩트 | collector Phase 2 |
| `refined_post` | HTML | 최종 HTML 글 | contents_maker |
| `image_urls` | JSON | 단락별 이미지 URL 매핑 | contents_maker |
| `system_check_result` | JSON | 결정적 검증 항목별 결과 | checker Stage 1 |
| `plagiarism_overall` | Float | 전체 유사도 | checker Stage 1 |
| `plagiarism_max_sentence` | Float | 문장 단위 최대 유사도 | checker Stage 1 |
| `summary_embedding` | Vector | title + intro + short_conclusion 합산 임베딩. 자기잠식 체크 및 자기표절 1차 스크리닝용. contents 테이블 전체(모든 status)와 비교 | collector Phase 1 |
| `platform_url` | String | 발행된 티스토리 URL | publisher |
| `published_at` | DateTime | 실제 발행 시각 | publisher |
| `publish_attempt_count` | Int | 발행 재시도 횟수 | publisher |
| `error_log` | Text | 에러 메시지 | 각 모듈 |
| `created_at` | DateTime | 레코드 생성일시 | collector (생성) |

**config** — 임계치·파라미터 런타임 관리 (총 **20개**)
| 필드 | 타입 | 설명 |
|------|------|------|
| `key` | String | dot notation: `{module}.{parameter_name}` 형식 (예: `publisher.daily_limit`) |
| `value` | String | 문자열 저장, 코드에서 타입 변환 |
| `updated_at` | DateTime | 마지막 수정 시각 |

> 코드 수정 없이 파라미터 조정 가능. 값 조회 우선순위: 환경변수 > config 테이블 > 코드 기본값

**config 초기값 목록 (v1) — 총 21개**

| key | 설명 | v1 시작값 | 조정 트리거 |
|-----|------|-----------|-------------|
| `keyword.min_search_volume` | 하드컷 조건 ① — 이 값 미만의 월간 검색량이면 점수 계산 없이 폐기. 수요 없는 키워드 차단 | **500** | 폐기율 너무 높거나 낮으면 |
| `keyword.min_blog_count` | 하드컷 조건 ③ — 이 값 미만의 blog_total_count면 점수 계산 없이 폐기. collector 레퍼런스 확보 가능성 없는 키워드 차단 | **30** | ⚠️ 케이스 발생 빈도 보고 |
| `keyword.pool_max_size` | 키워드 풀 최대 보관 수. 초과 시 삭제 정책 실행 | **50** | 풀이 자주 꽉 차거나 거의 안 차면 |
| `keyword.pool_eviction_score_threshold` | 풀 삭제 1순위 조건 — 부스러기 등급 상한 점수. avg_score가 이 값 미만이면 삭제 후보 | **45** | 삭제가 너무 자주/거의 안 일어나면 |
| `keyword.pool_eviction_eval_count` | 풀 삭제 1순위 조건 — 최소 평가 횟수. 이 값 이상 평가받은 키워드만 1순위 삭제 대상 | **3** | 초반에 삭제가 안 일어나면 낮춤 |
| `keyword.revival_days` | 평가된 키워드를 재평가 대상으로 올리기까지 최소 대기 일수 | 30 | 재평가 결과가 첫 평가와 차이 없으면 |
| `keyword.reuse_days` | 동일 블로그에서 같은 황금 키워드 재사용 금지 기간 (자기 잠식 방지) | 180 | 발행 후 SEO 데이터 보고 판단 |
| `keyword.similarity_cooldown_threshold` | 기발행 글과 의미 유사도가 이 값 이상이면 쿨다운 적용 (어뷰징 회피) | 0.85 | 쿨다운이 너무 자주/거의 안 걸리면 |
| `keyword.similarity_cooldown_days` | 유사도 초과 시 해당 키워드 선정을 금지하는 기간 | 3 | 실제 계정 패턴 탐지 여부 보고 |
| `keyword.recent_density_window_days_short` | 최근 발행 밀도 계산 — 단기 창 (과포화 탐지, primary). Blog 경쟁도 최근 밀도 점수에 사용 | **7** | 단기 트렌드 반응 속도 조정 시 |
| `keyword.recent_density_window_days_long` | 최근 발행 밀도 계산 — 장기 창 (월간 추이 참고용) | **30** | 월간 추이 기준 변경 시 |
| `keyword.golden_threshold` | 황금 키워드 선정 최소 점수 (100점 만점). 미설정 시 코드 기본값 60 사용 | 코드 기본값 60 | v1 첫 발행 데이터 쌓인 후 |
| `keyword.seed_duplicate_threshold` | 씨드 입력 시 keywords.embedding 유사도가 이 값 이상인 기존 키워드가 있으면 "이거 말씀하시나요?" 안내 표시 | 0.93 | 안내가 너무 자주/거의 안 뜨면 |
| `keyword.irrelevant_filter_threshold` | relKeyword 후보 중 씨드 임베딩과의 유사도가 이 값 미만이면 평가 대상에서 제외 (무관 키워드 필터). 0.55 기준 10~20개/실행 통과 예상 | **0.55** | 필터링이 너무 많거나 노이즈가 많이 통과하면 |
| `collector.min_blogs` | Phase 1 fallback 기준 — 경쟁 블로그 최소 수. 미달 시 상위 개념 재검색 → LLM 단독 + ⚠️ | 3 | 니치 키워드 비율 데이터 보고 |
| `collector.similarity_warning_threshold` | collector Phase 1에서 summary_embedding 비교 시 유사도 경고를 표시할 임계치. 이 값 이상이면 Slack 화면에 경고 표시 → 사용자 판단 | 0.75 | 경고가 너무 자주/거의 안 뜨면 |
| `checker.plagiarism_overall_threshold` | 글 전체 표절 유사도 허용 상한. 초과 시 시스템 검증 탈락 | 0.15 | 통과율 너무 낮거나 표절 누락 시 |
| `checker.plagiarism_sentence_threshold` | 문장 단위 최대 유사도 허용 상한. 전체가 낮아도 특정 문장 초과 시 탈락 | 0.35 | — |
| `checker.min_char_count` | 발행 가능 최소 글자 수. 미달 시 시스템 검증 탈락 | 1500 | 발행 글 품질 피드백 반영 시 |
| `publisher.daily_limit` | 계정당 하루 최대 발행 편수. 초과분은 다음 날로 순서 유지하며 hold | 2 | 어뷰징 탐지 신호 있으면 즉시 낮춤 |
| `publisher.min_draft_minutes` | 글 생성 완료 시각부터 발행까지 최소 대기 시간 (분). 즉시 발행 패턴 방지 | 30 | — |
| `publisher.similarity_cooldown_threshold` | 직전 발행 글과 유사도 이 값 이상이면 발행을 쿨다운 기간 후로 자동 지연. 다중 큐 대기 시나리오 대응 | 0.85 | `keyword.similarity_cooldown_threshold`와 함께 조정 |
| `publisher.similarity_cooldown_days` | 연속 발행 유사도 초과 시 발행을 미루는 일수 | 3 | `keyword.similarity_cooldown_days`와 함께 조정 |
| `contents_maker.blogger_persona` | 블로거 1인칭 페르소나 설명. llm_generated 단락(도입부·결말) 작성 시 컨텍스트로 주입. AdSense AI 감지 대응 목적 | `""` (최초 사용자 입력 필요) | 심사 탈락 시 페르소나 톤 재조정 |

> **v13 → v14 config 변경**: `keyword.recent_density_window_days` (14일) 단일 항목 → `keyword.recent_density_window_days_short` (7일) + `keyword.recent_density_window_days_long` (30일) 2개로 분리. 총 19개 → 20개.
> **v14 → v15 config 변경**: `keyword.irrelevant_filter_threshold` (0.55) 신규 추가. 총 20개 → **21개**.
> **v15 → v16 config 변경**: `contents_maker.blogger_persona` 신규 추가. 총 21개 → **22개**.
> **v16 → v17 config 변경**: `keyword.min_search_volume` (500), `keyword.min_blog_count` (30) 하드컷 조건 신규 추가. 총 22개 → **24개**.

#### contents status 전이

```
구조확정대기 → 생성대기 → 시스템검증대기 → 사용자검토중 → 승인완료 → 발행완료
                                                          ↘ 실패 / 발행차단
```

> **keyword_usages.status와 contents.status는 독립적**: contents가 실패 상태가 되더라도 keyword_usages는 별도로 failed 갱신 처리가 필요. 어느 단계에서 중단되든 keyword_usages.status = failed → in_progress 잠금 해제.

#### DB 업데이트 타임라인 요약

| 시점 | 모듈 | 업데이트 내용 |
|------|------|---------------|
| **실행 시작 시 housekeeping** | keyword_researcher | ① 이물질 탐지(last_evaluated_at IS NULL) → DELETE + 알림 → ② revival_days 초과 키워드 재평가 → keyword_evaluations 기록 → 저품질 archived → pool_max_size 초과 시 삭제 정책 실행 |
| 씨드 확장 + 평가 | keyword_researcher | keywords 적재, keyword_evaluations 기록 |
| 황금 키워드 선정 | keyword_researcher | keyword_evaluations.result = selected, keyword_usages 생성 (`status = in_progress`) |
| **파이프라인 중단** (사유 불문) | 중단 발생 모듈 | **keyword_usages.status = failed 갱신 → in_progress 잠금 해제. published_at = null 유지 (180일 카운트 없음). 재선택 여부는 사용자 결정** |
| 구조 확정 | collector Phase 1 | contents 레코드 생성, title + paragraph_blueprint(target_reader 포함) + collection_context + summary_embedding, status: 구조확정대기 |
| 팩트 수집 완료 | collector Phase 2 | normalized_sources, status: 생성대기 |
| 글 생성 완료 | contents_maker | refined_post, image_urls, status: 시스템검증대기 |
| 시스템 검증 완료 | checker Stage 1 | system_check_result, plagiarism_*, status: 사용자검토중 |
| 사용자 승인 | checker Stage 2 | refined_post (수정분), status: 승인완료 |
| 발행 완료 | publisher | platform_url, published_at, status: 발행완료, keyword_usages.published_at 갱신, **keyword_usages.status = published** |

### 6.2 키워드 재평가 (REVIVAL_DAYS) 규칙
- keyword_pool은 더 이상 Google Sheets가 아닌 **keywords 테이블**로 관리
- 재평가 트리거: keyword_researcher **매 실행 시 시작 단계**에서 자동 수행 (Option A, v13 확정)
- 재평가 필요 여부: `keywords.last_evaluated_at` + REVIVAL_DAYS (config 관리) 기준
- 재사용 가능 여부: `keyword_usages`에서 해당 `blog_id`의 최근 발행일(`published_at`) 기준 (블로그 단위 독립)
  - `status = failed` 레코드는 `published_at = null`이므로 180일 카운트에 포함되지 않음
- 동일 키워드라도 다른 블로그(M, N)에서는 독립적으로 사용 가능
- 아카이브 기준: 재평가 시 저품질 판정 → `keywords.status = archived`
  - archived 시 연결된 `keyword_evaluations`도 함께 삭제 (데이터 일관성)
- 활성 키워드 상한: `config.keyword.pool_max_size` (v1 시작값 **50**)

### 6.3 임베딩 인프라
- 한국어 sentence embedding 모델 (`jhgan/ko-sroberta-multitask` 등)
- v1은 로컬 실행 (비용 0)

**용도별 정리**

| 용도 | 비교 대상 | 시점 | 저장 여부 | 임계치 |
|------|-----------|------|-----------|--------|
| 씨드 입력 중복 확인 (UX) | 입력 씨드 임베딩(즉석 생성) vs `keywords.embedding` 전체 | keyword_researcher 씨드 입력 시 | ❌ 별도 저장 없음 | `keyword.seed_duplicate_threshold` = 0.93 |
| 어뷰징 쿨다운 체크 | 황금 키워드 후보 `keywords.embedding` vs 기발행 글의 황금 키워드 `keywords.embedding` | keyword_researcher 황금 키워드 선정 시 | ❌ 별도 저장 없음 (keywords 테이블 조회) | `keyword.similarity_cooldown_threshold` = 0.85 |
| 자기잠식 + 자기표절 1차 스크리닝 | 새 글 `summary_embedding` vs 기존 모든 글 `summary_embedding` | collector Phase 1 완료 후 | ✅ contents.summary_embedding에 저장 | `collector.similarity_warning_threshold` = 0.75 (경고 표시) |
| 표절 검사 (외부 소스 대조) | refined_post 문장 vs 매핑된 original source 문장 (문장 단위 cross 비교) | checker Stage 1 | ❌ 결과만 저장 (plagiarism_overall, plagiarism_max_sentence) | `checker.plagiarism_overall_threshold` = 0.15 / `checker.plagiarism_sentence_threshold` = 0.35 |
| 어뷰징 쿨다운 재확인 | 발행 예정 글 `summary_embedding` vs 직전 발행 글 `summary_embedding` | publisher | ❌ 별도 저장 없음 (contents 테이블 조회) | `publisher.similarity_cooldown_threshold` = 0.85 |

> **씨드 중복 확인**: 씨드 입력 시 keywords.embedding 즉석 비교로 유사 키워드 안내. 재평가 흐름과 자연스럽게 연결.
> **어뷰징 쿨다운 비교 대상 확정**: keyword_researcher에서는 keyword embedding끼리 비교 (keyword vs keyword). publisher에서는 summary_embedding끼리 비교 (article vs article). 두 비교 대상이 다름에 유의.
> **자기잠식 체크 역할 분리**: keyword_researcher는 keyword 텍스트 기반 DB 조회(keyword_usages)로 동일 키워드 중복 진입을 차단. 의미 수준 자기잠식은 collector Phase 1으로 이동.
> **자기표절 vs 표절 분리**: summary_embedding 비교(Phase 1, 임계치 0.75)는 내 글 vs 내 글의 조기 경보. checker의 문장 단위 비교는 내 글 vs 외부 소스의 정밀 검사.

### 6.4 Slack 알림 컨벤션
- collector Phase 1 완료: 구조 초안 + 사용자 검토 요청
- contents_maker 완료: 시스템 검증으로 자동 진입
- checker 시스템 검증 완료: 미리보기 URL + 결과 카드 (HTML 기준)
- publisher 완료: 발행 URL
- 실패: 단계 + 에러 메시지

### 6.5 토큰/비용 관리
- **LLM 사용처**: collector (시장조사 분석, 구조 초안, 팩트 추출), contents_maker (글쓰기)
- **LLM 비사용처**: keyword_researcher 점수화, checker 결정적 검증, publisher 정책 게이트
- **임베딩**: 로컬 모델
- **외부 API**: Firecrawl (소스), Unsplash (이미지)

---

## 7. 미결 태스크 (다음 미팅 우선 논의)

| 우선순위 | 태스크 | 내용 |
|----------|--------|------|
| — | ~~**keyword_pool ↔ contents_db 분리 구조 확정**~~ | ✅ 완료 (v6) |
| — | ~~**config 테이블 초기값 목록 확정**~~ | ✅ 완료 (v7, 15개 항목 + dot notation 컨벤션) |
| — | ~~**keyword_researcher housekeeping 트리거 방식 확정**~~ | ✅ 완료 (v13, Option A — 매 실행 시 내재화) |
| — | ~~**풀 삭제 정책 확정**~~ | ✅ 완료 (v13, 2단계 정책 + 키워드 등급 체계) |
| — | ~~**contents 테이블 컬럼 재검토**~~ | ✅ 완료 (v13 확인) |
| — | ~~**키워드 등급 중간 구간 이름 정의**~~ | ✅ 완료 — **강철** (46~59점) 확정 |
| — | ~~**점수 모델 구현 명세 확정**~~ | ✅ 완료 (KEYWORD_SCORING_SPEC_20260509 → v14 반영) |
| — | ~~**무관 키워드 필터링 기준**~~ | ✅ 완료 (v15 — 씨드 임베딩 anchor, threshold=0.55 확정) |
| 1 | **씨드 분해 로직 명세** | "홈카페 원두 추천" → ["홈카페", "원두", "추천"] 분해 규칙. 형태소 분석기 vs 공백 split 결정 필요. relKeyword 전환으로 중요도 상승 (hintKeywords 제약 직결) |
| 2 | **무관 키워드 필터 임계치 실측 검증** | ko-sroberta로 대표 키워드 쌍 테스트 → 0.55 초기값 적정성 확인. `test_searchad_api.py` 방식으로 30분 내 검증 가능 |
| 3 | **Search Ad API 일일 호출 한도 확인** | Naver Open API 25,000회/일 한도와 별도 관리되는지 콘솔 확인 필요 |
| 4 | **점수 환산 구간 재보정** | v1 운영 후 실제 키워드 분포 확인 → 사분위수 기반 구간 조정. 현재 값은 가설 기반 |
| — | ~~**모듈별 무료 API·MCP 사용 한도 정리**~~ | ✅ 완료 (API_LIMITS_20260509.md) |
| 5 | **AI 감지 API 한국어 정확도 실증** | GPTZero·ZeroGPT 무료 티어로 한국어 생성 글 테스트. 유의미한 결과이면 checker Tier B에 추가. 영어 기반 도구라 한국어 정확도 불확실 — 검증 선행 필요 |

---

## 8. 오픈 이슈 (시스템 전체)

1. **발행 플랫폼**: Tistory 단일 vs 멀티 플랫폼 로드맵 (이미지 호스팅 결정에 영향)
2. ~~**수정 흐름 UX**: 슬랙 답글 vs 대시보드 인라인 편집~~ → ✅ v19 확정: Slack 답글(파라미터 선택) + 대시보드 링크(세밀 편집) 병행
3. **카피킬러 정식 도입 시점**: 트래픽 임계 결정
4. **이미지 소스 대안 탐색**: Pexels/Pixabay hot-linking 정책 vs Unsplash API 크레딧 의무
5. **상위 블로그 5개 미달 시 fallback**: 니치 키워드 예외 처리
6. ~~**Google CSE 2027년 1월 서비스 종료**~~: v16에서 제거 완료 (계정 없음 + 기능 중복). 광역 표절 검사 필요성 재평가 결과 v1 범위 밖으로 판단.
7. **AdSense AI 감지 대응**: contents_maker 페르소나 주입 + Stage 2 필수 검토로 1차 대응. AI 감지 API(GPTZero 등) 한국어 정확도 검증 후 checker Tier B 추가 여부 결정.

---

## 9. 변경 이력 (Changelog)

### v23 (2026-05-22) — 수직 확장 최대 단계 2→1 하향

- **수직 확장 max_levels 변경 (2.4)**: `min(2, 청크수-1)` → `min(1, 청크수-1)`. Level 2는 "상황 맥락" 청크까지 제거되어 Phase 1-B가 해당 단락을 레퍼런스 없이 창작해야 하는 환각 위험 존재. 환각 최소화를 파이프라인 원칙으로 확인하고 Level 1으로 제한. Level 1은 타겟 독자 수식어 수준의 맥락 희석이며, Phase 1-B의 original_keyword 참조 + Phase 2 소스로 커버 가능.
- **collection_type `vertical_expansion_level2` 제거 (2.4)**: max_levels 1 제한에 따라 해당 타입 삭제.
- **트래킹 방침 추가 (2.6)**: v1 운영 후 Level 1 글 성과(조회수·체류시간) 기반으로 max_levels 재검토. 상세: COLLECTOR_PHASE1A_SPEC_20260522_v4.md Section 9.3.
- **선행 문서 갱신**: COLLECTOR_PHASE1A_SPEC_20260517_v3.md → COLLECTOR_PHASE1A_SPEC_20260522_v4.md

### v22 (2026-05-21) — contents 테이블 컬럼 개정

- **`target_reader` 독립 컬럼 제거 (6.1)**: `paragraph_blueprint` 내부에 이미 포함된 중복 필드. 별도 컬럼 제거로 단일 저장 위치 확정.
- **`collection_context` JSONB 컬럼 신규 추가 (6.1)**: Phase 1-A 출력(collection_type, chunks, datalab_slope, reference_blogs)을 그대로 저장. Phase 1-D에서 사용자가 `content_template.type` 변경 시 Phase 1-B 재호출 재료로 사용. `collection_type` 조회 필요 시 JSONB 연산자(`->>'collection_type'`)로 접근 가능 — 독립 컬럼 불필요.
- **DB 업데이트 타임라인 갱신 (6.2)**: 구조 확정 시점 저장 필드 목록에 `collection_context` 추가, `target_reader` 제거.

### v21 (2026-05-21) — collector 출력 스키마 개정, Phase 1-D 수정 선택지 간소화

- **target_reader 확장 (2.3)**: `primary_intent` 값 영문화 (`learn | buy | solve`). `reader_awareness` 신규 추가 (`unaware | problem_aware | solution_aware | product_aware`) — 독자 인식 단계와 목적(intent)은 독립된 축으로 분리
- **overall_tone 폐지 → tone_style 신규 (2.3)**: 구조와 목소리 혼용 문제 해소. `voice`(friendly | professional | analytical) + `emotion`(neutral | persuasive | empathetic) 두 축으로 분리. 구조는 `content_template`이 담당
- **inferred_template_type 폐지 → content_template 신규 (2.3, 2.4)**: `type` 고정 어휘(problem_solving | comparison | data_analysis | story) + `flow` 자유 텍스트 배열 하이브리드. `type`은 로그/분석용 레이블, `flow`는 contents_maker가 단락별로 직접 참조하는 지시문. type별 유효 스텝 수 검증
- **ending 구조 확장 (2.3)**: `type` → `style`, `direction` → `next_action`(자유 텍스트) 변경. `cta_strength`(soft | hard) 신규 추가 — style이 cta/recommendation일 때만 유효
- **Phase 1-D Slack 수정 선택지 4종 → 2종 간소화 (2.4)**: 결정 피로도 감소 목적. Slack에서는 임팩트 가장 큰 `content_template.type`(구조) + `tone_style.voice`(느낌) 2종만 제공. `tone_style.emotion`, `target_reader` 세부값, `ending`, `content_template.flow`는 대시보드 세밀 편집 영역으로 분리
- **Phase 1-D 기본 메시지 업데이트 (2.4)**: 폐지된 필드명 제거, 신규 스키마 필드명으로 전면 갱신

### v20 (2026-05-21) — DB 저장소 v1부터 PostgreSQL(로컬) 확정

- **DB 저장소 전략 변경 (6.1)**: v1 SQLite → **PostgreSQL 로컬**. v2+는 PostgreSQL 클라우드(Supabase 등). SQLite 관련 표현 전면 제거.
- **`summary_embedding` 타입 유지**: pgvector 네이티브 지원으로 `Vector(768)` 타입 그대로 사용 가능. SQLite BLOB/JSON 우회 처리 불필요.
- **v1 → v2 마이그레이션 부담 최소화**: 동일 PostgreSQL 엔진이므로 연결 문자열 교체 수준.

### v19 (2026-05-17) — Phase 1-D 사용자 알림 UX 확정, Phase 2 소스 탐색 명세, 공신력 소스 범위 확정, 다중 소스 매핑 명시

- **Phase 1-B 역할 재정의 (2.4)**: Slack 전송 분리 → Phase 1-D로 이동. Phase 1-B는 blueprint 생성 + `inferred_template_type` 출력 + Phase 1-D로 전달까지만 담당.
- **Phase 1-D 신규 명세 (2.4)**: 사용자 Slack 알림 + 조건부 파라미터 수정 선택 UX 전체 설계.
  - 기본 메시지(항상 전송): 키워드, 제목, 단락 구성, 템플릿 타입, 승인 / 대시보드 링크 포함
  - 조건부 수정 선택(similarity ≥ 0.75일 때만): target_reader / overall_tone / ending / template 4개 파라미터 수정 선택 제공. 유사도 낮은 경우 불필요한 선택 피로 제거 목적.
  - 파라미터 수정 시 Phase 1-B 재호출 (동일 압축 블로그 재사용 — 추가 Firecrawl 없음)
  - 대시보드 직접 수정: Slack 메시지에 링크 첨부. 단락 수준 세밀 편집은 대시보드에서.
- **템플릿 타입 4종 파라미터화 (2.4)**: A(문제 해결형) / B(비교형) / C(데이터 분석형) / D(스토리형). Phase 1-B `inferred_template_type`으로 추론 후 Phase 1-D에서 사용자 변경 가능.
- **Phase 2 구조 분리 (2.4)**: Phase 2-A(소스 탐색) + Phase 2-B(팩트 정규화 + 소스 저장) 명확화.
- **Phase 2-A 쿼리 필드 명세 (2.4)**: `h2_subtitle` + `core_message` + `assigned_keywords` 3개 필드 조합으로 검색 쿼리 구성 확정. 기존 "단락 주제"라는 추상적 표현 → 명시적 필드 매핑.
- **공신력 소스 범위 확정 (2.4)**: 뉴스·매거진·칼럼·공공기관 자료. 개인 블로그·포럼·광고성 콘텐츠 제외.
- **다중 소스 per 단락 명시 (2.4)**: 하나의 단락에 여러 소스의 팩트 매핑 허용. facts 배열 구조가 이미 지원하나 의도를 명문화. source_url per fact가 Checker cross 비교의 기준 링크임을 명시.
- **2.6 트레이드오프 항목 추가**: Phase 1-D 조건부 수정, Phase 2 쿼리 필드 선택, 공신력 소스 범위, 다중 소스 결정 배경.
- **2.7 오픈 이슈 업데이트**: "단락 구조 초안의 Slack 전송 UX 설계" → ✅ 완료. 대시보드 직접 수정 UX 구현 범위 신규 등록.

### v18 (2026-05-17) — collector Phase 1 설계 고도화

(동일 날짜 이전 버전)

### v16 (2026-05-12) — Google CSE 제거, 블로거 페르소나 도입, AdSense AI 감지 대응 전략 반영

- **Google CSE 제거 (4.4)**: 신규 계정 발급 불가(2026년 현재 closed to new customers) + 계정 미보유 확인. 기능 중복 사유 병기 — fact_based 단락은 collector 원문 소스 대조로 커버, llm_generated 단락은 원문 직접 참조 없이 생성되어 외부 소스 표절 가능성 낮음. v1에서 광역 검사 불필요 판단.
- **블로거 페르소나 도입 (3.5, 6.1)**: `contents_maker.blogger_persona` config 항목 신규 추가. llm_generated 단락(도입부·결말) 작성 시 1인칭 페르소나 컨텍스트 주입. config 총 **22개**.
- **llm_generated 단락 작성 지침 신규 (3.5)**: AdSense AI 감지 대응 목적. 전형적 AI 패턴 금지 문구 목록, 페르소나 기반 직접 경험 서술, 문장 길이 불균일 혼용 지침 포함.
- **checker Stage 2 필수 검토 항목 추가 (4.4)**: 도입부·결말 AI 패턴 검토 체크리스트 명시. 시스템 자동화 1차 대응 + 사람 검토 최종 방어선 구조.
- **AI 감지 API 오픈 이슈 등록 (4.6, 8)**: GPTZero·ZeroGPT 무료 티어 한국어 정확도 검증 후 Tier B 추가 여부 결정.
- **오픈 이슈 #6 완료 처리 (8)**: Google CSE 종료 이슈 → 제거로 해결. AdSense AI 감지 대응 신규 이슈(#7) 등록.
- **미결 태스크 갱신 (7)**: API 한도 정리 → 완료 처리. AI 감지 API 검증 신규 추가.
- **외부 API 목록 갱신 (6.5)**: Google CSE 제거.

### v15 (2026-05-11) — 씨드 확장 relKeyword 전환, 무관 키워드 필터 신규, 씨드 중복 확인 분기 재정의, 중복 노출 정책, Rank UI 명세, --recommend 모드 정의, pool 적재 방식 명시

- **씨드 확장 방식 전환 (1.4)**: Naver 자동완성(키워드 단독 유입 8개 고정) → Search Ad API `/keywordstool` relKeyword 배열로 교체. 변경 배경: relKeyword는 월 검색량 평가 시 이미 호출하는 동일 endpoint → **추가 API 호출 0회**. 자동완성 대비 상업적 의도가 더 강한 연관어 반환, 최대 ~100개 후보 확보 가능
- **무관 키워드 필터 신규 (1.4)**: relKeyword 후보 100개 → 씨드 임베딩 앵커(원문 구문) 기준 코사인 유사도 측정 → `keyword.irrelevant_filter_threshold`(0.55) 미만 제거. 임베딩 모델: ko-sroberta-multitask. 앵커를 씨드 원문으로 설정한 이유: 기존 풀 키워드 기준으로 쓸 경우 신규 토픽 전체가 필터 아웃되는 문제 회피. 기대 통과 수: 10~20개/런
- **임베딩 재사용**: 씨드 임베딩은 중복 확인(seed_duplicate_threshold) 단계에서 이미 생성 → 무관 필터 단계에서 재사용, **추가 연산 0회**
- **씨드 입력 중복 확인 분기 재정의 (1.4)**: 유사 기존 키워드 발견 시 단순 재평가 안내에서 2-path flow로 확장. Path A — 기존 키워드 재평가 전용(확장 없음). Path B — 새 씨드로 취급, relKeyword 확장 + 무관 필터 + 평가 전체 실행. 사용자가 Slack에서 경로 선택
- **중복 확인 노출 정책 확정 (1.4)**: 중복 후보 목록에 어뷰징 쿨다운·자기잠식 신호 라벨만 표시(⚠️ 어뷰징 쿨다운 / ⚠️ 자기잠식 신호). 사전 필터링 없음. 이유: 어뷰징·자기잠식 체크는 황금 키워드 선정 시점에 최종 수행 — 두 곳에서 필터링하면 로직 중복 및 예외 처리 복잡도 상승
- **Rank UI 명세 신규 (1.4)**: 아케이드 스코어보드 스타일. Top 5 키워드 항상 표시(점수 기준). 이번 세션 신규 진입 후보는 `(new)` 라벨 부착. 신규 후보가 top 5 외 순위 → 해당 순위와 함께 top 5 아래 구분 표시
- **`--recommend` 모드 명시 (1.4)**: 확장·평가 없이 기존 active 풀에서 top 5만 반환. 별도 Slack 프롬프트 스타일 유지
- **Pool 적재 방식 명시 (1.4)**: 무관 필터 통과 + 평가 완료된 n개 후보 **전량 pool 적재**. 등급 기반 사전 필터 없음(평가 전 등급 미확정). overflow는 기존 eviction 정책(pool_max_size, pool_eviction_score_threshold, pool_eviction_eval_count)이 처리
- **config 항목 추가 (6.1)**: `keyword.irrelevant_filter_threshold` = 0.55 신규 추가. 총 **21개** 항목. 조정 기준: 0.55 미만 시 "쌀20KG", "요구르트" 수준 무관어 제거, 동일 카테고리 연관어는 통과 확인 필요 (임계치 보정은 ko-sroberta 실증 실험 후 재조정 예정)
- **housekeeping 이물질 처리 정책 확정 (1.4, 6.1)**: `last_evaluated_at IS NULL` 키워드는 정상 흐름에서 발생 불가(평가가 풀 적재 전제). 발견 시 트랜잭션 버그로 간주 → 로그/Slack 알림 + `keywords` 즉시 DELETE. 외래 키 연쇄 삭제 없음(keyword_evaluations·keyword_usages 레코드 미존재).
- **미결 태스크 갱신 (7)**: 무관 키워드 필터 임계치 결정·`last_evaluated_at = null` 정책 → 완료 처리. ko-sroberta 실증 검증 신규 추가. 씨드 분해 로직·Search Ad API 한도 확인 미결 유지

### v14 (2026-05-11) — 점수 모델 구현 명세 반영 (KEYWORD_SCORING_SPEC_20260509 동기화)

- **점수 모델 가중치 테이블 전면 교체 (1.4)**: DataLab 트렌드 40점 폐지 → 월 검색량 30점(Search Ad API) + 발행 추세 10점(DataLab slope)으로 분리. Google Trends 10점 폐지 → DataLab slope 10점 대체. 총 100점 유지. 변경 배경: DataLab ratio 상대값 문제, pytrends archived, 실 트래픽 구글 비중 0.1%
- **Blog 경쟁도 기간 재정의 (1.4)**: 최근 발행 밀도 기준 14일 단일 → 7일(primary, 단기 과포화 탐지) + 30일(월간 추이) 이중 창으로 세분화
- **API 호출 흐름 섹션 신규 추가 (1.4)**: 키워드 1개 평가 시 총 4회 호출 (Search Ad API, Blog Search ×2, DataLab). 기존 대비 호출 횟수 동일 유지
- **raw_signals 필드명 전면 변경 (6.1)**: 5개 → 8개. `search_volume`→`monthly_search_volume`, `competition_count`→`blog_total_count`, `recent_density_14d`→`blog_recent_7d_count`(+`blog_recent_30d_count` 신규), `commercial_intent`→`comp_idx`+`shopping_total`+`commercial_pattern_score`(3개 분리), `google_trend_score`→`datalab_slope`
- **score_breakdown 필드명 변경 (6.1)**: 4개 → 5개. `datalab_trend`→`search_volume`(30점), `blog_competition`→`blog_competition_volume`+`blog_competition_density`(구조 변경 없음, 명칭만), `google_trends`→`trend_slope`. `commercial_intent` 유지
- **config 항목 분리 (6.1)**: `keyword.recent_density_window_days`(14일) 단일 항목 → `keyword.recent_density_window_days_short`(7일) + `keyword.recent_density_window_days_long`(30일) 2개로 분리. 총 19개 → **20개**
- **1.7 트레이드오프 항목 추가**: DataLab 폐지·Google Trends 폐지·최근 밀도 기간 재정의 결정 배경 명시
- **미결 태스크 갱신 (7)**: 점수 모델 구현 명세 확정 처리. 씨드 분해·무관 키워드 필터·API 한도 확인·환산 구간 재보정 우선순위 재조정
- **오픈 이슈 추가 (8)**: Google CSE 2027년 서비스 종료 이슈 추가

### v13 (2026-05-06) — keyword_researcher housekeeping 내재화, 키워드 풀 삭제 정책 2단계 확정, 키워드 등급 체계 도입

- **keyword_researcher housekeeping 내재화 (1.4, 6.2)**: 매 실행 시 시작 단계에서 revival_days 초과 키워드 스캔·재평가·아카이브 + pool_max_size 초과 시 삭제 정책 실행. 별도 스케줄러 불필요 (Option A 확정)
- **풀 삭제 정책 2단계 확정 (1.5)**: 1순위 — evaluation_count ≥ 3 AND avg_score < 45, last_evaluated_at 오래된 순. 2순위 fallback — last_evaluated_at 오래된 순 정렬 후 total_score(최근 평가 기준) 낮은 순 순차 삭제 (평균 미적용)
- **키워드 등급 체계 도입 (1.5)**: 부스러기(0~45점) / 강철(46~59점) / 황금(60점+). 부스러기 등급이 풀 삭제 1순위 임계치 기준
- **config 항목 변경 (6.1)**: `keyword.pool_max_size` 200 → **50** (v1 타이트하게 설정), `keyword.pool_eviction_score_threshold`(45), `keyword.pool_eviction_eval_count`(3) 신규 추가. 총 **19개** 항목
- **1.7 트레이드오프 추가**: evaluation_count 비정규화 미채택 이유, housekeeping Option A 채택 이유
- **6.1 keyword_evaluations 테이블 total_score 설명 보완**: 풀 삭제 2순위 정렬 기준(가장 최근 레코드)임을 명시
- **6.1 DB 업데이트 타임라인 "실행 시작 시 housekeeping" 행 추가**
- **6.2 재평가 트리거 갱신**: "사용자가 --recommend 요청 시"에서 "keyword_researcher 매 실행 시 시작 단계"로 확정
- **미결 태스크**: housekeeping 트리거 및 풀 삭제 정책 완료 처리. 키워드 등급 중간 구간 이름 정의 신규 추가. contents 테이블 컬럼 재검토 완료 처리

### v12 (2026-05-06) — keyword_usages failed 처리 정책 확정

- **keyword_usages 파이프라인 중단 정책 신규 (1.4, 1.6, 6.1, 6.2)**: 파이프라인이 어떤 이유로든 중단되면 `keyword_usages.status = failed`로 갱신 → in_progress 잠금 즉시 해제. `published_at = null` 유지 (180일 재사용 카운트 미적용). 시스템은 중단 사유를 세분화하지 않음 — 재선택 여부는 사용자가 결정
- **1.7 트레이드오프 항목 추가**: failed 이유 세분화 없음 결정 배경 명시
- **6.1 keyword_usages 테이블 status 필드 설명 업데이트**: failed 처리 정책 및 잠금 해제 동작 명문화
- **6.1 DB 업데이트 타임라인 "파이프라인 중단" 행 추가**
- **6.2 재사용 가능 여부 설명 보완**: status = failed 레코드는 published_at = null이므로 180일 카운트에 포함되지 않음을 명시

### v11 (2026-05-06) — keywords.embedding 컬럼 추가, 씨드 중복 체크 UX, 어뷰징 비교 방식 확정, collector Phase 1 경고 임계치

- **keywords 테이블 embedding 컬럼 추가**: Vector(768). 씨드 입력 중복 확인 및 keyword_researcher 어뷰징 쿨다운 비교에 사용
- **씨드 입력 중복 확인 UX 신규 (1.4)**: 유사도 ≥ 0.93 시 안내 → 재평가 흐름 연결
- **(a) 어뷰징 쿨다운 비교 방식 확정**: keyword embedding끼리 비교로 명확화
- **collector Phase 1 유사도 경고 임계치 확정**: `collector.similarity_warning_threshold = 0.75`
- **임베딩 인프라 표 전면 개정 (6.3)**: 5개 용도로 확장, 각 임계치 명시
- **config 항목 2개 추가**: `keyword.seed_duplicate_threshold`, `collector.similarity_warning_threshold`

### v10 (2026-05-06) — DB 타임라인 keyword_embedding 잔존 제거

- **DB 업데이트 타임라인 표 수정**: contents_maker 행의 `keyword_embedding` 항목 제거

### v9 (2026-05-04) — keyword_embedding → summary_embedding, 임베딩 인프라 역할 재정의

- **keyword_embedding 컬럼 폐기 → summary_embedding으로 대체**
- **summary_embedding 정의**: embed(title + intro + short_conclusion). collector Phase 1 완료 시점 생성·저장
- **자기잠식 체크 역할 분리 확정**: keyword_researcher = keyword 텍스트 기반 DB 조회 / collector Phase 1 = summary_embedding 비교

### v8 (2026-05-04) — collector 입력 구조 수정, contents 테이블 title 컬럼 추가

- **collector 입력에서 keyword_pool 제거**: golden_keyword 단독 입력
- **assigned_keywords 설명 수정**: LLM이 단락 주제 분석으로 도출한 서브 키워드로 정정
- **contents 테이블 title 컬럼 추가**: collector Phase 1에서 독립 컬럼으로 저장

### v7 (2026-05-04) — 시크릿 관리 구조 확정, config 초기값 목록, 회피 규칙 체크 시점 정리

- 시크릿 관리 3계층 분리 확정, accounts 테이블 신규 추가
- config 테이블 초기값 목록 확정 (15개 항목, dot notation 컨벤션)
- 회피 규칙 체크 시점 정리

### v6 (2026-05-03) — DB 구조 전면 개정, collector 스키마 보완

- DB 저장소 전환: Google Sheets → PostgreSQL(v1~)
- 테이블 분리: keywords + keyword_evaluations + keyword_usages + contents + config
- 버전별 로드맵 확정

### v5 (2026-05-03) — Collector 전면 재설계, 발행 포맷 확정

- 발행 포맷 확정: refined_post = HTML
- Collector Phase 1/2 플로우 재설계, 단락 타입 도입

### v4 (2026-04-30) — 모듈 단위 상세 합의

- 모듈명 표준화, checker 두 단계 게이트, publisher 발행 정책 게이트

### v3 (이전) — 키워드 모듈 + 데이터 스키마 확정

- DataLab+Blog+GT 점수 모델, 키워드 풀 (max 200) + 연금술
