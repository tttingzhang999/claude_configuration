---
name: cook-messages
description: 整理指定時間區間內「跟 Your Name 有關」的 Gmail / Slack 訊息，產出分級摘要（🔴 需處理 / ⚪ FYI）。對每則 🔴 且能對應到已知專案的訊息，額外分類目的地（Action Items / Meeting / Keypoint）並寫入 `_staging/`（等待 cook-staging 審核後才真正進 vault）。時間區間完全由參數決定，呼叫者（cook-loop）負責 checkpoint；本 skill 從不直寫 vault 路徑、也不發訊息。觸發詞：`/cook-messages`、「整理我的訊息」、「幫我看 inbox」。
argument-hint: "[gmail|slack] (gmail: --gmail-query '<q>' | slack: --slack-after <epoch> --slack-before <epoch>) --from <ISO> --to <ISO>"
allowed-tools: ToolSearch, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Slack__slack_search_public_and_private, mcp__claude_ai_Slack__slack_read_thread, Read, Write
model: sonnet
---

# cook-messages

**這是一個任務指令，不是參考文件。讀完後立即依參數執行。**

整理時間區間內跟 user（Your Name）有關的 Gmail / Slack 訊息，回傳 session 摘要；並對能對應到專案的 🔴 訊息額外寫入 staging 草稿。一次只跑一個來源（由第一個位置參數決定）。

## 設計約束（必守）

- **雙輸出，非純函數但仍不直寫 vault**：本 skill（1）一律回傳 markdown session 摘要給呼叫者，（2）**可能**額外把 🔴 訊息寫成草稿到 `_staging/`（見下方「分類與 staging」）。除 `_staging/*.md` 外不寫任何其他檔案，不改 vault 內既有筆記，不發送任何訊息。
- **不自己算時間**：一律使用參數給的 query / epoch，缺參數時才向 user 要，不要自行推算區間。
- MCP 工具 schema 未載入時先用 ToolSearch 載入。
- 任一來源失敗不影響另一來源：照常產出成功的部分，失敗的在輸出尾端標註。

## 參數

- 第一個位置參數：`gmail`（預設）或 `slack` — 一次跑一個來源
- **Gmail**：`--gmail-query '<query>'` — 現成搜尋字串（例 `in:inbox after:1781229600 before:1781234046`）
- **Slack**：`--slack-after <epoch>` / `--slack-before <epoch>` — Unix 秒，本 skill 用它拼兩條 search query
- `--from <ISO>` / `--to <ISO>` — 人類可讀的區間，只用於輸出標題顯示

手動呼叫沒給 query/epoch 時：請 user 提供區間（或明說「過去 N 小時」），不要自行推算 — 推不出來就問，不要猜。

## Gmail 流程

1. `mcp__claude_ai_Gmail__search_threads(query=<--gmail-query>, pageSize=50)`，有 `nextPageToken` 就翻頁取完
2. 同一 thread 只取區間內的新訊息；snippet 不足以判斷重要性時，對「看起來需要 user 動作」的信用 `get_thread` 看全文（最多 3 封，控成本）
3. 分級（**寬召回優先：判不準就歸 🔴，寧可多納讓 user 人工濾，也不要漏掉他該知道的**）：
   - 🔴 **需處理 / 需知道**：直接問 Your Name、要求回覆/審核、會議邀請變動、deadline，**以及任何跟 Your Name 專案相關、他可能需要知道的內容（決策、進度、風險、stakeholder 動態）**——判不準時一律歸 🔴
   - ⚪ **FYI**：純系統/通知類（Jira/Calendar/系統信）、電子報、與 Your Name 專案無關的 cc

## Slack 流程

Slack 沒有收件匣，用兩條 search 拼出「跟 Your Name 有關」（`slack_user_id` 讀自 `config.json`，目前 `YOUR_SLACK_USER_ID`）。兩條都帶 `after=<--slack-after>`、`before=<--slack-before>`、`sort=timestamp`、`response_format=detailed`、`include_context=false`，有 `cursor` 就翻頁取完：

