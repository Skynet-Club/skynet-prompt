import { Plugin } from "@opencode/plugin/tui"
import { execFileSync } from "node:child_process"
import { mkdirSync, appendFileSync, existsSync } from "node:fs"
import { homedir } from "node:os"
import { dirname, join } from "node:path"
import { createPicker } from "./picker.js"

const LOG = join(homedir(), ".local", "state", "skynet-prompt", "opencode-plugin.log")
const DEFAULT_BIN = join(homedir(), ".local", "bin", "psup")
const BIN = (globalThis as any).process?.env?.SKYNET_PROMPT_BIN
  ?? (existsSync(DEFAULT_BIN) ? DEFAULT_BIN : "psup")

function log(message: string) {
  try {
    mkdirSync(dirname(LOG), { recursive: true })
    appendFileSync(LOG, `${new Date().toISOString()} ${message}\n`)
  } catch {}
}

function psup<T>(...args: string[]): T {
  const output = execFileSync(BIN, args, {
    encoding: "utf8",
    maxBuffer: 4 * 1024 * 1024,
  })
  return JSON.parse(output) as T
}

function copyToClipboard(text: string): boolean {
  const attempts: Array<[string, string[]]> = [
    ["wl-copy", ["--paste-once"]],
    ["xclip", ["-selection", "clipboard", "-loops", "1"]],
    ["pbcopy", []],
  ]
  for (const [command, args] of attempts) {
    try {
      execFileSync(command, args, { input: text, stdio: ["pipe", "ignore", "ignore"] })
      return true
    } catch (error) {
      log(`clipboard ${command} failed: ${String(error)}`)
    }
  }
  return false
}

async function appendToPrompt(context: any, text: string): Promise<boolean> {
  if (!copyToClipboard(text)) return false
  try {
    await context.keymap?.dispatch?.("prompt.paste")
    log("append via clipboard + prompt.paste")
    return true
  } catch (error) {
    log(`prompt.paste failed: ${String(error)}`)
    return false
  }
}

export default Plugin.define({
  id: "skynet.prompt",
  setup(context: any) {
    log("setup")
    context.keymap.layer(() => ({
      mode: "global" as const,
      priority: 20,
      commands: [
        {
          id: "skynet.prompt.open",
          title: "skynet-prompt：选择提示词",
          group: "skynet-prompt",
          palette: true,
          slash: { name: "psup", aliases: ["prompts"] },
          run: async () => {
            try {
              await runPicker(context)
            } catch (error) {
              log(`picker failed: ${String(error)}`)
              context.ui.toast.show({
                title: "skynet-prompt",
                message: String(error),
                variant: "error",
                duration: 5000,
              })
            }
          },
        },
      ],
    }))
    context.ui.toast.show({
      message: "skynet-prompt 已加载：/prompts",
      variant: "success",
      duration: 3000,
    })
  },
})

async function runPicker(context: any): Promise<void> {
  const openPicker = createPicker({
    psup: (command: string) => psup(command, "--json"),
    select: (options: any) => context.ui.dialog.select(options),
    append: (text: string) => appendToPrompt(context, text),
    alert: (options: any) => context.ui.dialog.alert(options),
    toast: (options: any) => context.ui.toast.show(options),
    currentRoute: () => context.ui.router.current(),
  })
  await openPicker()
}
