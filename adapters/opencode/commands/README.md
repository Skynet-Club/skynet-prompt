# opencode 产物（42 条）

由 `psup build` 从 `content/` 生成，不要手改。

## 安装

```sh
mkdir -p ~/.config/opencode/command
cp adapters/opencode/commands/psup-*.md ~/.config/opencode/command/
```

## 使用

当前输入框入口是 `/psup` 或 `/prompts`。统一触发器 `；；` 在该宿主暂无原生拦截，
因此会走文本指令或命令降级；也可以 `/psup-<id>` 直接取单条。

正文是中文直译，逐字节来自 `content/items/<id>/zh.txt`。要英文原文：

```sh
psup print kp-verify-18 --field en
```

菜单描述里的 `本人原话 / 他人整理 / 未核实 / 节选` 是出处标记，不是正文。
