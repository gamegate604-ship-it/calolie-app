"""Calolie — スマートカロリー管理"""
import base64
import io
import os
from datetime import date as _date, timedelta

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────────────────────
CSV_FILE    = "food_log.csv"
WEIGHT_CSV  = "weight_log.csv"
FIELDNAMES  = ["日付", "種別", "食事", "食べ物", "カロリー(kcal)",
               "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
WEIGHT_COLS = ["日付", "体重(kg)", "メモ"]
BMR_KCAL    = 1630

MEAL_TIMES     = ["朝", "昼", "夜", "間食"]
ACTIVITY_TYPES = ["ランニング20分", "フットサル1時間", "エルゴ2000m", "自重筋トレ20分", "ヨガ20分"]
ACTIVITY_KCAL  = {"ランニング20分": 200, "フットサル1時間": 600,
                  "エルゴ2000m": 120, "自重筋トレ20分": 100, "ヨガ20分": 60}

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
    "アボカド(1/2個70g)":     {"kcal": 131, "protein":  1.5, "fat": 13.1, "carbs":  3.3, "fiber": 3.8},
    "フルーツ盛り(150g)":     {"kcal":  87, "protein":  0.8, "fat":  0.2, "carbs": 21.5, "fiber": 1.8},
    "チョコレート(25g)":      {"kcal": 136, "protein":  1.7, "fat":  8.5, "carbs": 14.5, "fiber": 0.9},
    "アイスクリーム(100ml)":  {"kcal": 180, "protein":  3.5, "fat":  8.0, "carbs": 24.0, "fiber": 0.0},
    "プロテインバー(40g)":    {"kcal": 160, "protein": 10.0, "fat":  6.0, "carbs": 18.0, "fiber": 2.0},
    "プロテイン(30g)":        {"kcal": 119, "protein": 22.5, "fat":  2.0, "carbs":  4.5, "fiber": 0.5},
    "スムージー(200ml)":      {"kcal": 140, "protein":  3.0, "fat":  1.2, "carbs": 31.0, "fiber": 3.5},
    "オレンジジュース(200ml)":{"kcal":  84, "protein":  0.8, "fat":  0.2, "carbs": 20.0, "fiber": 0.4},
    "コーヒー(200ml)":        {"kcal":   8, "protein":  0.4, "fat":  0.0, "carbs":  1.1, "fiber": 0.0},
    "緑茶・紅茶(200ml)":      {"kcal":   4, "protein":  0.2, "fat":  0.0, "carbs":  0.8, "fiber": 0.0},
    "ウインナー1本(20g)":     {"kcal":  64, "protein":  2.3, "fat":  5.7, "carbs":  0.7, "fiber": 0.0},
    "ウインナー3本(60g)":     {"kcal": 193, "protein":  6.9, "fat": 17.1, "carbs":  2.0, "fiber": 0.0},
    "ウインナー5本(100g)":    {"kcal": 321, "protein": 11.5, "fat": 28.5, "carbs":  3.3, "fiber": 0.0},
}
FOOD_OPTIONS = sorted(NUTRITION.keys())
_DFLT_FOOD   = "バナナ(1本100g)"
_DFLT_IDX    = FOOD_OPTIONS.index(_DFLT_FOOD)

# 栄養素の1日目標値（成人女性・運動習慣あり）
NUTR_TGT = {"protein": 60, "fat": 50, "carbs": 230, "fiber": 18}

GP = dict(bg="#F0FDF4", panel="#FFFFFF", grid="#D1FAE5",
          text="#111827", dim="#6B7280", head="#059669",
          intake="#059669", consume="#7C3AED",
          pos="#EF4444", neg="#059669", border="#A7F3D0",
          weight="#F59E0B")


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


def load_weight_df() -> pd.DataFrame:
    if not os.path.exists(WEIGHT_CSV):
        return pd.DataFrame(columns=WEIGHT_COLS)
    try:
        df = pd.read_csv(WEIGHT_CSV, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=WEIGHT_COLS)
    for c in WEIGHT_COLS:
        if c not in df.columns:
            df[c] = ""
    return df[WEIGHT_COLS]


def save_weight_df(df: pd.DataFrame):
    df.to_csv(WEIGHT_CSV, index=False, encoding="utf-8")


def _nutr(food: str) -> dict:
    n = NUTRITION.get(food, {})
    return {"protein": n.get("protein", 0.0), "fat": n.get("fat", 0.0),
            "carbs":   n.get("carbs",   0.0), "fiber": n.get("fiber", 0.0)}


