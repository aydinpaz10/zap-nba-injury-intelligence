"""Post-evaluation paired uncertainty only; never train or change score/winner forecasts.

Each observation is a whole game (both predicted team scores travel together).
Circular moving blocks resample calendar dates, preserving all games on each date
and short-range temporal dependence. Seven-day primary and 14-day sensitivity
are fixed before computing intervals. --verify recomputes without writing.
"""
import gzip
import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPLICATES = 20000
BLOCK_LENGTHS = (7, 14)
SEED_BASE = 20261022


def calculate():
    source = ROOT / 'data/score-features-v1.jsonl.gz'
    report = json.loads((ROOT / 'data/score-model-report-v1.json').read_text())
    raw = source.read_bytes()
    rows = [json.loads(line) for line in gzip.decompress(raw).decode().splitlines()]
    rows = [r for r in rows if r['season'] == 2026]
    assert len(rows) == 1230
    assert len({r['id'] for r in rows}) == len(rows)
    assert all(r['cutoff_day'] is None or r['cutoff_day'] < r['day'] for r in rows)
    # Freeze/check both the evaluated score method and the prior winner artifacts.
    preserved = {name: hashlib.sha256((ROOT / 'data' / name).read_bytes()).hexdigest()
                 for name in ['score-engine-v1.json', 'score-model-report-v1.json',
                              'score-features-v1.jsonl.gz', *report['winner_file_hashes']]}
    assert all(preserved[name] == digest for name, digest in report['winner_file_hashes'].items())
    actual = np.array([[r['actual_home'], r['actual_away']] for r in rows], dtype=float)
    model = np.array([[r['predicted_home'], r['predicted_away']] for r in rows], dtype=float)
    baseline = np.maximum(0, np.floor(np.array([[r['baseline_home'], r['baseline_away']]
                                               for r in rows]) + .5))
    errors = {}
    for name, prediction in [('model', model), ('baseline', baseline)]:
        errors[name] = np.column_stack([
            np.abs(prediction - actual).mean(axis=1),
            np.abs((prediction[:, 0] - prediction[:, 1]) - (actual[:, 0] - actual[:, 1]))])
        assert np.isclose(errors[name][:, 0].mean(), report['evaluation'][name]['team_score_mae'], atol=1e-12)
        assert np.isclose(errors[name][:, 1].mean(), report['evaluation'][name]['winning_margin_mae'], atol=1e-12)
    differences = errors['model'] - errors['baseline']
    start = date.fromisoformat(min(r['day'] for r in rows))
    end = date.fromisoformat(max(r['day'] for r in rows))
    span = (end - start).days + 1
    sums = np.zeros((span, 2))
    counts = np.zeros(span, dtype=int)
    for row, difference in zip(rows, differences):
        index = (date.fromisoformat(row['day']) - start).days
        sums[index] += difference
        counts[index] += 1
    results = {}
    for length in BLOCK_LENGTHS:
        rng = np.random.default_rng(SEED_BASE + length)
        values = []
        for _ in range(REPLICATES):
            starts = rng.integers(0, span, size=math.ceil(span / length))
            sampled_days = ((starts[:, None] + np.arange(length)) % span).ravel()[:span]
            denominator = counts[sampled_days].sum()
            assert denominator > 0
            values.append(sums[sampled_days].sum(axis=0) / denominator)
        values = np.array(values)
        stats = {}
        for column, name in enumerate(['team_score_mae', 'winning_margin_mae']):
            difference = float(differences[:, column].mean())
            interval = np.quantile(values[:, column], [.025, .975]).tolist()
            p = float((1 + np.sum(np.abs(values[:, column] - difference) >= abs(difference))) / (REPLICATES + 1))
            stats[name] = {
                'baseline': float(errors['baseline'][:, column].mean()),
                'model': float(errors['model'][:, column].mean()),
                'model_minus_baseline': difference,
                'ci_95': interval,
                'centered_bootstrap_two_sided_p': p,
                'interval_includes_zero': bool(interval[0] <= 0 <= interval[1])}
        results[str(length) + '_calendar_day_blocks'] = stats
    output = {
        'version': 'zap-score-v1-paired-uncertainty',
        'score_model_version': report['version'],
        'games': len(rows), 'team_scores': 2 * len(rows),
        'evaluation_season': '2025-26', 'date_range': [start.isoformat(), end.isoformat()],
        'evaluation_disclosure': '2025-26 had already been inspected for winner evaluation and sign audits. Score comparisons and intervals are exploratory, not a new untouched holdout. No refitting or selection uses these intervals.',
        'method': 'Paired circular moving-block bootstrap of calendar dates. Both teams stay in each game; all games on a sampled date stay together. Resample the full calendar span including off-days and divide summed paired game errors by sampled game count. Team MAE is the mean of the two absolute team errors within each game; margin MAE is one absolute signed-margin error per game.',
        'primary_block_days': 7, 'sensitivity_block_days': 14,
        'replicates': REPLICATES, 'seed_rule': '20261022 + block_length',
        'interval': 'Percentile 95%; approximate centered two-sided bootstrap p-values; no multiplicity correction.',
        'difference_direction': 'Model minus baseline; negative favors score model. Units are points.',
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'preserved_artifact_hashes': preserved,
        'results': results,
        'limitations': [
            'Conditional on fitted models and one previously inspected season; intervals omit model-selection and training uncertainty.',
            'Seven- and 14-day blocks address local temporal dependence but may not capture longer season effects or all shared-team dependence.',
            'No official historical injury designations; historical availability is a lagged participation proxy, not confirmed injury.',
            'Live official overrides have not been separately score-validated.'],
        'conclusion': 'Percentile intervals exclude zero at both block lengths for both errors, conditional on this exploratory season and fixed models. Team-score MAE is borderline: the 14-day approximate centered bootstrap p-value is 0.05345, so its conclusion is sensitive to interval/test construction. Margin-MAE evidence is stronger within this season. The gains are small and do not establish a new untouched prospective edge.'}
    assert all(hashlib.sha256((ROOT / 'data' / name).read_bytes()).hexdigest() == digest
               for name, digest in preserved.items())
    return output


if __name__ == '__main__':
    output = calculate()
    target = ROOT / 'data/score-uncertainty-v1.json'
    if '--verify' in sys.argv:
        assert json.loads(target.read_text()) == output, 'Saved uncertainty differs from deterministic replay'
        print('Verified: exact deterministic replay, 1,230 whole-game pairs; frozen artifacts unchanged.')
    else:
        target.write_text(json.dumps(output, indent=2) + '\n')
        print(json.dumps(output['results'], indent=2))
