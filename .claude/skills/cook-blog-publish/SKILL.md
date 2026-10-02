---
name: cook-blog-publish
description: 全量同步 Obsidian blog 到個人網站，保留子目錄、更新圖片並下架移回 drafts 的文章；區分同步、部署與正式上線。無校稿或品質關卡。
---

# cook-blog-publish

## 唯一來源

- Vault：`{base_url}`；網站 repo：`{home}/code/personal/youruser-blog`。
  先展開機器路徑；其他機器用 repo-router 定位，不猜路徑。
- `03 Writing/blog/**/*.md` 是完整公開集合，`drafts/**` 是撰寫中。
  不使用 frontmatter draft。不以單篇同步漏掉其他文章的更新／下架。
- 文章與圖片的文字編輯只在 Vault；repo 的 `content/blog/**` 是產物。
- Skill 與 agent 設定原稿也只在 Vault；修改後從 Vault 跑 `DRY_RUN=1 ./install.sh`，
  檢查預覽，再跑 `DRY_RUN=0 ./install.sh`，驗證 Claude／Codex 入口指向同一份原稿。

## 操作

在網站 repo 執行（`--vault` 後面傳已展開的 Vault 絕對路徑）：

```sh
npm run blog:plan -- --vault "$VAULT_ROOT"
npm run blog:sync -- --vault "$VAULT_ROOT"
npm run blog:status -- --vault "$VAULT_ROOT" --verify
```

- 盤點／`status`：跑 status，回報全量差異與 Production 狀態。
- 預覽／`--dry-run`：只跑 plan，包含格式驗證，不寫檔、不 commit、不部署。
- 同步：先跑 plan，展示新增／更新／下架、圖片變化，再跑 sync。
  使用者已授權同步時不重複逐階段確認。
- 「發布」、「同步部落格」、「同步並上線」：執行到部署驗證；明說只同步本機則停在 sync。

同步程式負責 Markdown 轉換、資產解析、hash 比對、衝突偵測與完整集合移除。
不要用臨時腳本繞過驗證。無變更時不建立空 commit。

## 部署

1. 保留既有工作，確認分支與 repo 的 Git 規範；只 stage 本次管理的檔案。
2. 執行 `npm test`、`npm run typecheck`、`npm run generate`、`npm run test:seo-build`；
   路由／renderer 有修改時補關鍵 E2E。失敗先診斷，不跳過檢查。
3. Conventional commit，push，依 repo 分支流程推進 Production。
   若建立 PR，只在目前授權包含合併時合併；否則回報 Preview／PR，不能稱為正式上線。
4. 查詢對應 Production 部署，成功後執行 status --verify。
   不把 Preview、commit、push 或本機 sync 成功當成上線。
5. 若部署仍進行中，用有界等待；失敗回報原因、舊版是否仍在線上。
   下次從同一 commit 繼續，不重做內容修改。

## 格式與邊界

- 保留文章相對路徑；網址由 Content 路徑規則產生，檔案改名會改網址。
- 僅驗證 metadata、圖片存在、路徑／網址衝突、可轉換語法與建置。
  不做通順度檢查、技術主張評分、品質快取或強制圖片重命名。
- 缺 metadata 請在 Vault 修正；不知道的日期或內容不能自行捏造。
- repo 手動修改衝突：展示差異，將要保留的修改先裁決並回填 Vault。
  不改 manifest hash 來繞過衝突。
- `![[note]]` 的全文嵌入不支援，需在原稿展開；圖片、wikilink、callout 由程式轉換。
- 無法讀取 Vault 必須停止，不能解讀成全部下架。只有使用者明確要求清空公開集合，
  才傳 `--allow-empty`。
- 同步 manifest 是機械紀錄，不是另一份文章 source of truth。

## 回報

列出新增／更新／下架篇數、commit、部署狀態與正式網址。
status --verify 同時要求部署內容 manifest 對齊、公開網址 200、下架網址 404。
不確定部署狀態時寫「未知」，不要推測成功。