# ─────────────────────────────────────────────────────────────────────────────
# アイコン生成（PWA用・起動時に一度だけ生成）
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def _icon_b64() -> str:
    size = 512
    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, size); ax.set_ylim(0, size); ax.axis("off")

    # グラデーション背景（左上:エメラルド → 右下:バイオレット）
    for i in range(size):
        t = i / size
        r = 0.020 + (0.486 - 0.020) * t
        g = 0.588 + (0.231 - 0.588) * t
        b = 0.412 + (0.929 - 0.412) * t
        ax.fill_between([0, size], [i, i], [i + 1, i + 1], color=(r, g, b), lw=0)

    # 葉の形
    theta = np.linspace(0, 2 * np.pi, 300)
    cx, cy = 240, 270
    r_base = np.sqrt((130 * 185) ** 2 / ((185 * np.cos(theta)) ** 2 + (130 * np.sin(theta)) ** 2))
    r_mod  = r_base * (0.82 + 0.18 * np.cos(2 * theta))
    ang    = np.radians(12)
    lx = cx + r_mod * np.cos(theta - ang)
    ly = cy + r_mod * np.sin(theta - ang)
    ax.fill(lx, ly, color="white", alpha=0.93, zorder=3)

    # 葉脈（中心線）
    vx = [cx - 18, cx + 22]
    vy = [cy - 162, cy + 162]
    ax.plot(vx, vy, color="#059669", lw=5, alpha=0.45, zorder=4,
            solid_capstyle="round")

    # 茎
    ax.plot([cx + 12, cx + 38], [cy - 162, cy - 218],
            color="white", lw=15, solid_capstyle="round", zorder=4, alpha=0.88)

    # 星（5角形）
    def _star(cx_, cy_, ro, ri, n=5):
        pts = []
        for i in range(n * 2):
            r_ = ro if i % 2 == 0 else ri
            a_ = np.pi / 2 + i * np.pi / n
            pts.append((cx_ + r_ * np.cos(a_), cy_ + r_ * np.sin(a_)))
        return zip(*pts)

    sx, sy = _star(375, 385, 40, 17)
    ax.fill(list(sx), list(sy), color="white", alpha=0.95, zorder=5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ─────────────────────────────────────────────────────────────────────────────
# グラフ：カロリー収支
# ─────────────────────────────────────────────────────────────────────────────
def build_calorie_figure(df: pd.DataFrame):
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
    bi = ax.bar(x - w / 2, iv, width=w, color=p["intake"],  label="摂取",          zorder=3, alpha=0.85)
    bc = ax.bar(x + w / 2, cv, width=w, color=p["consume"], label="消費(BMR+運動)", zorder=3, alpha=0.85)
    for i, (a, b, c) in enumerate(zip(iv, cv, bv)):
        top   = max(a, b)
        color = p["pos"] if c >= 0 else p["neg"]
        ax.text(x[i], top + 20, f"{'+'if c>=0 else''}{c:.0f}",
                ha="center", va="bottom", fontsize=9, color=color, fontweight="bold", zorder=4)
    for bar in [*bi, *bc]:
        h = bar.get_height()
        if h > 60:
            ax.text(bar.get_x() + bar.get_width() / 2, h / 2, f"{h:.0f}",
                    ha="center", va="center", fontsize=8, color="#FFF", fontweight="bold", zorder=5)
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
# グラフ：体重推移
# ─────────────────────────────────────────────────────────────────────────────
def build_weight_figure(wdf: pd.DataFrame):
    p = GP
    wdf = wdf.copy()
    wdf["体重(kg)"] = pd.to_numeric(wdf["体重(kg)"], errors="coerce")
    wdf = wdf.dropna(subset=["体重(kg)"]).sort_values("日付")
    if wdf.empty:
        return None

    dates   = wdf["日付"].tolist()
    weights = wdf["体重(kg)"].tolist()
    x       = np.arange(len(dates))

    fig, ax = plt.subplots(figsize=(max(7, len(dates) * 0.9), 4), facecolor=p["bg"])
    ax.set_facecolor(p["panel"])

    ax.plot(x, weights, color=p["weight"], lw=2.5, marker="o",
            markersize=8, markerfacecolor=p["weight"],
            markeredgecolor="white", markeredgewidth=2, zorder=3)
    ax.fill_between(x, weights, min(weights) - 0.5,
                    color=p["weight"], alpha=0.10, zorder=2)

    # 3日移動平均
    if len(weights) >= 3:
        ma = pd.Series(weights).rolling(3, center=True).mean().tolist()
        ax.plot(x, ma, color="#7C3AED", lw=1.8, ls="--", alpha=0.75,
                label="3日移動平均", zorder=4)

    # 各点にラベル
    for xi, w in zip(x, weights):
        ax.text(xi, w + 0.08, f"{w:.1f}", ha="center", va="bottom",
                fontsize=8, color=p["text"], fontweight="bold", zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=30, ha="right", color=p["text"], fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=p["text"])
    ax.tick_params(colors=p["dim"])
    ax.set_ylabel("kg", color=p["dim"], fontsize=10)
    ax.spines[:].set_color(p["border"])
    ax.grid(axis="y", color=p["grid"], lw=0.8, zorder=1)
    ax.set_title("体重推移", color=p["head"], fontsize=14, pad=14, fontweight="bold")
    if len(weights) >= 3:
        ax.legend(facecolor=p["panel"], edgecolor=p["border"],
                  labelcolor=p["text"], fontsize=9)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Calolie", page_icon="🌿",
                   layout="wide", initial_sidebar_state="expanded")

