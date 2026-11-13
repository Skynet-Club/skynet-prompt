const TRIGGER = /^\s*[；;]{2}([\s\S]*)$/u

export function rewriteTrigger(prompt) {
  if (typeof prompt !== "string" || prompt.trimStart().startsWith("；；；")) {
    return null
  }
  const match = prompt.match(TRIGGER)
  if (!match) return null
  const query = match[1].trim()
  return [
    "[skynet-prompt 已触发]",
    `用户使用了统一触发器，查询内容：${query || "（空）"}`,
    "请使用 skynet-prompt 个人 Skill 和已连接的 skynet-prompt MCP。",
    query
      ? "先调用 prompt_search；如果查询是条目 id，调用 prompt_get。"
      : "运行 psup categories --json，只列 9 个类目和条数。",
    "返回候选时展示 id、类目、作者、来源和可信状态；正文必须原样，不要改写。",
    "不要发送消息，不要修改仓库，不要读取凭据。",
  ].join("\n")
}
