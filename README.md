# pm-market-intel

以產品經理視角做**面向市場的市調** Agent Skill（Claude Code / Claude Agent Skills 格式）。

用「功能 / 成本 / 營收」價值框架切分市場，建立產業鏈名單（品牌、施工/SI、通路），收集展覽與規格書證據，做固定維度競品比較，輸出市調報告（Markdown → Word），並支援定期更新與差異比對。

> v1 範圍：市調到「市場機會結論」為止。PRD／功能規劃待開發決策確認後另行處理。

## 流程

```
brief → value-mapper → landscape-scout（可依角色平行）→ comparator → report.md → report.docx
                                ↑
                     定期/搜：增量搜尋 + diff_landscape.py
```

## 結構

| 路徑 | 用途 |
|---|---|
| `SKILL.md` | Orchestrator：流程、證據規則、完成檢查 |
| `agents/value-mapper.md` | 功能/成本/營收 → segment / use case |
| `agents/landscape-scout.md` | 市場名單建立與增量更新 |
| `agents/comparator.md` | 比較矩陣、定位、市場缺口 |
| `schemas/` | `player`、`evidence`、`comparison-dims` 格式定義 |
| `templates/` | `brief.md`、`report.md` |
| `scripts/build_docx.py` | Markdown 報告 → Word |
| `scripts/diff_landscape.py` | 兩份名單快照的差異報告 |

## 安裝

```bash
git clone <this-repo> ~/.claude/skills/pm-market-intel
pip install python-docx pyyaml
```

## 使用

在 Claude Code 中：「幫我做 <品類> 在 <地區> 的市調」或「更新 <專案> 的市調」。

產出位於 `market-intel/<project-slug>/`，報告轉 Word：

```bash
python scripts/build_docx.py market-intel/<slug>/40-report.md
```

## 證據等級

- **A** 一手來源（官網、規格書、官方公告、政府資料）
- **B** 可信二手（主流媒體、產業研究摘要、展覽官方名錄）
- **C** 弱來源（論壇、轉述、業務口頭情報）——僅有 C 的結論標 `[待查證]`
