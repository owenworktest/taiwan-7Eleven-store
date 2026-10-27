import json
import os
import re
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 全形英數標點（U+FF01–U+FF5E）與全形空格（U+3000）轉半形。
# 刻意不用 NFKC，避免一併改動到中文字。
FULLWIDTH_TO_HALFWIDTH = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}
FULLWIDTH_TO_HALFWIDTH[0x3000] = 0x20


def normalize(text: str) -> str:
    """統一全形為半形。各家對全形的使用差異極大（全家約 99% 地址用全形數字、
    7-ELEVEN 幾乎全半形），不統一的話下游搜尋「535號」會對不到「５３５號」。"""
    return text.translate(FULLWIDTH_TO_HALFWIDTH).strip()


def write_outputs(stores: dict, basename: str) -> None:
    """正規化後輸出 {basename}.json（單行壓縮）與 {basename}-pretty.json（縮排）。"""
    stores = {
        store_id: {"store": normalize(info["store"]), "address": normalize(info["address"])}
        for store_id, info in stores.items()
    }

    # ensure_ascii=False 確保中文不轉義，dict 保持插入順序 (Python 3.7+)
    with open(os.path.join(SCRIPT_DIR, f"{basename}.json"), "w", encoding="utf-8") as f:
        json.dump(stores, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(SCRIPT_DIR, f"{basename}-pretty.json"), "w", encoding="utf-8") as f:
        json.dump(stores, f, ensure_ascii=False, indent=2)

    print(f"完成。已將 {len(stores)} 筆資料寫入 {basename}.json / {basename}-pretty.json")


def update_readme(brand: str, count: int) -> None:
    """更新 README.MD 資料表中該品牌的筆數與更新日期。"""
    readme_path = os.path.join(SCRIPT_DIR, "README.MD")
    if not os.path.exists(readme_path):
        return

    date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y/%m/%d")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 比對 README 資料表列：| 品牌 | 檔名前綴 | 筆數 | 更新日期 |
    pattern = rf"(\| {re.escape(brand)} \|[^|]*\| )[\d,]+( \|)[^|]*(\|)"
    new_content = re.sub(pattern, rf"\g<1>{count}\g<2> {date_str} \g<3>", content)

    if new_content != content:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
