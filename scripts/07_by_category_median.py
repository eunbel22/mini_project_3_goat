# 필요한 라이브러리를 불러온다
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# 스크립트 파일 위치 기준으로 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
CLEAN_PATH = BASE_DIR / ".." / "data" / "clean.csv"
CHART_PATH = BASE_DIR / ".." / "charts" / "by_category_median.png"

# 가로축 순서를 고정한다 (06_by_category.py와 동일)
RAM_ORDER = [8, 16, 24, 32]


def main():
    # clean.csv를 읽는다 (data 폴더 파일은 고치지 않는다)
    df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")
    n = len(df)

    # ram_gb별로 개수·중앙값·평균을 구한다 (평균은 순서 비교용으로만 쓴다)
    grouped = df.groupby("ram_gb")["price"].agg(["count", "median", "mean"])

    # 그림을 그린다
    fig, ax = plt.subplots(figsize=(8, 6))

    x_pos = []
    bar_heights = []
    pos = 0
    for ram in RAM_ORDER:
        if ram in grouped.index:
            x_pos.append(pos)
            bar_heights.append(grouped.loc[ram, "median"])
        pos += 1

    bars = ax.bar(x_pos, bar_heights, color="#3B82C4", edgecolor="white", width=0.6)

    # 막대 위에 중앙값과 n을 두 줄로 적는다
    for rect, ram in zip(bars, [r for r in RAM_ORDER if r in grouped.index]):
        cnt = int(grouped.loc[ram, "count"])
        median = grouped.loc[ram, "median"]
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height(),
                f"{median:.2f}\nn={cnt}", ha="center", va="bottom", fontsize=9)

    # 가로축을 8/16/24/32 순서 그대로 맞춘다
    ax.set_xticks(range(len(RAM_ORDER)))
    ax.set_xticklabels([str(r) for r in RAM_ORDER])

    # 축 이름과 제목을 영어로 적는다
    ax.set_xlabel("RAM (GB)")
    ax.set_ylabel("Median price (KRW)")
    ax.set_title(f"Median price by RAM, n = {n}")

    # 막대 위 글자가 잘리지 않게 세로축 위쪽 여백을 넉넉히 준다
    ax.margins(y=0.15)

    # 배경 격자선을 옅게 넣고 여백을 정리한다
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    # charts/by_category_median.png로만 저장한다 (by_category.png는 건드리지 않는다)
    CHART_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_PATH, dpi=150)
    plt.close(fig)

    # 그룹별 표를 마크다운으로 출력한다 (중앙값·평균 둘 다 보여 순서 비교)
    print("| 범주 | 개수 | 중앙값 | 평균 |")
    print("|---|---|---|---|")
    for ram in RAM_ORDER:
        if ram in grouped.index:
            cnt = int(grouped.loc[ram, "count"])
            median = grouped.loc[ram, "median"]
            mean = grouped.loc[ram, "mean"]
            print(f"| {ram} | {cnt} | {median:.2f} | {mean:.2f} |")
        else:
            print(f"| {ram} | 자료 없음 | 자료 없음 | 자료 없음 |")
    print()

    # 중앙값 순위와 평균 순위를 비교한다
    present = [r for r in RAM_ORDER if r in grouped.index]
    median_rank = sorted(present, key=lambda r: grouped.loc[r, "median"], reverse=True)
    mean_rank = sorted(present, key=lambda r: grouped.loc[r, "mean"], reverse=True)
    print("중앙값 기준 내림차순 순위:", median_rank)
    print("평균 기준 내림차순 순위:", mean_rank)
    print("순위가 같은가:", "같음" if median_rank == mean_rank else "다름")


if __name__ == "__main__":
    main()
