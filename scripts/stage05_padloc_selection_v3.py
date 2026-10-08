"""Coordinate-aware PADLOC2 domain selection; preparation only until adopted.

The installed detector groups by replicon/start/end, irrespective of strand or
locus tag. Exact source locus keys remain the identifiers of retained raw hits.
No clustering, architecture classification or functional claim occurs here.
"""
from collections import defaultdict
import math

PINNED_NATIVE_SOURCE_SHA256 = 'd21ba942e80720d80027aa1740d756322560feaeb168bfa2890640d88950d4c0'
ROLE_CLASSES = {'core_genes', 'secondary_genes', 'neutral_genes', 'prohibited_genes'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value, name):
    require(not isinstance(value, bool), 'Boolean is not a ' + name)
    number = int(value)
    require(str(number) == str(value), 'Noncanonical integer ' + name)
    return number


def geometry(key, source):
    parts = key.split('|')
    require(len(parts) == 3 and all(parts), 'Exact assembly|replicon|locus required')
    require(source['assembly_accession'] == parts[0] and source['replicon'] == parts[1]
            and source['locus_tag'] == parts[2], 'Source locus identity differs')
    lo = integer(source['derived_linear_order_start_one_based'], 'source start')
    hi = integer(source['derived_linear_order_end_one_based'], 'source end')
    require(1 <= lo <= hi, 'Invalid source linear-order geometry')
    return parts[0], parts[1], lo, hi


def effective_priority(classes):
    require(classes and classes <= ROLE_CLASSES, 'Unknown/empty PADLOC role class')
    # Native alias expansion is followed by set differences: core wins all;
    # prohibited removes secondary/neutral; secondary removes neutral.
    if 'core_genes' in classes:
        return 4
    if 'prohibited_genes' in classes:
        return 1
    if 'secondary_genes' in classes:
        return 3
    return 2


def numeric(hit):
    domain = hit['domain']
    require(domain['profile_name'] == hit['profile_name'], 'Native profile identity differs')
    ie = float(domain['independent_evalue'])
    require(math.isfinite(ie) and ie >= 0, 'Invalid native domain E value')
    hlen = integer(domain['profile_length'], 'profile length')
    tlen = integer(hit['target_length'], 'target length')
    hlo, hhi = (integer(domain[k], k) for k in ('hmm_from', 'hmm_to'))
    alo, ahi = (integer(domain[k], k) for k in ('alignment_from', 'alignment_to'))
    require(1 <= hlo <= hhi <= hlen and 1 <= alo <= ahi <= tlen,
            'Native domain bounds differ')
    # PADLOC calculates this sum before rounding the two individual coverages.
    combined = (hhi - hlo) / hlen + (ahi - alo) / tlen
    return ie, combined


def padloc_selection_facts(hits, sources):
    """Annotate all raw hits with exact per-model native domain eligibility."""
    groups = defaultdict(list)
    numbers = {}
    for index, (hid, hit) in enumerate(hits.items()):
        if hit['detector'] != 'PADLOC':
            continue
        key = hit['locus_key']
        require(key in sources, 'PADLOC hit has no exact source locus')
        coordinates = geometry(key, sources[key])
        require(hit['domain']['target_name'] == key, 'Native target/source locus differs')
        numbers[hid] = numeric(hit)
        passed = hit['native_role_threshold_passed']
        require(type(passed) is bool, 'Native numerical eligibility must be boolean')
        hit['native_numerical_domain_filter_passed'] = passed
        hit['native_selected_model_ids'] = []
        roles = defaultdict(set)
        for assignment in hit['native_model_roles']:
            require(isinstance(assignment['model'], str) and assignment['model'], 'Empty native model')
            roles[assignment['model']].add(assignment['role_class'])
        for model, classes in roles.items():
            groups[(model, *coordinates)].append((hid, effective_priority(classes), index))
    for (model, *_), members in groups.items():
        minima = {}
        for hid, _, _ in members:
            profile = hits[hid]['profile_name']
            minima[profile] = min(minima.get(profile, numbers[hid][0]), numbers[hid][0])
        best = [row for row in members if numbers[row[0]][0] == minima[hits[row[0]]['profile_name']]]
        cutoff = sorted(numbers[row[0]][0] for row in best)[min(4, len(best) - 1)]
        eligible = [row for row in best if numbers[row[0]][0] <= cutoff
                    and hits[row[0]]['native_numerical_domain_filter_passed']]
        if eligible:
            winner = min(eligible, key=lambda row: (-row[1], numbers[row[0]][0], -numbers[row[0]][1], row[2]))
            hits[winner[0]]['native_selected_model_ids'].append(model)
    for hit in hits.values():
        if hit['detector'] == 'PADLOC':
            hit['native_selected_model_ids'].sort()
            hit['native_role_threshold_passed'] = hit['native_numerical_domain_filter_passed'] and bool(hit['native_selected_model_ids'])
            hit['native_filter_basis'] = ('Pinned PADLOC2 per-model replicon/start/end groups; minimum-iE domains and top5 with ties before numerical filters; '
                                          'native alias-overlap role precedence; iE, unrounded combined coverage, stable domain order. Architecture not inferred.')
    return hits
