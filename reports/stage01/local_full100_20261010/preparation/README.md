# Full-100 Stage 3 input audit

This read-only audit verified the curated Stage 3 v2 per-marker source FASTAs against the accepted sequence manifest and independent Stage 3 validation summary. It does not stage, align, infer trees, or modify the canonical repository.

The source set contains 100 ordered marker FASTAs and 19,359 accepted records. Their accession union is exactly the 196-ID approved panel. Every record's normalized amino-acid SHA-256 and length match `accepted_sequence_manifest.tsv`; there are no duplicate accession headers, gaps, empty sequences, unapproved IDs, or sequence/length manifest mismatches. Per-marker record counts range from 177 to 196, so absent marker-accession pairs remain absent and are not filled.

Identical sequence strings recur across distinct accessions within markers. These 9,065 excess identical-content records are retained; the duplicate-free check applies to accession headers/records, not to biological sequence equality.

All five existing files in canonical `input_genes/` are byte-identical to their corresponding v2 marker FASTAs. `C:\Users\wheel\Downloads\input_genes` was absent at audit time. Stage 3 validation summary SHA-256: `6cbefd1c485823a858121417f1419aa8fe86ba1684b34eaf504eef7a63db8bd5`. Accepted manifest SHA-256: `d307b8a3f5c9057616c66868ba8e8082fdc269f25fa72e476396dfbcbd34ac2a`. Total source FASTA bytes: `4034538`. Extractor SHA-256: `5f16e2aeb7e038dc4277e4c0615b78fa79b19369fbf6a7fd5ac7e6042087763d`.

Reproduce with Python 3 (result files are opened exclusively and will not be overwritten):

```powershell
python .\audit_full100_inputs.py --project-root 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196' --output-dir .
```
