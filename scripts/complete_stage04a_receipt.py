"""Resume Stage04a publication bookkeeping using its unchanged frozen payload."""
from pathlib import Path
import json
import stage04_controller as C
import production_resume as w
from portable_release import publish_frozen
from workflow_publication import commit
R=w.R;PUBLIC=R/'reports/stage04a';STAGING=R/'release_staging/stage04a'
w.LOG=PUBLIC/'publication_commands_resume.jsonl'

def main():
    with C.WorkflowLock(R/'.work/workflow.lock'):
        C.reconcile(R)
        manifest=C.load(PUBLIC/'asset_manifest.json')
        C.check(manifest['scientific_validation']=='PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' and
                manifest['whole_stage04_phylogeny']=='NOT_COMPLETED' and
                manifest['alignment_validation_sha256']==C.digest(R/'.work/stage04_alignment_validation/validation_summary.json'),
                'Frozen alignment substage gate differs')
        paths=C.load(STAGING/'payload_paths.json')
        receipt=publish_frozen('stage04a','stage04a-hostalignments196-v1',STAGING,PUBLIC/'asset_manifest.json',paths,
                  'Stage04a: independently validated full196 alignments; phylogeny pending',PUBLIC/'RELEASE_NOTES.md')
        receipt.update(approved_assemblies=196,scientific_validation=manifest['scientific_validation'],
                       whole_stage04_phylogeny='NOT_COMPLETED',alignment_validation_sha256=manifest['alignment_validation_sha256'])
        w.js(PUBLIC/'publication_receipt.json',receipt)
        selected=[]
        for line in (R/'reports/stage00/commands.jsonl').read_text(encoding='utf-8').splitlines():
            row=json.loads(line)
            if any('stage04a' in str(arg) for arg in row.get('argv',[])):selected.append(row)
        w.atomic(PUBLIC/'original_publication_commands.jsonl',(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected)).encode())
        w.atomic(PUBLIC/'RESUMED_PUBLICATION.md',(
            '# Stage04a publication receipt recovery\n\n'
            'The original publisher verified both ZIPs and sidecars, then its final receipt commit failed because it expected a stage-specific commands file that had not been configured. Actual command records had appended to the existing mutable Stage00 log, which is preserved locally unchanged. This report selects only Stage04a command records; no private session events are used.\n\n'
            'This new resumed task configures a separate Stage04a command log and rechecks the unchanged immutable plan/tag/assets before committing the verified receipt. No ZIP, scientific payload, alignment, filter or historical commit is rewritten. Whole Stage4 phylogeny remains incomplete.\n').encode())
        print(commit(['scripts/complete_stage04a_receipt.py','reports/stage04a/publication_receipt.json',
                      'reports/stage04a/publication_progress.json','reports/stage04a/publication_commands_resume.jsonl',
                      'reports/stage04a/original_publication_commands.jsonl','reports/stage04a/RESUMED_PUBLICATION.md'],
                     'Recover verified alignment substage receipt without rewriting frozen payload'))
        print('STAGE04A_PORTABLE_BYTES_AND_REMOTE_RECEIPT_VERIFIED',flush=True)
if __name__=='__main__':main()
