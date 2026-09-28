# 필요한 라이브러리를 불러온다
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

# 화면에서 직접 센 항목 수(광고 제외, 순위 번호 상품만)
EXPECTED_COUNT = 30

# 스크립트 파일 위치 기준으로 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
PAGE_PATH = BASE_DIR / ".." / "data" / "page_p1.html"
SAVE_PATH = BASE_DIR / ".." / "data" / "raw_p1.csv"

# page_p1.html 안에서 이스케이프된 큰따옴표(백슬래시+따옴표)를 나타내는 상수
ESC = re.escape('\\"')

# 상품 하나의 시작 지점을 알아내는 표시(“id”: 숫자, 바로 뒤에 “makerCode”가 오는 자리)
START_PATTERN = re.compile(ESC + "id" + ESC + r":(\d+)," + ESC + "makerCode")

# 화면에 실제로 그려지는 순위 제목(ProductListTitle) 글자를 pcode와 함께 찾는 표시
VISIBLE_TITLE_PATTERN = re.compile(
    r'인기순위 (\d+)위"[^>]*>\d+</span><a href="https://prod\.danawa\.com/info/\?pcode=(\d+)'
    r'[^"]*"[^>]*class="([^"]*)"[^>]*>(.*?)</a>'
)


def unescape(s):
    # JSON 문자열 이스케이프(\/, \uXXXX, \", \\)를 원래 글자로 되돌린다
    s = s.replace("\\/", "/")
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    s = s.replace('\\"', '"')
    s = s.replace("\\\\", "\\")
    return s


def find_str(window, key):
    # window 안에서 "key":"값" 형태의 문자열 값을 찾는다
    m = re.search(ESC + re.escape(key) + ESC + ":" + ESC + "(.*?)" + ESC, window)
    return unescape(m.group(1)) if m else ""


def find_num(window, key):
    # window 안에서 "key":숫자 형태의 값을 찾는다
    m = re.search(ESC + re.escape(key) + ESC + r":(\d+)", window)
    return m.group(1) if m else ""


def get_description_texts(window):
    # descriptionSegments 배열 안 "text" 값들을 순서대로 뽑는다
    m = re.search(
        ESC + "descriptionSegments" + ESC + r":\[(.*?)" + ESC + "mobileDescriptionSegments",
        window, re.DOTALL,
    )
    if not m:
        return []
    seg = m.group(1)
    return [unescape(t) for t in re.findall(ESC + "text" + ESC + ":" + ESC + "(.*?)" + ESC, seg)]


def get_bracket_value(texts, label, until_next_bracket):
    # "[라벨]" 텍스트가 정확히 나오는 위치를 찾는다
    start_idx = None
    for i, t in enumerate(texts):
        if t == label:
            start_idx = i
            break
    if start_idx is None:
        return ""

    values = []
    if until_next_bracket:
        # 다음 "[...]" 라벨이 나오기 전까지 뒤이은 값들을 이어붙인다
        for t in texts[start_idx + 1:]:
            if t.startswith("[") and t.endswith("]"):
                break
            values.append(t)
    else:
        # 라벨 바로 뒤의 값 하나만 가져온다
        if start_idx + 1 < len(texts):
            values.append(texts[start_idx + 1])
    return " / ".join(v for v in values if v)


def format_price(price_min):
    # 숫자를 "1,329,990원" 형태로 만든다
    if not price_min:
        return ""
    return f"{int(price_min):,}원"


def format_mall_count(shop_count):
    # 숫자를 "32몰" 형태로 만든다
    if not shop_count:
        return ""
    return f"{shop_count}몰"


def collect():
    # page_p1.html이 없으면 여기서는 새로 요청하지 않고 멈춘다
    if not PAGE_PATH.exists():
        print("page_p1.html이 없어서 진행할 수 없음 (다나와에 새로 요청하지 않음)")
        return

    html = PAGE_PATH.read_text(encoding="utf-8")

    # page_p1.html 파일의 수정 시각을 한국 시간으로 변환한다
    mtime = PAGE_PATH.stat().st_mtime
    scraped_at = datetime.fromtimestamp(mtime, tz=ZoneInfo("Asia/Seoul")).isoformat()

    # 상품 블록의 시작 지점들을 모두 찾는다
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

        rows.append({
            "hit_rank": int(hit_rank),
            "pcode": pid,
            "name": name,
            "cpu_raw": cpu_raw,
            "ram_raw": ram_raw,
            "storage_raw": bundle,
            "screen_size_raw": screen_size_raw,
            "weight_raw": weight_raw,
            "price_raw": format_price(price_min),
            "mall_count_raw": format_mall_count(shop_count),
            "detail_url": url,
            "scraped_at": scraped_at,
        })

    # hitRank(순위) 순서로 정렬한다
    rows.sort(key=lambda r: r["hit_rank"])

    # 뽑은 순서대로 1~3번 상품명을 출력한다
    print("--- hitRank로 뽑은 1~3번 상품명 ---")
    for r in rows[:3]:
        print(r["hit_rank"], r["name"])

    # 화면에 실제로 그려지는 순위 제목 글자(ProductListTitle)를 pcode 기준으로 찾는다
    visible_titles = {}
    for _, pcode, _, title in VISIBLE_TITLE_PATTERN.findall(html):
        visible_titles[pcode] = title

    # name(JSON productName)과 화면 글자가 다른 항목 수를 센다
    truncated_count = 0
    for r in rows:
        screen_text = visible_titles.get(r["pcode"])
        if screen_text is not None and screen_text != r["name"]:
            truncated_count += 1
    print(f"화면 글자와 name이 다른 항목(잘려 보이는 이름) 수: {truncated_count}개")

    df = pd.DataFrame(rows, columns=[
        "name", "cpu_raw", "ram_raw", "storage_raw", "screen_size_raw",
        "weight_raw", "price_raw", "mall_count_raw", "detail_url", "scraped_at",
    ])

    # 행 수를 출력한다
    print("행 수:", len(df))

    # 앞 3행을 출력한다
    print(df.head(3))

    # 열마다 빈 값 개수를 출력한다
    print("열마다 빈 값 개수:")
    print((df == "").sum())

    # 화면에서 센 항목 수와 다르면 차이를 알려준다
    if len(df) != EXPECTED_COUNT:
        print(f"항목 수 차이: 화면에서 센 {EXPECTED_COUNT}개와 실제 수집 {len(df)}개가 다름 (차이 {EXPECTED_COUNT - len(df)}개)")

    if len(df) == 0:
        print("0행이므로 저장하지 않고 멈춘다.")
        return

    # 새 결과를 raw_p1.csv로 저장한다
    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    collect()
