# skynet-prompt Agent 安装契约

这份文件是给 Agent 执行的固定契约。用户只需要理解一句话：

> 请读取 skynet-prompt 的 `AGENT_INSTALL.md`，先展示安装计划；我确认后执行安装，
> 最后报告机器验证结果。不要读取凭据、发送提示词或执行远程脚本。

## 适用范围

当前仅支持 Linux（Ubuntu/Debian 系已验收），要求 Python 3.8+，安装不需要 `sudo`。
Windows 和 macOS 暂不支持，计划在未来版本提供。

支持的宿主适配器：

| 适配器 | 检测方式 | 能力 |
|---|---|---|
| `cli` | 始终可用 | `psup`、`psup-mcp`、`psupd` |
| `codex` | `command -v codex` | Skill、`；；` 指令、CLI |
| `pi` | `command -v pi` | Package、`；；` 抽屉、插入和撤销 |
| `opencode` | `command -v opencode` | TUI plugin、`/prompts`、MCP |
| `hermes` | `command -v hermes` | 原生 `；；` 抽屉、插入和撤销 |
| `copilot` | `command -v copilot` | 个人 Skill、输入触发器 Extension、MCP、CLI |
| `claude` | `command -v claude` | 个人 Skill、Input Hook、MCP、CLI |

其他客户端不会由 Agent 猜测配置路径。它们只能使用 CLI；只有在客户端已经提供明确、
可验证的 MCP 或 Skill 安装方式时，才可以额外配置。

## 获取固定版本

Agent 先读取 release 的 `install-manifest.json`，根据 `source.type` 选择获取方式：

### release-archive

当 `source.type` 是 `release-archive` 时：

1. 从同一 release 下载 `source.archive`；
2. 校验文件 SHA-256 等于 `source.sha256`；
3. 解压到新的临时目录；
4. 使用解压目录中的安装契约和执行器。

校验失败立即停止，不得解压执行或退回到其他分支。

如果 manifest 包含 `signature`，还必须验证 Ed25519 签名。manifest 内嵌公钥只能证明
内容未被改动；发布者身份必须通过独立可信渠道核对 `key_id` 和公钥指纹。签名无效时停止。

manifest 的 `contract.sha256` 是当前安装契约的 SHA-256。Agent 在执行本文件步骤前必须
核对当前 `AGENT_INSTALL.md` 哈希；不一致时停止。

如果 Agent 已从独立渠道取得发布者公钥库，可以在所有执行器命令中传入：

```sh
python3 scripts/agent_install.py --plan --trust /path/to/known/trust/keys.json
```

提供 `--trust` 时，签名身份校验失败必须立即停止。

### local-checkout / git-tag

公开发布后，Agent 必须使用 release tag 或不可变 commit，不得默认安装 `main`：

```sh
git clone --depth 1 --branch v0.3.0 <REPOSITORY_URL> /tmp/skynet-prompt-install
cd /tmp/skynet-prompt-install
```

如果 release 提供 `SHA256SUMS`，先校验下载产物。校验失败立即停止，不允许继续安装。

当前开发机已经在本地 checkout 中时，可以直接在该仓库根目录执行后续命令。

## 第一步：只读计划

```sh
./skynet-prompt-bootstrap
```

等价的机器入口是：

```sh
python3 scripts/agent_install.py --plan
```

Agent 必须向用户展示：

- manifest 中的版本和触发器；
- 检测到的适配器；
- 将要安装的适配器；
- 跳过的适配器和降级方式；
- 将要执行的安装命令；
- 卸载命令。

默认模式不会创建链接或修改宿主配置。

## 第二步：用户确认

展示计划后必须停下来等待用户明确确认。用户没有确认时不得运行 `--apply`。

## 第三步：执行并自检

```sh
./skynet-prompt-bootstrap --apply
```

等价的机器入口是：

```sh
python3 scripts/agent_install.py --apply
```

安装器只安装：

- `cli`；
- 本机检测到并选中的宿主适配器；
- 用户在计划中明确接受的适配器。

安装完成后执行器自动运行：

```sh
psup selftest
psup doctor
```

也可以单独验证：

```sh
python3 scripts/agent_install.py --verify
```

硬门是：

```text
selftest.ok = true
selftest.count = 42
sha256 = meta_sha256
doctor.ok = true
```

任何一项失败时，Agent 必须停止并把原始机器报告返回给用户。

## 第四步：报告

Agent 最终至少报告：

```text
STATUS
version
detected adapters
installed adapters
trigger
selftest count and hash
doctor result
modified locations
uninstall command
```

不要用自然语言声称“应该已经安装好”。只有 `--apply` 返回 `ok=true` 且 verification
全部通过，才能报告安装成功。

## 卸载

```sh
python3 scripts/agent_install.py --uninstall
```

如果计划中选择了特定适配器，卸载时保留相同的 `--adapter` 参数：

```sh
python3 scripts/agent_install.py --adapter codex --uninstall
```

Hermes 当前通过修改宿主源码挂载抽屉。安装器和卸载器会报告备份位置；不要删除备份，
除非用户明确要求。

## 安全边界

Agent 不得：

- 使用 `sudo`；
- 执行 `curl | sh`；
- 从 `main` 或其他可变分支直接安装；
- 读取 API Key、Cookie、SSH key 或 Agent 会话；
- 发送、发布或改写提示词正文；
- 跳过 `selftest` 和 `doctor`；
- 在不存在的宿主上伪造安装成功；
- 自行猜测未知客户端的扩展目录。

Agent 可以：

- 读取本文件和 `install-manifest.json`；
- 运行安装器生成的只读计划；
- 在用户确认后运行 `--apply`；
- 读取安装器的 JSON 报告并原样转述失败；
- 在失败后运行对应卸载命令。

## 客户端能力判断

一个客户端可以被 Agent 自动安装，至少需要同时提供：

1. 执行命令；
2. 写入用户目录；
3. 访问已下载源码或 release；
4. 宿主自己的扩展、Skill 或 MCP 配置入口；
5. 安装后的重新加载方式。

缺少宿主扩展入口时，Agent 只能安装通用 CLI，不能声称获得了原生 `；；` 抽屉。
客户端名称、界面外观或“看起来像 Agent”不能作为兼容证据。
