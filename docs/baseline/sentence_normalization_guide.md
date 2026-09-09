# 문장 정규화 & 팩트 기반 단락 생성 가이드

> **용도**: 뉴스/기사 URL에서 팩트를 추출해 표절 없이 단락을 재구성하는 파이프라인 정리  
> **작성**: Claude와의 대화 기반 정리 문서

---

## 1. 문장 정규화 (Sentence Normalization) 개념

문장 정규화란 텍스트를 일관된 형식으로 변환하는 과정이다.  
표절 방지 목적에서는 **원문의 사실 정보(팩트)만 추출**하고, 문체·구조·표현은 완전히 새로 구성한다.

### 핵심 원칙: 팩트 레이어 vs 표현 레이어

| 구분 | 내용 |
|------|------|
| **추출할 것 (팩트 레이어)** | 수치, 날짜, 고유명사, 인과관계, 시간 순서·배경 정보 |
| **버릴 것 (표현 레이어)** | 원문 문장 구조, 기자의 서술 방식, 특정 단어 선택, 감정적 수식어 |

### 표절 방지 기준

| 구분 | 설명 |
|------|------|
| ✅ 허용 | 공개된 사실·수치·통계를 자신의 문장으로 재서술 |
| ✅ 허용 | 여러 출처의 팩트를 종합해 새로운 문맥 구성 |
| ⚠️ 주의 | 인용문은 반드시 출처 명시 후 따옴표 처리 |
| ❌ 위반 | 원문 문장 구조를 단어만 바꿔 유사 표현으로 쓰는 것 |
| ❌ 위반 | 팩트 변형 없이 문체만 살짝 바꾸는 것 |

---

## 2. 정규화 프로세스

```
원문 입력
   ↓
1. 문장 분절 — 문장을 단위별로 쪼갬
   ↓
2. 개체명 인식 (NER) — 인물/장소/날짜/수치 태깅
   ↓
3. 관계 추출 — "누가 / 언제 / 어디서 / 무엇을 / 왜" 구조화
   ↓
4. 팩트 트리플 생성 — (주체 - 행위 - 객체) 형태로 추상화
   ↓
5. 재구성 — 팩트 트리플을 기반으로 새 문장 생성
```

### 예시

**원문**
> "삼성전자는 3일 2분기 영업이익이 전년 동기 대비 15% 급증한 12조 원을 기록했다고 밝혔다."

**팩트 트리플 추출**
```
주체: 삼성전자
지표: 2분기 영업이익
수치: 12조 원
변화율: +15% (전년 동기 대비)
발표일: 3일
```

**재구성된 문장**
> "삼성전자의 올해 2분기 영업이익은 12조 원으로, 지난해 같은 기간과 비교해 15% 증가한 수준이다."

---

## 3. 구현 파이프라인 아키텍처

### 입력 / 출력 구조

```
[입력]
 - URL 목록 (뉴스/기사 링크)
 - 주제 (Topic)
 - 핵심 키워드 (Primary Keywords)
 - 보조 키워드 (Secondary Keywords)

        ↓

[Stage 1] 콘텐츠 수집
 - URL 크롤링 → 본문 추출 (Boilerplate 제거)

        ↓

[Stage 2] 팩트 정규화
 - 문장 분절 → NER → 팩트 트리플 추출
 - 키워드 관련성 스코어링
 - 중복 팩트 제거 및 병합

        ↓

[Stage 3] 단락 생성
 - 팩트 배열 (논리 순서 정렬)
 - 키워드 기반 문장 재구성
 - 단락 일관성 검증
```

---

## 4. 코드 구현

### Stage 1: 콘텐츠 수집

```python
import requests
from newspaper import Article

def extract_article(url: str) -> dict:
    article = Article(url, language='ko')
    article.download()
    article.parse()
    
    return {
        "url": url,
        "title": article.title,
        "text": article.text,
        "publish_date": article.publish_date,
        "authors": article.authors
    }

def collect_sources(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        try:
            results.append(extract_article(url))
        except Exception as e:
            print(f"Failed: {url} - {e}")
    return results
```

> `newspaper3k` 라이브러리가 광고·메뉴 등 Boilerplate를 자동 제거해줌

---

### Stage 2: 팩트 정규화 (Claude API 활용)

