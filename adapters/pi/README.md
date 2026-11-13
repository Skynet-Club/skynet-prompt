# Pi 产物（42 条）

由 `psup build` 从 `content/` 生成，不要手改。

## 安装

```sh
pi install git:github.com/<owner>/skynet-prompt@v1
```

或本地试用：

```sh
pi install /path/to/skynet-prompt
```

## 使用

输入 `；；` 打开抽屉，或输入 `/psup-` 过滤出全部条目，例如：

```text
/psup-kp-verify-18
```

正文是中文直译，逐字节来自 `content/items/<id>/zh.txt`。要英文原文：

```sh
psup print kp-verify-18 --field en
```

菜单描述里的 `本人原话 / 他人整理 / 未核实 / 节选` 是出处标记，不是正文。
