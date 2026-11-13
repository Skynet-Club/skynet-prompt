# 统一提示词触发器

用户只需要记住：

```text
；；
```

它是 `skynet-prompt` 的统一入口。ASCII 的 `;;` 只作为兼容别名，不写入新手说明。

## 交互规则

- 输入 `；；`：打开或请求提示词选择器。
- 输入 `；； 验收`：打开选择器并带入搜索词。
- 输入 `；； 定验收`：直接进入指定类目。
- 输入 `；； kp-verify-18`：直接预览指定条目。
- 输入 `；；；`：保留字面量 `；；`，不触发。
- 代码块、URL 和已有普通正文中的分号不触发。

## 宿主降级

| 能力 | 宿主 | 行为 |
|---|---|---|
| 原生即时抽屉 | Hermes、pi | 立即显示选择器；选中后原样插入，不发送 |
| 指令识别 | Codex、MCP 客户端 | 把 `；；` 解释为提示词查询；返回候选和来源 |
| 输入事件拦截 | Copilot | Extension 改写 `；；`，再调用个人 Skill 和本地 MCP |
| 输入事件拦截 | Claude Code | UserPromptSubmit Hook 注入明确查询上下文 |
| 命令降级 | Claude Code、Copilot、DSH、1Agent | 使用 `psup` 查询；无法插入时复制正文 |

OpenCode 当前插件只有 `/psup` 和 `/prompts` 入口，未提供纯文本输入拦截。这个限制必须
在安装提示和能力清单中明确显示；不能把它算作原生 `；；` 支持。

统一的是用户入口和结果契约，不是宿主的私有实现。任何宿主都不得声称支持它没有的能力。

## 命令兼容

Shell 和脚本继续使用 `psup`，不能把 `；；` 当作 Shell 命令：

```sh
psup
psup 验收
psup show kp-verify-18
psup print kp-verify-18
```

机器可以读取：

```sh
psup capabilities --json
```

其中的 `experience.trigger`、`aliases`、`literal_escape` 和降级能力列表是协议事实来源。
