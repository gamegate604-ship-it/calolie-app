"""Calolie — スマートカロリー管理"""
import os
from datetime import date as _date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────────────────────
CSV_FILE   = "food_log.csv"
FIELDNAMES = ["日付", "種別", "食事", "食べ物", "カロリー(kcal)",
              "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
BMR_KCAL   = 1630

MEAL_TIMES     = ["朝", "昼", "夜", "間食"]
ACTIVITY_TYPES = ["ランニング20分", "フットサル1時間", "エルゴ2000m", "自重筋トレ20分", "ヨガ20分"]
ACTIVITY_KCAL  = {
    "ランニング20分": 200, "フットサル1時間": 600,
    "エルゴ2000m": 120,   "自重筋トレ20分": 100, "ヨガ20分": 60,
}

# 栄養素データ — 日本食品標準成分表ベース（1人前あたり）
# keys: kcal, protein(g), fat(g), carbs(g), fiber(g)
NUTRITION: dict[str, dict[str, float]] = {
    # ── 穀物・主食 ──
    "ご飯(1杯160g)":          {"kcal": 269, "protein":  4.1, "fat":  0.5, "carbs": 59.4, "fiber": 0.5},
    "おにぎり(1個100g)":      {"kcal": 179, "protein":  3.0, "fat":  0.5, "carbs": 39.8, "fiber": 0.4},
    "食パン(1枚60g)":         {"kcal": 158, "protein":  5.3, "fat":  2.5, "carbs": 28.6, "fiber": 1.3},
    "グラノーラ(50g)":        {"kcal": 224, "protein":  4.7, "fat":  7.2, "carbs": 34.4, "fiber": 3.1},
    "オートミール(30g)":      {"kcal": 114, "protein":  3.8, "fat":  1.8, "carbs": 20.6, "fiber": 2.7},
    "パスタ(1人前)":          {"kcal": 432, "protein": 14.0, "fat":  8.0, "carbs": 76.5, "fiber": 3.0},
    "うどん(1玉260g)":        {"kcal": 261, "protein":  7.8, "fat":  1.0, "carbs": 54.3, "fiber": 2.1},
    "そば(1人前200g)":        {"kcal": 264, "protein":  9.6, "fat":  1.6, "carbs": 51.2, "fiber": 3.2},
    "ラーメン(1杯)":          {"kcal": 489, "protein": 17.0, "fat": 18.0, "carbs": 66.0, "fiber": 2.0},
    # ── 定食・丼・弁当 ──
    "定食(標準)":             {"kcal": 650, "protein": 28.0, "fat": 18.0, "carbs": 82.0, "fiber": 4.0},
    "カレー(1人前)":          {"kcal": 556, "protein": 16.6, "fat": 22.0, "carbs": 72.0, "fiber": 3.9},
    "親子丼":                 {"kcal": 565, "protein": 24.5, "fat": 15.5, "carbs": 79.5, "fiber": 1.5},
    "コンビニ弁当":           {"kcal": 540, "protein": 18.0, "fat": 16.0, "carbs": 78.0, "fiber": 3.0},
    "サンドイッチ(1個)":      {"kcal": 280, "protein": 11.0, "fat": 11.0, "carbs": 35.0, "fiber": 2.0},
    "ハンバーガー(1個)":      {"kcal": 395, "protein": 17.3, "fat": 18.0, "carbs": 42.0, "fiber": 1.5},
    "アボカドトースト":        {"kcal": 380, "protein":  9.0, "fat": 20.0, "carbs": 38.0, "fiber": 7.0},
    "パンケーキ(2枚)":        {"kcal": 320, "protein":  9.0, "fat": 12.0, "carbs": 46.0, "fiber": 1.5},
    # ── たんぱく質・おかず ──
    "チキン胸肉(100g)":       {"kcal": 116, "protein": 23.3, "fat":  1.9, "carbs":  0.0, "fiber": 0.0},
    "鮭の塩焼き(100g)":       {"kcal": 139, "protein": 22.3, "fat":  5.8, "carbs":  0.1, "fiber": 0.0},
    "豚の生姜焼き":           {"kcal": 380, "protein": 22.0, "fat": 22.0, "carbs": 15.0, "fiber": 0.5},
    "牛ステーキ(150g)":       {"kcal": 393, "protein": 30.5, "fat": 30.0, "carbs":  0.5, "fiber": 0.0},
    "唐揚げ(3個100g)":        {"kcal": 307, "protein": 18.7, "fat": 21.0, "carbs": 11.5, "fiber": 0.3},
    "卵(Mサイズ1個)":         {"kcal":  76, "protein":  6.2, "fat":  5.2, "carbs":  0.2, "fiber": 0.0},
    "豆腐(絹150g)":           {"kcal":  80, "protein":  7.4, "fat":  4.2, "carbs":  2.1, "fiber": 0.2},
    # ── サラダ・汁物 ──
    "サラダ(150g)":           {"kcal":  75, "protein":  2.5, "fat":  4.2, "carbs":  7.5, "fiber": 2.8},
    "味噌汁(1杯)":            {"kcal":  42, "protein":  3.0, "fat":  1.5, "carbs":  4.8, "fiber": 1.2},
    # ── 乳製品・卵 ──
    "牛乳(200ml)":            {"kcal": 134, "protein":  6.6, "fat":  7.6, "carbs":  9.6, "fiber": 0.0},
    "ヨーグルト無糖(100g)":   {"kcal":  62, "protein":  3.6, "fat":  3.0, "carbs":  4.9, "fiber": 0.0},
    "チーズ(1枚18g)":         {"kcal":  62, "protein":  4.1, "fat":  4.9, "carbs":  0.2, "fiber": 0.0},
    # ── フルーツ ──
    "バナナ(1本100g)":        {"kcal":  86, "protein":  1.1, "fat":  0.2, "carbs": 22.5, "fiber": 1.1},
    "りんご(1/2個100g)":      {"kcal":  61, "protein":  0.2, "fat":  0.2, "carbs": 16.2, "fiber": 1.9},
    "みかん(2個150g)":        {"kcal":  71, "protein":  0.9, "fat":  0.2, "carbs": 17.9, "fiber": 1.5},
    "いちご(10粒150g)":       {"kcal":  51, "protein":  1.4, "fat":  0.2, "carbs": 12.8, "fiber": 1.7},
    "アボカド(1/2個70g)":     {"kcal": 115, "protein":  1.5, "fat": 11.6, "carbs":  4.1, "fiber": 4.1},
    "フルーツ盛り(150g)":     {"kcal":  87, "protein":  0.8, "fat":  0.2, "carbs": 21.5, "fiber": 1.8},
    # ── スイーツ・スナック ──
    "チョコレート(25g)":      {"kcal": 136, "protein":  1.7, "fat":  8.5, "carbs": 14.5, "fiber": 0.9},
    "アイスクリーム(100ml)":  {"kcal": 180, "protein":  3.5, "fat":  8.0, "carbs": 24.0, "fiber": 0.0},
    "プロテインバー(40g)":    {"kcal": 160, "protein": 10.0, "fat":  6.0, "carbs": 18.0, "fiber": 2.0},
    # ── ドリンク ──
    "プロテイン(30g)":        {"kcal": 119, "protein": 22.5, "fat":  2.0, "carbs":  4.5, "fiber": 0.5},
    "スムージー(200ml)":      {"kcal": 140, "protein":  3.0, "fat":  1.2, "carbs": 31.0, "fiber": 3.5},
    "オレンジジュース(200ml)":{"kcal":  84, "protein":  0.8, "fat":  0.2, "carbs": 20.0, "fiber": 0.4},
    "牛乳コーヒー(200ml)":    {"kcal":  90, "protein":  3.2, "fat":  3.0, "carbs": 12.0, "fiber": 0.0},
    "コーヒー(200ml)":        {"kcal":   8, "protein":  0.4, "fat":  0.0, "carbs":  1.1, "fiber": 0.0},
    "緑茶・紅茶(200ml)":      {"kcal":   4, "protein":  0.2, "fat":  0.0, "carbs":  0.8, "fiber": 0.0},
}
FOOD_OPTIONS = sorted(NUTRITION.keys())

# グラフパレット
GP = dict(
    bg="#F0FDF4", panel="#FFFFFF", grid="#D1FAE5",
    text="#111827", dim="#6B7280", head="#059669",
    intake="#059669", consume="#7C3AED",
    pos="#EF4444", neg="#059669", border="#A7F3D0",
)


# ─────────────────────────────────────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────────────────────────────────────
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
    if df["種別"].eq("").all():
        df["種別"] = "摂取"
    return df[FIELDNAMES]


def save_df(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False, encoding="utf-8")


def _nutr(food: str) -> dict:
    n = NUTRITION.get(food, {})
    return {"protein": n.get("protein", 0.0), "fat": n.get("fat", 0.0),
            "carbs":   n.get("carbs",   0.0), "fiber": n.get("fiber", 0.0)}


# ─────────────────────────────────────────────────────────────────────────────
# グラフ
# ─────────────────────────────────────────────────────────────────────────────
def build_figure(df: pd.DataFrame):
    p = GP
    i_rows = df[df["種別"] == "摂取"].copy()
    e_rows = df[df["種別"] == "消費"].copy()
    for d in [i_rows, e_rows]:
        d["カロリー(kcal)"] = pd.to_numeric(d["カロリー(kcal)"], errors="coerce").fillna(0)

    i_by = i_rows.groupby("日付")["カロリー(kcal)"].sum()
    e_by = e_rows.groupby("日付")["カロリー(kcal)"].sum()
    dates = sorted(set(i_by.index) | set(e_by.index))
    if not dates:
        return None

    iv  = [i_by.get(d, 0) for d in dates]
    ev  = [e_by.get(d, 0) for d in dates]
    cv  = [BMR_KCAL + e   for e in ev]
    bv  = [i - c          for i, c in zip(iv, cv)]

    x, w = np.arange(len(dates)), 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(dates) * 1.4), 5), facecolor=p["bg"])
    ax.set_facecolor(p["panel"])

    bars_i = ax.bar(x - w/2, iv, width=w, color=p["intake"],  label="摂取",       zorder=3, alpha=0.85)
    bars_c = ax.bar(x + w/2, cv, width=w, color=p["consume"], label="消費(BMR+運動)", zorder=3, alpha=0.85)

    for i, (a, b, c2) in enumerate(zip(iv, cv, bv)):
        top   = max(a, b)
        color = p["pos"] if c2 >= 0 else p["neg"]
        ax.text(x[i], top + 20, f"{'+'if c2>=0 else''}{c2:.0f}",
                ha="center", va="bottom", fontsize=9, color=color, fontweight="bold", zorder=4)

    for bar in [*bars_i, *bars_c]:
        h = bar.get_height()
        if h > 60:
            ax.text(bar.get_x() + bar.get_width()/2, h/2,
                    f"{h:.0f}", ha="center", va="center",
                    fontsize=8, color="#FFFFFF", fontweight="bold", zorder=5)

    ax.axhline(BMR_KCAL, color=p["dim"], lw=1.2, ls="--", zorder=2,
               label=f"基礎代謝 {BMR_KCAL} kcal")
    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=30, ha="right", color=p["text"], fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=p["text"])
    ax.tick_params(colors=p["dim"])
    ax.set_ylabel("kcal", color=p["dim"], fontsize=10)
    ax.spines[:].set_color(p["border"])
    ax.grid(axis="y", color=p["grid"], lw=0.8, zorder=1)
    ax.set_title("カロリー収支", color=p["head"], fontsize=14, pad=14, fontweight="bold")
    ax.legend(facecolor=p["panel"], edgecolor=p["border"], labelcolor=p["text"], fontsize=9)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Calolie", page_icon="🌿",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
