"""Calolie App — Ancient-Rome dark-themed calorie tracker."""
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date as _date
import subprocess
import sys
import os

# ── CSV ──────────────────────────────────────────────────────────────────────
CSV_FILE = "food_log.csv"
FIELDNAMES = ["日付", "種別", "食事", "食べ物", "カロリー(kcal)"]
DISPLAY_COLS = ["日付", "食事", "食べ物", "カロリー(kcal)"]

# ── Choices ───────────────────────────────────────────────────────────────────
MEAL_TIMES = ["朝", "昼", "夜", "間食"]
ACTIVITY_TYPES = ["ランニング20分", "フットサル1時間", "エルゴ2000m", "自重筋トレ20分", "ヨガ20分"]
ACTIVITY_KCAL = {
    "ランニング20分": 200,
    "フットサル1時間": 600,
    "エルゴ2000m": 120,
    "自重筋トレ20分": 100,
    "ヨガ20分": 60,
}
FOOD_KCAL = {
    "バナナ": 90,
    "カレー": 700,
    "うどん": 300,
    "定食": 650,
    "ご飯": 270,
    "パン": 250,
    "サラダ": 80,
    "ラーメン": 500,
    "パスタ": 450,
    "チキン": 300,
    "卵": 90,
    "ヨーグルト": 100,
    "牛乳": 130,
    "おにぎり": 180,
    "サンドイッチ": 350,
    "ハンバーガー": 550,
    "コーヒー": 5,
    "ジュース": 120,
}
BMR_KCAL = 1630

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#1A1610"
BG_ENTRY = "#26201A"
BG_BTN   = "#38281C"
BG_SEL   = "#5C1818"
BG_ALT   = "#161210"
FG       = "#C8B48A"
FG_DIM   = "#7A6848"
FG_HEAD  = "#C8963C"
FG_CONS  = "#8ABD78"
ACCENT   = "#8B1A1A"
BORDER   = "#4A3C28"
COL_POS  = ACCENT
COL_NEG  = "#4A9B38"

FONT    = ("Georgia", 11)
FONT_B  = ("Georgia", 11, "bold")
FONT_SM = ("Georgia", 9)
FONT_NUM = ("Georgia", 18, "bold")
FONT_H1  = ("Georgia", 14, "bold")


# ── Helpers ──────────────────────────────────────────────────────────────────
def today_str() -> str:
    return _date.today().strftime("%Y-%m-%d")


def load_rows():
    if not os.path.exists(CSV_FILE):
        return []
    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(dict(r))
    return rows


def save_rows(rows):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore", restval="")
        writer.writeheader()
        for r in rows:
            if "種別" not in r:
                r = {"種別": "摂取", **r}
            writer.writerow(r)


def _make_btn(parent, text, command, padx=16, pady=8, font=None, small=False):
    b = tk.Button(
        parent, text=text, command=command,
        bg=BG_BTN, fg=FG,
        activebackground=ACCENT, activeforeground=FG,
        font=font or (FONT_SM if small else FONT_B),
        relief="flat", bd=0, padx=padx, pady=pady,
        cursor="hand2", highlightthickness=1, highlightbackground=BORDER,
    )
    b.bind("<Enter>", lambda *_a, w=b: w.config(bg=ACCENT, highlightbackground=FG_HEAD))
    b.bind("<Leave>", lambda *_a, w=b: w.config(bg=BG_BTN, highlightbackground=BORDER))
    return b


