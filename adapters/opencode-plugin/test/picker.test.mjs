import assert from "node:assert/strict"
import test from "node:test"
import { createPicker } from "../src/picker.js"

const categories = [
  { key: "check", name: "加检验", count: 1 },
]
const items = [
  { id: "fx-verify-15", cat: "check", zh: "用外部裁判：不要让模型评判它自己。", author: "Felix" },
]

test("opens scene, item and appends the exact zh text", async () => {
  const choices = ["check", "fx-verify-15"]
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
    "skynet-prompt · 选择场景",
    "skynet-prompt · 加检验",
  ])
  assert.equal(toasts.at(-1).variant, "success")
})

test("does not show evidence labels in the item list", async () => {
  const choices = ["check", "fx-verify-15"]
  const titles = []
  const openPicker = createPicker({
    psup: (command) => command === "categories" ? categories : items,
    select: async (options) => {
      if (options.title === "skynet-prompt · 加检验") {
        titles.push(...options.options.map((option) => option.title))
      }
      return choices.shift()
    },
    append: async () => true,
    alert: async () => {},
    toast: () => {},
  })

  await openPicker()
  assert.doesNotMatch(titles.join("\n"), /未核实|逐字可核|他人整理/)
})

test("shows fallback text when host append API is unavailable", async () => {
  const choices = ["check", "fx-verify-15"]
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

test("opens without a route argument", async () => {
  const choices = ["check", "fx-verify-15"]
  const appended = []
  const openPicker = createPicker({
    psup: (command) => command === "categories" ? categories : items,
    select: async () => choices.shift(),
    append: async (text) => {
      appended.push(text)
      return true
    },
    alert: async () => {},
    toast: () => {},
  })

  await openPicker()
  assert.deepEqual(appended, [items[0].zh])
})
