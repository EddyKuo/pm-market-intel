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

## 安裝（Claude Code）

在 Claude Code session 中執行：

```text
/plugin marketplace add EddyKuo/pm-market-intel
/plugin install pm-market-intel@eddykuo-pm
```

Claude Code 2.1.275 以上也可一步完成：

```text
/plugin install pm-market-intel --marketplace EddyKuo/pm-market-intel
```

或在 shell：

```bash
claude plugin marketplace add EddyKuo/pm-market-intel
claude plugin install pm-market-intel@eddykuo-pm
```

報告轉 Word 需要：`pip install python-docx pyyaml`

更新：`/plugin marketplace update eddykuo-pm`

## 使用

- 直接說：「幫我做 <品類> 在 <地區> 的市調」「更新 <專案> 的市調」，Claude 會自動載入
- 或明確呼叫：`/pm-market-intel:market-intel <品類與範圍>`

產出寫在目前工作目錄的 `market-intel/<project-slug>/`，包含 brief、價值地圖、`players.yaml`、`evidence.yaml`、比較矩陣、`40-report.md` 與 `40-report.docx`。

## Repo 結構

```
.claude-plugin/marketplace.json           # marketplace：eddykuo-pm
plugins/pm-market-intel/
├── .claude-plugin/plugin.json
└── skills/market-intel/
    ├── SKILL.md                          # orchestrator
    ├── agents/                           # value-mapper / landscape-scout / comparator
    ├── schemas/                          # player / evidence / comparison-dims
    ├── templates/                        # brief / report
    └── scripts/                          # build_docx.py / diff_landscape.py
```

## 證據等級

- **A** 一手來源（官網、規格書、官方公告、政府資料）
- **B** 可信二手（主流媒體、產業研究摘要、展覽官方名錄）
- **C** 弱來源（論壇、轉述、業務口頭情報）——僅有 C 的結論標 `[待查證]`
