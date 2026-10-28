"""pm-market-intel 腳本共用函式：讀檔、列舉值、ID 規則、證據強度計算。"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

import yaml

ROLES = {"brand", "integrator", "channel", "component", "platform"}
LENSES = {"功能", "成本", "營收"}
STATUSES = {"active", "inactive"}
DEPTHS = {"teardown", "profile"}
CLAIM_TYPES = {"vendor_claim", "measured", "customer_case", "user_voice", "official_data", "analysis", "inference"}
SOURCE_TYPES = {
    "official", "datasheet", "docs", "release_notes", "job_posting", "patent", "exhibition",
    "gov", "media", "report", "review", "community", "interview", "web",
}
CONFIDENCE = {"A", "B", "C"}
GAP_TYPES = {"supply", "information", "hypothesis"}
STAKEHOLDERS = {"user", "buyer", "decision_maker"}
OPP_STATUSES = {"open", "validated", "killed"}
STRENGTH_RANK = {"weak": 0, "moderate": 1, "strong": 2}
VALIDATION_METHODS = {"interview", "prototype", "quote", "field_visit", "data", "survey", "desk"}

ID_PATTERNS = {
    "P": re.compile(r"^P-\d{4}$"),
    "E": re.compile(r"^E-\d{4}$"),
    "O": re.compile(r"^O-\d{4}$"),
    "S": re.compile(r"^S-\d{2}$"),
}
REF_PATTERN = re.compile(r"\b([PEO]-\d{4}|S-\d{2})\b")

# 「非宣稱」證據：能佐證實際情況，而不只是廠商說法或我方推論
INDEPENDENT_TYPES = {"measured", "customer_case", "user_voice", "official_data", "analysis"}

DATA_FILES = ("players.yaml", "evidence.yaml", "opportunities.yaml")


class DuplicateIdError(ValueError):
    pass


def load_list(path: Path) -> list:
    """讀取頂層為 list 的 YAML。檔案不存在回傳空 list；格式錯誤丟出 ValueError。"""
    path = Path(path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError(f"{path}: 頂層必須是 list，實際是 {type(data).__name__}")
    return data


def index_by_id(items: list, source: str) -> dict:
    """以 id 建索引；遇到重複 ID 直接報錯，避免後一筆靜默覆蓋前一筆。"""
    out, dups = {}, []
    for i, item in enumerate(items):
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError(f"{source}: 第 {i + 1} 筆缺少 id")
        if item["id"] in out:
            dups.append(item["id"])
        out[item["id"]] = item
    if dups:
        raise DuplicateIdError(f"{source}: 重複 ID {sorted(set(dups))}")
    return out


def resolve_data_path(base: Path, name: str) -> Path:
    """base 可以是資料夾（專案或快照）或直接是 players.yaml 檔案。"""
    base = Path(base)
    if base.is_dir():
        return base / name
    return base.parent / name if base.name != name else base


def is_iso_date(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (_dt.date, _dt.datetime)):
        return True
    try:
        _dt.date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def next_id(prefix: str, existing: set[str]) -> str:
    nums = [int(x.split("-")[1]) for x in existing if ID_PATTERNS[prefix].match(str(x))]
    return f"{prefix}-{(max(nums) + 1 if nums else 1):04d}"


def compute_strength(evidence_for: list[str], evidence_against: list[str], evidence: dict) -> str:
    """依 SKILL.md 規則計算證據強度。

    strong   ：≥2 個獨立 origin，且其中至少 1 筆是 A/B 級的非宣稱證據，且沒有 A/B 級反證
    moderate ：至少 1 筆 A/B 級非宣稱證據，或 ≥2 個獨立 origin
    weak     ：其他（例如只有廠商宣稱、只有推論、只有 C 級來源）
    """
    items = [evidence[e] for e in evidence_for if e in evidence]
    origins = {str(i.get("origin") or i.get("source") or i.get("url") or i["id"]).strip().lower() for i in items}
    solid = [i for i in items if i.get("claim_type") in INDEPENDENT_TYPES and i.get("confidence") in {"A", "B"}]
    strong_against = [
        evidence[e] for e in evidence_against
        if e in evidence and evidence[e].get("confidence") in {"A", "B"}
    ]
    if len(origins) >= 2 and solid and not strong_against:
        return "strong"
    if solid or len(origins) >= 2:
        return "moderate"
    return "weak"
