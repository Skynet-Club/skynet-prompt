# 给 Agent 的说明（skynet-prompt）

本仓库提供 75 条带出处与中文直译的提示词：56 条逐字可核、12 条他人整理、7 条未核实；作者包括 Karpathy、Felix Rieseberg、Daniel Miessler / Fabric contributors、云中江树 / LangGPT、DAIR.AI / Elvis Saravia 和 prompts.chat 的 CC0 贡献者。**取用只走一个入口：`psup` 命令。**
不要复制 `data/prompts.json` 到你自己的目录，也不要改写原文——副本必然过期，改写会让“可核”失效。

## 你能用的命令

```sh
psup                      # fzf 选择（需要 fzf）
psup list [关键词]        # 一行一条：id / 场景 / 中文 / 作者
psup list --category 定验收 --json
psup categories --json    # 9 个场景和条数
psup print <id>           # 只要中文正文
psup print <id> --field en|url|author|id
psup show <id>            # 全文：原文、中文、作者、日期、性质、链接
psup selftest             # 条数、场景、sha256
psup audit                # 证据和版权
psup doctor               # 本地数据是否可用
```

## 契约

1. **插入的文本 = `zh` 原样**，不加前缀、不改写、不截断。
2. 一次只补一条；补完告诉用户补了哪条（场景 + 标题），并说明可以撤销。
3. 用之前先跑 `psup selftest`，把 `sha256` 报给用户——那是这份数据是哪一版的唯一凭据。
4. 原文版权归各作者：引用时保留作者、日期、链接；不要把 `en` 整段转述成你的话。

## 数据字段

| 字段 | 含义 |
|---|---|
| `id` | 稳定标识，形如 `kp-verify-18` |
| `cat` | 内部场景键，显示名见 `psup categories --json` |
| `author` / `date` / `url` | 出处 |
| `en` | 英文原文（`excerpt: true` 表示超过 200 字，属节选） |
| `zh` | 中文直译，与原文字面并列，不是改写 |
| `nature` | `本人原文` / `项目原文` / `他人整理` / `未核实` |
| `evidence.verdict` | `verbatim` / `paraphrase` / `unverified` |

## 边界

- 56 条 `verbatim` 逐字核对通过，进入官方包；`official_ready=true`。
- 12 条 `paraphrase` 是他人整理，不是作者原话；7 条 `unverified` 未核到来源。
- 可以拿来用，但不要宣称“每一条都是作者原话”；官方包只认 56 条 `verbatim`。
