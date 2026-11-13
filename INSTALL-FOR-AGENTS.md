# 给 agent 的安装指令

把下面这段粘给任意 agent（Claude Code / Codex / opencode / Copilot / 别的能跑 shell 的）：

---

读 `/home/skynet/skynet-prompt/AGENTS.md`，按它接入。然后只回四件事：

1. `psup selftest` 的原样输出
2. `psup print kp-verify-18` 的原样输出
3. `psup capabilities --json` 的原样输出
4. 你把接入指针写进了哪个文件（你自己的全局指令文件，给绝对路径）

缺什么、做不到什么，直接说；不要编，也不要复制 `data/prompts.json`。

可选：如果你的 `/` 菜单能加自定义命令，把 `adapters/<你的名字>/` 拷进你的命令目录，
在界面里按 `/` 看「定验收」有没有出现；出不来就说这家不支持，别硬装。

---

## 为什么就三行

- **契约在 `AGENTS.md` 里，不在指令里。** 指令只负责让 agent 去读它；读文件是它最擅长的事，
  把契约抄进粘贴框只会多一份会过期的副本。
- **只要两个可核对的东西。** `selftest` 证明数据是哪一版（sha256 对得上 meta 才算），`print`
  证明它真能取到正文。其余都是话术。
- **第 3 条防的是"假装装好了"。** 让它报出写了哪个文件，你一眼能去核；报不出来就是没做。

## 各家目前的样子（实测）

| 宿主 | 通道 | 状态 |
|---|---|---|
| Hermes | 输入 `;;` / `；；` 抽屉 | 可用 |
| Codex | shell 调 `psup` | 已验证 |
| Codex | 斜杠菜单 | **不支持**：`~/.codex/prompts/` 在 0.167 上不进菜单，它自己的机制叫 `/presets` |
| Claude Code | shell 调 `psup` | 实验：命令文件尚未真机验收 |
| opencode 2.2.5 | `psup-mcp` / TUI 插件 | 实验：自动测通过，待真实 TUI 验收 |
| pi | package / `psup` | 实验：包已生成，待真实宿主验收 |
| 任意 MCP 客户端 | `psup-mcp` tools | 服务可用，客户端逐个待验 |
| 浏览器 / GUI | Web UI 或 MCP tools | Web UI 可用；桌面 GUI 未实现 |
