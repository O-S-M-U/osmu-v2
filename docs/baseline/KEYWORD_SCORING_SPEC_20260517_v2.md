# keyword_researcher 점수 모델 구현 명세서
> 버전: v2 | 작성일: 2026-05-17  
> 선행 문서: MODULE_SPEC_20260517_v17.md  
> 변경 이력: v1(2026-05-09) → v2(2026-05-17) — 하드컷 선행 조건 3개 추가, 모듈 간 전달 페이로드 정의

---

## 1. 왜 이 문서가 필요한가

MODULE_SPEC v13까지의 점수 모델은 **"무엇을 측정하는가"(가중치)** 는 정의되어 있었지만,  
**"어떤 API로 어떻게 값을 가져오는가"(구현)** 는 전혀 기재되지 않은 상태였다.

개발팀이 구현에 들어가려면 아래 4가지가 모두 확정되어야 한다.

1. 어떤 API 엔드포인트를 호출하는가
2. 어떤 응답 필드를 사용하는가
3. raw 값을 점수(0~N점)로 어떻게 환산하는가
4. `raw_signals` / `score_breakdown` JSON에 어떤 이름으로 저장하는가

이 문서가 그 4가지를 모두 정의한다.

---

## 2. 기존 모델 요약 (v13 기준)

### 2.1 가중치 테이블

| 항목           | DEFAULT | LONGTAIL | 비고                                  |
| -------------- | ------- | -------- | ------------------------------------- |
| DataLab 트렌드 | 40      | 20       | 롱테일은 절대 트렌드 낮아도 OK        |
| Blog 경쟁도    | 30      | 45       | 총량 15 + 최근 밀도 15 (DEFAULT 기준) |
| 상업적 의도    | 20      | 25       |                                       |
| Google Trends  | 10      | 10       |                                       |
| **합계**       | **100** | **100**  |                                       |

### 2.2 기존 모델의 미결 상태

| 항목                | 측정 의도         | 실제 상태                                                                                     |
| ------------------- | ----------------- | --------------------------------------------------------------------------------------------- |
| DataLab 트렌드 40점 | 수요(검색량) 측정 | DataLab ratio는 **상대값**이라 절대 검색량 불가. 어떤 기간의 ratio를 어떻게 점수화하는지 미정 |
| Blog 경쟁도 30점    | 공급(경쟁) 측정   | Naver Blog Search API 사용 추정되나 미기재                                                    |
| 상업적 의도 20점    | CPC/구매 의도     | 측정 방법 전혀 미정                                                                           |
| Google Trends 10점  | 트렌드 방향성     | pytrends 예상이나 미기재. **pytrends 2025년 4월 archived**                                    |

---

## 3. 변경 사항 및 결정 이유

### 3.1 DataLab 트렌드 40점 → 역할 분리

**기존 의도**: "DataLab 트렌드"라는 이름에서 알 수 있듯 수요(검색량) + 트렌드 방향성을 함께 담으려 했던 것으로 보임.

**문제점**:
- DataLab API 응답값 `ratio`는 조회 기간 내 최대값 = 100으로 정규화한 **상대값**
- 키워드 A의 ratio 80과 키워드 B의 ratio 80은 절대 검색량이 전혀 다를 수 있음
- "얼마나 검색되는가(수요)"를 측정하는 데 DataLab ratio는 부적합

**발견**: Naver Search Ad API(`/keywordstool`)가 실제 월간 절대 검색량을 제공하며, **광고 계정 생성(무료) + API 신청만으로 광고비 없이 사용 가능**함이 실 계정으로 확인됨 (2026-05-09 테스트).

**결정**:
- 40점을 두 역할로 분리
  - **월 검색량 30점**: Search Ad API 절대값 → 진짜 수요 측정
  - **발행 추세 10점**: DataLab slope → Google Trends 대체 (아래 3.2 참조)
- 합계 40점 유지, 가중치 총합 100점 유지

```
변경 전: DataLab 트렌드 (40점) — 상대값, 방향+수준 혼합 측정
변경 후: 월 검색량 (30점, Search Ad API) + 발행 추세 (10점, DataLab slope)
```

