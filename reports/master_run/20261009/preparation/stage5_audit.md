# Stage 5 readiness audit — 2026-10-09

Read-only audit of `G:\My Drive\LAB_RM\lab-rm-phylogenomics-196`. No WSL startup, detector/HMM searches, installations, repo modifications, or production fixture executions. Existing reports were inspected, not rerun. Current direct human continuation/per-genome instructions supersede historical halt and controller requirements; old evidence must remain preserved.

## Outcome

Stage 5 biological execution remains **NOT_RUN**. Validated primary sequence/context inputs already exist. The retained upstream detector environment/models were successfully exercised on 2026-10-08, but are inside the currently unmounted Linux toolchain; their current executability has not been verified. The existing V7 runner is deliberately BUILD-only and is not an operational one-genome runner.

## Accepted inputs and provenance

- `reports/stage02/validation_summary.json`: PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS, all196 packages/assemblies, zero errors, 411514 CDS locus rows, 16155 documented annotation/partial/archive exceptions.
- Primary raw files are under `data/raw_ncbi/<accession>/package/ncbi_dataset/data/<accession>/`; original ZIP, catalog, provider checksum, member manifest and retrieval checkpoint are retained beside each package.
- `.work/source_locus_inputs_v1/assemblies/<accession>/`: exact-locus FAA, original primary NCBI FAA, complete locus crosswalk, replicon manifest, and separate per-replicon PADLOC/DefenseFinder FAA/GFF/topology inputs. Their `build_receipt.json` binds raw ZIP, source files and outputs.
- `.work/stage03_source_validation/validation_summary.json`: PASS_SOURCE_LOCUS_INPUT_TRACEABILITY, all196 passed; 2120 replicons, 411523 source context loci, 398537 protein-bearing loci, nine gene-only pseudogenes, 86 origin-spanning loci, 7502 coordinate-review loci; 12812 files/1893101586 bytes verified historically.
- Exact frozen approved panel SHA256: `85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6`.
- This audit read certificates and sample receipts; it did not repeat the accepted ~1.9GB source hash audit. Every future atomic genome job should reopen its own source receipt/member hashes before launch.

## Retained installed versions/models (historical executed receipts)

` .work/detector_review/runtime_evidence.json`, README and compile/model manifests record:

| Component | Pinned identity |
|---|---|
| PADLOC | 2.0.0; native R source SHA256 `d21ba942e80720d80027aa1740d756322560feaeb168bfa2890640d88950d4c0` |
| PADLOC-DB | v2.0.0, commit `7f99b47b75e232b111c18626badb9ac32e8e0b5a`; archive SHA256 `de1c9697ee735c7c8a856295ace5614c9c1959b6010cbc074a29125aa9c04fc9` |
| Active PADLOC profiles | 5027, exactly top-level `hmm/*.hmm`; 38 deprecated profiles preserved separately |
| Compiled PADLOC HMM | 984039424 bytes; SHA256 `a03df990d47ef40d2573a04d9a0f513e70999c3b9104216e3f6656a9bef8d5da` |
| DefenseFinder | 3.0.0 |
| MacSyFinder | 2.1.4 |
| DefenseFinder models | 3.0.0, commit `9b0d07b759f5f73d8c2b9aa3e696f4cdd04c11d2`; archive SHA256 `77e3486c30a889ee2b38121ea481769e12bd1871b0e6b6a0fdd845bdb42e97eb` |
| CasFinder models | 3.1.0, commit `ad7096548a814788ca04538602d71f85115b4c71`; archive SHA256 `c2f7cb124d0500ed97826a77fefd1c6a2ebce7c791e5e990c445f9cbf8da0bc8` |
| Supporting runtime | HMMER3.4, R4.3.1, Python3.11.17, pyhmmer0.12.3, pyrodigal3.7.1, Prodigal2.6.3; tidyverse2.0.0/yaml2.3.7/getopt1.20.3 |

Stable C tool root is `C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.tools`. Its `toolchain.ext4` exists (8589934592 bytes); `linux` is presently an empty mountpoint. The live detector prefix/models/DB therefore cannot be certified by Windows file checks without mounting/accessing the retained Linux toolchain. Get-Command found no native Windows Rscript/hmmsearch/padloc/defense-finder/macsyfinder; `C:\Program Files\R` was absent. This is not evidence that packages are missing inside the Linux image. No large download/install is currently justified.

## Boundary and scientific guarantees

Existing builder uses assembly+replicon+locus identity, never WP alone. PADLOC native source groups and orders by seqid/start, so one assembly FAA plus matching multi-seqid GFF preserves replicon boundaries. PADLOC does **not** wrap circular-origin neighborhoods: origin cases require review or separately validated classification-only rotation of cached hits.

MacSyFinder input is order-sensitive. Existing proposed routing places 1610 multigene replicons into 196 assembly gembase tasks, preserves contiguous replicon blocks/topology, and isolates239 singletons into supported ordered_replicon tasks.271 replicons have zero primary protein targets and need explicit review states. The retained native parser fixture demonstrated an installed2.1.4 singleton gembase bounds defect; never pad or concatenate singletons across boundaries. A simpler per-replicon ordered_replicon route is faithful but incurs many more searches.

