---
name: cook-loop
description: vault 自動化任務的 loop 觸發器與 orchestrator。`/cook-loop start` 在開機後啟動 loop（預設 30m tick）；`/cook-loop tick` 由 loop 自動觸發：每日第一個 tick 推 morning brief（WIP 未完項 / 到期複習字 / resurface 舊筆記，純讀取不寫檔），偵測還沒跑過的 promptlingo / cook-meeting 任務並以 auto 模式補跑，平日 09:00–20:00 額外跑 cook-messages 整理 Gmail / Slack 訊息（各自 checkpoint 區間制，零重複），完成後自動 commit（user 已授權豁免詢問）並在 session 內輸出摘要。觸發詞：`/cook-loop`、「啟動每日 loop」、「開啟自動 cook」、「start cook loop」。
argument-hint: "[start [interval] | tick]"
allowed-tools: Skill, Bash, Read, Write, Edit, Glob, Grep
model: sonnet
---

# cook-loop

**這是一個任務指令，不是參考文件。讀完後立即依參數執行對應流程。**

把 vault 的每日整理任務（promptlingo、cook-meeting）變成無人值守的 loop：偵測「還有哪些檔沒跑過」→ 以 auto 模式補跑 → 自動 commit。

設 `SKILL_DIR` 為本檔目錄，`VAULT_ROOT` 為 vault 根目錄。

## 用法

- `/cook-loop start` — 開機後手動跑一次，啟動 loop（預設間隔 `30m`，供 message digest 用；cook 任務冪等，高頻無副作用）
- `/cook-loop start 1d` — 自訂 tick 間隔（不需要 digest 時可調回低頻）
- `/cook-loop tick` — 由 loop 觸發的單次執行；也可手動跑來立即補跑

---

## `start` 流程

1. **環境檢查**：
   - `uv --version` 可用
   - `git -C "$VAULT_ROOT" status --porcelain` — 若有未 commit 變更，提醒 user（不阻擋，tick 只會 commit 自己寫的檔）
2. **先跑一次 tick**（見下方），把積欠的任務立即補掉。
3. **啟動 loop**：呼叫 Skill tool → `loop`，args：`<interval，預設 30m> /cook-loop tick`
4. **提醒 user 維運限制**：
   - loop 是 session-scoped：關掉這個 terminal / session 就停
   - loop 最長跑 **7 天**，到期或重開機後要重新 `/cook-loop start`
   - 防睡眠：建議用 `caffeinate -is claude` 啟動 session，或插電並關閉系統睡眠

## `tick` 流程

> [!important] staging 模型
> cook-meeting / cook-messages **不再直接寫 vault**,而是把產出放進 `_staging/`(`reviewed: false`)。機器控制欄位藏在 body 的 `<!--cook-staging ... -->` 註解裡,frontmatter 只留 `reviewed`,所以 Obsidian Properties 面板乾淨。user 在 Obsidian review、把 `reviewed` 翻成 `true` 後,由 `cook-staging` 正式寫入並刪 staging 檔。tick 開頭(Step 0)先 flush 上次審好的。**只有 promptlingo 仍直接寫 vault。**

### Step 0 — Flush 已審核的 staging

tick 一開始先把 user 上次 review 好的寫進 vault:呼叫 Skill tool → `cook-staging`(它會 promote `reviewed: true` 的檔、append `_log.md`、刪 staging、只 commit 實際 promote 的檔)。無已審核項時它自然 no-op。失敗不中斷 tick。

### Step 1 — 偵測待辦

```bash
uv run "$SKILL_DIR/scripts/loop_status.py" --days 7
```

輸出 JSON：

- `promptlingo_pending` — 有 transcript 但缺 `<DATE> English Daily.md` 的日期
- `meetings_pending` — frontmatter 缺 `parsed:` 且 mtime 超過 2 小時的 raw 會議檔
- `progress_stale` — WIP `last_updated` 超過 7 天的專案（**只提醒，不自動跑** cook-progress 口語模式，因為它需要 user 口語輸入）
- `progress_checked` — WIP 有 `- [x]` 打勾未搬項的專案（`[{project, checked}]`）→ Step 2.7 自動掃勾直寫（不需口語輸入）
- `digest` — message digest 視窗：`is_work_window`（平日 09:00–20:00 Asia/Taipei）+ gmail 的 `due` 與現成的查詢區間（`gmail_query`）。**所有時間計算都在 script 內完成，不要自己推算區間。**

