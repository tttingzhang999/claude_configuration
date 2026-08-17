---
name: cook-meeting
description: 將開會時邊記邊寫的 raw markdown 檔案重新整理成符合 vault 規範的會議紀錄（補 frontmatter、TOC、結構化章節、callouts），並擷取 action items 同步到專案的「Action Items - WIP.md」。**產出寫入 `_staging/` 供審核，不直接改 vault**：審核方式為編輯 staging 檔並設 `reviewed: true`，再由 `cook-staging` / `cook-loop` 正式 promote。觸發詞：「cook 這份會議紀錄」、「整理會議記錄」、「把這份 raw 變正式格式」、「把這篇歸檔到專案」、「format meeting notes」。當 user 給 `01 Work/projects/*/meetings/*.md` 路徑並要求整理 / 歸檔時，務必使用此 skill，不要直接動手寫。
argument-hint: "<raw meeting file path> [--auto]"
allowed-tools: Read, Write, Bash, Glob, Grep
model: sonnet
---

# cook-meeting

**這是一個任務指令，不是參考文件。讀完後立即從 Step 1 開始執行，不要只回答「我會做」就停下。**

把使用者開會時邊記邊寫的 raw `.md` 會議檔，重新煮成符合 vault 規範的會議紀錄，並把擷取出的 action items 同步到該專案的 `Action Items - WIP.md`。

> [!note] `cooked` 閘門
> 會議 frontmatter 的 `cooked` 是「會後是否已讓 LLM 整理過」的旗標。User 開會邊寫的 raw 檔 `cooked` 缺或為 `false`；本 skill cook 完，在產出的會議紀錄 frontmatter 標 `cooked: true` 與 `keypoints_synced` / `action_items_synced`。`--scan` 模式即據此挑出未處理（`cooked != true`）的會議。

> **強制流程**：Step 1–3 在記憶體裡完成，Step 4–5 把結果寫成兩份 `_staging/` 草稿（不直接改 vault）。Review 由使用者編輯 staging 檔並把 `reviewed` 改成 `true`，之後由 `cook-staging`（或 `cook-loop` tick）正式 promote 進 vault。任何情況下不可跳過 staging，直接寫入 `01 Work/projects/**` 下的檔案。

## 觸發

- `/cook-meeting <raw file path>` — 明確指定檔案
- `/cook-meeting <raw file path> --auto` — 無人值守模式（由 [[cook-loop]] 呼叫），見 Step 4 的 auto 規則
- `/cook-meeting`（無參數）— 從對話上下文取最近被提到的會議檔
- `/cook-meeting --scan [PROJECT]` — 掃 `meetings/` 下 `cooked != true`（或缺 `cooked`）的會議，逐一 cook（未指定 PROJECT 則掃全部專案）
- 自然語言：「cook 這份會議紀錄」、「幫我整理這份開會 raw」、「把這篇歸檔到專案」、「整理還沒處理的會議」

## 前提

Raw 檔必須位於：

```
<VAULT_ROOT>/01 Work/projects/<PROJECT>/meetings/<filename>.md
```

如果路徑不符合（例如沒有 `meetings/` 父資料夾或不在 `01 Work/projects/` 下），**告知 user 並停止**，不要強行處理。

---

## 流程

設 `VAULT_ROOT = {base_url}`，路徑交給工具之前先依 `rules/00-machine-paths.md` 解析 `{base_url}`。

### Step 1 — 解析參數與上下文

從 `$ARGUMENTS` 或對話中取得 raw 檔絕對路徑；`$ARGUMENTS` 含 `--auto` 時設 `AUTO = true`（影響 Step 4 / Step 6）。

從路徑推斷：

- `PROJECT` = `01 Work/projects/` 後的第一段目錄名
- `MEETING_DATE` = 從檔名前 8 碼推斷 `YYYY-MM-DD`（例如 `20260612 GC ExampleClientB.md` → `2026-06-12`）；若檔名不含日期，從 frontmatter 找；都沒有就用 today

如果 `PROJECT` 推不出來或 raw 檔不存在 → 報錯停止。

### Step 2 — 蒐集上下文（並行 Read）

並行讀以下三個來源，作為 cook 時的參考：

1. **Raw 會議檔**：完整內容
2. **同專案最近一份已整理的會議檔**：用 `ls -t` 取 `01 Work/projects/<PROJECT>/meetings/` 下最新且**不是**本檔的 `.md`，讀來當「格式錨點」
3. **該專案的 WIP**：`01 Work/projects/<PROJECT>/Action Items - WIP.md`（用於去重，並確認 `## 進行中` 區段的真實標題文字，供 Step 5 的 `append_anchor` 使用）

