---
name: cook-progress
description: 根據使用者的口語進度回報，更新某專案的「Action Items - WIP.md」與「Action Items - Done.md」，並建議連動更新的 plan / keypoint 檔案。處理：勾選完成、append 新項、新增 follow-up、調整描述、移動 WIP→Done。**強制流程：先給變更預覽 → 等使用者明確同意 → 才寫入**。觸發詞：「我完成了 ...」、「update action items」、「整理進度」、「WIP 更新」、「把 X 移到 done」、「cook progress」、`/cook-progress`。**只記錄 Your Name 個人工項**（per `01 Work/CLAUDE.md`），拒絕 PM 主導事項、團隊待辦、ExampleClient 窗口工項。
argument-hint: "[<project>] [--sweep]  # 預設口語回報模式；--sweep 為自動掃勾模式（供 cook-loop）"
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
model: sonnet
---

# cook-progress

**這是一個任務指令，不是參考文件。讀完後立即從 Step 1 開始執行。**

把使用者的口語進度回報（"我做完了 X、Y 還在卡 Z、新增 follow-up 追 @Steven"）煮成對 `Action Items - WIP.md` 與 `Action Items - Done.md` 的結構化更新，並列出可能需要連動更新的 plan / keypoint 檔（**不自動改**）。

> **強制流程**：Step 1–3 在記憶體裡完成，**Step 4 必須先給使用者預覽 + 等待明確同意**，之後 Step 5 才寫入磁碟。任何情況下不可跳過 Step 4 直接寫檔。

## 觸發

- `/cook-progress <project>` — 明確指定專案
- `/cook-progress`（無參數）— 從對話 / cwd / 最近開啟檔案推斷
- 自然語言：「我完成了 ...」、「update action items」、「整理進度」、「WIP 更新」、「把 X 移到 done」
- `/cook-progress <project> --sweep` — **自動掃勾模式**（見下方專節，供 cook-loop 無人值守呼叫）

## 自動掃勾模式（`--sweep`）

> **只有這個模式跳過 Step 4 預覽 gate**，因為輸入不是口語回報、而是 user **已經在 WIP 手動打勾**的 `- [x]` 條目——勾選本身就是明確的「完成」授權。此模式供 `cook-loop` tick 全自動直寫；人手用一律走口語模式。

觸發此模式時**不跑** Step 1–5 的口語流程，改跑以下 4 步：

1. **讀 WIP**：`01 Work/projects/<PROJECT>/Action Items - WIP.md`。用 `- [x]`（含縮排 sub-bullet、大小寫不拘）找出所有打勾的 top-level 條目群。沒有任何打勾項 → 直接結束（no-op，不寫檔）。
2. **搬到 Done（changelog）**：把這批打勾條目當一次 release，完全依 `references/changelog-format.md` 決定版號 bump、分類六 section（把每個 top-level 條目按語意判 `change_type`，sub-bullet 併入該條描述）、產 release 標題，prepend 到 Done.md。
3. **從 WIP 移除**：刪掉那些打勾的 top-level 條目群（含其 sub-bullet），保留未勾的 `- [ ]` 條目與所有區段標題 / frontmatter / TOC。兩檔的 `last_updated` 都更新為 today。
4. **不預覽、不詢問、不 commit**：直接 Write/Edit 兩檔。commit 由呼叫端（cook-loop Step 4）負責——回報實際寫入的兩個檔路徑即可。

強制規則仍適用：只搬 `- [x]` 條目，**絕不**動未勾項、絕不重排、絕不 `git add`。歸類不確定的條目預設 `Changed`。

## 前提

操作對象限定：

```
<VAULT_ROOT>/01 Work/projects/<PROJECT>/Action Items - WIP.md
<VAULT_ROOT>/01 Work/projects/<PROJECT>/Action Items - Done.md
```

如果 `<PROJECT>` 推不出來，**用 AskUserQuestion 列出候選讓 user 選**，不要瞎猜。

---

## 流程

設 `VAULT_ROOT = {base_url}`，路徑交給工具之前先依 `rules/00-machine-paths.md` 解析 `{base_url}`。

### Step 1 — 解析口語回報與 target project

1. 從 `$ARGUMENTS` / 對話 / IDE 開啟檔案 / cwd 推斷 `PROJECT`
2. 列出 `01 Work/projects/` 下所有子目錄當候選
3. 若不確定 → `AskUserQuestion` 列候選讓 user 選
4. 把 user 的口語回報解析成結構：

