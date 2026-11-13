import assert from "node:assert/strict"
import test from "node:test"

import { rewriteTrigger } from "../rewrite.mjs"

test("full-width trigger is rewritten", () => {
  const text = rewriteTrigger("；；定验收")
  assert.match(text, /skynet-prompt/)
  assert.match(text, /定验收/)
  assert.match(text, /prompt_search/)
})

test("empty trigger asks for categories", () => {
  const text = rewriteTrigger("；；")
  assert.match(text, /psup categories --json/)
})

test("literal escape and ordinary text are untouched", () => {
  assert.equal(rewriteTrigger("；；；"), null)
  assert.equal(rewriteTrigger("普通消息"), null)
})