cook 任務全空、`progress_checked` 空、digest 非 due、且 `brief.due` 為 false → 回報「無待辦」，結束（不寫檔、不 commit）。

### Step 1.5 — Morning Brief（`brief.due: true` 才執行，每日一次）

**讀取管線**：把 vault 主動推回來，不等 user 去查。純讀取、只輸出到 session，**不寫任何筆記、不進 commit**。

1. **複習字**：`uv run "$VAULT_ROOT/.claude/skills/promptlingo/scripts/due.py" <today> --limit=5`，取回今日到期的 Leitner 複習字。失敗不中斷，該區塊省略。
2. **WIP 未完項 / resurface**：直接用 Step 1 的 `brief.wip`、`brief.resurface`，不另查。
3. 組 `📤 Morning Brief` 區塊（見 Step 5），在 session 輸出。
4. **推進 checkpoint（防一天多推）**：brief 輸出後立即執行
   ```bash
   uv run "$SKILL_DIR/scripts/digest_state.py" set brief <brief.now_iso>
   ```
   失敗時 checkpoint 不動，下個 tick 會重推（可接受，無副作用）。
5. brief 是純讀取，**不 append `_log.md`、不列入 `WRITTEN_FILES`**。

### Step 2 — 依序補跑（用 Skill tool，逐項執行）

執行順序固定（舊日期優先）：

1. 每個 `meetings_pending` 路徑 → `Skill(cook-meeting, args: "<VAULT_ROOT>/<path> --auto")`
2. 每個 `promptlingo_pending` 日期 → `Skill(promptlingo, args: "<YYYY-MM-DD>")`

規則：

- 單項失敗**不中斷整個 tick**：記下錯誤，繼續下一項，最後一併回報
- meetings 現在只產 `_staging/` 檔(不進 vault、不進 commit);只有 **promptlingo 直接寫 vault**,把它實際寫入的檔記到 `WRITTEN_FILES`(commit 用)
- 同一日期重跑是安全的:偵測「輸出檔存在就跳過」,且 staging 類 skill 若 `_staging/` 已有同 target 檔會自行跳過(不覆蓋 user 編輯中的檔);故一項在「已 staged 未 flush」期間會被 loop_status 持續標為 pending,skill 每 tick 跳過即可,flush 後 vault 檔出現就不再標

### Step 2.5 — Message Digest（gmail `due: true` 才執行）

1. 呼叫 Skill tool → `cook-messages`，args 直接帶 Step 1 輸出的現成值：

   ```
   gmail --gmail-query '<digest.gmail.gmail_query>' --from <window_start_iso> --to <window_end_iso>
   ```

2. **Checkpoint 推進（防重複的核心）**：
   - cook-messages 成功產出後，立即執行：
     ```bash
     uv run "$SKILL_DIR/scripts/digest_state.py" set gmail <window_end_iso>
     ```
   - cook-messages 回報失敗（輸出含 `⚠️ gmail digest 失敗`）→ **checkpoint 不動**，下個 tick 自動重新涵蓋同區間

3. digest 失敗（含 MCP 未授權 / 過期）**不中斷 tick**：記到 `_log.md`，cook 任務照常進行。

### Step 2.6 — Slack Digest（slack `due: true` 才執行）

1. 呼叫 Skill tool → `cook-messages`，args 帶 Step 1 的 `digest.slack` 現成值：

   ```
   slack --slack-after <slack.window_start_epoch> --slack-before <slack.window_end_epoch> --from <slack.window_start_iso> --to <slack.window_end_iso>
   ```

2. **Checkpoint 推進**：
   - cook-messages 成功產出後，立即執行：
     ```bash
     uv run "$SKILL_DIR/scripts/digest_state.py" set slack <slack.window_end_iso>
     ```
   - 回報失敗（輸出含 `⚠️ slack digest 失敗`）→ **checkpoint 不動**，下個 tick 自動重涵蓋同區間

3. Slack 與 Gmail 兩個 checkpoint **各自獨立**：一邊失敗不影響另一邊推進。Slack digest 失敗不中斷 tick。

### Step 2.7 — 自動掃勾 WIP→Done（`progress_checked` 非空才執行）

user 在 Obsidian 手動打勾的 `- [x]` 條目不會自己搬走。這步把它們自動搬到 Done：

