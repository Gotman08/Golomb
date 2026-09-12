# Historical material

The following material was already present at baseline revision `d533cab`, committed on 2026-03-31. It is retained for provenance. **Historical performance is not remeasured** in the September 2026 WSL session and is not used in the headline, new tables or new SVG figures.

| Material | Status |
|---|---|
| [Romeo CSV files and raw logs](../results/romeo/) | Historical cluster data, including archived runs and some v5 records for which the current checkout has no solver source |
| [Canonical historical plots](../results/plots/) | Existing PNG figures; the duplicate copies formerly under `docs/images/` were removed |
| [Cluster report PDF](rapport_golomb_hpc.pdf) and [LaTeX source](rapport_golomb_hpc.tex) | Original report, internally labelled academic year 2024 to 2025; PDF preserved unchanged |
| [Presentation PDF](presentation_golomb.pdf) and [LaTeX source](presentation_golomb.tex) | Original presentation, internally labelled academic year 2025 to 2026; PDF preserved unchanged |
| [Historical plotting program](../tools/visualization/generate_romeo_plots.py) | Reads the historical CSV files and writes the historical plot set |
| [Legacy plot scripts](../tools/visualization/legacy/) | Earlier analysis workflows, retained for provenance |

The academic labels are not timestamps for individual measurements. Some CSV filenames encode machine allocations, while other files use earlier formats. The old reports' timings, speedups and inferred bottlenecks have not been independently confirmed here. The original PDFs can contain claims or examples superseded by the maintained README.

The historical plot generator can be invoked in a separate environment with the dependencies listed in `tools/visualization/requirements.txt`:

```bash
python tools/visualization/generate_romeo_plots.py --data results/romeo --output build/historical-plots
```

Those old dependencies are not an exact lockfile, so a byte-for-byte match to the saved PNGs is not promised. Current benchmark figures use the separately pinned environment in `bench/requirements.txt`. The LaTeX sources refer to the canonical plots in `results/plots/`. The PDFs have not been rebuilt in this update; a full TeX environment and the report's external logo asset have not been verified. Temporary LaTeX compilation files were removed.
