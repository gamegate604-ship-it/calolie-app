"""Calolie — スマートカロリー管理"""
import base64
import io
from datetime import date as _date, timedelta

import gspread
from google.oauth2.service_account import Credentials

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────────────────────
FIELDNAMES  = ["日付", "種別", "食事", "食べ物", "カロリー(kcal)",
               "タンパク質(g)", "脂質(g)", "炭水化物(g)", "食物繊維(g)"]
WEIGHT_COLS = ["日付", "体重(kg)", "メモ"]
_bmr    = 1630

MEAL_TIMES     = ["朝", "昼", "夜", "間食"]
ACTIVITY_TYPES = ["ランニング20分", "フットサル1時間", "エルゴ2000m",
                  "エルゴ3000m", "エルゴ3000mレート17", "自重筋トレ20分", "ヨガ20分"]
ACTIVITY_KCAL  = {"ランニング20分": 200, "フットサル1時間": 600,
                  "エルゴ2000m": 120, "エルゴ3000m": 180,
                  "エルゴ3000mレート17": 193,
                  "自重筋トレ20分": 100, "ヨガ20分": 60}

NUTRITION: dict[str, dict[str, float]] = {
    "ご飯(1杯160g)":          {"kcal": 269, "protein":  4.1, "fat":  0.5, "carbs": 59.4, "fiber": 0.5},
    "ご飯1合(炊いた330g)":   {"kcal": 554, "protein":  8.3, "fat":  1.0, "carbs":122.4, "fiber": 1.0},
    "ご飯2合(炊いた660g)":   {"kcal":1109, "protein": 16.5, "fat":  2.0, "carbs":244.9, "fiber": 2.0},
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
    "唐揚げ定食":             {"kcal": 750, "protein": 27.0, "fat": 22.0, "carbs": 95.0, "fiber": 2.5},
    "お好み焼き(1枚)":        {"kcal": 320, "protein": 15.0, "fat": 11.0, "carbs": 40.0, "fiber": 2.5},
    "卵(Mサイズ1個)":         {"kcal":  76, "protein":  6.2, "fat":  5.2, "carbs":  0.2, "fiber": 0.0},
    "卵2個":                  {"kcal": 152, "protein": 12.4, "fat": 10.4, "carbs":  0.4, "fiber": 0.0},
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

# ご飯1杯追加分の栄養素（ご飯(1杯160g) から）
_RICE_ADD = {"kcal": 269, "protein": 4.1, "fat": 0.5, "carbs": 59.4, "fiber": 0.5}

# 栄養素の1日目標値（成人女性・運動習慣あり）
NUTR_TGT = {"protein": 60, "fat": 50, "carbs": 230, "fiber": 18}

GP = dict(bg="#F0FDF4", panel="#FFFFFF", grid="#D1FAE5",
          text="#111827", dim="#6B7280", head="#059669",
          intake="#059669", consume="#7C3AED",
          pos="#EF4444", neg="#059669", border="#A7F3D0",
          weight="#F59E0B")


# ─────────────────────────────────────────────────────────────────────────────
# Google Sheets
# ─────────────────────────────────────────────────────────────────────────────
_GS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
FOOD_SHEET_NAME   = "食事記録"
WEIGHT_SHEET_NAME = "体重記録"


@st.cache_resource
def _gs_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=_GS_SCOPES)
    return gspread.authorize(creds)


def _get_ws(sheet_name: str, cols: list) -> gspread.Worksheet:
    ss = _gs_client().open_by_key(st.secrets["sheets"]["spreadsheet_id"])
    try:
        ws = ss.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=sheet_name, rows=2000, cols=len(cols))
        ws.append_row(cols)
    return ws


FOOD_SHEET_NAME   = "食事記録"
WEIGHT_SHEET_NAME = "体重記録"
SETTINGS_SHEET    = "設定"
CONDITION_SHEET   = "コンディション記録"
CONDITION_COLS    = ["日付", "コンディション", "メモ"]
COND_EMOJI  = {1: "😩", 2: "😕", 3: "😐", 4: "😊", 5: "😄"}
COND_LABEL  = {1: "最悪", 2: "イマイチ", 3: "普通", 4: "良い", 5: "最高"}

ERGO_SHEET_NAME = "エルゴ記録"
ERGO_DISTANCES  = [2000, 3000, 4000]
ERGO_SPLITS     = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
ERGO_COLS       = (["日付", "距離(m)", "トータルタイム", "メモ"] +
                   [c for d in ERGO_SPLITS for c in (f"{d}m_タイム", f"{d}m_レート")])
_ERGO_DIST_COLOR = {"2000": "#7C3AED", "3000": "#059669", "4000": "#F59E0B"}


def _time_to_sec(s: str) -> "int | None":
    """'M:SS' or 'MM:SS' → seconds。パース失敗時は None"""
    s = s.strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None


def _sec_to_mmss(sec) -> str:
    """seconds → 'M:SS'"""
    try:
        sec = int(sec)
        return f"{sec // 60}:{sec % 60:02d}"
    except Exception:
        return ""


def load_df() -> pd.DataFrame:
    try:
        ws   = _get_ws(FOOD_SHEET_NAME, FIELDNAMES)
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return pd.DataFrame(columns=FIELDNAMES)
        df = pd.DataFrame(rows[1:], columns=rows[0]).fillna("")
        for col in FIELDNAMES:
            if col not in df.columns:
                df[col] = ""
        if df["種別"].eq("").all():
            df["種別"] = "摂取"
        return df[FIELDNAMES]
    except Exception:
        return pd.DataFrame(columns=FIELDNAMES)


def save_df(df: pd.DataFrame):
    ws = _get_ws(FOOD_SHEET_NAME, FIELDNAMES)
    ws.clear()
    ws.update([FIELDNAMES] + df[FIELDNAMES].fillna("").astype(str).values.tolist())