Protein-only rank spacing omits untranslated/pseudogene context. Full source locus coordinates must remain in architecture review. Treat unknown topology conservatively as linear and retain the documented source topology. Existing coordinate audit found zero coincident `(seqid,start,end)` source groups across all196. Its accepted certificate is preparation evidence, not biological detection.

Native detector calls do not imply complete architecture. PADLOC Type I allows R/M with S secondary; DefenseFinder's R/M/S model minimum is two. HNH/VSPR or generic MTase hits must not become complete Type II; IIG folds into Type II only after architecture review. Type IV needs appropriate modification-dependent REase evidence, without forcing an MTase. Duplicate tool calls must merge by exact genes/coordinates. Failed/not-run/empty-target/partial/unresolved states never become zero.

## Existing implementation: useful parts and blockers

`scripts/stage05_detectors_windows_v7.py` imports fcntl/resource, reads `/proc`, uses `/bin` Linux tools and explicitly requires `sys.platform == 'linux'`. Its Windows filename describes the owner/path adapter; it is **not** a native Windows detector implementation.

The adapter preserves unmodified upstream PADLOC classification and unmodified DefenseFinder post-treatment. `native_df_scope_windows_v7.py` uses actual MacSyFinder configuration/model parsing. The runner's three MacSyFinder families/defaults match inspected packaged DefenseFinder3 engine source. PADLOC HMMER options match its packaged wrapper. This is a documented orchestration deviation designed to retain raw caches and avoid the ordinary DefenseFinder CLI's raw-directory removal/automatic annotation path. It is more scientifically faithful than rewriting PADLOC/DF classification in Python.

Current operational blockers:

1. `stage05_runtime_paths_windows_v7.py::require_execution_adoption` always raises BUILD_ONLY_OWNER_LIFETIME_RECEIPT_VALIDATOR_NOT_YET_IMPLEMENTED_NO_NATIVE_LAUNCH. Missing production bundle/parser/adoption/admission paths are confirmed absent.
2. Runner hardcodes all196 in one serial loop and has no accession argument; a failure aborts that invocation, although successful caches remain reusable. It does not implement the user's four terminal atomic-job states or finite resource wait.
3. `execute()` observes only the root child. Launch-receipt write failure after Popen lacks structured cleanup; PID absence is not descendant closure. It uses a historical 2GiB per-process address-space cap, which is not an aggregate subtree memory measurement/budget.
4. Whole mutable resource-receipt hash is included in scientific freeze; refreshing admission invalidates cache equality. New version must separate stable scientific/resource-policy identity from immutable fresh per-attempt admission.
5. Stage04 paths bind an obsolete four-scope V6 final certificate. New human instruction accepts primary196 tree and optional sensitivities separately: use new explicit provenance bindings, not forged old PASS files.
6. Current curation checker/adapter is not end-to-end adopted. Historical R selection fixture passed17 cases, but full metadata/alias expansion oracle remained resource-rejected/NOT_RUN. Python selection helpers are evidence-checking components, not validated substitutes for upstream classification.

Confirmed absent: `.work/stage05_bundles_windows_v7`, bundle validation, native execution, inventory, raw validation; `reports/stage05/windows_v7/{adoption.json,resource_preflight.json}`; older production inputs/native/inventory namespaces. Existing reports repeatedly identify searches, raw full196 validation, curation and784 final cells as NOT_RUN. Synthetic model/parser/cache/coordinate results must not be promoted into them.

## Smallest faithful implementation path

After the accepted primary tree is validated/published, access the retained WSL environment once under fresh resource admission and verify actual paths/interpreter/tool/model hashes. Preserve original source/tool artifacts. No supported Windows-native detector stack is presently established; upstream DefenseFinder declares POSIX, and the installed code and dependency builds are Linux. Porting engines would add avoidable scientific equivalence work.

Create one new simple runner namespace with an explicit `--accession` restricted to approved196. Reuse source parser/crosswalk and builder's per-assembly logic; independently validate that genome's detector bundle before searches. Execute one genome serially, its PADLOC then boundary-safe DefenseFinder tasks, with exact inputs/models/code stable identity, append-only attempts, logs/exit/timing/process identity, measured resources, finite timeout and verified child/descendant closure. No nested controller system or prior acceptance certificate architecture is intrinsically required by the current human instruction. If runtime ownership cannot be established, terminate the attempted admission as explicit deferred/fatal state, never start a duplicate.

Retain complete detector scope/defaults to avoid introducing a new model-equivalence problem; report/curate only R-M results. If narrowing detector models for cost is chosen, document it as a new explicit method and include every competing/forbidden role—do not silently cut the DB. On success, independently audit complete search/query and locus coverage, commit one hash-bound genome COMPLETE_VALIDATED checkpoint, and keep successes while later genomes fail/retry. Cache identity excludes transient PID/time/resource snapshots. Curation and784 explicit state/count/binary cells remain separate scientific work; raw native success never supplies those automatically.

Primary upstream references checked during audit: https://github.com/padlocbio/padloc ; https://github.com/padlocbio/padloc-db ; https://github.com/mdmparis/defense-finder/blob/master/setup.py ; https://macsyfinder.readthedocs.io/en/master/developer_guide/api/database.html . Pinned local source is authoritative for the retained implementation; current upstream pages do not establish live installed versions.
