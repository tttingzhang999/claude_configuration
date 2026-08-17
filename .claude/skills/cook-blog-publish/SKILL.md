---
name: cook-blog-publish
description: 把 Obsidian vault `03 Writing/blog/` 的文章發布並對齊到個人 blog repo (`youruser-blog/content/blog`)。流程：lint → quality check（通順度 + 技術正確性，websearch/context7）→ image 規範化（無意義檔名請使用者重命名，含 vision 建議）→ frontmatter 統一 → wikilink/callout 轉成標準 markdown → 同步檔案 + 圖片（含 banner）→ 清孤兒 → repo 端 conventional commit。**Vault 是 source of truth**。**強制流程：每階段先給預覽 → 等使用者明確同意 → 才寫入**。觸發：「發布文章」、「publish blog」、「對齊 blog」、「sync blog」、`/cook-blog-publish`。
argument-hint: "[<slug>] | --all | --dry-run  # 不給就問哪一篇"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
model: sonnet
---

# cook-blog-publish

**這是一個任務指令，不是參考文件。讀完後立即從 Step 1 開始執行。**

把使用者在 vault 寫的文章發布到個人 blog repo，同時保證兩端 markdown renderer 都能正確渲染、frontmatter 通過 Nuxt Content zod schema、技術內容經過品質檢查。

> **強制流程**：每階段（Lint / Quality / Image / Sync）都要先給預覽，等使用者明確同意才往下走或寫檔。不可一次跑完全部後才回報。

## 路徑常數

```
VAULT_ROOT = {base_url}
VAULT_BLOG = $VAULT_ROOT/03 Writing/blog
VAULT_ASSETS = $VAULT_ROOT/_assets
REPO_ROOT  = {home}/code/personal/youruser-blog
REPO_BLOG  = $REPO_ROOT/content/blog
REPO_IMG   = $REPO_ROOT/public/images/blog
STATE_FILE = $VAULT_ROOT/.claude/skills/cook-blog-publish/state/state.json
```

## 觸發

- `/cook-blog-publish <slug>` — 發布單篇
- `/cook-blog-publish --all` — 對齊所有 vault blog 文章
- `/cook-blog-publish --dry-run` — 跑 lint + quality + 預覽，但不寫任何檔
- 自然語言：「發布文章」、「publish blog」、「對齊 blog」、「sync blog」、「把 X 推到 blog」

無 slug 時：列 vault blog 下所有 md，用 `AskUserQuestion` 讓使用者選（或 `--all`）。

## Frontmatter Schema（兩端統一，符合 Nuxt zod）

```yaml
---
title: '<繁中標題>'
description: '<一句話描述，showcard 用>'
date: 'YYYY-MM-DD'                              # 字串，不是 date object
tags: ['Tag1', 'Tag2']
category: '技術' | '職涯' | '生活' | '工具'      # 自由文字但限定常用
author: 'Your Name'
image: '/images/blog/<slug>/banner.<ext>' | ''  # banner，repo 路徑
draft: false
---
```

**規則**：

- vault 與 repo md 用**完全相同**的 frontmatter。`image` 在 vault 也存 repo 路徑（Obsidian 不會 inline render，但不會壞）
- Body 各用 native：vault `![[<slug>-<name>]]`、repo `![alt](/images/blog/<slug>/<name>)`
- vault 額外想記的 metadata（如 `status`/`created`）**不寫進 frontmatter**，避免污染兩端

## 品質快取（避免重複 quality check）

`STATE_FILE` 結構：

```json
{
  "<slug>": {
    "content_hash": "<sha256 of normalized body, hex>",
    "quality_checked_at": "YYYY-MM-DDTHH:MM:SS+08:00",
    "quality_status": "pass" | "pass_with_warnings",
    "warnings": ["..."],
    "last_published_at": "..."
  }
}
```

**Content hash 計算**：取 vault md 的 body（去 frontmatter），strip trailing whitespace，sha256 hex digest。Frontmatter 變動不觸發 re-check（不影響內容正確性）。

**何時 skip quality check**：state 內 `content_hash` 與當前計算結果一致 → skip 階段 2，告訴 user「已通過品質檢查（YYYY-MM-DD），跳過」。使用者可加 `--force-quality` 強制重跑。

