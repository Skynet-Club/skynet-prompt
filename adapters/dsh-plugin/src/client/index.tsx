/**
 * DSH Web client half: a composer button, a `/p` command and a three-column
 * prompt picker rendered above the composer. Selection inserts at the current
 * cursor through InputActions.insertText.
 */
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore } from "react"
import { createPortal } from "react-dom"
// JSON is bundled into the client artifact; the picker never calls the Host.
import payload from "../../../../data/prompts.json"

type Lang = "zh" | "en"
type Focus = "cats" | "items"

interface Anchor {
  left: number
  width: number
  top: number
}

interface Prompt {
  id: string
  cat: string
  zh: string
  en: string
  excerpt?: boolean
  author: string
  date: string
  url: string
}

interface Category {
  key: string
  zh: string
  en: string
  count: number
}

const CATS = [
  { key: "goal", zh: "加目标", en: "Goal" },
  { key: "depth", zh: "加深度", en: "Depth" },
  { key: "breadth", zh: "加广度", en: "Breadth" },
  { key: "constraint", zh: "加约束", en: "Constraints" },
  { key: "evidence", zh: "加证据", en: "Evidence" },
  { key: "check", zh: "加检验", en: "Check" },
  { key: "reader", zh: "加读者", en: "Reader" },
  { key: "execution", zh: "加执行", en: "Execution" },
  { key: "time", zh: "加时间", en: "Time" },
] as const

const PROMPTS: Prompt[] = (payload as { items: Prompt[] }).items
const CATEGORIES: Category[] = CATS.map(row => ({
  ...row,
  count: PROMPTS.filter(item => item.cat === row.key).length,
}))

function promptText(item: Prompt, lang: Lang): string {
  return lang === "en" ? item.en || item.zh : item.zh
}

function text(lang: Lang, zh: string, en: string): string {
  return lang === "en" ? en : zh
}

class PickerController {
  private open = false
  private readonly listeners = new Set<() => void>()

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener)
    return () => { this.listeners.delete(listener) }
  }

  readonly getSnapshot = (): boolean => this.open

  show(): void {
    if (this.open) return
    this.open = true
    this.emit()
  }

  close(): void {
    if (!this.open) return
    this.open = false
    this.emit()
  }

  private emit(): void {
    for (const listener of [...this.listeners]) listener()
  }
}

