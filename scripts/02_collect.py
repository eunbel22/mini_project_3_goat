# 필요한 라이브러리를 불러온다
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import pandas as pd
import requests

# 페이지 주소 꼴을 정한다
URL_TEMPLATE = "https://prod.danawa.com/list/?cate=112758&page={page}"

# 최대 몇 페이지까지 볼지, 합계 몇 행 이상이면 멈출지 정한다
MAX_PAGES = 3
MIN_TOTAL_ROWS = 50

# 일반 브라우저처럼 보이는 요청 헤더를 만든다
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# 스크립트 파일 위치 기준으로 저장 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
SAVE_PATH = BASE_DIR / ".." / "data" / "raw.csv"

# 01_collect_p1.py 와 똑같은 방식으로, 이스케이프된 큰따옴표(백슬래시+따옴표)를 나타내는 상수
ESC = re.escape('\\"')

# 01_collect_p1.py 와 똑같이, 상품 하나의 시작 지점을 알아내는 표시
START_PATTERN = re.compile(ESC + "id" + ESC + r":(\d+)," + ESC + "makerCode")


def unescape(s):
    # 01_collect_p1.py 와 똑같이, JSON 문자열 이스케이프를 원래 글자로 되돌린다
    s = s.replace("\\/", "/")
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    s = s.replace('\\"', '"')
    s = s.replace("\\\\", "\\")
    return s


def find_str(window, key):
    # 01_collect_p1.py 와 똑같이, "key":"값" 형태의 문자열 값을 찾는다
    m = re.search(ESC + re.escape(key) + ESC + ":" + ESC + "(.*?)" + ESC, window)
    return unescape(m.group(1)) if m else ""


def find_num(window, key):
    # 01_collect_p1.py 와 똑같이, "key":숫자 형태의 값을 찾는다
    m = re.search(ESC + re.escape(key) + ESC + r":(\d+)", window)
    return m.group(1) if m else ""


def get_description_texts(window):
    # 01_collect_p1.py 와 똑같이, descriptionSegments 안 "text" 값들을 순서대로 뽑는다
    m = re.search(
        ESC + "descriptionSegments" + ESC + r":\[(.*?)" + ESC + "mobileDescriptionSegments",
        window, re.DOTALL,
    )
    if not m:
        return []
    seg = m.group(1)
    return [unescape(t) for t in re.findall(ESC + "text" + ESC + ":" + ESC + "(.*?)" + ESC, seg)]


def get_bracket_value(texts, label, until_next_bracket):
    # 01_collect_p1.py 와 똑같이, "[라벨]" 텍스트가 정확히 나오는 위치를 찾는다
    start_idx = None
    for i, t in enumerate(texts):
        if t == label:
            start_idx = i
            break
    if start_idx is None:
        return ""

    values = []
    if until_next_bracket:
        for t in texts[start_idx + 1:]:
            if t.startswith("[") and t.endswith("]"):
                break
            values.append(t)
    else:
        if start_idx + 1 < len(texts):
            values.append(texts[start_idx + 1])
    return " / ".join(v for v in values if v)


def format_price(price_min):
    # 01_collect_p1.py 와 똑같이, 숫자를 "1,329,990원" 형태로 만든다
    if not price_min:
        return ""
    return f"{int(price_min):,}원"


def format_mall_count(shop_count):
    # 01_collect_p1.py 와 똑같이, 숫자를 "32몰" 형태로 만든다
    if not shop_count:
        return ""
    return f"{shop_count}몰"


