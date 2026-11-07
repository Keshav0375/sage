# Extract: Confluent topic configs + Basic pricing (fetched 2026-11-01)

## Q1/Q2 Confluent Cloud topic config reference: NOT FOUND
- https://docs.confluent.io/cloud/current/topics/topic-configs.html and .../topics/kafka-topic-configs-cc.html both returned only the docs landing page (no config table).
- Cloud clients page sidebar says "Configuration Reference" under Manage Topics, linking to https://docs.confluent.io/cloud/current/topics/manage.html (already read by caller).
- Q2 (compaction available for all cluster types): NOT FOUND.

## Fallback (Confluent PLATFORM, NOT Cloud; no Cloud editability/ranges): https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html  "Last updated: May 29, 2026"
- cleanup.policy: Default "delete"; Valid "[compact, delete]"; "This config designates the retention policy to use on log segments."
- retention.ms: Default "604800000 (7 days)"; Valid "[-1,…]"
- max.compaction.lag.ms: Default "9223372036854775807"; Valid "[1,…]"; "The maximum time a message will remain ineligible for compaction in the log."
- min.compaction.lag.ms: Default "0"; Valid "[0,…]"
- delete.retention.ms: Default "86400000 (1 day)"; Valid "[0,…]"
- segment.ms: Default "604800000 (7 days)"; Valid "[1,…]"

## Q3 Pricing
- https://docs.confluent.io/cloud/current/billing/overview.html (Last updated: Oct 29, 2026): no rates. "For current rates, see Confluent Cloud Pricing." (only first 100000 of 208648 chars read)
- https://www.confluent.io/confluent-cloud/pricing/ (no date shown), Basic tier (WebFetch summarized, not verbatim page text):
  - eCKU-hour: "First eCKU free, then $0.14"
  - Data In/Out (Ingress/Egress) ($/GB): "$0.05" each
  - Data Stored ($/GB-month): "$0.08"
