# Codex Ctrl+G 抽屉（可选）

Codex 的插件系统只提供 `$` 技能引用，不能像 pi 那样在输入框里原生拦截 `；；`。
默认安装走 `$psup` 快捷指令，不需要组合键。只有你接受 **Ctrl+G** 时，才用
这个可选入口：它把当前草稿写进临时文件，调用 `$VISUAL/$EDITOR`，再把文件
内容放回输入框（不发送）。

```text
草稿：你好；；（兼容别名 ;;）
按 Ctrl+G
  → 两级抽屉（左类目 / 右条目 / 下方预览）
  → ↑↓ 选择，→ 进列表，← 回类目
  → Enter 把 ;; 替换成中文原文，Esc 取消
  → 回到 Codex 输入框，仍未发送
```

## 用

```sh
./install.sh --with-picker codex
```

它会把 `codex` 换成一个只设置 `$VISUAL` 的 shim（原软链备份为
`codex.real`，`./install.sh --uninstall codex` 可恢复）。之后直接：

```sh
codex
```

输入 `；；`（兼容 `;;`），按 **Ctrl+G**。

不想改 `codex` 软链时，也可以手动：

```sh
export VISUAL=/home/skynet/skynet-prompt/adapters/codex-picker/psup-editor.sh
codex
```

或者用自带 wrapper：

```sh
ln -s /home/skynet/skynet-prompt/adapters/codex-picker/codex-prompt.sh ~/.local/bin/codex-prompt
codex-prompt
```

## 回退

`psup-editor.sh` 只在草稿里有 `；；` / `;;` 时打开抽屉；没有时交给
`$PSUP_FALLBACK_EDITOR`（默认 `vi`），所以 Ctrl+G 仍然可以当普通外部编辑器用。

## Codex 里的技能不是斜杠命令

`/psup` 在 Codex 里不存在——插件技能通过 `$` 引用：

- 输入 `$psup` 按类目浏览 42 条
- 或直接输入 `$psup-kp-verify-18`
- 或输入 `$` 打开技能列表，或 `/skills` → List skills

`$` 技能插入的是技能名；要把**正文**放进输入框，用上面的 `;; + Ctrl+G`。
