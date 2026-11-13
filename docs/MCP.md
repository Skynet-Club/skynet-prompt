# MCP 接入

`psup-mcp` 是只读 stdio MCP Server，支持：

- `prompt_packs`
- `prompt_search`
- `prompt_get`
- `prompt_compose`

它和 CLI 共用 `PromptService`，不读取 Agent 会话，不发网络请求，不写本地内容。

## 客户端配置

```json
{
  "mcpServers": {
    "skynet-prompt": {
      "command": "/home/skynet/skynet-prompt/psup-mcp"
    }
  }
}
```

安装器会把 `psup` 和 `psup-mcp` 一起链接到 `~/.local/bin`：

```sh
python3 scripts/install.py
```

opencode 2.2.5 可直接注册本地 MCP：

```sh
opencode mcp add skynet-prompt --global -- ~/.local/bin/psup-mcp
opencode mcp list
```

如果 `mcp list` 报 `EPERM: operation not permitted, listen`，先修复 opencode 后台服务的
监听权限；这不是 `psup-mcp` 故障。

opencode 的二级输入框菜单由本地 TUI 插件提供，不依赖 Markdown 命令：

- 输入 `/psup` 或 `/prompts`：类目 → 条目 → 插入当前输入框。
- `/psup`：聊天式降级流程，由 Agent 调用 MCP。

插件位置：`adapters/opencode-plugin/`，注册在 `~/.config/opencode/cli.json`。

## 工具契约

`prompt_search` 接受：

```json
{
  "query": "验收 裁判",
  "category": "定验收",
  "pack": "builtin",
  "limit": 10
}
```

所有关键词必须同时命中。`category` 可以使用内部键或显示名。

`prompt_compose` 只按 `ids` 顺序拼接 `zh` 或 `en`，不调用模型，不做改写。
