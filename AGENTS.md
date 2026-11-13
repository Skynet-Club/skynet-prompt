# 给 agent 的说明（skynet-prompt）

本仓库提供 42 条带出处与中文直译的提示词。**取用只走一个入口：`psup` 命令。**
不要复制 `data/prompts.json` 到你自己的目录，也不要改写原文——副本必然过期，改写会让"可核"失效。

## 你能用的命令

```sh
psup                      # 交互（fzf 两栏），需要 fzf
psup <关键词…>            # 列出来，一行一条：id / 类目 / 中文（截断）/ 作者
psup packs                # 列出内置与扩展提示词包
psup audit                # 汇总 verbatim / paraphrase / unverified
psup capabilities         # 列出各入口与宿主支持等级
psupd                      # 本地只读 HTTP API
psup show <id>            # 一条的全文：原文、中文、作者、日期、性质、链接
psup print <id>           # 只要中文直译，可直接 $(psup print <id>)
psup print <id> --field en|url|author|id
psup list --json          # 结构化，适合你解析
psup selftest             # 自证：条数、类目数、sha256（与 meta 一致才算对）
```

开发后的完整质量门：`python3 scripts/test.py`（需要 `requirements-test.txt`）。

找不到 `psup` 时，装它：

```sh
python3 <本仓库>/scripts/install.py     # 只做两件事：链命令行；若本机有 Hermes 则挂抽屉
```

## 契约（四条，别越界）

1. **插入的文本 = `zh` 原样**，不加前缀、不改写、不截断。
2. 一次只补一条；补完告诉用户补了哪条（类目 + 标题），并说明可以撤销。
3. 用之前先跑 `psup selftest`，把 `sha256` 报给用户——那是这份数据是哪一版的唯一凭据。
4. 原文版权归各作者：引用时保留作者、日期、链接；不要把 `en` 整段转述成你的话。

## 数据字段

| 字段 | 含义 |
|---|---|
| `id` | 稳定标识，形如 `kp-verify-18` |
| `cat` | 内部类目键，显示名见 `meta.json → cats` |
| `author` / `date` / `url` | 出处 |
| `en` | 英文原文（`excerpt: true` 表示超过 200 字，属节选） |
| `zh` | 中文直译，与原文字面并列，不是改写 |
| `nature` | `本人原文` / `他人整理` / `未核实`——`他人整理` 的句子不是作者原话 |

## 现在的边界

- 42 条里 22 条逐字核对通过，12 条为他人整理，8 条未核实（见 `reports/source-check.json`）
- 12 条是他人整理的改写版本，8 条未核到原文
- 因此：**可以拿来用，但不要宣称"每一条都是作者原话"**
