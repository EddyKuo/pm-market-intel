#!/usr/bin/env python3
"""檢查市調專案資料的一致性。

檢查：唯一 ID、ID 格式、必填欄位、列舉值、日期格式、所有 ID 引用都存在
（YAML 之間、以及 .md 文件內出現的 P-/E-/O-/S- ID）、teardown 檔案存在、
機會假說的宣告證據強度不得高於規則計算值。

用法：python3 validate.py market-intel/<slug> [--strict]
  exit 0：無錯誤（--strict 時警告也算錯誤）；exit 1：有錯誤
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mi_common as mc  # noqa: E402


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def require(item, fields, where, rep):
    for f in fields:
        if item.get(f) in (None, "", []):
            rep.err(f"{where}: 缺少必填欄位 `{f}`")


def check_enum(value, allowed, where, field, rep, multi=False):
    values = value if multi else [value]
    if multi and not isinstance(value, list):
        rep.err(f"{where}: `{field}` 必須是 list")
        return
    for v in values:
        if v is not None and v not in allowed:
            rep.err(f"{where}: `{field}` 值 `{v}` 不在 {sorted(allowed)}")


def check_id(item, prefix, where, rep):
    if not mc.ID_PATTERNS[prefix].match(str(item.get("id", ""))):
        rep.err(f"{where}: ID `{item.get('id')}` 格式應為 {prefix}-" + ("NN" if prefix == "S" else "NNNN"))


def check_refs(refs, valid: set, where, field, rep):
    if refs is None:
        return
    if not isinstance(refs, list):
        rep.err(f"{where}: `{field}` 必須是 list")
        return
    for r in refs:
        if r not in valid:
            rep.err(f"{where}: `{field}` 引用了不存在的 `{r}`")


def segment_ids(project: Path) -> set:
    vm = project / "10-value-map.md"
    if not vm.exists():
        return set()
    return {m for m in mc.REF_PATTERN.findall(vm.read_text(encoding="utf-8")) if m.startswith("S-")}


def validate(project: Path) -> Report:
    rep = Report()
    data = {}
    for name in mc.DATA_FILES:
        try:
            data[name] = mc.load_list(project / name)
        except ValueError as e:
            rep.err(str(e))
            data[name] = []

    idx = {}
    for name in mc.DATA_FILES:
        try:
            idx[name] = mc.index_by_id(data[name], name)
        except (mc.DuplicateIdError, ValueError) as e:
            rep.err(str(e))
            idx[name] = {i.get("id"): i for i in data[name] if isinstance(i, dict)}

    players, evidence, opps = idx["players.yaml"], idx["evidence.yaml"], idx["opportunities.yaml"]
    segs = segment_ids(project)
    all_ids = set(players) | set(evidence) | set(opps) | segs

    if not (project / "players.yaml").exists():
        rep.warn("找不到 players.yaml")
    if (project / "players.yaml").exists() and not segs:
        rep.warn("10-value-map.md 中找不到任何 S-NN segment ID")

    for pid, p in players.items():
        w = f"players.yaml {pid}"
        check_id(p, "P", w, rep)
        require(p, ["name", "roles", "primary_lens", "regions", "depth", "evidence",
                    "first_seen", "last_verified", "status"], w, rep)
        check_enum(p.get("roles"), mc.ROLES, w, "roles", rep, multi=True)
        check_enum(p.get("primary_lens"), mc.LENSES, w, "primary_lens", rep)
        if p.get("lenses") is not None:
            check_enum(p.get("lenses"), mc.LENSES, w, "lenses", rep, multi=True)
        check_enum(p.get("status"), mc.STATUSES, w, "status", rep)
        check_enum(p.get("depth"), mc.DEPTHS, w, "depth", rep)
        for f in ("first_seen", "last_verified"):
            if not mc.is_iso_date(p.get(f)):
                rep.err(f"{w}: `{f}` 不是 ISO 日期")
        check_refs(p.get("evidence"), set(evidence), w, "evidence", rep)
        if segs:
            check_refs(p.get("segments"), segs, w, "segments", rep)
        for prod in p.get("products") or []:
            check_refs(prod.get("evidence"), set(evidence), f"{w} 產品 {prod.get('name')}", "evidence", rep)
        if p.get("depth") == "teardown":
            td = p.get("teardown")
            if not td:
                rep.err(f"{w}: depth=teardown 但未填 `teardown` 路徑")
            elif not (project / td).exists():
                rep.err(f"{w}: teardown 檔案 `{td}` 不存在")
        if p.get("status") == "inactive" and not p.get("status_note"):
            rep.warn(f"{w}: inactive 但沒有 status_note")

    for eid, e in evidence.items():
        w = f"evidence.yaml {eid}"
        check_id(e, "E", w, rep)
        require(e, ["claim", "claim_type", "source_type", "confidence", "accessed"], w, rep)
        if not (e.get("url") or e.get("source")):
            rep.err(f"{w}: `url` 與 `source` 至少要有一個")
        check_enum(e.get("claim_type"), mc.CLAIM_TYPES, w, "claim_type", rep)
        check_enum(e.get("source_type"), mc.SOURCE_TYPES, w, "source_type", rep)
        check_enum(e.get("confidence"), mc.CONFIDENCE, w, "confidence", rep)
        for f in ("published", "accessed", "valid_until"):
            if not mc.is_iso_date(e.get(f)):
                rep.err(f"{w}: `{f}` 不是 ISO 日期")
        check_refs(e.get("related"), all_ids, w, "related", rep)
        check_refs(e.get("contradicts"), set(evidence), w, "contradicts", rep)
        if not e.get("origin"):
            rep.warn(f"{w}: 沒有 origin，無法判斷來源是否獨立")

    for oid, o in opps.items():
        w = f"opportunities.yaml {oid}"
        check_id(o, "O", w, rep)
        require(o, ["hypothesis", "segment", "stakeholder", "lens", "gap_type",
                    "kill_criteria", "validation_next", "evidence_strength", "status"], w, rep)
        check_enum(o.get("stakeholder"), mc.STAKEHOLDERS, w, "stakeholder", rep)
        check_enum(o.get("lens"), mc.LENSES, w, "lens", rep)
        check_enum(o.get("gap_type"), mc.GAP_TYPES, w, "gap_type", rep)
        check_enum(o.get("status"), mc.OPP_STATUSES, w, "status", rep)
        check_enum(o.get("evidence_strength"), set(mc.STRENGTH_RANK), w, "evidence_strength", rep)
        if segs and o.get("segment") not in segs:
            rep.err(f"{w}: segment `{o.get('segment')}` 不在 10-value-map.md")
        check_refs(o.get("evidence_for"), set(evidence), w, "evidence_for", rep)
        check_refs(o.get("evidence_against"), set(evidence), w, "evidence_against", rep)
        if "evidence_against" not in o:
            rep.err(f"{w}: 缺少 `evidence_against`（找不到反證請寫 [] 並在 notes 說明）")
        elif o.get("evidence_against") == [] and not o.get("notes"):
            rep.warn(f"{w}: 沒有反證也沒有 notes 說明找過哪裡")
        if o.get("gap_type") == "supply" and not o.get("evidence_for"):
            rep.err(f"{w}: gap_type=supply 必須有 evidence_for")
        for key in ("problem_importance", "unmet"):
            v = (o.get("scores") or {}).get(key)
            if not isinstance(v, int) or not 1 <= v <= 5:
                rep.err(f"{w}: scores.{key} 必須是 1–5 的整數")
        fit = (o.get("fit") or {}).get("score")
        if not isinstance(fit, int) or not 1 <= fit <= 5:
            rep.err(f"{w}: fit.score 必須是 1–5 的整數")
        for step in o.get("validation_next") or []:
            if not isinstance(step, dict) or step.get("method") not in mc.VALIDATION_METHODS:
                rep.err(f"{w}: validation_next.method 必須在 {sorted(mc.VALIDATION_METHODS)}")
        declared = o.get("evidence_strength")
        if declared in mc.STRENGTH_RANK:
            computed = mc.compute_strength(o.get("evidence_for") or [], o.get("evidence_against") or [], evidence)
            if mc.STRENGTH_RANK[declared] > mc.STRENGTH_RANK[computed]:
                rep.err(f"{w}: 宣告 evidence_strength={declared}，但依規則只有 {computed}")

    for md in sorted(project.rglob("*.md")):
        if "runs" in md.relative_to(project).parts:
            continue
        text = md.read_text(encoding="utf-8")
        for ref in sorted(set(mc.REF_PATTERN.findall(text))):
            if ref.startswith("S-") and md.name == "10-value-map.md":
                continue
            if ref not in all_ids:
                rep.err(f"{md.relative_to(project)}: 引用了不存在的 `{ref}`")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--strict", action="store_true", help="警告也視為錯誤")
    args = ap.parse_args()
    project = Path(args.project)
    if not project.is_dir():
        sys.exit(f"找不到專案資料夾：{project}")
    rep = validate(project)
    for e in rep.errors:
        print(f"✘ {e}")
    for w in rep.warnings:
        print(f"⚠ {w}")
    failed = bool(rep.errors) or (args.strict and bool(rep.warnings))
    print(f"\n{'✘ 驗證失敗' if failed else '✔ 驗證通過'}：{len(rep.errors)} 錯誤、{len(rep.warnings)} 警告")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
