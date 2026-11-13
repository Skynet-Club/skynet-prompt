# Club 频道发布

目标频道：

```text
【A】全球优秀提示词（channel id 13）
契约：请遵从 Skyent-Prompt 格式标准
```

生成批次：

```sh
python3 scripts/export_club_posts.py \
  --release dist/release-2026-11-13 \
  --out dist/club-posts-13-v2026-11-13 \
  --channel 13
```

每条稿件包含：

- 提示词 ID；
- 作者与日期；
- `verbatim / paraphrase` 证据性质；
- 原始链接；
- 未声明许可与短引用边界；
- 英文短引用；
- 完整中文直译；
- Pack 版本与来源快照摘要。

发布必须通过 `skynet-club validate` 和 Gate。普通写入受每小时、每日和连续 bot 限额约束。
站长明确授权专用导入频道时，可用 `--owner-authorized-bulk`，该模式只调整单次进程内 Gate 的
节奏限制，仍执行长度、红线、重复、来源、nobots 和审计。

```sh
python3 scripts/publish_club_batch.py \
  --batch dist/club-posts-13/batch.json \
  --max-send 24 --wait-seconds 1 \
  --owner-authorized-bulk --send
```

2026-11-12/13 发布结果：

- 34/34 条全部落库；
- 消息 id `182–215`；
- 34 条都有来源与版权字段；
- 回读 `missing=[]`。

主题：

https://club.skynet.club/#narrow/channel/13-.E3.80.90A.E3.80.91.E5.85.A8.E7.90.83.E4.BC.98.E7.A7.80.E6.8F.90.E7.A4.BA.E8.AF.8D/topic/skynet-prompt.20v0.2E3.2E0.20.C2.B7.20.E5.AE.98.E6.96.B9.E6.8F.90.E7.A4.BA.E8.AF.8D/with/182
