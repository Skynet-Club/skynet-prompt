---
name: skynet-prompt
description: 当用户消息以 ；；（兼容 ;;）开头时，从本地 skynet-prompt 提示词库搜索类目、条目或指定 id，展示来源和作者后原样返回正文。
---

# skynet-prompt

当用户消息以 `；；` 或兼容的 `;;` 开头时：

1. 去掉触发器，把后面的文字当作类目、搜索词或条目 id。
2. 优先使用已连接的 `skynet-prompt` MCP 工具：
   - 搜索：`prompt_search`
   - 读取：`prompt_get`
3. 如果没有 MCP，则运行：
   - 无后续文字：`psup categories --json`
   - 类目：`psup list --category <key> --json`
   - 条目 id：`psup print <id>`

不要一次列出全部条目。返回正文时保留来源、作者和可信状态，不重写、不截断正文。
单独输入 `；；；` 时保留字面量 `；；`，不调用工具。