def load_weight_df() -> pd.DataFrame:
    try:
        ws   = _get_ws(WEIGHT_SHEET_NAME, WEIGHT_COLS)
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return pd.DataFrame(columns=WEIGHT_COLS)
        df = pd.DataFrame(rows[1:], columns=rows[0]).fillna("")
        for c in WEIGHT_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[WEIGHT_COLS]
    except Exception:
        return pd.DataFrame(columns=WEIGHT_COLS)


def save_weight_df(df: pd.DataFrame):
    ws = _get_ws(WEIGHT_SHEET_NAME, WEIGHT_COLS)
    ws.clear()
    ws.update([WEIGHT_COLS] + df[WEIGHT_COLS].fillna("").astype(str).values.tolist())


def load_settings() -> dict:
    try:
        ws   = _get_ws(SETTINGS_SHEET, ["項目", "値"])
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return {}
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2}
    except Exception:
        return {}


def save_settings(d: dict):
    ws = _get_ws(SETTINGS_SHEET, ["項目", "値"])
    ws.clear()
    ws.update([["項目", "値"]] + [[k, v] for k, v in d.items()])


def load_cond_df() -> pd.DataFrame:
    try:
        ws   = _get_ws(CONDITION_SHEET, CONDITION_COLS)
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return pd.DataFrame(columns=CONDITION_COLS)
        df = pd.DataFrame(rows[1:], columns=rows[0]).fillna("")
        for c in CONDITION_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[CONDITION_COLS]
    except Exception:
        return pd.DataFrame(columns=CONDITION_COLS)


def save_cond_df(df: pd.DataFrame):
    ws = _get_ws(CONDITION_SHEET, CONDITION_COLS)
    ws.clear()
    ws.update([CONDITION_COLS] + df[CONDITION_COLS].fillna("").astype(str).values.tolist())


def load_ergo_df() -> pd.DataFrame:
    try:
        ws   = _get_ws(ERGO_SHEET_NAME, ERGO_COLS)
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return pd.DataFrame(columns=ERGO_COLS)
        df = pd.DataFrame(rows[1:], columns=rows[0]).fillna("")
        for c in ERGO_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[ERGO_COLS]
    except Exception:
        return pd.DataFrame(columns=ERGO_COLS)


