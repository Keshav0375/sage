# script-worker rank report, run 20261115-001544

## Command 1: rank.py
`python3 plugins/gimme-job/scripts/rank.py --run 20261115-001544`

Result: total 405 ranked, top_k 15.

## Features

No `features/` folder exists in the run. No CLI writes features. The `extract` package (`plugins/gimme-job/scripts/extract/`) has no `__main__` entry point. The `jobs.jsonl` rows have no `extract` field.

I computed the features in memory with `extract_all()` and `rules_confidence()` from the package, using each row `description` and the job row. I wrote no files.

`company_size` is null for all 15 jobs. The rule matches only explicit size text in the posting.

## Top 15 jobs

| # | id | title | company | location | pre_score | rules_confidence | company_size |
|---|----|-------|---------|----------|-----------|------------------|--------------|
| 1 | a41b73fc0e1d59c4 | AI Engineer – Applied AI, Data & LLM Systems | 247Labs | Toronto, Ontario | 81.5 | 0.222 | null |
| 2 | 655f07473920532e | AI Developer (LLM & Agentic Systems) | WSP in Canada | Vancouver, British Columbia, Canada | 81.2 | 0.222 | null |
| 3 | 809b3593cfdad7ca | Software Development Engineer, AWS Forward Deployed Engineering | Amazon Web Services Korea LLC | Seoul, KOR | 77.8 | 0.222 | null |
| 4 | 5c40ff22fc335f51 | Forward Deployed Engineer, AWS Forward Deployed Engineering | Amazon Web Services, Inc. | Herndon VA; Seattle WA; Arlington VA; New York NY; East Palo Alto CA (USA) | 77.5 | 0.222 | null |
| 5 | ec9649f7608336fd | Data Scientist II, AWS - Quick | ADCI MAA 15 SEZ | Chennai, Tamil Nadu, IND | 77.5 | 0.333 | null |
| 6 | 743999181d3a55b3 | Feltsense AI Engineer | Silver.dev | (blank) | 77.0 | 0.444 | null |
| 7 | b3b06b1141132d77 | Sr Forward Deployed Engineer, AWS Forward Deployed Engineering | Amazon Web Services, Inc. | Chicago, Illinois, USA | 76.8 | 0.333 | null |
| 8 | 0359587c2db3fc30 | Sr Forward Deployed Engineer (FDE), AWS Forward Deployed Engineering, US Government | Amazon Web Services, Inc. | Denver CO; Jessup MD; Arlington VA; Seattle WA; New York NY; Herndon VA (USA) | 75.2 | 0.333 | null |
| 9 | c0530e30daefee1c | Forward Deployed Engineer (FDE), AWS Forward Deployed Engineering, US Government | Amazon Web Services, Inc. | Arlington VA; Jessup MD; Seattle WA; Denver CO; Herndon VA (USA) | 74.8 | 0.222 | null |
| 10 | ab42406721374481 | Operations Expert with Python for AI Supply Chain Task Design | Toptal | Anywhere in the World | 74.5 | 0.556 | null |
| 11 | 58251ba27e0927ec | Embedded Software Designer - AI Agents and Tooling | Fidus Systems | Ottawa, Ontario, Canada | 73.8 | 0.222 | null |
| 12 | 78e9afd727a8d891 | Forward Deployed Engineer (Model Customization and Optimization), AWS Forward Deployed Engineering | AWS EMEA SARL (UK Branch) | London, England, GBR | 73.5 | 0.222 | null |
| 13 | bdea4ae67bc8be0c | Sr Forward Deployed Engineer, AWS Forward Deployed Engineering | AWS EMEA SARL (Germany Branch) | Berlin, Berlin, DEU | 72.8 | 0.333 | null |
| 14 | 7d3f1016d64c85d1 | Forward Deployed Engineer (Model Customization and Optimization), AWS Forward Deployed Engineering | Amazon Web Services, Inc. | Arlington VA; Boston MA; Seattle WA; New York NY; East Palo Alto CA (USA) | 72.2 | 0.222 | null |
| 15 | 8d69cb003c2c4c6c | AI Security Engineer, AWS Security - AISec | Amazon Web Services Canada, Inc. | Nova Scotia, CAN; Vancouver, British Columbia, CAN | 70.5 | 0.222 | null |

## Summary

- Total ranked: 405
- top_k count: 15
- Jobs with rules_confidence < 0.6: 15 of 15 (highest is 0.556, id ab42406721374481)
- company_size: null for all 15
- Features: computed in memory only, not saved to disk
