# Stage00: measured acquisition preflight

Executed on WD at 2026-10-08T11:46:56.551027+00:00. Stage01 immutable payload and receipt were independently checked (71 files, 196 exact accessions); no bootstrap repeated. GitHub identity serg-alexv and main reconciled.

Windows free RAM 4805017600 bytes; C free disk 118363553792 bytes. One sequential NCBI download; at most two compute threads. No unrelated processes stopped. Ubuntu inspected: Python/curl available; downstream scientific tools absent from PATH. Their installation and database pinning remain pending, explicitly recorded.

Official NCBI Datasets datasets version: 18.38.0 is acquisition-ready; exact binary SHA256 and actual --help retained. The six requested file roles are genome, protein, CDS, GFF3, GBFF and sequence report. Exact version accessions only; --assembly-version all permits archived explicit versions, with returned membership checked.

Validation: input SHA256/196 uniqueness, stage01 verified receipt, WD identity, authenticated user, remote commit, >10GiB disk and actual CLI help passed. Independent checker report is included. No sequence QC, phylogeny or R-M results are claimed.

Methods source: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/download-and-install/
