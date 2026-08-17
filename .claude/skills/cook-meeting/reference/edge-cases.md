# reference/edge-cases.md

cook-meeting 的邊界情境處理與禁止事項。

## Edge cases

| 情境                                     | 處理方式                                                                                  |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| Raw 檔已經有 frontmatter                 | 合併欄位（保留 user 既有的、補上缺的），不覆蓋                                            |
| Raw 完全是空 bullet / 半句話             | 告知 user「內容太少，無法 cook」並列出實際讀到的內容，停止                                |
| Raw 含敏感資訊（密碼 / token / API key） | 在 Step 6 回報中**明確 flag**，建議移除或遮蔽；`--auto` 模式直接跳過該檔不產出 staging    |
| Raw 提到的 action 沒有具體動作           | 列在 Action Items 但加 `（待釐清）` 標記                                                  |
| WIP 不存在                               | staging 檔 2 的 `target_path` 仍指向該路徑；由 `cook-staging` 在 promote 時視情況建立新檔 |
| 沒有 `## 進行中` 區段                    | `append_anchor` 仍寫 `## 進行中`；由 `cook-staging` 視情況建立該區段                      |
| Raw 跟現有 cook 過的會議檔同名           | staging 檔 1 的 `overwrite_existing: true` 已表明覆寫既有，review 時請自行核對差異        |
| 推不出 participants                      | 列 `- TBD` 並在 Step 6 回報中提醒 user 補                                                 |
| 兩份 staging 之一已存在（尚未 review）   | 跳過該份，不覆寫使用者正在 review 的內容，在回報中標註「已存在，跳過」                    |

## 不做的事

- **不直接寫入** `01 Work/projects/*/meetings/**` 或 `Action Items - WIP.md`——一律先寫 `_staging/`，等 user 把 `reviewed` 改成 `true` 後由 `cook-staging` / `cook-loop` promote
- 不 append `_log.md`（那是 `cook-staging` promote 時的職責）
- 不寫入 `keypoint/` 目錄（只建議）
- 不處理 `01 Work/projects/*/meetings/` 路徑外的檔（會報錯停止）
- 不做 `_raw/` 的 ingest workflow（那是另一個流程）
- 不刪掉 raw 內 user 手寫的事實內容（只重組 / 補格式）
