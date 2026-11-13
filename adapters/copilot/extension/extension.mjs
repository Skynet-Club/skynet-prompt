import { joinSession } from "@github/copilot-sdk/extension"
import { rewriteTrigger } from "./rewrite.mjs"

const session = await joinSession({
  hooks: {
    onSessionStart: async () => {
      await session.log("skynet-prompt 已加载：输入 ；； 使用")
    },
    onUserPromptSubmitted: async (input) => {
      const modifiedPrompt = rewriteTrigger(input.prompt)
      if (modifiedPrompt) {
        await session.log("skynet-prompt 已识别 ；；", { ephemeral: true })
      }
      return modifiedPrompt ? { modifiedPrompt } : undefined
    },
  },
  tools: [],
})
