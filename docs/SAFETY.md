# 提示词安全扫描

提示词可能包含会影响 Agent 工具调用的指令，因此发布前需要做供应链安全检查。

```sh
psup safety
psup safety --json
python3 scripts/scan_safety.py
```

报告写入 `reports/safety.json`。

当前规则检查：

- 覆盖系统/开发者指令；
- 读取或泄露 API key、密码、令牌和凭据；
- 上传或外传文件、密钥和 `.env`；
- 使用凭据登录或连接主机；
- 破坏性 Shell 命令；
- 下载后直接执行远程脚本；
- 不可信网络访问。

扫描结果只有：

- `passed`：未命中已知规则；
- `needs-review`：命中规则，必须人工判断。

`passed` 不等于人工批准。v2 条目的 `review.safety` 仍默认为 `unreviewed`；只有人工审核后
才能进入 `stable` 通道。扫描器只输出规则代码，不在报告中复制疑似秘密。
