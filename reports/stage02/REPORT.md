# Stage02: complete approved196 sequences and independent integrity validation

All196 exact-version assemblies were downloaded on WD with NCBI Datasets18.38.0. Independent validation reports zero errors and 16155 explicit source annotation/metadata review exceptions. Full196 accounting passed; no assembly was dropped, replaced or used as a pilot.

Validation elapsed: 265.802s. Python 3.14.6; BioPython 1.88; 16 parser self-tests, plus separately executed synthetic package tests in validator_review_evidence.json. This stage verifies file/feature/translation integrity and preserved taxonomy compatibility, not independent ANI or enzymatic function.

The checker rereads raw provider ZIPs, catalog roles, provider MD5/member SHA256, genomic FASTA and sequence-report IDs/lengths, GBFF genomic sequences, protein/CDS/GFF/GBFF exact-locus joins, CDS frames/segment phases and source translations. It retains assembly+replicon+locus keys; repeated WP accessions do not collapse biological loci. GC, ambiguity, record count and replicon topology are in replicon_qc.tsv.

Pseudogenes and documented translation exceptions remain explicit. Annotated codon_start offsets are applied only during CDS comparison. For documented 3-prime partial codons, virtual N ambiguity padding is used only as a validation operation; source sequence files are never altered. Omission is accepted only for an unresolved terminal X with an exactly matching complete-codon prefix. Internal mismatches fail.

NCBI --assembly-version all was experimentally rejected when it returned unapproved historical biological files. Its failed raw attempt is retained. Subsequent retrieval used tested default exact-accession commands. The few earlier accepted packages retain historical metadata-only catalog/report entries, explicitly reviewed and excluded from biological membership. Archived metadata are not an alternative cohort.

The Windows restart interrupted retrieval at79 packages; the independent restart audit preserved all79. Mutable progress replacement later encountered Windows file-sharing denial, so timestamped atomic progress receipts were used. No unrelated processes were stopped and no restart was requested by the workflow.

Publication is checked separately from scientific validation. Standalone ZIP batches contain original provider ZIPs, extracted portable files, individual hashes and per-assembly validation. Full locus tables are Release assets to avoid giant Git blobs. Source/derived namespaces remain separate.

[NCBI Datasets documentation](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/download-and-install/) supplies the acquisition method; exact executed commands and tool/code/input hashes are retained in this repository and asset manifests.

Stages3-7 remain not run at this payload freeze. Host filters are predeclared in config/host_primary.json before marker searches/topology.