### 3.2 Google Trends 10점 → DataLab slope 10점

**기존 도구**: pytrends (비공식 Google Trends 라이브러리)

**문제점**:
- pytrends **2025년 4월 17일 공식 archived** (read-only, 유지보수 중단)
- 공식 Google Trends API는 2025년 7월 론칭했으나 **초대제 알파** (일반 접근 불가)
- 실제 블로그 트래픽 분석 결과 **네이버 검색 99%, 구글 검색 0.1%** → 구글 트렌드 신호가 이 서비스의 수요 예측에 실질적 기여 없음

**결정**: DataLab 시계열 데이터로 slope(기울기)를 계산해 대체
- DataLab은 이미 30점 계산을 위해 호출하는 API → **추가 API 호출 없이** 같은 응답 재활용
- DataLab slope는 구글 트렌드 대비 오히려 **네이버 기반 실트래픽에 더 직접적인 신호**

```
변경 전: Google Trends 10점 (pytrends) — 구글 기반, archived, 트래픽 관련성 낮음
변경 후: DataLab slope 10점 — 네이버 기반, 공식 API, 추가 호출 없음
```

### 3.3 Blog 경쟁도 30점 — 구조 유지, 측정 방법 확정

**결정**: 총량(15점) + 최근 발행 밀도(15점) 구조 **그대로 유지**.  
이번에 측정 방법을 처음으로 구체 명세화한 것이며, 가중치·구조 변경 없음.

- 총량: Naver Blog Search API `total` (sort=sim)
- 최근 밀도: 동일 API에 날짜 파라미터 추가

### 3.4 상업적 의도 20점 — 측정 방법 확정

**결정**: 완전한 CPC 데이터는 광고 집행 없이 불가하므로 3가지 proxy 조합.

---

## 4. 🚨 하드컷 선행 조건 (v2 신규 — 점수 계산 전 적용)

> **설계 원칙**: 점수 모델은 *비교 우위*를 측정하는 도구다. 수요 자체가 없거나, 관심이 식어가는 키워드는 점수 계산에 앞서 제거한다. 이 조건들은 소프트 패널티가 아닌 **하드컷** — 통과 못 하면 점수 계산 없이 즉시 폐기.

### 왜 하드컷이 필요한가

점수 모델 구조상 논리적 허점이 있다.

`blog_total_count`가 낮으면(블로그 글이 없으면) → 경쟁 낮음 → **blog_competition 점수가 높게 나온다.**

결과적으로 "아무도 검색 안 하고 아무도 글을 안 쓴" 키워드가 낮은 경쟁도 덕분에 golden_threshold를 통과하는 역설이 발생할 수 있다. 점수 가중치 조정으로는 이 구조적 허점을 해결할 수 없으므로 선행 하드컷으로 차단한다.

### 하드컷 조건 3개

점수 계산 전에 아래 순서대로 체크. **하나라도 해당하면 즉시 폐기 — 점수 계산 없음.**

```python
# 하드컷 체크 (점수 계산 전 실행)

# ① 검색 수요 없음
if monthly_search_volume < config["keyword.min_search_volume"]:
    → 폐기 ("검색량 부족으로 폐기")

# ② 관심 하락 중
if datalab_slope < 0:
    → 폐기 ("트렌드 하락으로 폐기")

# ③ 레퍼런스 수집 불가 예상
if blog_total_count < config["keyword.min_blog_count"]:
    → 폐기 ("블로그 레퍼런스 부족으로 폐기")
```

**조건별 설명**:

| 조건                         | 근거                                                                                                                           | config 항목                  | v1 초기값 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- | --------- |
| `monthly_search_volume` 미달 | 수요 자체가 없는 키워드. 글을 써도 유입 없음                                                                                   | `keyword.min_search_volume`  | **500**   |
| `datalab_slope < 0`          | 검색 관심이 하락 중. 에버그린(≈0)은 허용, 명확한 하락만 차단                                                                   | 임계치 없음 (음수 전체 차단) | —         |
| `blog_total_count` 미달      | collector Phase 1-A에서 품질 필터 통과 블로그 5개 확보 가능성이 극히 낮음. 양(quantity) 기반 근사값이므로 보수적으로 낮게 설정 | `keyword.min_blog_count`     | **30**    |

