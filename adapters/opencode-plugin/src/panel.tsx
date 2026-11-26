/** @jsxImportSource @opentui/solid */
import { For, Show, createMemo, createSignal, onMount } from "solid-js"
import { useKeyboard, useTerminalDimensions } from "@opentui/solid"
import type { BoxRenderable } from "@opentui/core"

export const PANEL_NAME = "skynet-prompt.picker"

// 军旅绿：深橄榄底、苔绿选中、浅橄榄字
const MIL = {
  bg: "#0c1109",
  panel: "#131a0f",
  border: "#3b4a2e",
  borderFocus: "#8fb35e",
  title: "#b2c98a",
  titleFocus: "#d7e8ae",
  titleMuted: "#77865f",
  text: "#c9d5b7",
  muted: "#839170",
  accent: "#a8c878",
  selectBg: "#4e6630",
  selectFg: "#f4f8e9",
  selectDimBg: "#2a351d",
  selectDimFg: "#b9c7a5",
  link: "#8fb39c",
} as const

const BOLD = 1 // TextAttributes.BOLD; 不在运行时导入 @opentui/core

export interface Category {
  key: string
  name: string
  en?: string
  count: number
}

export interface Item {
  id: string
  cat: string
  zh: string
  en?: string
  excerpt?: boolean
  author: string
  date: string
  url: string
}

export interface PickerState {
  categories: Category[]
  items: Item[]
}

export interface PanelLike {
  name: string
  sessionID: string
  width: number
  height?: number
  presentation: "panel" | "fullscreen"
  focused: boolean
  close: () => void
}

const CATEGORY_EN: Record<string, string> = {
  goal: "Goal",
  depth: "Depth",
  breadth: "Breadth",
  constraint: "Constraints",
  evidence: "Evidence",
  check: "Check",
  reader: "Reader",
  execution: "Execution",
  time: "Time",
}

function categoryLabel(row: Category, lang: "zh" | "en"): string {
  return lang === "en" ? row.en ?? CATEGORY_EN[row.key] ?? row.key.replace(/_/g, " ") : row.name
}

function cells(text: string): number {
  let width = 0
  for (const char of text) width += (char.codePointAt(0) ?? 0) > 0xff ? 2 : 1
  return width
}

function clip(text: string, width: number): string {
  const value = text.replace(/\s+/g, " ").trim()
  if (cells(value) <= width) return value
  let out = ""
  for (const char of value) {
    if (cells(out + char) > width - 1) break
    out += char
  }
  return out + "…"
}

function pad(text: string, width: number): string {
  return text + " ".repeat(Math.max(0, width - cells(text)))
}

