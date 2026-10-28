#!/usr/bin/env python3
"""為市調專案建立唯一的快照（run），供之後 diff 使用。

建立 runs/<run-id>/，複製 players / evidence / opportunities，並在 runs/index.yaml 記錄。
run-id = YYYYMMDD-HHMMSS[-label]；同一秒重跑會自動加序號，不會覆寫。

用法：
  python3 snapshot.py market-intel/<slug> [--label before-update]   # 建立快照
  python3 snapshot.py market-intel/<slug> --latest                   # 只印出最近一次快照路徑
輸出（stdout，一行一個 key=value）：run_id=…、run_dir=…、previous=…（沒有則為空）
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mi_common as mc  # noqa: E402


def read_index(runs: Path) -> list:
    idx = runs / "index.yaml"
    if not idx.exists():
        return []
    data = yaml.safe_load(idx.read_text(encoding="utf-8")) or []
    return data if isinstance(data, list) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--label", default="")
    ap.add_argument("--latest", action="store_true")
    args = ap.parse_args()

    project = Path(args.project)
    runs = project / "runs"
    index = read_index(runs)
    previous = index[-1]["run_id"] if index else ""

    if args.latest:
        print(f"previous={runs / previous if previous else ''}")
        return

    for name in mc.DATA_FILES:
        try:
            mc.index_by_id(mc.load_list(project / name), name)
        except (mc.DuplicateIdError, ValueError) as e:
            sys.exit(f"✘ 快照前資料檢查失敗：{e}")

    label = re.sub(r"[^A-Za-z0-9_-]+", "-", args.label).strip("-")
    base = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{label}" if label else "")
    run_id, n = base, 2
    while (runs / run_id).exists():
        run_id, n = f"{base}-{n}", n + 1
    run_dir = runs / run_id
    run_dir.mkdir(parents=True)

    copied = []
    for name in mc.DATA_FILES:
        src = project / name
        if src.exists():
            shutil.copy2(src, run_dir / name)
            copied.append(name)

    index.append({"run_id": run_id, "created": dt.datetime.now().isoformat(timespec="seconds"),
                  "files": copied, "previous": previous or None})
    (runs / "index.yaml").write_text(yaml.safe_dump(index, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print(f"run_id={run_id}")
    print(f"run_dir={run_dir}")
    print(f"previous={runs / previous if previous else ''}")


if __name__ == "__main__":
    main()
