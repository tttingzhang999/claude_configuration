# reference/meeting-note.md

## Contents

- Frontmatter 強制欄位
- Body 結構(順序固定)
- Cook 規則
- 標準模板(無同專案會議檔可參考時使用)

Step 3a 產出的「正式會議紀錄」內容規格：frontmatter、body 結構、cook 規則，以及無同專案會議檔可參考時的標準模板。

## Frontmatter 強制欄位

```yaml
---
date: <YYYY-MM-DD>
project: <PROJECT>
type: meeting
title: <從檔名或 raw 第一行推斷>
participants:
  - <參與方，從 raw 推斷；推不出來就列 "TBD">
cooked: true
keypoints_synced: true
action_items_synced: true
tags: [meeting, <project-slug>, <topic-tags>]
---
```

## Body 結構（順序固定）

````markdown
```table-of-contents

```

## 討論內容

### <主題 1>

...

### <主題 2>

...

## 結論 / 決議

1. ...
2. ...

## Action Items

- [ ] <具體任務>
- [ ] ...

---

## 延伸閱讀

- [[index]]
- [[<相關會議或筆記，如有>]]
````

## Cook 規則

1. **逐字保留事實**，不編造、不省略具體數字 / 名字 / 系統名
2. **重要限制 / 警告**用 `> [!warning]`；**待辦** `> [!todo]`；**補充** `> [!note]`；**Q&A** 用表格
3. **bullet 過深（> 3 層）** → 改成子標題或表格
4. **行內 inline `- 對` / `- OK` 這種回覆** → 整併到上方 bullet 的同一條，或用 callout
5. 不要把整篇用 `>` blockquote 包起來
6. 同義 / 重複的 bullet 合併

## 標準模板（無同專案會議檔可參考時使用）

````markdown
---
date: YYYY-MM-DD
project: <PROJECT>
type: meeting
title: <Meeting Title>
participants:
  - <Party 1>
  - <Party 2>
cooked: true
keypoints_synced: true
action_items_synced: true
tags: [meeting, <project-slug>]
---

```table-of-contents

```

## 討論內容

### <Topic 1>

<content>

### <Topic 2>

<content>

## 結論 / 決議

1. ...

## Action Items

- [ ] ...

---

## 延伸閱讀

- [[index]]
````
