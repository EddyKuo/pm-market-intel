# pm-market-intel

給**產品經理**用的面向市場市調 Claude Code plugin。

它幫 PM 回答三件事：哪些問題值得解、對誰（使用者／採購者／決策者）；現有方案做了什麼取捨、能力邊界在哪；哪些產品機會值得花時間驗證，以及怎麼用最便宜的方式驗證或淘汰。

> 這不是業務工具：名單求代表性不求數量，比較看能力邊界與設計取捨，產出是**機會假說 + 驗證計畫**，不是業務名單，也不是 PRD。

## 流程

```
brief ─▶ value-mapper ─▶ landscape-scout ×N（平行）─▶ merge_scout ─▶ teardown ×N
   需求面：S-NN、角色痛點      代表性名單＋覆蓋率          統一分配 ID     能力邊界／取捨
                                                                              │
     snapshot ◀─ build_docx ◀─ report ◀─ validate ◀─ opportunity-framer ◀─ comparator
                                                      機會假說＋驗證計畫      矩陣＋分類缺口

更新：snapshot → 增量 scout → merge → diff（產出「需重新檢視」）→ 逐項重算 → validate → 重產報告
```

## 安裝（Claude Code）

在 Claude Code session 中：

```text
/plugin marketplace add EddyKuo/pm-market-intel
/plugin install pm-market-intel@eddykuo-pm
```

Claude Code 2.1.275 以上也可一步完成：

```text
/plugin install pm-market-intel --marketplace EddyKuo/pm-market-intel
```

或在 shell：`claude plugin marketplace add EddyKuo/pm-market-intel && claude plugin install pm-market-intel@eddykuo-pm`

腳本需要：`pip install python-docx pyyaml`

更新到新版：`/plugin marketplace update eddykuo-pm`

## 使用

- 直接說：「幫我做 <品類> 在 <地區> 的市調，要決定 <產品決策>」「分析 <品類> 的競品」「更新 <專案> 的市調」
- 或明確呼叫：`/pm-market-intel:market-intel <品類、範圍與要支持的決策>`

產出在目前工作目錄的 `market-intel/<project-slug>/`。

## 證據模型

每筆證據分開記錄**來源可靠度**（A/B/C）與**主張類型**（廠商宣稱／實測／客戶案例／使用者評價／官方統計／第三方分析／推論），並記錄原始出處以判斷獨立性。結論強度：

| 強度 | 條件 |
|---|---|
| strong | ≥ 2 個獨立出處，且至少 1 筆 A/B 級非宣稱證據，且無 A/B 級反證 |
| moderate | 至少 1 筆 A/B 級非宣稱證據，或 ≥ 2 個獨立出處 |
| weak | 其他（例如只有廠商宣稱） |

## 腳本

| 腳本 | 用途 |
|---|---|
| `validate.py` | 唯一 ID、必填欄位、列舉值、所有 ID 引用（含 .md 內文）、teardown 檔存在、證據強度不得高估 |
| `merge_scout.py` | 合併平行 scout 輸出包，依網域／名稱判重，統一分配 P-/E- ID 並改寫引用 |
| `snapshot.py` | 建立唯一 run-id 快照（同秒重跑不覆寫），記錄於 `runs/index.yaml` |
| `diff_landscape.py` | 名單／證據／機會假說差異，雙向狀態轉移，輸出「需重新檢視」清單 |
| `build_docx.py` | Markdown → Word：可點擊連結、`\|` 跳脫、寬表格橫向頁、表頭跨頁重複 |

## Repo 結構

```
.claude-plugin/marketplace.json                    # marketplace：eddykuo-pm
plugins/pm-market-intel/
├── .claude-plugin/plugin.json
└── skills/market-intel/
    ├── SKILL.md                                   # orchestrator
    ├── agents/        value-mapper · landscape-scout · teardown · comparator · opportunity-framer
    ├── schemas/       player · evidence · opportunity · comparison-dims
    ├── templates/     brief · landscape · teardown · report
    └── scripts/       validate · merge_scout · snapshot · diff_landscape · build_docx
tests/test_scripts.py                              # python3 -m unittest discover -s tests
```

## 開發

```bash
python3 -m unittest discover -s tests -v
claude plugin validate .
```

版本紀錄見 [CHANGELOG.md](CHANGELOG.md)。