---

## 流程

### Step 0 — 解析參數、決定 target slugs

1. 從 `$ARGUMENTS` 取 slug / `--all` / `--dry-run` / `--force-quality`
2. 沒指定 slug 且非 `--all` → `AskUserQuestion` 列 vault blog md 讓使用者選
3. 對每個目標 slug 做 Step 1–7

### Step 1 — Lint（每個 slug 都跑）

讀 `$VAULT_BLOG/<slug>.md`，檢查：

1. **Frontmatter 完整性**
   - 8 必要欄位都在（`title/description/date/tags/category/author/image/draft`）
   - `date` 格式 `YYYY-MM-DD`、`tags` 是陣列、`draft` 是 boolean
   - 缺欄位/格式錯 → 列出問題，**問使用者要不要補**（用 `AskUserQuestion`）
2. **Image 命名檢查**
   - 掃描 body 所有 `![[...]]` embed + `frontmatter.image`
   - 無意義名 pattern（regex）：
     - `^Pasted image \d+\.\w+$`
     - `^Screenshot.*`
     - `^Untitled.*`
     - `^IMG_\d+`
     - `^image\d*\.\w+$` 純編號
   - 命中 → 列「需重命名清單」，丟到 Step 3 處理
3. **Wikilink 非圖片**
   - 列出所有 `[[Note Title]]` / `[[Note|Alias]]`（非圖片副檔名）
   - 標明 Step 4 會被轉成純文字（alias 優先，沒 alias 用 title 去 emoji 前綴）
4. **Callout**
   - 列出所有 `> [!type]` 區塊
   - Step 4 會轉成 `> **Type**\n> ...`
5. **Embed 其他筆記**
   - `![[note.md]]` / `![[some note]]`（非圖片）→ 拒絕發布，要求使用者展開內容
6. **產 lint report**，等使用者同意才繼續

**Lint report 範例**：

```
[Lint] concurrency.md
  Frontmatter: ✅ 全部欄位齊全
  Images (3):
    ⚠️ Pasted image 20260510084316.png — 無意義名，需重命名
    ✅ concurrency-gil-diagram.png
    ✅ concurrency-asyncio-flow.png
  Wikilinks (2): [[Python GIL]] → "Python GIL", [[asyncio|asyncio]] → "asyncio"
  Callouts (1): > [!warning] → > **Warning**
  Embeds: none

繼續到 Step 2 Quality Check? (y/n)
```

### Step 2 — Quality Check（所有文章都跑，除非 hash 命中快取）

1. **計算 content hash**，比對 `STATE_FILE`
   - 命中 → skip，告知使用者
   - 未命中 → 進品質檢查
2. **通順度檢查**
   - 自己讀全文，標出：錯字、語句不通順、邏輯跳躍、段落結構問題
   - 給 inline 建議：`段落 X (line Y-Z): 建議改成 ...`
3. **技術正確性檢查**（針對 `category: 技術` 或文章含 code block / API 名）
   - 抽取「需驗證的技術主張」：library API、版本特性、效能數字、CLI flag、配置選項
   - 用 **`context7` MCP**（透過 documentation-lookup skill 或 mcp__context7__resolve-library-id + query-docs）查 library docs
   - 用 **WebSearch** 驗證一般技術事實 / 新版本資訊
   - 列出可疑/錯誤主張 + 建議修正 + 引用來源
4. **產 quality report**，等使用者裁決：
   - `pass` → 寫 hash + status 到 STATE_FILE，繼續
   - `pass_with_warnings` → 列出 warnings 進 STATE_FILE，繼續
   - `fail` → 停止，請使用者修正後重跑

**Quality report 範例**：

```
[Quality] concurrency.md
  通順度:
    ⚠️ line 45-47: "GIL 並不會 ..." 語句不通，建議改成 "GIL 讓 ..."
    ✅ 其餘段落通順
  技術正確性（用 context7 查 Python docs + WebSearch）:
    ❌ line 89: "asyncio.create_task() 在 Python 3.7 引入" — 實際是 3.7 加入，正確
    ⚠️ line 102: "ThreadPoolExecutor 預設 workers = CPU 核心數 * 5" — Python 3.8 後改為 min(32, os.cpu_count() + 4)，請更新
    ✅ 其他主張驗證通過

修正後繼續？(y / 忽略 warning 繼續 / abort)
```

