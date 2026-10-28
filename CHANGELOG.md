# Changelog

## 1.1.0 — 2026-10-28

定位調整為 **PM 工具**（產品判斷），而非業務工具（名單開發）。

### 修正
- `diff_landscape.py`：`inactive → active` 狀態轉移未被偵測
- `diff_landscape.py`：重複 ID 會被後一筆靜默覆蓋；現在直接報錯（exit 2）
- `build_docx.py`：Markdown 連結未轉成超連結；表格內 `\|` 被誤切成額外欄位
- comparator 不再要求「至少三個缺口」，避免硬湊機會

### 新增
- `validate.py`：ID 唯一性與格式、必填、列舉、全部 ID 引用（含 .md 內文）、teardown 檔存在、證據強度不得高於規則值
- `merge_scout.py`：平行 scout 各寫輸出包，由腳本統一分配正式 ID、判重、改寫引用
- `snapshot.py`：唯一 run-id 快照與 `runs/index.yaml`，解決同日重跑覆寫與「上次」不明確
- `diff_landscape.py`：比較證據與機會假說，輸出「需重新檢視」清單，完成更新閉環
- `build_docx.py`：寬表格自動橫向頁、表頭跨頁重複、引用區塊、斜體
- agent `teardown`：競品深度拆解（能力邊界、架構整合、導入代價、設計取捨、迭代訊號、使用者聲音）
- agent `opportunity-framer`：可證偽的產品機會假說，含反證、kill criteria、最便宜的驗證步驟、數量級規模感
- 證據模型：`claim_type`（主張類型）與 `confidence`（來源可靠度）分離，`origin` 判斷獨立性，`valid_until`、`scope`、`contradicts`
- 缺口分類：供給缺口／資訊缺口／待驗證假說
- 需求面依使用者／採購者／決策者拆解痛點，加入替代方案與切換障礙
- 覆蓋率表與搜尋停止條件；「搜不到／讀不到／未查核」分開記錄
- `tests/test_scripts.py`：17 個測試

### 變更
- `players.yaml`：`role` 改為 `roles`（list），新增 `depth`、`teardown`；`segments` 改用 `S-NN` ID；移除 `customer` 角色，新增 `platform`
- 比較維度改為產品取向（能力邊界、架構、整合、導入成本、UX、設計取捨、迭代、切換成本、使用者聲音）；價格降為輔助
- 名單規模由每角色 15–40 家改為 5–8 家代表性 player
- TAM/SAM/SOM 改為前 3 名假說的數量級估算
- 報告結構改為「需求 → 供給 → 取捨 → 缺口 → 機會假說 → 驗證計畫」，檔名改為 `50-report.md`

## 1.0.0 — 2026-10-28
- 初版：功能/成本/營收框架、市場名單、競品比較、Word 報告、定期 diff
