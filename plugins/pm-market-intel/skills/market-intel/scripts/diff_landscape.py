#!/usr/bin/env python3
"""比較兩份 players.yaml 快照，輸出 Markdown 差異報告。

用法：python diff_landscape.py old.yaml new.yaml > delta.md
依賴：pip install pyyaml
"""
import sys
from datetime import date

import yaml

TRACKED = ["role", "primary_lens", "lenses", "regions", "segments", "business_model", "status", "notable"]


def load(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return {p["id"]: p for p in data}


def product_map(p):
    return {prod.get("name"): prod for prod in (p.get("products") or [])}


def fmt(v):
    if isinstance(v, dict) and "amount" in v:
        if v.get("amount") is None:
            return "—"
        tag = "[估]" if v.get("estimated") else ""
        tax = {True: "含稅", False: "未稅"}.get(v.get("tax_included"), "")
        return f"{v.get('currency', '')} {v['amount']:,} {tax}{tag} ({v.get('date') or '日期未知'})".strip()
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "—"
    return "—" if v in (None, "") else str(v)


def main(old_path, new_path):
    old, new = load(old_path), load(new_path)
    added = [new[k] for k in new if k not in old]
    missing = [old[k] for k in old if k not in new]
    exited, changed = [], []

    for pid in new.keys() & old.keys():
        o, n = old[pid], new[pid]
        if o.get("status") == "active" and n.get("status") == "inactive":
            exited.append(n)
        diffs = [(f, o.get(f), n.get(f)) for f in TRACKED if f != "status" and o.get(f) != n.get(f)]
        op, np_ = product_map(o), product_map(n)
        for name in np_.keys() - op.keys():
            diffs.append(("新產品", None, name))
        for name in op.keys() - np_.keys():
            diffs.append(("移除產品", name, None))
        for name in op.keys() & np_.keys():
            for key in ("key_specs", "price"):
                if op[name].get(key) != np_[name].get(key):
                    diffs.append((f"{name}.{key}", op[name].get(key), np_[name].get(key)))
        if diffs:
            changed.append((n, diffs))

    out = [f"# 市場名單變動報告（{date.today().isoformat()}）", ""]
    out.append(f"- 比較基準：`{old_path}` → `{new_path}`")
    out.append(f"- 新增 {len(added)}｜退出 {len(exited)}｜變動 {len(changed)}｜名單遺失 {len(missing)}")
    out.append("")

    out.append("## 新進者")
    if added:
        out.append("| ID | 名稱 | 角色 | 主 lens | 主要市場 |")
        out.append("|---|---|---|---|---|")
        for p in added:
            out.append(f"| {p['id']} | {p.get('name')} | {p.get('role')} | {p.get('primary_lens')} | {fmt(p.get('regions'))} |")
    else:
        out.append("無")
    out.append("")

    out.append("## 退出 / 停止營運")
    if exited:
        for p in exited:
            out.append(f"- {p['id']} {p.get('name')}：{fmt(p.get('status_note'))}")
    else:
        out.append("無")
    out.append("")

    out.append("## 既有 player 變動")
    if changed:
        out.append("| ID | 名稱 | 欄位 | 舊值 | 新值 |")
        out.append("|---|---|---|---|---|")
        for p, diffs in changed:
            for field, a, b in diffs:
                out.append(f"| {p['id']} | {p.get('name')} | {field} | {fmt(a)} | {fmt(b)} |")
    else:
        out.append("無")
    out.append("")

    if missing:
        out.append("## ⚠ 名單遺失（舊快照有、新名單沒有）")
        out.append("退出者應標 `status: inactive` 而非刪除，請檢查：")
        for p in missing:
            out.append(f"- {p['id']} {p.get('name')}")
        out.append("")

    out.append("## 對市場判斷的影響")
    out.append("<由 agent 補寫 3–5 句>")
    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("用法：python diff_landscape.py old.yaml new.yaml")
    main(sys.argv[1], sys.argv[2])
