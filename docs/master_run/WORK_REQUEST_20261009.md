You are continuing an existing bacterial phylogenomics project on the WD workstation.

Your job is to complete the scientific analysis from the last validated checkpoint and deliver a publication-ready circular phylogenetic tree with binary annotation rings showing the distribution of restriction–modification (R–M) system types, together with all raw/intermediate/final data required to reproduce and audit the result.

CANONICAL PROJECT REPOSITORY:

https://github.com/serg-alexv/lab-rm-phylogenomics-196

REFERENCE FIGURE STYLE:

Tesson et al., Nature Communications (2022), Figure 4b/c:
https://www.nature.com/articles/s41467-022-30269-9/figures/4

The desired final visualization is an annotated circular host phylogeny with concentric binary presence/absence tracks.

The four R–M rings, from inner to outer, must be:

1. Type I
2. Type II, including Type IIG
3. Type III
4. Type IV

The work must be scientifically defensible, reproducible, independently validated, and deposited stage-by-stage in the existing repository/releases in the same spirit as the already completed Stages 0–4a.

================================================================
1. BOOTSTRAP FROM ZERO CONTEXT
================================================================

Assume you have no memory of previous sessions.

Before running any biological computation, reconstruct the current project state from:

A. the WD filesystem and currently running processes;
B. the canonical GitHub repository.

First inspect the local WD project location and determine:

- local repository path;
- current git commit;
- git status;
- local uncommitted changes;
- currently running project processes;
- existing IQ-TREE, PADLOC, DefenseFinder, R, Python, WSL or controller processes;
- existing Stage 4/5 output and checkpoint files;
- available Windows RAM;
- Windows commit headroom;
- available disk space;
- WSL distributions and their current state;
- relevant WSL disk/free-space information;
- installed scientific tools and versions.

Then inspect the current remote repository state, at minimum:

- `README.md`
- `AGENTS.md`
- `WORK_ORDER.md`
- `STATUS.md`
- `status/stages.tsv`
- `status/stage04_execution.json`
- `reports/stage04a/REPORT.md`
- `reports/stage04a/alignment_summary.json`
- `reports/stage04a/validation_summary.json`
- `reports/stage04b/REPORT.md`
- newer files under `reports/stage04/` and `reports/stage04/recovery_*`

Do NOT blindly `git pull`.

First compare local and remote state.

If the local clone is clean and merely behind remote `main`, a normal fast-forward/fetch is acceptable.

If local work or execution state exists that is not yet published, preserve and reconcile it before changing the working tree.

Do not redownload existing GitHub Release assets if the corresponding local files already exist and their hashes match.

Download only missing scientific inputs required for the current stage.

================================================================
2. ACCEPTED UPSTREAM WORK: DO NOT REDO IT
================================================================

Unless current independent validation proves corruption or invalidation, treat the following as completed upstream work:

- Stage 0 — environment/setup
- Stage 1 — approved 196-genome panel
- Stage 2 — genome acquisition and validation
- Stage 3 — conserved host-marker identification and curation
- Stage 4a — alignment, trimming and concatenation

The accepted primary host-phylogeny input is the validated Stage 4a `primary196` concatenated amino-acid alignment.

The repository previously recorded approximately:

- 196 genomes/tips
- 100 curated conserved host protein markers
- 17,456 aligned amino-acid columns

Verify the exact current files and SHA-256 hashes from the repository/local release.

The primary tree must start directly from this validated concatenated alignment.

Do NOT rerun:

- genome downloads;
- host marker detection;
- orthology selection;
- MAFFT;
- trimAl;
- marker concatenation;
- construction of the primary196 supermatrix;

unless independent validation demonstrates that the accepted Stage 4a artifact is actually invalid.

The concatenated alignment is already the complete input matrix for phylogenetic inference.

The 100 markers and 17,456 columns describe how that alignment was constructed; Stage 4 does not reconstruct them again.

================================================================
3. RESOURCE AND EXECUTION POLICY
================================================================

You may use any available WD resources that are appropriate:

- native Windows;
- WSL;
- Ubuntu/Linux tools;
- PowerShell;
- Python;
- R;
- Conda/Micromamba environments.

Choose the environment best suited to each atomic task.

However:

A heavy biological job must remain in one execution environment from launch to completion. Do not migrate a running IQ-TREE or equivalent inference process between Windows and WSL.

Do not construct elaborate nested controller/observer systems unless strictly necessary.

Use simple, atomic jobs with:

- explicit inputs;
- input hashes;
- exact command;
- resource requirements;
- start time;
- process identity;
- output directory;
- bounded resource-admission wait;
- bounded or monitored runtime;
- exit status;
- independent output validation.

Every computational job must terminate in one of:

- `COMPLETE_VALIDATED`
- `FAILED_RETRYABLE`
- `FAILED_FATAL`
- `DEFERRED_RESOURCE`

Do not remain indefinitely in `WAITING`, `UNKNOWN`, or polling loops.

An uncertain prior process may be investigated for a finite bounded interval; if ownership cannot be established, report it explicitly and do not launch a duplicate job.

Resource problems must not be solved by silently removing genomes or accepted host markers.

The approved biological dataset remains 196 genomes and the accepted 100-marker Stage 4a alignment unless a new scientific validation result explicitly invalidates part of it.

================================================================
4. STAGE 4 — COMPLETE THE HOST PHYLOGENETIC TREE
================================================================

The scientific task is now:

validated Stage 4a concatenated alignment
→ maximum-likelihood phylogenetic inference
→ validated 196-tip host tree.

------------------------------------------------------------
4.1 First reconcile any existing Stage 4 result
------------------------------------------------------------

Before launching new inference, inspect all existing Stage 4 processes, checkpoints and outputs.

Determine whether the latest Stage 4 attempt produced a complete scientifically valid tree.

Inspect, where present:

- `.treefile`
- `.contree`
- `.iqtree`
- `.log`
- model files
- bootstrap/support outputs
- checkpoints
- process receipts
- exact input hashes

If a complete 196-tip tree already exists and passes independent validation, adopt it and do not rerun Stage 4.

If an old process is still genuinely running, do not start a duplicate.

If the previous attempt is dead/incomplete/invalid, preserve its outputs and proceed according to the fallback policy below.

Do not spend unlimited time reconstructing obsolete controller history.

------------------------------------------------------------
4.2 Preferred analysis
------------------------------------------------------------

Use the existing validated Stage 4a primary196 alignment and its existing partition map.

Preferred inference:

- IQ-TREE 3.x, using the pinned/validated installed executable;
- amino-acid data;
- the existing 100-marker partition definitions;
- ModelFinder/model selection appropriate for the partitioned analysis;
- maximum-likelihood topology optimization;
- 1,000 ultrafast bootstrap replicates;
- 1,000 SH-aLRT replicates;
- deterministic recorded seed;
- branch lengths preserved;
- support values preserved;
- exact command recorded.

Use only as many threads as current resource measurements safely support.

Do not use an outgroup merely for visual aesthetics.

If no biologically justified and separately validated outgroup is already available, retain the host tree as explicitly unrooted. Circular display does not require a biologically rooted topology.

------------------------------------------------------------
4.3 Resource admission for heavy inference
------------------------------------------------------------

Before starting IQ-TREE, measure fresh:

- available physical RAM;
- Windows commit headroom or Linux equivalent;
- free disk space on the actual working volume.

Estimate a conservative job requirement using historical measurements from the repository plus a safety margin.

Require both:

1. enough memory for the job;
2. a meaningful host reserve.

Do not blindly reuse an old 1.5-GiB or 3-GiB cap if historical evidence demonstrates that it was too small.

If the preferred partitioned analysis cannot be admitted immediately, wait only for a bounded period, approximately 30 minutes unless current evidence justifies another finite interval.

During this wait:

- do not kill unrelated user processes;
- do not repeatedly restart IQ-TREE;
- do not change the biological dataset.

If sufficient resources still do not become available, move automatically to the predefined scientific fallback.

------------------------------------------------------------
4.4 First fallback: same data, simpler statistical model
------------------------------------------------------------

If the full partition-aware analysis repeatedly fails because of resource limitations, keep the exact same:

- 196 genomes;
- 100 accepted markers;
- 17,456-aa concatenated alignment.

Do not redo Stage 4a.

Run a single-model concatenated maximum-likelihood analysis using the same alignment, for example conceptually:

`iqtree3 -s concatenated.faa -st AA -m MFP -B 1000 --alrt 1000 -T <safe_threads> -seed <recorded_seed> -keep-ident -pre <new_unique_prefix>`

Verify the exact installed IQ-TREE syntax before execution.

This fallback changes model complexity, not the biological dataset.

Record clearly in Methods that the final tree was inferred from the concatenated 100-protein alignment using a single best-fit amino-acid substitution model.