> **datalab_slope ≈ 0 (평탄) 처리**: 평탄은 에버그린 키워드 신호로 허용한다. slope < 0인 경우만 하드컷. 평탄 키워드가 collector에서 블로그 5개 미달일 경우 수직 확장 전략을 적용한다 (COLLECTOR_PHASE1A_SPEC 참조).

> **v1 초기값 근거**: min_search_volume=500은 점수 환산 표의 최하위 구간 하한(2점 구간). min_blog_count=30은 collector 품질 필터(1,500자↑, H2 4개↑, 2년 이내) 통과 기대값 기준으로 여유 마진 포함한 보수적 값. 둘 다 v1 운영 후 실데이터 분포 보고 재조정 예정.

---

## 5. 신규 점수 모델 (구현 명세 포함)

### 5.1 확정 가중치 테이블

| 항목                    | DEFAULT | LONGTAIL | 변경 여부                       |
| ----------------------- | ------- | -------- | ------------------------------- |
| 월 검색량 (수요)        | **30**  | **15**   | 🔄 DataLab 40점에서 분리         |
| Blog 경쟁도 — 총량      | 15      | 22.5     | ✅ 유지                          |
| Blog 경쟁도 — 최근 밀도 | 15      | 22.5     | ✅ 유지                          |
| 상업적 의도             | 20      | 25       | ✅ 유지 (측정 방법 신규 확정)    |
| 발행 추세 (slope)       | **10**  | **10**   | 🔄 Google Trends → DataLab slope |
| **합계**                | **100** | **100**  |                                 |

> LONGTAIL에서 Blog 경쟁도 45점 = 총량 22.5 + 최근 밀도 22.5 (동일 비율 분할 유지)

---

### 5.2 항목별 구현 명세

---

#### ① 월 검색량 (수요) — DEFAULT 30점 / LONGTAIL 15점

**측정 의도**: 이 키워드를 실제로 얼마나 많은 사람이 검색하는가 (절대 수요)

**API**: Naver Search Ad API  
**엔드포인트**: `GET https://api.searchad.naver.com/keywordstool`  
**인증**: HMAC-SHA256 서명 (X-Timestamp, X-API-KEY, X-Customer, X-Signature)

**요청 파라미터**:
```
hintKeywords={단어1},{단어2}   ← 공백 포함 구문 불가, 반드시 단어 단위
showDetail=1
```

> ⚠️ **핵심 제약**: `hintKeywords`에 공백 포함 구문 입력 시 `{"code":11001, "message":"hintKeywords 파라미터가 유효하지 않습니다."}` 오류 발생.  
> 사용자 씨드 "홈카페 원두 추천" → 단어 분해 → `hintKeywords=홈카페,원두,추천` 으로 호출

**사용 응답 필드**:
| 필드                 | 타입             | 설명                      |
| -------------------- | ---------------- | ------------------------- |
| `relKeyword`         | String           | 연관 키워드 (씨드 확장용) |
| `monthlyPcQcCnt`     | Int 또는 `"<10"` | 월간 PC 검색량            |
| `monthlyMobileQcCnt` | Int 또는 `"<10"` | 월간 모바일 검색량        |

**raw_signal 계산**:
```python
def parse_cnt(val) -> int:
    if isinstance(val, int): return val
    if val == "<10": return 5   # 소량 처리: 5로 근사
    return 0

monthly_total = parse_cnt(monthlyPcQcCnt) + parse_cnt(monthlyMobileQcCnt)
```

**점수 환산 (절대 정규화, v1 초기값)**:
```
monthly_total >= 50,000  → 30점 (MAX)
monthly_total >= 10,000  → 22점
monthly_total >=  3,000  → 15점
monthly_total >=    500  → 8점
monthly_total <     500  → 2점 (MIN, 검색량 거의 없음)
```