如果該專案沒有其他會議檔，沿用 [`reference/meeting-note.md`](reference/meeting-note.md) 的「標準模板」。
如果 WIP 不存在，視為空。

### Step 3 — Cook（in-memory，**不寫檔**）

產出三樣東西，先放在記憶體：

#### 3a. 新的會議檔內容

依 [`reference/meeting-note.md`](reference/meeting-note.md) 的 frontmatter 強制欄位、固定 body 結構與 cook 規則產出會議紀錄內容。若該專案沒有其他會議檔可當格式錨點，改用同檔的「標準模板」。

#### 3b. 待新增的 Action Items

- 從 raw 中抽出**所有**待辦條目
- 跟現有 WIP 內容比對，**只保留新增**（用語意比對，不是 exact match）
- 每條開頭用具體動詞（提供 / 確認 / 詢問 / 部署...）
- 預計 append 到 WIP `## 進行中` 區段下的新 subsection：
  ```markdown
  ### <主題> （來源：[[<會議檔名（不含 .md）>]]）

  - [ ] ...
  ```

#### 3c. 建議 promote 到 keypoint/ 的條目

掃描 raw，若有以下任一性質的內容，列為「建議 promote」（**不自動寫**）：

- 架構決策 / 設計選型
- Bug 根因 / 系統限制
- Stakeholder 角色關係
- 長期不變的事實（如「UT/UAT Node 晚上八點關」）

只列出標題與一句摘要，由 user 自行決定要不要 promote 到 `01 Work/projects/<PROJECT>/keypoint/`。

### Step 4 — Raw 快照 commit（安全備份）

Raw 檔最終會在 review 通過後被 `cook-staging` 覆寫成正式格式，先進 git 確保永遠可回復。命令**只 add 這一個 raw 檔**，不用 `git add -A`：

```bash
git -C "$VAULT_ROOT" add "<raw 檔路徑>"
git -C "$VAULT_ROOT" diff --cached --quiet -- "<raw 檔路徑>" || \
  git -C "$VAULT_ROOT" commit -m "chore(<project-slug>): snapshot raw meeting <檔名>"
```

- **`--auto` 模式(cook-loop 呼叫)**：直接執行,不問（vault commit 規則的 cook-loop 例外）。
- **互動模式(`/cook-meeting`)**：**先問使用者是否要 snapshot commit**,同意才執行;否則跳過,在 Step 6 回報「raw 尚未 snapshot」。不要靜默 commit。

**`--auto` 模式的敏感資訊安全閥**：raw 含密碼 / token / API key 時，**不要產出 staging**，跳過此檔並在回報中 flag，留給手動處理；其餘步驟正常進行到 Step 6 回報。

### Step 5 — 產出 staging 檔案（冪等，跳過已存在）

依 [`reference/staging-files.md`](reference/staging-files.md) 產出兩份 `_staging/` 檔：

- **檔 1** — 正式會議紀錄（`op: overwrite`），內容用 Step 3a
- **檔 2** — WIP action items（`op: append`），內容用 Step 3b；去重後無新增項目就**不產出**此檔，在回報中註明「無新增 action items」

slug 命名、冪等跳過、frontmatter / `<!--cook-staging-->` 欄位與 `append_anchor` 規則見該 reference。

### Step 6 — 回報

兩種模式都輸出（`--auto` 模式不等待回覆，其餘一致）：

```
🍳 已 cook：<raw 檔相對路徑>
專案：<PROJECT>　日期：<YYYY-MM-DD>

已產出 staging（待審核）：
[1] _staging/<slug1>.md → overwrite → <target_path_1>
[2] _staging/<slug2>.md → append → <target_path_2>（N 個新項目，已去重）
    （若任一份已存在，改標註「已存在，跳過」）

建議 promote 到 keypoint/（M 項，不會自動寫）：
- <標題> — <一句摘要>
...

Review 方式：編輯上述 staging 檔，確認無誤後把 frontmatter 的 reviewed 改成 true，
再跑 /cook-staging（或等 cook-loop 下一個 tick）即會正式寫入 vault。
```

---

## Reference（按需載入）

- [`reference/meeting-note.md`](reference/meeting-note.md) — 正式會議紀錄的 frontmatter 欄位、body 結構、cook 規則、標準模板（Step 2 / 3a）
- [`reference/staging-files.md`](reference/staging-files.md) — 兩份 staging 檔的格式、slug 規則、冪等檢查、`cook-staging` 控制欄位（Step 5）
- [`reference/edge-cases.md`](reference/edge-cases.md) — 邊界情境處理表與「不做的事」清單

```

```
