#!/usr/bin/env python3
"""Independent completed IQ-TREE locus audit; reads science files, writes only to --out."""
import argparse, csv, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fasta(path):
    records, errors, header, chunks = {}, [], None, []
    def finish():
        if header is None: return
        seq = ''.join(chunks).upper()
        if not seq: errors.append(f'{path.name}: empty sequence: {header}')
        if header in records: errors.append(f'{path.name}: duplicate ID: {header}')
        else: records[header] = seq
    with path.open(encoding='utf-8') as f:
        for n, raw in enumerate(f, 1):
            s = raw.strip()
            if not s: continue
            if s.startswith('>'):
                finish(); parts = s[1:].split(); header = parts[0] if parts else ''; chunks = []
                if not header: errors.append(f'{path.name}:{n}: empty ID')
            elif header is None: errors.append(f'{path.name}:{n}: sequence before header')
            else: chunks.append(''.join(s.split()))
    finish()
    return records, errors


def label(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'": return text[1:-1].replace("''", "'")
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"': return text[1:-1].replace('""', '"')
    return text


def parse_newick(path):
    s = path.read_text(encoding='utf-8').strip()
    tokens, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace(): i += 1; continue
        if c == '[':
            depth = 1; i += 1
            while i < len(s) and depth:
                if s[i] == '[': depth += 1
                elif s[i] == ']': depth -= 1
                i += 1
            if depth: raise ValueError(f'{path.name}: unclosed comment')
            continue
        if c in '(),:;': tokens.append(c); i += 1; continue
        if c in "'\"":
            q = c; i += 1; out = ''
            while i < len(s):
                if s[i] == q:
                    if i + 1 < len(s) and s[i+1] == q: out += q; i += 2; continue
                    i += 1; break
                out += s[i]; i += 1
            tokens.append(('label', out)); continue
        j = i
        while i < len(s) and not s[i].isspace() and s[i] not in '(),:;[]': i += 1
        if i == j: raise ValueError(f'{path.name}: unexpected character at {i}')
        tokens.append(('label', s[j:i]))
    pos, leaves, supports = 0, [], []
    def take(expected=None):
        nonlocal pos
        if pos >= len(tokens): raise ValueError(f'{path.name}: unexpected end')
        t = tokens[pos]; pos += 1
        if expected is not None and t != expected: raise ValueError(f'{path.name}: expected {expected}, got {t}')
        return t
    def node():
        nonlocal pos
        internal = False
        if pos < len(tokens) and tokens[pos] == '(':
            internal = True; take('('); node()
            while pos < len(tokens) and tokens[pos] == ',': take(','); node()
            take(')')
        else:
            if pos >= len(tokens) or not (isinstance(tokens[pos], tuple) and tokens[pos][0] == 'label'):
                raise ValueError(f'{path.name}: missing leaf label')
            leaves.append(tokens[pos][1]); pos += 1
        support = None
        if pos < len(tokens) and isinstance(tokens[pos], tuple) and tokens[pos][0] == 'label':
            support = tokens[pos][1]; pos += 1
        if internal: supports.append(support)
        if pos < len(tokens) and tokens[pos] == ':':
            take(':')
            if pos >= len(tokens) or not (isinstance(tokens[pos], tuple) and tokens[pos][0] == 'label'):
                raise ValueError(f'{path.name}: missing branch length')
            try: float(tokens[pos][1])
            except ValueError: raise ValueError(f'{path.name}: nonnumeric branch length {tokens[pos][1]}')
            pos += 1
    node()
    if pos < len(tokens) and tokens[pos] == ';': take(';')
    if pos != len(tokens): raise ValueError(f'{path.name}: trailing tokens')
    numeric, invalid = [], []
    for x in supports:
        if x is None or x == '': continue
        try: v = float(x)
        except ValueError: invalid.append(x); continue
        if not 0 <= v <= 100: invalid.append(x)
        else: numeric.append(v)
    return {'leaves': leaves, 'internal_nodes': len(supports), 'unlabeled_internal_nodes': sum(x is None or x == '' for x in supports),
            'numeric_support_count': len(numeric), 'support_min': min(numeric) if numeric else None,
            'support_max': max(numeric) if numeric else None, 'invalid_support_labels': invalid}


def parse_phylip(path):
    lines = [x.strip() for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
    head = lines[0].split()
    if len(head) < 2: raise ValueError(f'{path.name}: malformed PHYLIP dimensions')
    ntax, nchar = int(head[0]), int(head[1]); records = {}
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 2: raise ValueError(f'{path.name}: malformed sequence row {line[:50]}')
        name, seq = parts[0], ''.join(parts[1:]).upper()
        if name in records: raise ValueError(f'{path.name}: duplicate taxon {name}')
        records[name] = seq
    if len(records) != ntax: raise ValueError(f'{path.name}: dimensions declare {ntax} taxa, parsed {len(records)}')
    if any(len(x) != nchar for x in records.values()): raise ValueError(f'{path.name}: sequence length differs from declared {nchar}')
    return ntax, nchar, records


def parse_splits(path):
    text = path.read_text(encoding='utf-8')
    m = re.search(r'DIMENSIONS\s+ntax\s*=\s*(\d+)\s+nsplits\s*=\s*(\d+)', text, re.I)
    if not m: raise ValueError(f'{path.name}: missing ntax/nsplits')
    ntax, nsplits = map(int, m.groups())
    taxa_block = re.search(r'TAXLABELS\s+(.*?)\s*;', text, re.I | re.S)
    if not taxa_block: raise ValueError(f'{path.name}: missing TAXLABELS')
    taxa = re.findall(r"\[\d+\]\s+'((?:''|[^'])*)'", taxa_block.group(1))
    taxa = [x.replace("''", "'") for x in taxa]
    matrix = re.search(r'MATRIX\s+(.*?)\s*;', text, re.I | re.S)
    if not matrix: raise ValueError(f'{path.name}: missing split MATRIX')
    values = []
    for line in matrix.group(1).splitlines():
        t = line.strip()
        if not t: continue
        first = t.split()[0]
        try: value = float(first)
        except ValueError: raise ValueError(f'{path.name}: nonnumeric split support {first}')
        if not 0 <= value <= 100: raise ValueError(f'{path.name}: split support outside 0..100: {value}')
        values.append(value)
    if len(taxa) != ntax: raise ValueError(f'{path.name}: declared ntax={ntax}, parsed {len(taxa)} labels')
    if len(values) != nsplits: raise ValueError(f'{path.name}: declared nsplits={nsplits}, parsed {len(values)} supports')
    return {'ntax': ntax, 'nsplits': nsplits, 'taxa': taxa, 'support_count': len(values), 'support_min': min(values) if values else None, 'support_max': max(values) if values else None}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--marker', required=True)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--alignment-manifest', required=True, type=Path)
    a = p.parse_args(); started = datetime.now(timezone.utc).isoformat()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', a.marker): p.error('unsafe marker name')
    a.out.mkdir(parents=True, exist_ok=True)
    root = a.root; gene = a.marker
    input_path = root / 'input_genes' / f'{gene}.fasta'
    alignment_path = root / 'pipeline_output' / 'alignments' / f'{gene}_aligned.fasta'
    tree_dir = root / 'pipeline_output' / 'trees'
    prefix = tree_dir / gene
    accepted = {}
    with a.alignment_manifest.open('r', encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row.get('marker') == gene: accepted = row; break
    errors = []
    if not accepted: errors.append('marker absent from accepted alignment manifest')
    watched = [input_path, alignment_path] + sorted(tree_dir.glob(gene + '.*'))
    before = {str(x): {'sha256': sha256(x), 'bytes': x.stat().st_size, 'mtime_ns': x.stat().st_mtime_ns} for x in watched if x.is_file()}
    required_exts = ['.treefile', '.contree', '.splits.nex', '.log', '.iqtree', '.uniqueseq.phy']
    for ext in required_exts:
        if not (tree_dir / (gene + ext)).is_file(): errors.append(f'missing required output {gene+ext}')
    input_records, input_errors = fasta(input_path); aligned_records, aligned_errors = fasta(alignment_path)
    errors.extend(input_errors); errors.extend(aligned_errors)
    ids = set(input_records); aligned_ids = set(aligned_records)
    if ids != aligned_ids: errors.append(f'input/alignment ID mismatch missing={sorted(ids-aligned_ids)[:20]} extra={sorted(aligned_ids-ids)[:20]}')
    if len(ids) != len(input_records): errors.append('input ID count mismatch')
    approved = {x.strip() for x in (root / 'config' / 'approved_accessions.txt').read_text(encoding='utf-8').splitlines() if x.strip()}
    if not ids <= approved: errors.append(f'unapproved IDs: {sorted(ids-approved)[:20]}')
    lengths = {len(x) for x in aligned_records.values()}
    if len(lengths) != 1: errors.append(f'alignment has unequal sequence lengths: {sorted(lengths)}')
    for taxon in ids & aligned_ids:
        if aligned_records[taxon].replace('-', '') != input_records[taxon]: errors.append(f'{taxon}: aligned sequence ungapped differs from input')
    if accepted:
        ih, ah = sha256(input_path), sha256(alignment_path)
        if ih != accepted['input_sha256_before']: errors.append('input SHA-256 differs from accepted all-locus alignment audit')
        if ah != accepted['alignment_sha256_before']: errors.append('alignment SHA-256 differs from accepted all-locus alignment audit')
    unique = parse_phylip(tree_dir / (gene + '.uniqueseq.phy'))
    unique_ntax, unique_nchar, unique_records = unique
    aligned_unique = set(aligned_records.values())
    unique_seq_set = set(unique_records.values())
    if unique_ntax != len(unique_records): errors.append('uniqueseq taxa count mismatch')
    if unique_seq_set != aligned_unique: errors.append('IQ-TREE uniqueseq.phy sequence set differs from unique sequences in published alignment')
    if set(unique_records) - ids: errors.append('uniqueseq.phy has representative IDs absent from alignment')
    tree_results = {}
    for ext in ['.treefile', '.contree']:
        r = parse_newick(tree_dir / (gene + ext)); leaves = r['leaves']
        dup = sorted({x for x in leaves if leaves.count(x) > 1})
        missing, extra = sorted(ids-set(leaves)), sorted(set(leaves)-ids)
        r.update({'taxa_count': len(leaves), 'unique_taxa_count': len(set(leaves)), 'duplicate_taxa': dup, 'missing_taxa': missing, 'extra_taxa': extra})
        if dup or missing or extra or len(leaves) != len(ids): errors.append(f'{gene+ext}: expected exact {len(ids)} input taxa; observed {len(leaves)} leaves, missing={missing[:10]}, extra={extra[:10]}, duplicates={dup[:10]}')
        if r['invalid_support_labels']: errors.append(f'{gene+ext}: invalid/non-numeric or out-of-range support labels {r["invalid_support_labels"][:20]}')
        tree_results[ext[1:]] = r
    split = parse_splits(tree_dir / (gene + '.splits.nex'))
    if set(split['taxa']) != set(unique_records) or len(split['taxa']) != len(set(split['taxa'])):
        errors.append('splits.nex taxon set differs from IQ-TREE unique-sequence representatives')
    if split['ntax'] != unique_ntax: errors.append('splits.nex ntax differs from uniqueseq.phy (expected identical-sequence reduction)')
    iqpath, logpath = tree_dir/(gene+'.iqtree'), tree_dir/(gene+'.log')
    iqtxt, logtxt = iqpath.read_text(encoding='utf-8', errors='replace'), logpath.read_text(encoding='utf-8', errors='replace')
    if f'{len(ids)} sequences' not in iqtxt: errors.append('IQ-TREE report does not state expected input sequence count')
    m = re.search(r'Consensus tree is constructed from\s+(\d+) bootstrap trees', iqtxt)
    generated_trees = int(m.group(1)) if m else None
    if generated_trees is None: errors.append('IQ-TREE report lacks actual consensus bootstrap-tree count')
    mt = re.search(r'ultrafast bootstrap \((\d+) replicates\)', iqtxt, re.I)
    requested = int(mt.group(1)) if mt else None
    if requested != 1000: errors.append(f'IQ-TREE report requested UFBoot count expected 1000, observed {requested}')
    if 'TREE SEARCH COMPLETED' not in logtxt or 'Analysis results written to:' not in logtxt: errors.append('native IQ-TREE log lacks completion/output-write receipts')
    dt = re.search(r'Date and Time:\s*(.+)', logtxt)
    date_time = dt.group(1).strip() if dt else None
    if not date_time: errors.append('native IQ-TREE log lacks completion date/time')
    warn_lines = []
    iq_lines = iqtxt.splitlines()
    i = 0
    while i < len(iq_lines):
        if '**************************** WARNING ****************************' in iq_lines[i]:
            block = [iq_lines[i]]; i += 1
            while i < len(iq_lines):
                block.append(iq_lines[i])
                if '************************ END OF WARNING ***********************' in iq_lines[i]: break
                i += 1
            warn_lines.extend(block)
        elif 'WARNING:' in iq_lines[i]: warn_lines.append(iq_lines[i])
        i += 1
    (a.out/'native_warnings.txt').write_text(('\n'.join(warn_lines)+'\n') if warn_lines else 'No native IQ-TREE warning lines found.\n', encoding='utf-8')
    after_paths = [input_path, alignment_path] + sorted(tree_dir.glob(gene + '.*'))
    after = {str(x): {'sha256': sha256(x), 'bytes': x.stat().st_size, 'mtime_ns': x.stat().st_mtime_ns} for x in after_paths if x.is_file()}
    if set(before) != set(after): errors.append('marker file set changed during audit')
    for path in set(before) & set(after):
        if before[path] != after[path]: errors.append(f'file changed during audit: {Path(path).name}')
    file_rows = []
    for path in sorted(set(before) | set(after)):
        b, e = before.get(path, {}), after.get(path, {})
        file_rows.append((Path(path).name, b.get('bytes'), b.get('sha256'), e.get('bytes'), e.get('sha256'), b == e and bool(b)))
    with (a.out/'file_manifest.tsv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n'); w.writerow(['filename','bytes_before','sha256_before','bytes_after','sha256_after','stable'])
        w.writerows(file_rows)
    result = {
        'audit': 'completed_iqtree_locus_independent_validation', 'marker': gene, 'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'state': 'PASS' if not errors else 'FAIL', 'errors': errors,
        'accepted_alignment_manifest_row': accepted, 'expected_alignment_sha256': accepted.get('alignment_sha256_before') if accepted else None,
        'observed_input_sha256': sha256(input_path), 'observed_alignment_sha256': sha256(alignment_path),
        'input_records': len(input_records), 'alignment_records': len(aligned_records), 'alignment_columns': next(iter(lengths)) if len(lengths)==1 else None,
        'input_alignment_ids_exact': ids == aligned_ids, 'all_ids_approved': ids <= approved,
        'ungapped_alignment_sequences_exact': True if not any('ungapped differs' in e for e in errors) else False,
        'iqtree_tree_taxa_expected': len(ids), 'tree_outputs': tree_results,
        'iqtree_unique_sequence_reduction': {'unique_taxa': unique_ntax, 'alignment_distinct_sequences': len(aligned_unique), 'uniqueseq_sequence_set_exact': unique_seq_set == aligned_unique, 'splits_taxa': split['ntax'], 'splits_count': split['nsplits'], 'splits_support_min': split['support_min'], 'splits_support_max': split['support_max']},
        'bootstrap': {'requested_ufboot_replicates': requested, 'bootstrap_trees_in_consensus_report': generated_trees, 'source': 'IQ-TREE .iqtree Type of analysis and consensus summary'},
        'native_completion_datetime': date_time, 'native_log_completed': 'TREE SEARCH COMPLETED' in logtxt and 'Analysis results written to:' in logtxt,
        'native_warning_excerpt_file': 'native_warnings.txt', 'marker_file_set_stable_before_after': set(before)==set(after) and all(before.get(k)==after.get(k) for k in set(before)&set(after)),
        'file_count_stable': len(before), 'execution_source': 'audit_completed_locus.py'
    }
    (a.out/'audit.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1

if __name__ == '__main__': sys.exit(main())