const CSS = `
.skp-trigger {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; padding: 0; border: 0; border-radius: 8px;
  background: transparent; cursor: pointer;
}
.skp-trigger:hover { background: rgba(168, 200, 120, .12); }
.skp-trigger svg { display: block; width: 26px; height: 26px; }
.skp-window {
  --skp-bg: #0c1109; --skp-panel: #131a0f; --skp-border: #3b4a2e;
  --skp-focus: #8fb35e; --skp-title: #b2c98a; --skp-title-focus: #d7e8ae;
  --skp-text: #c9d5b7; --skp-muted: #839170; --skp-sel: #4e6630;
  --skp-sel-fg: #f4f8e9; --skp-sel-dim: #2a351d; --skp-sel-dim-fg: #b9c7a5;
  box-sizing: border-box;
  position: fixed; z-index: 2147483000; top: 6vh; left: 50%;
  transform: translateX(-50%); width: min(1120px, 94vw); height: min(42vh, 520px);
  display: grid; grid-template-rows: auto auto 1fr auto; overflow: hidden;
  background: var(--skp-bg); color: var(--skp-text);
  border: 1px solid var(--skp-border); border-radius: 10px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .55); outline: none;
  font: 14px/1.45 -apple-system, "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
}
.skp-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 14px 0; }
.skp-brand { color: var(--skp-title); font: 700 13px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; white-space: nowrap; }
.skp-count { color: var(--skp-muted); font-size: 12px; white-space: nowrap; }
.skp-hint { padding: 7px 14px 9px; color: var(--skp-muted); font-size: 12px; }
.skp-grid { display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 8px; min-height: 0; padding: 0 12px; }
.skp-col {
  min-width: 0; min-height: 0; display: flex; flex-direction: column;
  background: var(--skp-panel); border: 1px solid var(--skp-border); border-radius: 7px; overflow: hidden;
}
.skp-col.skp-col-focus { border-color: var(--skp-focus); }
.skp-colhead {
  flex: none; padding: 7px 10px; color: var(--skp-muted);
  border-bottom: 1px solid var(--skp-border); font-size: 12px; font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.skp-col.skp-col-focus .skp-colhead { color: var(--skp-title-focus); }
.skp-list { min-height: 0; overflow: auto; padding: 4px; }
.skp-row {
  display: flex; align-items: center; gap: 6px; width: 100%; box-sizing: border-box;
  padding: 5px 7px; border: 0; border-radius: 5px; background: transparent;
  color: var(--skp-text); text-align: left; font: inherit; font-size: 13px;
  white-space: nowrap; overflow: hidden; cursor: pointer;
}
.skp-row:hover { background: rgba(168, 200, 120, .07); }
.skp-row.skp-row-sel { background: var(--skp-sel-dim); color: var(--skp-sel-dim-fg); }
.skp-row.skp-row-active { background: var(--skp-sel); color: var(--skp-sel-fg); font-weight: 700; }
.skp-row-main { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.skp-row-count { flex: none; margin-left: auto; color: var(--skp-muted); font-size: 11px; }
.skp-row-active .skp-row-count { color: var(--skp-sel-fg); opacity: .8; }
.skp-detail { min-height: 0; overflow: auto; padding: 10px 12px 14px; }
.skp-prompt { color: var(--skp-text); white-space: pre-wrap; overflow-wrap: anywhere; font-size: 14px; line-height: 1.65; }
.skp-meta { margin-top: 10px; color: var(--skp-muted); font-size: 12px; line-height: 1.7; }
.skp-meta-label { display: inline-block; min-width: 68px; color: var(--skp-muted); }
.skp-link { color: #8fb39c; text-decoration: none; overflow-wrap: anywhere; }
.skp-link:hover { text-decoration: underline; }
.skp-empty { color: var(--skp-muted); padding: 12px; font-size: 13px; }
.skp-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 14px 10px; }
.skp-foot-hint { color: var(--skp-muted); font-size: 12px; }
.skp-insert {
  flex: none; border: 1px solid var(--skp-focus); border-radius: 6px;
  background: var(--skp-sel); color: var(--skp-sel-fg); padding: 6px 14px;
  font: 600 12px/1 inherit; cursor: pointer;
}
.skp-insert:disabled { opacity: .4; cursor: default; }
.skp-error { margin: 0 14px 8px; color: #c88370; font-size: 12px; }
@media (max-width: 760px) {
  .skp-window { top: 3vh; width: 96vw; height: 56vh; }
  .skp-grid { grid-template-columns: 1fr 1fr; }
  .skp-grid > .skp-col:last-child { grid-column: 1 / -1; max-height: 28vh; }
}
`

