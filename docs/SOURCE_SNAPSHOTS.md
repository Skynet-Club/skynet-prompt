# 来源快照与采集

`reports/sources/index.json` 是 schema 1 来源 manifest，至少记录：

- 原始 URL；
- 本地快照文件；
- SHA-256；
- 文件大小；
- 媒体类型；
- 抓取方式；
- 抓取时间；
- 是否可用。

校验：

```sh
psup sources
psup sources --json
python3 scripts/check_sources.py
```

升级旧索引或重新登记本地文件：

```sh
python3 scripts/build_source_manifest.py
```

正式 v2 包导出的 `source.snapshot_sha256` 来自 manifest 校验后的文件内容。来源文件缺失、
哈希不符或 URL 未登记时，正式导出失败。

`scripts/check_sources.py` 另外核对提示词原文片段是否出现在快照中；该报告用于判断
`verbatim / paraphrase / unverified`，与快照文件完整性检查是两层不同门槛。

当前新增内容使用 Fabric `v1.4.568` 固定标签的 10 个 pattern 快照，许可证为 MIT；原文、
仓库元数据、LICENSE 和逐文件 SHA-256 均可复核。
