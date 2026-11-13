# 来源证据字段

条目在兼容旧字段的基础上增加两组结构化字段：

```json
{
  "source": {
    "quote": "来源中的候选文本",
    "url": "https://example.com/source",
    "author": "Author",
    "published_at": "2026-11-11"
  },
  "evidence": {
    "verdict": "verbatim",
    "checked_at": "2026-11-11T21:32:17+08:00",
    "method": "curl",
    "report": "reports/source-check.json"
  }
}
```

`evidence.verdict` 只有三种值：

- `verbatim`：来源页面能逐字找到引文。
- `paraphrase`：有明确整理来源，但不是作者原话。
- `unverified`：没有找到可核来源，只能进入实验数据。

正式包还必须包含结构化版权字段。未声明许可的来源明确记录为
`license: not-declared`，并通过 `rights_basis` 和 `redistribution` 限定为短引用分发。
详见 `docs/RIGHTS.md`。

包清单设置 `"require_evidence": true` 后，加载时强制检查 `source.quote`、
`source.url`、`evidence.verdict` 和 `evidence.checked_at`。内置 `data/meta.json`
也会控制同一门槛。

```sh
psup audit
psup audit --json
python3 scripts/export_official.py
```

审计不会把旧 `nature` 字段猜成“已核实”，只汇总实际结构化证据。
`ok=true` 表示所有条目都有结构化证据；`official_ready=true` 还要求
`unverified=0`，内置 42 条实验包当前为 false，正式 34 条包为 true。

`scripts/export_official.py` 生成 `dist/official/prompts.json` 和 `pack.json`，只保留
`verbatim` 与 `paraphrase`。当前内置 42 条会导出 34 条，8 条 `unverified` 只保留在
实验快照中，不进入正式发布包。

正式包同时生成 `meta.json`，因此可以独立运行，不与内置实验快照叠加：

```sh
SKYNET_PROMPT_DATA=dist/official psup audit
SKYNET_PROMPT_DATA=dist/official psup selftest
```
