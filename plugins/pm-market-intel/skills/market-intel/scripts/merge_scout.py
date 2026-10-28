#!/usr/bin/env python3
"""把平行 landscape-scout 的輸出包合併進專案，統一分配正式 ID。

每個 scout 只寫自己的輸出包，不直接改 players.yaml / evidence.yaml，避免 ID 碰撞。
輸出包格式（YAML）：

  scout: brand                 # 這個包負責的角色或範圍
  players:                     # 欄位同 schemas/player.yaml，但 id 用暫時 ID（如 tmp-p1）
    - id: tmp-p1
      ...
      evidence: [tmp-e1]
  evidence:                    # 欄位同 schemas/evidence.yaml，id 用暫時 ID（如 tmp-e1）
    - id: tmp-e1
      related: [tmp-p1]

合併規則：
- player 判重：官網網域相同，或正規化後的名稱/別名有交集 → 合併為同一筆
  （roles / regions / lenses / segments / aliases / evidence 取聯集；products 依名稱合併；既有非空欄位不覆寫）
- evidence 判重：url + claim 相同 → 視為同一筆
- 暫時 ID 一律換成正式 P-/E- ID，並改寫所有引用

用法：python3 merge_scout.py market-intel/<slug> bundle1.yaml [bundle2.yaml ...] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mi_common as mc  # noqa: E402

LIST_FIELDS = ("roles", "regions", "lenses", "segments", "aliases", "notable")
SUFFIXES = re.compile(r"(co\.?,?\s*ltd\.?|inc\.?|corp(oration)?\.?|limited|llc|gmbh|股份有限公司|有限公司|公司)$", re.I)


def norm_name(name: str) -> str:
    s = (name or "").strip().lower()
    s = SUFFIXES.sub("", s).strip(" ,.")
    return re.sub(r"[\s\-_.,()（）]", "", s)


def domain(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url if "//" in url else f"//{url}").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def keys_for(p: dict) -> set:
    keys = {f"n:{norm_name(p.get('name', ''))}"} | {f"n:{norm_name(a)}" for a in p.get("aliases") or []}
    d = domain(p.get("website"))
    if d:
        keys.add(f"d:{d}")
    return {k for k in keys if k not in ("n:", "d:")}


def union(a, b):
    out = list(a or [])
    for x in b or []:
        if x not in out:
            out.append(x)
    return out


def merge_player(base: dict, incoming: dict):
    for f in LIST_FIELDS + ("evidence",):
        if incoming.get(f):
            base[f] = union(base.get(f), incoming.get(f))
    prods = {pr.get("name"): pr for pr in base.get("products") or []}
    for pr in incoming.get("products") or []:
        if pr.get("name") in prods:
            tgt = prods[pr["name"]]
            for k, v in pr.items():
                if k == "evidence":
                    tgt["evidence"] = union(tgt.get("evidence"), v)
                elif tgt.get(k) in (None, "", []):
                    tgt[k] = v
        else:
            base.setdefault("products", []).append(pr)
    for k, v in incoming.items():
        if k in LIST_FIELDS or k in ("id", "evidence", "products", "first_seen"):
            continue
        if base.get(k) in (None, "", []):
            base[k] = v
    if incoming.get("last_verified") and str(incoming["last_verified"]) > str(base.get("last_verified") or ""):
        base["last_verified"] = incoming["last_verified"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    project = Path(args.project)

    try:
        players = mc.load_list(project / "players.yaml")
        evidence = mc.load_list(project / "evidence.yaml")
        p_idx = mc.index_by_id(players, "players.yaml")
        e_idx = mc.index_by_id(evidence, "evidence.yaml")
    except (mc.DuplicateIdError, ValueError) as e:
        sys.exit(f"✘ 專案資料錯誤，先修正再合併：{e}")

    key_to_pid = {}
    for p in players:
        for k in keys_for(p):
            key_to_pid.setdefault(k, p["id"])
    ev_key_to_eid = {(e.get("url"), e.get("claim")): e["id"] for e in evidence}

    stats = {"players_new": 0, "players_merged": 0, "evidence_new": 0, "evidence_dup": 0}
    for bundle_path in args.bundles:
        bundle = yaml.safe_load(Path(bundle_path).read_text(encoding="utf-8")) or {}
        b_players, b_evidence = bundle.get("players") or [], bundle.get("evidence") or []
        try:
            mc.index_by_id(b_players, f"{bundle_path} players")
            mc.index_by_id(b_evidence, f"{bundle_path} evidence")
        except (mc.DuplicateIdError, ValueError) as e:
            sys.exit(f"✘ {e}")

        emap = {}
        for e in b_evidence:
            key = (e.get("url"), e.get("claim"))
            if key in ev_key_to_eid:
                emap[e["id"]] = ev_key_to_eid[key]
                stats["evidence_dup"] += 1
            else:
                new_id = mc.next_id("E", set(e_idx))
                emap[e["id"]] = new_id
                e_idx[new_id] = None
                ev_key_to_eid[key] = new_id

        pmap = {}
        for p in b_players:
            match = next((key_to_pid[k] for k in keys_for(p) if k in key_to_pid), None)
            if match:
                pmap[p["id"]] = match
            else:
                new_id = mc.next_id("P", set(p_idx))
                pmap[p["id"]] = new_id
                p_idx[new_id] = None
                for k in keys_for(p):
                    key_to_pid.setdefault(k, new_id)

        def rw(refs):
            return [pmap.get(r, emap.get(r, r)) for r in refs or []]

        for e in b_evidence:
            if e_idx.get(emap[e["id"]]) is not None:
                continue
            e = dict(e, id=emap[e["id"]], related=rw(e.get("related")), contradicts=rw(e.get("contradicts")))
            evidence.append(e)
            e_idx[e["id"]] = e
            stats["evidence_new"] += 1

        for p in b_players:
            p = dict(p, evidence=rw(p.get("evidence")))
            p["products"] = [dict(pr, evidence=rw(pr.get("evidence"))) for pr in p.get("products") or []]
            target_id = pmap[p["id"]]
            if p_idx.get(target_id) is not None:
                merge_player(p_idx[target_id], p)
                stats["players_merged"] += 1
            else:
                p["id"] = target_id
                players.append(p)
                p_idx[target_id] = p
                stats["players_new"] += 1
            for k in keys_for(p_idx[target_id]):
                key_to_pid.setdefault(k, target_id)

    print(" ".join(f"{k}={v}" for k, v in stats.items()))
    if args.dry_run:
        print("（dry-run，未寫檔）")
        return
    (project / "players.yaml").write_text(yaml.safe_dump(players, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (project / "evidence.yaml").write_text(yaml.safe_dump(evidence, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("✔ 已寫入 players.yaml、evidence.yaml；接著執行 validate.py")


if __name__ == "__main__":
    main()