1. 對每個 `progress_checked` 專案，呼叫 Skill tool → `cook-progress`，args：`<project> --sweep`
2. sweep 模式**直接寫 vault**（不預覽、不詢問），把該專案 WIP 的打勾項搬成 Done 的一次 changelog release、從 WIP 移除。把它實際寫入的兩個檔（`Action Items - WIP.md` + `Action Items - Done.md`）記到 `WRITTEN_FILES`（commit 用）。
3. 單項失敗**不中斷 tick**：記下錯誤繼續下一個專案，最後一併回報。

> 這是 cook-progress **唯一**跳過預覽 gate 的路徑——授權來自「user 已手動打勾」這個明確動作。口語模式永遠不自動跑（見設計備忘）。

### Step 3 — Append `_log.md`

```markdown
## [<today>] cook-loop tick

- meetings staged: <N>（<檔名清單，無則省略>）
- messages staged: <N 項，無則省略>
- promptlingo: <日期清單 或 無>（直接寫入）
- progress swept: <每個掃勾專案 `專案 → Done vX.Y.Z`，無則省略>
- digest: <gmail <HH:MM>–<HH:MM> N 封 ・ slack <HH:MM>–<HH:MM> N 則，未跑的省略>
- 失敗: <項目 + 原因，無則省略>
- progress 提醒: <stale 專案清單，無則省略>
```

**Digest-only tick 不寫 `_log.md`**（30 分鐘一次會灌爆 log）;只有本 tick 有 staged 產出 / promptlingo 寫入 / progress swept、或 digest **失敗**時才 append。flush 促成的 vault 寫入由 Step 0 的 cook-staging 自行記 `_log`,此處不重複。

### Step 4 — 自動 commit（user 已授權，不需詢問）

**只 add 本次 tick 直接寫入的檔案**(`WRITTEN_FILES`,現在僅 promptlingo + `_log.md`),**絕對不要 `git add -A` / `git add .`** — vault 可能有 user 手動編輯中的未 commit 檔案,不可掃進來。meetings / messages 只在 `_staging/`(gitignore),不在此 commit;它們的 vault 寫入由 Step 0 的 cook-staging 負責 commit。

```bash
git -C "$VAULT_ROOT" add <每個 WRITTEN_FILES 路徑> _log.md
git -C "$VAULT_ROOT" commit -m "chore(loop): auto cook tick <YYYY-MM-DD>"
```

無任何寫入時跳過此步。

### Step 5 — Session 回報

在 session 內輸出本次 tick 摘要。格式：

