"""Regenerate both SVG themes and summary tables from one measurement directory."""
import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
LABELS = {(1, 1): 'Sequential', (2, 1): 'OpenMP, 1 thread', (2, 2): 'OpenMP, 2 threads', (2, 4): 'OpenMP, 4 threads'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Directory containing samples.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/assets')
    parser.add_argument('--preview-dir', type=Path, help='Optional PNG previews for visual review')
    args = parser.parse_args()
    samples = defaultdict(list)
    with (args.input / 'samples.csv').open() as source:
        for row in csv.DictReader(source):
            if row['phase'] == 'measured':
                if row['valid'] != 'True':
                    raise ValueError('Invalid ruler in measurement data')
                samples[(int(row['order']), int(row['version']), int(row['threads']))].append(float(row['time_ms']))
    if not samples:
        raise ValueError('No measured samples')
    expected = {(order, version, threads) for order in (8, 9, 10) for version, threads in LABELS}
    if set(samples) != expected:
        raise ValueError('Expected all G8/G9/G10 sequential and OpenMP configurations')
    summary = []
    for (order, version, threads), values in sorted(samples.items()):
        if len(values) != 5:
            raise ValueError(f'Expected five measured samples for G{order} v{version} t{threads}')
        q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive')
        median = statistics.median(values)
        baseline = statistics.median(samples[(order, 1, 1)])
        summary.append({'order': order, 'version': version, 'threads': threads, 'repetitions': len(values),
                        'median_ms': median, 'q1_ms': q1, 'q3_ms': q3, 'iqr_ms': q3 - q1,
                        'speedup_vs_v1': baseline / median})
    (args.input / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    table = ['| Order | Configuration | Median (ms) | Q1 to Q3 (ms) | Ratio vs sequential |',
             '|---|---|---:|---:|---:|']
    for row in summary:
        table.append(f'| G{row["order"]} | {LABELS[(row["version"], row["threads"])]} | {row["median_ms"]:.2f} | {row["q1_ms"]:.2f} to {row["q3_ms"]:.2f} | {row["speedup_vs_v1"]:.2f} |')
    (args.input / 'table.md').write_text('\n'.join(table) + '\n')
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.hashsalt': 'golomb-local', 'svg.fonttype': 'none'})
    for theme, background, foreground in [('light', '#ffffff', '#202830'), ('dark', '#0d1117', '#e6edf3')]:
        colors = ['#0072B2', '#D55E00', '#009E73', '#8F62A5'] if theme == 'light' else ['#56B4E9', '#E69F00', '#55C79F', '#CC79A7']
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), layout='constrained', facecolor=background)
        for ax in axes:
            ax.set_facecolor(background)
            ax.tick_params(colors=foreground)
            ax.xaxis.label.set_color(foreground)
            ax.yaxis.label.set_color(foreground)
            ax.set_xlabel('Ruler order (marks)')
            ax.set_xticks(sorted({row['order'] for row in summary}))
            for side in ('top', 'right'):
                ax.spines[side].set_visible(False)
            for side in ('bottom', 'left'):
                ax.spines[side].set_color(foreground)
        for index, ((version, threads), label) in enumerate(LABELS.items()):
            rows = [row for row in summary if (row['version'], row['threads']) == (version, threads)]
            x = [row['order'] for row in rows]
            y = [row['median_ms'] for row in rows]
            errors = [[row['median_ms'] - row['q1_ms'] for row in rows], [row['q3_ms'] - row['median_ms'] for row in rows]]
            axes[0].errorbar(x, y, yerr=errors, marker=['o', 's', '^', 'D'][index], linestyle=['-', '--', '-.', ':'][index], color=colors[index], capsize=3, label=label)
            if version == 2:
                axes[1].plot(x, [row['speedup_vs_v1'] for row in rows], marker=['o', 's', '^', 'D'][index], linestyle=['-', '--', '-.', ':'][index], color=colors[index], label=label)
        axes[0].set_yscale('log')
        axes[0].set_ylabel('Solver time (ms), median and IQR')
        axes[1].set_ylabel('Sequential median / OpenMP median')
        axes[1].axhline(1, color=foreground, linewidth=0.7, alpha=0.55)
        for ax in axes:
            legend = ax.legend(frameon=False, fontsize=8, loc='best')
            for item in legend.get_texts():
                item.set_color(foreground)
        fig.savefig(args.output / f'local-benchmark-{theme}.svg', metadata={'Date': None})
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            fig.savefig(args.preview_dir / f'local-benchmark-{theme}.png', dpi=150)
        plt.close(fig)
    print('\n'.join(table))


if __name__ == '__main__':
    main()
