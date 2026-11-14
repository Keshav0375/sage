---
name: knobs
description: Show or change gimme-job knobs (search filters, sources, waves, ranking, loop, budget, models) with provenance; switch presets.
argument-hint: "show | set KEY.PATH VALUE | get KEY.PATH | presets | brief [--preset NAME]"
---

# /gimme-job:knobs
Run `python3 plugins/gimme-job/scripts/knobs.py <args>` and show the output.
- `show` prints every knob, its value and where it came from (default / preset / user / flag).
- `set` writes `memory/resume/knobs.toml` and validates against `config/knobs.schema.json` first.
- Filters per source (exact API names) are listed in `projects/gimme-job/plan.md` section 6 and `projects/gimme-job/providers.md`.
