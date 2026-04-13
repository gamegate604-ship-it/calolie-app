"""Calolie — grouped bar chart (摂取 vs 消費) with Roman dark theme."""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np

CSV_FILE = "food_log.csv"
BMR_KCAL = 1630

# ── Palette ──────────────────────────────────────────────────────────────────
C_BG      = "#1A1610"
C_PANEL   = "#26201A"
C_GRID    = "#38281C"
C_TEXT    = "#C8B48A"
C_DIM     = "#7A6848"
C_HEAD    = "#C8963C"
C_INTAKE  = "#C8963C"
C_CONSUME = "#6AAF5A"
C_POS     = "#8B1A1A"
C_NEG     = "#4A9B38"
C_BORDER  = "#4A3C28"


def load_data():
    if not os.path.exists(CSV_FILE):
        return {}, {}
    intake  = defaultdict(float)
    expense = defaultdict(float)
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d    = r.get("日付", "").strip()
            kcal = r.get("カロリー(kcal)", "0").strip()
            kind = r.get("種別", "摂取").strip()
            if not d or not kcal:
                continue
            try:
                v = float(kcal)
            except ValueError:
                continue
            if kind == "消費":
                expense[d] += v
            else:
                intake[d] += v
    return intake, expense


def main():
    # Change to app directory so CSV is found regardless of cwd
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    intake_d, expense_d = load_data()
    all_dates = sorted(set(intake_d) | set(expense_d))

    if not all_dates:
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=C_BG)
        ax.set_facecolor(C_PANEL)
        ax.text(0.5, 0.5, "記録がありません", ha="center", va="center",
                color=C_DIM, fontsize=14, transform=ax.transAxes)
        plt.tight_layout()
        plt.show()
        return

    intake_v  = [intake_d.get(d, 0.0)              for d in all_dates]
    exercise_v = [expense_d.get(d, 0.0)             for d in all_dates]
    consume_v = [BMR_KCAL + e                        for e in exercise_v]
    balance_v = [i - c for i, c in zip(intake_v, consume_v)]

    x   = np.arange(len(all_dates))
    w   = 0.38

    fig, ax = plt.subplots(figsize=(max(8, len(all_dates) * 1.4), 6), facecolor=C_BG)
    ax.set_facecolor(C_PANEL)

    bars_in  = ax.bar(x - w / 2, intake_v,  width=w, color=C_INTAKE,  label="摂取", zorder=3)
    bars_con = ax.bar(x + w / 2, consume_v, width=w, color=C_CONSUME, label="消費(BMR+運動)", zorder=3)

    # Balance annotation above / below the taller bar
    for i, (iv, cv, bv) in enumerate(zip(intake_v, consume_v, balance_v)):
        top   = max(iv, cv)
        color = C_POS if bv >= 0 else C_NEG
        sign  = "+" if bv >= 0 else ""
        ax.text(x[i], top + 20, f"{sign}{bv:.0f}", ha="center", va="bottom",
                fontsize=9, color=color, fontweight="bold", zorder=4)

    # Value labels inside bars
    for bar in bars_in:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h / 2,
                    f"{h:.0f}", ha="center", va="center",
                    fontsize=8, color=C_BG, fontweight="bold", zorder=5)
    for bar in bars_con:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h / 2,
                    f"{h:.0f}", ha="center", va="center",
                    fontsize=8, color=C_BG, fontweight="bold", zorder=5)

    # Baseline BMR line
    ax.axhline(BMR_KCAL, color=C_DIM, linewidth=1, linestyle="--", zorder=2,
               label=f"基礎代謝 {BMR_KCAL} kcal")

    # Axes styling
    ax.set_xticks(x)
    ax.set_xticklabels(all_dates, rotation=30, ha="right", color=C_TEXT, fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=C_TEXT)
    ax.tick_params(colors=C_DIM)
    ax.set_ylabel("kcal", color=C_DIM, fontsize=10)
    ax.spines[:].set_color(C_BORDER)
    ax.grid(axis="y", color=C_GRID, linewidth=0.8, zorder=1)
    ax.set_title("カロリー収支", color=C_HEAD, fontsize=14, pad=14)

    ax.legend(
        facecolor=C_PANEL, edgecolor=C_BORDER,
        labelcolor=C_TEXT, fontsize=9,
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
