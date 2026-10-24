# {{PROJECT}} — project rules

Loaded only when Claude works inside `projects/{{PROJECT}}/`. Keep it to what is *different* about
this project; the brain's ground rules already apply.

- **Binding docs:** `arch/` (read sections with `sagectl arch <doc> <§>`, never the whole file).
- **Decisions:** `arch/decisions.md` — why, and what superseded what.
- **Live state:** `STATE.md` (cheap, read whole) · tasks in `phases/TODO.md` (use `sagectl where`).
- **Lessons:** `sagectl lesson list -p {{PROJECT}}` before planning anything non-trivial.

<!-- Add project-only rules below. Each rule earns its place: if it was learned the hard way,
     link the lesson id (L007) that taught it. -->
