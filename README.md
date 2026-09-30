# 노트북 비교 도우미

## 1. 무엇을 하나
노트북 예산을 정해 두고 고르는, 컴퓨터 용어에 익숙하지 않은 사용자를 위한 화면이다.
예산(원)과 최소 램(GB)을 넣으면 조건에 맞는 카드만 가격 낮은 순으로 걸러서 보여준다.

## 2. 배포 주소
https://miniproject3-sage.vercel.app

## 3. 데이터
- 출처: 다나와 노트북 전체(cate=112758) 인기순 1페이지
- 수집 시점: 2026-09-28 15:53 (notes.md 수집 기록서 기준)
- 행 수: 원본 60행(2페이지가 1페이지를 그대로 반복해서 고유 상품은 30개) → 정제 30행 → data/data.json 30개
- 정제한 열: price_raw에서 쉼표와 "원"을 뗀 정수 `price`, ram_raw에서 "GB"를 뗀 정수 `ram_gb`, 앞뒤 공백을 정리한 `name`
- 화면(index.html)에서 실제로 쓰는 값: `data/data.json`의 `name` · `price` · `ram_gb` · `detail_url` 네 개뿐

## 4. AI 추천
"이 조건으로 추천받기" 단추를 누르면 Vercel 서버리스 함수(`api/recommend.js`)가 Gemini(`gemini-3.5-flash-lite`)를 호출한다.

**AI에게 넘기는 것**
- 예산, 최소 램 조건
- 조건에 맞는 후보 중 가격 낮은 순 최대 5개, 각 후보의 이름·가격·램(GB)만

**AI에게 받는 것**
- JSON `{"pick": 후보 이름, "reasons": [이유 2개]}`

**지키게 한 규칙** (api/recommend.js에 실제로 적힌 그대로)
- pick 값은 후보 이름을 큰따옴표 안 글자 그대로, 띄어쓰기와 글자 하나까지 완전히 똑같이 복사
- 이유는 정확히 2개 문장, 각 문장은 한글 기준 40자를 넘지 않음, 문장마다 후보 표의 price 또는 ram_gb 숫자를 하나 이상 그대로 포함
- 숫자는 후보 표에 적힌 값을 그대로 옮기고, 새로 계산하거나 줄이거나 반올림하지 않음(예: "877000"을 "약 88만 원"으로 쓰지 않음)
- 후보 목록에 없는 노트북이나 표에 없는 정보(성능·용도·가성비·경제성·인기·품질·배터리·무게·할인 등)는 말하지 않음
- temperature 0, 10초 안에 응답이 없으면 타임아웃 처리

화면 안내 문장(index.html 실제 글자)
- 후보 0개: "조건에 맞는 항목이 없습니다." + 예산·램을 조정했을 때의 안내 문장
- 기다리는 동안 단추: "고르는 중…"
- 규칙을 어긴 답: "추천을 확인하지 못했습니다"
- AI가 답을 못 줄 때: "잠시 뒤 다시 눌러 주세요"

열쇠는 코드에 직접 넣지 않고 Vercel 환경변수 `GEMINI_API_KEY`에 넣어서 쓴다.

## 5. 확인한 것
- M10 조건별 검산표: 정상(예산 1,000,000·램 8GB) 6개, 후보 1개(예산 800,000·램 8GB) 1개, 후보 없음(예산 800,000·램 16GB) 0개 — 세 경우 모두 계산값이 화면 표시와 일치
- M14 세 경우 검증표: 위 세 조건으로 실제 배포 주소에 "이 조건으로 추천받기"를 눌러본 결과, AI가 고른 이름과 이유 속 숫자가 data.json의 값과 모두 일치했고, 표 밖 정보나 지어낸 말은 없었음

## 6. 한계
- 다나와 인기순 1페이지 고유 30개만 모음(`?page=` 파라미터가 실제로 페이지를 넘기지 않음)
- 2026-09-28 수집 시점 가격이라 지금과 다를 수 있음
- 같은 조건에서도 추천이 가끔 달라짐(5번 중 1번)
- 예산 칸에 글자를 넣으면 조건 없음으로 조용히 처리됨
- Gemini 과부하(503)나 요청 한도 때 추천 실패

## 실행 안내

### 1. 다시 모으기
윈도우는 `python`, 맥은 `python3`로 실행한다. scripts 폴더 파일을 번호 순서대로.

| 파일 | 무엇을 만드는지 | 실행 명령 | 확인 |
|---|---|---|---|
| `00_env_check.py` | 파이썬·pandas 환경이 되는지 가상 표로 확인 | `python scripts/00_env_check.py` | 확인 안 함 |
| `01_collect_p1.py` | 다나와 목록 1페이지를 읽어(`data/page_p1.html`) `data/raw_p1.csv` 생성 — 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python scripts/01_collect_p1.py` | 확인 안 함 |
| `02_collect.py` | 다나와 목록을 여러 번 읽어 `data/raw.csv` 생성 — 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python scripts/02_collect.py` | 확인 안 함 |
| `03_check_page_boundaries.py` | `data/raw.csv`를 읽어 페이지 경계를 확인(요청은 안 보냄) | `python scripts/03_check_page_boundaries.py` | 확인 안 함 |
| `03_clean.py` | `data/raw.csv`를 정제해 `data/clean.csv` 생성 | `python scripts/03_clean.py` | **확인함** — 오류 없이 종료, `data/clean.csv` 30행 생성 |
| `04_stats.py` | `data/clean.csv`의 price 기초 통계 출력 | `python scripts/04_stats.py` | 확인 안 함 |
| `05_hist.py` | 가격 구간별 히스토그램 `charts/hist.png` 생성 | `python scripts/05_hist.py` | 확인 안 함 |
| `06_by_category.py` | 램별 평균 가격 막대 그래프 `charts/by_category.png` 생성 | `python scripts/06_by_category.py` | 확인 안 함 |
| `06_hist_half.py` | 구간 폭을 절반으로 줄인 히스토그램 `charts/hist_half.png` 생성 | `python scripts/06_hist_half.py` | 확인 안 함 |
| `07_by_category_median.py` | 램별 중앙값 막대 그래프 `charts/by_category_median.png` 생성 | `python scripts/07_by_category_median.py` | 확인 안 함 |
| `07_export_json.py` | `data/clean.csv`를 `data/data.json`으로 내보냄 | `python scripts/07_export_json.py` | 확인 안 함 |

- `scripts/01_collect_p1.py`는 `data/page_p1.html`을 읽는데, 이 파일은 저장소에 없다.
- 다나와 가격·순위는 수시로 바뀌어, 수집을 다시 하면 2026-09-28과 같은 값이 나오지 않는다.
- 보고서와 같은 숫자를 보려면 저장소의 `data/raw.csv`로 `scripts/03_clean.py`부터 실행한다.

### 2. 화면에 반영하기
새 `data/data.json`·`charts/`를 커밋·푸시하면 Vercel이 다시 배포한다.

### 3. AI 연결
Vercel 환경변수 이름 `GEMINI_API_KEY`에 열쇠를 넣고 Redeploy한다. (열쇠 값은 여기에 쓰지 않음)