def save_ergo_df(df: pd.DataFrame):
    ws = _get_ws(ERGO_SHEET_NAME, ERGO_COLS)
    ws.clear()
    ws.update([ERGO_COLS] + df[ERGO_COLS].fillna("").astype(str).values.tolist())


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
def build_calorie_figure(df: pd.DataFrame, bmr_kcal: int = _bmr):
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
    cv = [bmr_kcal + e for e in ev]
    bv = [i - c for i, c in zip(iv, cv)]

    x, w = np.arange(len(dates)), 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(dates) * 1.4), 5), facecolor=p["bg"])
    ax.set_facecolor(p["panel"])

    # 棒グラフ（ラベルなし — 凡例をテキストのみにするため label 非設定）
    ax.bar(x - w / 2, iv, width=w, color=p["intake"],  zorder=3, alpha=0.82)
    ax.bar(x + w / 2, cv, width=w, color=p["consume"], zorder=3, alpha=0.82)

    # 棒の上に収支 (+/-) だけ表示
    for i, (a, b, c) in enumerate(zip(iv, cv, bv)):
        top   = max(a, b)
        color = p["pos"] if c >= 0 else p["neg"]
        ax.text(x[i], top + 15, f"{'+'if c>=0 else''}{c:.0f}",
                ha="center", va="bottom", fontsize=8, color=color, fontweight="bold", zorder=4)

    # 目標ライン
    ax.axhline(bmr_kcal, color=p["dim"], lw=1.2, ls="--", zorder=2)

    # 凡例を四角パッチなし・テキストのみで右上に表示
    ax.text(0.99, 0.97, f"■ 摂取", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color=p["intake"], fontweight="bold")
    ax.text(0.99, 0.91, f"■ 消費", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color=p["consume"], fontweight="bold")
    ax.text(0.99, 0.85, f"-- 目標 {bmr_kcal} kcal", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color=p["dim"])

    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=30, ha="right", color=p["text"], fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=p["text"])
    ax.tick_params(colors=p["dim"])
    ax.set_ylabel("kcal", color=p["dim"], fontsize=10)
    ax.spines[:].set_color(p["border"])
    ax.grid(axis="y", color=p["grid"], lw=0.6, zorder=1)
    ax.set_title("カロリー収支", color=p["head"], fontsize=14, pad=14, fontweight="bold")
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
        ax.text(0.99, 0.97, "── 体重",    transform=ax.transAxes,
                ha="right", va="top", fontsize=8, color=p["weight"], fontweight="bold")
        ax.text(0.99, 0.91, "-- 3日平均", transform=ax.transAxes,
                ha="right", va="top", fontsize=8, color="#7C3AED")
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# グラフ：エルゴ タイム推移
# ─────────────────────────────────────────────────────────────────────────────
def build_ergo_trend_figure(edf: pd.DataFrame, dist: int):
    p   = GP
    edf = edf.copy()
    edf["_sec"] = edf["トータルタイム"].apply(_time_to_sec)
    edf = edf.dropna(subset=["_sec"]).sort_values("日付").reset_index(drop=True)
    if edf.empty:
        return None

    dates = edf["日付"].tolist()
    secs  = edf["_sec"].tolist()
    x     = np.arange(len(dates))
    color = _ERGO_DIST_COLOR.get(str(dist), p["head"])

    fig, ax = plt.subplots(figsize=(max(6, len(dates) * 1.2), 4), facecolor=p["bg"])
    ax.set_facecolor(p["panel"])

    ax.plot(x, secs, color=color, lw=2.5, marker="o", markersize=9,
            markerfacecolor=color, markeredgecolor="white", markeredgewidth=2, zorder=3)
    ax.fill_between(x, secs, min(secs) - 5, color=color, alpha=0.12, zorder=2)

    for xi, s in zip(x, secs):
        ax.text(xi, s + 1, _sec_to_mmss(s), ha="center", va="bottom",
                fontsize=9, color=color, fontweight="bold")

    # Y軸を MM:SS 表記
    _mn, _mx = min(secs), max(secs)
    _range = max(_mx - _mn, 10)
    _step  = max(1, _range // 5)
    yticks = list(range(max(0, _mn - _step), _mx + _step * 2, _step))
    ax.set_yticks(yticks)
    ax.set_yticklabels([_sec_to_mmss(s) for s in yticks], color=p["text"], fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=30, ha="right", color=p["text"], fontsize=9)
    ax.set_ylabel("タイム", color=p["dim"], fontsize=10)
    ax.spines[:].set_color(p["border"])
    ax.grid(axis="y", color=p["grid"], lw=0.6, zorder=1)
    ax.set_title(f"エルゴ {dist}m タイム推移（↓ 速い）",
                 color=p["head"], fontsize=13, pad=12, fontweight="bold")
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# グラフ：エルゴ スプリット詳細
# ─────────────────────────────────────────────────────────────────────────────
def build_ergo_split_figure(row: pd.Series, dist: int):
    p             = GP
    active_splits = list(range(500, dist + 1, 500))
    labels        = [f"{d}m" for d in active_splits]
    color         = _ERGO_DIST_COLOR.get(str(dist), p["head"])
    rate_color    = "#F59E0B"

    times_sec, rates = [], []
    for d in active_splits:
        t = _time_to_sec(str(row.get(f"{d}m_タイム", "")))
        r_raw = str(row.get(f"{d}m_レート", "")).strip()
        times_sec.append(t)
        rates.append(int(r_raw) if r_raw.isdigit() and int(r_raw) > 0 else 0)

    has_times = any(t is not None and t > 0 for t in times_sec)
    has_rates = any(r > 0 for r in rates)

    if not has_times and not has_rates:
        return None

    times_plot = [t if (t is not None and t > 0) else 0 for t in times_sec]
    x = np.arange(len(labels))

    nrows = 2 if (has_times and has_rates) else 1
    fig, axes = plt.subplots(nrows, 1,
                             figsize=(max(6, len(labels) * 1.3), 4 * nrows),
                             facecolor=p["bg"])
    if nrows == 1:
        axes = [axes]

    # ── スプリットタイム棒グラフ ──
    if has_times:
        ax1 = axes[0]
        ax1.set_facecolor(p["panel"])
        bars = ax1.bar(x, times_plot, color=color, alpha=0.82, zorder=3)
        for bar, t in zip(bars, times_sec):
            if t and t > 0:
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         _sec_to_mmss(t), ha="center", va="bottom",
                         fontsize=9, color=color, fontweight="bold")
        valid = [t for t in times_sec if t and t > 0]
        if valid:
            _mn, _mx = min(valid), max(valid)
            _r = max(_mx - _mn, 5)
            _s = max(1, _r // 4)
            yticks = list(range(max(0, _mn - _s), _mx + _s * 2, _s))
            ax1.set_yticks(yticks)
            ax1.set_yticklabels([_sec_to_mmss(s) for s in yticks],
                                color=p["text"], fontsize=9)
        ax1.set_xticks(x); ax1.set_xticklabels(labels, color=p["text"])
        ax1.set_ylabel("タイム (M:SS)", color=p["dim"])
        ax1.spines[:].set_color(p["border"])
        ax1.grid(axis="y", color=p["grid"], lw=0.6, zorder=1)
        ax1.set_title(f"{dist}m スプリット詳細（{row['日付']}）",
                      color=p["head"], fontsize=13, pad=12, fontweight="bold")

    # ── レート棒グラフ ──
    if has_rates:
        ax2 = axes[-1]
        ax2.set_facecolor(p["panel"])
        rbars = ax2.bar(x, rates, color=rate_color, alpha=0.82, zorder=3)
        for bar, r in zip(rbars, rates):
            if r > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                         str(r), ha="center", va="bottom",
                         fontsize=9, color=rate_color, fontweight="bold")
        ax2.set_xticks(x); ax2.set_xticklabels(labels, color=p["text"])
        ax2.set_ylabel("レート (SPM)", color=p["dim"])
        ax2.yaxis.set_tick_params(labelcolor=p["text"])
        ax2.spines[:].set_color(p["border"])
        ax2.grid(axis="y", color=p["grid"], lw=0.6, zorder=1)
        if not has_times:
            ax2.set_title(f"{dist}m レート詳細（{row['日付']}）",
                          color=p["head"], fontsize=13, pad=12, fontweight="bold")

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Calolie", page_icon="🌿",
                   layout="wide", initial_sidebar_state="collapsed")

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
for _k, _v in [("df", None), ("wdf", None), ("cdf", None), ("ergo_df", None),
               ("fv", 0), ("wfv", 0), ("ergofv", 0), ("ss_saved", False),
               ("settings", None), ("dialog_init", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.df is None:
    st.session_state.df = load_df()
if st.session_state.wdf is None:
    st.session_state.wdf = load_weight_df()
if st.session_state.settings is None:
    st.session_state.settings = load_settings()
if st.session_state.cdf is None:
    st.session_state.cdf = load_cond_df()
if st.session_state.ergo_df is None:
    st.session_state.ergo_df = load_ergo_df()

_bmr = int(st.session_state.settings.get("目標カロリー", str(_bmr)))
fv     = st.session_state.fv
wfv    = st.session_state.wfv
ergofv = st.session_state.ergofv
if f"nutr_{fv}" not in st.session_state:
    st.session_state[f"nutr_{fv}"] = _nutr(_DFLT_FOOD)


# ─── コールバック ─────────────────────────────────────────────────────────────
def _on_food_search():
    """検索テキスト変更時: プリセット＋過去の記録から候補を更新"""
    text = st.session_state.get(f"w_food_text_{fv}", "")
    if not text:
        st.session_state[f"food_matches_{fv}"] = []
        st.session_state[f"food_sel_{fv}"]     = ""
        st.session_state[f"nutr_{fv}"]         = _nutr("")
        st.session_state[f"w_kcal_{fv}"]       = 0
        return
    q = text.lower()
    # プリセット候補
    preset_hits = [k for k in FOOD_OPTIONS if q in k.lower()]
    # 過去の記録候補（📝 プレフィックスで区別）
    past_hits   = [f"📝 {k}" for k in _past_foods if q in k.lower()]
    st.session_state[f"food_matches_{fv}"] = preset_hits + past_hits
    st.session_state[f"food_sel_{fv}"]     = ""
    st.session_state[f"nutr_{fv}"]         = _nutr("")
    st.session_state[f"w_kcal_{fv}"]       = 0


def _on_food_select():
    """候補セレクトボックス変更時: プリセット or 過去の記録からkcalを補完"""
    chosen = st.session_state.get(f"w_food_preset_{fv}", "")
    # 過去の記録（📝 プレフィックスを除去して実際の食品名を取得）
    actual = chosen.removeprefix("📝 ") if chosen.startswith("📝 ") else chosen
    if actual in NUTRITION:
        st.session_state[f"food_sel_{fv}"] = actual
        st.session_state[f"w_kcal_{fv}"]   = NUTRITION[actual]["kcal"]
        st.session_state[f"nutr_{fv}"]     = _nutr(actual)
    elif actual in _past_foods:
        st.session_state[f"food_sel_{fv}"] = actual
        st.session_state[f"w_kcal_{fv}"]   = _past_foods[actual]
        st.session_state[f"nutr_{fv}"]     = _nutr("")  # 栄養素データなし
    else:
        st.session_state[f"food_sel_{fv}"] = ""


def _on_kcal():
    kcal = st.session_state.get(f"w_kcal_{fv}", 0) or 0
    food = (st.session_state.get(f"food_sel_{fv}", "")
            or st.session_state.get(f"w_food_text_{fv}", ""))
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
cdf = st.session_state.cdf

# ── 過去の記録から食品名→平均kcalを構築（プリセットにないものだけ） ─────────
_past_foods: dict[str, int] = {}
if df is not None and not df.empty:
    _pi = df[df["種別"] == "摂取"].copy()
    _pi["カロリー(kcal)"] = pd.to_numeric(_pi["カロリー(kcal)"], errors="coerce")
    _pi = _pi[(_pi["食べ物"].str.strip() != "") & (_pi["カロリー(kcal)"] > 0)]
    if not _pi.empty:
        _past_foods = {
            k: int(v)
            for k, v in _pi.groupby("食べ物")["カロリー(kcal)"].mean().round().items()
            if k not in NUTRITION
        }


# ─────────────────────────────────────────────────────────────────────────────
# 入力ダイアログ
# ─────────────────────────────────────────────────────────────────────────────
@st.dialog("📝 食事・運動を記録する", width="large")
def _input_dialog():
    _fv = st.session_state.fv

    kind_raw = st.radio("種別", ["🍽️ 食事（摂取）", "🏃 運動（消費）"],
                         horizontal=True, key=f"w_kind_{_fv}")
    kind_val = "摂取" if "摂取" in kind_raw else "消費"

    # 日付
    _today = _date.today()
    _dc1, _dc2 = st.columns([1, 1])
    with _dc1:
        _use_today = st.checkbox(
            f"📅 今日（{_today.strftime('%m/%d')}）",
            value=True, key=f"w_use_today_{_fv}"
        )
    if not _use_today:
        with _dc2:
            st.date_input("別の日付", value=_today, key=f"w_date_{_fv}",
                          label_visibility="collapsed")

    if kind_val == "摂取":
        st.selectbox("🕐 タイミング", MEAL_TIMES, key=f"w_meal_{_fv}")

        st.markdown("**食べ物を検索**")
        for _k, _v in [(f"food_sel_{_fv}", ""), (f"food_matches_{_fv}", [])]:
            if _k not in st.session_state:
                st.session_state[_k] = _v
        if f"w_kcal_{_fv}" not in st.session_state:
            st.session_state[f"w_kcal_{_fv}"] = 0

        st.text_input(
            "食べ物を検索", placeholder="バナナ、鶏むね肉など…",
            key=f"w_food_text_{_fv}", label_visibility="collapsed",
            on_change=_on_food_search,
        )

        matches = st.session_state.get(f"food_matches_{_fv}", [])
        if matches:
            options = ["── 選択してください ──"] + matches
            if f"w_food_preset_{_fv}" not in st.session_state:
                st.session_state[f"w_food_preset_{_fv}"] = options[0]
            st.selectbox(
                "候補", options=options,
                key=f"w_food_preset_{_fv}", label_visibility="collapsed",
                on_change=_on_food_select,
            )

        sel       = st.session_state.get(f"food_sel_{_fv}", "")
        food_text = st.session_state.get(f"w_food_text_{_fv}", "")
        if sel:
            _is_past = sel not in NUTRITION and sel in _past_foods
            _badge   = "📝 履歴" if _is_past else "✅ プリセット"
            _color   = "#EDE9FE" if _is_past else "#D1FAE5"
            _tcolor  = "#5B21B6" if _is_past else "#065F46"
            st.markdown(
                f'<div style="background:{_color};border-radius:8px;padding:6px 12px;'
                f'font-size:.84rem;font-weight:700;color:{_tcolor};margin:4px 0">'
                f'{_badge} {sel}</div>',
                unsafe_allow_html=True)

        food_save = sel if sel else food_text
        is_preset = food_save in NUTRITION
        is_custom = bool(food_save) and not is_preset

        # ご飯追加チェックボックス
        _add_rice = False
        if food_save:
            _add_rice = st.checkbox(
                f"🍚 ご飯を追加（+{_RICE_ADD['kcal']} kcal）",
                key=f"w_add_rice_{_fv}",
            )

        st.number_input("🔥 カロリー (kcal)",
                         min_value=0, step=5, key=f"w_kcal_{_fv}", on_change=_on_kcal)

        nutr = st.session_state[f"nutr_{_fv}"]
        if is_custom:
            for _k, _v in [(f"w_np_{_fv}",  float(nutr["protein"])),
                           (f"w_nf_{_fv}",  float(nutr["fat"])),
                           (f"w_nc_{_fv}",  float(nutr["carbs"])),
                           (f"w_nfi_{_fv}", float(nutr["fiber"]))]:
                if _k not in st.session_state:
                    st.session_state[_k] = _v
            st.markdown("**栄養素（手動入力）**")
            _n1, _n2 = st.columns(2)
            with _n1:
                st.number_input("タンパク質 g", min_value=0.0, step=0.1, key=f"w_np_{_fv}")
                st.number_input("炭水化物 g",   min_value=0.0, step=0.1, key=f"w_nc_{_fv}")
            with _n2:
                st.number_input("脂質 g",     min_value=0.0, step=0.1, key=f"w_nf_{_fv}")
                st.number_input("食物繊維 g", min_value=0.0, step=0.1, key=f"w_nfi_{_fv}")
        elif is_preset:
            _n1, _n2, _n3, _n4 = st.columns(4)
            _n1.metric("🥩 タンパク質", f"{nutr['protein']} g")
            _n2.metric("🧈 脂質",       f"{nutr['fat']} g")
            _n3.metric("🍚 炭水化物",   f"{nutr['carbs']} g")
            _n4.metric("🥦 食物繊維",   f"{nutr['fiber']} g")

    else:  # 消費
        st.selectbox("🏋️ 活動", ACTIVITY_TYPES,
                      key=f"w_activity_{_fv}", on_change=_on_activity)
        st.text_input("📝 メモ（任意）", placeholder="公園で実施など",
                       key=f"w_memo_{_fv}")
        if f"w_kcal_{_fv}" not in st.session_state:
            st.session_state[f"w_kcal_{_fv}"] = ACTIVITY_KCAL[ACTIVITY_TYPES[0]]
        st.number_input("🔥 カロリー (kcal)", min_value=0, step=5, key=f"w_kcal_{_fv}")

    st.divider()
    if st.button("✨ 保存する", use_container_width=True, type="primary",
                 key=f"dialog_save_{_fv}"):
        kcal_now  = st.session_state.get(f"w_kcal_{_fv}", 0) or 0
        _sel      = st.session_state.get(f"food_sel_{_fv}", "")
        _txt      = st.session_state.get(f"w_food_text_{_fv}", "")
        food_save = _sel if _sel else _txt
        act_sel   = st.session_state.get(f"w_activity_{_fv}", ACTIVITY_TYPES[0])
        memo      = st.session_state.get(f"w_memo_{_fv}", "")
        if st.session_state.get(f"w_use_today_{_fv}", True):
            date_val = _date.today()
        else:
            date_val = st.session_state.get(f"w_date_{_fv}", _date.today())
        meal_val = st.session_state.get(f"w_meal_{_fv}", MEAL_TIMES[0])
        nutr_now = st.session_state[f"nutr_{_fv}"]
        is_c     = food_save not in NUTRITION

        err = None
        if kind_val == "摂取" and not food_save:
            err = "食べ物名を入力してください。"
        elif kcal_now <= 0:
            err = "カロリーを入力してください。"

        if err:
            st.error(err)
        else:
            _add_rice = st.session_state.get(f"w_add_rice_{_fv}", False)
            _re = _RICE_ADD if _add_rice else {k: 0 for k in _RICE_ADD}
            if kind_val == "摂取":
                _p  = float(st.session_state.get(f"w_np_{_fv}",  nutr_now["protein"]) if is_c else nutr_now["protein"])
                _f  = float(st.session_state.get(f"w_nf_{_fv}",  nutr_now["fat"])     if is_c else nutr_now["fat"])
                _c  = float(st.session_state.get(f"w_nc_{_fv}",  nutr_now["carbs"])   if is_c else nutr_now["carbs"])
                _fi = float(st.session_state.get(f"w_nfi_{_fv}", nutr_now["fiber"])   if is_c else nutr_now["fiber"])
                row = {
                    "日付": str(date_val), "種別": "摂取",
                    "食事": meal_val,
                    "食べ物": food_save + ("＋ご飯" if _add_rice else ""),
                    "カロリー(kcal)": str(kcal_now + _re["kcal"]),
                    "タンパク質(g)": str(round(_p  + _re["protein"], 1)),
                    "脂質(g)":       str(round(_f  + _re["fat"],     1)),
                    "炭水化物(g)":   str(round(_c  + _re["carbs"],   1)),
                    "食物繊維(g)":   str(round(_fi + _re["fiber"],   1)),
                }
            else:
                row = {
                    "日付": str(date_val), "種別": "消費",
                    "食事": act_sel, "食べ物": memo or act_sel,
                    "カロリー(kcal)": str(kcal_now),
                    "タンパク質(g)": "0", "脂質(g)": "0",
                    "炭水化物(g)": "0", "食物繊維(g)": "0",
                }
            updated = pd.concat([st.session_state.df, pd.DataFrame([row])],
                                 ignore_index=True)
            save_df(updated)
            st.session_state.df = updated
            st.toast("✅ 保存しました！", icon="🌿")
            st.session_state.fv += 1
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# サイドバー（設定のみ）
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="grad-title">🌿 Calolie</p>', unsafe_allow_html=True)
    st.divider()
    with st.expander("⚙️ 目標カロリーを設定"):
        _cur = int(st.session_state.settings.get("目標カロリー", str(_bmr)))
        _new = st.number_input(
            "基礎代謝 / 目標摂取カロリー (kcal)",
            min_value=1000, max_value=5000, step=10, value=_cur,
            help="消費カロリー = この値 + 運動消費。デフォルト 1630 kcal",
        )
        if st.button("設定を保存", key="save_settings_btn"):
            st.session_state.settings["目標カロリー"] = str(_new)
            save_settings(st.session_state.settings)
            st.session_state.settings = load_settings()
            st.toast(f"✅ 目標カロリーを {_new} kcal に設定しました", icon="⚙️")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# メインエリア
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  background: linear-gradient(135deg, #059669 0%, #7C3AED 100%);
  border-radius: 20px;
  padding: 28px 32px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 24px rgba(5,150,105,0.18);
">
  <div style="font-size:2.2rem;font-weight:900;color:#fff;letter-spacing:.02em;line-height:1.15;">
    🌿 Calolie
  </div>
  <div style="color:rgba(255,255,255,0.82);font-size:.88rem;margin-top:6px;font-weight:500;">
    食事・運動・体重・栄養をまとめて管理 — なりたい自分をデザインしよう ✨
  </div>
</div>
""", unsafe_allow_html=True)

# ── ダイアログ自動オープン（初回のみ）＋ 記録ボタン ─────────────────────────
if not st.session_state.dialog_init:
    st.session_state.dialog_init = True
    st.session_state.show_input_dialog = True

_btn_c1, _btn_c2, _btn_c3 = st.columns([1, 2, 1])
with _btn_c2:
    if st.button("➕ 食事・運動を記録する", type="primary",
                 use_container_width=True, key="open_dialog_btn"):
        st.session_state.show_input_dialog = True

if st.session_state.pop("show_input_dialog", False):
    _input_dialog()

tab_bal, tab_log, tab_weight, tab_nutr, tab_graph, tab_ergo = st.tabs(
    ["📊 収支", "📝 記録・編集", "⚖️ 体重", "🧬 栄養素", "📈 グラフ", "🚣 エルゴ"])

today_str = str(_date.today())


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: 収支
# ─────────────────────────────────────────────────────────────────────────────
with tab_bal:
    all_dates = sorted(df["日付"].unique(), reverse=True)

    if not all_dates:
        st.markdown("""
<div style="text-align:center;padding:48px 24px;">
  <div style="font-size:3rem;margin-bottom:12px;">🌱</div>
  <div style="font-size:1.1rem;font-weight:700;color:#059669;margin-bottom:8px;">
    まだ記録がありません
  </div>
  <div style="color:#6B7280;font-size:.88rem;">
    左のサイドバーから食事・運動を記録してみましょう！
  </div>
</div>""", unsafe_allow_html=True)
    else:
        def_i = all_dates.index(today_str) if today_str in all_dates else 0
        sel   = st.selectbox("📅 日付", all_dates, index=def_i, key="bal_date")

        day = df[df["日付"] == sel].copy()
        day["カロリー(kcal)"] = pd.to_numeric(day["カロリー(kcal)"], errors="coerce").fillna(0)

        intake_k   = day[day["種別"] == "摂取"]["カロリー(kcal)"].sum()
        exercise_k = day[day["種別"] == "消費"]["カロリー(kcal)"].sum()
        consume_k  = _bmr + exercise_k
        balance    = intake_k - consume_k
        sign       = "+" if balance >= 0 else ""

        m1, m2, m3 = st.columns(3)
        m1.metric("🍽️ 摂取カロリー", f"{intake_k:,.0f} kcal")
        m2.metric("🔥 消費カロリー",  f"{consume_k:,.0f} kcal",
                  f"目標 {_bmr:,} + 運動 {exercise_k:,.0f}")
        m3.metric("⚖️ 今日の収支",   f"{sign}{balance:,.0f} kcal")

        # ── 食事別カロリー小計 ─────────────────────────────────────────────
        st.write("")
        st.markdown('<p class="sec-head">🕐 食事別カロリー内訳</p>', unsafe_allow_html=True)
        _intake_day  = day[day["種別"] == "摂取"]
        _meal_totals = _intake_day.groupby("食事")["カロリー(kcal)"].sum()
        _mcols       = st.columns(len(MEAL_TIMES))
        for _i, _meal in enumerate(MEAL_TIMES):
            _mk = _meal_totals.get(_meal, 0)
            with _mcols[_i]:
                st.markdown(
                    f'<div style="background:#FFF;border-radius:12px;padding:10px 8px;'
                    f'text-align:center;border:1px solid #D1FAE5;box-shadow:0 1px 4px rgba(5,150,105,.08)">'
                    f'<div style="font-size:.72rem;font-weight:700;color:#6B7280;letter-spacing:.06em">{_meal}</div>'
                    f'<div style="font-size:1.1rem;font-weight:800;color:{"#059669" if _mk>0 else "#9CA3AF"};margin-top:2px">'
                    f'{_mk:,.0f}</div>'
                    f'<div style="font-size:.65rem;color:#9CA3AF">kcal</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

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

        # ── コンディション入力 ────────────────────────────────────────────────
        st.divider()
        st.markdown('<p class="sec-head">💭 今日のコンディション</p>', unsafe_allow_html=True)

        _cdf        = st.session_state.cdf
        _cond_row   = _cdf[_cdf["日付"] == sel]
        _cur_score  = int(_cond_row["コンディション"].values[0]) if not _cond_row.empty else 0

        # 5つのワンタップボタン
        _btn_cols = st.columns(5)
        for _s in range(1, 6):
            _selected = (_s == _cur_score)
            _label    = f"{COND_EMOJI[_s]}\n{COND_LABEL[_s]}"
            if _btn_cols[_s - 1].button(
                _label, key=f"cond_{_s}_{sel}",
                use_container_width=True,
                type="primary" if _selected else "secondary",
            ):
                _new_row  = pd.DataFrame([{"日付": sel, "コンディション": str(_s), "メモ": ""}])
                _updated  = pd.concat([_cdf[_cdf["日付"] != sel], _new_row], ignore_index=True)
                save_cond_df(_updated)
                st.session_state.cdf = _updated
                st.rerun()

        if _cur_score:
            st.caption(f"記録済: {COND_EMOJI[_cur_score]} {COND_LABEL[_cur_score]}")

        # ── 過去7日間の傾向 ───────────────────────────────────────────────────
        with st.expander("📈 過去7日間の傾向（コンディション × カロリー収支）"):
            _cutoff7 = (pd.Timestamp(today_str) - pd.Timedelta(days=6)).strftime("%Y-%m-%d")
            _cdf7    = _cdf[_cdf["日付"] >= _cutoff7].copy()
            _cdf7["コンディション"] = pd.to_numeric(_cdf7["コンディション"], errors="coerce")

            _dates7  = [(pd.Timestamp(today_str) - pd.Timedelta(days=i)).strftime("%Y-%m-%d")
                        for i in range(6, -1, -1)]

            _rows7 = []
            for _d in _dates7:
                _c  = _cdf7[_cdf7["日付"] == _d]["コンディション"].values
                _dk = df[df["日付"] == _d].copy()
                _dk["カロリー(kcal)"] = pd.to_numeric(_dk["カロリー(kcal)"], errors="coerce").fillna(0)
                _ik = _dk[_dk["種別"] == "摂取"]["カロリー(kcal)"].sum()
                _ek = _dk[_dk["種別"] == "消費"]["カロリー(kcal)"].sum()
                _bk = _ik - (_bmr + _ek)
                _rows7.append({
                    "日付":      _d[5:],  # MM-DD
                    "コンディション": (f"{COND_EMOJI[int(_c[0])]} {COND_LABEL[int(_c[0])]}"
                                   if len(_c) > 0 and not pd.isna(_c[0]) else "—"),
                    "収支(kcal)": f"{'+' if _bk >= 0 else ''}{_bk:,.0f}" if _ik > 0 else "—",
                })

            st.dataframe(
                pd.DataFrame(_rows7),
                use_container_width=True, hide_index=True,
            )


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
    _w_saved = st.session_state.pop("weight_saved", False)
    with st.expander("➕ 体重を記録する", expanded=(wdf.empty and not _w_saved)):
        with st.form(f"weight_form_{wfv}"):
            wc1, wc2 = st.columns([1, 2])
            with wc1:
                w_date = st.date_input("📅 日付", value=_date.today(), key=f"wf_date_{wfv}")
            with wc2:
                # 直近の体重を初期値に（フォームリセット後は55.0に戻す）
                _wkg_key = f"wf_kg_{wfv}"
                if _wkg_key not in st.session_state:
                    last_w = 55.0
                    if not wdf.empty:
                        tmp = wdf.copy()
                        tmp["体重(kg)"] = pd.to_numeric(tmp["体重(kg)"], errors="coerce")
                        tmp = tmp.dropna(subset=["体重(kg)"])
                        if not tmp.empty:
                            last_w = float(tmp.sort_values("日付").iloc[-1]["体重(kg)"])
                    st.session_state[_wkg_key] = last_w
                w_kg = st.number_input("⚖️ 体重 (kg)", min_value=20.0, max_value=250.0,
                                        step=0.1, format="%.1f", key=_wkg_key)
            w_memo = st.text_input("📝 メモ（任意）", placeholder="例: 朝起床後・食前",
                                   key=f"wf_memo_{wfv}")
            if st.form_submit_button("記録する", type="primary", use_container_width=True):
                new_w = pd.DataFrame([{
                    "日付": str(w_date), "体重(kg)": str(w_kg), "メモ": w_memo
                }])
                updated_w = pd.concat([wdf, new_w], ignore_index=True)
                save_weight_df(updated_w)
                st.session_state.wdf = updated_w
                wdf = updated_w
                st.toast(f"✅ {w_kg:.1f} kg を記録しました！", icon="⚖️")
                st.session_state.weight_saved = True
                st.session_state.wfv += 1
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
    fig = build_calorie_figure(df, bmr_kcal=_bmr)
    if fig is None:
        st.info("記録がありません。上の「➕ 食事・運動を記録する」から追加してください 🌿")
    else:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 6: エルゴ
# ─────────────────────────────────────────────────────────────────────────────
with tab_ergo:
    ergodf  = st.session_state.ergo_df
    _efv    = st.session_state.ergofv
    _e_saved = st.session_state.pop("ergo_saved", False)

    # ── 入力フォーム ──────────────────────────────────────────────────────────
    with st.expander("➕ エルゴを記録する",
                     expanded=(ergodf.empty and not _e_saved)):

        # 距離はフォーム外（変更で即リレンダー）
        _edist = st.selectbox(
            "🚣 距離", ERGO_DISTANCES,
            index=ERGO_DISTANCES.index(3000),
            key=f"ergo_dist_{_efv}",
        )
        _active_splits = list(range(500, _edist + 1, 500))

        with st.form(f"ergo_form_{_efv}"):
            _ec1, _ec2 = st.columns(2)
            with _ec1:
                _edate = st.date_input("📅 日付", value=_date.today(),
                                       key=f"ergo_date_{_efv}")
            with _ec2:
                _etotal = st.text_input(
                    "⏱️ トータルタイム (M:SS)",
                    placeholder="例: 12:30",
                    key=f"ergo_total_{_efv}",
                )

            st.markdown("**500m ごとのスプリット**")
            _hc1, _hc2, _hc3 = st.columns([1, 2, 1])
            _hc1.markdown("**区間**")
            _hc2.markdown("**タイム (M:SS)**")
            _hc3.markdown("**レート (SPM)**")

            _splits_data = []
            for _sd in _active_splits:
                _rc1, _rc2, _rc3 = st.columns([1, 2, 1])
                with _rc1:
                    st.markdown(f"**{_sd}m**")
                with _rc2:
                    _t = st.text_input(
                        "タイム", placeholder="1:55",
                        label_visibility="collapsed",
                        key=f"ergo_t_{_sd}_{_efv}",
                    )
                with _rc3:
                    _r = st.number_input(
                        "レート", min_value=0, max_value=50, step=1,
                        value=0, label_visibility="collapsed",
                        key=f"ergo_r_{_sd}_{_efv}",
                    )
                _splits_data.append((_sd, _t, _r))

            _ememo = st.text_input("📝 メモ（任意）",
                                   placeholder="例: レート17で統一",
                                   key=f"ergo_memo_{_efv}")

            if st.form_submit_button("記録する", type="primary",
                                     use_container_width=True):
                # トータルタイム未入力 → スプリット合計で計算
                _total_sec = _time_to_sec(_etotal)
                if _total_sec is None:
                    _sum = sum(
                        _time_to_sec(_t) or 0
                        for _, _t, _ in _splits_data
                    )
                    _etotal_save = _sec_to_mmss(_sum) if _sum > 0 else ""
                else:
                    _etotal_save = _etotal.strip()

                if not _etotal_save and not any(_t for _, _t, _ in _splits_data):
                    st.error("タイムを入力してください。")
                else:
                    _erow = {c: "" for c in ERGO_COLS}
                    _erow["日付"]           = str(_edate)
                    _erow["距離(m)"]        = str(_edist)
                    _erow["トータルタイム"] = _etotal_save
                    _erow["メモ"]           = _ememo
                    for _sd, _t, _r in _splits_data:
                        _erow[f"{_sd}m_タイム"] = _t
                        _erow[f"{_sd}m_レート"] = str(_r) if _r > 0 else ""
                    updated_e = pd.concat(
                        [ergodf, pd.DataFrame([_erow])], ignore_index=True
                    )
                    save_ergo_df(updated_e)
                    st.session_state.ergo_df = updated_e
                    st.toast("✅ エルゴ記録を保存しました！", icon="🚣")
                    st.session_state.ergo_saved = True
                    st.session_state.ergofv += 1
                    st.rerun()

    # ── 記録一覧 ──────────────────────────────────────────────────────────────
    if ergodf.empty:
        st.info("まだエルゴの記録がありません。上のフォームから追加してください 🚣")
    else:
        st.markdown("### 📋 記録一覧")
        _disp = ergodf[["日付", "距離(m)", "トータルタイム", "メモ"]].copy()
        _disp.index = range(1, len(_disp) + 1)
        st.dataframe(_disp, use_container_width=True)

        with st.expander("🗑️ エルゴ記録を削除する"):
            _del_opts = [
                f"{r['日付']} — {r['距離(m)']}m — {r['トータルタイム']}"
                for _, r in ergodf.iterrows()
            ]
            _di_e = st.selectbox("削除する行", range(len(_del_opts)),
                                  format_func=lambda i: _del_opts[i],
                                  key="del_ergo")
            if st.button("削除", type="secondary", key="del_ergo_btn"):
                _upd_e = ergodf.drop(index=_di_e).reset_index(drop=True)
                save_ergo_df(_upd_e)
                st.session_state.ergo_df = _upd_e
                st.success("削除しました。")
                st.rerun()

        # ── グラフ ────────────────────────────────────────────────────────────
        st.markdown("### 📈 グラフ")
        _edist_filter = st.selectbox(
            "距離でフィルタ", ERGO_DISTANCES,
            index=ERGO_DISTANCES.index(3000),
            key="ergo_graph_dist",
            format_func=lambda d: f"{d}m",
        )
        _esub = ergodf[ergodf["距離(m)"] == str(_edist_filter)].copy()

        if _esub.empty:
            st.info(f"{_edist_filter}m の記録がまだありません。")
        else:
            # タイム推移グラフ
            _fig_trend = build_ergo_trend_figure(_esub, _edist_filter)
            if _fig_trend:
                st.pyplot(_fig_trend, use_container_width=True)
                plt.close(_fig_trend)

            # スプリット詳細グラフ
            st.markdown("**スプリット詳細**")
            _sess_labels = [
                f"{r['日付']}  {r['トータルタイム']}"
                for _, r in _esub.reset_index(drop=True).iterrows()
            ]
            _sel_sess = st.selectbox(
                "セッションを選択", range(len(_sess_labels)),
                format_func=lambda i: _sess_labels[i],
                index=len(_sess_labels) - 1,
                key="ergo_split_sess",
            )
            _fig_split = build_ergo_split_figure(
                _esub.reset_index(drop=True).iloc[_sel_sess], _edist_filter
            )
            if _fig_split:
                st.pyplot(_fig_split, use_container_width=True)
                plt.close(_fig_split)
            else:
                st.info("スプリットデータがありません。記録時に入力してください。")
