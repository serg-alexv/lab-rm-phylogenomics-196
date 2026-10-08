# Read-only review of the production Stage 2 validator

WD review date: 2026-10-08; final artifact check completed 13:03:53 UTC. Source and completed-output inspection; no biological search, new genome validation, installation, process interruption, or mutable Desktop Commander checkpoint read. Parser self-tests were executed in memory under the existing validation environment. After the active validator and wrapper exited, the parent explicitly authorized one bounded wrapper argument correction, preservation of its original bytes, and isolated synthetic tests; those actions are recorded below. The scientific validator was unchanged.

## Conclusion

The executed production candidate retains the substantive source-TaxID, cumulative multipart-phase, CDS-frame and partial-translation repairs. `scripts/validate_sequences.py` is byte-identical to `.work/review2/validator_repaired.py`, SHA256 `345bcea7a0decf8a34b485eeb2260e1298c3ebf4ef508e8e654b239c45fc4e64`.

The final independent artifact check passed: all 196 completed per-assembly records and final aggregate tables account for the exact approved panel, zero errors, 411,514 unique locus keys, 2,120 assembly sequence records, 1,960 source members and 16,155 explicit review exceptions. The sequence records may include scaffolds/contigs; this count is not 2,120 biologically proven replicons. Chromosome/plasmid/topology identity requires the retained source fields. Each per-assembly record reports `PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS` and binds the expected source/panel/taxonomy hashes. The completed scientific summary ended 13:01:05 UTC after 265.802 seconds. The original child command independently records exit 0 and 266.364 elapsed seconds. This establishes completed sequence/annotation integrity with preserved exceptions; GitHub publication was not checked by this reviewer.

The inspected wrapper had a concrete orchestration defect: `validate_stage02_locked.py` passed `check=False` to `production_resume.run`; that helper returns only stdout, discarding the return code from its caller's perspective. A validator exit 1 could therefore still leave the wrapper exiting0. The current successful run is supported by the actual child exit and scientific artifacts, not its wrapper exit. After verifying the original processes had exited and the wrapper had not changed, the authorized one-argument fix to `check=True` was applied and tested. No active source was modified.

## Final output verification

Read all 196 completed per-assembly JSONs sequentially and independently parsed the six final TSVs. Verified exact accession membership, zero per-assembly errors, retained exception count/category sums, expected hashes, and unique locus keys equal to assembly + genomic sequence accession + locus. The producer labels that sequence-key field `replicon`; the 2,120-row table includes assembly sequence records and must not be interpreted as a count of complete biological replicons. Summary counts equal the per-assembly totals and TSV row counts; `errors.tsv` is header-only.

| Final artifact under .work/stage02_validated | Data rows | SHA256 |
|---|---:|---|
| assembly_qc.tsv | 196 | aaf510067a229f8c4f4444345506dc1c65169dcce7a77f6d574840b301d4b99e |
| errors.tsv | 0 | 3f6962bd8c745e44f91a8d1a6b1524779a327bce2426cd5f4c2a80fdfb927df2 |
| review_exceptions.tsv | 16155 | bfaaf33d1af5ce87ffae96360ad707f4b75814fdf2eedd0536fe29e5b12fc6b4 |
| replicon_qc.tsv | 2120 | e46d7ea029f792239578f15a43861b2a558b3df91f493bfb2f0da94aa1d1af3d |
| member_sha256.tsv | 1960 | b1dca123e6d0e04a54ff7567e1a14804ace21faacb4fa52a78e9a827697a8b9f |
| locus_protein_map.tsv | 411514 | 0bca7835e3fe0b3e91a5a4c17596111b7f274126c9976418da7af0e1917530cb |

Exception totals retained: 13,586 DOCUMENTED_ANNOTATION_EXCEPTION; 609 GFF_INTERNAL_PHASE_DOCUMENTED_EXCEPTION; 4 ARCHIVAL_METADATA_CATALOG_REFERENCE; 4 ARCHIVAL_ASSEMBLY_METADATA_REPORT; 1,011 SOURCE_PARTIAL_OR_FUZZY_CDS; 535 SOURCE_CDS_CODON_START_OFFSET; 282 PARTIAL_TERMINAL_UNKNOWN_OMITTED; 115 PARTIAL_TERMINAL_CODON_AMBIGUITY_VALIDATION; 9 PSEUDOGENE_GENE_WITHOUT_CDS. These are exception records, not necessarily distinct genes or defects. Their presence is not an independent claim of activity or sequence quality certification beyond the documented scope.

At 13:06:16 UTC, independently compared all 1,960 extracted portable package files against their validated raw-ZIP member byte lengths and SHA256 values: 2,460,621,325 bytes matched. This binds the extracted handoff files to the independently validated raw members; no biological parser was rerun.

## Source and input checks