/** Inlined from assets/prompt.svg so the client bundle is self-contained. */
function PromptIcon() {
  return (
    <svg viewBox="0 0 140.113 140.113" aria-hidden="true" focusable="false">
      <path
        d="M37.592 0.5 L102.521 0.5 C123.007 0.5 139.613 17.107 139.613 37.592 L139.613 102.521 C139.613 123.007 123.007 139.613 102.521 139.613 L37.592 139.613 C17.107 139.613 0.5 123.007 0.5 102.521 L0.5 37.592 C0.5 17.107 17.107 0.5 37.592 0.5 Z"
        fill="#333333"
        stroke="#000000"
        strokeMiterlimit={10}
      />
      <path
        d="M45.398 35.387 L57.915 35.387 C60.937 35.387 63.387 37.836 63.387 40.858 L63.387 53.375 C63.387 56.397 60.937 58.846 57.915 58.846 L45.398 58.846 C42.377 58.846 39.927 56.397 39.927 53.375 L39.927 40.858 C39.927 37.836 42.377 35.387 45.398 35.387 Z M45.398 69.864 L57.915 69.864 C60.937 69.864 63.387 72.314 63.387 75.336 L63.387 82.396 C63.387 94.368 59.158 105.627 50.702 116.172 L39.927 116.172 C43.646 111.384 46.269 107.181 47.798 103.564 C49.071 100.609 49.937 97.196 50.396 93.324 L39.927 93.324 L39.927 75.336 C39.927 72.314 42.377 69.864 45.398 69.864 Z"
        fill="#d0ff2d"
      />
      <path
        d="M82.198 35.387 L94.715 35.387 C97.737 35.387 100.187 37.836 100.187 40.858 L100.187 53.375 C100.187 56.397 97.737 58.846 94.715 58.846 L82.198 58.846 C79.176 58.846 76.727 56.397 76.727 53.375 L76.727 40.858 C76.727 37.836 79.176 35.387 82.198 35.387 Z M82.198 69.864 L94.715 69.864 C97.737 69.864 100.187 72.314 100.187 75.336 L100.187 82.396 C100.187 94.368 95.958 105.627 87.501 116.172 L76.727 116.172 C80.446 111.384 83.069 107.181 84.598 103.564 C85.871 100.609 86.737 97.196 87.196 93.324 L76.727 93.324 L76.727 75.336 C76.727 72.314 79.176 69.864 82.198 69.864 Z"
        fill="#d0ff2d"
      />
    </svg>
  )
}

function PromptButton({ picker }: { picker: PickerController }) {
  return (
    <button
      type="button"
      className="skp-trigger"
      title="skynet-prompt：输入 ；； 打开提示词选择器"
      aria-label="skynet-prompt"
      onClick={() => picker.show()}
    >
      <PromptIcon />
    </button>
  )
}