# PWA アイコン・マニフェスト注入
_ib64 = _icon_b64()
st.markdown(f"""
<script>
(function(){{
  var h = document.head || document.getElementsByTagName('head')[0];
  // favicon
  var fi = document.createElement('link');
  fi.rel='icon'; fi.type='image/png';
  fi.href='data:image/png;base64,{_ib64}';
  h.appendChild(fi);
  // Apple touch icon
  var ai = document.createElement('link');
  ai.rel='apple-touch-icon';
  ai.href='data:image/png;base64,{_ib64}';
  h.appendChild(ai);
  // Apple PWA
  [['mobile-web-app-capable','yes'],
   ['apple-mobile-web-app-capable','yes'],
   ['apple-mobile-web-app-title','Calolie'],
   ['apple-mobile-web-app-status-bar-style','black-translucent']
  ].forEach(function(kv){{
    var m=document.createElement('meta');
    m.name=kv[0]; m.content=kv[1]; h.appendChild(m);
  }});
  // Web App Manifest
  var manifest={{
    "name":"Calolie","short_name":"Calolie",
    "description":"スマートカロリー管理アプリ",
    "start_url":".","display":"standalone",
    "orientation":"portrait",
    "background_color":"#F0FDF4","theme_color":"#059669",
    "icons":[{{"src":"data:image/png;base64,{_ib64}",
               "sizes":"512x512","type":"image/png","purpose":"any maskable"}}]
  }};
  var blob=new Blob([JSON.stringify(manifest)],{{type:'application/manifest+json'}});
  var ml=document.createElement('link');
  ml.rel='manifest'; ml.href=URL.createObjectURL(blob);
  h.appendChild(ml);
}})();
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
html,body,[class*="css"]{font-family:'Hiragino Sans','Noto Sans JP','Yu Gothic',sans-serif;}
.grad-title{background:linear-gradient(135deg,#059669 0%,#7C3AED 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  font-size:1.9rem;font-weight:900;letter-spacing:.03em;line-height:1.2;}
.caption{color:#6B7280;font-size:.82rem;margin-top:2px;}
.card{background:#FFF;border-radius:16px;padding:20px 24px;
  box-shadow:0 1px 8px rgba(5,150,105,.10);border:1px solid #D1FAE5;margin-bottom:12px;}
.badge{display:inline-block;padding:3px 10px;border-radius:50px;
  font-size:.78rem;font-weight:700;letter-spacing:.04em;}
.badge-g{background:#D1FAE5;color:#065F46;}
.badge-p{background:#EDE9FE;color:#5B21B6;}
.badge-a{background:#FEF3C7;color:#92400E;}
.badge-r{background:#FEE2E2;color:#991B1B;}
[data-testid="metric-container"]{background:#FFF;border-radius:16px;
  padding:16px!important;box-shadow:0 1px 8px rgba(5,150,105,.08);border:1px solid #D1FAE5;}
.stButton>button{border-radius:50px!important;font-weight:700!important;
  letter-spacing:.04em;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;
  box-shadow:0 4px 16px rgba(5,150,105,.25)!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#ECFDF5 0%,#EEF2FF 100%);
  border-right:1px solid #D1FAE5;}
.saved-banner{background:linear-gradient(90deg,#D1FAE5,#EDE9FE);border-radius:12px;
  padding:10px 16px;text-align:center;font-weight:700;color:#065F46;
  margin-bottom:10px;font-size:.9rem;}
.n-row{display:flex;align-items:center;gap:8px;margin:5px 0;}
.n-lbl{width:80px;font-size:.78rem;color:#6B7280;font-weight:600;}
.n-bg{flex:1;background:#F3F4F6;border-radius:8px;height:10px;overflow:hidden;}
.n-fill{height:10px;border-radius:8px;}
.n-val{width:72px;font-size:.78rem;color:#374151;text-align:right;}
.sec-head{font-size:.75rem;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;color:#6B7280;margin:16px 0 6px;}
.stTabs [data-baseweb="tab-list"]{gap:4px;}
.stTabs [data-baseweb="tab"]{border-radius:50px;padding:6px 18px;font-weight:600;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session State 初期化
# ─────────────────────────────────────────────────────────────────────────────
for _k, _v in [("df", None), ("wdf", None), ("fv", 0), ("ss_saved", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.df is None:
    st.session_state.df = load_df()
if st.session_state.wdf is None:
    st.session_state.wdf = load_weight_df()

fv = st.session_state.fv
if f"nutr_{fv}" not in st.session_state:
    st.session_state[f"nutr_{fv}"] = _nutr(_DFLT_FOOD)


# ─── コールバック ─────────────────────────────────────────────────────────────
def _on_food():
    food = st.session_state.get(f"w_food_{fv}", "")
    if food in NUTRITION:
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


df  = st.session_state.df
wdf = st.session_state.wdf


# ─────────────────────────────────────────────────────────────────────────────
# サイドバー（食事・運動入力）
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

    kind_raw = st.radio("種別", ["🍽️ 食事（摂取）", "🏃 運動（消費）"],
                         horizontal=True, key=f"w_kind_{fv}")
    kind_val = "摂取" if "摂取" in kind_raw else "消費"

    # 日付（format パラメータなし → カレンダー表示される）
    st.date_input("📅 日付", value=_date.today(), key=f"w_date_{fv}")

    if kind_val == "摂取":
        st.selectbox("🕐 タイミング", MEAL_TIMES, key=f"w_meal_{fv}")
        st.markdown('<p class="sec-head">食べ物を選択</p>', unsafe_allow_html=True)

        food_choice = st.selectbox(
            "食べ物", FOOD_OPTIONS + ["✏️ その他を入力…"],
            index=_DFLT_IDX, key=f"w_food_{fv}",
            on_change=_on_food, label_visibility="collapsed",
        )
        is_custom = food_choice == "✏️ その他を入力…"
        if is_custom:
            st.text_input("食べ物名", placeholder="例: タピオカ 🧋",
                           key=f"w_custom_{fv}")

        if f"w_kcal_{fv}" not in st.session_state:
            st.session_state[f"w_kcal_{fv}"] = int(
                NUTRITION.get(food_choice, {}).get("kcal", 0))
        st.number_input("🔥 カロリー (kcal)",
                         min_value=0, step=5, key=f"w_kcal_{fv}", on_change=_on_kcal)

        nutr = st.session_state[f"nutr_{fv}"]
        if is_custom:
            for _k, _v in [(f"w_np_{fv}",  float(nutr["protein"])),
                           (f"w_nf_{fv}",  float(nutr["fat"])),
                           (f"w_nc_{fv}",  float(nutr["carbs"])),
                           (f"w_nfi_{fv}", float(nutr["fiber"]))]:
                if _k not in st.session_state:
                    st.session_state[_k] = _v
            st.markdown('<p class="sec-head">栄養素（手動入力）</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("タンパク質 g", min_value=0.0, step=0.1, key=f"w_np_{fv}")
                st.number_input("炭水化物 g",   min_value=0.0, step=0.1, key=f"w_nc_{fv}")
            with c2:
                st.number_input("脂質 g",     min_value=0.0, step=0.1, key=f"w_nf_{fv}")
                st.number_input("食物繊維 g", min_value=0.0, step=0.1, key=f"w_nfi_{fv}")
        else:
            st.markdown('<p class="sec-head">推定栄養素（kcalに連動）</p>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("🥩 タンパク質", f"{nutr['protein']} g")
            c2.metric("🧈 脂質",       f"{nutr['fat']} g")
            c3, c4 = st.columns(2)
            c3.metric("🍚 炭水化物",   f"{nutr['carbs']} g")
            c4.metric("🥦 食物繊維",   f"{nutr['fiber']} g")

    else:
        st.selectbox("🏋️ 活動", ACTIVITY_TYPES,
                      key=f"w_activity_{fv}", on_change=_on_activity)
        st.text_input("📝 メモ（任意）", placeholder="公園で実施など",
                       key=f"w_memo_{fv}")
        if f"w_kcal_{fv}" not in st.session_state:
            st.session_state[f"w_kcal_{fv}"] = ACTIVITY_KCAL[ACTIVITY_TYPES[0]]
        st.number_input("🔥 カロリー (kcal)", min_value=0, step=5, key=f"w_kcal_{fv}")

    st.divider()

    if st.button("✨ 保存する", use_container_width=True, type="primary"):
        kcal_now = st.session_state.get(f"w_kcal_{fv}", 0) or 0
        food_sel = st.session_state.get(f"w_food_{fv}", "")
        custom   = st.session_state.get(f"w_custom_{fv}", "")
        food_save = custom if food_sel == "✏️ その他を入力…" else food_sel
        act_sel  = st.session_state.get(f"w_activity_{fv}", ACTIVITY_TYPES[0])
        memo     = st.session_state.get(f"w_memo_{fv}", "")
        date_val = st.session_state.get(f"w_date_{fv}", _date.today())
        meal_val = st.session_state.get(f"w_meal_{fv}", MEAL_TIMES[0])
        nutr_now = st.session_state[f"nutr_{fv}"]

        err = None
        if kind_val == "摂取" and not food_save:
            err = "食べ物名を入力してください。"
        elif kcal_now <= 0:
            err = "カロリーを入力してください。"

        if err:
            st.error(err)
        else:
            is_c = (food_sel == "✏️ その他を入力…")
            if kind_val == "摂取":
                row = {
                    "日付": str(date_val), "種別": "摂取",
                    "食事": meal_val, "食べ物": food_save,
                    "カロリー(kcal)": str(kcal_now),
                    "タンパク質(g)": str(st.session_state.get(f"w_np_{fv}",  nutr_now["protein"]) if is_c else nutr_now["protein"]),
                    "脂質(g)":       str(st.session_state.get(f"w_nf_{fv}",  nutr_now["fat"])     if is_c else nutr_now["fat"]),
                    "炭水化物(g)":   str(st.session_state.get(f"w_nc_{fv}",  nutr_now["carbs"])   if is_c else nutr_now["carbs"]),
                    "食物繊維(g)":   str(st.session_state.get(f"w_nfi_{fv}", nutr_now["fiber"])   if is_c else nutr_now["fiber"]),
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
            st.session_state.ss_saved = True
            st.session_state.fv += 1   # ← ウィジェットキーに直接代入しない
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# メインエリア
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="grad-title">🌿 Calolie</p>', unsafe_allow_html=True)
st.markdown('<p class="caption">食事・運動・体重・栄養をまとめて管理 — なりたい自分をデザインしよう ✨</p>',
            unsafe_allow_html=True)
st.write("")

tab_bal, tab_log, tab_weight, tab_nutr, tab_graph = st.tabs(
    ["📊 収支", "📝 記録・編集", "⚖️ 体重", "🧬 栄養素", "📈 グラフ"])

today_str = str(_date.today())


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: 収支
# ─────────────────────────────────────────────────────────────────────────────
with tab_bal:
    all_dates = sorted(df["日付"].unique(), reverse=True)

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

        # ── 妥当な文言ロジック ──────────────────────────────────────────────
        if exercise_k >= 600:
            # 運動量が非常に多い日 → 消費過多を警告
            if balance < -800:
                st.error(f"⚠️ 運動量がかなり多く、収支は **{abs(balance):,.0f} kcal** マイナスです。"
                         f"疲労回復のためにしっかり食事で補給しましょう！")
            elif balance < -300:
                st.warning(f"💪 よく動きました！収支 **{abs(balance):,.0f} kcal** マイナス。"
                           f"タンパク質など栄養補給も忘れずに。")
            else:
                st.success(f"✨ 運動と食事のバランスが取れています！収支 **{sign}{balance:,.0f} kcal**")
        elif balance > 600:
            st.error(f"📢 摂取オーバー **{balance:,.0f} kcal**。明日は少し体を動かしてみましょう。")
        elif balance > 250:
            st.warning(f"🔸 **{balance:,.0f} kcal** プラス。少し食べ過ぎかも。")
        elif balance >= -250:
            st.success(f"✨ 収支 **{sign}{balance:,.0f} kcal**。理想的なバランスです！")
        elif balance >= -500:
            st.success(f"💚 **{abs(balance):,.0f} kcal** マイナス。いい調子です！")
        else:
            st.warning(f"⚠️ **{abs(balance):,.0f} kcal** マイナスは多すぎるかも。"
                       f"食事量を少し増やして体を労ってあげましょう。")


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

        # 摂取
        st.markdown('<p class="sec-head">🍽️ 摂取記録（セルを直接タップして編集可）</p>',
                    unsafe_allow_html=True)
        in_df = (df[df["種別"] == "摂取"].copy()
                 .sort_values("日付", ascending=asc).reset_index(drop=True))
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
                    })
                if st.form_submit_button("💾 摂取記録を保存", type="primary",
                                          use_container_width=True):
                    si = df[df["種別"] == "摂取"].sort_values("日付", ascending=asc).index
                    for i, oi in enumerate(si):
                        if i < len(ed_in):
                            for col in ec_in:
                                df.loc[oi, col] = str(ed_in.iloc[i][col])
                    save_df(df); st.session_state.df = df
                    st.success("摂取記録を更新しました ✨"); st.rerun()

        # 消費
        st.markdown('<p class="sec-head">🏃 運動記録（セルを直接タップして編集可）</p>',
                    unsafe_allow_html=True)
        ex_df = (df[df["種別"] == "消費"].copy()
                 .sort_values("日付", ascending=asc).reset_index(drop=True))
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
                    })
                if st.form_submit_button("💾 運動記録を保存", type="primary",
                                          use_container_width=True):
                    si2   = df[df["種別"] == "消費"].sort_values("日付", ascending=asc).index
                    ed_ex2 = ed_ex.rename(columns={"活動": "食事", "メモ": "食べ物"})
                    for i, oi in enumerate(si2):
                        if i < len(ed_ex2):
                            for col in ec_ex:
                                df.loc[oi, col] = str(ed_ex2.iloc[i][col])
                    save_df(df); st.session_state.df = df
                    st.success("運動記録を更新しました ✨"); st.rerun()

        # 削除
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
                    save_df(updated); st.session_state.df = updated
                    st.success("削除しました。"); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: 体重
# ─────────────────────────────────────────────────────────────────────────────
with tab_weight:
    # ── 入力フォーム ──────────────────────────────────────────────────────────
    with st.expander("➕ 体重を記録する", expanded=wdf.empty):
        with st.form("weight_form"):
            wc1, wc2 = st.columns([1, 2])
            with wc1:
                w_date = st.date_input("📅 日付", value=_date.today(), key="wf_date")
            with wc2:
                # 直近の体重を初期値に
                last_w = 55.0
                if not wdf.empty:
                    tmp = wdf.copy()
                    tmp["体重(kg)"] = pd.to_numeric(tmp["体重(kg)"], errors="coerce")
                    tmp = tmp.dropna(subset=["体重(kg)"])
                    if not tmp.empty:
                        last_w = float(tmp.sort_values("日付").iloc[-1]["体重(kg)"])
                w_kg = st.number_input("⚖️ 体重 (kg)", min_value=20.0, max_value=250.0,
                                        value=last_w, step=0.1, format="%.1f")
            w_memo = st.text_input("📝 メモ（任意）", placeholder="例: 朝起床後・食前")
            if st.form_submit_button("記録する", type="primary", use_container_width=True):
                new_w = pd.DataFrame([{
                    "日付": str(w_date), "体重(kg)": str(w_kg), "メモ": w_memo
                }])
                updated_w = pd.concat([wdf, new_w], ignore_index=True)
                save_weight_df(updated_w)
                st.session_state.wdf = updated_w
                wdf = updated_w
                st.success(f"✅ {w_date} の体重 {w_kg:.1f} kg を記録しました！")
                st.rerun()

    # ── グラフ ────────────────────────────────────────────────────────────────
    if wdf.empty:
        st.info("まだ体重の記録がありません。上のフォームから追加してください ⚖️")
    else:
        wdf_sorted = wdf.copy()
        wdf_sorted["体重(kg)"] = pd.to_numeric(wdf_sorted["体重(kg)"], errors="coerce")
        wdf_sorted = wdf_sorted.dropna(subset=["体重(kg)"]).sort_values("日付")

        # サマリー
        if len(wdf_sorted) >= 2:
            latest  = float(wdf_sorted.iloc[-1]["体重(kg)"])
            prev    = float(wdf_sorted.iloc[-2]["体重(kg)"])
            delta   = latest - prev
            sign_w  = "+" if delta >= 0 else ""
            wm1, wm2, wm3 = st.columns(3)
            wm1.metric("最新体重", f"{latest:.1f} kg")
            wm2.metric("前回比",   f"{sign_w}{delta:.1f} kg")
            if len(wdf_sorted) >= 7:
                avg7 = float(wdf_sorted.tail(7)["体重(kg)"].mean())
                wm3.metric("7日平均", f"{avg7:.1f} kg")

        fig_w = build_weight_figure(wdf_sorted)
        if fig_w:
            st.pyplot(fig_w, use_container_width=True)
            plt.close(fig_w)

        # 体重記録テーブル（編集可）
        st.markdown('<p class="sec-head">体重記録一覧（セルをタップして編集可）</p>',
                    unsafe_allow_html=True)
        wdf_disp = wdf_sorted[["日付", "体重(kg)", "メモ"]].reset_index(drop=True)
        with st.form("f_edit_weight"):
            ed_w = st.data_editor(
                wdf_disp, use_container_width=True, hide_index=True, num_rows="fixed",
                column_config={
                    "体重(kg)": st.column_config.NumberColumn("体重 (kg)", format="%.1f"),
                })
            if st.form_submit_button("💾 体重記録を保存", type="primary",
                                      use_container_width=True):
                save_weight_df(ed_w)
                st.session_state.wdf = ed_w
                st.success("体重記録を更新しました ✨"); st.rerun()

        with st.expander("🗑️ 体重記録を削除する"):
            wdf_idx = wdf.reset_index()
            del_opts_w = [f"{r['日付']} — {r['体重(kg)']} kg"
                          for _, r in wdf_idx.iterrows()]
            if del_opts_w:
                di_w = st.selectbox("削除する行", range(len(del_opts_w)),
                                     format_func=lambda i: del_opts_w[i], key="del_w")
                if st.button("削除", type="secondary", key="del_w_btn"):
                    upd_w = wdf.drop(index=wdf_idx.iloc[di_w]["index"]).reset_index(drop=True)
                    save_weight_df(upd_w); st.session_state.wdf = upd_w
                    st.success("削除しました。"); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tab 4: 栄養素
# ─────────────────────────────────────────────────────────────────────────────
with tab_nutr:
    all_dn = sorted(df["日付"].unique(), reverse=True)
    if not all_dn:
        st.info("まだ記録がありません 🌿")
    else:
        # ── 日別ビュー ────────────────────────────────────────────────────────
        st.markdown('<p class="sec-head">📅 日別の栄養素</p>', unsafe_allow_html=True)
        def_i2 = all_dn.index(today_str) if today_str in all_dn else 0
        sel_n  = st.selectbox("日付", all_dn, index=def_i2, key="nutr_d",
                               label_visibility="collapsed")

        nd = df[(df["日付"] == sel_n) & (df["種別"] == "摂取")].copy()
        for c in ["カロリー(kcal)", "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]:
            nd[c] = pd.to_numeric(nd[c], errors="coerce").fillna(0)

        tp  = nd["タンパク質(g)"].sum()
        tf  = nd["脂質(g)"].sum()
        tc  = nd["炭水化物(g)"].sum()
        tfi = nd["食物繊維(g)"].sum()

        n1, n2, n3, n4 = st.columns(4)
        n1.metric("🥩 タンパク質", f"{tp:.1f} g",  f"目安 {NUTR_TGT['protein']} g")
        n2.metric("🧈 脂質",       f"{tf:.1f} g",  f"目安 {NUTR_TGT['fat']} g")
        n3.metric("🍚 炭水化物",   f"{tc:.1f} g",  f"目安 {NUTR_TGT['carbs']} g")
        n4.metric("🥦 食物繊維",   f"{tfi:.1f} g", f"目安 {NUTR_TGT['fiber']} g")

        def pbar(label, val, tgt, color, icon):
            pct  = min(val / tgt * 100, 110) if tgt else 0
            flag = ("✅" if 75 <= pct <= 105
                    else ("⚠️ 摂りすぎ" if pct > 105 else "📉 不足気味"))
            st.markdown(
                f'<div class="n-row">'
                f'<span class="n-lbl">{icon} {label}</span>'
                f'<div class="n-bg"><div class="n-fill" '
                f'style="width:{min(pct,100):.0f}%;background:{color};"></div></div>'
                f'<span class="n-val">{val:.1f}/{tgt}g</span>'
                f'<span style="font-size:.7rem;color:#6B7280;margin-left:4px">{flag}</span>'
                f'</div>', unsafe_allow_html=True)

        st.write("")
        pbar("タンパク質", tp,  NUTR_TGT["protein"], "#059669", "🥩")
        pbar("脂質",       tf,  NUTR_TGT["fat"],     "#F59E0B", "🧈")
        pbar("炭水化物",   tc,  NUTR_TGT["carbs"],   "#6366F1", "🍚")
        pbar("食物繊維",   tfi, NUTR_TGT["fiber"],   "#10B981", "🥦")

        # PFCバランス
        total_m = tp + tf + tc
        if total_m > 0:
            pp, pf, pc = tp/total_m*100, tf/total_m*100, tc/total_m*100
            st.markdown(f"""
            <div class="card" style="margin-top:12px">
              <div style="font-size:.75rem;font-weight:700;color:#6B7280;letter-spacing:.08em">PFCバランス</div>
              <div style="margin-top:8px">
                <span class="badge badge-g">P {pp:.0f}%</span>&nbsp;
                <span class="badge badge-a">F {pf:.0f}%</span>&nbsp;
                <span class="badge badge-p">C {pc:.0f}%</span>
              </div>
              <div style="font-size:.72rem;color:#9CA3AF;margin-top:6px">
                理想 P 15–20% / F 20–30% / C 50–60%</div>
            </div>""", unsafe_allow_html=True)

        # 食品別内訳
        if not nd.empty:
            st.markdown('<p class="sec-head">食品別の内訳</p>', unsafe_allow_html=True)
            sc = ["食事", "食べ物", "カロリー(kcal)", "タンパク質(g)",
                  "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
            st.dataframe(nd[sc].reset_index(drop=True),
                         use_container_width=True, hide_index=True)

        st.divider()

        # ── 過去7日の傾向・不足判定 ────────────────────────────────────────────
        st.markdown('<p class="sec-head">📈 過去7日間の平均と傾向</p>', unsafe_allow_html=True)

        cutoff = (pd.Timestamp(today_str) - pd.Timedelta(days=6)).strftime("%Y-%m-%d")
        week_df = df[(df["日付"] >= cutoff) & (df["種別"] == "摂取")].copy()
        for c in ["タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]:
            week_df[c] = pd.to_numeric(week_df[c], errors="coerce").fillna(0)

        days_in_range = max(week_df["日付"].nunique(), 1)
        avg_p  = week_df["タンパク質(g)"].sum() / days_in_range
        avg_f  = week_df["脂質(g)"].sum()        / days_in_range
        avg_c  = week_df["炭水化物(g)"].sum()     / days_in_range
        avg_fi = week_df["食物繊維(g)"].sum()     / days_in_range

        wa1, wa2, wa3, wa4 = st.columns(4)
        wa1.metric("🥩 タンパク質 平均", f"{avg_p:.1f} g/日")
        wa2.metric("🧈 脂質 平均",       f"{avg_f:.1f} g/日")
        wa3.metric("🍚 炭水化物 平均",   f"{avg_c:.1f} g/日")
        wa4.metric("🥦 食物繊維 平均",   f"{avg_fi:.1f} g/日")

        st.write("")

        # 不足している栄養素のカード表示
        shortfalls = []
        if avg_p  < NUTR_TGT["protein"] * 0.75:
            shortfalls.append(("🥩 タンパク質", avg_p,  NUTR_TGT["protein"],
                                "肉・魚・卵・豆腐・プロテインを意識して追加しましょう"))
        if avg_f  < NUTR_TGT["fat"]     * 0.75:
            shortfalls.append(("🧈 脂質",       avg_f,  NUTR_TGT["fat"],
                                "アボカド・ナッツ・オリーブオイルで良質な脂質を補いましょう"))
        if avg_c  < NUTR_TGT["carbs"]   * 0.75:
            shortfalls.append(("🍚 炭水化物",   avg_c,  NUTR_TGT["carbs"],
                                "ご飯・パン・オートミールでエネルギー源をしっかり確保しましょう"))
        if avg_fi < NUTR_TGT["fiber"]   * 0.75:
            shortfalls.append(("🥦 食物繊維",   avg_fi, NUTR_TGT["fiber"],
                                "野菜・きのこ・海藻・豆類を積極的に取り入れましょう"))

        if shortfalls:
            st.markdown("**⚠️ 不足気味の栄養素**", unsafe_allow_html=False)
            for name, avg_val, tgt_val, tip in shortfalls:
                pct = avg_val / tgt_val * 100 if tgt_val else 0
                st.markdown(f"""
                <div class="card" style="border-left:4px solid #F59E0B;padding:14px 18px">
                  <div style="font-weight:700;font-size:1rem">{name}</div>
                  <div style="color:#6B7280;font-size:.82rem;margin:4px 0">
                    平均 {avg_val:.1f} g / 目安 {tgt_val} g（{pct:.0f}%）</div>
                  <div style="font-size:.85rem;color:#374151">💡 {tip}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("✅ 過去7日間の栄養バランスは良好です！この調子で続けましょう 🌿")

        # 過去7日の日別栄養素グラフ
        if not week_df.empty:
            daily_nutr = (week_df.groupby("日付")
                          [["タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]]
                          .sum().reset_index())
            fig_n, ax_n = plt.subplots(figsize=(max(7, len(daily_nutr)*1.1), 4),
                                        facecolor=GP["bg"])
            ax_n.set_facecolor(GP["panel"])
            x_n = np.arange(len(daily_nutr))
            colors_n = ["#059669", "#F59E0B", "#6366F1", "#10B981"]
            cols_n   = ["タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
            labels_n = ["タンパク質", "脂質", "炭水化物", "食物繊維"]
            for ci, (col, label, color) in enumerate(zip(cols_n, labels_n, colors_n)):
                ax_n.plot(x_n, daily_nutr[col], color=color, lw=2,
                           marker="o", markersize=6,
                           markeredgecolor="white", markeredgewidth=1.5,
                           label=label, zorder=3)
            ax_n.set_xticks(x_n)
            ax_n.set_xticklabels(daily_nutr["日付"].tolist(),
                                  rotation=30, ha="right", color=GP["text"], fontsize=9)
            ax_n.yaxis.set_tick_params(labelcolor=GP["text"])
            ax_n.set_ylabel("g", color=GP["dim"], fontsize=10)
            ax_n.spines[:].set_color(GP["border"])
            ax_n.grid(axis="y", color=GP["grid"], lw=0.8, zorder=1)
            ax_n.set_title("過去7日間の栄養素推移",
                            color=GP["head"], fontsize=13, pad=12, fontweight="bold")
            ax_n.legend(facecolor=GP["panel"], edgecolor=GP["border"],
                        labelcolor=GP["text"], fontsize=9, ncol=2)
            plt.tight_layout()
            st.pyplot(fig_n, use_container_width=True)
            plt.close(fig_n)

        st.divider()
        with st.expander("📚 栄養データの出典"):
            st.markdown("""
**出典：文部科学省『日本食品標準成分表2020年版（八訂）』**

プリセット食品の栄養値は上記成分表に基づいています。
定食・カレー・ラーメンなど複合料理は概算値です。
「✏️ その他を入力…」で選択した場合は手入力した値がそのまま記録されます。

- 成分表の詳細: [文部科学省 食品成分データベース](https://fooddb.mext.go.jp/)
""")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 5: グラフ（カロリー収支）
# ─────────────────────────────────────────────────────────────────────────────
with tab_graph:
    fig = build_calorie_figure(df)
    if fig is None:
        st.info("記録がありません。サイドバーからデータを追加してください 🌿")
    else:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
