# 필요한 라이브러리를 불러온다
from pathlib import Path

import pandas as pd

# 스크립트 파일 위치 기준으로 clean.csv 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
CLEAN_PATH = BASE_DIR / ".." / "data" / "clean.csv"


def main():
    # clean.csv를 읽는다 (data 폴더 파일은 고치지 않는다)
    df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")

    # price 열의 개수·최소·최대·평균·중앙값을 구한다
    count = df["price"].count()
    min_price = df["price"].min()
    max_price = df["price"].max()
    mean_price = df["price"].mean()
    median_price = df["price"].median()

    # 최솟값 행의 name과 ram_gb를 찾는다
    min_row = df.loc[df["price"].idxmin()]
    # 최댓값 행의 name과 ram_gb를 찾는다
    max_row = df.loc[df["price"].idxmax()]

    # 평균은 소수 둘째 자리까지 반올림한다
    mean_price_rounded = round(mean_price, 2)

    # 마크다운 표로 출력한다
    print("| 항목 | 값 |")
    print("|---|---|")
    print(f"| 개수 | {count} |")
    print(f"| 최소 | {min_price} ({min_row['name']}, ram_gb={min_row['ram_gb']}) |")
    print(f"| 최대 | {max_price} ({max_row['name']}, ram_gb={max_row['ram_gb']}) |")
    print(f"| 평균 | {mean_price_rounded} |")
    print(f"| 중앙값 | {median_price} |")
    print()

    # 개수와 clean.csv 전체 행 수를 나란히 출력하고 같은지 다른지 적는다
    total_rows = len(df)
    same_or_diff = "같음" if count == total_rows else "다름"
    print(f"price 개수: {count} / clean.csv 전체 행 수: {total_rows} -> {same_or_diff}")
    print()

    # 범주 열(ram_gb) 값별 행 수를 큰 값 순으로 센다
    ram_counts = df["ram_gb"].value_counts().sort_index(ascending=False)
    print("| ram_gb | 행 수 |")
    print("|---|---|")
    for ram_value, cnt in ram_counts.items():
        print(f"| {ram_value} | {cnt} |")

    # 가장 적은 범주가 몇 행인지 따로 적는다
    min_ram_value = ram_counts.idxmin()
    min_ram_count = ram_counts.min()
    print(f"가장 적은 범주: ram_gb={min_ram_value}, {min_ram_count}행")


if __name__ == "__main__":
    main()
