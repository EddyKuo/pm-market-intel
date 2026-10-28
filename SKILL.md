---
name: pm-market-intel
description: 以產品經理視角做面向市場的市調：用「功能/成本/營收」價值框架切分市場，建立產業鏈名單（品牌、施工/SI、通路），收集展覽與規格書證據，做固定維度競品比較，輸出市調報告 .md（可轉 Word），並支援定期搜尋更新與差異比對。用於「幫我做 X 市場的市調」「建立 X 產業名單」「更新上次的市調」。不產出 PRD 或功能規劃。
---

# PM Market Intel（v1：市調）

面向市場的市調 pipeline。目標是把「市場上有誰、在賣什麼、靠什麼賺錢、缺口在哪」變成可追溯、可定期更新的資料集與報告。

**範圍邊界**：本 skill 到「市場機會結論」為止。**不做** PRD、功能規格、開發排程——那些要等開發決策確認後另行進行。若使用者在本流程中要求 PRD，先完成市調報告，並說明 PRD 不在此 skill 範圍。

---

## 0. 價值框架：功能 / 成本 / 營收

所有分析的第一層切分都用這三個 value lens，而不是產品類別：

| Lens | 客戶買單的理由 | 典型問題 |
|---|---|---|
| **功能（能）** | 能做到原本做不到的事 | 解決什麼痛點？取代什麼現有作法？性能門檻？ |
| **成本（省）** | 用更少的錢/人力/時間/能源達成 | 省多少？ROI/Payback？與替代方案 TCO 比較？ |
| **營收（賺）** | 幫客戶創造新收入 | 新收入來源？商業模式？誰分潤？ |

同一個產品可跨多個 lens；每個 segment 標出**主 lens**（最能打動該客群的那個）。

---

## 1. 工作目錄與產出物

每個市調專案一個資料夾 `market-intel/<project-slug>/`：

```
market-intel/<project-slug>/
├── 00-brief.md              # 範圍定義（Step 1）
├── 10-value-map.md          # 功能/成本/營收 → segment/use case（Step 2）
├── players.yaml             # 市場名單（Step 3，結構見 schemas/player.yaml）
├── evidence.yaml            # 證據庫（全程累積，結構見 schemas/evidence.yaml）
├── 30-comparison.md         # 比較矩陣 + 缺口（Step 4）
├── 40-report.md             # 市調報告（Step 5，模板 templates/report.md）
├── 40-report.docx           # Word 版（scripts/build_docx.py 產出）
└── snapshots/
    ├── players-YYYY-MM-DD.yaml   # 每次更新前的快照
    └── delta-YYYY-MM-DD.md       # 定期更新的差異報告（Step 6）
```

規則：
- 中間產物一律 `.md` / `.yaml`；只有最終報告轉 `.docx`。
- 每一筆事實性陳述都要能指回 `evidence.yaml` 的 `E-xxxx`。沒有證據的推論標 `[推論]`。
- 所有日期用 ISO（YYYY-MM-DD）。

---

## 2. 流程

### Step 1 — 範圍定義（brief）
用 `templates/brief.md` 建立 `00-brief.md`。必填：
- 產品/品類（例：工商業儲能 EMS、IoT gateway）
- 地理範圍（台灣 / 東南亞 / 全球）
- 我方定位（若已知：既有產品、能力、通路）
- 市調要回答的 3–5 個關鍵問題
- 時間範圍（例：近 24 個月的產品與事件）

資訊不足時：先向使用者問**一次**，最多 3 題；若使用者不在，採最合理假設並在 brief 中標 `[假設]`，然後繼續。

### Step 2 — 價值地圖（agents/value-mapper.md）
對每個 lens 列出 2–5 個 segment / use case，每個標：目標客群、痛點、現有替代方案、主 lens、需求驅動因素（法規、電價、補助、技術成熟度…）。產出 `10-value-map.md`。

