"""Calolie — Streamlit Web App（カロリー記録）"""
import csv
import os
from collections import defaultdict
from datetime import date as _date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ── 定数 ────────────────────────────────────────────────────────────────────
CSV_FILE   = "food_log.csv"
FIELDNAMES = ["日付", "種別", "食事", "食べ物", "カロリー(kcal)"]
BMR_KCAL   = 1630

MEAL_TIMES     = ["朝", "昼", "夜", "間食"]
ACTIVITY_TYPES = ["ランニング20分", "フットサル1時間", "エルゴ2000m", "自重筋トレ20分", "ヨガ20分"]
ACTIVITY_KCAL  = {
    "ランニング20分":  200,
    "フットサル1時間": 600,
    "エルゴ2000m":    120,
    "自重筋トレ20分": 100,
    "ヨガ20分":       60,
}
FOOD_OPTIONS = ["バナナ", "カレー", "うどん", "定食", "ご飯", "パン", "サラダ",
                "ラーメン", "パスタ", "チキン", "卵", "ヨーグルト", "牛乳",
                "おにぎり", "サンドイッチ", "ハンバーガー", "コーヒー", "ジュース"]
FOOD_KCAL = {
    "バナナ": 90, "カレー": 700, "うどん": 300, "定食": 650,
    "ご飯": 270, "パン": 250, "サラダ": 80, "ラーメン": 500,
    "パスタ": 450, "チキン": 300, "卵": 90, "ヨーグルト": 100,
    "牛乳": 130, "おにぎり": 180, "サンドイッチ": 350, "ハンバーガー": 550,
    "コーヒー": 5, "ジュース": 120,
}

# Matplotlib ダークテーマ
PALETTE = dict(
    bg="#1A1610", panel="#26201A", grid="#38281C",
    text="#C8B48A", dim="#7A6848", head="#C8963C",
    intake="#C8963C", consume="#6AAF5A",
    pos="#8B1A1A", neg="#4A9B38", border="#4A3C28",
)


# ── CSV ──────────────────────────────────────────────────────────────────────
def load_df() -> pd.DataFrame:
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=FIELDNAMES)
    try:
        df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=FIELDNAMES)
    for col in FIELDNAMES:
        if col not in df.columns:
            df[col] = ""
    if "種別" not in df.columns or df["種別"].eq("").all():
        df["種別"] = "摂取"
    return df[FIELDNAMES]


def save_df(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False, encoding="utf-8")


# ── グラフ ────────────────────────────────────────────────────────────────────
def build_figure(df: pd.DataFrame):
    p = PALETTE
    intake_rows  = df[df["種別"] == "摂取"].copy()
    expense_rows = df[df["種別"] == "消費"].copy()

    intake_rows["カロリー(kcal)"]  = pd.to_numeric(intake_rows["カロリー(kcal)"],  errors="coerce").fillna(0)
    expense_rows["カロリー(kcal)"] = pd.to_numeric(expense_rows["カロリー(kcal)"], errors="coerce").fillna(0)

    intake_by_date  = intake_rows.groupby("日付")["カロリー(kcal)"].sum()
    expense_by_date = expense_rows.groupby("日付")["カロリー(kcal)"].sum()

    all_dates = sorted(set(intake_by_date.index) | set(expense_by_date.index))
    if not all_dates:
        return None

    intake_v  = [intake_by_date.get(d, 0) for d in all_dates]
    exercise_v = [expense_by_date.get(d, 0) for d in all_dates]
    consume_v = [BMR_KCAL + e for e in exercise_v]
    balance_v = [i - c for i, c in zip(intake_v, consume_v)]

    x = np.arange(len(all_dates))
    w = 0.38

    fig, ax = plt.subplots(figsize=(max(7, len(all_dates) * 1.4), 5),
                           facecolor=p["bg"])
    ax.set_facecolor(p["panel"])

    bars_in  = ax.bar(x - w / 2, intake_v,  width=w, color=p["intake"],  label="摂取",          zorder=3)
    bars_con = ax.bar(x + w / 2, consume_v, width=w, color=p["consume"], label="消費(BMR+運動)", zorder=3)

    for i, (iv, cv, bv) in enumerate(zip(intake_v, consume_v, balance_v)):
        top   = max(iv, cv)
        color = p["pos"] if bv >= 0 else p["neg"]
        sign  = "+" if bv >= 0 else ""
        ax.text(x[i], top + 20, f"{sign}{bv:.0f}",
                ha="center", va="bottom", fontsize=9,
                color=color, fontweight="bold", zorder=4)

    for bar in [*bars_in, *bars_con]:
        h = bar.get_height()
        if h > 50:
            ax.text(bar.get_x() + bar.get_width() / 2, h / 2,
                    f"{h:.0f}", ha="center", va="center",
                    fontsize=8, color=p["bg"], fontweight="bold", zorder=5)

    ax.axhline(BMR_KCAL, color=p["dim"], linewidth=1, linestyle="--",
               zorder=2, label=f"基礎代謝 {BMR_KCAL} kcal")

    ax.set_xticks(x)
    ax.set_xticklabels(all_dates, rotation=30, ha="right", color=p["text"], fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=p["text"])
    ax.tick_params(colors=p["dim"])
    ax.set_ylabel("kcal", color=p["dim"], fontsize=10)
    ax.spines[:].set_color(p["border"])
    ax.grid(axis="y", color=p["grid"], linewidth=0.8, zorder=1)
    ax.set_title("カロリー収支", color=p["head"], fontsize=14, pad=14)
    ax.legend(facecolor=p["panel"], edgecolor=p["border"],
              labelcolor=p["text"], fontsize=9)

    plt.tight_layout()
    return fig


# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Calolie",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタム CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1A1610; }
    div[data-testid="metric-container"] {
        background: #26201A;
        border: 1px solid #4A3C28;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .stButton > button {
        background-color: #38281C;
        color: #C8B48A;
        border: 1px solid #4A3C28;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #8B1A1A;
        border-color: #C8963C;
        color: #C8B48A;
    }
    h1, h2, h3 { color: #C8963C !important; }
</style>
""", unsafe_allow_html=True)


# ── セッション初期化 ──────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load_df()


def reload():
    st.session_state.df = load_df()


df = st.session_state.df

# ── サイドバー（入力フォーム） ────────────────────────────────────────────────
with st.sidebar:
    st.title("🏛️ Calolie")
    st.caption("カロリー記録")
    st.divider()

    kind = st.radio("種別", ["摂取", "消費"], horizontal=True)
    entry_date = st.date_input("日付", value=_date.today(), format="YYYY-MM-DD")

    if kind == "摂取":
        meal = st.selectbox("食事", MEAL_TIMES)

        food_choice = st.selectbox("食べ物", FOOD_OPTIONS + ["その他を入力..."])
        if food_choice == "その他を入力...":
            food_name = st.text_input("食べ物名を入力", placeholder="例: チーズケーキ")
            default_kcal = 0
        else:
            food_name    = food_choice
            default_kcal = FOOD_KCAL.get(food_choice, 0)

        kcal = st.number_input("カロリー (kcal)", min_value=0, value=default_kcal, step=10)

    else:  # 消費
        activity = st.selectbox("活動", ACTIVITY_TYPES)
        meal     = activity
        food_name = st.text_input("活動メモ（任意）", placeholder="例: 公園で実施")
        kcal     = st.number_input("カロリー (kcal)", min_value=0,
                                    value=ACTIVITY_KCAL.get(activity, 0), step=10)

    st.divider()
    if st.button("保存  ＋", use_container_width=True, type="primary"):
        if not food_name and kind == "摂取":
            st.error("食べ物名を入力してください。")
        elif kcal <= 0:
            st.error("カロリーを入力してください。")
        else:
            new_row = pd.DataFrame([{
                "日付":           str(entry_date),
                "種別":           kind,
                "食事":           meal,
                "食べ物":         food_name if kind == "摂取" else activity,
                "カロリー(kcal)": str(kcal),
            }])
            updated = pd.concat([df, new_row], ignore_index=True)
            save_df(updated)
            st.session_state.df = updated
            st.success("保存しました！")
            st.rerun()


# ── メインエリア ──────────────────────────────────────────────────────────────
st.title("🏛️ Calolie — カロリー収支")

tab_balance, tab_log, tab_graph = st.tabs(["📊 収支", "📋 記録一覧", "📈 グラフ"])

# ── Tab 1: 収支 ───────────────────────────────────────────────────────────────
with tab_balance:
    all_dates = sorted(df["日付"].unique(), reverse=True)
    today_str = str(_date.today())

    default_idx = 0
    if today_str in all_dates:
        default_idx = all_dates.index(today_str)

    if all_dates:
        sel_date = st.selectbox("日付を選択", all_dates, index=default_idx)
    else:
        sel_date = today_str
        st.info("まだ記録がありません。サイドバーから追加してください。")

    day_df = df[df["日付"] == sel_date].copy()
    day_df["カロリー(kcal)"] = pd.to_numeric(day_df["カロリー(kcal)"], errors="coerce").fillna(0)

    intake_kcal  = day_df[day_df["種別"] == "摂取"]["カロリー(kcal)"].sum()
    exercise_kcal = day_df[day_df["種別"] == "消費"]["カロリー(kcal)"].sum()
    consume_kcal = BMR_KCAL + exercise_kcal
    balance      = intake_kcal - consume_kcal

    col1, col2, col3 = st.columns(3)
    col1.metric("摂取", f"{intake_kcal:,.0f} kcal")
    col2.metric("消費",
                f"{consume_kcal:,.0f} kcal",
                f"基礎代謝 {BMR_KCAL:,} + 運動 {exercise_kcal:,.0f}")
    sign = "+" if balance >= 0 else ""
    col3.metric("収支", f"{sign}{balance:,.0f} kcal")

    if balance > 0:
        st.warning(f"本日は {balance:,.0f} kcal のプラスです。")
    elif balance < 0:
        st.success(f"本日は {abs(balance):,.0f} kcal のマイナスです。")
    else:
        st.info("本日の収支はちょうどゼロです。")


# ── Tab 2: 記録一覧 ────────────────────────────────────────────────────────────
with tab_log:
    col_l, col_r = st.columns([3, 1])
    with col_r:
        sort_order = st.selectbox("日付ソート", ["降順（新しい順）", "昇順（古い順）"], label_visibility="collapsed")

    asc = sort_order == "昇順（古い順）"
    display_df = df.copy()
    display_df["カロリー(kcal)"] = pd.to_numeric(display_df["カロリー(kcal)"], errors="coerce")
    display_df = display_df.sort_values("日付", ascending=asc)

    st.subheader("摂取")
    intake_df = display_df[display_df["種別"] == "摂取"][["日付", "食事", "食べ物", "カロリー(kcal)"]].reset_index(drop=True)
    if intake_df.empty:
        st.caption("記録なし")
    else:
        st.dataframe(intake_df, use_container_width=True, hide_index=True)

    st.subheader("消費")
    expense_df = display_df[display_df["種別"] == "消費"][["日付", "食事", "食べ物", "カロリー(kcal)"]].rename(
        columns={"食事": "活動", "食べ物": "メモ"}).reset_index(drop=True)
    if expense_df.empty:
        st.caption("記録なし")
    else:
        st.dataframe(expense_df, use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("⚠️ 記録を削除する"):
        if df.empty:
            st.caption("記録がありません。")
        else:
            del_date = st.selectbox("削除する日付", sorted(df["日付"].unique(), reverse=True),
                                     key="del_date")
            del_kind = st.radio("種別", ["摂取", "消費"], key="del_kind", horizontal=True)
            day_rows = df[(df["日付"] == del_date) & (df["種別"] == del_kind)].reset_index()
            if day_rows.empty:
                st.caption("該当する記録がありません。")
            else:
                options = [
                    f"{r['食べ物']} ({r['カロリー(kcal)']} kcal)"
                    for _, r in day_rows.iterrows()
                ]
                del_idx = st.selectbox("削除する行", range(len(options)),
                                        format_func=lambda i: options[i], key="del_idx")
                if st.button("削除する", type="secondary"):
                    orig_idx = day_rows.iloc[del_idx]["index"]
                    updated  = df.drop(index=orig_idx).reset_index(drop=True)
                    save_df(updated)
                    st.session_state.df = updated
                    st.success("削除しました。")
                    st.rerun()


# ── Tab 3: グラフ ──────────────────────────────────────────────────────────────
with tab_graph:
    fig = build_figure(df)
    if fig is None:
        st.info("記録がありません。サイドバーからデータを追加してください。")
    else:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
