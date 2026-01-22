import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "master.csv"
REF_DIR = BASE_DIR / "references"

REF_DIR.mkdir(exist_ok=True)

with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    rows = list(reader)

# 1行目がヘッダーだが、最後の列名が改行を含んでいるため連結する
header = []
data_start_index = 1

# ヘッダー行の復元
# rows[0] と rows[1] の先頭列が空で、ヘッダー最終列名が2行に分かれている前提で処理
if len(rows) >= 2 and len(rows[0]) == len(rows[1]):
    header = rows[0]
    # 最後の列名が途中で閉じている可能性があるので、2行目の同じ列位置が空でなければ結合
    last_idx = len(header) - 1
    if rows[1][0] == "" and rows[1][last_idx]:
        header[last_idx] = (header[last_idx] + "\n" + rows[1][last_idx]).strip('"')
        data_start_index = 2
else:
    header = rows[0]

# 列名から必要カラムのインデックスを取得
col_index = {name: i for i, name in enumerate(header)}

required_cols = [
    "番号",
    "チェック用キーワード",
    "対応",
    "分類",
    "表示例",
    "読み",
    "判断",
    "OKの場合",
    "NGの場合",
    "備考",
]

# 「ガイドライン等」の列名は改行を含んでいる可能性があるので曖昧検索
guideline_key = None
for name in header:
    if "ガイドライン等" in name:
        guideline_key = name
        break

if guideline_key:
    required_cols.append(guideline_key)

for row in rows[data_start_index:]:
    if not row or all(not cell for cell in row):
        continue

    try:
        keyword = row[col_index["チェック用キーワード"]].strip()
    except KeyError:
        continue

    if not keyword:
        continue

    # ファイル名用に最低限のサニタイズ（スラッシュだけ別文字に）
    filename = keyword.replace("/", "／") + ".md"
    out_path = REF_DIR / filename

    values = {}
    for col in required_cols:
        idx = col_index.get(col)
        if idx is None or idx >= len(row):
            values[col] = ""
        else:
            values[col] = row[idx].strip()

    # Markdown本文生成
    lines = []
    lines.append(f"# チェック用キーワード: {keyword}")
    lines.append("")
    lines.append(f"- 番号: {values.get('番号', '')}")
    lines.append(f"- 分類: {values.get('分類', '')}")
    lines.append(f"- 読み: {values.get('読み', '')}")
    lines.append("")

    lines.append("## 対応")
    lines.append(values.get("対応", ""))
    lines.append("")

    lines.append("## 表示例")
    lines.append(values.get("表示例", ""))
    lines.append("")

    lines.append("## 判断")
    lines.append(values.get("判断", ""))
    lines.append("")

    lines.append("## OKの場合")
    lines.append(values.get("OKの場合", ""))
    lines.append("")

    lines.append("## NGの場合")
    lines.append(values.get("NGの場合", ""))
    lines.append("")

    lines.append("## 備考")
    lines.append(values.get("備考", ""))
    lines.append("")

    if guideline_key:
        lines.append("## ガイドライン等の出典")
        lines.append(values.get(guideline_key, ""))
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
