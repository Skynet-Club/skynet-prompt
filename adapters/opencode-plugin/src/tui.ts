import { Plugin } from "@opencode/plugin/tui"
import { execFileSync } from "node:child_process"
import { mkdirSync, appendFileSync, existsSync } from "node:fs"
import { homedir } from "node:os"
import { dirname, join } from "node:path"
import { createSignal, type Setter } from "solid-js"
import { createPicker } from "./picker.js"
import {
  PANEL_NAME, renderComposer, renderOverlay, renderPanel,
  type Category, type Item, type PickerState,
} from "./panel.tsx"

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
    const [state, setState] = createSignal<PickerState | null>(null)
    const [overlay, setOverlay] = createSignal(false)
    const [overlayMode, setOverlayMode] = createSignal<"home" | "session">("home")
    let disposeSlot: (() => void) | undefined
    let disposeApp: (() => void) | undefined
    let disposeComposer: (() => void) | undefined
    let appSlot = false
    let composerSlot = false

    let previousFocus: any
    const rememberFocus = () => {
      previousFocus = context.renderer?.currentFocusedRenderable
    }
    const restoreFocus = () => {
      try { previousFocus?.focus?.() } catch {}
      previousFocus = undefined
    }

    const finish = (item: Item, text: string, close?: () => void) => {
      close?.()
      setOverlay(false)
      setState(null)
      restoreFocus()
      setTimeout(() => {
        void appendToPrompt(context, text).then((ok) => {
          if (ok) {
            context.ui.toast.show({
              message: `已补 ${item.id}`,
              variant: "success",
              duration: 3000,
            })
          } else {
            void context.ui.dialog.alert({
              title: "无法追加到输入框",
              message: text,
            })
          }
        })
      }, 30)
    }

    if (context.ui?.slot) {
      try {
        disposeSlot = context.ui.slot({
          append: "session.panel",
          render: (panel: any) => {
            const data = state()
            if (!data) return null
            return renderPanel({
              panel,
              state: data,
              onClose: () => {
                panel.close?.()
                setState(null)
              },
              onPick: (item: Item, text: string) => finish(item, text, () => panel.close?.()),
            })
          },
        })
      } catch (error) {
        log(`slot failed ${String(error)}`)
      }
      try {
        disposeApp = context.ui.slot({
          append: "app",
          render: () => renderOverlay({
            open: overlay() && (overlayMode() === "home" || !composerSlot),
            state: state(),
            mode: overlayMode(),
            onClose: () => {
              setOverlay(false)
              setState(null)
              restoreFocus()
            },
            onPick: (item: Item, text: string) => finish(item, text),
          }),
        })
        appSlot = true
      } catch (error) {
        log(`app slot failed ${String(error)}`)
      }
      try {
        disposeComposer = context.ui.slot({
          append: "session.composer.top",
          render: () => renderComposer({
            open: overlay() && overlayMode() === "session",
            state: state(),
            onClose: () => {
              setOverlay(false)
              setState(null)
              restoreFocus()
            },
            onPick: (item: Item, text: string) => finish(item, text),
          }),
        })
        composerSlot = true
      } catch (error) {
        log(`composer slot failed ${String(error)}`)
      }
    } else {
      log("slot missing")
    }

    context.keymap.layer(() => ({
      mode: "global" as const,
      priority: 20,
      commands: [
        {
          id: "skynet.prompt.open",
          title: "skynet-prompt：选择提示词（Alt+P）",
          description: "在任意光标位置打开提示词选择器",
          group: "skynet-prompt",
          palette: true,
          bind: "alt+p",
          slash: { name: "p" },
          run: async () => {
            try {
              await runPanel(context, setState, setOverlay, setOverlayMode, appSlot, rememberFocus)
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
      message: "skynet-prompt 已加载：/p 或 Alt+P（任意光标）",
      variant: "success",
      duration: 3000,
    })
    return () => {
      try {
        disposeSlot?.()
      } catch {}
      try {
        disposeApp?.()
      } catch {}
      try {
        disposeComposer?.()
      } catch {}
    }
  },
})

async function runPanel(
  context: any,
  setState: Setter<PickerState | null>,
  setOverlay: Setter<boolean>,
  setOverlayMode: Setter<"home" | "session">,
  appSlot: boolean,
  rememberFocus: () => void,
): Promise<void> {
  try {
    const route = context.ui?.router?.current?.()
    setOverlayMode(route?.type === "session" ? "session" : "home")
    rememberFocus()
    const categories = psup<Category[]>("categories", "--json").filter((row) => row.count > 0)
    const items = psup<Item[]>("list", "--json")
    setState({ categories, items })
    if (appSlot) {
      setOverlay(true)
      log(`overlay open (${route?.type ?? "unknown"})`)
      return
    }
    const opened = context.ui?.panel?.open?.(PANEL_NAME, { presentation: "panel" })
    log(`panel open ${String(opened)}`)
    if (!opened) {
      setState(null)
      await runDialogPicker(context)
    }
  } catch (error) {
    log(`panel failed ${String(error)}`)
    if (appSlot) setOverlay(true)
    else {
      setState(null)
      await runDialogPicker(context)
    }
  }
}

async function runDialogPicker(context: any): Promise<void> {
  const openPicker = createPicker({
    psup: (command: string) => psup(command, "--json"),
    select: (options: any) => context.ui.dialog.select(options),
    append: (text: string) => appendToPrompt(context, text),
    alert: (options: any) => context.ui.dialog.alert(options),
    toast: (options: any) => context.ui.toast.show(options),
  })
  await openPicker()
}
