# 提示词包扩展接口

提示词目录由 `skynet_prompt.catalog.PromptCatalog` 统一合并。CLI、Hermes 抽屉和未来的
HTTP/MCP 客户端都从这个目录读取，不在界面层各自维护数据源。

## 本地包

一个扩展目录至少包含两个文件：

```text
team-pack/
  pack.json
  prompts.json
```

`pack.json`：

```json
{
  "schema_version": 1,
  "id": "team-backend",
  "name": "后端团队提示词",
  "version": "2026.11",
  "items": "prompts.json",
  "sha256": "<prompts.json 的 SHA-256，可省略>"
}
```

`prompts.json` 使用现有顶层结构：

```json
{
  "version": "2026.11",
  "count": 1,
  "items": [
    {
      "id": "team-backend-verify-01",
      "cat": "verify",
      "author": "Team",
      "date": "2026-11-12",
      "url": "https://example.com/source",
      "en": "State the acceptance check.",
      "zh": "先写清楚验收标准。",
      "nature": "本人原文"
    }
  ]
}
```

接入一个或多个包：

```sh
SKYNET_PROMPT_PACKS=/path/to/team-pack:/path/to/other-pack psup packs
psup list --pack team-backend
```

`SKYNET_PROMPT_PACKS` 使用操作系统路径分隔符；Linux/macOS 是 `:`，Windows 是 `;`。值可以是
包目录，也可以直接指向 `pack.json`。

包和条目 id 在整个目录中必须唯一。`id`、`cat`、`author`、`date`、`url`、`en`、`zh`
是必填字段；`cat` 必须属于现有的 9 个类目。清单写了 `sha256` 时，加载会硬校验。

## 程序化数据源

未来接入 Club、HTTP、数据库或 MCP 时，先由同步层取得并校验不可变快照，再实现同一个最小接口：

```python
from skynet_prompt.catalog import PromptCatalog, PromptPack


class RemoteSource:
    def load(self) -> PromptPack:
        return PromptPack(
            id="remote-team",
            name="Remote Team",
            version="42",
            items=load_remote_items(),
            sha256="source-provided-digest",
        )


catalog = PromptCatalog([RemoteSource()]).load()
items = catalog.items()
```

任何来源返回的包都会经过同一套校验、重复 id 检查和类目检查。远端加载逻辑放在 source
内部；`PromptCatalog` 和下游客户端不感知网络、缓存或鉴权。

运行时命令行、MCP 和本地 API 不直接读取 Club 编辑数据库。在线来源的职责是更新本地
发布包或缓存，Core 继续消费确定性快照。
