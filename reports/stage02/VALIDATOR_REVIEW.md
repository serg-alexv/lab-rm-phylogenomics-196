# Independent Stage2 cache-reader review

The repaired checker passed sequence integrity checks for the 79-package cache snapshot with zero errors. This is a review of already retrieved members of the approved196 cohort, not completion of full196 acquisition or Stage2 publication. No biological source file was changed. All 79 ZIP hashes matched between the original and repaired reader passes.

Final candidate: `validator_repaired.py`, SHA256 `345bcea7a0decf8a34b485eeb2260e1298c3ebf4ef508e8e654b239c45fc4e64`.

The biological parser was tested before the final TSV streaming change, at source SHA256 `6472ceb0055c9c549af7d3f3d10c6f20a55f62256b451c8223221508389d8122`. The final source changed full196 output streaming and corrected the historical catalog rationale. Its parser self-tests, synthetic packages, and output completion semantics were tested afterward. Full196 scientific validation remains the production runner's next gate.

## Executed checks and repairs

| Finding | Executed source evidence | Repair |
|---|---|---|
| CDS FASTA reading frame offset omitted by draft | All 214 draft CDS discrepancies exactly match GBFF extraction after `/codon_start - 1`; every `[frame]` agrees | Validate exact offset and preserve separate whole-feature and supplied-CDS hashes |
| Terminal partial codon discarded by draft | All 58 original partial translation differences have a source 3-prime partial endpoint and exactly match virtual-N ambiguity translation | Validate the terminal ambiguous codon without emitting or modifying a sequence |
| Unresolved terminal amino acid omitted by NCBI | 110 additional source partial CDSs have virtual terminal `X`; all complete codons exactly match the annotated protein | Permit only this unresolved terminal-X omission and record it explicitly; resolvable residue omissions fail |
| Internal GFF phase not checked | Synthetic valid two-part CDS passes; changing the internal phase now fails | Check phase in GBFF biological part order; retain explicit source exception records for documented translation/slippage cases |
| Conflicting CDS header tags silently collapsed | Synthetic duplicate conflicting locus tags now fail | Reject duplicate header keys |
| GBFF source TaxID unchecked | Synthetic incompatible source TaxID fails; preserved species/strain lineage case passes | Require exact reported TaxID or compatible species/descendant represented in the frozen lineage |

The same-base archival metadata exception retains raw historical records while exact catalog roles, sequence report assembly, GFF build, GBFF assembly DBLINK, and biological payload membership remain required. Synthetic archival biological files and unrelated accession bases fail. A metadata-only historical catalog reference passes with an explicit exception.

The original reader audited 79 packages in 112.97 seconds. The final biological reader pass audited the same 79 packages in 133.20 seconds. A Windows process snapshot during the latter pass reported peak working set 173,293,568 bytes and CPU 93.45 seconds; these are snapshot measurements, not claimed final process metrics. Python was 3.14.6 and Biopython 1.88.

## Output and malformed-input checks

All 16 parser self-tests passed. All 16 synthetic package expectations passed: six valid cases and ten rejected cases, including wrong internal/initial phase, unrelated metadata, archival biological version, wrong source TaxID, duplicate attributes, wrong frame, incorrect primary protein, missing 3-prime partial endpoint, and omission of a resolvable terminal residue.

The full196 CLI streams `locus_protein_map.tsv.tmp`, retains per-assembly JSON, and atomically renames the TSV after all approved assemblies are accounted for. An IO-only test reused prior validation JSON without rereading biological sources. It compared all 161,227 locus rows and all columns to those JSON records. Completed output was renamed atomically. An injected interruption left only `.tmp`, with no final TSV or completed summary. The 117 assemblies outside this IO test cache were reported as missing, so the IO test summary deliberately remained FAIL; its receipt is `PASS_IO_CONTRACT_ONLY`.

Evidence: `review_evidence.json`, `cds_exception_summary.json`, `omitted_partial_terminal_analysis.json`, `repaired_final/cached_review_summary.json`, `repaired_synthetic/synthetic_tests.json`, `final_selftest/negative_parser_tests.json`, and `streaming_io_test_receipt.json`.

Executed commands used the existing `.tools/validation_env/Scripts/python.exe` with `run_cached_review.py`, `analyze_cds_exceptions.py`, `run_repaired_review.py`, `synthetic_review.py validator_repaired.py`, `validator_repaired.py --self-test-only --output-dir .work/review2/final_selftest`, and `test_streaming_io.py`. Outputs stayed under `.work/review2/`.

The checks establish package/annotation joins and computational translation consistency with recorded source exceptions. They do not establish independent ANI/taxonomy, marker orthology, or R-M enzymatic function. NCBI describes phase, origin-spanning coordinates, and source exceptions in its [GFF3 documentation](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/file-formats/annotation-files/about-ncbi-gff3/); the reading frame qualifier is described in its [feature table guide](https://www.ncbi.nlm.nih.gov/genbank/feature_table/). The terminal handling above is backed by the actual retained package evidence and the stated malformed-input tests.