```python
{
  "completed": [           # 明確說「做完了」的項目
    {"text": "原文 / 我描述的事", "change_type": "added|changed|deprecated|removed|fixed|security", "notes_link": "<可選的會議連結>"}
  ],
  "in_progress_updates": [  # 推進但未完成（要改 WIP 描述或加 sub-bullet）
    {"match": "原 WIP 描述關鍵字", "update": "新狀況"}
  ],
  "new_items": [            # 新增的 task
    {"text": "...", "source": "<可選的會議/keypoint>"}
  ],
  "follow_ups": [           # 追蹤他人的事項
    {"text": "追蹤 @XXX 是否完成 YYY"}
  ],
  "blocked": [              # 卡住的事，改加 [!warning] callout 或 sub-bullet
    {"match": "...", "blocker": "..."}
  ],
  "remove": []              # user 明確說「這項取消 / 不做」的
}
```

**解析規則：**

- release 日期用 today（沒指定時）；不再逐項標日期
- user 講 "完成 X, Y" → 兩筆 completed，各自判 `change_type`（分類指引見 `references/changelog-format.md`）
- user 講 "X 卡住，因為 Y" → 進 blocked
- 含「追 / follow up / 跟進 @人名」→ 進 follow_ups
- user 含糊的（"進度推一下"）→ 在 Step 4 預覽中標 `（待釐清）` 並請 user 補

### Step 2 — 蒐集上下文（並行 Read）

並行讀：

1. `01 Work/projects/<PROJECT>/Action Items - WIP.md`
2. `01 Work/projects/<PROJECT>/Action Items - Done.md`
3. `01 Work/projects/<PROJECT>/`（用 Glob 列 `*.md`，找可能需連動的 plan / SA / keypoint 檔）

如果 WIP 不存在 → 用標準模板建立。
如果 Done 不存在 → 用標準模板建立。

### Step 3 — Cook（in-memory，**不寫檔**）

#### 3a. WIP.md 變更計畫

對每個 `completed` 項：

- 在 WIP 找最匹配的 `- [ ]` 條目（用語意比對，不是 exact match）
- 計畫：從 WIP **刪除**該行（或整個 sub-bullet 群）
- 計畫：納入本次 Done release（見 3b）

對每個 `in_progress_updates`：

- 找匹配條目 → 計畫：替換文字 / 加 sub-bullet

對每個 `new_items`：

- 計畫：append 到 WIP `## 進行中` 適當 subsection（用 source 推斷）
- 若無對應 subsection，列在「### 其他」或新建 subsection

對每個 `follow_ups`：

- 統一格式 `- [ ] 追蹤 @XXX 是否完成 YYY`
- 計畫：append 到 WIP「### Follow-ups」subsection（沒有就新建）

對每個 `blocked`：

- 計畫：在原條目下加 `> [!warning] Blocked: <原因>` 或 sub-bullet `  - blocker: <原因>`

對每個 `remove`：

- 計畫：從 WIP 刪除（在預覽中**明顯標示為刪除**，user 容易看漏）

更新 `last_updated: <today>` frontmatter。

#### 3b. Done.md 變更計畫（changelog 格式）

Done.md 是 Keep a Changelog + SemVer 格式，**每次 cook-progress = 一個版本 release**。
完整格式規範、版號判定表、範例、新建模板見 **`references/changelog-format.md`**（讀它，別憑記憶）。

步驟：

1. 讀 Done.md 最上方第一個 `## [X.Y.Z]` 當現行版；沒有 → 視為 `0.0.0`。
2. 依該批 `completed` 的性質決定 bump（major/minor/patch，取最高影響者；規則見 reference）。
3. 產生一句話 release 標題。
4. 把 `completed` 按 `change_type` 分到六類 section（**空類不列**），條目格式 `- **<重點>**: <描述>`（無 checkbox、無逐項日期，有 notes 用句尾 `[[...]]`）。
5. 新版本區塊 **prepend** 到 intro note 之後、所有既有版本之上（newest-first）。

更新 `last_updated: <today>` frontmatter。

#### 3c. 建議連動更新的檔案（**不自動改**）

掃 `01 Work/projects/<PROJECT>/` 下：

- `plan*.md`、`*Plan*.md`、`SA*.md`、`系統設計*.md`
- `keypoint/*.md`

若 completed / blocked / new_items 中有跟這些檔內容明顯相關的（例：完成「部署 service gateway」而 `plan-deployment.md` 還列為 TODO），列在「建議手動更新」清單。