# ── Main App ─────────────────────────────────────────────────────────────────
class CalorieApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calolie — カロリー記録")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(900, 600)

        self._rows: list[dict] = load_rows()
        self._sort_asc = True
        self._type_var = tk.StringVar(value="摂取")

        self._build_style()
        self._build_ui()
        self._refresh_table()
        self._refresh_balance()

    # ── Style ─────────────────────────────────────────────────────────────────
    def _build_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG, font=FONT)
        s.configure("TCombobox",
            fieldbackground=BG_ENTRY, background=BG_ENTRY,
            foreground=FG, selectbackground=BG_SEL, selectforeground=FG,
            arrowcolor=FG_HEAD, font=FONT)
        s.map("TCombobox",
            fieldbackground=[("readonly", BG_ENTRY)],
            foreground=[("readonly", FG)])
        s.configure("Treeview",
            background=BG_ALT, foreground=FG,
            fieldbackground=BG_ALT, rowheight=28,
            font=FONT, borderwidth=0)
        s.configure("Treeview.Heading",
            background=BG_BTN, foreground=FG_HEAD,
            font=FONT_B, relief="flat")
        s.map("Treeview",
            background=[("selected", BG_SEL)],
            foreground=[("selected", FG)])
        s.configure("TSeparator", background=BORDER)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Left panel (form + balance) ──
        left = tk.Frame(self, bg=BG, padx=16, pady=16)
        left.pack(side="left", fill="y")

        self._build_form(left)
        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=12)
        self._build_balance(left)

        # ── Right panel (table) ──
        right = tk.Frame(self, bg=BG, padx=8, pady=16)
        right.pack(side="left", fill="both", expand=True)
        self._build_table(right)

    # ── Form ──────────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        tk.Label(parent, text="記録を追加", font=FONT_H1, bg=BG, fg=FG_HEAD).pack(anchor="w", pady=(0, 8))

        # Type toggle
        type_fr = tk.Frame(parent, bg=BG)
        type_fr.pack(fill="x", pady=(0, 8))
        tk.Label(type_fr, text="種別", font=FONT_B, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 8))
        for val in ("摂取", "消費"):
            rb = tk.Radiobutton(
                type_fr, text=val, variable=self._type_var, value=val,
                command=self._on_type_changed,
                bg=BG, fg=FG, selectcolor=BG_SEL, activebackground=BG,
                activeforeground=FG_HEAD, font=FONT_B, cursor="hand2",
                indicatoron=True,
            )
            rb.pack(side="left", padx=4)

        # Date
        self._date_var = tk.StringVar(value=today_str())
        self._build_field(parent, "日付", self._date_var)

        # Meal time (摂取) / Activity (消費)
        self._meal_var = tk.StringVar(value=MEAL_TIMES[0])
        self._meal_label = tk.Label(parent, text="食事", font=FONT_B, bg=BG, fg=FG_DIM)
        self._meal_label.pack(anchor="w")
        self._meal_cb = ttk.Combobox(
            parent, textvariable=self._meal_var,
            values=MEAL_TIMES, state="readonly",
            width=28, font=FONT,
        )
        self._meal_cb.pack(fill="x", pady=(2, 8), ipady=4)
        self._meal_cb.bind("<<ComboboxSelected>>", self._on_meal_changed)

        # Food / Activity name
        self._food_var = tk.StringVar()
        self._food_var.trace_add("write", self._on_food_typed)
        self._food_label = tk.Label(parent, text="食べ物", font=FONT_B, bg=BG, fg=FG_DIM)
        self._food_label.pack(anchor="w")
        self._food_entry = tk.Entry(
            parent, textvariable=self._food_var,
            bg=BG_ENTRY, fg=FG, insertbackground=FG,
            font=FONT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=FG_HEAD,
        )
        self._food_entry.pack(fill="x", pady=(2, 2), ipady=6)

        # Autocomplete listbox
        self._ac_frame = tk.Frame(parent, bg=BORDER, bd=1, relief="flat")
        self._ac_list = tk.Listbox(
            self._ac_frame, bg=BG_ENTRY, fg=FG, font=FONT,
            selectbackground=BG_SEL, selectforeground=FG,
            relief="flat", bd=0, highlightthickness=0, activestyle="none",
            height=4,
        )
        self._ac_list.pack(fill="both", expand=True, padx=1, pady=1)
        self._ac_list.bind("<<ListboxSelect>>", self._on_ac_select)
        self._ac_list.bind("<Return>", self._on_ac_select)

        # Kcal
        self._kcal_var = tk.StringVar()
        self._build_field(parent, "カロリー (kcal)", self._kcal_var)

        # Buttons
        btn_fr = tk.Frame(parent, bg=BG)
        btn_fr.pack(fill="x", pady=(8, 0))
        _make_btn(btn_fr, "保存  ＋", self._on_save).pack(side="left", padx=(0, 8))
        _make_btn(btn_fr, "グラフ", self._on_graph, small=True).pack(side="left")

    def _build_field(self, parent, label, var):
        tk.Label(parent, text=label, font=FONT_B, bg=BG, fg=FG_DIM).pack(anchor="w")
        e = tk.Entry(
            parent, textvariable=var,
            bg=BG_ENTRY, fg=FG, insertbackground=FG,
            font=FONT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=FG_HEAD,
        )
        e.pack(fill="x", pady=(2, 8), ipady=6)
        return e

    # ── Balance Panel ──────────────────────────────────────────────────────────
    def _build_balance(self, parent):
        tk.Label(parent, text="カロリー収支", font=FONT_H1, bg=BG, fg=FG_HEAD).pack(anchor="w", pady=(0, 6))

        # Date selector
        date_fr = tk.Frame(parent, bg=BG)
        date_fr.pack(fill="x", pady=(0, 8))
        tk.Label(date_fr, text="日付", font=FONT_B, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 6))
        self._bal_date_var = tk.StringVar(value=today_str())
        self._bal_date_cb = ttk.Combobox(
            date_fr, textvariable=self._bal_date_var,
            state="readonly", width=14, font=FONT,
        )
        self._bal_date_cb.pack(side="left")
        self._bal_date_cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_balance())
        _make_btn(date_fr, "今日", self._go_today, padx=8, pady=4, small=True).pack(side="left", padx=(6, 0))

        # Numbers
        num_fr = tk.Frame(parent, bg=BG)
        num_fr.pack(fill="x")

        self._intake_lbl = tk.Label(num_fr, text="摂取: —", font=FONT_B, bg=BG, fg=FG)
        self._intake_lbl.pack(anchor="w")
        self._consume_lbl = tk.Label(num_fr, text="消費: —", font=FONT_B, bg=BG, fg=FG_CONS)
        self._consume_lbl.pack(anchor="w")
        self._consume_sub = tk.Label(num_fr, text="", font=FONT_SM, bg=BG, fg=FG_DIM)
        self._consume_sub.pack(anchor="w")

        self._balance_num = tk.Label(num_fr, text="±0 kcal", font=FONT_NUM, bg=BG, fg=FG)
        self._balance_num.pack(anchor="w", pady=(6, 0))
        self._balance_tag = tk.Label(num_fr, text="収支", font=FONT_SM, bg=BG, fg=FG_DIM)
        self._balance_tag.pack(anchor="w")

    # ── Table ─────────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        hdr_fr = tk.Frame(parent, bg=BG)
        hdr_fr.pack(fill="x", pady=(0, 6))
        tk.Label(hdr_fr, text="記録一覧", font=FONT_H1, bg=BG, fg=FG_HEAD).pack(side="left")

        btn_fr = tk.Frame(hdr_fr, bg=BG)
        btn_fr.pack(side="right")
        _make_btn(btn_fr, "日付 ↕", self._toggle_sort, padx=8, pady=4, small=True).pack(side="left", padx=4)
        _make_btn(btn_fr, "削除", self._on_delete, padx=8, pady=4, small=True).pack(side="left")

        tree_fr = tk.Frame(parent, bg=BG)
        tree_fr.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            tree_fr,
            columns=DISPLAY_COLS,
            show="tree headings",
            selectmode="extended",
        )
        self.tree.column("#0", width=120, anchor="w", stretch=False)
        col_w = {"日付": 100, "食事": 70, "食べ物": 160, "カロリー(kcal)": 100}
        for c in DISPLAY_COLS:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=col_w.get(c, 100), anchor="center")

        sb = ttk.Scrollbar(tree_fr, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Row tags
        self.tree.tag_configure("intake",  background=BG_ALT, foreground=FG)
        self.tree.tag_configure("expense", background="#130E0A", foreground=FG_CONS)
        self.tree.tag_configure("section", background=BG_BTN, foreground=FG_HEAD, font=FONT_B)

    # ── Events ────────────────────────────────────────────────────────────────
    def _on_type_changed(self):
        kind = self._type_var.get()
        if kind == "摂取":
            self._meal_label.config(text="食事")
            self._meal_cb.config(values=MEAL_TIMES, state="readonly")
            self._meal_var.set(MEAL_TIMES[0])
            self._food_label.config(text="食べ物")
            self._food_var.set("")
            self._kcal_var.set("")
        else:
            self._meal_label.config(text="活動")
            self._meal_cb.config(values=ACTIVITY_TYPES, state="readonly")
            self._food_label.config(text="活動メモ")
            self._food_var.set("")
            self._kcal_var.set("")
            self._meal_var.set(ACTIVITY_TYPES[0])
            self._kcal_var.set(str(ACTIVITY_KCAL[ACTIVITY_TYPES[0]]))

    def _on_meal_changed(self, _event=None):
        if self._type_var.get() == "消費":
            act = self._meal_var.get()
            if act in ACTIVITY_KCAL:
                self._kcal_var.set(str(ACTIVITY_KCAL[act]))

    def _on_food_typed(self, *_):
        if self._type_var.get() != "摂取":
            return
        q = self._food_var.get().strip()
        if not q:
            self._ac_frame.place_forget()
            return
        matches = [f for f in FOOD_KCAL if q in f]
        if matches:
            self._ac_list.delete(0, "end")
            for m in matches:
                self._ac_list.insert("end", m)
            x = self._food_entry.winfo_x()
            y = self._food_entry.winfo_y() + self._food_entry.winfo_height() + 2
            self._ac_frame.place(in_=self._food_entry.master,
                                  x=x, y=y,
                                  width=self._food_entry.winfo_width())
        else:
            self._ac_frame.place_forget()

    def _on_ac_select(self, _event=None):
        sel = self._ac_list.curselection()
        if not sel:
            return
        food = self._ac_list.get(sel[0])
        self._food_var.set(food)
        if food in FOOD_KCAL:
            self._kcal_var.set(str(FOOD_KCAL[food]))
        self._ac_frame.place_forget()

    def _on_save(self):
        d = self._date_var.get().strip()
        meal = self._meal_var.get().strip()
        food = self._food_var.get().strip()
        kcal = self._kcal_var.get().strip()
        kind = self._type_var.get()

        if not d or not food or not kcal:
            messagebox.showwarning("入力エラー", "日付・食べ物・カロリーを入力してください。")
            return
        try:
            float(kcal)
        except ValueError:
            messagebox.showwarning("入力エラー", "カロリーは数値で入力してください。")
            return

        self._rows.append({"日付": d, "種別": kind, "食事": meal, "食べ物": food, "カロリー(kcal)": kcal})
        save_rows(self._rows)
        self._food_var.set("")
        self._kcal_var.set("")
        self._refresh_table()
        self._refresh_balance()
        self._update_date_list()

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        # Collect row indices to delete (skip section headers)
        to_delete = set()
        for iid in sel:
            parent = self.tree.parent(iid)
            if parent in ("intake_section", "expense_section"):
                idx = self.tree.index(iid)
                # Map back to _rows
                kind = "摂取" if parent == "intake_section" else "消費"
                same_kind = [i for i, r in enumerate(self._rows) if r.get("種別", "摂取") == kind]
                if idx < len(same_kind):
                    to_delete.add(same_kind[idx])
            elif iid in ("intake_section", "expense_section"):
                # Delete all children
                kind = "摂取" if iid == "intake_section" else "消費"
                for i, r in enumerate(self._rows):
                    if r.get("種別", "摂取") == kind:
                        to_delete.add(i)
        self._rows = [r for i, r in enumerate(self._rows) if i not in to_delete]
        save_rows(self._rows)
        self._refresh_table()
        self._refresh_balance()
        self._update_date_list()

    def _on_graph(self):
        script = os.path.join(os.path.dirname(__file__), "calorie_graph.py")
        subprocess.Popen([sys.executable, script])

    def _toggle_sort(self):
        self._sort_asc = not self._sort_asc
        self._refresh_table()

    def _go_today(self):
        self._bal_date_var.set(today_str())
        self._refresh_balance()

    # ── Refresh ───────────────────────────────────────────────────────────────
    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        intake  = [r for r in self._rows if r.get("種別", "摂取") == "摂取"]
        expense = [r for r in self._rows if r.get("種別", "摂取") == "消費"]

        def sort_key(r):
            return r.get("日付", "")

        intake  = sorted(intake,  key=sort_key, reverse=not self._sort_asc)
        expense = sorted(expense, key=sort_key, reverse=not self._sort_asc)

        # Sections
        self.tree.insert("", "end", iid="intake_section",
                         text="▸ 摂取", values=["", "", "", ""], tags=("section",))
        for r in intake:
            self.tree.insert("intake_section", "end",
                             values=[r.get("日付",""), r.get("食事",""),
                                     r.get("食べ物",""), r.get("カロリー(kcal)","")],
                             tags=("intake",))

        self.tree.insert("", "end", iid="expense_section",
                         text="▸ 消費", values=["", "", "", ""], tags=("section",))
        for r in expense:
            self.tree.insert("expense_section", "end",
                             values=[r.get("日付",""), r.get("食事",""),
                                     r.get("食べ物",""), r.get("カロリー(kcal)","")],
                             tags=("expense",))

        self.tree.item("intake_section",  open=True)
        self.tree.item("expense_section", open=True)

    def _refresh_balance(self):
        d = self._bal_date_var.get()
        intake_v  = sum(float(r["カロリー(kcal)"]) for r in self._rows
                        if r.get("日付") == d and r.get("種別", "摂取") == "摂取"
                        and r["カロリー(kcal)"])
        exercise_v = sum(float(r["カロリー(kcal)"]) for r in self._rows
                         if r.get("日付") == d and r.get("種別", "摂取") == "消費"
                         and r["カロリー(kcal)"])
        consumed  = BMR_KCAL + exercise_v
        balance   = intake_v - consumed

        self._intake_lbl.config(text=f"摂取: {intake_v:,.0f} kcal")
        self._consume_lbl.config(text=f"消費: {consumed:,.0f} kcal")
        self._consume_sub.config(
            text=f"  基礎代謝 {BMR_KCAL:,} + 運動 {exercise_v:,.0f}")

        sign = "+" if balance >= 0 else ""
        color = COL_POS if balance >= 0 else COL_NEG
        self._balance_num.config(
            text=f"{sign}{balance:,.0f} kcal", fg=color)

    def _update_date_list(self):
        dates = sorted({r.get("日付", "") for r in self._rows if r.get("日付")}, reverse=True)
        self._bal_date_cb["values"] = dates


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CalorieApp()
    app.mainloop()