### Step 3 — Image Normalize

對每張需重命名的圖片：

1. **Claude 用 vision 看圖** + 文章上下文 → 生成有意義名建議
   - 格式：`<slug>-<kebab-desc>.<ext>`，例：`concurrency-gil-diagram.png`
   - 不確定 → 標 `[需手動]`，請使用者填名
   - confidence 高（圖明確）→ 直接給建議
2. **Banner 特殊處理**
   - frontmatter.image 若為 vault embed 形式 `[[Pasted image ...]]` 或空 → 處理
   - 若 vault `_assets/` 有對應原圖 → 重命名為 `<slug>-banner.<ext>`，frontmatter.image 改成 `/images/blog/<slug>/banner.<ext>`
   - banner 沒設且沒原圖 → 詢問是否要設定 banner（可選）
3. **列出重命名 plan**：

```
[Image Rename]
  Body images:
    Pasted image 20260510084316.png → concurrency-gil-diagram.png
      (vision: 顯示 Python 多執行緒受 GIL 限制示意圖)
    Pasted image 20260510084336.png → concurrency-asyncio-event-loop.png
      (vision: asyncio event loop 結構圖)
    Pasted image 20260510084349.png → [需手動] (vision: 圖片內容不明確)
  Banner:
    (none) → 略過

確認重命名？(y/n/edit)
```

4. **同意後執行**（這是 Step 6 才真寫；Step 3 只決定 plan）

### Step 4 — Content Transform（產 repo 版 markdown，記憶體中）

從 vault md 產出 repo md：

1. **Frontmatter**：保留 8 欄位原樣
2. **Callout** `> [!type]\n> content` → `> **Type**\n> content`
   - Type 首字大寫，例：`note` → `Note`, `warning` → `Warning`
3. **Wikilink 非圖片** `[[X|Y]]` → `Y`；`[[X]]` → `X`（vault 檔名已禁止 emoji 前綴；若遇到 legacy 檔名殘留前綴，仍防禦性去除：例 `GIL` → `GIL`）
4. **Image embed** `![[<slug>-<name>]]` → `![](/images/blog/<slug>/<name>)`
   - 含寬度 `![[<slug>-<name>|600]]` → `<img src="/images/blog/<slug>/<name>" width="600" />`
   - alt 文字：用檔名去 slug 前綴去副檔名變 kebab-readable，例 `concurrency-gil-diagram.png` → `alt="gil-diagram"`；想要更好的 alt 可在 vault 用 `![[xxx|alt text]]` 但要區分 alt 與寬度（純數字是寬度，其他是 alt）
5. **產 unified diff**（vault md → repo md），列給使用者看

### Step 5 — Sync 預覽

對單一 slug 列出總結：

```
[Sync Plan] concurrency.md
  Direction: VAULT → REPO (Vault is SoT)
  Frontmatter changes: 補 description="..."（vault 缺）
  Body changes:
    - 3 callouts 轉換
    - 2 wikilinks 剝除
    - 3 image embeds 改寫
  Image files:
    + copy _assets/concurrency-gil-diagram.png → public/images/blog/concurrency/gil-diagram.png
    + copy _assets/concurrency-asyncio-event-loop.png → public/images/blog/concurrency/asyncio-event-loop.png
    + copy _assets/concurrency-banner.png → public/images/blog/concurrency/banner.png
    - delete public/images/blog/concurrency/old-orphan.png（vault 不再引用）
  Vault md updates:
    - rename 3 _assets 圖片
    - update 3 ![[...]] embed 引用新檔名

確認執行？(y/n/edit)
```

**反向同步偵測**：若 repo md 的 mtime 較新且內容與 vault 差異不只 transform 結果 → 提示「repo 有手動修改」，列差異讓使用者裁決（vault 永遠贏，但要告知）。

### Step 6 — Apply（使用者 y 後執行）

**順序很重要**，先 vault 後 repo：

1. **Vault 圖片重命名**
   - `mv _assets/<old> _assets/<new>`（用 git mv 若 vault 在 git）