> LONGTAIL은 동일 구간에서 15/11/7/4/1점으로 환산 (가중치 비율 유지)  
> v1 운영 후 실제 키워드 분포 기준으로 구간 재보정 예정

**raw_signals JSON 필드명**: `monthly_search_volume`  
**score_breakdown JSON 필드명**: `search_volume`

---

#### ② Blog 경쟁도 — 총량 (DEFAULT 15점 / LONGTAIL 22.5점)

**측정 의도**: 이 키워드로 이미 발행된 블로그 글이 얼마나 많은가 (누적 공급량)

**API**: Naver Search API (Blog)  
**엔드포인트**: `GET https://openapi.naver.com/v1/search/blog`  
**인증**: Client-ID + Client-Secret 헤더

**요청 파라미터**:
```
query={keyword}
sort=sim          ← 정확도순 (관련성 높은 글 기준 total)
display=1         ← total 값만 필요하므로 1건만 받음
```

**사용 응답 필드**: `total` (검색 결과 총 문서 수)

> ⚠️ `total`은 실제 전체 글 수가 아닌 추정치임. 절대적 수치보다 키워드 간 상대 비교에 활용.

**점수 환산**:
```
total >= 500,000  →  0점 (레드오션, 진입 불가)
total >= 100,000  →  4점
total >=  30,000  →  9점
total >=   5,000  → 13점
total <    5,000  → 15점 (블루오션)
```

> LONGTAIL은 동일 구간에서 0/6/13/19/22.5점으로 환산

**raw_signals JSON 필드명**: `blog_total_count`  
**score_breakdown JSON 필드명**: `blog_competition_volume`

---

#### ③ Blog 경쟁도 — 최근 발행 밀도 (DEFAULT 15점 / LONGTAIL 22.5점)

**측정 의도**: 최근 짧은 기간에 경쟁 글이 폭발적으로 늘고 있는가 (과포화 신호)

**API**: Naver Search API (Blog), 동일 엔드포인트  
**요청 파라미터**: 날짜 필터 추가

```python
# 최근 7일 발행 수
from datetime import datetime, timedelta
today = datetime.today()
week_ago = today - timedelta(days=7)

params_7d = {
    "query": keyword,
    "sort": "date",
    "display": 1,
    "start": week_ago.strftime("%Y%m%d"),
    "end": today.strftime("%Y%m%d"),
}
recent_7d_count = response["total"]

# 최근 30일 발행 수 (동일 패턴, 기간만 변경)
```

**점수 환산 (7일 기준 primary)**:
```
recent_7d >= 1,000  →  0점 (최근 폭발적 과포화)
recent_7d >=   300  →  4점
recent_7d >=    50  →  9점
recent_7d >=    10  → 13점
recent_7d <     10  → 15점 (최근 경쟁 없음)
```

**raw_signals JSON 필드명**: `blog_recent_7d_count`, `blog_recent_30d_count`  
**score_breakdown JSON 필드명**: `blog_competition_density`

---

#### ④ 상업적 의도 (DEFAULT 20점 / LONGTAIL 25점)

**측정 의도**: 이 키워드로 유입된 사람이 구매/전환 행동을 할 가능성이 있는가

**측정 불가 이유**: Naver Search Ad API의 CPC는 광고를 집행해야 조회 가능 (미집행 계정 불가)

**대체 방법 3단계 조합**:

**Step 1. 광고 경쟁 지수 (compIdx)** — Search Ad API 응답에서 무료 취득
```python
comp_score = {"낮음": 0, "중간": 1, "높음": 2}.get(compIdx, 0)
# 높음: 광고주들이 많이 입찰 = 상업적 가치 있음
```

**Step 2. 쇼핑 검색 결과 수** — Naver Search API (Shop)
```
GET https://openapi.naver.com/v1/search/shop?query={keyword}&display=1
응답 total → 쇼핑 상품이 많을수록 상업적 의도 높음
```

