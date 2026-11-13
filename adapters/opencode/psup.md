---
description: 浏览 skynet-prompt 全库并选择条目
---

使用 `skynet-prompt` MCP 工具浏览全库：

1. 调用 `prompt_search`，参数 `{"limit":200}`。
2. 按 9 个类目分组，用编号展示每条的 `id`、中文、作者和可信状态。
3. 展示后停下来等用户按编号或 id 选择，不要自动应用。
4. 用户选择后调用 `prompt_get`，把 `zh` 原样作为当前任务的附加约束，并说明来源与撤销。

不要生成新提示词，也不要把 paraphrase 或 unverified 说成作者原话。
