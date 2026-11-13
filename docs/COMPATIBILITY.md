# 兼容性清单

当前平台范围：**Linux（Ubuntu/Debian 系已验证）**。Windows 和 macOS 尚未支持，
只作为未来计划；Bootstrap 会在非 Linux 平台拒绝安装。

支持等级：

| 等级 | 能力 |
|---|---|
| A | 直接插入光标并撤销 |
| B | 查询、读取、组合或由 Agent 调用 |
| C | 浏览、复制后手动粘贴 |
| D | 无可靠集成路径 |

机器可读清单：

```sh
psup capabilities
psup capabilities --json
```

统一用户触发器是 `；；`；`;;` 只作为兼容别名。原生输入框拦截和文本指令降级是两种
不同能力，详见 [TRIGGER.md](TRIGGER.md)。

当前状态：

| 入口 | 等级 | 状态 |
|---|---|---|
| `psup` CLI | B | 可用 |
| `psup` fzf TUI | B | 可用 |
| `psup-mcp` | B | 可用 |
| `psupd` 本地 API | B | 仅回环地址 |
| Web UI | C | 仅回环地址 |
| Hermes 抽屉 | A | 0.22.5 已验证 |
| Codex Shell | B | 已验证 `psup` |
| Claude Code Skill + Hook + MCP | B | 2.1.314 已安装；MCP 健康检查受环境阻塞 |
| OpenCode Shell | B | 2.2.7 standalone 实测通过 |
| OpenCode TUI 插件 | B | 实验，自动测通过，待真实 TUI 验收 |
| pi Shell + package | B | 1.5.0 实测通过，包已安装 |
| Copilot CLI Shell | B | 1.0.107 实测通过 |
| DeepSeek Harness | B | 0.2.1-rc.5 headless 与 Web 服务实测通过 |
| 1Agent | B | 0.96.1 terminal 工具实测通过；当前 build 不支持 DeepSeek provider |
| 桌面 GUI | D | 计划中 |

触发方式：

| 入口 | 触发方式 | 状态 |
|---|---|---|
| Hermes | `；；` 即时抽屉 | 已验证 |
| pi | `；；` 即时抽屉 | 包已安装，待完整 TUI 回归 |
| Codex | `；；` 指令识别；兼容 `$psup` | 待新版插件验收 |
| OpenCode | `/prompts`；文本 `；；` 暂无原生拦截 | 已知边界 |
| MCP 客户端 | `；；` 指令 + MCP tools | 协议已写入 initialize |
| Copilot | Extension 拦截 `；；`，Skill + MCP 查询 | 已安装，模型认证待恢复 |
| Claude Code | UserPromptSubmit Hook 注入上下文，Skill + MCP 查询 | 已安装，MCP 健康检查待恢复 |
| CLI / HTTP / Web | `psup` / UI 操作 | 已可用 |

Agent 自安装：

| 能力 | 当前策略 |
|---|---|
| 固定安装契约 | `AGENT_INSTALL.md` |
| 机器清单 | `install-manifest.json` |
| 默认行为 | `scripts/agent_install.py --plan`，只读 |
| 单入口 | `./skynet-prompt-bootstrap` 检测系统和 Agent 版本后生成计划 |
| 修改系统 | 用户确认后显式 `--apply` |
| 自动验收 | `psup selftest` + `psup doctor` |
| 未知客户端 | 只安装 CLI，不猜 Skill 或插件目录 |
| 签名身份 | 可选 `--trust <keys.json>` 校验 key id、状态和公钥指纹 |
| Copilot 输入拦截 | `~/.copilot/extensions/skynet-prompt/extension.mjs` |
| Claude 输入拦截 | `~/.claude/skynet-prompt/hook.py` + UserPromptSubmit |

一句话安装只适用于有命令执行和文件写入能力的 Agent；纯聊天客户端只能使用文本降级。

真实第三方客户端验收完成后，必须同步更新 `skynet_prompt/compat.py` 和本表。

opencode 的 `/psup`（`/prompts` 同义）由实验性本地 TUI 插件提供：

1. 在会话输入框输入 `/psup` 或 `/prompts`。
2. 第一层用 opencode 原生 select 对话框选择类目。
3. 第二层选择具体提示词。
4. 插件通过 `tui.prompt.append` 将 `zh` 插入当前输入框，不发送。

旧的 Markdown 命令保留为 MCP 不可用时的聊天式降级路径。

通用性的边界：

- Prompt Pack、搜索、读取和组合通过 CLI/MCP/HTTP 通用。
- 用户入口统一为 `；；`，但插入方式和即时拦截能力没有跨 Agent 标准，必须逐个适配。
- opencode TUI 插件不能作为其他 Agent 的兼容层。