**只列檔名 + 一句建議理由，不直接改。**

### Step 4 — 預覽 + 等待 user 確認（**強制 gate**）

依 **`references/preview-format.md`** 的模板對 user 輸出預覽（三區塊 + 回覆選項）。

**未獲明確同意前不可呼叫 Write / Edit。**（`[3] 建議手動更新` 永遠不寫。）

### Step 5 — 寫入（只執行 user 批准的部分）

用 **Edit**（針對單行修改）或 **Write**（整檔重寫）。

注意：

- 不破壞 user 手寫但無關的內容
- frontmatter `last_updated` 同步更新
- 保留 ` ```table-of-contents``` ` 區塊

### Step 6 — 提示 commit

按照 vault CLAUDE.md 的 commit 政策：

```
修改完成。是否要 commit？
建議的 message：`docs(<project-slug>): changelog <version> (<YYYY-MM-DD>)`
（若該次沒動到 Done 版本，用 `docs(<project-slug>): update action items (<YYYY-MM-DD>)`）
```

---

## 強制規則（per `01 Work/CLAUDE.md`）

**Action Items 範圍 — 只記錄 Your Name 個人工項：**

- ✅ Your Name 自己要執行的任務
- ✅ Your Name 需要主動追蹤他人是否完成的 follow-up
- ❌ PM 主導事項
- ❌ 整體團隊待辦
- ❌ ExampleClient 窗口的工項

若 user 回報的內容看起來像團隊待辦或 PM 事項，**在 Step 4 預覽中明確 flag**，問 user 是否真的要記。

**Follow-up 統一格式：**

```markdown
- [ ] 追蹤 @<人名> 是否完成 <事項>
```

**Done 格式：** Keep a Changelog + SemVer，每次一個版本 release（無 checkbox、無逐項日期）。
完整規範與範例見 `references/changelog-format.md`。

---

## 標準模板

WIP.md / Done.md 新建模板見 **`references/file-templates.md`**（Done.md 的 changelog 格式詳見 `references/changelog-format.md`）。

---

## Edge cases

| 情境                                               | 處理方式                                                                            |
| -------------------------------------------------- | ----------------------------------------------------------------------------------- |
| User 講「全部做完了」但 WIP 有 20 條               | Step 4 預覽列出**所有將被移到 Done 的條目**，請 user 逐條確認，不直接全 mark done   |
| User 報的事 WIP 找不到對應條目                     | 當作 completed 直接進 Done release（WIP 無對應行可刪），在預覽註明「原 WIP 未紀錄」 |
| 同一條 task 在 WIP 出現兩次                        | 在預覽 flag 並請 user 指明哪一條                                                    |
| User 說「把 X 改成 Y」但 X 是團隊待辦              | 提醒「這看起來是團隊待辦，per 01 Work/CLAUDE.md 不該在 Action Items」，問是否仍要寫 |
| Done.md 不存在                                     | 用 changelog 模板建立（見 reference），首版依 bump 規則                             |
| Done.md 為空 / 舊 checkbox 格式（無 `## [X.Y.Z]`） | 現行版視為 `0.0.0`，新版本區塊 prepend 到最上方；舊內容原地保留不動                 |
| completed 項無法歸類 change_type                   | 預設歸 `Changed`                                                                    |
| WIP 沒有 `## 進行中` 區段                          | 建立                                                                                |
| User 含糊（"進度推一下"）                          | 在預覽中標 `（待釐清）`，列具體問題請 user 補                                       |
| 多專案模糊（"那個 ExampleClient 的進度..."）                | 用 `AskUserQuestion` 在 API / 子專案B 中選                                         |
| Completed 項含敏感資訊（密碼 / token）             | Step 4 預覽 flag，建議遮蔽                                                          |

---

## 不做的事

- 不自動 commit（commit 是 user-driven，只能詢問）
- 不直接改 plan / SA 檔（只列建議）
- keypoint 檔：只列建議（3c），不自動寫
- 未經 Step 4 批准，任何模式都不寫 WIP / Done / keypoint
- 不處理 `01 Work/projects/*` 外的 Action Items（會報錯停止）
- 不擅自重排 WIP 順序（除非 user 明確要求）
- 不把 user 沒提到的條目 mark done
- 不靜默刪除 WIP 條目（刪除必須在 Step 4 預覽中明顯標出）

```

```
