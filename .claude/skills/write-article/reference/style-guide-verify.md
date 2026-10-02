# Style Guide — Verify

> 用途：階段 4 批判迭代時，由 critique agent 載入執行。逐 Rule（A–K）檢查草稿，每個問題回報：原句 / 違反哪條Rule / 建議改寫方向。

## Contents

- Rule A 禁用詞／禁用片語 · B 動詞三層 · C 證據鏈 vs 情緒鏈 · D 技術名詞錯誤使用 · E 元件指代具體性
- Rule F Heading 設計 · G 過度口語 · H 輕重緩急 · I 推理跳步 · J `[待補]` 清點 · K 引用堆疊與內化
- Rule L Claude cliché scan（22 patterns，另檔）
- 輸出格式（嚴重度排序）

## Rule A：禁用詞 / 禁用片語

- AI 句式：這不是...，而是...
  - 判定含所有變體：「不是 A，是 B」「不是 A，而是 B」「不在 A，而在 B」「靠的不是 A，是 B」
  - 零容忍：不設保留名額，不因句子承載核心主張而豁免 — 一律改寫成直陳句

## Rule B：動詞三層

| 層級         | 用法         | 範例                                             |
| ------------ | ------------ | ------------------------------------------------ |
| 技術動詞     | 用英文       | invoke、deploy、consume、retry、resolve、recycle |
| 中性中文動詞 | 描述具體行為 | 檢查、設定、執行、印出、回傳、初始化             |
| 禁用三類     | 全部標記     | 見下                                             |

禁用三類：比喻動詞（往下挖、追下去、撞牆、繞遠路、踩雷 — 除非真的在講比喻情境）、擬人／戲劇化動詞（噴錯、爆掉、死掉、卡住、起不來 — 描述系統行為時）、疊字／口語動詞（跑跑、看看、試試、玩玩、聊聊）。

## Rule C：證據鏈 vs 情緒鏈

推理路徑必須是證據與驗證的鏈條：觀察到的事實 → 根據 X 證據懷疑 Y → 採取 Z 行動驗證 → 排除／確認。

標記情緒鏈：「直覺反應是…」「那時候以為…」「啊找到了」「才意識到方向錯了」、任何把作者寫成驚訝／恍然大悟的句子、用感受字眼（困惑、焦慮、鬆了一口氣）描述 debug 過程。

| ❌ 情緒鏈                                                           | ✅ 證據鏈                                                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 那時候直覺反應是「啊找到了」——一定是缺權限觸發 retry。              | Log 中的 `AccessDeniedException` 讓我先懷疑是 retry 行為打高 token request。               |
| 補完權限後等了一天再看，發現還是 1,600 筆——這時候才意識到方向錯了。 | 補上缺少的 IAM permission 重新 deploy 後，token_post 頻率沒有變化，可以排除 retry 是根因。 |
| 翻了很久才想通 X 跟 Y 沒關係。                                      | 對照 X 跟 Y 的時間序列，發現兩者沒有相關性，X 可以從候選原因中排除。                       |

Rule：拿掉作者的主觀感受，剩下的事實能不能獨立成立？

例外（保留，不標記）：「我後來才想通」「這點我一開始沒注意」「我不確定 X 在 Y 場景會不會壞」— 承認認知不足或表達不確定的第一人稱反思是真實、書面、可驗證的，不要跟戲劇化反應混淆。

## Rule D：技術名詞錯誤使用

逐一檢查全文的技術名詞是否用錯，三種常見錯誤型態：

**1. 名詞誤用**：把相近但不同的術語當同義詞。例：authentication vs authorization、latency vs throughput、concurrency vs parallelism、container vs image、Pod vs Node。檢查：這個詞的實際定義，跟句子描述的行為對得上嗎？

**2. 抽象層級混用**：工具／產品（Terraform、Kubernetes）、概念（IaC、CI/CD）、模式（Declarative、GitOps）、實例（某個 stack、某個 cluster）分屬不同層，不互當同義詞：

| ❌ 層級混用                | ✅ 正確                                     |
| -------------------------- | ------------------------------------------- |
| Terraform IaC 模式         | 用 Terraform 寫 IaC / IaC 走 Terraform 路線 |
| 走 Kubernetes 那條路       | 改用 Kubernetes orchestration               |
| 用 CI/CD 跑 GitHub Actions | 用 GitHub Actions 做 CI/CD                  |

**3. 自創組合**：主流技術文件、官方 docs、spec 裡不會出現的詞語組合或用法。

