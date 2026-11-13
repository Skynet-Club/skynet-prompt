# content/

逐条冻结的内容层。**文本文件就是正文字节**：不折行、不做引号/空白规范化、不加前后缀、
不自动补结尾换行。

```text
content/
  index.json                 # 32 条的清单、计数、类目名与 digest
  items/<id>/
    zh.txt                   # 默认插入文本（逐字节）
    en.txt                   # 英文原文（逐字节）
    meta.json                # 类目、作者、日期、链接、出处类型、两个 sha256
```

## 字段

| 字段 | 取值 | 说明 |
|---|---|---|
| `origin` | `verbatim` / `compilation` / `unverified` | 本人原话 / 他人整理 / 未在标注链接定位到 |
| `excerpt` | `true` / `false` | 原文超过 200 字时的节选标记，与 `origin` 正交 |
| `sha256.zh` / `sha256.en` | 64 位十六进制 | 两个文本文件的摘要 |
| `source.url/author/published_at` | 字符串 | 出处；不再保留 `quote`（与 `en.txt` 重复） |
| `source.license` | 字符串 | 来源许可；未声明时明确记录 `not-declared` |
| `source.rights_basis` | `short-quotation-with-attribution` | 只做带署名的短句引用 |
| `source.redistribution` | `excerpt-only` | 不允许把第三方全文作为正式包分发 |

旧数据里的 `nature` 与 `evidence.verdict` 两套字段已合并为 `origin`，以
`evidence.verdict` 为准：`verbatim → verbatim`、`paraphrase → compilation`、
`unverified → unverified`。原先 9 条互相矛盾的记录由此消失。

## 校验

```sh
psup verify                  # 读 content/，并与 data/prompts.json 做逐字节比对
python3 scripts/freeze_content.py --check
```

任何一条 `zh.txt`/`en.txt` 与 `data/` 不是逐字节一致、`meta.json` 声明与文件摘要不符、
`index.json` 计数或 digest 不符，都会失败并指出条目 id。

## 状态

`content/` 是发布与构建真相源。`data/` 是旧客户端兼容镜像，迁移期两者必须逐字节一致；
`data/` 不得作为独立编辑入口。

编辑工作区（Club / 飞书）只负责候选、审核和导入。只有审核通过的不可变快照进入
`content/`；Registry 上线后，客户端读取签名发布清单和本地缓存，不读取编辑数据库。

当前运行时仍读兼容镜像 `data/`，`psup verify` 和
`python3 scripts/freeze_content.py --check` 负责硬校验一致性。读路径迁移必须作为独立
工作包完成，不能用“两边看起来一样”替代校验。