function PickerOverlay(props: any) {
  const picker = props.picker as PickerController
  const open = useSyncExternalStore(picker.subscribe, picker.getSnapshot, picker.getSnapshot)
  const draft = props.useInput?.((state: any) => state.draft) ?? ""
  const draftRef = useRef(draft)
  draftRef.current = draft
  const inputActions = props.inputActions
  const probeRef = useRef<HTMLSpanElement>(null)
  const [anchor, setAnchor] = useState<Anchor | null>(null)

  const measureAnchor = useCallback((): void => {
    const card = probeRef.current?.closest("[data-composer-card]")
    if (!(card instanceof HTMLElement)) return
    const rect = card.getBoundingClientRect()
    setAnchor(prev => prev
      && prev.left === rect.left
      && prev.width === rect.width
      && prev.top === rect.top
      ? prev
      : { left: rect.left, width: rect.width, top: rect.top })
  }, [])

  useLayoutEffect(() => {
    measureAnchor()
    const card = probeRef.current?.closest("[data-composer-card]")
    const observer = card instanceof HTMLElement ? new ResizeObserver(measureAnchor) : null
    if (card instanceof HTMLElement) observer?.observe(card)
    window.addEventListener("resize", measureAnchor)
    window.addEventListener("scroll", measureAnchor, true)
    return () => {
      observer?.disconnect()
      window.removeEventListener("resize", measureAnchor)
      window.removeEventListener("scroll", measureAnchor, true)
    }
  }, [measureAnchor])

  useLayoutEffect(() => {
    if (open) measureAnchor()
  }, [open, measureAnchor])

  useEffect(() => {
    if (!open) return
    let frame = 0
    const tick = (): void => {
      measureAnchor()
      frame = window.requestAnimationFrame(tick)
    }
    tick()
    return () => window.cancelAnimationFrame(frame)
  }, [open, measureAnchor])

  useEffect(() => {
    if (!inputActions?.captureInsertion || !inputActions?.insertText) return
    let timer: number | undefined
    let disposed = false
    const check = (attempt: number): void => {
      if (disposed || picker.getSnapshot()) return
      const span = inputActions.captureInsertion()
      const before = String(draftRef.current ?? "").slice(0, span.start)
      const trigger = before.endsWith("；；") ? "；；" : before.endsWith(";;") ? ";;" : null
      if (trigger === null || span.start !== span.end) {
        if (attempt < 30) {
          timer = window.setTimeout(() => {
            timer = undefined
            check(attempt + 1)
          }, 20)
        }
        return
      }
      const removed = inputActions.insertText("", {
        start: span.start - trigger.length,
        end: span.start,
        draftRev: span.draftRev,
      })
      if (removed) picker.show()
    }
    const schedule = (): void => {
      if (timer !== undefined || picker.getSnapshot()) return
      timer = window.setTimeout(() => {
        timer = undefined
        check(0)
      }, 0)
    }
    const onInput = (event: Event): void => {
      const target = event.target
      if (!(target instanceof Element)) return
      if (!(target.closest("[data-composer-input], [contenteditable='true']") instanceof HTMLElement)) return
      schedule()
    }
    const onKeyUp = (event: KeyboardEvent): void => {
      if (event.key === ";" || event.key === "；" || event.key === "Process") schedule()
    }
    document.addEventListener("input", onInput, true)
    document.addEventListener("compositionend", onInput, true)
    document.addEventListener("keyup", onKeyUp, true)
    return () => {
      disposed = true
      if (timer !== undefined) window.clearTimeout(timer)
      document.removeEventListener("input", onInput, true)
      document.removeEventListener("compositionend", onInput, true)
      document.removeEventListener("keyup", onKeyUp, true)
    }
  }, [inputActions, picker])

  return (
    <>
      <span ref={probeRef} hidden />
      {open ? createPortal(<Picker picker={picker} anchor={anchor} inputActions={inputActions} />, document.body) : null}
    </>
  )
}

