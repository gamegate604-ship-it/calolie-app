# Calolie — カロリー記録アプリ

古代ローマをテーマにしたダークスタイルのカロリートラッカーです。  
食事の摂取カロリーと運動による消費カロリーを記録し、日ごとの収支をグラフで確認できます。

## 機能

- 食事（朝・昼・夜・間食）のカロリーを記録
- よく食べるもののカロリーを自動補完
- 運動プリセット（ランニング・フットサル・エルゴ・筋トレ・ヨガ）
- 基礎代謝（1,630 kcal）を自動加算した消費カロリー計算
- 日付ごとの摂取/消費収支パネル
- グループ化された記録一覧（摂取 / 消費セクション）
- 摂取 vs 消費のグループ棒グラフ

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/gamegate604-ship-it/calolie-app.git
cd calolie-app

# uv で環境を構築（推奨）
uv sync

# 起動
uv run python food_log_gui.py
```

### pip を使う場合

```bash
pip install matplotlib numpy
python food_log_gui.py
```

## グラフ表示

アプリ内の **グラフ** ボタン、またはコマンドラインから:

```bash
uv run python calorie_graph.py
```

## 動作環境

- Python 3.11+
- Tkinter（標準ライブラリ）
- matplotlib, numpy

## ライセンス

MIT
