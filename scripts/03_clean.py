# 필요한 라이브러리를 불러온다
import re
from pathlib import Path

import pandas as pd

# 스크립트 파일 위치 기준으로 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / ".." / "data" / "raw.csv"
CLEAN_PATH = BASE_DIR / ".." / "data" / "clean.csv"

# raw.csv의 열 이름과 순서
COLUMNS = [
    "name", "cpu_raw", "ram_raw", "storage_raw", "screen_size_raw",
    "weight_raw", "price_raw", "mall_count_raw", "detail_url", "scraped_at",
]


def blank_count(df):
    # 열마다 빈칸(NaN 또는 빈 문자열) 개수를 센다
    result = {}
    for col in df.columns:
        result[col] = int((df[col].isna() | (df[col].astype(str).str.strip() == "")).sum())
    return result


def print_stats(df, label):
    # 처리 전후 상태(행 수, 데이터형, 빈칸 수, detail_url 중복 수)를 출력한다
    print(f"--- {label} ---")
    print("행 수:", len(df))
    print("데이터형:")
    print(df.dtypes)
    print("열별 빈칸 수:")
    for col, cnt in blank_count(df).items():
        print(f"  {col}: {cnt}")
    if "detail_url" in df.columns:
        dup = len(df) - df["detail_url"].nunique()
        print("detail_url 중복 수:", dup)
    print()


def parse_price(price_raw):
    # price_raw에서 쉼표와 "원"을 떼고 정수로 바꾼다. 못 바꾸면 NaN을 돌려준다
    if pd.isna(price_raw):
        return float("nan")
    digits = str(price_raw).replace(",", "").replace("원", "").strip()
    if re.fullmatch(r"\d+", digits):
        return int(digits)
    return float("nan")


def parse_ram_gb(ram_raw):
    # ram_raw에서 "GB"를 떼고 정수로 바꾼다. 못 바꾸면 NaN을 돌려준다
    if pd.isna(ram_raw):
        return float("nan")
    digits = str(ram_raw).replace("GB", "").strip()
    if re.fullmatch(r"\d+", digits):
        return int(digits)
    return float("nan")


def clean():
    # raw.csv를 읽는다 (raw.csv 자체는 고치지 않는다)
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig", usecols=COLUMNS)[COLUMNS]

    # 처리 전 상태를 출력한다
    print_stats(df, "처리 전")

    # 1. price_raw의 쉼표와 "원"을 떼고 정수로 바꿔 price 열을 만든다
    df["price"] = df["price_raw"].apply(parse_price)

    # 2. ram_raw의 "GB"를 떼고 정수로 바꿔 ram_gb 열을 만든다
    df["ram_gb"] = df["ram_raw"].apply(parse_ram_gb)

    # 3. name 앞뒤 공백을 정리한다
    df["name"] = df["name"].astype(str).str.strip()

    # price로 못 바꾼 원문 목록을 출력한다
    bad_price = df.loc[df["price"].isna(), "price_raw"].unique()
    print("price로 못 바꾼 price_raw 원문 목록:", list(bad_price))

    # ram_gb로 못 바꾼 원문 목록을 출력한다
    bad_ram = df.loc[df["ram_gb"].isna(), "ram_raw"].unique()
    print("ram_gb로 못 바꾼 ram_raw 원문 목록:", list(bad_ram))
    print()

    # name · price · detail_url 중 빈칸인 행을 찾는다
    is_blank_name = df["name"].str.strip() == ""
    is_blank_price = df["price"].isna()
    is_blank_url = df["detail_url"].isna() | (df["detail_url"].astype(str).str.strip() == "")
    blank_mask = is_blank_name | is_blank_price | is_blank_url

    # 빈칸 행을 사유와 함께 먼저 출력한다
    print("--- name/price/detail_url 빈칸이라 빼는 행 ---")
    for idx in df.index[blank_mask]:
        reasons = []
        if is_blank_name[idx]:
            reasons.append("name 빈칸")
        if is_blank_price[idx]:
            reasons.append("price 빈칸(변환 실패 포함)")
        if is_blank_url[idx]:
            reasons.append("detail_url 빈칸")
        print(f"행 {idx}: 사유={', '.join(reasons)}")
    print("빈칸이라 뺀 행 수:", int(blank_mask.sum()))
    print()

    # 빈칸 행을 뺀다
    df = df.loc[~blank_mask].copy()

    # detail_url이 겹치는 행(처음 한 행만 남김)을 찾는다
    dup_mask = df["detail_url"].duplicated(keep="first")

    # 겹치는 행을 사유와 함께 먼저 출력한다
    print("--- detail_url이 겹쳐서 빼는 행(처음 한 행만 남김) ---")
    for idx in df.index[dup_mask]:
        print(f"행 {idx}: 사유=detail_url 중복({df.loc[idx, 'detail_url']})")
    print("중복이라 뺀 행 수:", int(dup_mask.sum()))
    print()

    # 중복 행을 뺀다
    df = df.loc[~dup_mask].copy()

    # 처리 후 상태를 출력한다
    print_stats(df, "처리 후")

    # 새 표를 CSV로 저장한다
    df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    clean()
