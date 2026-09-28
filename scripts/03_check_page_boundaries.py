# 필요한 라이브러리를 불러온다
from pathlib import Path

import pandas as pd

# 스크립트 파일 위치 기준으로 raw.csv 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / ".." / "data" / "raw.csv"


def main():
    # raw.csv를 읽기만 한다 (수집 스크립트는 다시 돌리지 않음)
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")

    # raw.csv에는 page 열이 없어서, 같은 페이지 안 행들이 공유하는 scraped_at 값으로 페이지 경계를 나눈다
    # (02_collect.py의 parse_page가 페이지 하나당 scraped_at을 한 번만 찍기 때문)
    page_keys = df["scraped_at"].tolist()
    boundaries = []
    start = 0
    for i in range(1, len(page_keys) + 1):
        if i == len(page_keys) or page_keys[i] != page_keys[start]:
            boundaries.append((start, i - 1))
            start = i

    print("나뉜 페이지(같은 scraped_at 기준) 수:", len(boundaries))

    # 페이지마다 첫 이름과 끝 이름을 출력한다
    for page_num, (first_idx, last_idx) in enumerate(boundaries, start=1):
        first_name = df.iloc[first_idx]["name"]
        last_name = df.iloc[last_idx]["name"]
        print(f"페이지 {page_num} (행 {first_idx}~{last_idx}) scraped_at={page_keys[first_idx]}")
        print(f"  첫 이름: {first_name}")
        print(f"  끝 이름: {last_name}")


if __name__ == "__main__":
    main()
