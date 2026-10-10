# Raw NCBI host metadata audit

This is a one-to-one join of the canonical 196 approved accessions to downloaded NCBI `assembly_data_report.jsonl` BioSample fields. It is metadata evidence only: it contains no DefenseFinder, PADLOC, or other defense-system calls, and creates no defense 0/1/unknown matrix.

`host_metadata_raw.tsv` joins `approved_panel.tsv:assembly_accession` to each report's `currentAccession` by exact string equality. It copies `biosample.host`, `biosample.isolationSource`, and `biosample.hostDisease` as source-reported strings. JSON null or absent values become blank cells; literal source strings such as `missing` are retained. No host-category inference or taxonomy reclassification is performed.

`audit.json` records SHA-256 provenance for the approved panel, `status/stages.tsv`, and all 196 source reports. Three source files contain older `accession` aliases (four alias records total); the exact current-accession record is selected when a report contains multiple records, and aliases are preserved in the audit with source line numbers. Stage 5 is recorded NOT_RUN for execution, validation, and publication. That is workflow status, not biological absence.

Reproduce with Python 3 (the extractor refuses to overwrite any result file):

```powershell
python .\extract_host_metadata.py --project-root 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196' --output-dir .
```

Extractor SHA-256: `4977509ca99d5e4a4ea1fb837612e8b04edadfd4dafd44a0264974282d461d47`  
TSV SHA-256: `d396deed70cf14eb5b707e2df947c7d5c93a02456c66def44c70e5b8f91cac40`
