# v2 发布流水线

```sh
psup release --channel dev --out dist/release
python3 scripts/release.py --channel dev --out dist/release
```

流水线按顺序执行：

1. `content/` 与 `data/` 逐字节和 digest 校验；
2. 证据和版权字段审计；
3. 34 条正式条目的来源、翻译和安全审核账本校验；
4. 来源快照文件与 SHA-256 校验；
5. 正式条目安全扫描；
6. 宿主产物构建一致性检查；
7. 导出 Pack v2；
8. 重新加载导出包并验证 schema；
9. 写入 `release-report.json`。

任何一步失败都会终止整次发布。`dev` 和 `canary` 允许未签名包用于内部验证；`stable`
在 M2 签名实现前始终拒绝。

报告包含包版本、digest、内容 digest、证据/版权统计、审核数、快照数、安全规则版本和
Git commit，便于把发布结果回溯到具体代码与数据。
