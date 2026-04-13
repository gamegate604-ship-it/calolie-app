"""Calolie — おしゃれカロリー記録 Web アプリ"""
import os
from datetime import date as _date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ── 定数 ─────────────────────────────────────────────────────────────────────
CSV_FILE   = "food_log.csv"
FIELDNAMES = ["日付", "種別", "食事", "食べ物", "カロリー(kcal)",
              "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
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

# 栄養素データ（100g相当の標準的な値）
NUTRITION: dict[str, dict] = {
    "バナナ":        {"kcal": 90,  "protein": 1.1, "fat": 0.2, "carbs": 21.4, "fiber": 1.1},
    "カレー":        {"kcal": 700, "protein": 20.0, "fat": 30.0, "carbs": 85.0, "fiber": 3.0},
    "うどん":        {"kcal": 300, "protein": 8.5,  "fat": 1.0,  "carbs": 62.0, "fiber": 1.3},
    "定食":          {"kcal": 650, "protein": 28.0, "fat": 18.0, "carbs": 85.0, "fiber": 3.0},
    "ご飯":          {"kcal": 270, "protein": 4.5,  "fat": 0.5,  "carbs": 59.0, "fiber": 0.5},
    "パン":          {"kcal": 250, "protein": 8.0,  "fat": 4.0,  "carbs": 46.0, "fiber": 2.5},
    "サラダ":        {"kcal": 80,  "protein": 2.0,  "fat": 4.0,  "carbs": 8.0,  "fiber": 2.0},
    "ラーメン":      {"kcal": 500, "protein": 18.0, "fat": 18.0, "carbs": 65.0, "fiber": 2.0},
    "パスタ":        {"kcal": 450, "protein": 14.0, "fat": 8.0,  "carbs": 78.0, "fiber": 3.0},
    "チキン":        {"kcal": 300, "protein": 35.0, "fat": 10.0, "carbs": 5.0,  "fiber": 0.0},
    "卵":            {"kcal": 90,  "protein": 7.3,  "fat": 6.2,  "carbs": 0.2,  "fiber": 0.0},
    "ヨーグルト":    {"kcal": 100, "protein": 4.0,  "fat": 3.0,  "carbs": 14.0, "fiber": 0.0},
    "牛乳":          {"kcal": 130, "protein": 6.8,  "fat": 7.8,  "carbs": 9.5,  "fiber": 0.0},
    "おにぎり":      {"kcal": 180, "protein": 3.5,  "fat": 0.5,  "carbs": 39.0, "fiber": 0.5},
    "サンドイッチ":  {"kcal": 350, "protein": 12.0, "fat": 12.0, "carbs": 46.0, "fiber": 2.0},
    "ハンバーガー":  {"kcal": 550, "protein": 25.0, "fat": 28.0, "carbs": 52.0, "fiber": 2.0},
    "コーヒー":      {"kcal": 5,   "protein": 0.1,  "fat": 0.0,  "carbs": 0.7,  "fiber": 0.0},
    "ジュース":      {"kcal": 120, "protein": 0.5,  "fat": 0.2,  "carbs": 29.0, "fiber": 0.5},
    "アボカドトースト": {"kcal": 380, "protein": 9.0, "fat": 20.0, "carbs": 42.0, "fiber": 7.0},
    "スムージー":    {"kcal": 160, "protein": 3.0,  "fat": 1.0,  "carbs": 36.0, "fiber": 3.0},
    "グラノーラ":    {"kcal": 420, "protein": 8.0,  "fat": 15.0, "carbs": 64.0, "fiber": 5.0},
    "プロテイン":    {"kcal": 120, "protein": 24.0, "fat": 1.5,  "carbs": 4.0,  "fiber": 0.5},
    "チョコレート":  {"kcal": 280, "protein": 3.5,  "fat": 17.0, "carbs": 30.0, "fiber": 2.0},
    "フルーツ盛り":  {"kcal": 150, "protein": 1.5,  "fat": 0.5,  "carbs": 36.0, "fiber": 3.0},
    "アイスクリーム":{"kcal": 220, "protein": 3.5,  "fat": 11.0, "carbs": 28.0, "fiber": 0.0},
    "お寿司（5貫）": {"kcal": 350, "protein": 18.0, "fat": 5.0,  "carbs": 58.0, "fiber": 1.0},
    "唐揚げ":        {"kcal": 480, "protein": 28.0, "fat": 28.0, "carbs": 25.0, "fiber": 0.5},
}
FOOD_OPTIONS = sorted(NUTRITION.keys())

# グラフパレット
P = dict(
    bg="#FFF5F9", panel="#FFFFFF", grid="#F0E6EC",
    text="#2D2D2D", dim="#999999", head="#FF6B9D",
    intake="#FF6B9D", consume="#A78BFA",
    pos="#FF6B9D", neg="#34D399", border="#F9A8D4",
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
    intake_rows  = df[df["種別"] == "摂取"].copy()
    expense_rows = df[df["種別"] == "消費"].copy()
    for d in [intake_rows, expense_rows]:
        d["カロリー(kcal)"] = pd.to_numeric(d["カロリー(kcal)"], errors="coerce").fillna(0)

    intake_by  = intake_rows.groupby("日付")["カロリー(kcal)"].sum()
    expense_by = expense_rows.groupby("日付")["カロリー(kcal)"].sum()
    all_dates  = sorted(set(intake_by.index) | set(expense_by.index))
    if not all_dates:
        return None

    intake_v  = [intake_by.get(d, 0)  for d in all_dates]
    exercise_v = [expense_by.get(d, 0) for d in all_dates]
    consume_v = [BMR_KCAL + e          for e in exercise_v]
    balance_v = [i - c for i, c in zip(intake_v, consume_v)]

    x, w = np.arange(len(all_dates)), 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(all_dates) * 1.4), 5),
                           facecolor=P["bg"])
    ax.set_facecolor(P["panel"])

    bars_in  = ax.bar(x - w / 2, intake_v,  width=w, color=P["intake"],  label="摂取",          zorder=3, alpha=0.85)
    bars_con = ax.bar(x + w / 2, consume_v, width=w, color=P["consume"], label="消費(BMR+運動)", zorder=3, alpha=0.85)

    for i, (iv, cv, bv) in enumerate(zip(intake_v, consume_v, balance_v)):
        top   = max(iv, cv)
        color = P["pos"] if bv >= 0 else P["neg"]
        sign  = "+" if bv >= 0 else ""
        ax.text(x[i], top + 20, f"{sign}{bv:.0f}",
                ha="center", va="bottom", fontsize=9,
                color=color, fontweight="bold", zorder=4)

    for bar in [*bars_in, *bars_con]:
        h = bar.get_height()
        if h > 50:
            ax.text(bar.get_x() + bar.get_width() / 2, h / 2,
                    f"{h:.0f}", ha="center", va="center",
                    fontsize=8, color="#FFFFFF", fontweight="bold", zorder=5)

    ax.axhline(BMR_KCAL, color=P["dim"], linewidth=1.2, linestyle="--",
               zorder=2, label=f"基礎代謝 {BMR_KCAL} kcal")
    ax.set_xticks(x)
    ax.set_xticklabels(all_dates, rotation=30, ha="right", color=P["text"], fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=P["text"])
    ax.tick_params(colors=P["dim"])
    ax.set_ylabel("kcal", color=P["dim"], fontsize=10)
    ax.spines[:].set_color(P["border"])
    ax.grid(axis="y", color=P["grid"], linewidth=0.8, zorder=1)
    ax.set_title("カロリー収支", color=P["head"], fontsize=14, pad=14, fontweight="bold")
    ax.legend(facecolor=P["panel"], edgecolor=P["border"], labelcolor=P["text"], fontsize=9)
    plt.tight_layout()
    return fig


# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Calolie ✨",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── 全体 ── */
html, body, [class*="css"] { font-family: 'Hiragino Sans', 'Noto Sans JP', sans-serif; }

/* ── ヘッダーグラデーション ── */
.gradient-title {
    background: linear-gradient(90deg, #FF6B9D, #C084FC, #60A5FA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: 0.02em;
    margin-bottom: 0;
}
.subtitle { color: #888; font-size: 0.85rem; margin-top: -4px; }

/* ── カード ── */
.card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(255,107,157,0.10);
    margin-bottom: 12px;
}

/* ── メトリクス ── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 2px 12px rgba(255,107,157,0.10);
    border: 1px solid #F9D0E0;
}

/* ── ボタン ── */
.stButton > button {
    border-radius: 50px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em;
    transition: all 0.2s;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(255,107,157,0.3); }

/* ── サイドバー ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFF0F5 0%, #F5F0FF 100%);
    border-right: 1px solid #F9D0E0;
}

/* ── 入力 ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border-radius: 12px !important;
}

/* ── 保存済みバナー ── */
.saved-banner {
    background: linear-gradient(90deg, #FF6B9D22, #C084FC22);
    border: 1px solid #FF6B9D66;
    border-radius: 12px;
    padding: 12px 16px;
    text-align: center;
    color: #FF6B9D;
    font-weight: 700;
    margin-bottom: 12px;
}

/* ── 栄養バー ── */
.nutr-row { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
.nutr-label { width: 70px; font-size: 0.8rem; color: #888; }
.nutr-bar-bg { flex: 1; background: #F0E6EC; border-radius: 8px; height: 8px; overflow: hidden; }
.nutr-bar { height: 8px; border-radius: 8px; }
.nutr-val { width: 50px; font-size: 0.8rem; color: #555; text-align: right; }

/* ── タブ ── */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { border-radius: 50px; padding: 6px 18px; }
</style>
""", unsafe_allow_html=True)


# ── セッション初期化 ──────────────────────────────────────────────────────────
for k, v in [("df", None), ("form_key", 0), ("just_saved", False),
             ("edit_idx", None), ("edit_mode", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.df is None:
    st.session_state.df = load_df()

df = st.session_state.df
fk = st.session_state.form_key  # form key: 変わるとウィジェットがリセット


# ── サイドバー ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="gradient-title">🌸 Calolie</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">あなたの毎日をキレイに記録</p>', unsafe_allow_html=True)
    st.divider()

    # 保存成功バナー（フォームリセット後に表示）
    if st.session_state.just_saved:
        st.markdown('<div class="saved-banner">✅ 保存しました！</div>', unsafe_allow_html=True)
        st.session_state.just_saved = False

    kind = st.radio("種別", ["🍽️ 摂取", "🏃 消費"],
                    horizontal=True, key=f"kind_{fk}")
    kind_val = "摂取" if "摂取" in kind else "消費"

    entry_date = st.date_input("📅 日付", value=_date.today(),
                                format="YYYY-MM-DD", key=f"date_{fk}")

    nutrition = {"protein": 0.0, "fat": 0.0, "carbs": 0.0, "fiber": 0.0}

    if kind_val == "摂取":
        meal = st.selectbox("🕐 食事タイミング", MEAL_TIMES, key=f"meal_{fk}")

        food_choice = st.selectbox("🥗 食べ物を選ぶ",
                                    FOOD_OPTIONS + ["✏️ その他を入力..."],
                                    key=f"food_sel_{fk}")

        if food_choice == "✏️ その他を入力...":
            food_name    = st.text_input("食べ物名", placeholder="例: タピオカ", key=f"food_txt_{fk}")
            default_kcal = 0
        else:
            food_name    = food_choice
            ndata        = NUTRITION.get(food_name, {})
            default_kcal = ndata.get("kcal", 0)
            nutrition    = {"protein": ndata.get("protein", 0),
                            "fat":     ndata.get("fat", 0),
                            "carbs":   ndata.get("carbs", 0),
                            "fiber":   ndata.get("fiber", 0)}

        kcal = st.number_input("🔥 カロリー (kcal)",
                                min_value=0, value=default_kcal, step=10, key=f"kcal_{fk}")

        # 栄養素（プリセットで自動入力、編集可）
        with st.expander("🧬 栄養素を確認・編集"):
            p_val = st.number_input("タンパク質 (g)", value=float(nutrition["protein"]),
                                     min_value=0.0, step=0.1, key=f"prot_{fk}")
            f_val = st.number_input("脂質 (g)", value=float(nutrition["fat"]),
                                     min_value=0.0, step=0.1, key=f"fat_{fk}")
            c_val = st.number_input("炭水化物 (g)", value=float(nutrition["carbs"]),
                                     min_value=0.0, step=0.1, key=f"carbs_{fk}")
            fi_val = st.number_input("食物繊維 (g)", value=float(nutrition["fiber"]),
                                      min_value=0.0, step=0.1, key=f"fiber_{fk}")

        meal_save = meal

    else:  # 消費
        activity = st.selectbox("🏋️ 活動", ACTIVITY_TYPES, key=f"act_{fk}")
        meal_save = activity
        food_name = st.text_input("📝 活動メモ（任意）",
                                   placeholder="例: 公園で実施", key=f"memo_{fk}")
        if not food_name:
            food_name = activity
        kcal  = st.number_input("🔥 カロリー (kcal)",
                                 min_value=0, value=ACTIVITY_KCAL.get(activity, 0),
                                 step=10, key=f"kcal2_{fk}")
        p_val = f_val = c_val = fi_val = 0.0

    st.divider()

    if st.button("✨ 保存する", use_container_width=True, type="primary", key=f"save_{fk}"):
        if kind_val == "摂取" and not food_name:
            st.error("食べ物名を入力してください。")
        elif kcal <= 0:
            st.error("カロリーを入力してください。")
        else:
            new_row = pd.DataFrame([{
                "日付":           str(entry_date),
                "種別":           kind_val,
                "食事":           meal_save,
                "食べ物":         food_name,
                "カロリー(kcal)": str(kcal),
                "タンパク質(g)":  str(p_val),
                "脂質(g)":        str(f_val),
                "炭水化物(g)":    str(c_val),
                "食物繊維(g)":    str(fi_val),
            }])
            updated = pd.concat([df, new_row], ignore_index=True)
            save_df(updated)
            st.session_state.df   = updated
            st.session_state.just_saved = True
            st.session_state.form_key  += 1  # フォームをリセット
            st.rerun()


# ── メインエリア ──────────────────────────────────────────────────────────────
st.markdown('<p class="gradient-title">🌸 Calolie</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">あなたの毎日をキレイに記録 ✨</p>', unsafe_allow_html=True)
st.write("")

tab_balance, tab_log, tab_nutr, tab_graph = st.tabs(
    ["📊 今日の収支", "📋 記録一覧", "🧬 栄養素", "📈 グラフ"])


# ── Tab 1: 収支 ───────────────────────────────────────────────────────────────
with tab_balance:
    all_dates = sorted(df["日付"].unique(), reverse=True)
    today_str = str(_date.today())

    c1, c2 = st.columns([2, 1])
    with c1:
        if all_dates:
            def_i = all_dates.index(today_str) if today_str in all_dates else 0
            sel_date = st.selectbox("📅 日付", all_dates, index=def_i)
        else:
            sel_date = today_str
            st.info("まだ記録がありません。サイドバーから追加してください 🌸")

    day_df = df[df["日付"] == sel_date].copy()
    day_df["カロリー(kcal)"] = pd.to_numeric(day_df["カロリー(kcal)"], errors="coerce").fillna(0)

    intake_k   = day_df[day_df["種別"] == "摂取"]["カロリー(kcal)"].sum()
    exercise_k = day_df[day_df["種別"] == "消費"]["カロリー(kcal)"].sum()
    consume_k  = BMR_KCAL + exercise_k
    balance    = intake_k - consume_k

    m1, m2, m3 = st.columns(3)
    m1.metric("🍽️ 摂取", f"{intake_k:,.0f} kcal")
    m2.metric("🏃 消費", f"{consume_k:,.0f} kcal",
              f"基礎代謝 {BMR_KCAL:,} + 運動 {exercise_k:,.0f}")
    sign = "+" if balance >= 0 else ""
    m3.metric("⚖️ 収支", f"{sign}{balance:,.0f} kcal")

    st.write("")
    if balance > 200:
        st.warning(f"📢 本日は **{balance:,.0f} kcal** オーバーです。少し動きましょう！")
    elif balance > 0:
        st.info(f"🔸 本日は **{balance:,.0f} kcal** プラスです。")
    elif balance < -200:
        st.success(f"🎉 本日は **{abs(balance):,.0f} kcal** しっかり消費できています！")
    else:
        st.success(f"✨ 本日の収支はほぼゼロです！バランス◎")


# ── Tab 2: 記録一覧 + 編集・削除 ─────────────────────────────────────────────
with tab_log:
    col_l, col_r = st.columns([3, 1])
    with col_r:
        sort_asc = st.selectbox("ソート", ["新しい順 ↓", "古い順 ↑"],
                                 label_visibility="collapsed") == "古い順 ↑"

    disp = df.copy()
    disp["カロリー(kcal)"] = pd.to_numeric(disp["カロリー(kcal)"], errors="coerce")
    disp = disp.sort_values("日付", ascending=sort_asc).reset_index(drop=True)

    st.subheader("🍽️ 摂取")
    in_df = disp[disp["種別"] == "摂取"][
        ["日付", "食事", "食べ物", "カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)"]
    ].reset_index(drop=True)
    if in_df.empty:
        st.caption("記録なし")
    else:
        st.dataframe(in_df, use_container_width=True, hide_index=True)

    st.subheader("🏃 消費")
    ex_df = disp[disp["種別"] == "消費"][
        ["日付", "食事", "食べ物", "カロリー(kcal)"]
    ].rename(columns={"食事": "活動", "食べ物": "メモ"}).reset_index(drop=True)
    if ex_df.empty:
        st.caption("記録なし")
    else:
        st.dataframe(ex_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── 編集 ──────────────────────────────────────────────────────────────────
    with st.expander("✏️ 記録を編集する"):
        if df.empty:
            st.caption("記録がありません。")
        else:
            edit_kind = st.radio("種別", ["摂取", "消費"], horizontal=True, key="edit_kind_sel")
            edit_rows = df[df["種別"] == edit_kind].reset_index()
            if edit_rows.empty:
                st.caption("該当する記録がありません。")
            else:
                opts = [f"{r['日付']} | {r['食べ物']} ({r['カロリー(kcal)']} kcal)"
                        for _, r in edit_rows.iterrows()]
                sel_i = st.selectbox("編集する行", range(len(opts)),
                                      format_func=lambda i: opts[i], key="edit_row_sel")
                orig_idx = edit_rows.iloc[sel_i]["index"]
                row      = df.loc[orig_idx]

                with st.form("edit_form"):
                    e_date  = st.text_input("日付",           value=row["日付"])
                    e_meal  = st.text_input("食事/活動",      value=row["食事"])
                    e_food  = st.text_input("食べ物/メモ",    value=row["食べ物"])
                    e_kcal  = st.number_input("カロリー (kcal)",
                                              value=float(row["カロリー(kcal)"]) if row["カロリー(kcal)"] else 0.0,
                                              min_value=0.0, step=1.0)
                    if edit_kind == "摂取":
                        e_prot = st.number_input("タンパク質 (g)",
                                                  value=float(row.get("タンパク質(g)", 0) or 0),
                                                  min_value=0.0, step=0.1)
                        e_fat  = st.number_input("脂質 (g)",
                                                  value=float(row.get("脂質(g)", 0) or 0),
                                                  min_value=0.0, step=0.1)
                        e_carb = st.number_input("炭水化物 (g)",
                                                  value=float(row.get("炭水化物(g)", 0) or 0),
                                                  min_value=0.0, step=0.1)
                        e_fib  = st.number_input("食物繊維 (g)",
                                                  value=float(row.get("食物繊維(g)", 0) or 0),
                                                  min_value=0.0, step=0.1)
                    else:
                        e_prot = e_fat = e_carb = e_fib = 0.0

                    submitted = st.form_submit_button("💾 更新する", type="primary",
                                                       use_container_width=True)
                    if submitted:
                        df.loc[orig_idx, "日付"]           = e_date
                        df.loc[orig_idx, "食事"]           = e_meal
                        df.loc[orig_idx, "食べ物"]         = e_food
                        df.loc[orig_idx, "カロリー(kcal)"] = str(e_kcal)
                        df.loc[orig_idx, "タンパク質(g)"]  = str(e_prot)
                        df.loc[orig_idx, "脂質(g)"]        = str(e_fat)
                        df.loc[orig_idx, "炭水化物(g)"]    = str(e_carb)
                        df.loc[orig_idx, "食物繊維(g)"]    = str(e_fib)
                        save_df(df)
                        st.session_state.df = df
                        st.success("更新しました！✨")
                        st.rerun()

    # ── 削除 ──────────────────────────────────────────────────────────────────
    with st.expander("🗑️ 記録を削除する"):
        if df.empty:
            st.caption("記録がありません。")
        else:
            del_kind = st.radio("種別", ["摂取", "消費"], horizontal=True, key="del_kind_sel")
            del_rows = df[df["種別"] == del_kind].reset_index()
            if del_rows.empty:
                st.caption("該当する記録がありません。")
            else:
                del_opts = [f"{r['日付']} | {r['食べ物']} ({r['カロリー(kcal)']} kcal)"
                            for _, r in del_rows.iterrows()]
                del_i = st.selectbox("削除する行", range(len(del_opts)),
                                      format_func=lambda i: del_opts[i], key="del_sel")
                if st.button("🗑️ 削除する", type="secondary", key="del_btn"):
                    orig_idx = del_rows.iloc[del_i]["index"]
                    updated  = df.drop(index=orig_idx).reset_index(drop=True)
                    save_df(updated)
                    st.session_state.df = updated
                    st.success("削除しました。")
                    st.rerun()


# ── Tab 3: 栄養素 ─────────────────────────────────────────────────────────────
with tab_nutr:
    all_dates_n = sorted(df["日付"].unique(), reverse=True)
    if not all_dates_n:
        st.info("まだ記録がありません。サイドバーから追加してください 🌸")
    else:
        def_i2 = all_dates_n.index(today_str) if today_str in all_dates_n else 0
        sel_date_n = st.selectbox("📅 日付", all_dates_n, index=def_i2, key="nutr_date")

        nutr_df = df[(df["日付"] == sel_date_n) & (df["種別"] == "摂取")].copy()
        for col in ["カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]:
            nutr_df[col] = pd.to_numeric(nutr_df[col], errors="coerce").fillna(0)

        total_p  = nutr_df["タンパク質(g)"].sum()
        total_f  = nutr_df["脂質(g)"].sum()
        total_c  = nutr_df["炭水化物(g)"].sum()
        total_fi = nutr_df["食物繊維(g)"].sum()
        total_k  = nutr_df["カロリー(kcal)"].sum()

        # 目安（成人女性・一般的な推奨値）
        TARGET = {"protein": 50, "fat": 55, "carbs": 250, "fiber": 18}

        n1, n2, n3, n4 = st.columns(4)
        n1.metric("🥩 タンパク質", f"{total_p:.1f} g", f"目安 {TARGET['protein']} g")
        n2.metric("🧈 脂質",       f"{total_f:.1f} g", f"目安 {TARGET['fat']} g")
        n3.metric("🍚 炭水化物",   f"{total_c:.1f} g", f"目安 {TARGET['carbs']} g")
        n4.metric("🥦 食物繊維",   f"{total_fi:.1f} g", f"目安 {TARGET['fiber']} g")

        st.write("")

        def pct_bar(label, val, target, color):
            pct  = min(val / target * 100, 100) if target else 0
            flag = "✅" if 80 <= pct <= 110 else ("⚠️" if pct > 110 else "📉")
            st.markdown(
                f'<div class="nutr-row">'
                f'<span class="nutr-label">{flag} {label}</span>'
                f'<div class="nutr-bar-bg"><div class="nutr-bar" '
                f'style="width:{pct:.0f}%;background:{color};"></div></div>'
                f'<span class="nutr-val">{val:.1f} / {target} g</span>'
                f'</div>', unsafe_allow_html=True)

        pct_bar("タンパク質", total_p,  TARGET["protein"], "#FF6B9D")
        pct_bar("脂質",       total_f,  TARGET["fat"],     "#F59E0B")
        pct_bar("炭水化物",   total_c,  TARGET["carbs"],   "#60A5FA")
        pct_bar("食物繊維",   total_fi, TARGET["fiber"],   "#34D399")

        st.write("")
        st.subheader("食品別の内訳")
        if nutr_df.empty:
            st.caption("摂取記録がありません。")
        else:
            show_cols = ["食事", "食べ物", "カロリー(kcal)",
                         "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
            st.dataframe(nutr_df[show_cols].reset_index(drop=True),
                         use_container_width=True, hide_index=True)


# ── Tab 4: グラフ ─────────────────────────────────────────────────────────────
with tab_graph:
    fig = build_figure(df)
    if fig is None:
        st.info("記録がありません。サイドバーからデータを追加してください 🌸")
    else:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
