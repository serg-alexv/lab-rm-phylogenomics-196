from pathlib import Path
import hashlib, json

G = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
R = G / 'reports/stage01/itol_api_20261010'
old = (G / 'run_pipeline.sh').read_bytes()
assert hashlib.sha256(old).hexdigest() == '5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))

write(R / 'run_pipeline.before_integration.sh', old)
text = old.decode('utf-8')
anchor = '  echo "Pilot done: pilot_output/species_tree.newick"'
assert text.count(anchor) == 1
text = text.replace(anchor, '  python scripts/validate_pipeline.py --mode pilot --report-dir reports/stage01/validation_pilot\n' + anchor)
text += '\n# User-requested full-run validation and authenticated iTOL upload.\n'
text += 'python scripts/validate_pipeline.py --mode full --report-dir reports/stage01/validation_full\n'
text += 'python scripts/make_itol_decorations.py\n'
text += 'python scripts/upload_itol.py\n'
write(R / 'run_pipeline.with_validation_itol.sh', text)
packages = json.loads((R / 'requests_install.json').read_text())['install']
write(G / 'scripts/requirements-itol.txt', ''.join(f"{item['metadata']['name']}=={item['metadata']['version']}\n" for item in packages))
write(G / '.github/copilot-instructions.md', '''# Local phylogenomics execution and validation

The latest user instruction is five-marker pilot first, then explicit user approval
before the full 100-marker run. Never start a second runner or replace its active
script. All scientific execution stays local in Ubuntu WSL. Do not overwrite,
move, or delete existing scientific artifacts without the user's approval.

## 10. Post-execution validation loop

Immediately after ASTRAL, run scripts/validate_pipeline.py with explicit
--mode pilot or --mode full and a fresh --report-dir. The prepared Bash integration
uses reports/stage01/validation_pilot and reports/stage01/validation_full.
The validator prints GLOBAL_PIPELINE_STATUS: PASS or FAIL, prints each failing
check, writes validation_summary.tsv, and exits nonzero on failure. set -euo
pipefail stops the Bash pipeline before decoration/upload if validation fails.

Compare every gene tree with its own FASTA taxa and the ASTRAL tree with the union
of selected marker taxa. Pilot mode selects the first five sorted FASTAs; full
mode requires exactly 100 markers and all 196 approved accessions. Never infer
mode from directory existence: both output directories are created in either mode.
Record unlabeled IQ-TREE branches explicitly without imputing support. Preserve
raw ASTRAL annotations and a separate validated numeric q1-frequency tree.
Use isolated fixture copies for corruption tests; never truncate master results.

The iTOL uploader requires the full validation receipt and matching source/derived
tree SHA256 values. Credentials remain in /mnt/c/itol.api-key.txt and must never
enter Git, archives, stdout, or logs. Publish completed results with checksums and
independently read back the remote bytes. Never force-push.
''')
write(R / 'README.md', '''# Validation and direct iTOL API integration

The existing five-marker pilot is still running from unchanged run_pipeline.sh
SHA256 5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b.
run_pipeline.with_validation_itol.sh is a prepared revision, not the active runner.
Activate it only after the current runner has a successful terminal receipt and
has released the original lock. Its source installation is user-authorized; a
full 100-marker execution still requires separate user confirmation.

The candidate validates after ASTRAL in both explicit modes. Full mode then
generates the two decoration files from the real cell_mapping.tsv and uploads
through scripts/upload_itol.py. All inference remains local. Existing outputs
are refused rather than overwritten. The five current FASTAs are not a complete
100-marker input set. root cell_mapping.tsv and final species_tree.newick are
currently absent; real dataset generation/upload have not happened.

Validation checks each locus against its own input taxon set and checks ASTRAL
against the selected marker union. A pilot may legitimately cover fewer than196
taxa; the actual current five-marker union contains all196. Full mode additionally
requires100 markers and equality with all196 approved IDs. Truncation, duplicate,
missing and extra tips fail. Unlabeled gene-tree supports are recorded, not filled.
This checks workflow/data integrity, not biological reliability or model adequacy.

Official API contract checked 2026-10-10:
https://itol.embl.de/help.cgi#batch
Upload uses https://itol.embl.de/batch_uploader.cgi with APIkey, projectName and
zipFile. The ZIP has a .tree member and two tab-separated datasets. The tree member
is the hash-verified flat q1-frequency derivative; the native ASTRAL source is
retained unchanged. q1 is a quartet frequency, not the pp1 local posterior.
Defense source accepts defense_systems.txt or the earlier defense_systems_heatmap.txt
name; both use DATASET_BINARY, and conflicting copies are rejected. Host strip is
required. Dataset identifiers must exactly match all196 validated tree tips.

The key is read only from /mnt/c/itol.api-key.txt, after local preflight. Requests
are authenticated only to the official HTTPS endpoint; redirects and automatic
retries are disabled. SUCCESS with a numeric tree ID is required. The permalink
is printed to stdout and saved. Circular SVG/PDF exports use batch_downloader.cgi
and display_mode=2; this does not assert a persistent circular setting in the UI.
Official batch upload requires an active standard iTOL subscription; account
eligibility has not been tested. No real upload was attempted.

pipeline_output/itol contains the ZIP, asset hashes, redacted response, permalink
and successful export files. A failed or ambiguous network request preserves
evidence and stops; the directory blocks blind resubmission. A permalink proves
upload acceptance only; both exports also need exit0 and their saved files.

requests and its dependencies were installed only into the existing local
phylogeny Conda environment. requirements-itol.txt pins installed versions;
requests_install.json/log retain the install receipt. Synthetic API tests use
dummy credentials and fake HTTP, never the real key or iTOL service.
''')
print(json.dumps({'candidate_sha256': hashlib.sha256(text.encode()).hexdigest(),
                  'active_script_unchanged': (G / 'run_pipeline.sh').read_bytes() == old,
                  'source_only': True}))
