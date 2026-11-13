# 剩余外部验证

## 1. 独立人工盲评

生成匿名评审包：

```sh
python3 scripts/export_eval_packet.py
```

评审者只看 `dist/evaluation-packets/<task>.md`，不得查看 `answer-key.json`。回收 winner 和 reason
后，用 answer key 解开 A/B，计算基线、增强和 tie。

完成条件：独立评审者完成 10 项，且结果与单模型裁判方向一致或给出可解释差异。

## 2. 团队连续 4 周

- 使用两个独立成员 key；
- `psup team` 配置私有 Registry；
- reviewer 和 publisher 分别签名；
- 连续 4 周记录 `psup events`、反馈、升级和至少一次回滚；
- 4 周后运行 `psup doctor` 和团队审计报告。

完成条件：真实团队连续 4 周留下可复核事件与反馈。

## 3. 第三方发布者

- 第三方生成自己的 Ed25519 key；
- 维护者执行 `psup trust-add`；
- 第三方发布符合 v2 Schema 的 Pack；
- 完成一次 Registry 发布、升级、撤销 key 和回滚。

完成条件：不是开发测试 key，而是独立发布者的真实包和审计记录。
