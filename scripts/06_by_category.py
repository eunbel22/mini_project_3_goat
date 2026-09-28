# 필요한 라이브러리를 불러온다
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# 스크립트 파일 위치 기준으로 경로를 정한다
BASE_DIR = Path(__file__).resolve().parent
CLEAN_PATH = BASE_DIR / ".." / "data" / "clean.csv"
CHART_PATH = BASE_DIR / ".." / "charts" / "by_category.png"

# 가로축 순서를 고정한다
RAM_ORDER = [8, 16, 24, 32]


def main():
    # clean.csv를 읽는다 (data 폴더 파일은 고치지 않는다)
    df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")
    n = len(df)

    # ram_gb별로 개수·합·평균을 구한다
    grouped = df.groupby("ram_gb")["price"].agg(["count", "sum", "mean"])

    # 그림을 그린다
    fig, ax = plt.subplots(figsize=(8, 6))

    # 값이 있는 범주만 막대를 그리고, 없는 범주는 건너뛴다
    x_labels = []
    x_pos = []
    bar_heights = []
    pos = 0
    table_rows = []
    for ram in RAM_ORDER:
        if ram in grouped.index:
            cnt = int(grouped.loc[ram, "count"])
            total = grouped.loc[ram, "sum"]
            mean = grouped.loc[ram, "mean"]
            x_labels.append(str(ram))
            x_pos.append(pos)
            bar_heights.append(mean)
            table_rows.append((ram, cnt, total, mean))
        else:
            # 값이 없는 범주는 막대를 그리지 않고 표에는 "자료 없음"으로 적는다
            table_rows.append((ram, None, None, None))
        pos += 1

    bars = ax.bar(x_pos, bar_heights, color="#3B82C4", edgecolor="white", width=0.6)

    # 막대 위에 평균(소수 둘째 자리)과 n을 두 줄로 적는다
    for rect, ram in zip(bars, [r for r in RAM_ORDER if r in grouped.index]):
        cnt = int(grouped.loc[ram, "count"])
        mean = grouped.loc[ram, "mean"]
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height(),
                f"{mean:.2f}\nn={cnt}", ha="center", va="bottom", fontsize=9)

    # 가로축을 8/16/24/32 순서 그대로, 값 없는 자리도 위치만 비워둔다
    ax.set_xticks(range(len(RAM_ORDER)))
    ax.set_xticklabels([str(r) for r in RAM_ORDER])

    # 축 이름과 제목을 영어로 적는다
    ax.set_xlabel("RAM (GB)")
    ax.set_ylabel("Average price (KRW)")
    ax.set_title(f"Average price by RAM, n = {n}")

    # 막대 위 글자가 잘리지 않게 세로축 위쪽 여백을 넉넉히 준다
    ax.margins(y=0.15)

    # 배경 격자선을 옅게 넣고 여백을 정리한다
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    # charts/by_category.png로만 저장한다 (화면 표시는 하지 않는다)
    CHART_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_PATH, dpi=150)
    plt.close(fig)

    # 그룹별 표를 마크다운으로 출력한다
    print("| 범주 | 개수 | 합 | 평균 |")
    print("|---|---|---|---|")
    total_count = 0
    for ram, cnt, total, mean in table_rows:
        if cnt is None:
            print(f"| {ram} | 자료 없음 | 자료 없음 | 자료 없음 |")
        else:
            print(f"| {ram} | {cnt} | {int(total)} | {mean:.2f} |")
            total_count += cnt
    print()

    # 개수 합과 clean 행 수를 나란히 적는다
    same_or_diff = "같음" if total_count == n else "다름"
    print(f"개수 합: {total_count} / clean.csv 행 수: {n} -> {same_or_diff}")


if __name__ == "__main__":
    main()
