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

# 栄養素データ（日本食品標準成分表ベース・1人前）
NUTRITION: dict[str, dict[str, float]] = {
    "ご飯(1杯160g)":          {"kcal": 269, "protein":  4.1, "fat":  0.5, "carbs": 59.4, "fiber": 0.5},
    "おにぎり(1個100g)":      {"kcal": 179, "protein":  3.0, "fat":  0.5, "carbs": 39.8, "fiber": 0.4},
    "食パン(1枚60g)":         {"kcal": 158, "protein":  5.3, "fat":  2.5, "carbs": 28.6, "fiber": 1.3},
    "グラノーラ(50g)":        {"kcal": 224, "protein":  4.7, "fat":  7.2, "carbs": 34.4, "fiber": 3.1},
    "オートミール(30g)":      {"kcal": 114, "protein":  3.8, "fat":  1.8, "carbs": 20.6, "fiber": 2.7},
    "パスタ(1人前)":          {"kcal": 432, "protein": 14.0, "fat":  8.0, "carbs": 76.5, "fiber": 3.0},
    "うどん(1玉260g)":        {"kcal": 261, "protein":  7.8, "fat":  1.0, "carbs": 54.3, "fiber": 2.1},
    "そば(1人前200g)":        {"kcal": 264, "protein":  9.6, "fat":  1.6, "carbs": 51.2, "fiber": 3.2},
    "ラーメン(1杯)":          {"kcal": 489, "protein": 17.0, "fat": 18.0, "carbs": 66.0, "fiber": 2.0},
    "定食(標準)":             {"kcal": 650, "protein": 28.0, "fat": 18.0, "carbs": 82.0, "fiber": 4.0},
    "カレー(1人前)":          {"kcal": 556, "protein": 16.6, "fat": 22.0, "carbs": 72.0, "fiber": 3.9},
    "親子丼":                 {"kcal": 565, "protein": 24.5, "fat": 15.5, "carbs": 79.5, "fiber": 1.5},
    "コンビニ弁当":           {"kcal": 540, "protein": 18.0, "fat": 16.0, "carbs": 78.0, "fiber": 3.0},
    "サンドイッチ(1個)":      {"kcal": 280, "protein": 11.0, "fat": 11.0, "carbs": 35.0, "fiber": 2.0},
    "ハンバーガー(1個)":      {"kcal": 395, "protein": 17.3, "fat": 18.0, "carbs": 42.0, "fiber": 1.5},
    "アボカドトースト":        {"kcal": 380, "protein":  9.0, "fat": 20.0, "carbs": 38.0, "fiber": 7.0},
    "パンケーキ(2枚)":        {"kcal": 320, "protein":  9.0, "fat": 12.0, "carbs": 46.0, "fiber": 1.5},
    "チキン胸肉(100g)":       {"kcal": 116, "protein": 23.3, "fat":  1.9, "carbs":  0.0, "fiber": 0.0},
    "鮭の塩焼き(100g)":       {"kcal": 139, "protein": 22.3, "fat":  5.8, "carbs":  0.1, "fiber": 0.0},
    "豚の生姜焼き":           {"kcal": 380, "protein": 22.0, "fat": 22.0, "carbs": 15.0, "fiber": 0.5},
    "牛ステーキ(150g)":       {"kcal": 393, "protein": 30.5, "fat": 30.0, "carbs":  0.5, "fiber": 0.0},
    "唐揚げ(3個100g)":        {"kcal": 307, "protein": 18.7, "fat": 21.0, "carbs": 11.5, "fiber": 0.3},
    "卵(Mサイズ1個)":         {"kcal":  76, "protein":  6.2, "fat":  5.2, "carbs":  0.2, "fiber": 0.0},
    "豆腐(絹150g)":           {"kcal":  80, "protein":  7.4, "fat":  4.2, "carbs":  2.1, "fiber": 0.2},
    "サラダ(150g)":           {"kcal":  75, "protein":  2.5, "fat":  4.2, "carbs":  7.5, "fiber": 2.8},
    "味噌汁(1杯)":            {"kcal":  42, "protein":  3.0, "fat":  1.5, "carbs":  4.8, "fiber": 1.2},
    "牛乳(200ml)":            {"kcal": 134, "protein":  6.6, "fat":  7.6, "carbs":  9.6, "fiber": 0.0},
    "ヨーグルト無糖(100g)":   {"kcal":  62, "protein":  3.6, "fat":  3.0, "carbs":  4.9, "fiber": 0.0},
    "チーズ(1枚18g)":         {"kcal":  62, "protein":  4.1, "fat":  4.9, "carbs":  0.2, "fiber": 0.0},
    "バナナ(1本100g)":        {"kcal":  86, "protein":  1.1, "fat":  0.2, "carbs": 22.5, "fiber": 1.1},
    "りんご(1/2個100g)":      {"kcal":  61, "protein":  0.2, "fat":  0.2, "carbs": 16.2, "fiber": 1.9},
    "みかん(2個150g)":        {"kcal":  71, "protein":  0.9, "fat":  0.2, "carbs": 17.9, "fiber": 1.5},
    "いちご(10粒150g)":       {"kcal":  51, "protein":  1.4, "fat":  0.2, "carbs": 12.8, "fiber": 1.7},
    "アボカド(1/2個70g)":     {"kcal": 115, "protein":  1.5, "fat": 11.6, "carbs":  4.1, "fiber": 4.1},
    "フルーツ盛り(150g)":     {"kcal":  87, "protein":  0.8, "fat":  0.2, "carbs": 21.5, "fiber": 1.8},
    "チョコレート(25g)":      {"kcal": 136, "protein":  1.7, "fat":  8.5, "carbs": 14.5, "fiber": 0.9},
    "アイスクリーム(100ml)":  {"kcal": 180, "protein":  3.5, "fat":  8.0, "carbs": 24.0, "fiber": 0.0},
    "プロテインバー(40g)":    {"kcal": 160, "protein": 10.0, "fat":  6.0, "carbs": 18.0, "fiber": 2.0},
    "プロテイン(30g)":        {"kcal": 119, "protein": 22.5, "fat":  2.0, "carbs":  4.5, "fiber": 0.5},
    "スムージー(200ml)":      {"kcal": 140, "protein":  3.0, "fat":  1.2, "carbs": 31.0, "fiber": 3.5},
    "オレンジジュース(200ml)":{"kcal":  84, "protein":  0.8, "fat":  0.2, "carbs": 20.0, "fiber": 0.4},
    "コーヒー(200ml)":        {"kcal":   8, "protein":  0.4, "fat":  0.0, "carbs":  1.1, "fiber": 0.0},
    "緑茶・紅茶(200ml)":      {"kcal":   4, "protein":  0.2, "fat":  0.0, "carbs":  0.8, "fiber": 0.0},
}
FOOD_OPTIONS = sorted(NUTRITION.keys())
_DFLT_FOOD   = "バナナ(1本100g)"
_DFLT_IDX    = FOOD_OPTIONS.index(_DFLT_FOOD)

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
    ir = df[df["種別"] == "摂取"].copy()
    er = df[df["種別"] == "消費"].copy()
    for d in [ir, er]:
        d["カロリー(kcal)"] = pd.to_numeric(d["カロリー(kcal)"], errors="coerce").fillna(0)

    ib = ir.groupby("日付")["カロリー(kcal)"].sum()
    eb = er.groupby("日付")["カロリー(kcal)"].sum()
    dates = sorted(set(ib.index) | set(eb.index))
    if not dates:
        return None

    iv = [ib.get(d, 0) for d in dates]
    ev = [eb.get(d, 0) for d in dates]
    cv = [BMR_KCAL + e for e in ev]
    bv = [i - c for i, c in zip(iv, cv)]

    x, w = np.arange(len(dates)), 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(dates) * 1.4), 5), facecolor=p["bg"])
    ax.set_facecolor(p["panel"])
    bi = ax.bar(x - w/2, iv, width=w, color=p["intake"],  label="摂取",          zorder=3, alpha=0.85)
    bc = ax.bar(x + w/2, cv, width=w, color=p["consume"], label="消費(BMR+運動)", zorder=3, alpha=0.85)

    for i, (a, b, c) in enumerate(zip(iv, cv, bv)):
        top   = max(a, b)
        color = p["pos"] if c >= 0 else p["neg"]
        ax.text(x[i], top + 20, f"{'+'if c>=0 else''}{c:.0f}",
                ha="center", va="bottom", fontsize=9, color=color, fontweight="bold", zorder=4)
    for bar in [*bi, *bc]:
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
# ページ設定 & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Calolie", page_icon="🌿",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Hiragino Sans', 'Noto Sans JP', 'Yu Gothic', sans-serif;
}
.grad-title {
    background: linear-gradient(135deg, #059669 0%, #7C3AED 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-size: 1.9rem; font-weight: 900; letter-spacing: .03em; line-height: 1.2;
}
.caption { color: #6B7280; font-size: .82rem; margin-top: 2px; }
.card {
    background: #FFFFFF; border-radius: 16px; padding: 20px 24px;
    box-shadow: 0 1px 8px rgba(5,150,105,.10); border: 1px solid #D1FAE5; margin-bottom: 12px;
}
.badge { display:inline-block; padding:3px 10px; border-radius:50px;
         font-size:.78rem; font-weight:700; letter-spacing:.04em; }
.badge-g { background:#D1FAE5; color:#065F46; }
.badge-p { background:#EDE9FE; color:#5B21B6; }
.badge-a { background:#FEF3C7; color:#92400E; }
[data-testid="metric-container"] {
    background:#FFFFFF; border-radius:16px; padding:16px !important;
    box-shadow:0 1px 8px rgba(5,150,105,.08); border:1px solid #D1FAE5;
}
.stButton > button {
    border-radius:50px !important; font-weight:700 !important;
    letter-spacing:.04em; transition:all .2s !important;
}
.stButton > button:hover { transform:translateY(-1px) !important;
    box-shadow:0 4px 16px rgba(5,150,105,.25) !important; }
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#ECFDF5 0%,#EEF2FF 100%);
    border-right:1px solid #D1FAE5;
}
.saved-banner {
    background:linear-gradient(90deg,#D1FAE5,#EDE9FE); border-radius:12px;
    padding:10px 16px; text-align:center; font-weight:700; color:#065F46;
    margin-bottom:10px; font-size:.9rem;
}
.n-row  { display:flex; align-items:center; gap:8px; margin:5px 0; }
.n-lbl  { width:80px; font-size:.78rem; color:#6B7280; font-weight:600; }
.n-bg   { flex:1; background:#F3F4F6; border-radius:8px; height:8px; overflow:hidden; }
.n-fill { height:8px; border-radius:8px; }
.n-val  { width:72px; font-size:.78rem; color:#374151; text-align:right; }
.sec-head { font-size:.75rem; font-weight:700; letter-spacing:.12em;
            text-transform:uppercase; color:#6B7280; margin:16px 0 6px; }
.stTabs [data-baseweb="tab-list"] { gap:4px; }
.stTabs [data-baseweb="tab"] { border-radius:50px; padding:6px 18px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session State（ウィジェットキー非使用の安全な初期化）
# ─────────────────────────────────────────────────────────────────────────────
for _k, _v in [("df", None), ("fv", 0), ("ss_saved", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.df is None:
    st.session_state.df = load_df()

# フォームバージョン（保存ごとにインクリメントして全ウィジェットをリセット）
fv = st.session_state.fv

# このバージョン用の非ウィジェット状態を初期化
if f"nutr_{fv}" not in st.session_state:
    st.session_state[f"nutr_{fv}"] = _nutr(_DFLT_FOOD)


# ─── コールバック（ウィジェット間の連動 — on_change から呼ばれるので安全）────────
def _on_food():
    food = st.session_state.get(f"w_food_{fv}", "")
    if food in NUTRITION:
        # 同一バージョンの別ウィジェットのキーをコールバック内で設定するのは合法
        st.session_state[f"w_kcal_{fv}"] = NUTRITION[food]["kcal"]
        st.session_state[f"nutr_{fv}"]   = _nutr(food)
    else:
        st.session_state[f"w_kcal_{fv}"] = 0
        st.session_state[f"nutr_{fv}"]   = _nutr("")


def _on_kcal():
    kcal = st.session_state.get(f"w_kcal_{fv}", 0) or 0
    food = st.session_state.get(f"w_food_{fv}", "")
    if food in NUTRITION and NUTRITION[food]["kcal"] > 0:
        r    = kcal / NUTRITION[food]["kcal"]
        base = NUTRITION[food]
        st.session_state[f"nutr_{fv}"] = {
            k: round(base[k] * r, 1) for k in ["protein", "fat", "carbs", "fiber"]
        }


def _on_activity():
    act = st.session_state.get(f"w_activity_{fv}", "")
    st.session_state[f"w_kcal_{fv}"] = ACTIVITY_KCAL.get(act, 0)


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

    # ── 種別 ──────────────────────────────────────────────────────────────────
    kind_raw  = st.radio("種別", ["🍽️ 食事（摂取）", "🏃 運動（消費）"],
                          horizontal=True, key=f"w_kind_{fv}")
    kind_val  = "摂取" if "摂取" in kind_raw else "消費"

    # ── 日付 ──────────────────────────────────────────────────────────────────
    st.date_input("📅 日付", value=_date.today(),
                   format="YYYY-MM-DD", key=f"w_date_{fv}")

    # ─────────────────────────────────────────────────────────────────────────
    if kind_val == "摂取":
        st.selectbox("🕐 タイミング", MEAL_TIMES, key=f"w_meal_{fv}")

        st.markdown('<p class="sec-head">食べ物を選択</p>', unsafe_allow_html=True)
        food_choice = st.selectbox(
            "食べ物", FOOD_OPTIONS + ["✏️ その他を入力…"],
            index=_DFLT_IDX,
            key=f"w_food_{fv}", on_change=_on_food,
            label_visibility="collapsed",
        )

        is_custom = food_choice == "✏️ その他を入力…"
        if is_custom:
            st.text_input("食べ物名", placeholder="例: タピオカ 🧋", key=f"w_custom_{fv}")

        # kcal — セッション状態に値があればそれを使う（コールバックで更新済み）
        kcal_init = (st.session_state.get(f"w_kcal_{fv}")
                     or NUTRITION.get(food_choice, {}).get("kcal", 0))
        st.number_input("🔥 カロリー (kcal)", value=int(kcal_init),
                         min_value=0, step=5,
                         key=f"w_kcal_{fv}", on_change=_on_kcal)

        # 栄養素表示（kcalに連動して自動更新）
        nutr = st.session_state[f"nutr_{fv}"]
        if is_custom:
            st.markdown('<p class="sec-head">栄養素（手動入力）</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("タンパク質 g", value=float(nutr["protein"]),
                                 min_value=0.0, step=0.1, key=f"w_np_{fv}")
                st.number_input("炭水化物 g",   value=float(nutr["carbs"]),
                                 min_value=0.0, step=0.1, key=f"w_nc_{fv}")
            with c2:
                st.number_input("脂質 g",       value=float(nutr["fat"]),
                                 min_value=0.0, step=0.1, key=f"w_nf_{fv}")
                st.number_input("食物繊維 g",   value=float(nutr["fiber"]),
                                 min_value=0.0, step=0.1, key=f"w_nfi_{fv}")
        else:
            st.markdown('<p class="sec-head">推定栄養素（kcalに連動）</p>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("🥩 タンパク質", f"{nutr['protein']} g")
            c2.metric("🧈 脂質",       f"{nutr['fat']} g")
            c3, c4 = st.columns(2)
            c3.metric("🍚 炭水化物",   f"{nutr['carbs']} g")
            c4.metric("🥦 食物繊維",   f"{nutr['fiber']} g")

    else:  # ── 消費 ────────────────────────────────────────────────────────
        st.selectbox("🏋️ 活動", ACTIVITY_TYPES,
                      key=f"w_activity_{fv}", on_change=_on_activity)
        st.text_input("📝 メモ（任意）", placeholder="公園で実施など",
                       key=f"w_memo_{fv}")
        kcal_ex = st.session_state.get(f"w_kcal_{fv}",
                  ACTIVITY_KCAL[ACTIVITY_TYPES[0]])
        st.number_input("🔥 カロリー (kcal)", value=int(kcal_ex),
                         min_value=0, step=5, key=f"w_kcal_{fv}")

    st.divider()

    # ── 保存ボタン ─────────────────────────────────────────────────────────────
    if st.button("✨ 保存する", use_container_width=True, type="primary"):
        kcal_now  = st.session_state.get(f"w_kcal_{fv}", 0) or 0
        food_sel  = st.session_state.get(f"w_food_{fv}", "")
        custom    = st.session_state.get(f"w_custom_{fv}", "")
        food_save = custom if food_sel == "✏️ その他を入力…" else food_sel
        act_sel   = st.session_state.get(f"w_activity_{fv}", ACTIVITY_TYPES[0])
        memo      = st.session_state.get(f"w_memo_{fv}", "")
        date_val  = st.session_state.get(f"w_date_{fv}", _date.today())
        meal_val  = st.session_state.get(f"w_meal_{fv}", MEAL_TIMES[0])
        nutr_now  = st.session_state[f"nutr_{fv}"]

        err = None
        if kind_val == "摂取" and not food_save:
            err = "食べ物名を入力してください。"
        elif kcal_now <= 0:
            err = "カロリーを入力してください。"

        if err:
            st.error(err)
        else:
            if kind_val == "摂取":
                is_c = (food_sel == "✏️ その他を入力…")
                np_v  = st.session_state.get(f"w_np_{fv}",  nutr_now["protein"]) if is_c else nutr_now["protein"]
                nf_v  = st.session_state.get(f"w_nf_{fv}",  nutr_now["fat"])     if is_c else nutr_now["fat"]
                nc_v  = st.session_state.get(f"w_nc_{fv}",  nutr_now["carbs"])   if is_c else nutr_now["carbs"]
                nfi_v = st.session_state.get(f"w_nfi_{fv}", nutr_now["fiber"])   if is_c else nutr_now["fiber"]
                row = {
                    "日付": str(date_val), "種別": "摂取",
                    "食事": meal_val, "食べ物": food_save,
                    "カロリー(kcal)": str(kcal_now),
                    "タンパク質(g)": str(np_v), "脂質(g)": str(nf_v),
                    "炭水化物(g)": str(nc_v), "食物繊維(g)": str(nfi_v),
                }
            else:
                row = {
                    "日付": str(date_val), "種別": "消費",
                    "食事": act_sel, "食べ物": memo or act_sel,
                    "カロリー(kcal)": str(kcal_now),
                    "タンパク質(g)": "0", "脂質(g)": "0",
                    "炭水化物(g)": "0", "食物繊維(g)": "0",
                }

            updated = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_df(updated)
            st.session_state.df = updated
            df = updated
            # ▼ ここが重要: ウィジェットキーに直接代入せず、fv をインクリメントするだけ
            st.session_state.ss_saved = True
            st.session_state.fv      += 1
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
        sel   = st.selectbox("📅 日付", all_dates, index=def_i, key="bal_date")

        day = df[df["日付"] == sel].copy()
        day["カロリー(kcal)"] = pd.to_numeric(day["カロリー(kcal)"], errors="coerce").fillna(0)

        intake_k   = day[day["種別"] == "摂取"]["カロリー(kcal)"].sum()
        exercise_k = day[day["種別"] == "消費"]["カロリー(kcal)"].sum()
        consume_k  = BMR_KCAL + exercise_k
        balance    = intake_k - consume_k
        sign       = "+" if balance >= 0 else ""

        m1, m2, m3 = st.columns(3)
        m1.metric("🍽️ 摂取カロリー", f"{intake_k:,.0f} kcal")
        m2.metric("🔥 消費カロリー",  f"{consume_k:,.0f} kcal",
                  f"基礎代謝 {BMR_KCAL:,} + 運動 {exercise_k:,.0f}")
        m3.metric("⚖️ 今日の収支",   f"{sign}{balance:,.0f} kcal")

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
        _, col_r = st.columns([3, 1])
        with col_r:
            asc = st.selectbox("並び順", ["新しい順", "古い順"],
                               label_visibility="collapsed") == "古い順"

        # ── 摂取 ──────────────────────────────────────────────────────────────
        st.markdown('<p class="sec-head">🍽️ 摂取記録（セルをタップして直接編集できます）</p>',
                    unsafe_allow_html=True)
        in_df = (df[df["種別"] == "摂取"]
                 .copy().sort_values("日付", ascending=asc).reset_index(drop=True))
        for c in ["カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]:
            in_df[c] = pd.to_numeric(in_df[c], errors="coerce").fillna(0)

        if in_df.empty:
            st.caption("記録なし")
        else:
            ec_in = ["日付", "食事", "食べ物", "カロリー(kcal)",
                     "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
            with st.form("f_edit_in"):
                ed_in = st.data_editor(
                    in_df[ec_in], use_container_width=True,
                    hide_index=True, num_rows="fixed",
                    column_config={
                        "カロリー(kcal)": st.column_config.NumberColumn("kcal",    format="%g"),
                        "タンパク質(g)":  st.column_config.NumberColumn("P(g)",    format="%.1f"),
                        "脂質(g)":        st.column_config.NumberColumn("F(g)",    format="%.1f"),
                        "炭水化物(g)":    st.column_config.NumberColumn("C(g)",    format="%.1f"),
                        "食物繊維(g)":    st.column_config.NumberColumn("繊維(g)", format="%.1f"),
                    },
                )
                if st.form_submit_button("💾 摂取記録を保存", type="primary",
                                          use_container_width=True):
                    sorted_idx = (df[df["種別"] == "摂取"]
                                  .sort_values("日付", ascending=asc).index)
                    for i, oi in enumerate(sorted_idx):
                        if i < len(ed_in):
                            for col in ec_in:
                                df.loc[oi, col] = str(ed_in.iloc[i][col])
                    save_df(df)
                    st.session_state.df = df
                    st.success("摂取記録を更新しました ✨")
                    st.rerun()

        # ── 消費 ──────────────────────────────────────────────────────────────
        st.markdown('<p class="sec-head">🏃 運動記録（セルをタップして直接編集できます）</p>',
                    unsafe_allow_html=True)
        ex_df = (df[df["種別"] == "消費"]
                 .copy().sort_values("日付", ascending=asc).reset_index(drop=True))
        ex_df["カロリー(kcal)"] = pd.to_numeric(
            ex_df["カロリー(kcal)"], errors="coerce").fillna(0)

        if ex_df.empty:
            st.caption("記録なし")
        else:
            ec_ex = ["日付", "食事", "食べ物", "カロリー(kcal)"]
            with st.form("f_edit_ex"):
                ed_ex = st.data_editor(
                    ex_df[ec_ex].rename(columns={"食事": "活動", "食べ物": "メモ"}),
                    use_container_width=True, hide_index=True, num_rows="fixed",
                    column_config={
                        "カロリー(kcal)": st.column_config.NumberColumn("kcal", format="%g"),
                    },
                )
                if st.form_submit_button("💾 運動記録を保存", type="primary",
                                          use_container_width=True):
                    sorted_idx_ex = (df[df["種別"] == "消費"]
                                     .sort_values("日付", ascending=asc).index)
                    ed_ex2 = ed_ex.rename(columns={"活動": "食事", "メモ": "食べ物"})
                    for i, oi in enumerate(sorted_idx_ex):
                        if i < len(ed_ex2):
                            for col in ec_ex:
                                df.loc[oi, col] = str(ed_ex2.iloc[i][col])
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
                    updated = df.drop(
                        index=del_rows.iloc[di]["index"]).reset_index(drop=True)
                    save_df(updated)
                    st.session_state.df = updated
                    st.success("削除しました。")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: 栄養素
# ─────────────────────────────────────────────────────────────────────────────
with tab_nutr:
    all_dn = sorted(df["日付"].unique(), reverse=True)
    today_str2 = str(_date.today())

    if not all_dn:
        st.info("まだ記録がありません 🌿")
    else:
        def_i2  = all_dn.index(today_str2) if today_str2 in all_dn else 0
        sel_n   = st.selectbox("📅 日付", all_dn, index=def_i2, key="nutr_d")

        nd = df[(df["日付"] == sel_n) & (df["種別"] == "摂取")].copy()
        for c in ["カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]:
            nd[c] = pd.to_numeric(nd[c], errors="coerce").fillna(0)

        tp  = nd["タンパク質(g)"].sum()
        tf  = nd["脂質(g)"].sum()
        tc  = nd["炭水化物(g)"].sum()
        tfi = nd["食物繊維(g)"].sum()
        TGT = {"protein": 60, "fat": 50, "carbs": 230, "fiber": 18}

        n1, n2, n3, n4 = st.columns(4)
        n1.metric("🥩 タンパク質", f"{tp:.1f} g",  f"目安 {TGT['protein']} g")
        n2.metric("🧈 脂質",       f"{tf:.1f} g",  f"目安 {TGT['fat']} g")
        n3.metric("🍚 炭水化物",   f"{tc:.1f} g",  f"目安 {TGT['carbs']} g")
        n4.metric("🥦 食物繊維",   f"{tfi:.1f} g", f"目安 {TGT['fiber']} g")

        st.write("")

        def pbar(label, val, tgt, color, icon):
            pct  = min(val / tgt * 100, 105) if tgt else 0
            flag = ("✅" if 75 <= pct <= 105 else
                    ("⚠️ 摂りすぎ" if pct > 105 else "📉 不足気味"))
            st.markdown(
                f'<div class="n-row">'
                f'<span class="n-lbl">{icon} {label}</span>'
                f'<div class="n-bg"><div class="n-fill" '
                f'style="width:{min(pct,100):.0f}%;background:{color};"></div></div>'
                f'<span class="n-val">{val:.1f}/{tgt}g</span>'
                f'<span style="font-size:.7rem;color:#6B7280">{flag}</span>'
                f'</div>', unsafe_allow_html=True)

        pbar("タンパク質", tp,  TGT["protein"], "#059669", "🥩")
        pbar("脂質",       tf,  TGT["fat"],     "#F59E0B", "🧈")
        pbar("炭水化物",   tc,  TGT["carbs"],   "#6366F1", "🍚")
        pbar("食物繊維",   tfi, TGT["fiber"],   "#10B981", "🥦")

        st.write("")
        total_m = tp + tf + tc
        if total_m > 0:
            pp, pf, pc = tp/total_m*100, tf/total_m*100, tc/total_m*100
            st.markdown(f"""
            <div class="card">
              <div style="font-size:.75rem;font-weight:700;color:#6B7280;letter-spacing:.08em">
                PFCバランス</div>
              <div style="margin-top:8px">
                <span class="badge badge-g">P {pp:.0f}%</span>&nbsp;
                <span class="badge badge-a">F {pf:.0f}%</span>&nbsp;
                <span class="badge badge-p">C {pc:.0f}%</span>
              </div>
              <div style="font-size:.72rem;color:#9CA3AF;margin-top:6px">
                理想 P 15–20% / F 20–30% / C 50–60%</div>
            </div>""", unsafe_allow_html=True)

        st.write("")
        st.markdown('<p class="sec-head">食品別の内訳</p>', unsafe_allow_html=True)
        if nd.empty:
            st.caption("摂取記録がありません。")
        else:
            sc = ["食事", "食べ物", "カロリー(kcal)",
                  "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
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
