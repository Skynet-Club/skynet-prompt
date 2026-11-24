# skynet-prompt

给 AI Agent 会话框补一条提示词：本地、只读、带出处。

- 42 条提示词，9 个类目：22 条逐字可核，12 条他人整理，8 条未核实。
- 官方包只发 22 条 `verbatim`；库里 42 条全部保留，选择器里带证据标签。
- 一份 `data/prompts.json`，一个 sha256；没有 Registry、团队、审批、签名、同步、评测。

## 安装

```sh
ln -sf "$PWD/psup" ~/.local/bin/psup
psup selftest
```

当前仓库包含 CLI、42 条数据、1:1:2 TUI 抽屉核心。Claude / Codex / opencode / pi / Copilot / Hermes 的宿主适配器和 DSH 嵌入式插件在后续提交中补齐。

## 用

```sh
psup list              # 一行一条：id / 类目 / 中文 / 作者
psup list 验收         # 搜索
psup show <id>         # 全文、原文、作者、日期、链接
psup print <id>        # 只要中文正文
psup categories        # 类目和条数
psup selftest          # 条数 + sha256
psup audit             # 证据和版权
psup doctor            # 本地数据是否可用
```

Agent 取用只走 `psup`；不要复制 `data/prompts.json`，它会过期。

## TUI 抽屉

在支持输入钩子的 TUI 宿主里输入 `；；`，弹出左中右 1:1:2 的抽屉：

- 左：类目
- 中：条目
- 右：完整中文正文 + 作者/日期/性质/链接 + 原文
- `↑↓` 选择，`→` 进条目，`Enter` 原样补入，`Esc` 关闭，`⌥Z` 撤销

## 数据

`data/prompts.json` 是唯一数据源；`data/meta.json` 记录版本、条数、sha256 和类目统计。

- 22 条 `verbatim`：进入官方包。
- 12 条 `paraphrase`：他人整理，保留在库里，选择器标注“他人整理”。
- 8 条 `unverified`：保留在库里，选择器标注“未核实”，不进入官方包。

`psup audit` 的 `official_ready=true` 只判断 22 条官方子集；实验内容不阻塞发布。未来新增内容必须带 `source`、`evidence`、`rights`，并按同样三档标注。

## 开发

```sh
python3 scripts/test.py
```

需要一个带 `prompt_toolkit` 的 Python（本仓库 `.venv/`）。

## 许可

代码 MIT；第三方提示词版权归各作者，引用时保留作者、日期和原始链接。
