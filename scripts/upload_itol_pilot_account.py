#!/usr/bin/env python3
"""Upload a validated five-marker pilot; use itolapi for checked SVG/PDF exports."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import quote, quote_plus
from xml.etree import ElementTree
import zipfile
import requests
from itolapi import ItolExport

UPLOAD = 'https://itol.embl.de/batch_uploader.cgi'
EXPORT = 'https://itol.embl.de/batch_downloader.cgi'


class CheckedExport:
    """Bound the toolkit transport and validate bytes before its file writer runs."""
    def export_image(self, params):
        response = requests.post(EXPORT, data=params, timeout=(30, 300), allow_redirects=False)
        if response.status_code != 200:
            raise ValueError(f'Export HTTP {response.status_code}')
        content = response.content
        if params['format'] == 'pdf':
            if not content.startswith(b'%PDF-') or b'%%EOF' not in content[-4096:]:
                raise ValueError('Invalid PDF export response')
        elif ElementTree.fromstring(content).tag not in {'svg', '{http://www.w3.org/2000/svg}svg'}:
            raise ValueError('Invalid SVG export response')
        return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    project = args.project.resolve()
    report_dir = project / 'reports/stage01/local_pilot_20261010/completed'
    report = json.loads((report_dir / 'validation_report.json').read_text())
    if report['status'] != 'PASS' or len(report['marker_results']) != 5 or report['astral_result']['tip_count'] != 196:
        raise ValueError('A completed validated five-marker,196-tip pilot is required')
    raw = (project / 'pilot_output/species_tree.newick').read_bytes()
    flat = (project / 'pilot_output/species_tree.itol_quartet_frequency.newick').read_bytes()
    for name, data in [('species_tree.newick', raw), ('species_tree.itol_quartet_frequency.newick', flat)]:
        if hashlib.sha256(data).hexdigest() != report['artifact_sha256'][name]:
            raise ValueError('Pilot tree differs from validation receipt: ' + name)
    out = project / 'pilot_output/itol'
    if out.exists() or out.is_symlink():
        raise FileExistsError('Refusing existing pilot upload directory; preserve prior evidence')
    # The user's local file contains username on line 1 and API key on line 2.
    # Also accept the original single-token format; never log either value.
    with open('/mnt/c/itol.api-key.txt', encoding='utf-8-sig') as handle:
        credential_lines = handle.read().splitlines()
    if len(credential_lines) not in (1, 2) or any(not line.strip() for line in credential_lines):
        raise ValueError('Expected one token line, or username then token on two lines')
    key = credential_lines[-1].strip()
    if any(c.isspace() for c in key):
        raise ValueError('The iTOL token line contains internal whitespace')
    out.mkdir()
    receipt = {'state': 'PREPARED', 'scope': 'pilot_5_markers_196_taxa', 'real_defense_host_datasets': False,
               'raw_tree_sha256': hashlib.sha256(raw).hexdigest(),
               'uploaded_flat_q1_sha256': hashlib.sha256(flat).hexdigest(),
               'toolkit': 'itolapi==4.1.6', 'tree_url': None, 'exports': {}}
    try:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('pilot_5_markers_196_taxa.tree', flat)
        package = buffer.getvalue()
        with (out / 'upload.zip').open('xb') as handle:
            handle.write(package)
        receipt['zip_sha256'] = hashlib.sha256(package).hexdigest()
        receipt['state'] = 'UPLOAD_REQUEST_STARTED'
        response = requests.post(UPLOAD,
            data={'APIkey': key, 'projectName': 'LAB_Phylogenomics_196',
                  'treeName': 'Pilot_5_Markers_196_Taxa',
                  'treeDescription': 'Validated local five-marker MAFFT/IQ-TREE/ASTRAL pilot.196 taxa. Numeric internal labels are q1 quartet frequencies. Host/defense data pending. This is a workflow pilot, not the full100-marker analysis.'},
            files={'zipFile': ('pilot.zip', package, 'application/zip')},
            timeout=(30, 300), allow_redirects=False)
        clean = response.text
        for secret in {key, quote(key, safe=''), quote_plus(key, safe='')}:
            clean = clean.replace(secret, '[REDACTED]')
        with (out / 'upload_response.txt').open('x', encoding='utf-8') as handle:
            handle.write(clean)
        if response.status_code != 200:
            raise ValueError(f'Upload HTTP {response.status_code}')
        lines = [line.strip() for line in clean.splitlines() if line.strip()]
        if any(line.startswith('ERR') for line in lines):
            raise ValueError(' | '.join(lines)[:1500])
        success = re.fullmatch(r'SUCCESS:\s*(\d+)', lines[-1]) if lines else None
        if success is None:
            raise ValueError('No valid iTOL SUCCESS record; do not automatically retry')
        tree_id = success.group(1)
        receipt['tree_url'] = 'https://itol.embl.de/tree/' + tree_id
        receipt['state'] = 'UPLOADED_EXPORT_PENDING'
        with (out / 'tree_url.txt').open('x', encoding='utf-8') as handle:
            handle.write(receipt['tree_url'] + '\n')
        print(receipt['tree_url'], flush=True)
        for line in lines[:-1]:
            print(line, file=sys.stderr)
        for extension in ('svg', 'pdf'):
            time.sleep(3)
            exporter = ItolExport()
            exporter.add_export_param_dict({'tree': tree_id, 'format': extension,
                                           'display_mode': '2', 'label_display': '1'})
            exporter.comm = CheckedExport()
            path = out / ('pilot_species_tree.circular.' + extension)
            if path.exists():
                raise FileExistsError('Refusing existing export file')
            exporter.export(path)
            data = path.read_bytes()
            receipt['exports'][path.name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        receipt['state'] = 'UPLOAD_AND_EXPORTS_COMPLETE'
        return 0
    except requests.RequestException as error:
        receipt['error'] = 'Network exception: ' + type(error).__name__
        print(receipt['error'] + '; no automatic retry', file=sys.stderr)
        return 1
    except (OSError, ValueError, ElementTree.ParseError) as error:
        receipt['error'] = str(error)
        print('iTOL: ' + str(error), file=sys.stderr)
        return 1
    finally:
        with (out / 'terminal.json').open('x', encoding='utf-8') as handle:
            json.dump(receipt, handle, indent=2)
            handle.write('\n')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print('Pilot iTOL preflight: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