```markdown
🍳 **cook-loop tick** <YYYY-MM-DD HH:MM>
TL;DR：🔴 <N> 需處理 ・ ⚪ <N> FYI ・ cooked <N> 項（沒有的部分省略）

> 📤 **Morning Brief**

**🗂️ WIP（<未完項總數>）**
↳ <每個有未完項的專案一行：`專案名 (open N)：最舊/最關鍵一兩項`>

**🔁 複習**
↳ <due.py 回傳的字，逗號分隔；無則「今日無到期」>

**💡 Resurface**
↳ [[<resurface.title>]] — <讀該筆記後一句話勾起記憶的提示>

> 📋 **Meeting**（<N> 份）

**<檔名>**
↳ <2-3 句重點總結（決議 / action items 數量）>

> 🗣️ **Promptlingo**

- <日期清單>

> ✅ **Progress swept**（<N> 專案）

- <每個掃勾專案一行：`專案名 → Done vX.Y.Z（搬 N 項）`>（無則整個區塊省略）

> 📥 **Staging**（待 review <N>）

- <每個 `_staging/*.md`（排除 README）一行：檔名 → target_path（target_path 讀 body 開頭的 `<!--cook-staging ... -->` 控制註解）>
- ↳ 提醒：在 Obsidian 編輯後把 Properties 的 `reviewed` 設為 `true`，下次 tick 或 `/cook-staging` 才會寫入 vault

> 📧 **Gmail**（<HH:MM>–<HH:MM>，<N> 封）

<cook-messages 的 Gmail 區塊原樣帶入（已是兩行式 + 空行分隔）>

> 💬 **Slack**（<HH:MM>–<HH:MM>，<N> 則）

<cook-messages 的 Slack 區塊原樣帶入（兩行式 + permalink）>

> ⚠️ **失敗**

- <項目 + 原因>（無則整個區塊省略）

> 🔔 **Progress 提醒**

- <stale 專案清單>（無則整個區塊省略）
```

規則：

- **排版三鐵則**：(1) 每個 `>` 區塊標題前後各空一行；(2) 區塊內每個項目之間空一行；(3) 詳細內容一律放 `↳` 開頭的第二行，第一行只放「標題級」資訊。文字牆 = 失敗
- **沒有內容的區塊整個省略**（包含標題），不要留空區塊；digest 回報「無新訊息」也省略
- Meeting 區塊要附**任務總結**（從剛 cook 完的輸出檔提煉），promptlingo 只列日期即可
- **Morning Brief 區塊只在 `brief.due` 為 true 的那個 tick 出現**（每日第一個 tick），之後當天的 tick 省略
- Resurface 的提示要真的讀過該筆記再寫，不要只覆述標題
- 不附 commit hash
- **完全無待辦、digest 無新訊息、且 brief 非 due 的 tick 不輸出摘要**（避免雜訊），但有失敗或 progress stale 提醒時仍要輸出

---

## 設計備忘

- **staging → review → flush**：meetings / messages 一律先寫 `_staging/`（`reviewed: false`），user 在 Obsidian 審核翻成 `true`，`cook-staging` 才 promote 進 vault 並刪 staging 檔。統一了手動/auto 兩條路徑（都先 stage），消掉舊 auto 繞過 review 的漏洞。promptlingo 是唯一例外（直接寫）。tick 開頭（Step 0）先 flush 上輪審好的，形成「上輪 promote → 本輪產新 staging」的節奏。
- **staged 但未 flush 期間會被 loop_status 持續標 pending**：因偵測看的是 vault 最終輸出檔。staging 類 skill 靠「`_staging/` 已有同 target 檔就跳過」保證不重生、不覆蓋 user 編輯;flush 後 vault 檔出現即不再標。這是刻意取捨（不改 loop_status 偵測邏輯）。
- **狀態不另存檔**（cook 任務）：「跑過沒」一律從輸出檔反推（report 檔 / frontmatter `parsed:`），重跑零成本。
- **Digest 是上述原則的唯一例外**：訊息摘要沒有輸出檔可反推，必須用 checkpoint（`state/digest_state.json`，已 gitignore — 純機器狀態，每 30 分鐘變動，進版控只會製造雜訊 commit）。視窗語義 `[start, end)`，成功才推進，保證跨 tick 零重複、失敗不漏。
- **時間計算只在 Python**：work window 判斷、區間換算（ISO/Gmail query 邊界）全在 `loop_status.py`，SKILL 與 LLM 只消費現成值。
- **不處理「今天」**（cook 任務）：今天的對話還在進行中，偵測視窗是昨天往回 7 天；今天的資料明天的 tick 自然補上。digest 不受此限（即時訊息）。
- **新增高頻任務**：在 `loop_status.py` 加偵測欄位 + 本檔 Step 2 加一行即可，tick 本身冪等不怕高頻。
- **Morning Brief 是讀取管線（與 cook 任務的寫入相反）**：loop 整體是寫入 vault，brief 反向把 WIP / 複習 / 舊筆記推回 session，治「只進不出」。設計上刻意**不寫筆記**（vault 已過載），純 session 輸出。「每日一次」沿用 digest 同套 checkpoint（`brief.last_end` 存日期，date != today 才 due），與 gmail 共用 `digest_state.json`。resurface 用 day-ordinal 輪播達成 stateless 每日換一篇。
- **cook-progress 口語模式永遠不自動跑**：它的輸入是 user 的口語回報，loop 只做 `progress_stale` staleness 提醒。**例外是 `--sweep` 自動掃勾模式**（Step 2.7）：輸入是 user 已在 WIP 手動打勾的 `- [x]` 條目，勾選本身即完成授權，故可全自動直寫；這是唯一跳過 cook-progress 預覽 gate 的路徑。偵測（哪些專案有打勾未搬）在 `loop_status.py` 的 `progress_checked`，搬移判斷（changelog 分類 / 版號）是 skill 內的 LLM 工作。
- **session 斷掉 / loop 過期重啟後**：checkpoint 持久化在檔案，第一個 tick 自動涵蓋斷線期間（上限 7 天），不漏不重。