Use a new output namespace/prefix. Never overwrite earlier attempts.

------------------------------------------------------------
4.5 Second fallback
------------------------------------------------------------

If the unpartitioned IQ-TREE analysis itself fails for a confirmed implementation/resource reason despite adequate disk and a reasonable memory budget, permit ONE alternative maximum-likelihood implementation capable of using the same concatenated alignment, preferably RAxML-NG.

Preserve:

- same 196 taxa;
- same accepted alignment;
- equivalent support analysis where scientifically appropriate.

Document the methodological change explicitly.

Do not automatically launch multiple competing tree engines.

If this also cannot run on the available WD hardware, stop Stage 4 with `FAILED_FATAL` or `DEFERRED_RESOURCE` and produce exact evidence of the limiting resource/error rather than looping.

Do not silently reduce the genome panel to solve hardware limitations.

------------------------------------------------------------
4.6 Stage 4 acceptance gate
------------------------------------------------------------

Independently validate the accepted final tree.

Require:

- exactly 196 unique tips;
- exact equality with the frozen approved accession set;
- no duplicate tips;
- no missing approved genomes;
- no extra taxa;
- valid parseable Newick;
- finite valid branch lengths;
- required support calculations completed;
- exact provenance to the accepted Stage 4a alignment;
- exact command/version/seed/model recorded;
- hashes recorded.

Freeze at minimum:

- `primary196_host_tree.nwk`
- `primary196_host_tree.nex`
- final `.iqtree`/equivalent report
- logs
- support outputs
- exact command
- input/output SHA-256 manifest
- independent validation report

Once this passes, Stage 4 is complete.

Do not let optional sensitivity analyses prevent progression to Stage 5.

Sensitivity analyses may be retained/completed separately where useful.

================================================================
5. STAGE 5 — R–M SYSTEM DETECTION AND CURATION
================================================================

This stage is independent of host-tree inference.

Analyze ONLY restriction–modification systems.

The final broad categories are:

- Type I
- Type II, including IIG
- Type III
- Type IV

Preserve finer subtype information when supported.

------------------------------------------------------------
5.1 Detection
------------------------------------------------------------

Use the existing validated genome/protein/annotation data from Stage 2.

Follow the existing repository work order unless current evidence justifies a documented adjustment.

Preferred strategy:

PRIMARY:
- PADLOC

CORROBORATION:
- DefenseFinder

Use HMM/domain/genomic-context analysis and REBASE/primary literature only where needed for classification or validation.

Freeze and record exact versions of:

- PADLOC;
- PADLOC database/models;
- DefenseFinder;
- DefenseFinder models/database;
- HMMER if used;
- reference database dates.

Do not silently change model/database versions mid-analysis.

------------------------------------------------------------
5.2 Fragment Stage 5 per genome
------------------------------------------------------------

R–M screening across 196 genomes is naturally separable.

Treat each genome as an independent atomic job.

For every genome, record:

- input accession/hash;
- detector status;
- raw outputs;
- exit code;
- validation status.

A failure for one genome must not invalidate or rerun successful analyses for the other 195.

Use resource-aware bounded concurrency.

Prefer one or a small number of simultaneous detector jobs based on current RAM/CPU measurements.

Do not automatically use all logical CPUs.

------------------------------------------------------------
5.3 Preserve genomic context
------------------------------------------------------------

Retain:

- assembly accession;
- replicon/contig/scaffold;
- protein ID;
- locus tag;
- coordinates;
- strand;
- local gene ordering.

Do not concatenate proteins from unrelated replicons and infer artificial gene adjacency.

------------------------------------------------------------
5.4 Classification rules
------------------------------------------------------------

Do not call generic methyltransferases, nucleases or ATPases complete R–M systems solely from names.

Type I:
require detector/architecture evidence compatible with a Type I system, typically involving appropriate HsdR/HsdM/HsdS components.

Type II:
require compatible Type II restriction–modification architecture.

Keep Type IIG as a subtype but collapse it into Type II for the final four-ring figure.

Do not treat orphan methyltransferases as complete Type II systems.

Type III:
require compatible Mod/Res or equivalent detector-supported architecture.

Type IV:
treat independently; do not require a cognate methyltransferase where biology does not require one.

Do not double-count the same biological locus merely because PADLOC and DefenseFinder both identify it.

Reconcile overlapping calls by genes/coordinates/system architecture.

------------------------------------------------------------
5.5 Required R–M outputs
------------------------------------------------------------

