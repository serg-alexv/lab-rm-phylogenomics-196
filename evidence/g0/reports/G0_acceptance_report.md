# G0 acceptance axes — HUMAN approval NOT_GRANTED

| Axis | Status | Scope |
| --- | --- | --- |
| Historical artifact reconciliation | PASS_ARTIFACT_RECONCILIATION |177/150/130/47/20/197; all histories preserved |
| Actual exact-version assembly metadata | PASS_EXTERNAL_METADATA |197 current NCBI records; full receipts |
| Ranked taxonomy | PASS_TAXONOMY |197 genus/species lineage joins, independently resolved in NCBI Taxonomy |
| Dated outside-Enterococcus lineage | PASS_ENTEROCOCCUS_EXCLUSION |197; retrieval window2026-10-08, no sequence identification claim |
| Reported strict quality predicates |196 PASS_REPORTED_THRESHOLDS;1 UNRESOLVED_QUALITY |GCF_000056065.1 contamination missing |
| Proposed sampling |196 PROPOSED_FOR_INCLUSION |Inclusive union proposal; one UNRESOLVED hold |
| Human final-panel/sequence authorization |NOT_GRANTED / PENDING_HUMAN_APPROVAL |Only explicit subsequent HUMAN approval can advance |

The metadata gate is complete for a proposed retained panel, subject to the decisive artifact tests in `validation_results.json` and local archive tests in `package_receipt.json`. Any failure of those decisive tests makes the gate BLOCKED/INCOMPLETE until corrected. G0 metadata pass is not sequence validation, biological function or a globally optimal panel. Approval reserved vocabulary is documented in the work order and never assigned to any record. Parent-agent review is not human approval. Historical-query MAG/atypical/multi-isolate filters and inherited experimental literature rationales are not independently revalidated.

Minimum categories are mapped in `minimum_content_category_manifest.tsv`. Raw JSON/XML replace a separate taxonomy-only ZIP without loss; the full portable archive includes those native bytes. Local SHA/CRC validation is distinct from transfer. Transfer and receipt-side integrity are NOT_PERFORMED_BY_THIS_SESSION; parent performs them after final logs are complete. Stop here; no genome acquisition, marker/phylogeny/R-M/figure work is authorized.
