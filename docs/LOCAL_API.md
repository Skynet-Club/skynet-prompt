# 本地 HTTP API

`psupd` 提供只读本地 API，默认监听 `127.0.0.1:8765`。服务拒绝绑定非回环地址。

```sh
psupd
psupd --port 0   # 随机端口，适合测试和客户端探测
```

启动后打开 `http://127.0.0.1:8765/` 使用内置 Web UI。Web UI 与 API 同源，不加载
第三方脚本，不向外发送数据。

接口：

```text
GET  /v1/health
GET  /v1/capabilities
GET  /v1/packs
GET  /v1/categories
GET  /v1/audit
GET  /v1/items/{id}
POST /v1/search
POST /v1/compose
```

搜索请求：

```json
{
  "query": "验收 裁判",
  "category": "定验收",
  "pack": "builtin",
  "limit": 10
}
```

组合请求：

```json
{
  "ids": ["fx-verify-13", "fx-verify-15"],
  "field": "zh",
  "separator": "\n\n"
}
```

所有接口与 CLI、MCP 共用 `PromptService`。服务不写数据、不调用模型、不接收 Agent 会话，也不提供远程访问。