function Picker({ picker, anchor, inputActions }: {
  picker: PickerController
  anchor: Anchor | null
  inputActions?: { captureInsertion: () => unknown; insertText: (text: string, span: unknown) => boolean }
}) {
  const [lang, setLang] = useState<Lang>("zh")
  const [focus, setFocus] = useState<Focus>("cats")
  const [catIndex, setCatIndex] = useState(0)
  const [itemIndex, setItemIndex] = useState(0)
  const [error, setError] = useState("")
  const windowRef = useRef<HTMLDivElement>(null)

  const category = CATEGORIES[catIndex] ?? CATEGORIES[0]!
  const rows = useMemo(() => PROMPTS.filter(item => item.cat === category.key), [category.key])
  const current = rows[Math.min(itemIndex, Math.max(rows.length - 1, 0))]
  const t = useCallback((zh: string, en: string) => text(lang, zh, en), [lang])

  useEffect(() => {
    const timer = window.setTimeout(() => windowRef.current?.focus(), 0)
    return () => window.clearTimeout(timer)
  }, [])

  useEffect(() => {
    const onPointerDown = (event: PointerEvent): void => {
      if (windowRef.current?.contains(event.target as Node)) return
      picker.close()
    }
    document.addEventListener("pointerdown", onPointerDown, true)
    return () => document.removeEventListener("pointerdown", onPointerDown, true)
  }, [picker])

  useEffect(() => {
    if (focus !== "items") return
    const selected = windowRef.current?.querySelector('[data-skp-item-selected="true"]')
    if (selected) (selected as HTMLElement).scrollIntoView({ block: "nearest" })
  }, [focus, itemIndex, rows])

  const setCategory = (index: number): void => {
    setCatIndex(index)
    setItemIndex(0)
    setFocus("cats")
  }

  const selectItem = (index: number): void => {
    setItemIndex(index)
    setFocus("items")
  }

  const insert = (item: Prompt | undefined): void => {
    if (!item) return
    if (!inputActions || typeof inputActions.insertText !== "function") {
      setError(t("当前输入框不可写。", "The composer is not writable."))
      return
    }
    const value = promptText(item, lang)
    try {
      const span = inputActions.captureInsertion()
      if (!inputActions.insertText(value, span)) {
        setError(t("输入框内容已变化，请重试。", "The draft changed; try again."))
        return
      }
      picker.close()
    } catch {
      setError(t("插入失败，请重试。", "Insert failed; try again."))
    }
  }

  const onKeyDown = (event: React.KeyboardEvent): void => {
    if (event.key === "Tab") {
      event.preventDefault()
      setLang(value => value === "zh" ? "en" : "zh")
      return
    }
    if (event.key === "Escape") {
      event.preventDefault()
      picker.close()
      return
    }
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault()
      const delta = event.key === "ArrowUp" ? -1 : 1
      if (focus === "cats") {
        const next = Math.min(Math.max(catIndex + delta, 0), CATEGORIES.length - 1)
        setCategory(next)
      } else {
        setFocus("items")
        setItemIndex(Math.min(Math.max(itemIndex + delta, 0), Math.max(rows.length - 1, 0)))
      }
      return
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault()
      setFocus("cats")
      return
    }
    if (event.key === "ArrowRight") {
      event.preventDefault()
      setFocus("items")
      return
    }
    if (event.key === "Enter") {
      event.preventDefault()
      if (focus === "cats") setFocus("items")
      else insert(current)
    }
  }

  const rightTitle = lang === "zh"
    ? (current?.excerpt ? "完整提示词 · 节选" : "完整提示词")
    : (current?.excerpt ? "Full prompt · excerpt" : "Full prompt")

  const anchorStyle = useMemo(() => {
    if (!anchor) return undefined
    const viewport = window.innerHeight
    const gap = 8
    const height = Math.max(160, Math.min(
      520,
      Math.round(viewport * 0.42),
      Math.round(anchor.top - gap - 8),
    ))
    return {
      left: `${anchor.left}px`,
      width: `${anchor.width}px`,
      height: `${height}px`,
      bottom: `${Math.max(8, viewport - anchor.top + gap)}px`,
      top: "auto",
      transform: "none",
    }
  }, [anchor])

  return (
    <div className="skp-window" ref={windowRef} style={anchorStyle} role="dialog" aria-modal="false"
      tabIndex={-1}
      aria-label={t("skynet-prompt 提示词选择器", "skynet-prompt picker")}
      onKeyDown={onKeyDown}>
      <div className="skp-top">
        <div className="skp-brand">skynet-prompt</div>
        <div className="skp-count">
          {lang === "zh" ? `${PROMPTS.length} 条 / ${CATEGORIES.length} 场景` : `${PROMPTS.length} items / ${CATEGORIES.length} scenes`}
        </div>
      </div>
      <div className="skp-hint">
        {t(
          "↑↓ 选择 · ←→ 切栏 · Tab 中/En · Enter 补入 · Esc 关闭",
          "↑↓ Select · ←→ Columns · Tab 中/En · Enter insert · Esc close",
        )}
      </div>
      <div className="skp-grid">
        <section className={`skp-col${focus === "cats" ? " skp-col-focus" : ""}`}>
          <div className="skp-colhead">{focus === "cats" ? "▸ " : ""}{t("场景", "Scenes")}</div>
          <div className="skp-list">
            {CATEGORIES.map((row, index) => (
              <button
                key={row.key}
                type="button"
                className={`skp-row${index === catIndex ? (focus === "cats" ? " skp-row-active" : " skp-row-sel") : ""}`}
                onClick={() => setCategory(index)}
              >
                <span className="skp-row-main">{row[lang]}</span>
                <span className="skp-row-count">{row.count}</span>
              </button>
            ))}
          </div>
        </section>
        <section className={`skp-col${focus === "items" ? " skp-col-focus" : ""}`}>
          <div className="skp-colhead">
            {focus === "items" ? "▸ " : ""}
            {t("条目", "Items")}
          </div>
          <div className="skp-list">
            {rows.length === 0 && <div className="skp-empty">{t("这个场景还没有提示词", "No prompts in this scene")}</div>}
            {rows.map((item, index) => (
              <button
                key={item.id}
                type="button"
                data-skp-item-selected={index === itemIndex ? "true" : undefined}
                className={`skp-row${index === itemIndex ? (focus === "items" ? " skp-row-active" : " skp-row-sel") : ""}`}
                onClick={() => selectItem(index)}
                onDoubleClick={() => insert(item)}
              >
                <span className="skp-row-main">{promptText(item, lang)}</span>
              </button>
            ))}
          </div>
        </section>
        <section className="skp-col">
          <div className="skp-colhead">{rightTitle}</div>
          <div className="skp-detail">
            {current ? (
              <>
                <div className="skp-prompt">{promptText(current, lang)}</div>
                <div className="skp-meta">
                  <div><span className="skp-meta-label">{t("作者", "Author")}</span>{current.author} · {current.date}</div>
                  <div><span className="skp-meta-label">{t("来源", "Source")}</span><a className="skp-link" href={current.url} target="_blank" rel="noreferrer">{current.url}</a></div>
                </div>
              </>
            ) : <div className="skp-empty">{t("请选择一条提示词", "Select a prompt")}</div>}
          </div>
        </section>
      </div>
      {error && <div className="skp-error" role="alert">{error}</div>}
      <div className="skp-foot">
        <span className="skp-foot-hint">
          {t("双击条目可直接补入", "Double-click an item to insert")}
        </span>
        <button type="button" className="skp-insert" disabled={!current} onClick={() => insert(current)}>
          {t("插入", "Insert")}
        </button>
      </div>
    </div>
  )
}

