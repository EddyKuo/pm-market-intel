#!/usr/bin/env python3
"""比較兩次市調資料（快照 vs 目前），輸出 Markdown 差異報告與「需重新檢視」清單。

輸入可以是資料夾（專案資料夾或 runs/<run-id>/ 快照，讀取 players / evidence / opportunities）
或直接是 players.yaml（只比較名單）。

用法：python3 diff_landscape.py <old> <new> > delta.md
  exit 0：成功；exit 2：資料有重複 ID 或格式錯誤（不產出報告，先修資料）
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mi_common as mc  # noqa: E402

PLAYER_FIELDS = ["roles", "primary_lens", "lenses", "regions", "segments", "business_model", "depth", "notable"]
EVIDENCE_FIELDS = ["claim", "claim_type", "confidence", "origin", "valid_until", "contradicts"]


def load(base: str):
    base_p = Path(base)
    if base_p.is_file():
        names = {"players.yaml": base_p}
    else:
        names = {n: base_p / n for n in mc.DATA_FILES}
    out = {}
    for n in mc.DATA_FILES:
        out[n] = mc.index_by_id(mc.load_list(names[n]), str(names[n])) if n in names else {}
    return out


def fmt(v):
    if isinstance(v, dict) and "amount" in v:
        if v.get("amount") is None:
            return "—"
        tag = "[估]" if v.get("estimated") else ""
        tax = {True: "含稅", False: "未稅"}.get(v.get("tax_included"), "")
        return f"{v.get('currency', '')} {v['amount']:,} {tax}{tag} ({v.get('date') or '日期未知'})".replace("  ", " ")
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "—"
    s = "—" if v in (None, "") else str(v)
    return s.replace("|", "\\|").replace("\n", " ")


def product_map(p):
    return {prod.get("name"): prod for prod in (p.get("products") or [])}


def main(old_path, new_path):
    try:
        old, new = load(old_path), load(new_path)
    except (mc.DuplicateIdError, ValueError) as e:
        print(f"✘ 資料錯誤，無法比較：{e}", file=sys.stderr)
        sys.exit(2)

    op, np_ = old["players.yaml"], new["players.yaml"]
    oe, ne = old["evidence.yaml"], new["evidence.yaml"]
    oo, no = old["opportunities.yaml"], new["opportunities.yaml"]

    recheck: dict[str, set[str]] = {}

    def flag(target, reason):
        recheck.setdefault(target, set()).add(reason)

    added = [np_[k] for k in np_ if k not in op]
    missing = [op[k] for k in op if k not in np_]
    exited, reactivated, changed = [], [], []

    for pid in sorted(np_.keys() & op.keys()):
        o, n = op[pid], np_[pid]
        os_, ns_ = o.get("status"), n.get("status")
        if os_ != "inactive" and ns_ == "inactive":
            exited.append(n)
        elif os_ == "inactive" and ns_ != "inactive":
            reactivated.append(n)
        diffs = [(f, o.get(f), n.get(f)) for f in PLAYER_FIELDS if o.get(f) != n.get(f)]
        opm, npm = product_map(o), product_map(n)
        for name in sorted(set(npm) - set(opm), key=str):
            diffs.append(("新產品", None, name))
        for name in sorted(set(opm) - set(npm), key=str):
            diffs.append(("移除產品", name, None))
        for name in sorted(set(opm) & set(npm), key=str):
            for key in ("key_specs", "price", "category"):
                if opm[name].get(key) != npm[name].get(key):
                    diffs.append((f"{name}.{key}", opm[name].get(key), npm[name].get(key)))
        if diffs:
            changed.append((n, diffs))
            flag("30-comparison.md", f"{pid} {n.get('name')} 資料變動")
            if n.get("depth") == "teardown" and n.get("teardown"):
                flag(n["teardown"], "產品／定位變動")

    for p in added + reactivated:
        flag("20-landscape.md", f"{p['id']} {p.get('name')} 新進或重新啟用")
        flag("30-comparison.md", f"{p['id']} {p.get('name')} 新進或重新啟用，評估是否列入比較")
    for p in exited:
        flag("20-landscape.md", f"{p['id']} {p.get('name')} 退出")
        flag("30-comparison.md", f"{p['id']} {p.get('name')} 退出")

    e_added = sorted(set(ne) - set(oe))
    e_removed = sorted(set(oe) - set(ne))
    e_changed = []
    for eid in sorted(set(ne) & set(oe)):
        d = [(f, oe[eid].get(f), ne[eid].get(f)) for f in EVIDENCE_FIELDS if oe[eid].get(f) != ne[eid].get(f)]
        if d:
            e_changed.append((eid, d))
    touched = set(e_added) | set(e_removed) | {e for e, _ in e_changed}

    moved_players = {p["id"] for p in exited + reactivated} | {p["id"] for p, _ in changed}

    opp_strength = []
    for oid, o in sorted(no.items()):
        refs = set(o.get("evidence_for") or []) | set(o.get("evidence_against") or [])
        new_related = [e for e in e_added if oid in (ne[e].get("related") or [])]
        via_players = sorted({
            pid for e in refs if e in ne for pid in (ne[e].get("related") or []) if pid in moved_players
        })
        if refs & touched or new_related or via_players:
            reason = []
            if refs & touched:
                reason.append("引用的證據變動：" + ", ".join(sorted(refs & touched)))
            if new_related:
                reason.append("新增相關證據：" + ", ".join(new_related))
            if via_players:
                reason.append("證據所涉 player 狀態或資料變動：" + ", ".join(via_players))
            flag("opportunities.yaml", f"{oid}：" + "；".join(reason))
        before = None
        if oid in oo:
            before = mc.compute_strength(oo[oid].get("evidence_for") or [], oo[oid].get("evidence_against") or [], oe)
        after = mc.compute_strength(o.get("evidence_for") or [], o.get("evidence_against") or [], ne)
        if before != after or (o.get("evidence_strength") and o.get("evidence_strength") != after):
            opp_strength.append((oid, before, after, o.get("evidence_strength")))
            flag("opportunities.yaml", f"{oid}：證據強度應為 {after}")

    if any(t == "opportunities.yaml" for t in recheck) or any(t == "30-comparison.md" for t in recheck):
        flag("50-report.md", "上游分析變動，重產報告並重新驗證")

    out = [f"# 市調資料變動報告（{date.today().isoformat()}）", ""]
    out.append(f"- 比較基準：`{old_path}` → `{new_path}`")
    out.append(
        f"- 名單：新增 {len(added)}｜退出 {len(exited)}｜重新啟用 {len(reactivated)}｜變動 {len(changed)}｜遺失 {len(missing)}"
    )
    out.append(f"- 證據：新增 {len(e_added)}｜移除 {len(e_removed)}｜變動 {len(e_changed)}")
    out.append("")

    out.append("## 新進者")
    if added:
        out += ["| ID | 名稱 | 角色 | 主 lens | 主要市場 |", "|---|---|---|---|---|"]
        for p in added:
            out.append(f"| {p['id']} | {fmt(p.get('name'))} | {fmt(p.get('roles'))} | "
                       f"{fmt(p.get('primary_lens'))} | {fmt(p.get('regions'))} |")
    else:
        out.append("無")
    out.append("")

    out.append("## 狀態轉移")
    if exited or reactivated:
        for p in exited:
            out.append(f"- active → inactive：{p['id']} {p.get('name')}（{fmt(p.get('status_note'))}）")
        for p in reactivated:
            out.append(f"- inactive → active：{p['id']} {p.get('name')}（{fmt(p.get('status_note'))}）")
    else:
        out.append("無")
    out.append("")

    out.append("## 既有 player 變動")
    if changed:
        out += ["| ID | 名稱 | 欄位 | 舊值 | 新值 |", "|---|---|---|---|---|"]
        for p, diffs in changed:
            for field, a, b in diffs:
                out.append(f"| {p['id']} | {fmt(p.get('name'))} | {field} | {fmt(a)} | {fmt(b)} |")
    else:
        out.append("無")
    out.append("")

    if e_added or e_removed or e_changed:
        out.append("## 證據變動")
        for e in e_added:
            out.append(f"- 新增 {e}：{fmt(ne[e].get('claim'))}（{ne[e].get('claim_type')}／{ne[e].get('confidence')}）")
        for e in e_removed:
            out.append(f"- 移除 {e}：{fmt(oe[e].get('claim'))}")
        for e, d in e_changed:
            out.append(f"- 變動 {e}：" + "；".join(f"{f} {fmt(a)} → {fmt(b)}" for f, a, b in d))
        out.append("")

    if opp_strength:
        out.append("## 機會假說的證據強度")
        out += ["| ID | 上次計算 | 本次計算 | 檔案宣告 |", "|---|---|---|---|"]
        for oid, b, a, decl in opp_strength:
            out.append(f"| {oid} | {fmt(b)} | {a} | {fmt(decl)} |")
        out.append("")

    if missing:
        out.append("## ⚠ 名單遺失（舊快照有、目前沒有）")
        out.append("退出者應標 `status: inactive` 而非刪除，請檢查：")
        for p in missing:
            out.append(f"- {p['id']} {p.get('name')}")
        out.append("")

    out.append("## 需重新檢視")
    if recheck:
        out += ["| 檔案／章節 | 原因 |", "|---|---|"]
        for target in sorted(recheck):
            for reason in sorted(recheck[target]):
                out.append(f"| {target} | {fmt(reason)} |")
        out.append("")
        out.append("完成上列檢視後執行 `validate.py`，再重產報告。")
    else:
        out.append("無：本次變動不影響既有分析結論。")
    out.append("")
    out.append("## 對產品判斷的影響")
    out.append("<由 agent 補寫 3–5 句：哪些機會假說變強／變弱、是否出現新的競品取捨>")
    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("用法：python3 diff_landscape.py <old> <new>")
    main(sys.argv[1], sys.argv[2])
