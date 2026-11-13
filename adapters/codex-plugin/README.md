# Codex 产物（42 条）

由 `psup build` 从 `content/` 生成，不要手改。

## 安装

```sh
codex plugin marketplace add <owner>/skynet-prompt
codex plugin add skynet-prompt@skynet-prompt
```

## 使用

输入 `；；` → 只列 9 个类目；回复类目 → 只列该类条目；回复 id → 原样正文。

```text
；；
；； 先想清楚
；； kp-think_first-03
```

也可以直接用 `$psup-<id>` 取单条。

Codex 的显式技能兼容入口仍然可用：

```text
$psup
$psup-kp-verify-18
```

也可以输入 `$` 打开技能列表，或用 `/skills` → List skills。

每个 skill 的正文是中文直译，逐字节来自 `content/items/<id>/zh.txt`；
单条 skill 使用 `disable-model-invocation: true`，只能显式选择；索引 skill 由统一
触发器激活，不会被普通请求自动挑中。
菜单描述里的 `本人原话 / 他人整理 / 未核实 / 节选` 是出处标记，不是正文。

要英文原文：

```sh
psup print kp-verify-18 --field en
```
