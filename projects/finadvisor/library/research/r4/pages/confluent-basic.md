# Extract: Confluent Cloud Basic cluster (r4)

Caveat: WebFetch returns a small-model digest of each page, not raw text. Quotes below are as relayed by that digest and were not checked against raw page HTML.
Each page is ~210-225k chars. Read chars 0-100000 and 100000-200000 per source (one continue each). The second chunk of each was nav only (no body). Last ~10-25k chars unread.

Sources and dates shown on page:
- cluster-types.html: "Last updated: Oct 30, 2026"
- broker-config.html: "Last updated: Oct 23, 2026"
- topics/overview.html: "Last updated: Oct 22, 2026"

## Q1 Basic cluster limits (cluster-types.html, Cluster limits)
- Sizing: Basic supports 1 to 50 eCKU (Cluster sizing > Minimum/maximum eCKU requirements).
- Cluster limit comparison: Ingress 250 MBps. Egress 750 MBps. Partitions (pre-replication) 1,500. Compactable partitions 1,500. Client connections 1,000. Connection attempts 250/s. Requests 5,000/s. Message size 8 MB. Request size 100 MB. Fetch bytes 55 MB. ACLs 1,000. API keys 50.
- Per-eCKU: ingress 5 MBps, egress 15 MBps, partitions 30, compactable partitions 30, connections 20, connection attempts 5/s, requests 100/s.
- Storage (Partition guidelines): Basic offers "5 TB per partition" and "5 TB per partition for compacted topics." Contrast: "Except for Basic clusters, all clusters offer:" "Unlimited storage per partition."
- SLA (Uptime service level agreement options): Basic listed at 99.5% only. "To obtain a higher uptime SLA, you can upgrade from Basic to a Standard cluster at any time using the Cloud Console."
- Connectors: "Basic clusters are limited to one task per connector." "You can deploy 250 connectors to a Basic cluster but each connector can only have one task."
- RBAC: "Basic clusters do not support RBAC roles for resources within the Kafka cluster."
- Max retention.ms: NOT FOUND on this page (only the 5 TB per-partition storage figure).

## Q2 cleanup.policy=compact and modifiable topic configs
- cleanup.policy=compact on Basic: NOT FOUND as an explicit statement. Indirect only: cluster-types lists "Compactable partitions: 1,500" and "5 TB per partition for compacted topics" for Basic.
- max.compaction.lag.ms, min.compaction.lag.ms, delete.retention.ms, segment.ms: NOT FOUND in the text read. broker-config.html only links to the topic configuration reference (manage.html), which was not fetched.
- broker-config.html (Considerations): "You cannot edit cluster settings on Basic, Standard, Enterprise, and Freight clusters in Confluent Cloud." and "Many configuration settings are available at the topic level instead."
- Dedicated-only table (broker-config): log.cleaner.max.compaction.lag.ms default 9223372036854775807, "Min: 21600000 ms"; log.retention.ms default 604800000, "Set to -1 for Infinite Storage". "These settings apply only to Dedicated clusters".
- topics/overview.html (Edit topics): "You can edit certain topic configurations after a topic has been created." "You can modify some parameters only after you create them." "You can't use Cloud Console to modify parameters with a lock symbol".
- retention.ms bounds: NOT FOUND.

## Q3 Infinite retention on Basic
- topics/overview.html (Create topics): "You can create a topic with Infinite Storage by specifying -1 for `retention.ms`." No cluster-type restriction stated in the text read.
- cluster-types: Basic storage is capped at 5 TB per partition, others unlimited. Whether -1 is permitted on Basic: NOT FOUND (the text read does not say).

## Q4 Pricing drivers
- cluster-types: Basic is elastic and billed in eCKUs. "For costs by dimension, see" the Billing Dimensions page. No per-GB or per-eCKU prices on the page: NOT FOUND.

## Gaps for the caller
- Topic configuration reference (https://docs.confluent.io/cloud/current/topics/manage.html or the configuration reference) is the likely source for Q2 and retention bounds.
- Billing Dimensions page is the likely source for Q4.
- Unread tails: cluster-types chars 200000-224681; broker-config 200000-208873; overview 200000-209734.