| Check | Evidence and finding |
|---|---|
| Exact approved panel | Validator lines 645-652 require 196 unique versioned GCF IDs, exact list SHA against approval.json, approved count 196 and no pilot. Actual approval is APPROVED_FOR_SEQUENCE_ANALYSIS. |
| Approval/list provenance | Approval SHA `9e231457d39cd959942f38930a1f2b72cc391cabc86d0839a8adf8f5b6c94bdc`; panel SHA `85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6`. Both independently match Stage1 SHA256SUMS. |
| Frozen taxonomy ledger | Lines 653-658 require 197 unambiguous historical candidates and membership of each approved accession. Actual ledger SHA `b2305b0e2766b097545ca727f12a01a81fcbe16076903c188a971dfe5243bde5` matches Stage1 SHA256SUMS. All196 selected lineages contain exactly one species-rank node. The code records this ledger hash but does not itself compare it to the Stage1 expected hash; the external check here supplies that missing provenance assertion for the inspected run inputs. |
| Exact package roles/version | Lines 166-264 require exact requested catalog/report assembly, same-base-only archival metadata exceptions, exactly six nonempty distinct roles, no unapproved biological-version payload, CRC, provider MD5 when supplied, and SHA256 for every member. CDS role is explicitly separated from genomic FASTA. |
| Source sequence joins | Lines 286-341 require exact assembly/replicon sequence-report joins and lengths, GBFF/genomic sequence equality, Assembly DBLINK and exact GFF build. No assumed latest-version substitution. |
| Locus/protein joins | Lines 342-493 use assembly + replicon + locus keys, reject ambiguous CDS/GBFF locus entries, compare GFF/GBFF membership/coordinates/protein IDs, CDS source extraction and primary protein/GBFF translation. Repeated identical WP accessions are preserved as an explicit exception rather than used as unique locus keys. |
| Source/code binding | Each package result retains raw ZIP/member hashes, validator source path/hash and version evidence. Completed results additionally retain approved-list and frozen-ledger hashes. These actual recorded hashes match this review. Hashes are computed from files during execution; future workflow hardening should freeze/check start/end source and input hashes against the launch receipt rather than permitting unobserved mid-run edits. No such edit was observed here. |

The 196-ID hash is the authority for biological membership; the 197-row ledger is explicitly filtered by accession. The excluded held assembly and Enterococcus are not silently reintroduced by reading the historical ledger. This validates frozen metadata identity/provenance; it is not independent ANI/taxonomic sequence certification.

## Semantic repairs confirmed in the actual production path

- **Taxonomy:** lines 271-285 compare the downloaded organism TaxID to the frozen ID or species/descendant IDs actually present in the preserved lineage. Lines 313-327 require exactly one numeric GBFF source taxon cross-reference and reject an unrelated source ID; compatible differences become explicit exceptions. No taxon ancestry is invented. An ambiguous multiple-species lineage is not explicitly rejected by this derivative, but the actual selected196 ledger has exactly one species node each.
- **Multipart phase:** lines 445-463 calculate `(codon_start - 1 - preceding biological part length) % 3`. First-part phase is checked even with translation exceptions; later parts are checked unless explicit translation/slippage qualifiers route them to a retained exception. GFF and GBFF coordinate multisets must already agree. The derivative does not include every extra ambiguity guard of the parent's alternative helper; this is not a reason to replace it and lose the external partial-CDS fixes.
- **CDS frame:** lines 468-478 compare CDS FASTA `[frame]` to GBFF `/codon_start` and require exact supplied CDS equality after that source offset. Whole-feature and supplied-CDS hashes remain separate; source bytes are not rewritten.
- **Partial translation:** lines 506-554 distinguish biological endpoints, allow virtual terminal ambiguity bases only for a documented 3-prime partial endpoint, require exact complete-codon agreement, and narrowly permit an omitted unresolved terminal X. Unexplained partial mismatches and exceptions fail. Virtual bases are validation-only, never emitted as recovered source sequence.
- **Exceptions:** pseudo/translation/slippage cases keep exact source joins and qualifiers, but naive translation is deliberately not asserted. Their label is integrity with documented exceptions, not universal translation PASS. Partial/fuzzy CDS, source offsets, omitted terminal ambiguity, historical metadata and pseudogenes without CDS remain reviewable. Downstream marker/R-M users must retain relevant locus flags and avoid inferring functional completeness from the Stage2 label.

Read `.work/parent_review_adoption.md` and the published candidate review evidence. Its cached79 results are historical, not substitutes for the current full 196 execution. Current production source equals the final streaming candidate rather than the earlier biological-parser hash. The cached review records16 synthetic package expectations (six positive, ten rejected); this review read those receipts rather than rerunning package fixtures. Separately, the production source's16 parser self-tests were executed here in memory and passed (15 rejected malformed cases, one combined positive case).

## Lock and completion behavior

The wrapper acquires the one-byte nonblocking Windows `.work/workflow.lock` before source workflow actions, waits at most20 attempts, and releases in `finally`. It holds the lock while the scientific child runs. This is materially useful duplicate protection for launches using that wrapper; `validate_sequences.py` itself has no lock and must not be launched directly in parallel. No duplicate process was started in this review.