Preserve raw calls before collapsing them.

Generate at minimum:

`rm_systems_raw.tsv`
- one row per raw detector system/hit.

`rm_loci_curated.tsv`
- one row per curated biological R–M locus/system.

Recommended fields include:

- accession;
- replicon;
- system ID;
- broad R–M type;
- subtype;
- detector;
- model/profile;
- genes/proteins;
- coordinates;
- completeness;
- confidence;
- caveats;
- corroboration.

Generate:

`rm_type_counts.tsv`

with:

`accession | Type_I | Type_II | Type_III | Type_IV`

where values are numbers of accepted systems.

Also generate:

`rm_type_presence_absence.tsv`

with the same columns, where:

- `1` = at least one accepted system of that type is present;
- `0` = screening completed successfully and no qualifying system was detected;
- `NA` or explicit nonbinary state = failed/unresolved/not-run case.

Multiple systems of the same type still produce a binary value of `1`.

Also preserve:

- `rm_subtypes.tsv`
- `rm_unclassified.tsv`
- `rm_type_state.tsv`
- validation report

Do not equate computational non-detection with experimentally proven biological absence.

================================================================
6. TREE–R–M JOIN VALIDATION
================================================================

Before plotting, validate the tree and R–M matrix by exact accession ID.

Require:

- exactly 196 unique tree tips;
- exactly 196 unique R–M matrix rows;
- set(tree tips) == set(R–M accession IDs);
- no duplicate accessions;
- no row-order-based matching;
- every genome has four broad-type states;
- all 196 × 4 = 784 cells are explicitly accounted for.

Generate:

- `tree_rm_join_validation.tsv`
- `tree_rm_join_validation.md`

The final figure must not be generated until this gate passes.

================================================================
7. STAGE 6 — FINAL CIRCULAR PHYLOGENETIC FIGURE
================================================================

Construct the final figure using the accepted host tree and validated R–M matrix.

The visualization should follow the logic of Nature Communications 2022 Figure 4b/c:

central circular host phylogeny
+
concentric binary annotation tracks.

Use:

CENTER:
- accepted 196-tip phylogenetic tree;
- topology unchanged;
- branch lengths retained.

RINGS, INNER → OUTER:

1. Type I
2. Type II, including IIG
3. Type III
4. Type IV

Primary ring semantics:

- colored/filled = present;
- white/empty = successfully screened and not detected;
- explicit separate state/color = unresolved/failed/not assessed.

Do not encode copy number in ring width or duplicate rings.

Copy number and subtype information remain in underlying tables.

------------------------------------------------------------
7.1 Rendering
------------------------------------------------------------

Produce a reproducible local vector figure, preferably using:

- R
- ggtree
- ggtreeExtra
- ggplot2

Use the existing or a clean isolated R environment.

R package/environment failures are Stage 6 environment issues and must not trigger rerunning Stage 4 or Stage 5.

Also generate iTOL-compatible data:

- `primary196_host_tree.nwk`
- `rm_types_itol.txt`

Use the current documented iTOL dataset syntax rather than guessing it.

Taxonomic coloring may be included where useful but must not obscure the R–M tracks.

Do not infer ancestral taxonomic states merely for aesthetics.

------------------------------------------------------------
7.2 Final figure outputs
------------------------------------------------------------

Produce at minimum:

- `rm_phylogeny_primary196.svg`
- `rm_phylogeny_primary196.pdf`
- high-resolution PNG if useful
- `primary196_host_tree.nwk`
- `primary196_host_tree.nex`
- `rm_types_itol.txt`
- exact plotting input table
- reproducible plotting script
- legend/color specification
- accession ↔ display-label mapping
- figure validation report

SVG/PDF are the authoritative publication-quality graphics.

Do not use a screenshot as the final scientific figure.

================================================================
8. FINAL INDEPENDENT VALIDATION
================================================================

Independently verify:

TREE:
- 196 exact approved tips;
- valid topology and branch lengths;
- support values present as intended;
- provenance to accepted Stage 4a alignment.

R–M DATA:
- every positive state traces to at least one curated R–M locus;
- count matrix and binary matrix are consistent;
- detector failures were not converted to zeros;
- Type IIG is retained as subtype but grouped into Type II for the four-ring figure.

FIGURE:
- 196 tips;
- four rings;
- correct ring order;
- 784 explicit genome × type assignments;
- no shifted annotation rows after tree reordering;
- rendered state equals source matrix state;
- topology was not modified during plotting.

