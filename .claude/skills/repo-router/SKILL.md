---
name: repo-router
description: 把 vault 筆記提到的專案/repo 解析成「這台機器上」的真實本機路徑,讓 Claude Code 能直接 Read/Grep/Glob 真實 repo 內容,而不是只靠筆記描述。也能定位該 repo 對應的 ~/.claude/projects 對話紀錄目錄。觸發:筆記提到某專案而你需要看真實程式碼、「去看 repo」、「這個專案的實作」、`/repo-router`。
allowed-tools: Read, Grep, Glob, Bash(uv *), Bash(ls *), Bash(test *), Bash(sed *)
model: inherit
---

# repo-router

**這是一個任務指令,不是參考文件。** 需要看某個 repo 的真實內容時,依下列流程解析路徑再讀取。

## 為什麼需要它

Vault 存在 iCloud,會在多台 Mac 間同步。三層資訊的絕對路徑都內嵌 `/Users/<username>/`,換機器就失效:

| 層              | 這台機器範例                                                          | 換機器會變的部分           |
| --------------- | --------------------------------------------------------------------- | -------------------------- |
| repo 本體       | `~/code/work/Project-ExampleProject`                              | `$HOME` 前綴(username)     |
| Claude 對話紀錄 | `~/.claude/projects/-Users-you-Documents-coding-gc-Project-ExampleProject` | slug 內的 `-Users-<user>-` |
| vault 筆記      | `01 Work/projects/ExampleProject/`                                          | 無(本來就相對)             |

**關鍵設計**:所有 repo 保證在 `~/code/` 底下(分 `gc/`、`personal/`、`side/`、`others/`),所以 `repos.yaml` 只存 **`$HOME` 相對路徑**(`code/...`),執行時再用當前機器的 `$HOME` 還原絕對路徑。零每機設定。

## 解析流程

1. **讀對照表** `repos.yaml`(此 skill 目錄下)。每筆:
   - `name` — repo 目錄名(模糊比對用)
   - `path` — `$HOME` 相對路徑(唯一鍵)
   - `remote` / `host` — git 來源
   - `vault_project`(選填)— 對應 `01 Work/projects/<X>/` 的資料夾名
   - `description`(選填)— 一句話說明這個 repo 做什麼

2. **比對查詢**。使用者/筆記給的線索依序比對:`vault_project` → `name` → `path` 片段 → `remote`。命中一筆就往下;命中多筆先列出讓使用者選。

3. **還原絕對路徑並驗證存在**:

   ```bash
   ABS="$HOME/<path>"          # 例:$HOME/code/work/Project-ExampleProject
   test -d "$ABS" && echo "OK $ABS" || echo "MISSING $ABS"
   ```
   - 存在 → 用 `Read` / `Grep` / `Glob` 直接讀 `$ABS` 底下的真實檔案。
   - `MISSING` → 這台機器沒 clone。回報 `remote`,問使用者是否要 clone,不要臆測內容。

4. **(選填)定位對話紀錄**。Claude log 目錄由絕對路徑決定性推導:把絕對路徑的 `/` 與 `.` 都換成 `-`。
   ```bash
   SLUG=$(echo "$ABS" | sed 's/[/.]/-/g')   # /Users/you/... -> -Users-you-...
   ls "$HOME/.claude/projects/$SLUG" 2>/dev/null
   ```

## 維護對照表

repo 有增刪、換位置、或新 clone 時,重掃即可:

```bash
uv run scripts/scan.py          # 1. 重掃磁碟,重建 repos.yaml
uv run scripts/gen_registry.py  # 2. 用 repos.yaml 刷新人類可讀的 [[Repo Registry]]
```

- `scan.py` 掃 `~/code`(`gc`/`personal`/`side`/`others`)找所有 git repo,重建 `repos.yaml`。
- **`vault_project` 與 `description` 會被保留**(以 `remote` 為鍵回填,所以 repo 換位置/改名仍留住 curation;無 remote 時才 fallback 到 `path`),其餘欄位由磁碟覆寫。
- 新增 vault 筆記專案 ↔ repo 的對應:掃完後手動在該 repo 條目補一行 `vault_project: <資料夾名>`,再跑 `gen_registry.py`。

## 不要做

- 不要在 `repos.yaml` 寫絕對路徑或 `/Users/you`——只存 `$HOME` 相對路徑(`code/...`),才跨機器可攜。
- repo 不存在時不要用筆記內容腦補程式碼,先回報 `MISSING` 與 `remote`。
- 不要手動維護 `repos:` 那份清單(用 scan.py);只手動維護 `vault_project` 覆寫。