The validator streams the large locus map into `.tmp`; final aggregate TSVs and then final locus-map rename precede the final summary. Completed per-assembly JSON is atomically renamed. An interruption should leave no completed summary for a fresh output directory. A future rerun must use a fresh output directory/run identity or explicitly quarantine any old final summary: the code does not invalidate an existing completed summary at startup, so mere existence could otherwise be stale. This review initially observed the current run before its final summary/locus map existed, and subsequently verified the newly completed outputs and actual child exit.

The validator's local atomic JSON helper uses a fixed `.tmp` sibling and does not use the production bounded sharing-lock retry helper. Single ownership and reading only completed immutable outputs reduces collisions, but a sharing error would still be a real failed run requiring explicit recovery; it must not be hidden by wrapper0.

## Required promotion gate and minimal later fix

For the current job, independently require all of the following before promoting Stage2 or starting dependent science:

1. The completed child command has exit 0; final summary is tied to this run/source/input hashes and its status is the documented integrity PASS, with zero errors and `complete_exact196_accounting=true`.
2. Summary says196 approved,196 raw packages and196 reported assemblies. QC table contains196 unique exact accessions equal to the approval list; all per-assembly records agree and error_count sums to zero. `errors.tsv` has a valid header and zero data rows.
3. Final locus map, assembly QC, replicon QC, member hashes, review exceptions and all 196 per-assembly JSONs exist and parse. No `.tmp` substitutes for final artifacts. Streamed locus row count equals the final summary and per-assembly locus sum; all locus keys and accession joins are checked independently.
4. Approval/list/ledger/source hashes equal the frozen Stage1 and final validator receipts; preserve all documented exceptions. Recheck hashes around promotion and preserve the raw package/member manifests rather than trusting output presence.
5. Package portable artifacts, verify the GitHub commit/release bytes separately, then mark publication verified and advance. Scientific integrity PASS alone is not UPLOAD_VERIFIED and does not establish marker/R-M science.

The minimal wrapper correction was applied after the active job finished: only `check=False` to `check=True` in the validator subprocess call. Exact original bytes were preserved in `.work/validator_wrapper_pre_parent_review.py`.

- Original successful run's wrapper SHA256: `496641651e8019b73c0314892507ebce549dfb355e263600eca38c287b85fc29`.
- Corrected wrapper SHA256: `f90e6778982f1161231205f16b7f7615143cc6ecd07809fb9c55de47da6e5c11`.
- Scientific validator unchanged: `345bcea7a0decf8a34b485eeb2260e1298c3ebf4ef508e8e654b239c45fc4e64`.
- Original production child command began 12:56:38.791578 UTC and records exit 0, elapsed 266.364 seconds in `reports/stage02/validation_commands.jsonl`; its science output ended 13:01:05.076842 UTC. The later wrapper fix is not retroactively attributed to that run.

Two isolated tests executed the actual corrected wrapper with fake production/publication modules inside Windows TemporaryDirectory. Each used 196 empty placeholder paths solely to satisfy the wrapper preflight, then a tiny real synthetic subprocess in place of biological validation. Child exit 7 propagated as CalledProcessError(returncode 7); child exit 0 returned normally. Both forwarded check=True and permitted the one-byte lock to be reacquired afterward. No source ZIP was parsed, no production lock acquired, no GitHub action performed, and the main CLI was untouched. The unmodified run helper was also exercised in isolation: check=False swallowed the synthetic exit 7 from its caller while check=True raised. A first harness assertion expected LF; it was corrected to platform-neutral splitlines for Windows CRLF and the tests passed. No production change was needed for that harness issue.

The explicit final scientific gate remains required beyond the one-argument fix. Add stale-summary/run-identity and launch-source/input hash guards in a focused subsequent change if needed; generic `production_resume.run` was not patched. Publication remains a separate unverified-by-this-review gate.

## Publisher source check

Read-only inspection of the active `scripts/finalize_stage02.py` confirms it checks exact 196 count/uniqueness, completed accounting/raw 196, current validator hash, zero summary/per-assembly errors, original raw-ZIP hashes, and ordered assembly-QC membership before final handoff. Its own gate does not independently re-count every final TSV or compare the approval/ledger hashes; the independent checks above supply those assertions for this actual run.

Publication code creates standalone ZIPs with local CRC/member SHA256 verification, enforces the practical 500MiB limit, checks remote asset size/digest where supplied, downloads each ZIP, rechecks its whole-file SHA256 and member hashes, and verifies the remote release tag commit before writing UPLOAD_VERIFIED. This is source inspection, not a claim that those uploads/readbacks have completed. At the last artifact comparison 13:06:16 UTC, a completed publication receipt was absent. The parent continues to verify actual publication separately.

The wrapper correction was made before the publisher began and before its methods-source hashing. Thus the future distributed wrapper may correctly be the repaired f90e... source while the already successful scientific run used original 4966... wrapper. Keep both identities with the run record; the unchanged scientific validator hash remains 345b.... No publisher source was edited by this reviewer.

The completed whole-panel result claimed here is sequence/annotation integrity with recorded exceptions only. No ANI/taxon certification, host phylogeny, R-M annotation, circular tree or publication verification is claimed.