Generate a machine-readable figure mapping such as:

`figure_ring_mapping.tsv`

with:

- accession;
- tree-tip order/index;
- Type I state;
- Type II state;
- Type III state;
- Type IV state.

================================================================
9. DEPOSIT ALL INTERMEDIATE AND FINAL RESULTS
================================================================

Preserve and publish stage-specific scientific artifacts in the canonical repository in the same general manner as Stages 0–4a.

After each newly completed stage:

1. validate locally;
2. freeze the accepted outputs;
3. generate SHA-256 manifests;
4. update concise stage reports;
5. publish compact text/code/tables to GitHub;
6. use GitHub Release ZIP assets for large portable datasets where appropriate;
7. verify remote upload/readback;
8. update `STATUS.md`;
9. update `status/stages.tsv`.

Do not overwrite or delete historical failed Stage 4 attempts.

Historical failure evidence is provenance, not an instruction to reproduce old controller architectures.

Scientific completion and publication are separate states.

A Git push does not constitute scientific validation.

A computation that passes validation but has not yet been published must be reported accordingly.

================================================================
10. EXECUTION ORDER
================================================================

Execute in this order:

A. Bootstrap and reconcile local WD + GitHub state.

B. Verify accepted Stage 4a primary196 alignment and hashes.

C. Determine whether an already completed valid Stage 4 tree exists.

D. If not, complete Stage 4 using:
   1. partition-aware IQ-TREE if feasible;
   2. same alignment with single-model IQ-TREE on resource failure;
   3. one alternative ML engine only if genuinely necessary.

E. Independently validate and freeze the final 196-tip host tree.

F. Run Stage 5 R–M screening across all 196 genomes using resumable per-genome jobs.

G. Curate loci and create:
   - raw R–M table;
   - curated locus table;
   - count matrix;
   - binary presence/absence matrix;
   - subtype/state tables.

H. Validate exact tree ↔ R–M accession matching.

I. Generate the circular phylogenetic figure with four binary R–M rings.

J. Export SVG/PDF/iTOL/raw data/reproducible scripts.

K. Perform final independent validation.

L. Publish and verify all accepted intermediate and final artifacts.

================================================================
11. DO NOT DO THE FOLLOWING
================================================================

Do not:

- redo Stages 0–4a without evidence of invalidation;
- restart from raw genomes for host-tree inference;
- reconstruct already accepted alignments;
- silently drop genomes because RAM is limited;
- silently drop accepted markers because RAM is limited;
- launch duplicate heavy phylogenetic jobs;
- wait indefinitely for RAM/disk/process ownership;
- migrate an active heavy job between Windows and WSL;
- build complicated nested controllers when a simple atomic job is sufficient;
- double-count PADLOC/DefenseFinder calls for the same locus;
- treat failed detector runs as biological absence;
- map R–M rows to tree tips by row position;
- alter phylogenetic topology for visual appearance;
- rerun Stage 4 because R plotting fails;
- rerun successful R–M genomes because another genome fails;
- claim experimentally active R–M systems from computational prediction alone.

================================================================
12. FINAL COMPLETION CRITERIA
================================================================

Do not declare the project complete until all of the following exist and pass validation:

HOST TREE:
- scientifically accepted 196-tip phylogeny;
- branch lengths;
- support values;
- full provenance and reproducible inference record.

R–M ANALYSIS:
- all 196 genomes screened or explicit documented exceptions;
- raw detector outputs;
- curated locus table;
- count matrix;
- binary Type I/II/III/IV matrix;
- subtype/uncertainty data retained.

JOIN:
- exact 196-accession equality between tree and R–M matrix;
- all 784 genome × broad-type cells accounted for.

FINAL FIGURE:
- circular host phylogeny;
- four concentric binary rings:
  - Type I
  - Type II including IIG
  - Type III
  - Type IV
- publication-quality SVG;
- publication-quality PDF;
- reproducible plotting code;
- iTOL-compatible files;
- exact underlying TSV data.

PROVENANCE:
- stage reports;
- commands;
- software/database versions;
- SHA-256 manifests;
- independent validation reports;
- repository/releases updated and remotely verified.

The final goal is not merely to “run the pipeline”.

The final goal is a scientifically validated, reproducible, publication-ready 196-genome phylogenetic tree with binary R–M Type I/II/III/IV annotation rings, plus the complete raw and intermediate evidence required to reproduce and defend the figure.