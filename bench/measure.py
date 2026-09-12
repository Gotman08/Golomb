"""Measure unchanged solver executables, preserving all samples and provenance."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shlex
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
KNOWN_LENGTHS = {8: 34, 9: 44, 10: 55}


def capture(command):
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=20)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def fingerprint():
    paths = [ROOT / 'Makefile', *sorted((ROOT / 'src').rglob('*.cpp')), *sorted((ROOT / 'include').rglob('*.hpp'))]
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def check_ruler(row, order):
    marks = json.loads(row['solution'])
    differences = [marks[j] - marks[i] for i in range(len(marks)) for j in range(i + 1, len(marks))]
    return (len(marks) == order and marks[0] == 0
            and all(value > 0 for value in differences)
            and len(differences) == len(set(differences))
            and marks[-1] == int(row['length']) == KNOWN_LENGTHS[order])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New output directory; existing paths are refused')
    parser.add_argument('--source-commit', help='Optional commit id when Git is unavailable inside WSL')
    parser.add_argument('--timeout', type=int, default=120, help='Seconds allowed per solver invocation')
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    output = args.output or ROOT / 'bench/results' / started.strftime('%Y%m%dT%H%M%SZ')
    if not output.is_absolute():
        output = ROOT / output
    output.mkdir(parents=True, exist_ok=False)
    build = ['make', '-j2', 'v1', 'v2']
    source_hashes = fingerprint()
    environment = {
        'started_utc': started.isoformat(),
        'system': platform.platform(),
        'os_release': platform.freedesktop_os_release(),
        'cpu': json.loads(capture(['lscpu', '--json']) or '{}'),
        'logical_cpus': os.cpu_count(),
        'memory_total_bytes': int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:'))) * 1024,
        'compiler': capture(['g++', '--version']),
        'make': capture(['make', '--version']),
        'mpi_runtime': capture(['mpirun', '--version']),
        'libgomp_package': capture(['dpkg-query', '-W', 'libgomp1']),
        'python': platform.python_version(),
        'git_commit': args.source_commit or capture(['git', 'rev-parse', 'HEAD']),
        'source_sha256': source_hashes,
        'build_command': build,
        'build_flags': '-std=c++17 -Wall -Wextra -O3 -flto=auto -march=native -funroll-loops -falign-functions=32 -falign-loops=32 -fno-rtti -mavx2 -mfma -DUSE_AVX2; v2 additionally -fopenmp',
        'protocol': {
            'orders': list(KNOWN_LENGTHS), 'configurations': ['v1', 'v2_t1', 'v2_t2', 'v2_t4'],
            'warmups_per_configuration_and_order': 1, 'measured_repetitions': 5,
            'schedule_seed': 0, 'schedule': 'one shuffled warmup round, then five shuffled measurement rounds',
            'solver_random_seed': None, 'solver_randomness': 'no stochastic input; parallel scheduling can change traversal order',
            'sample': 'one fresh process', 'primary_metric': 'solver-reported time_ms',
            'timer_scope': 'solver construction, solve and statistics retrieval; excludes process startup and printing',
            'reported_resolution_ms': 0.01, 'quartiles': 'inclusive linear interpolation (statistics.quantiles method=inclusive)',
            'warmups_retained': True, 'affinity': 'OpenMP OMP_PLACES=cores, OMP_PROC_BIND=close; sequential OS scheduling',
            'virtualization': 'host scheduling, CPU frequency and thermal state are not controlled',
        },
        'omp_environment': {'OMP_DYNAMIC': 'FALSE', 'OMP_PROC_BIND': 'close', 'OMP_PLACES': 'cores'},
    }
    metadata_path = output / 'environment.json'
    metadata_path.write_text(json.dumps(environment, indent=2) + '\n')
    with (output / 'build.log').open('w') as log:
        subprocess.run(build, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    configs = [(order, version, threads) for order in KNOWN_LENGTHS for version, threads in [(1, 1), (2, 1), (2, 2), (2, 4)]]
    fields = ['phase', 'repetition', 'sequence', 'version', 'order', 'threads', 'time_ms', 'process_wall_ms', 'nodes_explored', 'nodes_pruned', 'solution', 'length', 'valid', 'command']
    rng = random.Random(0)
    sequence = 0
    with (output / 'samples.csv').open('w', newline='') as raw, (output / 'runs.log').open('w') as log:
        writer = csv.DictWriter(raw, fieldnames=fields)
        writer.writeheader()
        for repetition in range(6):
            schedule = configs.copy()
            rng.shuffle(schedule)
            phase = 'warmup' if repetition == 0 else 'measured'
            for order, version, threads in schedule:
                sequence += 1
                command = [f'./build/golomb_v{version}', str(order)]
                if version == 2:
                    command += ['--threads', str(threads)]
                with tempfile.TemporaryDirectory(prefix='golomb-bench-') as tmp:
                    csv_path = Path(tmp) / 'sample.csv'
                    actual_command = command + ['--csv', str(csv_path)]
                    env = {**os.environ, **environment['omp_environment'], 'OMP_NUM_THREADS': str(threads)}
                    tick = time.perf_counter_ns()
                    result = subprocess.run(actual_command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=args.timeout)
                    wall_ms = (time.perf_counter_ns() - tick) / 1_000_000
                    log.write(f'{phase} {repetition}: $ {shlex.join(command)} --csv <temporary CSV>\n')
                    log.write(result.stdout.replace(str(csv_path), '<temporary CSV>') + '\n')
                    log.flush()
                    result.check_returncode()
                    with csv_path.open() as saved:
                        rows = list(csv.DictReader(saved))
                    if len(rows) != 1 or not check_ruler(rows[0], order):
                        raise RuntimeError(f'Invalid result for {shlex.join(command)}; inspect runs.log')
                    row = rows[0]
                    if (int(row['version']), int(row['order']), int(row['threads'])) != (version, order, threads):
                        raise RuntimeError('Reported configuration does not match the requested configuration')
                    writer.writerow({**row, 'phase': phase, 'repetition': repetition, 'sequence': sequence,
                                     'process_wall_ms': f'{wall_ms:.6f}', 'valid': True, 'command': shlex.join(command)})
                    raw.flush()
                print(f'{phase} {repetition}: G{order} v{version} threads={threads}: {row["time_ms"]} ms', flush=True)
    if fingerprint() != source_hashes:
        raise RuntimeError('Source files changed during measurement')
    environment['finished_utc'] = datetime.now(timezone.utc).isoformat()
    environment['completed_samples'] = sequence
    metadata_path.write_text(json.dumps(environment, indent=2) + '\n')
    print(f'Results: {output}')


if __name__ == '__main__':
    main()
