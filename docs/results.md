# Local measurements and validation

The current performance evidence is the WSL campaign in [wsl-2026-09-12](../bench/results/wsl-2026-09-12/), started at 05:07:06 UTC and completed at 05:07:16 UTC on 2026-09-12. Solver sources and headers match baseline `d533cab`. A preliminary run overlapped another compute task and was excluded in full; its files remain only in the local audit, outside the repository's published results.

## Measurement protocol

The harness runs orders eight, nine and ten with v1 on one thread and v2 on one, two and four threads. For each order/configuration pair it retains one warmup and five measured fresh-process executions. A single scheduling RNG seeded with zero shuffles each round, first the warmup round and then the five measured rounds. There is no stochastic solver input. Each invocation has a timeout and is accepted only when its marks are increasing from zero, its differences are unique, its reported length matches its marks, and that length matches the reference oracle.

The primary metric is the solver's `time_ms` CSV field. In v1 and v2 that timer includes construction, greedy initialization, the search and statistics retrieval. It excludes process startup, output formatting and CSV writing. The existing writer rounds to 0.01 ms. The harness records whole-process wall time separately, including subprocess startup and output capture; this field is not used in the published comparison.

The retained run contains 12 warmups and 60 measured samples. Nothing is removed as an outlier. The summary uses `statistics.median` and `statistics.quantiles(..., method='inclusive')`. With five samples, the interquartile endpoints are the second and fourth sorted observations. A ratio divides the v1 median by the corresponding v2 median. The plotted interval belongs to time, not to the ratio; no confidence interval or significance claim is made.

The [environment JSON](../bench/results/wsl-2026-09-12/environment.json) records the system, virtual topology, memory, compiler, OpenMP package, MPI runtime, flags, Python version and source hashes. `OMP_DYNAMIC=FALSE`, `OMP_PLACES=cores` and `OMP_PROC_BIND=close` are set. Frequency, thermals, power policy and host scheduling are not controlled. The parent work session kept other solver benchmarks out of the retained run's time window.

## Detailed timings

<!-- GENERATED_TABLE_START -->
| Order | Configuration | Median (ms) | Q1 to Q3 (ms) | Ratio vs sequential |
|---|---|---:|---:|---:|
| G8 | Sequential | 3.65 | 3.62 to 3.66 | 1.00 |
| G8 | OpenMP, 1 thread | 2.69 | 2.67 to 2.77 | 1.36 |
| G8 | OpenMP, 2 threads | 1.73 | 1.70 to 1.82 | 2.11 |
| G8 | OpenMP, 4 threads | 1.36 | 1.28 to 5.95 | 2.68 |
| G9 | Sequential | 34.91 | 34.90 to 35.15 | 1.00 |
| G9 | OpenMP, 1 thread | 22.38 | 22.37 to 22.81 | 1.56 |
| G9 | OpenMP, 2 threads | 12.20 | 12.00 to 12.24 | 2.86 |
| G9 | OpenMP, 4 threads | 6.57 | 6.57 to 6.75 | 5.31 |
| G10 | Sequential | 329.23 | 325.33 to 332.93 | 1.00 |
| G10 | OpenMP, 1 thread | 205.15 | 204.66 to 207.37 | 1.60 |
| G10 | OpenMP, 2 threads | 178.25 | 175.82 to 183.01 | 1.85 |
| G10 | OpenMP, 4 threads | 50.17 | 47.28 to 70.85 | 6.56 |

<!-- GENERATED_TABLE_END -->

The complete samples are [samples.csv](../bench/results/wsl-2026-09-12/samples.csv); the derived values are [summary.json](../bench/results/wsl-2026-09-12/summary.json). The table is also emitted by `bench/plot.py` as [table.md](../bench/results/wsl-2026-09-12/table.md). The solver's full text output is retained in [runs.log](../bench/results/wsl-2026-09-12/runs.log), and the [build log](../bench/results/wsl-2026-09-12/build.log) records exact options.

OpenMP on one thread is already faster than v1 here, so a sequential/OpenMP ratio does not isolate the benefit of extra threads. Their actual node counts differ in the raw samples. Four-thread G10 also changes the explored work between repetitions. Scheduling, bound discovery and different task decomposition are plausible contributors; these observations do not quantify a separate effect for each mechanism.

## Validation and known failure

The original component tests passed: 58 common assertions, 13 OpenMP assertions and 30 MPI assertions reported by the suites. The six compiled targets were v1, v2, v3, v4, v1_noavx and v2_noavx. [Build](../bench/results/validation/build.log), [component output](../bench/results/validation/unit-tests.log), and [environment](../bench/results/validation/environment.txt) are retained.

An initial independent CLI campaign passed all its cases, with [the initial output](../bench/results/validation/initial-integration.log) and [initial JSON](../bench/results/validation/initial-integration.json) preserved. The portable checker later returned **27 passes and one failure across 28 executions**. That checker enumerates differences itself and checks the last mark against the printed length, so it is stricter than the previous CI's length-only text match.

The failing invocation was:

```bash
mpirun --oversubscribe -np 4 ./build/golomb_v3 7 --threads 2
```

Its reported length was 25, but its returned marks were `[0, 1, 6, 14, 17, 24, 26]`. The process returned success. See [the final full output](../bench/results/validation/integration.log) and [machine-readable failure](../bench/results/validation/integration.json). Subsequent targeted repetitions all passed, which confirms that a passing rerun cannot be used to dismiss the observation. [Twenty follow-up executions](../bench/results/validation/v3-regression/integration.json) are retained separately.

The source-level cause has not been established. The consistency of the transmitted bound, solution length and mark vector is the next investigation target. This documentation update does not change synchronization or search logic. The new CI checker can fail on this unresolved case; no failure is suppressed. Remote CI has not yet run for this branch.

## Unmeasured claims

| Claim | Status and reason |
|---|---|
| Multi-node MPI scaling and network efficiency | Not measured (`non mesuré`): no Romeo allocation or matching cluster hardware in this session |
| Standalone AVX2 gain | Not measured (`non mesuré`): the current comparison uses the explicit AVX2 path in both solvers; no ablation campaign was run |
| Historical v5 performance | Not measured (`non mesuré`): current checkout contains historical records but no v5 solver source |
| Broad correctness beyond the exercised small orders | Not established: bounded checks are not a proof for every accepted input |
| ARM/macOS execution and portability | Not tested in this session: validation used x86-64 Ubuntu under WSL |
| Regenerated historical PDFs | Not performed: original PDFs retained; TeX environment and external logo asset not verified |

The [archive catalogue](archive.md) explains why old cluster plots, reports and timings are kept separate from the current claims.

## Regenerating the figures

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r bench/requirements.txt
.venv/bin/python bench/plot.py --input bench/results/wsl-2026-09-12
```

The command writes a light SVG, a dark SVG, a JSON summary and a Markdown table from the committed raw CSV. The two themes use identical data and different foreground/background colors. Markers and line styles distinguish the configurations without relying on color. Rebuild the figures from a new run by changing `--input`; the README's hand-written headline and compact table must then be reviewed against the new summary.
