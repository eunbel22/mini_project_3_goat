# 필요한 라이브러리를 불러온다
import json
from pathlib import Path

import pandas as pd

# 스크립트 파일 위치 기준으로 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
CLEAN_PATH = BASE_DIR / ".." / "data" / "clean.csv"
JSON_PATH = BASE_DIR / ".." / "data" / "data.json"


def main():
    # clean.csv를 읽는다 (clean.csv 자체는 고치지 않는다)
    df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")

    # name, price, ram_gb, detail_url 열만 고른다
    df_export = df[["name", "price", "ram_gb", "detail_url"]]

    # 한 행을 한 묶음으로 하는 목록 모양(records)으로 바꾼다
    records = df_export.to_dict(orient="records")

    # 한글이 깨지지 않게 utf-8로, 사람이 읽기 좋게 들여쓰기해서 저장한다
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # 저장한 data.json을 다시 읽는다
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    # 항목 수와 clean.csv 행 수를 나란히 출력하고 같은지 다른지 적는다
    json_count = len(loaded)
    csv_count = len(df)
    same_or_diff = "같음" if json_count == csv_count else "다름"
    print(f"data.json 항목 수: {json_count} / clean.csv 행 수: {csv_count} -> {same_or_diff}")
    print()

    # data.json 첫 항목과 clean.csv 첫 줄의 네 값을 나란히 보여준다
    first_json = loaded[0]
    first_csv = df_export.iloc[0]
    print("--- 첫 항목 비교 ---")
    for col in ["name", "price", "ram_gb", "detail_url"]:
        print(f"{col}: data.json={first_json[col]} / clean.csv={first_csv[col]}")


if __name__ == "__main__":
    main()
