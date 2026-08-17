# Step 4 預覽格式

Step 4 對 user 輸出的預覽模板與回覆選項。**未獲明確同意前不可呼叫 Write / Edit。**（`[3] 建議手動更新` 永遠不寫。）

```
🍳 cook-progress：<PROJECT>
日期：<YYYY-MM-DD>

預計變動：

[1] Action Items - WIP.md
    ✅ 完成（移除 N 條）：
      - <原 WIP 條目> → 移到 Done
      ...
    ✏️ 更新（M 條）：
      - <原條目> → <新文字 / +blocker>
      ...
    ➕ 新增（K 條）：
      - [ ] <新項目>（→ 落在 ### <subsection>）
      ...
    ❌ 刪除（user 取消，請仔細確認）：
      - <條目>
      ...

[2] Action Items - Done.md（changelog）
    🏷️ 新版本：<舊版> → <新版>（<major|minor|patch>）
    標題：<release title>
      ### Added
        - **<重點>**: <描述>
      ### Fixed
        - **<重點>**: <描述>
      （只列該次有的 section）

[3] 建議手動更新（不會自動寫）：
    - 📝 <檔名> — <一句理由>
    ...

請回覆：
- 「yes」/「全部寫入」  → 執行所有列出的寫入區塊（[1][2]）
- 「只寫 1」/「只寫 2」  → 部分執行（依區塊編號）
- 「展開」              → 貼出完整 WIP/Done 變動後內容
- 「改版號為 X」        → 覆寫建議版號
- 「改 X」              → 指定修改（含剔除某條）
- 「no」/「取消」       → 中止
```
