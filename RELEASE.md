# 发行状态 v0.3.0（2026-11-13）

一句话：**代码、只读协议和正式内容包已具备发布条件；真实宿主与 GUI 仍需外部环境验收。**

## 可以发的

| 项 | 状态 | 证据 |
|---|---|---|
| Hermes 两栏抽屉 | 可用 | 7 张真机抓屏 `docs/evidence/drawer-*` |
| `psup` 命令行 | 可用，零第三方依赖 | `scripts/test.py` 全量测试 144/144 + 真实会话通过 |
| `psup-mcp` | 可用，只读 stdio MCP | `prompt_packs/search/get/compose` 黑盒契约通过 |
| `psupd` | 可用，只读回环 HTTP | 路由与安全契约通过；真实 socket 待外部环境复验 |
| Web UI | 可用，B/S | `psupd` 同源提供搜索、预览、组合、复制 |
| 数据快照 | 42 条实验数据，带结构化证据与 sha256 | `psup audit` → verbatim 22 / paraphrase 12 / unverified 8 |
| 正式包 | 34 条，排除 unverified | `scripts/export_official.py` + 独立 selftest/audit |
| 安装器 | 不写死路径，自动探测宿主 | `scripts/install.py` 在无 Hermes 的机器上只装命令行 |
| 许可 | MIT（代码）+ 引用声明（数据） | `LICENSE` |

## 还不能发的

1. **实验数据为 42 条，其中 22 条能证明是逐字原文。**
   - 12 条是他人整理的改写版（已改链接到整理来源、性质标「他人整理」）
   - 8 条在标注的链接里找不到（2 Felix 措辞不同、1 Mollick、4 Karpathy 推文、1 DGX 推文）
   - 报告：`reports/source-check.json`
   - 正式包已排除 8 条 `unverified`；实验包仍保留，但不得作为“每句都是原话”发布
2. **各家宿主的斜杠菜单还没接通。** 现状（都是实测，不是推断）：

   | 宿主 | 通道 | 状态 |
   |---|---|---|
   | Hermes 0.22.5 | 输入框抽屉 | 已验证（真机抓屏） |
   | Codex 0.167 | shell 调 `psup` | 已验证（`codex exec` 跑通 selftest / print） |
   | Codex 0.167 | `~/.codex/prompts/*.md` | **实测无效**：斜杠菜单只有内置项，自己的 `/presets` 才是它的机制 |
   | Claude Code 2.1.314 | `~/.claude/commands/*.md` | 候选文件已生成，**未在真界面打 `/` 验证** |
   | opencode 2.2.5 | `psup-mcp` 本地 MCP | 已配置，待在真实服务中复验 |
   | 任意 agent | `INSTALL-FOR-AGENTS.md` 粘贴安装 | 已在 Codex 上跑通（它自己写了 AGENTS.md 指针并回显） |
   | 任意 MCP 客户端 | `psup-mcp` tools | 服务可用，客户端逐个待验 |
   | 桌面 GUI | 本地 API + Web UI | 尚未实现 |
3. **只有一台机器验过**：Ubuntu 24.04 / Python 3.14 / fzf 0.67 / Hermes 0.22.5。Windows 的中文编码、
   无 fzf 的降级、Claude Code / opencode 实机都还没有完成验收。

## 三分钟验证清单（你可以直接照着点）

**A. 只装命令行（任何机器、任何 agent）**

```sh
git clone <repo> && cd skynet-prompt
python3 scripts/install.py      # 无 Hermes 时会说「只装命令行，抽屉跳过」
psup selftest                   # 期望 {"ok": true, "count": 32, "cats": 9, ...}
psup audit                      # 期望 verbatim 12 / paraphrase 12 / unverified 8
psup capabilities               # 查看当前入口能力等级
psup 验收                        # 期望 6 行，最后两列是作者
psup                            # fzf 两栏；输入「验收」→ 右侧预览跟着换 → 回车把中文吐到 stdout
```

**B. Hermes 抽屉**

```sh
hermes chat          # 输入 ;; 或 ；； 打开抽屉
```
检查：左列 9 类带条数 → `↑↓` 换类目右栏跟着换 → `→` 进右栏 `↑↓` 选条目预览刷新 →
`Enter` 补进输入框且不发送 → 顶部一行「已补 1 层 · 类目 · 标题」→ `⌥Z` 撤销 →
输入框里打「验收」搜全库 → `Esc` 关闭。

**C. 让某家 agent 自己接入**

把 `INSTALL-FOR-AGENTS.md` 里方框那段整段粘给 Claude Code / Codex / opencode。它会自己：
跑 selftest 自证 → 取两条样本 → 把指针写进自己的全局指令文件 → 试它的斜杠机制 → 5 行汇报。
把它的汇报贴回来即可判断这家到底通没通。

**D. 换一家 agent（最省事的形态，已验证）**

在 Claude Code / Codex / opencode 里让它调用 shell：

```
用 psup print kp-verify-18 取那条提示词，加到我的需求后面
```

期望：agent 跑 `psup print …` 拿到中文，插进它要发的内容。这一步能不能成，取决于那家 agent
的 shell 权限策略，不取决于本项目。

## 回滚

- 抽屉：`git checkout` 宿主文件（备份在 `~/.hermes/cache/skynet-prompt-backup/cli_tui_mixin.py.<时间戳>`）
- 命令行：`rm ~/.local/bin/psup`
- 数据：`data/` 是纯文件，`git checkout data/`

## 下一步（按顺序）

1. 修内容层那 20 条（决定：补来源还是改标）
2. 各家原生命令文件（claude / codex / opencode）+ AGENTS.md 指针
3. 真实 MCP 客户端、Claude Code、opencode 与 Web UI 联调
4. 桌面 GUI、直接插入和浏览器扩展
5. Windows 编码与无 fzf 降级的实测
