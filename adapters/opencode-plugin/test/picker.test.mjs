import assert from "node:assert/strict"
import test from "node:test"
import { createPicker } from "../src/picker.js"

const categories = [
  { key: "verify", name: "定验收", count: 1 },
]
const items = [
  { id: "fx-verify-15", cat: "verify", zh: "用外部裁判：不要让模型评判它自己。", author: "Felix" },
]

test("opens category, item and appends the exact zh text", async () => {
  const choices = ["verify", "fx-verify-15"]
  const selected = []
  const appended = []
  const toasts = []
  const openPicker = createPicker({
    psup: (command) => command === "categories" ? categories : items,
    select: async (options) => {
      selected.push(options.title)
      return choices.shift()
    },
    append: async (text) => {
      appended.push(text)
      return true
    },
    alert: async () => {},
    toast: (options) => toasts.push(options),
    currentRoute: () => ({ type: "session", sessionID: "ses_test" }),
  })

  await openPicker()
  assert.deepEqual(appended, [items[0].zh])
  assert.deepEqual(selected, [
    "skynet-prompt · 选择类目",
    "skynet-prompt · 定验收",
  ])
  assert.equal(toasts.at(-1).variant, "success")
})

test("shows fallback text when host append API is unavailable", async () => {
  const choices = ["verify", "fx-verify-15"]
  const alerts = []
  const openPicker = createPicker({
    psup: (command) => command === "categories" ? categories : items,
    select: async () => choices.shift(),
    append: async () => false,
    alert: async (options) => alerts.push(options),
    toast: () => {},
    currentRoute: () => ({ type: "session" }),
  })

  await openPicker()
  assert.equal(alerts.length, 1)
  assert.match(alerts[0].message, /用外部裁判/)
})

test("does not open outside a session", async () => {
  const toasts = []
  const openPicker = createPicker({
    psup: () => [],
    select: async () => undefined,
    append: async () => true,
    alert: async () => {},
    toast: (options) => toasts.push(options),
    currentRoute: () => ({ type: "home" }),
  })
  await openPicker()
  assert.equal(toasts[0].variant, "warning")
})