```python
import anthropic
import json

def extract_facts(article_text: str, topic: str, keywords: list[str]) -> list[dict]:
    client = anthropic.Anthropic()
    
    prompt = f"""
    다음 기사에서 팩트만 추출해주세요.
    
    주제: {topic}
    핵심 키워드: {', '.join(keywords)}
    
    규칙:
    1. 수치, 날짜, 고유명사가 포함된 팩트만 추출
    2. 기자의 의견/해석 제외
    3. 각 팩트를 (주체, 행위, 객체, 수치/날짜) 형태로 구조화
    4. JSON 배열로 반환
    
    기사:
    {article_text}
    
    출력 형식:
    [
      {{
        "subject": "주체",
        "action": "행위",  
        "object": "객체",
        "value": "수치 또는 날짜 (없으면 null)",
        "relevance_score": 0.0~1.0
      }}
    ]
    """
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(response.content[0].text)


def deduplicate_facts(all_facts: list[dict]) -> list[dict]:
    """여러 기사에서 나온 중복 팩트 제거"""
    seen = set()
    unique = []
    for fact in all_facts:
        key = (fact['subject'], fact['action'], fact.get('value'))
        if key not in seen:
            seen.add(key)
            unique.append(fact)
    return unique
```

---

### Stage 3: 단락 생성

```python
def generate_paragraph(
    facts: list[dict],
    topic: str,
    primary_keywords: list[str],
    secondary_keywords: list[str],
    target_length: int = 300
) -> str:
    
    client = anthropic.Anthropic()
    sorted_facts = sorted(facts, key=lambda x: x['relevance_score'], reverse=True)
    top_facts = sorted_facts[:10]
    
    prompt = f"""
    아래 팩트들을 바탕으로 하나의 단락을 작성해주세요.
    
    ## 조건
    - 주제: {topic}
    - 핵심 키워드 (반드시 포함): {', '.join(primary_keywords)}
    - 보조 키워드 (자연스럽게 포함): {', '.join(secondary_keywords)}
    - 목표 길이: {target_length}자 내외
    - 팩트 외의 내용은 추가하지 말 것
    - 원문 문장 구조를 그대로 쓰지 말 것
    - 자연스러운 한국어 흐름 유지
    
    ## 사용할 팩트
    {json.dumps(top_facts, ensure_ascii=False, indent=2)}
    
    ## 출력
    단락 텍스트만 반환 (설명 없이)
    """
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text
```

---

### 전체 실행 파이프라인

```python
def run_pipeline(
    urls: list[str],
    topic: str,
    primary_keywords: list[str],
    secondary_keywords: list[str]
) -> str:
    
    print("📥 기사 수집 중...")
    articles = collect_sources(urls)
    
    print("🔍 팩트 정규화 중...")
    all_facts = []
    for article in articles:
        facts = extract_facts(
            article['text'], 
            topic, 
            primary_keywords + secondary_keywords
        )
        all_facts.extend(facts)
    
    unique_facts = deduplicate_facts(all_facts)
    print(f"✅ 유효 팩트 {len(unique_facts)}개 추출")
    
    print("✍️ 단락 생성 중...")
    paragraph = generate_paragraph(
        unique_facts,
        topic,
        primary_keywords,
        secondary_keywords
    )
    
    return paragraph


# 사용 예시
result = run_pipeline(
    urls=[
        "https://news.example.com/article1",
        "https://news.example.com/article2",
        "https://news.example.com/article3"
    ],
    topic="국내 반도체 산업 현황",
    primary_keywords=["삼성전자", "영업이익", "반도체"],
    secondary_keywords=["HBM", "AI 수요", "파운드리"]
)

print(result)
```

---

## 5. 추가 고려사항

| 항목 | 방법 |
|------|------|
| **크롤링 차단 우회** | `Playwright` 또는 `Selenium` 사용 (JS 렌더링 필요한 사이트) |
| **출처 추적** | 각 팩트에 `source_url` 필드 유지 → 레퍼런스 자동 생성 가능 |
| **품질 검증** | 생성된 단락을 Claude에게 "팩트 오류 여부" 재검토 요청 |
| **언어 다양성** | 같은 팩트로 여러 표현 후보 생성 후 선택하는 방식 추가 가능 |
| **다중 출처 교차검증** | 3개 이상 출처에서 동일 팩트 확인 후 정규화 레이어로 사용 |

---

## 6. Cowork에서 활용하는 방법

1. 이 파일(`sentence_normalization_guide.md`)을 Cowork 작업 폴더에 저장
2. 위 Python 코드를 `.py` 파일로 같은 폴더에 저장
3. Cowork에서 폴더를 열면 Claude가 이 가이드를 자동으로 컨텍스트로 읽음
4. "이 파이프라인으로 다음 URL들에서 단락 생성해줘" 라고 요청하면 바로 실행 가능

---

*이 문서는 Claude.ai 대화에서 정리되었습니다.*
