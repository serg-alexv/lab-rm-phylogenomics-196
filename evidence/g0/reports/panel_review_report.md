# G0 panel review — propose strict union196; HUMAN approval pending

**Recommended exact panel:** the196 versioned accessions in `proposed_accessions.txt`, equal to selected177 plus19 strict-valid frozen-only historical anchor additions. Hold `GCF_000056065.1` for missing reported contamination. This answers the Figure2 sampling question with an explicit inclusive proposal: preserve all110 ranked named species, original selected strains and24 source-derived historical anchors within the audited197 universe. It is not a globally optimal selection or an approved final panel. **PENDING_HUMAN_APPROVAL; human approval NOT_GRANTED.**

## Scientific comparison

| Alternative | Assemblies | Named species | Source-derived anchors | Complete / chromosome / scaffold |
| --- | ---: | ---: | ---: | --- |
| selected177 | 177 | 110 | 5 | 132/4/41 |
| frozen150_exception_alternative | 150 | 98 | 25 | 114/5/31 |
| strict_frozen149_alternative | 149 | 97 | 24 | 113/5/31 |
| proposed_union196_pending_human_approval | 196 | 110 | 24 | 150/5/41 |
| union197_exception_alternative | 197 | 110 | 25 | 151/5/41 |
| sensitivity162_alternative | 162 | 110 | 24 | 117/5/40 |

Counts were independently recomputed from cached exact assembly reports and ranked species/genus taxIDs. Strict196 and selected177 both cover110 species;196 adds19 historical anchor accessions and broader strain coverage, not19 new species. Baseline-only149 loses13 externally verified species versus196. Sensitivity162 preserves110 species and24 anchors with fewer sampled strains; its exact membership is provided. Thus196 is an inclusive strain-coverage choice, not necessary merely to preserve species coverage. Genomic redundancy is **unknown**: no sequence, pairwise ANI, marker or functional analysis ran. See `panel_comparison.tsv`, `genus_species_summary.tsv`, `species_memberships.tsv` and `alternative_panel_memberships.tsv`.

Union196 genus/group counts are Lacticaseibacillus19, Lactiplantibacillus22, Lactobacillus19, Lactococcus23, Leuconostoc19, Limosilactobacillus20, Oenococcus15, Pediococcus18, Streptococcus23 and Weissella18. All23 Streptococcus are species **Streptococcus thermophilus, taxID1308**. Lactobacillus sensu stricto remains an operational scope label tied to the ranked Lactobacillus genus, not a separate formal rank. Each comparison group reports species count, assembly levels, QC ranges, anchors, BioSamples and missing strain labels.

Strict196 has NCBI-reported completeness95.42–99.92%, contamination0.03–4.84% and1–99 contigs; levels150 complete/5 chromosome/41 scaffold. All196 have distinct BioSample accessions and no duplicate exact species-taxID+nonempty assembly strain label;10 lack assembly strain labels. Isolate and BioSample fields are preserved rather than invented. Exact-label uniqueness is not genetic nonredundancy.

## Per-accession fate and historical authority

Original manifests remain177/150, overlap130, selected-only47, frozen-only20, union197. All20 historical removals are restored in this broader proposal because their current metadata pass and inclusive strain/species coverage is the stated objective; the historical table documents replacement/balancing rationale, not present metadata failure. Of20 historical additions,19 pass and are included; one is held for missing contamination. All27 formerly unassigned extras are included. Their18-per-group versus15-per-group sampling origin is documented by the historical Stage1 report and externally consistent counts, but exact individual historical drop reasons and current human intent are not proved. No version or GCA/GCF mapping was silently substituted or collapsed.

There are25 historical anchor accessions, not20:20 are additions and5 are already in selected177. Each inherited rationale and quality exception is preserved per accession as **source-derived, not independently revalidated experimental activity**. NCBI validates identity/metadata, not literature claims. Historical Stage1 where-reported95/5 and≤200 versus QUALITY_POLICY strict95/5/100 are distinct policies; neither is rewritten as current authority. The new inclusive strict95/5/100 proposal is explicit.

## Verified evidence and boundaries

All197 exact requested versions are current, with unchanged current accessions. Datasets v2 and EFetch taxonomy resolve130 organism taxIDs, one ranked GENUS and SPECIES per accession, and agree on lineage after root/rank serialization normalization. No queried canonical ID change or AKA IDs was observed; synonymous/other names are preserved. The NCBI retrieval window is **2026-10-08T08:51:50.553815+00:00 through 2026-10-08T08:55:15.085599+00:00**. No new network calls were made for this revision; all40 native responses and original inputs still hash correctly. See `taxonomy_verified_197.tsv` for full lineage, URLs/receipts/row locators/hashes/date, separate verification axes and dispositions.

All197 have annotated NCBI RefSeq metadata and ranked named species. The prior historical query's MAG/atypical/multi-isolate exclusion was not rerun and is not established merely by an absent flag in these reports. This limitation is not represented as a failed taxonomy join or as an unseen query PASS. Current metadata and reported QC do not prove sequence quality/identity. Missing RefSeq category is preserved as null; it is not missing RefSeq source or annotation.

Identity edges: `GCF_000016825.1` has assembly strain taxID557433 and compatible BioSample subspecies ancestor557436, within species1598/genus2742598. `GCF_900240275.1` retains official organism **[Lactobacillus] timonensis**, taxID1970790, but ranked genus is **Limosilactobacillus2742598**. EFetch other names preserve `Lactobacillus timonensis` as synonym and `Limosilactobacillus timonensis` as misspelling; do not rewrite the official organism to manufacture lexical agreement.

## Gate and transfer

Artifact reconciliation, external assembly metadata, ranked taxonomy and dated lineage-based Enterococcus exclusion pass for all197. Quality is independently separate:196 pass the strict reported predicates, one is UNRESOLVED_QUALITY with taxonomy still PASS. No accession has sequence-analysis approval. The human must choose the proposed inclusive196 versus alternatives and decide whether the missing-contamination exception is ever acceptable. See `G0_acceptance_report.md`, `enterococcus_exclusion_report.md`, `unresolved_questions.md` and `minimum_content_category_manifest.tsv`.

Direct host WD was verified. Exact session reproducibility is CLI **0.162.0-alpha.2**, model **gpt-6.1-sol**, effort **ultra**, session **01a11a7e-d1a0-7222-b517-5d08748b462f**, evidenced by bounded local session records and line hashes. Raw inputs and older root outputs were not changed. Parent handles remote repair reporting, final Cloud transfer and receipt-side verification. Local archive integrity does not establish delivery or Cloud receipt integrity. STOP at HUMAN G0 approval; no sequences or downstream analyses are authorized.

<!-- G0 executed validation -->

## Executed validation

`python work/g0/verify_g0.py`: **PASS_METADATA_VALIDATION_ONLY_PENDING_HUMAN_APPROVAL**, 4514 assertions (3061 core and 1453 independent scientific/content checks), 2622 source locations, all 40 raw responses re-read. Runtime 0.424s; CPU 0.219s; verifier peak working set 60764160 bytes (separate child-script memory is not included). Original 15 checksummed files still match. No sequence/function validation and no panel approval is implied.
