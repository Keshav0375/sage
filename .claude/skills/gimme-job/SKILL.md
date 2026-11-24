---
name: gimme-job
description: Keshav's default job hunt. Runs the full /gimme-job:run loop on the saved default filters (memory/resume/knobs.toml) plus the company-mix rule below. Use when Keshav types "/gimme-job" with no other words, or asks to "run gimme-job" with no preset.
argument-hint: "[--max-iterations N]"
---

# /gimme-job (default run)

Run the `gimme-job:run` skill with NO preset. Pass on any arguments Keshav gave.
The search filters are the user knobs in `memory/resume/knobs.toml`. Do not change them in this run.
Change them only when Keshav asks (`/gimme-job:knobs set ...` or an edit to that file, then update the table below).

## Saved default filters
| Filter | Value |
|---|---|
| Titles | AI Engineer, Forward Deployed Engineer, Software Developer II, ML Engineer, Data Scientist, LLM Engineer, AI Developer |
| Experience | 1 to 3 years (`years_experience = 2`, buckets 0-2 and 2-5, seniority entry + associate, Senior/Staff/Lead titles excluded) |
| Salary | $90,000+ CAD base (ranking weight; jobs with no salary shown stay in) |
| Location | All of Canada: Toronto, Vancouver, Montreal, Ottawa, Calgary, Waterloo, Edmonton, Mississauga, plus "Canada" and remote in Canada |
| Company size | 500+ employees, plus some startups (rule below) |

## Company-mix rule (no knob yet: give it to the agents)
Add this text to the prompt when you spawn `gimme-job:scout-lead` and `gimme-job:analyst-lead`:

> Company mix: prefer companies with more than 500 employees. Also keep some startups, so the job
> descriptions are not biased toward large companies. Use `company_size` from the extracted features,
> the JD text ("X employees", "Series A", "startup") or the company's known size.
> When you select the top N jobs: at least N-2 jobs from 500+ employee companies, and 1 to 2 jobs from
> startups (under 500 employees or Series A-D). A job whose size is unknown counts as neither; do not
> drop it only for that. Write the size you used for each selected job in the report.

When you show Card 3 Selected jobs, add one line: how many selected jobs are 500+, startup, and unknown size.