1. **DM + 群組 DM**：`slack_search_public_and_private(query="to:me", channel_types="im,mpim", ...)`
2. **@mention 我**：`slack_search_public_and_private(query="<@YOUR_SLACK_USER_ID>", channel_types="public_channel,private_channel", ...)`

合併兩條結果，**三道處理**：

- **濾 bot**：帶 `[BOT]` 標記或 sender ID `U00`（standup 提醒 bot）→ 丟
- **濾自己**：sender user ID == `slack_user_id`（自己引用回覆帶到自己 mention）→ 丟
- **併 thread**：同 `channel_id + thread_ts` 的多則併成一則

分級（Slack 已用 `to:me` + `@mention` 圈過範圍，**同樣寬召回優先：判不準歸 🔴**）：

- 🔴 **需處理 / 需知道**：DM / 群組 DM 問我、頻道裡點名我，**或我專案頻道（`slack_channels` 命中）裡我可能需要知道的討論（決策 / 變更 / 風險 / stakeholder 動態）**——判不準時歸 🔴
- ⚪ **FYI**：bot / 純系統通知 / 與我及我專案都無關的閒聊

只有 `detailed` 內容不足以判斷時，才用 `slack_read_thread(channel_id, message_ts)` 展開全串（最多 3 串，控成本）。每則保留 `Permalink` 供輸出與 staging 來源用。

## 分類與 Staging（僅 🔴 訊息）

⚪ FYI 訊息**永不** staging，只進 session 摘要。對每則 🔴 訊息，額外判斷它是否能對應到一個已知專案，並分類目的地；分類與寫檔都在完成分級之後、輸出摘要之前進行。

### Step A — 對應專案

讀兩個來源：本 skill 目錄下的 `config.json`（Slack 頻道對應、`project_map`），以及 `01 Work/stakeholders.md`（Gmail 寄件人對應）。

- **Slack**：先用訊息的頻道（`#name` 或 channel ID）查 `config.json` 的 `slack_channels` map → 命中直接落該專案（**強訊號，優先**）；沒命中再用 `project_map` 語意比對。DM 沒有頻道，直接走語意比對。
- **Gmail**：Read `01 Work/stakeholders.md`（**強訊號，優先**），依它「對應規則」section 用寄件人 email 比對——先找某列「Email」欄完整命中，沒有再找某列「網域」欄命中 → 命中直接落該列的「專案」；都沒命中再用主旨關鍵字、thread 內容跟 `config.json` 的 `project_map` 各專案做語意比對。（`01 Work/stakeholders.md` 不存在或表格全空時，直接走語意比對。）

**對應不到任何專案就不 staging**——該則訊息只留在 session 摘要裡，不產生 staging 檔。

### Step B — 分類目的地（挑最貼切的一種；**寧可歸進來讓 user 人工濾，也不要直接丟掉**）

- **Action Items** → 這是 Your Name 本人必須執行的任務，或 Your Name 需要主動追蹤他人是否完成的 follow-up。
  **務必遵守 `01 Work/CLAUDE.md` 的 Action Items 範圍**：PM 主導事項、團隊整體待辦、ExampleClient 窗口工項**不**進 Action Items——但若 Your Name 可能需要知道，改歸 **Keypoint**（不要直接丟掉）。
  target: `01 Work/projects/<P>/Action Items - WIP.md`，`op: append`
- **Meeting** → 訊息內容是會議通知/記錄/紀要本體。
  target: `01 Work/projects/<P>/meetings/<slug>.md`，`op: write`（新筆記）
- **Keypoint（含「需知道」catch-all）** → 架構決策、stakeholder 異動、系統限制等值得長期保留的知識點，**以及任何 Your Name 可能需要知道、但不是他本人 task 的專案相關內容**。判不準就歸這裡，並在 body 開頭加 `> [!question] 待確認：<一句話說為何 stage 進來>`，讓 user 一眼看出這是待人工判斷的。
  target: `01 Work/projects/<P>/keypoint/<slug>.md`，`op: write`（新筆記）

