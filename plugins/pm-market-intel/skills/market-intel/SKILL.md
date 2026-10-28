---
name: market-intel
description: 給產品經理用的面向市場市調：以「功能/成本/營收」價值框架拆解需求與使用者/採購者/決策者痛點，建立代表性競品名單並做 teardown，比較產品取捨、分類缺口，產出可驗證、可淘汰的產品機會假說與驗證計畫，報告可轉 Word，並支援定期更新與差異比對。用於「幫我做 X 市場的市調」「分析 X 的競品」「更新上次的市調」。不做業務名單、不寫 PRD 或功能規格。
---

# PM Market Intel（v1.1）

> **路徑約定**：`agents/`、`schemas/`、`templates/`、`scripts/` 位於**本 skill 的目錄**（載入時顯示的 base directory，以下稱 `<SKILL_DIR>`）。市調產出寫在使用者目前工作目錄下的 `market-intel/<slug>/`。
>
> **相依套件**：首次執行腳本前確認 `python3 -c "import docx, yaml"`；缺少時 `pip install python-docx pyyaml`（受管環境加 `--break-system-packages` 或用 venv）。

## 定位

這是 **PM 的工具**，不是業務的工具。目的是幫 PM 回答：
- 哪些問題**值得解**？對誰（使用者／採購者／決策者）？
- 現有方案做了什麼**取捨**？能力邊界在哪？
- 哪些產品機會**值得花時間驗證**？怎麼用最便宜的方式驗證或淘汰？

因此：名單求**代表性**不求數量；比較看**能力邊界與設計取捨**，價格與通路只是輔助；產出是**機會假說 + 驗證計畫**，不是「應該做什麼產品」，也不是 PRD。

**範圍邊界**：不做業務名單、不做定價或通路策略、不寫 PRD／功能規格／roadmap。使用者要求這些時，先完成市調，並說明它們不在此 skill 範圍。

---

## 0. 價值框架：功能 / 成本 / 營收

| Lens | 客戶買單的理由 | PM 要問的 |
|---|---|---|
| **功能** | 能做到原本做不到的事 | 什麼工作完成不了？替代方案卡在哪？能力門檻在哪？ |
| **成本** | 用更少的錢／人力／時間／能源達成 | 省的是誰的成本？誰感受得到？替代方案的隱藏成本？ |
| **營收** | 幫客戶創造新收入 | 新收入靠什麼機制？誰承擔風險？誰分潤？ |

每個 segment 標**主 lens**；同一產品可跨 lens。

---

## 1. 專案資料夾

```
market-intel/<slug>/
├── 00-brief.md              # 範圍與要支持的決策（templates/brief.md）
├── 10-value-map.md          # 需求面：S-NN segment、角色痛點（agents/value-mapper.md）
├── 20-landscape.md          # 產業結構與覆蓋率（templates/landscape.md）
├── players.yaml             # 代表性 player（schemas/player.yaml）
├── evidence.yaml            # 證據庫（schemas/evidence.yaml）
├── teardowns/P-NNNN.md      # 競品深度拆解（agents/teardown.md、templates/teardown.md）
├── 30-comparison.md         # 比較矩陣、取捨地圖、分類缺口（agents/comparator.md）
├── opportunities.yaml       # 產品機會假說（schemas/opportunity.yaml）
├── 40-opportunities.md      # 假說排序與說明（agents/opportunity-framer.md）
├── 50-report.md / .docx     # 報告（templates/report.md）
├── scout-*.bundle.yaml      # 平行 scout 的暫存輸出包（合併後可刪）
└── runs/
    ├── index.yaml           # 快照紀錄
    └── <run-id>/            # 每次快照：players / evidence / opportunities + delta.md
```

ID 規則：`S-NN`（segment）、`P-NNNN`（player）、`E-NNNN`（evidence）、`O-NNNN`（opportunity）。ID 永不重用；正式 ID 只由 orchestrator 或 `merge_scout.py` 分配。

---

## 2. 證據規則

每筆證據分開記錄兩件事：
- **來源可靠度** `confidence`：A 一手（官網、規格書、官方文件、政府資料）／B 可信二手（主流媒體、產業研究、展覽官方名錄）／C 弱來源（論壇轉述、業務口頭情報）
- **主張類型** `claim_type`：`vendor_claim` 廠商宣稱／`measured` 實測／`customer_case` 客戶案例／`user_voice` 使用者評價／`official_data` 官方統計／`analysis` 第三方分析／`inference` 我方推論

官網是 A 級來源，但只能證明「廠商這樣說」。**能力與成效的判斷不能只靠 `vendor_claim`。**

**獨立性**：`origin` 記原始出處。多篇報導轉載同一份新聞稿 = 同一個 origin，不算多個來源。

**結論強度**（報告與 `opportunities.yaml` 都用這套，`validate.py` 會檢查）：
- `strong`：≥ 2 個獨立 origin，且至少 1 筆 A/B 級的非宣稱證據，且沒有 A/B 級反證
- `moderate`：至少 1 筆 A/B 級非宣稱證據，或 ≥ 2 個獨立 origin
- `weak`：其他