function PickerPanel(props: {
  panel: PanelLike
  state: PickerState
  onClose: () => void
  onPick: (item: Item, text: string) => void
}) {
  const [catIndex, setCatIndex] = createSignal(0)
  const [itemIndex, setItemIndex] = createSignal(0)
  const [query, setQuery] = createSignal("")
  const [focus, setFocus] = createSignal<"cats" | "items">("cats")
  const [lang, setLang] = createSignal<"zh" | "en">("zh")
  const dimensions = useTerminalDimensions()
  const promptText = (item: Item) => lang() === "en" ? item.en || item.zh : item.zh

  const categoryName = (key: string) => {
    const row = props.state.categories.find((item) => item.key === key)
    if (!row) return key
    return `${row.name} ${CATEGORY_EN[row.key] ?? row.key.replace(/_/g, " ")}`.trim()
  }
  const selectedCategory = createMemo(() => props.state.categories[catIndex()])
  const rows = createMemo(() => {
    const q = query().trim().toLowerCase()
    const key = selectedCategory()?.key
    return props.state.items.filter((item) => {
      if (q) {
        const haystack = `${item.zh} ${item.en ?? ""} ${item.author} ${categoryName(item.cat)}`.toLowerCase()
        return haystack.includes(q)
      }
      return key === undefined || item.cat === key
    })
  })
  const current = createMemo(() => rows()[Math.min(itemIndex(), Math.max(rows().length - 1, 0))])
  const panelHeight = createMemo(() => props.panel.height && props.panel.height > 0
    ? props.panel.height
    : dimensions().height)
  const view = createMemo(() => {
    const max = Math.max(5, panelHeight() - 9)
    const start = Math.max(0, Math.min(
      itemIndex() - Math.floor(max / 2),
      Math.max(rows().length - max, 0),
    ))
    return { start, rows: rows().slice(start, start + max) }
  })
  const panelWidth = createMemo(() => props.panel.width > 0 ? props.panel.width : dimensions().width)
  const rowWidth = createMemo(() => Math.max(10, Math.floor((panelWidth() - 6) / 4) - 2))
  const t = (zh: string, en: string) => lang() === "en" ? en : zh
  const headerText = createMemo(() => {
    const base = lang() === "en"
      ? `Prompt picker · ${props.state.items.length} items / ${props.state.categories.length} scenes`
      : `提示词补充 · ${props.state.items.length} 条 / ${props.state.categories.length} 场景`
    if (!query()) return base
    return base + (lang() === "en" ? ` · Search "${query()}"` : ` · 搜索「${query()}」`)
  })
  const hintText = createMemo(() => lang() === "en"
    ? "↑↓ Select · ←→ Columns · Tab: 中/En · Type to search · Enter insert · Esc close"
    : "↑↓ 选择 · ←→ 切栏 · Tab： 中/En · 直接打字搜索 · Enter 补入 · Esc 关闭")
  const leftTitle = createMemo(() => {
    const base = t("场景", "Scenes")
    return focus() === "cats" ? `▸ ${base}` : base
  })
  const midTitle = createMemo(() => {
    if (query()) return `▸ ${t("搜索结果", "Results")}`
    const base = t("条目", "Items")
    return focus() === "items" ? `▸ ${base}` : base
  })
  const rightTitle = createMemo(() => {
    if (lang() === "zh") return current()?.excerpt ? "完整提示词 · 节选" : "完整提示词"
    return current()?.excerpt ? "Full prompt · excerpt" : "Full prompt"
  })

  useKeyboard((key) => {
    if (!props.panel.focused) return
    const handled = () => {
      key.preventDefault()
      key.stopPropagation()
    }
    const name = key.name
    if (name === "tab") {
      handled()
      setLang((value) => value === "zh" ? "en" : "zh")
      return
    }
    if (name === "escape") {
      handled()
      if (query()) {
        setQuery("")
        setItemIndex(0)
      } else {
        props.onClose()
      }
      return
    }
    if (name === "return") {
      handled()
      if (focus() === "cats") setFocus("items")
      else if (current()) props.onPick(current()!, promptText(current()!))
      return
    }
    if (name === "up" || name === "down") {
      handled()
      const delta = name === "up" ? -1 : 1
      if (focus() === "cats") {
        setCatIndex((value) => Math.min(Math.max(value + delta, 0), props.state.categories.length - 1))
        setItemIndex(0)
      } else {
        setItemIndex((value) => Math.min(Math.max(value + delta, 0), Math.max(rows().length - 1, 0)))
      }
      return
    }
    if (name === "left" && focus() === "items") {
      handled()
      setFocus("cats")
      return
    }
    if (name === "right" && focus() === "cats") {
      handled()
      setFocus("items")
      return
    }
    if (name === "backspace") {
      handled()
      setQuery((value) => value.slice(0, -1))
      setItemIndex(0)
      setFocus("items")
      return
    }
    if (key.ctrl || key.meta || key.option) return
    if (["up", "down", "left", "right", "return", "escape", "tab", "backspace",
      "delete", "home", "end", "pageup", "pagedown", "insert"].includes(name)) return
    const sequence = key.sequence
    if (sequence && sequence.length > 0 && sequence !== "\r" && sequence !== "\n" && sequence !== "\t") {
      handled()
      setQuery((value) => value + sequence)
      setItemIndex(0)
      setFocus("items")
    }
  })

  return (
    <box flexDirection="column" flexGrow={1} padding={1} backgroundColor={MIL.bg}>
      <text fg={MIL.accent}>{headerText()}</text>
      <text fg={MIL.muted}>{hintText()}</text>
      <box flexDirection="row" flexGrow={1} gap={1}>
        <box flexGrow={1} flexBasis={0} flexDirection="column" border borderStyle="single"
             title={leftTitle()} backgroundColor={MIL.panel}
             borderColor={focus() === "cats" ? MIL.borderFocus : MIL.border}
             titleColor={focus() === "cats" ? MIL.titleFocus : MIL.titleMuted}>
          <For each={props.state.categories}>
            {(row, index) => {
              const selected = () => index() === catIndex()
              const active = () => selected() && focus() === "cats"
              const label = () => {
                const raw = `${selected() ? "▸" : " "} ${categoryLabel(row, lang())}  ${row.count}`
                return selected() ? pad(raw, rowWidth()) : raw
              }
              return (
                <text
                  bg={active() ? MIL.selectBg : selected() ? MIL.selectDimBg : MIL.panel}
                  fg={active() ? MIL.selectFg : selected() ? MIL.selectDimFg : MIL.text}
                  attributes={active() ? BOLD : 0}
                >
                  {label()}
                </text>
              )
            }}
          </For>
        </box>
        <box flexGrow={1} flexBasis={0} flexDirection="column" border borderStyle="single"
             title={midTitle()} backgroundColor={MIL.panel}
             borderColor={focus() === "items" ? MIL.borderFocus : MIL.border}
             titleColor={focus() === "items" ? MIL.titleFocus : MIL.titleMuted}>
          <For each={view().rows}>
            {(item, index) => {
              const selected = () => view().start + index() === itemIndex()
              const active = () => selected() && focus() === "items"
              const label = () => {
                const raw = `${selected() ? "▸" : " "} ${clip(promptText(item), rowWidth() - 2)}`
                return selected() ? pad(raw, rowWidth()) : raw
              }
              return (
                <text
                  bg={active() ? MIL.selectBg : selected() ? MIL.selectDimBg : MIL.panel}
                  fg={active() ? MIL.selectFg : selected() ? MIL.selectDimFg : MIL.text}
                  attributes={active() ? BOLD : 0}
                >
                  {label()}
                </text>
              )
            }}
          </For>
        </box>
        <box flexGrow={2} flexBasis={0} flexDirection="column" border borderStyle="single"
             title={rightTitle()}
             backgroundColor={MIL.panel}
             borderColor={MIL.border} titleColor={MIL.title}>
          <Show when={current()}>
            {(item) => (
              <>
                <text wrapMode="word" fg={MIL.text}>{promptText(item())}</text>
                <text> </text>
                <text fg={MIL.muted}>{`${t("作者", "Author")}  ${item().author} · ${item().date}`}</text>
                <text wrapMode="word" fg={MIL.link}>{`${t("链接", "Link")}  ${item().url}`}</text>
              </>
            )}
          </Show>
        </box>
      </box>
    </box>
  )
}