def parse_page(html, page_url):
    # 한 페이지의 HTML에서 순위 목록 상품 행을 뽑는다 (01_collect_p1.py와 같은 방식)
    scraped_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    starts = [(m.start(), m.group(1)) for m in START_PATTERN.finditer(html)]

    rows = []
    for i, (pos, pid) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(html)
        window = html[pos:end]

        hit_rank = find_num(window, "hitRank")

        # hitRank가 없거나 0이면 순위 목록 상품이 아니므로(광고/추천) 뺀다
        if not hit_rank or hit_rank == "0":
            continue

        name = find_str(window, "productName")
        price_min = find_num(window, "min")
        bundle = find_str(window, "bundleProductName")
        shop_count = find_num(window, "shopCount")
        url = find_str(window, "productUrl")
        texts = get_description_texts(window)

        cpu_raw = get_bracket_value(texts, "[CPU]", until_next_bracket=True)
        ram_raw = get_bracket_value(texts, "[구성]", until_next_bracket=False)
        screen_size_raw = texts[1] if len(texts) > 1 else ""
        weight_raw = texts[2] if len(texts) > 2 else ""

        # 그 페이지 주소 기준으로 전체 주소를 만든다
        detail_url = urljoin(page_url, url)

        rows.append({
            "hit_rank": int(hit_rank),
            "name": name,
            "cpu_raw": cpu_raw,
            "ram_raw": ram_raw,
            "storage_raw": bundle,
            "screen_size_raw": screen_size_raw,
            "weight_raw": weight_raw,
            "price_raw": format_price(price_min),
            "mall_count_raw": format_mall_count(shop_count),
            "detail_url": detail_url,
            "scraped_at": scraped_at,
        })

    rows.sort(key=lambda r: r["hit_rank"])
    return rows


def collect():
    all_rows = []
    stopped_page = None

    for page in range(1, MAX_PAGES + 1):
        # 이 페이지 주소를 만든다
        page_url = URL_TEMPLATE.format(page=page)

        # 실제로 연 주소를 출력한다
        print("실제로 연 주소:", page_url)

        # 페이지를 요청한다
        res = requests.get(page_url, headers=HEADERS, timeout=10)

        # 응답 상태를 출력한다
        print("응답 상태:", res.status_code)

        if res.status_code != 200:
            stopped_page = page
            print(f"{page}페이지에서 멈춤 (응답 상태가 200이 아님)")
            break

        # 응답 인코딩을 페이지에 맞춘다 (모르면 utf-8)
        res.encoding = res.apparent_encoding or "utf-8"

        # 이 페이지의 행을 뽑는다
        page_rows = parse_page(res.text, page_url)

        # 그 페이지 행 수를 출력한다
        print("그 페이지 행 수:", len(page_rows))

        if len(page_rows) == 0:
            stopped_page = page
            print(f"{page}페이지에서 멈춤 (그 페이지 행 수 0)")
            break

        all_rows.extend(page_rows)

        # 합계 50행 이상이면 여기서 멈춘다
        if len(all_rows) >= MIN_TOTAL_ROWS:
            stopped_page = page
            print(f"{page}페이지에서 멈춤 (합계 {len(all_rows)}행으로 50행 이상)")
            break

        # 마지막 페이지가 아니면 다음 페이지 전에 1초 쉰다
        if page < MAX_PAGES:
            time.sleep(1)

    df = pd.DataFrame(all_rows, columns=[
        "name", "cpu_raw", "ram_raw", "storage_raw", "screen_size_raw",
        "weight_raw", "price_raw", "mall_count_raw", "detail_url", "scraped_at",
    ])

    # 합계 행 수를 출력한다
    print("합계 행 수:", len(df))

    # 서로 다른 detail_url 개수를 출력한다
    print("서로 다른 detail_url 개수:", df["detail_url"].nunique())

    if len(df) == 0:
        print("0행이므로 저장하지 않는다.")
        return

    # 표본 3행을 출력한다: 첫 행, 가운데 행, 마지막 행
    first_idx = 0
    middle_idx = len(df) // 2
    last_idx = len(df) - 1
    print("--- 표본 3행 ---")
    for idx in [first_idx, middle_idx, last_idx]:
        print(f"행 번호 {idx}:")
        print(df.iloc[idx])
        print()

    # 합친 표를 CSV로 저장한다
    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    collect()