2. **Vault md 更新**
   - 改寫 body 內 `![[<old>]]` → `![[<new>]]`
   - 補/修 frontmatter（若 Step 1 有差異）
3. **Repo 圖片複製**
   - `mkdir -p $REPO_IMG/<slug>`
   - `cp $VAULT_ASSETS/<slug>-<name>.<ext> $REPO_IMG/<slug>/<name>.<ext>`（去 slug 前綴，因為 repo 路徑已有 slug 資料夾）
4. **Repo md 寫入**
   - Write transformed content 到 `$REPO_BLOG/<slug>.md`
5. **清孤兒圖片**
   - 比對 `$REPO_IMG/<slug>/` 內檔案 vs repo md 引用的圖片
   - 沒被引用的 → `rm`
6. **更新 STATE_FILE**
   - `content_hash`、`quality_checked_at`、`quality_status`、`last_published_at`（用 `date -Iseconds`）

### Step 7 — Git Commit（repo 端）

1. `cd $REPO_ROOT && git status` 看異動
2. 草擬 conventional commit：
   - 新文章（vault-only → 推到 repo）：`feat(blog): publish <slug>`
   - 內容更新：`docs(blog): update <slug>`
   - 只動圖片：`chore(blog): refresh images for <slug>`
   - 多篇：`docs(blog): sync N articles`
3. **問使用者**是否要 commit + message（用 vault root CLAUDE.md 的 commit 流程）
4. 同意 → `git add` 指定檔案（不要 `-A`）+ `git commit`
5. 問是否要 `git push`

### Step 8 — Report

最後給使用者：

```
✅ Published <slug>
  Vault: 03 Writing/blog/<slug>.md (updated)
  Repo:  content/blog/<slug>.md (created/updated)
  Images: N copied, M renamed in vault, K orphans deleted
  Quality: pass (cached) | pass (re-checked, N warnings)
  Commit: <hash> "<message>" — not pushed yet
```

---

## 邊界與規則

### 圖片重命名規則

- 一律 `<slug>-<kebab-desc>.<ext>`，全小寫
- Banner 一律 `<slug>-banner.<ext>`
- 同名衝突 → 加序號 `-2`, `-3`...
- 副檔名小寫化（`.JPEG` → `.jpeg`）

### Wikilink 剝除規則

- `[[A|B]]` → `B`
- `[[A]]` → `A`（vault 檔名已無 emoji 前綴；legacy 殘留前綴仍防禦性去除 + 去前置空白）
- `[[A]]` → `A`
- Skill 不嘗試把 wikilink 轉成 repo 內部超連結（除非該筆記也是已發布的 blog 文章，未來可延伸）

### Callout 對應

| Obsidian         | Repo              |
| ---------------- | ----------------- |
| `> [!note]`      | `> **Note**`      |
| `> [!tip]`       | `> **Tip**`       |
| `> [!warning]`   | `> **Warning**`   |
| `> [!important]` | `> **Important**` |
| `> [!example]`   | `> **Example**`   |
| `> [!bug]`       | `> **Bug**`       |
| `> [!question]`  | `> **Question**`  |
| `> [!todo]`      | `> **Todo**`      |

### Math / Code block

- 保留原樣（KaTeX / fenced code 兩端 renderer 都支援）

### 拒絕場景

- `![[note.md]]` 嵌入其他筆記 → 拒絕，要求展開
- `draft: true` 但跑 `--all` → 跳過該篇 + 提示
- vault md 不存在 frontmatter → 拒絕，請使用者先補

### Dry run

- `--dry-run` 跑到 Step 5 結束（含 quality check），印完 Sync Plan 就停，不寫任何檔，不更新 STATE_FILE

---

## Helper scripts

- `scripts/content_hash.py` — 算 body sha256

**呼叫方式**：`uv run scripts/<name>.py <args>`

（列 `![[...]]`/`frontmatter.image` 引用、讀寫 STATE_FILE 由 Claude 在流程中直接處理，不另外用 script。）

---

## 第一次跑（init mode）

若 STATE_FILE 不存在或為空：

1. 建立空 state
2. 跑時提示「首次發布，將對所有目標跑完整 quality check」
3. 完成後填入快取
