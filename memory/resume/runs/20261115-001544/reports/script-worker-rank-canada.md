# script-worker: rank after Canada filter (run 20261115-001544)

Status: DONE

- Rows before (jobs.all.jsonl): 405
- Rows after (jobs.jsonl): 99
- Rows removed: 306
  - Location not Canada: 305
  - Canada location but senior title: 1
- rank.py total: 99; top_k count: 15

## top_k

| # | id | title | company | location | pre_score | description chars |
|---|---|---|---|---|---|---|
| 1 | a41b73fc0e1d59c4 | AI Engineer – Applied AI, Data & LLM Systems | 247Labs | Toronto, Ontario | 81.5 | 0 |
| 2 | 655f07473920532e | AI Developer (LLM & Agentic Systems) | WSP in Canada | Vancouver, British Columbia, Canada | 81.2 | 0 |
| 3 | 58251ba27e0927ec | Embedded Software Designer - AI Agents and Tooling | Fidus Systems | Ottawa, Ontario, Canada | 73.8 | 0 |
| 4 | 8d69cb003c2c4c6c | AI Security Engineer, AWS Security - AISec | Amazon Web Services Canada, Inc. | Nova Scotia, CAN · Vancouver, British Columbia, CAN | 70.5 | 0 |
| 5 | 1dbaf124cb59d6fb | AI Data Developer II, Professional Services, Google Cloud | Google | Toronto, ON, Canada | 69.5 | 0 |
| 6 | 216491949b25fbcf | Cloud Engineer Automation | Smile Digital Health | Toronto, Ontario | 60.9 | 7546 |
| 7 | f997beef22b3a673 | AI Engineer, Trust & Evaluation | Equinix | Toronto, Ontario | 60.8 | 0 |
| 8 | 28701e456e5fd71c | Risk Data Scientist | Manulife | Waterloo, Ontario, Canada | 60.5 | 0 |
| 9 | 377d8f43870d21f8 | On-Device AI Engineer for In-Vehicle Infotainment | Ford | Ottawa, Ontario | 60.2 | 0 |
| 10 | 2496754c239e7126 | Data Scientist (Masters) | Alignerr | Edmonton, Alberta, Canada | 59.8 | 0 |
| 11 | 201f1af2bd730018 | Data Scientist | Government of Alberta | Edmonton, Alberta, Canada | 59.8 | 0 |
| 12 | b5729698d052fcba | AI Engineer, Innovation | MNP | Calgary, Alberta, Canada | 59.5 | 0 |
| 13 | 026c53ead66c93d5 | data scientist | Macropus IT Services | Victoria (BC) | 57.2 | 0 |
| 14 | 4821426bf3dadf81 | Software Developer III, AI/ML GenAI, Google Ads | Google | Mountain View, CA, USA; Waterloo, ON, Canada | 56.5 | 0 |
| 15 | 22b04aa3f2bbc5ee | Software Developer II, Early Career | Google | Waterloo, ON, Canada; Montreal, QC, Canada | 56.5 | 0 |

Top_k rows with empty description: 14

## Kept vs removed

- Kept: 99
- Removed: 306
- Removed for seniority word in title (Canada-located rows): 1

## Top 8 cities by count (kept rows, city = first location part)

| city | count |
|---|---|
| Toronto | 18 |
| Montreal | 15 |
| Vancouver | 7 |
| Ottawa | 7 |
| Calgary | 6 |
| Edmonton | 6 |
| Waterloo | 5 |
| Canada - Canada | 4 |