### Step 3 — 市場名單（agents/landscape-scout.md）
依產業鏈角色建立名單，至少涵蓋：
- `brand`：品牌/原廠
- `installer`：施工/系統整合（SI/EPC）
- `channel`：通路/經銷/平台
- （視品類）`component`：關鍵零組件供應商；`customer`：標竿案場業主

來源優先序：官網產品頁/規格書 PDF > 展覽參展商名錄與展品 > 新聞稿/年報/法說 > 產業報告摘要 > 一般網頁。每個 player 至少 1 筆證據。寫入 `players.yaml` 與 `evidence.yaml`。

### Step 4 — 比較（agents/comparator.md）
用 `schemas/comparison-dims.yaml` 的**固定維度**做比較矩陣（可依品類加維度，但不可刪核心維度，確保定期更新可 diff）。輸出 `30-comparison.md`：
1. 比較矩陣（主要 player × 維度）
2. 定位圖描述（兩軸，由 lens 決定，例：功能完整度 × 價格帶）
3. 缺口（whitespace）：哪個 segment × lens 組合供給不足

### Step 5 — 市調報告
依 `templates/report.md` 寫 `40-report.md`，然後：
```bash
python scripts/build_docx.py market-intel/<slug>/40-report.md
```
產出同名 `.docx`。報告最後一節是「市場機會結論」：值得進入的 segment 排序 + 理由 + 待驗證假設。**不寫功能規格。**

### Step 6 — 定期更新（定期/搜）
使用者要求「更新市調」或由排程觸發時：
1. 複製目前 `players.yaml` 到 `snapshots/players-<today>.yaml`
2. 只跑 landscape-scout 的**增量搜尋**：新進者、新產品、價格/規格變動、退出者、重大事件（募資、併購、標案）
3. 更新 `players.yaml`（更新 `last_verified`，退出者 `status: inactive`，不刪除）
4. 執行：
   ```bash
   python scripts/diff_landscape.py snapshots/players-<上次>.yaml players.yaml > snapshots/delta-<today>.md
   ```
5. 在 delta 報告末尾補 3–5 句「這次變化對市場判斷的影響」

---

## 3. Sub-agent 使用方式

有 Agent/Task 工具時：Step 3 可依角色（brand / installer / channel）**平行**派出 landscape-scout，各自寫回獨立的暫存 yaml，由 orchestrator 合併去重（以公司正式名稱 + 統編/網域判重）。Step 2、4 依序執行，因為後者依賴前者。

沒有 sub-agent 工具時：依序執行各 agent 檔的指示即可。

每個 agent 檔都定義了輸入、輸出、品質門檻；派工時把 agent 檔全文與 `00-brief.md` 一起給 sub-agent。

---

## 4. 證據與品質規則

- **信心等級**：`A` 一手來源（官網、規格書、官方公告、政府資料）；`B` 可信二手（主流媒體、產業研究摘要、展覽官方名錄）；`C` 弱來源（論壇、轉述、業務口頭情報）。
- 報告中的關鍵結論至少要有 1 筆 A 或 2 筆 B 支撐；只有 C 的結論標 `[待查證]`。
- 價格一律記錄幣別、含稅與否、日期、來源；推估價標 `[估]`。
- 市場規模數字必須寫出計算方法（top-down 或 bottom-up）與假設，不可只引一個數字。
- 引用網頁內容時用自己的話改寫，不大段複製。
- 搜尋時用當下年份，優先近 12–24 個月的資料；過時資料（> 24 個月）標註日期。

## 5. 完成檢查清單

- [ ] brief 的每個關鍵問題，報告中都有對應答案或明確標示「資料不足」
- [ ] 每個 player 有 role、lens、至少 1 筆 evidence
- [ ] 比較矩陣使用核心維度，缺值寫 `n/a` 而非留空
- [ ] 報告的數字可回溯到 evidence ID
- [ ] `.docx` 已產出並開啟檢查（標題層級、表格完整）
