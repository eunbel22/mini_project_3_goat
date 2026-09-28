# 필요한 라이브러리를 불러온다
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 스크립트 파일 위치 기준으로 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
CLEAN_PATH = BASE_DIR / ".." / "data" / "clean.csv"
CHART_PATH = BASE_DIR / ".." / "charts" / "hist.png"

# 구간 경계를 고정값으로 정한다
BIN_EDGES = [500000, 1000000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000]


def main():
    # clean.csv를 읽는다 (data 폴더 파일은 고치지 않는다)
    df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")
    n = len(df)

    # 왼쪽 끝 포함·오른쪽 끝 미포함, 마지막 구간만 오른쪽 끝 포함으로 구간별 개수를 센다
    counts, edges = np.histogram(df["price"], bins=BIN_EDGES)

    # 그림을 그린다 (막대 그래프 형태의 히스토그램)
    fig, ax = plt.subplots(figsize=(9, 6))
    bin_centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
    bin_widths = [edges[i + 1] - edges[i] for i in range(len(edges) - 1)]
    bars = ax.bar(bin_centers, counts, width=[w * 0.9 for w in bin_widths], color="#3B82C4", edgecolor="white")

    # 막대 위에 개수를 적는다
    for rect, cnt in zip(bars, counts):
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.05,
                str(int(cnt)), ha="center", va="bottom", fontsize=10)

    # 가로축 눈금을 구간 경계로 맞춘다
    ax.set_xticks(BIN_EDGES)
    ax.set_xticklabels([str(x) for x in BIN_EDGES], rotation=45, ha="right")

    # 축 이름과 제목을 영어로 적는다
    ax.set_xlabel("Price (KRW)")
    ax.set_ylabel("Number of laptops")
    ax.set_title(f"Danawa laptops (cate=112758), page 1\nn = {n}")

    # 배경 격자선을 옅게 넣고 여백을 정리한다
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    # charts/hist.png로만 저장한다 (화면 표시는 하지 않는다)
    CHART_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_PATH, dpi=150)
    plt.close(fig)

    # 구간별 빈도 표를 마크다운으로 출력한다
    print("| 구간 | 개수 |")
    print("|---|---|")
    for i in range(len(BIN_EDGES) - 1):
        left = BIN_EDGES[i]
        right = BIN_EDGES[i + 1]
        bracket = "]" if i == len(BIN_EDGES) - 2 else ")"
        print(f"| [{left}, {right}{bracket} | {int(counts[i])} |")

    total_count = int(counts.sum())
    print(f"| 합계 | {total_count} |")
    print()

    # 빈도 합과 clean 행 수를 나란히 출력하고 같은지 다른지 적는다
    same_or_diff = "같음" if total_count == n else "다름"
    print(f"빈도 합: {total_count} / clean.csv 행 수: {n} -> {same_or_diff}")


if __name__ == "__main__":
    main()