/* ─ フォント ─ */
html, body, [class*="css"] {
    font-family: 'Hiragino Sans', 'Noto Sans JP', 'Yu Gothic', sans-serif;
}

/* ─ グラデーションタイトル ─ */
.grad-title {
    background: linear-gradient(135deg, #059669 0%, #7C3AED 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: 0.03em;
    line-height: 1.2;
}
.caption { color: #6B7280; font-size: 0.82rem; margin-top: 2px; }

/* ─ カード ─ */
.card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 1px 8px rgba(5,150,105,0.10);
    border: 1px solid #D1FAE5;
    margin-bottom: 12px;
}

/* ─ バッジ ─ */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 50px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.badge-green  { background:#D1FAE5; color:#065F46; }
.badge-purple { background:#EDE9FE; color:#5B21B6; }
.badge-red    { background:#FEE2E2; color:#991B1B; }
.badge-amber  { background:#FEF3C7; color:#92400E; }

/* ─ メトリクス ─ */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 16px !important;
    box-shadow: 0 1px 8px rgba(5,150,105,0.08);
    border: 1px solid #D1FAE5;
}

/* ─ ボタン ─ */
.stButton > button {
    border-radius: 50px !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(5,150,105,0.25) !important;
}

/* ─ サイドバー ─ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ECFDF5 0%, #EEF2FF 100%);
    border-right: 1px solid #D1FAE5;
}

/* ─ 入力欄 ─ */
[data-baseweb="input"] {
    border-radius: 12px !important;
}

/* ─ 保存済みバナー ─ */
.saved-banner {
    background: linear-gradient(90deg, #D1FAE5, #EDE9FE);
    border-radius: 12px;
    padding: 10px 16px;
    text-align: center;
    font-weight: 700;
    color: #065F46;
    margin-bottom: 10px;
    font-size: 0.9rem;
}

/* ─ 栄養バー ─ */
.n-row  { display:flex; align-items:center; gap:8px; margin:5px 0; }
.n-lbl  { width:80px; font-size:0.78rem; color:#6B7280; font-weight:600; }
.n-bg   { flex:1; background:#F3F4F6; border-radius:8px; height:8px; overflow:hidden; }
.n-fill { height:8px; border-radius:8px; transition:width 0.4s; }
.n-val  { width:72px; font-size:0.78rem; color:#374151; text-align:right; }

/* ─ タブ ─ */
.stTabs [data-baseweb="tab-list"] { gap:4px; }
.stTabs [data-baseweb="tab"]      { border-radius:50px; padding:6px 18px; font-weight:600; }

/* ─ テーブル ─ */
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }

/* ─ セクション見出し ─ */
.sec-head {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6B7280;
    margin: 16px 0 6px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session State 初期化 & コールバック
# ─────────────────────────────────────────────────────────────────────────────
_FIRST_FOOD = FOOD_OPTIONS[0]

_INIT: dict = {
    "df":          None,
    "ss_kind":     "摂取",
    "ss_date":     _date.today(),
    "ss_meal":     MEAL_TIMES[0],
    "ss_food":     _FIRST_FOOD,
    "ss_custom":   "",
    "ss_kcal":     NUTRITION[_FIRST_FOOD]["kcal"],
    "ss_nutr":     _nutr(_FIRST_FOOD),
    "ss_activity": ACTIVITY_TYPES[0],
    "ss_memo":     "",
    "ss_saved":    False,
}
for _k, _v in _INIT.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.df is None:
    st.session_state.df = load_df()


def _on_food():
    food = st.session_state.ss_food
    if food in NUTRITION:
        st.session_state.ss_kcal = NUTRITION[food]["kcal"]
        st.session_state.ss_nutr = _nutr(food)
    else:
        st.session_state.ss_kcal = 0
        st.session_state.ss_nutr = _nutr("")


def _on_kcal():
    kcal = st.session_state.ss_kcal or 0
    food = st.session_state.ss_food
    if food in NUTRITION and NUTRITION[food]["kcal"] > 0:
        r = kcal / NUTRITION[food]["kcal"]
        base = NUTRITION[food]
        st.session_state.ss_nutr = {
            "protein": round(base["protein"] * r, 1),
            "fat":     round(base["fat"]     * r, 1),
            "carbs":   round(base["carbs"]   * r, 1),
            "fiber":   round(base["fiber"]   * r, 1),
        }


def _on_activity():
    st.session_state.ss_kcal = ACTIVITY_KCAL.get(st.session_state.ss_activity, 0)


def _reset_form():
    st.session_state.ss_kind     = "摂取"
    st.session_state.ss_date     = _date.today()
    st.session_state.ss_meal     = MEAL_TIMES[0]
    st.session_state.ss_food     = _FIRST_FOOD
    st.session_state.ss_custom   = ""
    st.session_state.ss_kcal     = NUTRITION[_FIRST_FOOD]["kcal"]
    st.session_state.ss_nutr     = _nutr(_FIRST_FOOD)
    st.session_state.ss_activity = ACTIVITY_TYPES[0]
    st.session_state.ss_memo     = ""
    st.session_state.ss_saved    = True


df = st.session_state.df


# ─────────────────────────────────────────────────────────────────────────────
# サイドバー（入力フォーム）
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="grad-title">🌿 Calolie</p>', unsafe_allow_html=True)
    st.markdown('<p class="caption">毎日の食事・運動を記録して、なりたい自分へ ✨</p>',
                unsafe_allow_html=True)
    st.divider()

    if st.session_state.ss_saved:
        st.markdown('<div class="saved-banner">✅ 保存しました！</div>',
                    unsafe_allow_html=True)
        st.session_state.ss_saved = False

    # ── 種別 ──
    kind = st.radio("種別", ["🍽️ 食事（摂取）", "🏃 運動（消費）"],
                    horizontal=True, key="ss_kind_radio")
    kind_val = "摂取" if "摂取" in kind else "消費"

    # ── 日付 ──
    st.date_input("📅 日付", key="ss_date", format="YYYY-MM-DD")

    # ─────────────────────────────────────────────────────────────────────────
    if kind_val == "摂取":
        st.selectbox("🕐 タイミング", MEAL_TIMES, key="ss_meal")

        st.markdown('<p class="sec-head">食べ物を選択</p>', unsafe_allow_html=True)
        food_choice = st.selectbox(
            "食べ物", FOOD_OPTIONS + ["✏️ その他を入力…"],
            key="ss_food", on_change=_on_food, label_visibility="collapsed",
        )

        if food_choice == "✏️ その他を入力…":
            st.text_input("食べ物名", placeholder="例: タピオカ 🧋", key="ss_custom")
            st.number_input("カロリー (kcal)", min_value=0, step=5,
                             key="ss_kcal", on_change=_on_kcal)
            nutr = st.session_state.ss_nutr
            st.markdown('<p class="sec-head">栄養素（手動入力）</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                np_v = st.number_input("タンパク質 g", value=nutr["protein"],
                                        min_value=0.0, step=0.1, key="ss_np")
                nc_v = st.number_input("炭水化物 g", value=nutr["carbs"],
                                        min_value=0.0, step=0.1, key="ss_nc")
            with c2:
                nf_v = st.number_input("脂質 g", value=nutr["fat"],
                                        min_value=0.0, step=0.1, key="ss_nf")
                nfi_v = st.number_input("食物繊維 g", value=nutr["fiber"],
                                         min_value=0.0, step=0.1, key="ss_nfi")
        else:
            # 既知食品 — kcal変更で栄養素も連動
            st.number_input("🔥 カロリー (kcal)", min_value=0, step=5,
                             key="ss_kcal", on_change=_on_kcal)
            nutr = st.session_state.ss_nutr

            st.markdown('<p class="sec-head">推定栄養素（kcalに連動）</p>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("🥩 タンパク質", f"{nutr['protein']} g")
            c2.metric("🧈 脂質",       f"{nutr['fat']} g")
            c3, c4 = st.columns(2)
            c3.metric("🍚 炭水化物",   f"{nutr['carbs']} g")
            c4.metric("🥦 食物繊維",   f"{nutr['fiber']} g")

            np_v  = nutr["protein"]
            nf_v  = nutr["fat"]
            nc_v  = nutr["carbs"]
            nfi_v = nutr["fiber"]

        meal_save = st.session_state.ss_meal
        food_save = (st.session_state.ss_custom
                     if food_choice == "✏️ その他を入力…"
                     else food_choice)

    else:  # 消費
        st.selectbox("🏋️ 活動", ACTIVITY_TYPES, key="ss_activity", on_change=_on_activity)
        st.text_input("📝 メモ（任意）", placeholder="公園で実施など", key="ss_memo")
        st.number_input("🔥 カロリー (kcal)", min_value=0, step=5, key="ss_kcal")
        meal_save = st.session_state.ss_activity
        food_save = st.session_state.ss_memo or st.session_state.ss_activity
        np_v = nf_v = nc_v = nfi_v = 0.0

    st.divider()

    if st.button("✨ 保存する", use_container_width=True, type="primary"):
        _err = None
        if kind_val == "摂取" and not food_save:
            _err = "食べ物名を入力してください。"
        elif (st.session_state.ss_kcal or 0) <= 0:
            _err = "カロリーを入力してください。"
        if _err:
            st.error(_err)
        else:
            new_row = pd.DataFrame([{
                "日付":           str(st.session_state.ss_date),
                "種別":           kind_val,
                "食事":           meal_save,
                "食べ物":         food_save,
                "カロリー(kcal)": str(st.session_state.ss_kcal),
                "タンパク質(g)":  str(np_v),
                "脂質(g)":        str(nf_v),
                "炭水化物(g)":    str(nc_v),
                "食物繊維(g)":    str(nfi_v),
            }])
            updated = pd.concat([df, new_row], ignore_index=True)
            save_df(updated)
            st.session_state.df = updated
            df = updated
            _reset_form()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# メインエリア
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="grad-title">🌿 Calolie</p>', unsafe_allow_html=True)
st.markdown('<p class="caption">食事・運動・栄養をまとめて管理 — なりたい自分をデザインしよう ✨</p>',
            unsafe_allow_html=True)
st.write("")

tab_bal, tab_log, tab_nutr, tab_graph = st.tabs(
    ["📊 収支", "📝 記録・編集", "🧬 栄養素", "📈 グラフ"])


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: 収支
# ─────────────────────────────────────────────────────────────────────────────
with tab_bal:
    all_dates = sorted(df["日付"].unique(), reverse=True)
    today_str = str(_date.today())

    if not all_dates:
        st.info("まだ記録がありません。サイドバーから追加してください 🌿")
    else:
        def_i = all_dates.index(today_str) if today_str in all_dates else 0
        sel = st.selectbox("📅 日付", all_dates, index=def_i, key="bal_date")

        day = df[df["日付"] == sel].copy()
        day["カロリー(kcal)"] = pd.to_numeric(day["カロリー(kcal)"], errors="coerce").fillna(0)

        intake_k   = day[day["種別"] == "摂取"]["カロリー(kcal)"].sum()
        exercise_k = day[day["種別"] == "消費"]["カロリー(kcal)"].sum()
        consume_k  = BMR_KCAL + exercise_k
        balance    = intake_k - consume_k
        sign       = "+" if balance >= 0 else ""

        m1, m2, m3 = st.columns(3)
        m1.metric("🍽️ 摂取カロリー",  f"{intake_k:,.0f} kcal")
        m2.metric("🔥 消費カロリー",   f"{consume_k:,.0f} kcal",
                  f"基礎代謝 {BMR_KCAL:,} + 運動 {exercise_k:,.0f}")
        m3.metric("⚖️ 今日の収支",    f"{sign}{balance:,.0f} kcal")

        st.write("")
        if balance > 300:
            st.warning(f"📢 **{balance:,.0f} kcal** オーバー。少し体を動かしてみましょう！")
        elif balance > 0:
            st.info(f"🔸 **{balance:,.0f} kcal** プラスです。")
        elif balance < -300:
            st.success(f"🎉 **{abs(balance):,.0f} kcal** しっかり消費！今日もよく頑張りました ✨")
        else:
            st.success("✨ 収支はほぼゼロ。理想的なバランスです！")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2: 記録・編集
# ─────────────────────────────────────────────────────────────────────────────
with tab_log:
    if df.empty:
        st.info("まだ記録がありません。サイドバーから追加してください 🌿")
    else:
        c1, c2 = st.columns([3, 1])
        with c2:
            asc = st.selectbox("並び順", ["新しい順", "古い順"],
                               label_visibility="collapsed") == "古い順"

        # ── 摂取 ──────────────────────────────────────────────────────────────
        st.markdown('<p class="sec-head">🍽️ 摂取記録</p>', unsafe_allow_html=True)

        intake_full = (df[df["種別"] == "摂取"]
                       .copy()
                       .sort_values("日付", ascending=asc)
                       .reset_index(drop=True))
        numeric_cols = ["カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
        for c in numeric_cols:
            intake_full[c] = pd.to_numeric(intake_full[c], errors="coerce").fillna(0)

        if intake_full.empty:
            st.caption("記録なし")
        else:
            edit_cols_in = ["日付", "食事", "食べ物", "カロリー(kcal)",
                            "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
            with st.form("form_edit_intake"):
                edited_in = st.data_editor(
                    intake_full[edit_cols_in],
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    column_config={
                        "カロリー(kcal)": st.column_config.NumberColumn("kcal",     format="%g"),
                        "タンパク質(g)":  st.column_config.NumberColumn("PFC: P(g)", format="%.1f"),
                        "脂質(g)":        st.column_config.NumberColumn("F(g)",     format="%.1f"),
                        "炭水化物(g)":    st.column_config.NumberColumn("C(g)",     format="%.1f"),
                        "食物繊維(g)":    st.column_config.NumberColumn("繊維(g)",  format="%.1f"),
                    },
                )
                if st.form_submit_button("💾 摂取記録を保存", type="primary",
                                          use_container_width=True):
                    # 摂取行のみ入れ替え
                    intake_idx = df[df["種別"] == "摂取"].index
                    sorted_idx = (df[df["種別"] == "摂取"]
                                  .sort_values("日付", ascending=asc).index)
                    for i, orig_i in enumerate(sorted_idx):
                        if i < len(edited_in):
                            for col in edit_cols_in:
                                df.loc[orig_i, col] = str(edited_in.iloc[i][col])
                    save_df(df)
                    st.session_state.df = df
                    st.success("摂取記録を更新しました ✨")
                    st.rerun()

        # ── 消費 ──────────────────────────────────────────────────────────────
        st.markdown('<p class="sec-head">🏃 運動記録</p>', unsafe_allow_html=True)

        expense_full = (df[df["種別"] == "消費"]
                        .copy()
                        .sort_values("日付", ascending=asc)
                        .reset_index(drop=True))
        expense_full["カロリー(kcal)"] = pd.to_numeric(
            expense_full["カロリー(kcal)"], errors="coerce").fillna(0)

        if expense_full.empty:
            st.caption("記録なし")
        else:
            edit_cols_ex = ["日付", "食事", "食べ物", "カロリー(kcal)"]
            with st.form("form_edit_expense"):
                edited_ex = st.data_editor(
                    expense_full[edit_cols_ex].rename(
                        columns={"食事": "活動", "食べ物": "メモ"}),
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    column_config={
                        "カロリー(kcal)": st.column_config.NumberColumn("kcal", format="%g"),
                    },
                )
                if st.form_submit_button("💾 運動記録を保存", type="primary",
                                          use_container_width=True):
                    sorted_idx_ex = (df[df["種別"] == "消費"]
                                     .sort_values("日付", ascending=asc).index)
                    edited_ex2 = edited_ex.rename(
                        columns={"活動": "食事", "メモ": "食べ物"})
                    for i, orig_i in enumerate(sorted_idx_ex):
                        if i < len(edited_ex2):
                            for col in edit_cols_ex:
                                df.loc[orig_i, col] = str(edited_ex2.iloc[i][col])
                    save_df(df)
                    st.session_state.df = df
                    st.success("運動記録を更新しました ✨")
                    st.rerun()

        # ── 削除 ──────────────────────────────────────────────────────────────
        with st.expander("🗑️ 行を削除する"):
            del_kind = st.radio("種別", ["摂取", "消費"], horizontal=True, key="del_k")
            del_rows = df[df["種別"] == del_kind].reset_index()
            if del_rows.empty:
                st.caption("該当なし")
            else:
                opts = [f"{r['日付']} ｜ {r['食べ物']} ({r['カロリー(kcal)']} kcal)"
                        for _, r in del_rows.iterrows()]
                di = st.selectbox("削除する行", range(len(opts)),
                                   format_func=lambda i: opts[i], key="del_sel")
                if st.button("削除する", type="secondary"):
                    updated = df.drop(index=del_rows.iloc[di]["index"]).reset_index(drop=True)
                    save_df(updated)
                    st.session_state.df = updated
                    st.success("削除しました。")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: 栄養素
# ─────────────────────────────────────────────────────────────────────────────
with tab_nutr:
    all_dn = sorted(df["日付"].unique(), reverse=True)
    if not all_dn:
        st.info("まだ記録がありません 🌿")
    else:
        def_i2 = all_dn.index(today_str) if today_str in all_dn else 0
        sel_n = st.selectbox("📅 日付", all_dn, index=def_i2, key="nutr_d")

        nd = df[(df["日付"] == sel_n) & (df["種別"] == "摂取")].copy()
        for c in ["カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]:
            nd[c] = pd.to_numeric(nd[c], errors="coerce").fillna(0)

        tp = nd["タンパク質(g)"].sum()
        tf = nd["脂質(g)"].sum()
        tc = nd["炭水化物(g)"].sum()
        tfi = nd["食物繊維(g)"].sum()

        # 目安値（成人女性・運動習慣あり）
        TGT = {"protein": 60, "fat": 50, "carbs": 230, "fiber": 18}

        n1, n2, n3, n4 = st.columns(4)
        n1.metric("🥩 タンパク質", f"{tp:.1f} g",   f"目安 {TGT['protein']} g")
        n2.metric("🧈 脂質",       f"{tf:.1f} g",   f"目安 {TGT['fat']} g")
        n3.metric("🍚 炭水化物",   f"{tc:.1f} g",   f"目安 {TGT['carbs']} g")
        n4.metric("🥦 食物繊維",   f"{tfi:.1f} g",  f"目安 {TGT['fiber']} g")

        st.write("")

        def pbar(label, val, tgt, color, icon):
            pct = min(val / tgt * 100, 105) if tgt else 0
            flag = ("✅" if 75 <= pct <= 105
                    else ("⚠️ 摂りすぎ" if pct > 105 else "📉 不足気味"))
            st.markdown(
                f'<div class="n-row">'
                f'<span class="n-lbl">{icon} {label}</span>'
                f'<div class="n-bg"><div class="n-fill" '
                f'style="width:{min(pct,100):.0f}%;background:{color};"></div></div>'
                f'<span class="n-val">{val:.1f}/{tgt}g</span>'
                f'<span style="font-size:0.7rem;color:#6B7280">{flag}</span>'
                f'</div>', unsafe_allow_html=True)

        pbar("タンパク質", tp,  TGT["protein"], "#059669", "🥩")
        pbar("脂質",       tf,  TGT["fat"],     "#F59E0B", "🧈")
        pbar("炭水化物",   tc,  TGT["carbs"],   "#6366F1", "🍚")
        pbar("食物繊維",   tfi, TGT["fiber"],   "#10B981", "🥦")

        # PFCバランス
        st.write("")
        total_macro = tp + tf + tc
        if total_macro > 0:
            pfc_p = tp / total_macro * 100
            pfc_f = tf / total_macro * 100
            pfc_c = tc / total_macro * 100
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"""
                <div class="card">
                  <div style="font-size:0.75rem;font-weight:700;color:#6B7280;letter-spacing:.08em">PFCバランス</div>
                  <div style="margin-top:8px">
                    <span class="badge badge-green">P {pfc_p:.0f}%</span>&nbsp;
                    <span class="badge badge-amber">F {pfc_f:.0f}%</span>&nbsp;
                    <span class="badge badge-purple">C {pfc_c:.0f}%</span>
                  </div>
                  <div style="font-size:0.72rem;color:#9CA3AF;margin-top:6px">
                    理想: P 15–20% / F 20–30% / C 50–60%
                  </div>
                </div>
                """, unsafe_allow_html=True)

        st.write("")
        st.markdown('<p class="sec-head">食品別の内訳</p>', unsafe_allow_html=True)
        if nd.empty:
            st.caption("摂取記録がありません。")
        else:
            sc = ["食事", "食べ物", "カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
            st.dataframe(nd[sc].reset_index(drop=True),
                         use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 4: グラフ
# ─────────────────────────────────────────────────────────────────────────────
with tab_graph:
    fig = build_figure(df)
    if fig is None:
        st.info("記録がありません。サイドバーからデータを追加してください 🌿")
    else:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