檢查方式：對每個技術名詞問 — 官方文件／主流技術文件是這樣用它的嗎？不確定的先用 context7 / WebSearch 查證再標記，不憑印象判。

## Rule E：元件指代具體性

不用代名詞「那層／那邊／整套／那塊」敘述具體服務 / 元件 / 實作：

| ❌ 代名詞指代            | ✅ 具體元件                                       |
| ------------------------ | ------------------------------------------------- |
| OTel 那層起不來          | OpenTelemetry SDK 在初始化階段失敗                |
| Cognito 那邊收到 1600 次 | Cognito User Pool 的 token endpoint 收到 1600 次  |
| 整套就掛了               | runtime 在 startup 階段 init 失敗，FastAPI 沒起來 |

## Rule F：Heading 設計

Rule：把全部 heading 抽出來單獨看，讀者能不能重建這篇文章的論證骨架？

層級規範：

- 不用 H1（標題由 frontmatter `title` 承擔）
- H2 是文章的主要分段：允許「前言」「總結」「背景」這類分類性用詞標示文章部位
- H3 是內容標題：一律適用下面三點檢查（分類性用詞的豁免只給 H2）

檢查三點：

1. **有具體對象**：heading 要點名這段的技術主體（元件、機制、設定、決策）。「問題」「原因」「解法」這種空泛名詞不能單獨成標，要帶上它的對象
2. **寫內容，不寫過程**：不用時間軸或心路歷程當標（「第一次嘗試」「真正的根因」「寫在最後」）— 這段的結論是什麼，標題就寫什麼
3. **同層級風格一致**：同一層的 heading 用同一種句式（都名詞短語、或都問句），不混用

| ❌ 劇情節點／空泛 | ✅ 內容主題                               |
| ----------------- | ----------------------------------------- |
| 真正的根因        | Root cause: 15 分鐘的 VM pre-warming 週期 |
| 第一個錯誤假設    | 排除 IAM retry：權限補齊後頻率不變        |
| 一些反思          | 這個方案的限制                            |

## Rule G：過度口語

口語碎片（啦、欸、嘛）、網路用語、顏文字、不專業措辭。
也需避免過於太乾淨變成教科書式的文章。
口語化但不失專業水準。

## Rule H：輕重緩急

拿階段 1 通過的大綱與「TL;DR」比對：

- 每個 section 是否服務「TL;DR」？不服務的標記
- 承載核心論證的 section 深度到位了嗎？（要有 trade-off 與邊界 case 的深度）
- 鋪陳與背景類 section 有沒有膨脹成長篇？
- 有沒有大綱外的離題段落？→ 標記砍掉

## Rule I：推理跳步 / 邏輯錯誤

逐段檢查：符合 TA 的讀者只靠文中已出現的資訊能不能跟上這段推理？
作者省略了自己已知、讀者不知的環節（背景假設、中間推導、術語）→ 標記補回。
這與「不解釋常識」不衝突：常識不用解釋，但推導不能跳。

## Rule J：`[待補]` 清點

- 草稿中所有 `[待補：___]` 佔位仍然存在、沒有被填成生成值
- 核對所有數字、版本號、定價的來源是否有相關素材或 reference？

## Rule K：引用堆疊與內化

- 正文中「某某說／某某認為／某某在某書給過建議」式句子超過 2 處 → 標記：觀點要內化成作者自己的論述，具名來源集中到文末「參考資料」
- 結尾出現「回到開頭／回顧本文」式字面回指 → 標記：首尾呼應靠主題與意象，不寫字面回指

## Rule L：Claude cliché scan

Run after Rule A–K, as a separate sweep. Load `reference/claude-cliches.md` and follow its detection protocol: 22 rhetorical patterns from the source catalog, each with English markers and its Chinese form, plus per-tier budgets.

- Tier 1 (CB, MCS, AE, AHM) has a budget of zero. Every instance is CRITICAL.
- CB is the wider form of Rule A. Report such a sentence once, under CB, and name Rule A.
- Read "What this pass must not destroy" before reporting. Substantive contrast teaching, real limitations, calibrated uncertainty, and honest parallel structure are not violations.
- Report only. The de-cliché rewrite runs as a separate step, driven by the rewrite prompt at the end of `claude-cliches.md`.

## 輸出格式

1. 問題清單，按嚴重度排序（幻覺類 J > 結構類 F/H/I > 風格類其餘），每項：原句 / Rule / 建議改寫方向
2. Rule L cliché scan：獨立區塊，格式見 `claude-cliches.md`「Detection protocol」— 先給每個 code 的 count vs budget 表，再列 CRITICAL / WARNING 明細
