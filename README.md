# Calolie — カロリー記録アプリ

古代ローマをテーマにしたダークスタイルのカロリートラッカーです。  
食事の摂取カロリーと運動による消費カロリーを記録し、日ごとの収支をグラフで確認できます。  
**スマートフォンのブラウザからも利用できます。**

## 機能

- 食事（朝・昼・夜・間食）のカロリーを記録
- よく食べるもののカロリーを自動補完
- 運動プリセット（ランニング・フットサル・エルゴ・筋トレ・ヨガ）
- 基礎代謝（1,630 kcal）を自動加算した消費カロリー計算
- 日付ごとの摂取/消費収支パネル
- グループ化された記録一覧（摂取 / 消費セクション）
- 摂取 vs 消費のグループ棒グラフ

---

## Streamlit Web アプリ（推奨・スマホ対応）

### ローカルで起動する

```bash
git clone https://github.com/gamegate604-ship-it/calolie-app.git
cd calolie-app

# uv で環境を構築（推奨）
uv sync
uv run streamlit run app.py
```

起動後、ブラウザで `http://localhost:8501` を開きます。  
同じ Wi-Fi 内のスマートフォンからは `http://<MacのIPアドレス>:8501` でアクセスできます。

### pip を使う場合

```bash
pip install streamlit matplotlib numpy pandas
streamlit run app.py
```

---

## Streamlit Cloud へのデプロイ（無料・外出先でも利用可能）

1. [share.streamlit.io](https://share.streamlit.io) にGitHubアカウントでログイン
2. **New app** → このリポジトリを選択 → Main file: `app.py` → **Deploy**
3. 発行されたURL（例: `https://calolie-app.streamlit.app`）をスマホのホーム画面に追加

---

## デスクトップアプリ（Tkinter）

```bash
uv run python food_log_gui.py
```

---

## 動作環境

- Python 3.11+
- streamlit, matplotlib, numpy, pandas

## ライセンス

MIT