只有**真雜訊**（bot / 純系統通知 / 與任何專案都無關）才不 staging。

### Step C — 寫入 staging 檔

1. 算 `slug`：把 `target_path` 中的 `/`、空格、結尾 `.md` 都換成 `_`（例：`01 Work/projects/ExampleProject/Action Items - WIP.md` → `01_Work_projects_ExampleProject_Action_Items_-_WIP_md`）。
2. staging 檔路徑：`<vault>/_staging/<slug>.md`。**冪等處理**（放寬後多條也要納入，別只留第一條）：
   - `op: write`（Meeting / Keypoint，slug 各自唯一）：該檔已存在就整則跳過（不覆寫）。
   - `op: append`（Action Items，同專案共用一個 slug）：該檔已存在時**不要整則跳過**，改用 **Read** 讀出後把新 bullet **append 到同一檔 body**（只有與檔內已有 bullet 語意重複的才跳過）——這樣同專案多條 action item 都會被納入。
     該檔會在下次 `cook-staging` flush 後清空，之後的 run 可再重新 staging。
3. 用 **Write** 寫入。**機器控制欄位放 body 開頭的 `<!--cook-staging ... -->` 註解裡,frontmatter 只留 `reviewed`（append 型）或 `reviewed` + 筆記自身 frontmatter（新筆記）**。這樣 Obsidian Properties 面板只顯示 `reviewed` 與筆記正式欄位,不被機器欄位灌爆;註解在 Live Preview / Reading 模式隱藏。時間戳一律 `Asia/Taipei`（`+08:00`）。**具體 frontmatter/註解模板見 [reference/staging-format.md](reference/staging-format.md)。**

4. 每則 staging 動作在 session 摘要尾端追加一行提示（例：`> 🗂️ 已 staging N 則 → _staging/`），讓呼叫者知道有新草稿待 `cook-staging` 審核。**不要**在此附加 `_log.md`（那是 `cook-staging` 的職責），也**不要**直接寫 `01 Work/projects/**` 下的任何檔案。

## 輸出格式（直接作為本 skill 的最終輸出）

每則訊息固定**兩行**：第一行「分級 + 來源 + 標題」，第二行 `↳` 開頭放一句話摘要。訊息之間、區塊之間**都空一行**，不要讓文字黏在一起。**只輸出本次實際跑的來源區塊。Gmail / Slack 的具體排版模板見 [reference/output-format.md](reference/output-format.md)。**

規則：

- **每則兩行、則與則之間空行**——這是可讀性的核心，不可壓縮回單行
- Gmail 寄件人用顯示名不用 email（`Alice Chen` 而非 `alice@example.com`）
- Slack 頻道用 `#name`，DM 用 `DM · <發話人>`；摘要行尾一律附 `[原訊息](<permalink>)`
- **主旨/訊息截斷到 ~30 字**：Gmail 去掉 `Re:`/`Fwd:`/`更新邀請函：` 前綴與 calendar 信的日期時間尾巴（日期資訊放摘要行）
- 摘要行一句話為限，明確說「需要什麼動作」（回覆 / 確認 / 純知悉）
- 時間用 `--from/--to` 的 HH:MM（跨日時帶日期）
- 區間內無相關訊息的來源輸出 `> 📧 **Gmail**（…）：無新訊息` / `> 💬 **Slack**（…）：無新訊息`（單獨一行，呼叫者據此省略區塊）
- 某來源失敗時輸出 `> ⚠️ <來源> digest 失敗：<原因>`，呼叫者據此決定不推進該來源的 checkpoint
- 同一 thread / 同一寄件人 / 同一 Slack thread 的連續訊息合併成一則（摘要行彙總）
- 摘要用繁體中文，人名、主旨關鍵字保留原文
