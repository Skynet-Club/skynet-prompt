# 团队私有源与角色

团队配置示例见 `team.example.json`。默认读取：

```text
~/.config/skynet-prompt/team.json
```

也可通过 `SKYNET_PROMPT_TEAM_CONFIG` 或 `--config` 指定。

```sh
psup team --config team.example.json --user 0@skynet-club --action publish
psup team-update --config team.json --registry-id team --pack official
```

角色：

- `author`：提交候选；
- `reviewer`：审核；
- `publisher`：发布；
- `admin`：全部权限；
- `reader`：只读。

Registry 各自声明 source、channel、trust 和 priority。`team-update` 按名字选择指定源，
不会让团队包覆盖官方包。这里的成员字符串只是本地授权配置，不会被当成已认证身份；真正发布
仍依赖签名 Pack 和审核账本。
