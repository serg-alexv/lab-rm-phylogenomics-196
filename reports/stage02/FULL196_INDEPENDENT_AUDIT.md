Full196 independent Stage2 audit passed. All 196 approved assemblies, 2,120 replicons, 1,960 extracted members and 411,514 unique assembly|replicon|locus keys were accounted for. 2,460,621,325 extracted bytes matched their recorded SHA256 and file sets; no extra files or error rows were found. 398,537 loci carry primary proteins. The 16,155 documented exception rows match the sequence-validation summary.

Checks independently read TSV/JSON accounting and raw extracted member bytes. Locus identity, uniqueness, per-assembly counts, replicon length sums, panel hash and validator source hash were verified. Translation states are preserved, including documented exceptions and partial terminal codon handling. This audit does not certify ANI, marker orthology, defense calls or function.

Command: `python audit_stage02_accounting.py --root . --validated .work/stage02_validated --output .work/review2/full196_independent_audit.json`
