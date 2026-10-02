---
name: write-article
description: 協助 Your Name 在 Obsidian 撰寫、續寫、修改或校稿文章；依現有原稿直接進入需要的步驟，要求發布時交接 cook-blog-publish。
---

# write-article

文章與圖片的 source of truth 是 Obsidian vault。展開機器路徑 `{base_url}`；
`03 Writing/drafts/**` 是撰寫中，`03 Writing/blog/**` 是已發布原稿。保留子目錄。
不在 website repo 寫原稿，不從 repo 取樣文章，不使用 frontmatter `draft`。

## 依意圖進入流程

- 新文章：整理主題、TA、主旨、大綱、素材與圖／程式碼需求成一份提案。
  等使用者確認方向後寫入 `drafts/<relative-path>.md`。若已有核准大綱，直接續寫。
- 續寫／局部修改：讀現有 Vault 原稿，直接處理指定範圍，不重走提案。
- 校稿：讀全文，找錯字、語意、邏輯、技術事實與不自然語氣。
  使用者要求修改時直接修稿並回報主要改動；只要求建議時不寫檔。
  有改變論點或缺少素材的問題才提出裁決，不自行補造內容。
- 已發布文章：原地修改 blog 原稿；除非使用者要求下架重寫，不自動移回 drafts。
- 完成草稿：仍留在 drafts。只有使用者表達發布意圖才移入 blog，保留相對路徑，
  隨後讀取並執行相鄰的 `../cook-blog-publish/SKILL.md`。目的地已有文章時先比較，
  不以同名草稿覆蓋不同版本。發布後不保留另一份可混淆的原稿副本。

## 文風與查證

- 生成時讀 `reference/style-guide-core.md`，必要時讀
  `reference/diataxis-article-framework.md` 協助定位；參考文章只從 Vault blog 取樣。
- 校稿時可參考 `reference/style-guide-verify.md`；需要去除套話時讀
  `reference/claude-cliches.md`，將它視為編輯參考，不使用配額、評分或強制循環作為交付門檻。
- 數字、版本、效能與技術主張必須有使用者素材或可查證來源。API／framework 文件用
  Context7；缺的素材明確標示待補，不虛構。保留 Your Name 的語氣與立場。
- 不強制 subagent、多輪 critique 或校稿通過紀錄。同步發布時不再校稿。
- 評語、提案與進度放在對話，不混入正式正文。校稿修改一律回 Vault。

## Metadata

發布原稿需 `title`、`description`、`date`（YYYY-MM-DD 字串）、`tags`（字串陣列）、
`category`。通常也保留 `author: Your Name`、`image: ''`。
可選 `language` 與 `updatedAt`；僅記錄真實已知日期，不用檔案 mtime 推測發布日期。
資料夾決定發布狀態，不增加 `status`／`published_at` 等重複狀態。
圖片可用 `![[filename.png]]` 或標準 Markdown；原圖留在 Vault，命名整理是寫作選項。
