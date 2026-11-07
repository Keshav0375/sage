# Extract: PG temporal constraints + pgvector (PARTIAL, handed back early on request)

Fetched 2026-11-02. Only 1 of 4 sources was fetched before the early hand-back request.

## A) https://www.postgresql.org/docs/18/ddl-constraints.html
Version shown: "PostgreSQL 18.6 Documentation", "Supported Versions: Current (18)". No "last updated" line.
Note: the fetch tool summarised the page with a small model. It reported NO temporal constraint content on this page. Treat as "not seen in this fetch", not proof the page lacks it. Re-fetch sql-createtable.html to confirm.

- Q A1 (WITHOUT OVERLAPS / PERIOD syntax): NOT FOUND in this fetch
- Q A2 (btree_gist requirement for temporal): NOT FOUND in this fetch (page does not mention btree_gist)
- Q A3 (limitations, FOR PORTION OF): NOT FOUND in this fetch
- Exclusion constraints, 5.5.6: "Exclusion constraints ensure that if any two rows are compared on the specified columns or expressions using the specified operators, at least one of these operator comparisons will return false or null."
  Example: CREATE TABLE circles ( c circle, EXCLUDE USING gist (c WITH &&) );
  "Adding an exclusion constraint will automatically create an index of the type specified in the constraint declaration."
- Foreign keys, 5.5.5: "A foreign key must reference columns that either are a primary key or form a unique constraint, or are columns from a non-partial unique index."
- Check constraints, 5.5.1: "PostgreSQL does not support CHECK constraints that reference table data other than the new or updated row being checked."

## A2) https://www.postgresql.org/docs/18/sql-createtable.html : NOT FETCHED
## A3) https://www.postgresql.org/docs/16/rangetypes.html (exclusion example): NOT FETCHED

## B) https://raw.githubusercontent.com/pgvector/pgvector/master/README.md : NOT FETCHED
- Filtering section: NOT FOUND
- hnsw.iterative_scan strict_order/relaxed_order: NOT FOUND
- hnsw.max_scan_tuples, hnsw.scan_mem_multiplier: NOT FOUND
- ivfflat.iterative_scan: NOT FOUND
- partial index / partitioning advice: NOT FOUND
- 0.8.0 release, latest version: NOT FOUND
