# 客户端同步、缓存与回滚

```sh
psup update --registry dist/registry/registry.json --pack official --channel dev
psup update --registry dist/registry/registry.json --pack official --channel dev
psup doctor --registry dist/registry/registry.json
psup cache
psup rollback --pack official --channel dev
psup pin --pack official --channel dev
psup unpin --pack official --channel dev
psup events
```

默认本地目录：

```text
~/.local/share/skynet-prompt/
  state.json
  packs/<pack>/<version>/
  cache/objects/<sha-prefix>/<sha-rest>
```

行为：

- Registry 与当前绑定版本相同：零 Pack 下载；
- 版本变化：只安装目标版本；
- Pack manifest、正文和签名必须验证；
- 正文写入内容寻址缓存，Pack 目录使用硬链接复用缓存对象；
- 安装完成后再原子更新 `state.json`；
- 每个绑定保留最近 10 个历史版本用于回滚；
- 回滚前重新验证旧版本签名；
- 固定版本后，新版本只提示可用但不会自动升级；
- 更新、回滚、固定和解除固定写入本地审计事件；
- `doctor` 检查本地 Pack、签名和 Registry。

`SKYNET_PROMPT_STORE` 可覆盖本地目录；`--store` 优先于环境变量。
