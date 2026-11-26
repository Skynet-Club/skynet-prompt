# skynet-prompt

给 AI Agent 会话框补一条提示词：本地、只读、带出处。

- 75 条提示词，9 个场景：加目标 / 加深度 / 加广度 / 加约束 / 加证据 / 加检验 / 加读者 / 加执行 / 加时间；每条都有 `zh` + `en`，选择器里 `Tab` 切换；56 条逐字可核，12 条他人整理，7 条未核实。
- 内容来自 Karpathy、Felix Rieseberg、Daniel Miessler / Fabric contributors、云中江树 / LangGPT、DAIR.AI / Elvis Saravia 和 prompts.chat 的 CC0 贡献者。
- 官方包只发 56 条 `verbatim`；库里 75 条全部保留。选择器只显示正文和作者/来源，证据留在 `psup audit` / `psup show`。
- 一份 `data/prompts.json`，一个 sha256；没有 Registry、团队、审批、签名、同步、评测。

## 安装

```sh
ln -sf "$PWD/psup" ~/.local/bin/psup
psup selftest
opencode plugin add "$PWD/adapters/opencode-plugin"   # opencode
```

当前仓库包含 CLI、75 条数据、1:1:2 TUI 抽屉核心、opencode 适配器、DSH Web 适配器。Claude / Codex / pi / Copilot / Hermes 的宿主适配器在后续提交中补齐。

## 用

```sh
psup list              # 一行一条：id / 场景 / 中文 / 作者
psup list 测试         # 搜索
psup show <id>         # 全文、原文、作者、日期、链接
psup print <id>        # 只要中文正文
psup categories        # 场景和条数
psup selftest          # 条数 + sha256
psup audit             # 证据和版权
psup doctor            # 本地数据是否可用
```

Agent 取用只走 `psup`；不要复制 `data/prompts.json`，它会过期。

## TUI 抽屉

在支持输入钩子的 TUI 宿主里输入 `；；`，弹出左中右 1:1:2 的抽屉：

- 左：场景
- 中：条目
- 右：完整中文正文 + 作者/日期/链接 + 原文
- `↑↓` 选择，`→` 进条目，`Enter` 原样补入，`Esc` 关闭，`⌥Z` 撤销

### opencode

```sh
opencode plugin add "$PWD/adapters/opencode-plugin"
```

在会话里输入 `/p`（仅输入框行首）或按 `Alt+P`（任意光标）：打开 1:1:2 三栏浮窗——左场景、中条目、右完整正文；浮窗只占上半屏，会话输入框留在下方。`↑↓` 选择、`←→` 切栏、`Tab` 切换整个窗体的中/英文（顶部、提示行、栏标题、场景、条目、右栏和补入语言）、直接打字搜索、`Enter` 补入当前光标处、`Esc` 关闭。首页同样打开三栏浮窗；没有 `app` slot 的宿主才回退为两段选择。

### DeepSeek Harness

```sh
dsh plugin --profile web add "file:$PWD/adapters/dsh-plugin"
# 重启 dsh web
```

兼容性：DSH Web 已在 Linux 与 Windows 11 验证（0.1.3 + DSH 0.2.2-rc.5）；opencode TUI 当前在 Linux 验证，Windows 原生尚未适配。

输入框工具栏的 prompt 图标，或在光标处输入 `；；`（兼容 `;;`），打开上半屏 1:1:2 浮窗；浮窗宽度与会话框一致、左右对齐，停在会话框上方 8px；收起侧栏、缩放窗口时持续跟随。`Tab` 切换整个窗体的中/英文，`Enter` 或「插入」补入当前光标处；`/p` 菜单项也可。图标来自 `prompt.svg`（深灰圆角方块 + 荧光绿双引号）。

## 数据

`data/prompts.json` 是唯一数据源；`data/meta.json` 记录版本、条数、sha256 和场景统计。

- 56 条 `verbatim`：进入官方包。
- 12 条 `paraphrase`：他人整理，保留在库里。
- 7 条 `unverified`：保留在库里，不进入官方包。

`psup audit` 的 `official_ready=true` 只判断 56 条官方子集；实验内容不阻塞发布。未来新增内容必须带 `source`、`evidence`、`rights`，并按同样三档标注。

## 开发

```sh
python3 scripts/test.py
```

需要一个带 `prompt_toolkit` 的 Python（本仓库 `.venv/`）。

## 许可

代码 MIT；第三方提示词版权归各作者，引用时保留作者、日期和原始链接。
