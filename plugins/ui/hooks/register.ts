import { emptyBucket, addUsage, maxBucket, localDay, bandLine } from './format.ts'

// Token totals come from two sources, merged per session and day with the higher value of each count:
//  - history: scripts/history.py sums every session transcript in ~/.claude/projects (all time,
//    including sessions from before this plugin was installed). Re-run every 10 minutes.
//  - live: each model response this session (main loop and subagents), saved to $.store as
//    `u:<day>:<session>`, so the line moves at once and parallel sessions never overwrite each other.
// The line is pinned under the prompt with $.ui.status.

let sid = ''
let day = ''
let mine = emptyBucket()
let stored = {}
let history = {}
let sessionUsd = undefined
let contextPercent = undefined
let rateLimits = []
let showCost = true

// Loads this session's live bucket for today when the session or the day changes.
async function syncSession($) {
  const id = await $.session.id()
  const d = localDay(new Date())
  if (id === sid && d === day) return
  sid = id
  day = d
  mine = (await $.store.get(`u:${day}:${sid}`)) ?? emptyBucket()
}

// Reads the other sessions' live buckets from the store, keyed `<day>:<session>`.
async function loadStored($) {
  const out = {}
  for (const key of await $.store.keys()) {
    if (key.startsWith('u:')) out[key.slice(2)] = await $.store.get(key)
  }
  stored = out
}

// Runs the transcript scan. Keeps the last good result when the scan fails.
async function loadHistory($) {
  const r = await $.process.run(['python3', `${$.plugin.root}/scripts/history.py`], { timeoutMs: 60_000 })
  if (r.exitCode !== 0) return
  const out = {}
  const data = JSON.parse(r.stdout)
  for (const [session, days] of Object.entries(data)) {
    for (const [d, b] of Object.entries(days)) out[`${d}:${session}`] = { ...emptyBucket(), ...b }
  }
  history = out
}

// Pins the current line under the prompt.
async function show($) {
  await syncSession($)
  const merged = { ...stored, [`${day}:${sid}`]: mine }
  let today = emptyBucket()
  let all = emptyBucket()
  for (const key of new Set([...Object.keys(history), ...Object.keys(merged)])) {
    const b = maxBucket(history[key], merged[key])
    all = addUsage(all, b)
    if (key.startsWith(`${day}:`)) today = addUsage(today, b)
  }
  $.ui.status(bandLine({ now: new Date(), today, all, sessionUsd, contextPercent, rateLimits, showCost }))
}

async function refreshAll($) {
  await syncSession($)
  await loadStored($)
  await loadHistory($)
  await show($)
}

export function register(on, options) {
  showCost = options?.show_cost !== false

  on('session.start', async ($, e, next) => {
    // Do not hold up the session start: the scan runs in the background.
    refreshAll($)
    $.clock.every(30_000, () => show($))
    $.clock.every(600_000, () => refreshAll($))
    return next(e)
  })

  // Every model response, in the main loop and in subagents, adds its token counts.
  on('turn.step', async function* ($, e, next) {
    const r = yield* next(e)
    if (r?.usage) {
      await syncSession($)
      mine = addUsage(mine, {
        input: r.usage.input_tokens ?? 0,
        output: r.usage.output_tokens ?? 0,
        cacheRead: r.usage.cache_read_input_tokens ?? 0,
        cacheWrite: r.usage.cache_creation_input_tokens ?? 0,
      })
      await $.store.set(`u:${day}:${sid}`, mine)
      await show($)
    }
    return r
  })

  // After each turn: this session's cost, context use, rate limits.
  on('session.measure', async ($, e, next) => {
    sessionUsd = e.cost?.usd
    contextPercent = e.context?.percent
    rateLimits = e.rateLimits ?? []
    await show($)
    return next(e)
  })
}
