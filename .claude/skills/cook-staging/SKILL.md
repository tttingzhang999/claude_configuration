---
name: cook-staging
description: 把 `_staging/` 裡 `reviewed: true` 的 cook 產出正式寫入 vault(write/overwrite/append 到各自的 target_path)、append `_log.md`、刪掉 staging 檔,最後只 commit 實際 promote 的檔。`reviewed: false` 的原地保留等你 review。觸發詞：`/cook-staging`、「flush staging」、「把 staging 寫進 vault」;也由 cook-loop tick 開頭自動呼叫。
argument-hint: "[--dry-run]"
allowed-tools: Bash(uv *), Bash(git add *), Bash(git commit *), Bash(git status *), Bash(git diff *), Read, Glob
model: haiku
---

# cook-staging

**這是任務指令,不是參考文件。讀完立即執行。**

把 `_staging/` 中已審核(`reviewed: true`)的產出 promote 進 vault。所有檔案操作由 `scripts/flush.py` 確定性完成(冪等),本 skill 只負責跑它 + commit。

## 流程

1. **執行 promote**:`uv run .claude/skills/cook-staging/scripts/flush.py`
   （帶 `--dry-run` 只列出會 promote 什麼、不寫檔,供預覽）
   - script 會:掃 `_staging/*.md` → 對「控制區塊有 `staging: true` 且 frontmatter `reviewed: true`」的檔剝除控制註解 + `reviewed` → 依 `op` write/overwrite/append 到 `target_path` → append `_log.md` → 刪該 staging 檔
   - stdout 回傳 JSON:`promoted`(檔名/target/op)、`pending`(待 review)、`errors`
2. **解析 JSON**。若 `errors` 非空,回報錯誤但不中斷已成功的部分。
3. **Commit**(僅當 `promoted` 非空):只 `git add` 每個 promoted 的 `target` + `_log.md`,**禁止 `git add -A`**(staging 已 gitignore,刪除無需入 git)。
   ```bash
   git add "<target1>" "<target2>" ... "_log.md"
   git commit -m "chore(cook): flush <N> staged item(s) into vault"
   ```
   本 repo 無 remote,不 push。
4. **回報**:`🍳 flushed <N> 項、pending <M> 項待 review`,列出 promoted 的 target 與仍 pending 的檔名(提醒去改 `reviewed`)。

## Staging 檔格式（重要）

機器控制欄位放在 body 開頭的 `<!--cook-staging ... -->` HTML 註解裡(內含 YAML),**不放 frontmatter** —— 這樣 Obsidian 前端的 Properties 面板只會顯示 `reviewed`(人工審核閘門)以及該筆記本身該有的 frontmatter(`date`/`project`/`type`…),不會被機器欄位灌爆。註解在 Live Preview / Reading 模式隱藏。

- **frontmatter**:只放 `reviewed: false/true` + 該筆記正式的 frontmatter(append 型無正式 frontmatter,故只有 `reviewed`)。
- **控制註解**(`<!--cook-staging ... -->`,promote 時整段剝除,不寫進筆記):`staging`、`source_skill`、`target_path`、`op`、`staged_at`、`overwrite_existing`、`append_anchor`。

## 約束

- 只 promote「控制註解 `staging: true` 且 frontmatter `reviewed: true`」;`reviewed: false` / 無控制註解的一律不動。
- promote 時 frontmatter 的 `reviewed` 也剝除,只留筆記正式 frontmatter。
- `op: write` 且 target 已存在但 `overwrite_existing` 非 true → script 報 error 跳過(保護既有檔),不強寫。
- commit 只含實際 promote 的檔;絕不 `git add -A`。