export function renderPanel(props: {
  panel: PanelLike
  state: PickerState
  onClose: () => void
  onPick: (item: Item, text: string) => void
}) {
  return (
    <Show when={props.panel.name === PANEL_NAME}>
      <PickerPanel {...props} />
    </Show>
  )
}


export function PickerOverlay(props: {
  open: boolean
  state: PickerState | null
  onClose: () => void
  onPick: (item: Item, text: string) => void
}) {
  const dimensions = useTerminalDimensions()
  const width = () => Math.max(20, dimensions().width)
  const height = () => Math.max(12, Math.min(
    dimensions().height - 4,
    Math.floor(dimensions().height * 0.5),
  ))
  let box: BoxRenderable | undefined
  onMount(() => { box?.focus?.() })
  return (
    <Show when={props.open && props.state !== null}>
      <box ref={(el: BoxRenderable) => { box = el }} focusable
           position="absolute" top={2} left={0}
           width={width()} height={height()} zIndex={1000}
           backgroundColor={MIL.bg}>
        <PickerPanel
          panel={{
            name: PANEL_NAME,
            sessionID: "",
            width: width(),
            height: height(),
            presentation: "fullscreen",
            focused: true,
            close: props.onClose,
          }}
          state={props.state!}
          onClose={props.onClose}
          onPick={props.onPick}
        />
      </box>
    </Show>
  )
}

export function renderOverlay(props: {
  open: boolean
  state: PickerState | null
  onClose: () => void
  onPick: (item: Item, text: string) => void
}) {
  return <PickerOverlay {...props} />
}