報告中每個結論都標強度。只有 weak 的結論放進「待驗證」，不放進摘要結論。
其他規則：價格記幣別／含稅／日期；有時效的資訊填 `valid_until`；推論標 `[推論]`；引用網頁用自己的話改寫；優先近 12–24 個月的資料，較舊的標註日期。

---

## 3. 流程

### Step 1 — Brief
用 `templates/brief.md` 建立 `00-brief.md`。**必填「要支持的產品決策」與「我方產品與能力」**——後者是評估機會適配度的依據。資訊不足時向使用者問一次（最多 3 題）；使用者不在時採最合理假設並標 `[假設]`。

### Step 2 — 需求面（agents/value-mapper.md）
產出 `10-value-map.md`，segment 用 `S-NN` ID，痛點依使用者／採購者／決策者拆開，列替代方案與切換障礙。

### Step 3 — 代表性名單（agents/landscape-scout.md）
- 依角色或地區分派 scout。有 Agent/Task 工具時**平行**派工；每個 scout 只寫自己的 `scout-<範圍>.bundle.yaml`（暫時 ID 用 `tmp-` 開頭）。
- 全部完成後合併並分配正式 ID：
  ```bash
  python3 <SKILL_DIR>/scripts/merge_scout.py market-intel/<slug> market-intel/<slug>/scout-*.bundle.yaml
  ```
- 依 bundle 的 `coverage` 寫 `20-landscape.md`（覆蓋率表與限制）。
- 沒有 sub-agent 工具時，依序執行 scout，仍用 bundle + merge，確保 ID 一致。

### Step 4 — Teardown（agents/teardown.md）
對 `depth: teardown` 的 player（建議總共 4–8 家）各寫 `teardowns/<P-ID>.md`。可平行；證據同樣先寫 bundle（只有 `evidence` 段）再用 `merge_scout.py` 合併，或由 orchestrator 依序寫入 `evidence.yaml` 並分配 ID。

### Step 5 — 比較與缺口（agents/comparator.md）
產出 `30-comparison.md`：矩陣、取捨地圖、**分類缺口**（供給／資訊／待驗證）。缺口沒有數量下限；找不到可驗證的供給缺口就直接說。

### Step 6 — 機會假說（agents/opportunity-framer.md）
產出 `opportunities.yaml` 與 `40-opportunities.md`：每個假說含正反證據、評分、我方適配、kill criteria、最便宜的下一步驗證；前 3 名做數量級規模感。

### Step 7 — 驗證與報告
1. 驗證資料一致性（錯誤必須修到 0）：
   ```bash
   python3 <SKILL_DIR>/scripts/validate.py market-intel/<slug>
   ```
2. 依 `templates/report.md` 寫 `50-report.md`，再驗證一次（報告內的 ID 引用也會被檢查）。
3. 轉 Word：
   ```bash
   python3 <SKILL_DIR>/scripts/build_docx.py market-intel/<slug>/50-report.md
   ```
   ≥ 7 欄的表格自動放進橫向頁面，連結可點擊。
4. 建立本次快照（之後更新時的比較基準）：
   ```bash
   python3 <SKILL_DIR>/scripts/snapshot.py market-intel/<slug> --label baseline
   ```

### Step 8 — 定期更新（閉環）
使用者要求「更新市調」或排程觸發時：
1. `snapshot.py market-intel/<slug> --label before-update` → 記下輸出的 `run_dir`（本次更新前的狀態）
2. scout 以**增量模式**執行，輸出 bundle → `merge_scout.py` 合併；退出者 `inactive`、恢復者 `active`，都填 `status_note`，不刪除
3. 產生差異與影響清單：
   ```bash
   python3 <SKILL_DIR>/scripts/diff_landscape.py <run_dir> market-intel/<slug> > <run_dir>/delta.md
   ```
4. **依 `delta.md` 的「需重新檢視」表逐項處理**：更新受影響的 teardown、`30-comparison.md`、`opportunities.yaml`（重新計算證據強度、檢查 kill criteria 是否已觸發 → `status: killed`）
5. 執行 `validate.py`，通過後重產 `50-report.md` 與 `.docx`，報告版本號 +0.1 並標本次 run-id
6. 在 `delta.md` 末尾補 3–5 句「對產品判斷的影響」
7. `snapshot.py market-intel/<slug> --label after-update`

**沒有走完第 4–5 步，不可宣稱報告已更新。**

---

## 4. 完成檢查清單
- [ ] `00-brief.md` 有「要支持的決策」與「我方產品與能力」
- [ ] 每個關鍵問題在報告中有答案，或明確標「資料不足」與下一步
- [ ] `validate.py` 0 錯誤（警告逐一確認）
- [ ] 摘要中的每個結論都標了證據強度，且沒有只靠 `vendor_claim` 的 strong
- [ ] 缺口已分類；資訊缺口沒有被寫成「沒人做」
- [ ] 每個機會假說都有反證欄、kill criteria、下一步驗證
- [ ] `20-landscape.md` 說明了覆蓋限制
- [ ] `.docx` 已產出並開啟檢查；已建立快照
