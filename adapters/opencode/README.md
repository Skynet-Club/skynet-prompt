# opencode 命令文件（10 个）

由 `scripts/export_commands.py --target opencode` 生成。

拷到宿主自己的命令目录即可：

| 宿主 | 目录 |
|---|---|
| Claude Code | `~/.claude/commands/` |
| Codex | `~/.codex/prompts/` |
| opencode | `.opencode/command/` 或 `~/.config/opencode/command/` |

这些文件不含数据，只调用 `psup`；发布快照在 `content/`，`data/` 仅作兼容镜像。