/** Client plugin entry: service injection, slots, command and styles. */
export const inject = ["slots", "commandUi"]

export function apply(ctx: any): void {
  const controllers = new Map<string, PickerController>()
  const pickerFor = (sessionId: string): PickerController => {
    let controller = controllers.get(sessionId)
    if (!controller) {
      controller = new PickerController()
      controllers.set(sessionId, controller)
    }
    return controller
  }

  if (typeof document !== "undefined") {
    const style = document.createElement("style")
    style.dataset.skynetPrompt = "picker"
    style.textContent = CSS
    document.head.appendChild(style)
    ctx.effect(() => () => { style.remove() }, "dsh-skynet-prompt: styles")
  }

  ctx.inject(["slots"], (scope: any) => {
    scope.slots.inject("conversation.input.overlay", () => scope.slots.register({
      name: "conversation.input.overlay",
      id: "skynet-prompt-picker",
      order: 20,
      inject: (sessionId: string) => ({ picker: pickerFor(sessionId) }),
    }, PickerOverlay))

    scope.slots.inject("conversation.input.left", () => scope.slots.register({
      name: "conversation.input.left",
      id: "skynet-prompt-button",
      order: 40,
      label: () => "Prompt",
      inject: (sessionId: string) => ({ picker: pickerFor(sessionId) }),
    }, PromptButton))
  })

  ctx.inject(["commandUi"], (scope: any) => {
    scope.effect(() => scope.commandUi.register({
      name: "p",
      label: () => "skynet-prompt",
      description: () => "选择提示词并插入到光标处 / Insert a prompt at the cursor",
      available: () => true,
      ui: {
        kind: "action",
        run: (session: { sessionId: string }) => { pickerFor(session.sessionId).show() },
      },
    }), "dsh-skynet-prompt: /p")
  })
}