**Step 3. 키워드 패턴 룰** — API 호출 없음, 구현 비용 0
```python
HIGH_INTENT = ["추천", "비교", "후기", "리뷰", "가격", "구매", "어디서", 
               "순위", "최고", "할인", "브랜드", "구입"]
LOW_INTENT  = ["방법", "이유", "뜻", "정의", "역사", "차이"]
```

**점수 환산 (3단계 합산)**:
```
compIdx 높음 + 쇼핑 total >= 10,000 + 패턴 2개 이상 → 20점
compIdx 중간 + 쇼핑 total >= 1,000  + 패턴 1개 이상 → 14점
compIdx 낮음 + 쇼핑 total < 1,000   + 패턴 없음    →  6점
(중간 조합은 선형 보간)
```

**raw_signals JSON 필드명**: `comp_idx`, `shopping_total`, `commercial_pattern_score`  
**score_breakdown JSON 필드명**: `commercial_intent`

---

#### ⑤ 발행 추세 / slope (DEFAULT 10점 / LONGTAIL 10점)

**측정 의도**: 이 키워드의 검색 관심도가 최근 상승 중인가, 하락 중인가

**API**: Naver DataLab API  
**엔드포인트**: `POST https://naveropenapi.apigw.ntruss.com/datalab/v1/search`  
**인증**: x-ncp-apigw-api-key-id + x-ncp-apigw-api-key

**요청 파라미터**:
```json
{
  "startDate": "{8주 전}",
  "endDate":   "{오늘}",
  "timeUnit":  "week",
  "keywordGroups": [
    { "groupName": "{keyword}", "keywords": ["{keyword}"] }
  ]
}
```

**slope 계산**:
```python
import numpy as np

def calc_slope(data: list[dict]) -> float:
    """DataLab 응답 data 배열에서 선형 회귀 기울기 계산"""
    ratios = [d["ratio"] for d in data]
    x = np.arange(len(ratios))
    slope, _ = np.polyfit(x, ratios, 1)
    return slope   # 양수: 상승, 음수: 하락, ≈0: 평탄(에버그린)
```

**점수 환산**:
```
slope >= +5.0  → 10점 (급상승)
slope >= +1.0  →  8점 (완만 상승)
slope >= -1.0  →  5점 (보합/평탄 — 에버그린)
slope >= -3.0  →  2점 (완만 하락) ← 하드컷에서 이미 제거되어 실제 도달 안 함
slope <  -3.0  →  0점 (급하락)    ← 하드컷에서 이미 제거되어 실제 도달 안 함
```

> **하드컷과의 관계**: slope < 0인 키워드는 하드컷 조건 ②에서 이미 폐기된다. 점수 환산 표의 2점·0점 구간은 하드컷 미도입 시 또는 향후 정책 변경을 대비한 참고값.

**raw_signals JSON 필드명**: `datalab_slope`  
**score_breakdown JSON 필드명**: `trend_slope`

---

## 6. collector로의 전달 페이로드 (v2 신규)

keyword_researcher가 황금 키워드를 선정하면 collector에 아래 페이로드를 전달한다.  
collector의 fallback 분기 판단에 `raw_signals` 일부가 필요하므로 v2에서 명시.

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

> **전달 필드 선택 이유**:
> - `monthly_search_volume`: collector가 블로그 수 부족 시 "수요 없음(폐기)"과 "수요 있음(fallback 전략 적용)"을 구분하는 데 사용
> - `datalab_slope`: collector fallback에서 수평 분해 vs 수직 확장 전략을 선택하는 기준
> - 전체 raw_signals를 전달하지 않는 이유: 최소 인터페이스 원칙. 필요한 필드만 노출.

---

## 7. raw_signals / score_breakdown 필드명 전체 매핑

### raw_signals (원시 데이터)

| 필드명                     | 타입   | 설명                               | 변경 이력                         |
| -------------------------- | ------ | ---------------------------------- | --------------------------------- |
| `monthly_search_volume`    | Int    | PC + Mobile 합산 월간 검색량       | 🆕 신규 (`search_volume` 대체)     |
| `blog_total_count`         | Int    | 블로그 검색 총 결과 수             | 🆕 신규 (`competition_count` 대체) |
| `blog_recent_7d_count`     | Int    | 최근 7일 발행 수                   | 🔄 (`recent_density_14d` → 7d)     |
| `blog_recent_30d_count`    | Int    | 최근 30일 발행 수                  | 🆕 신규                            |
| `comp_idx`                 | String | 광고 경쟁 지수 (낮음/중간/높음)    | 🆕 신규                            |
| `shopping_total`           | Int    | 쇼핑 검색 총 결과 수               | 🆕 신규                            |
| `commercial_pattern_score` | Int    | 구매 의도 패턴 룰 점수 (0~3)       | 🆕 신규                            |
| `datalab_slope`            | Float  | DataLab 8주 ratio 선형 회귀 기울기 | 🔄 (`google_trend_score` 대체)     |

### score_breakdown (점수 항목별 환산값)

| 필드명                     | 타입 | 점수 범위 (DEFAULT) | 변경 이력                               |
| -------------------------- | ---- | ------------------- | --------------------------------------- |
| `search_volume`            | Int  | 0~30                | 🔄 (`datalab_trend` 대체, 30점으로 조정) |
| `blog_competition_volume`  | Int  | 0~15                | 🔄 (`blog_competition` 분리)             |
| `blog_competition_density` | Int  | 0~15                | 🔄 (`blog_competition` 분리)             |
| `commercial_intent`        | Int  | 0~20                | ✅ 유지 (측정 방법 신규 확정)            |
| `trend_slope`              | Int  | 0~10                | 🔄 (`google_trends` 대체)                |

---

## 8. API 호출 흐름 요약

키워드 1개 평가 시 총 **4회 API 호출** (하드컷 통과 후 실행)

```
[하드컷 체크] monthly_search_volume / datalab_slope / blog_total_count
  → 통과한 경우에만 아래 4회 호출 실행

① Search Ad API  /keywordstool  → monthly_search_volume + comp_idx + relKeyword 목록
② Blog Search    /blog          → blog_total_count (sort=sim)
③ Blog Search    /blog          → blog_recent_7d_count (날짜 필터)
④ DataLab        /datalab/v1/search → datalab_slope 계산용 8주 시계열

(⑤ Shopping Search /shop → commercial_intent 보조, 선택적)
```

> **⚠️ 실행 순서 최적화**: 하드컷 판단에 필요한 ①②④를 먼저 호출하고 하드컷 통과 확인 후 나머지 점수 계산을 진행하면 불필요한 API 호출을 줄일 수 있다. (구체적 순서는 구현 시 결정)

---

## 9. 오픈 이슈 (다음 세션 결정 필요)

| #   | 항목                                | 내용                                                                                                                                                                   |
| --- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 점수 환산 구간                      | 본 문서의 환산 구간은 가설 기반. v1 운영 후 실제 키워드 분포 확인하고 사분위수 기반으로 재보정 필요                                                                    |
| 2   | `recent_density_window_days` config | 기존 14일 → 7일/30일 이중 창으로 변경 시 config 항목 재정의 필요                                                                                                       |
| 3   | 씨드 분해 로직                      | "홈카페 원두 추천" → ["홈카페", "원두", "추천"] 분해 규칙. 수직 확장·수평 분해 모두 LLM 위임으로 v1 방향 결정됨. 씨드 → hintKeywords 변환은 별도 (공백 split으로 충분) |
| 4   | 무관 키워드 필터링                  | relKeyword에서 "쌀20KG", "요구르트" 등 씨드와 무관한 키워드 필터 기준 (임베딩 유사도 threshold)                                                                        |
| 5   | Search Ad API 호출 한도             | 일일 호출 한도가 Naver Open API의 25,000회/일과 별도 관리되는지 콘솔에서 확인 필요                                                                                     |
| 6   | 하드컷 초기값 재보정                | `keyword.min_search_volume`(500), `keyword.min_blog_count`(30) 모두 v1 운영 후 실데이터 기준 재조정 예정                                                               |
