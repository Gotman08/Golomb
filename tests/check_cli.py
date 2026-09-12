"""Check returned rulers independently across sequential, OpenMP and local MPI."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KNOWN = {4: 6, 5: 11, 6: 17, 7: 25, 8: 34}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/validation')
    parser.add_argument('--v3-regression-runs', type=int, default=0, help='Run only the intermittent v3 G7 case this many times')
    args = parser.parse_args()
    if args.v3_regression_runs < 0:
        parser.error('--v3-regression-runs must be nonnegative')
    args.output.mkdir(parents=True, exist_ok=True)
    cases = []
    for version in ('v1', 'v1_noavx', 'v2', 'v2_noavx'):
        for order in KNOWN:
            cases.append([f'./build/golomb_{version}', str(order)] + (['--threads', '4'] if version.startswith('v2') else []))
    for version in ('v3', 'v4'):
        for ranks in (2, 4):
            for order in (7, 8):
                cases.append(['mpirun', '--oversubscribe', '-np', str(ranks), f'./build/golomb_{version}', str(order), '--threads', '2'])
    if args.v3_regression_runs:
        cases = [['mpirun', '--oversubscribe', '-np', '4', './build/golomb_v3', '7', '--threads', '2'] for _ in range(args.v3_regression_runs)]
    results = []
    with (args.output / 'integration.log').open('w') as log:
        for command in cases:
            log.write('$ ' + shlex.join(command) + '\n')
            process = subprocess.run(['timeout', '45', *command], cwd=ROOT, env={**os.environ, 'OMP_NUM_THREADS': '4'}, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
            log.write(process.stdout + '\n')
            match = re.search(r'Solution:\s*\[([^]]+)\]', process.stdout)
            marks = [int(value) for value in match.group(1).split(',')] if match else []
            length_match = re.search(r'^Length:\s*(\d+)', process.stdout, re.MULTILINE)
            length = int(length_match.group(1)) if length_match else None
            binary_index = next(index for index, value in enumerate(command) if value.startswith('./build/'))
            order = int(command[binary_index + 1])
            differences = [marks[j] - marks[i] for i in range(len(marks)) for j in range(i + 1, len(marks))]
            valid = len(marks) == order and marks[0] == 0 and all(value > 0 for value in differences) and len(differences) == len(set(differences)) and marks[-1] == length
            passed = process.returncode == 0 and valid and length == KNOWN[order]
            row = {'command': command, 'exit_code': process.returncode, 'order': order, 'expected_length': KNOWN[order], 'length': length, 'marks': marks, 'valid': valid, 'passed': passed}
            results.append(row)
            log.write('CHECK ' + json.dumps(row) + '\n\n')
            log.flush()
            print(('PASS' if passed else 'FAIL') + ' ' + shlex.join(command), flush=True)
    log_path = args.output / 'integration.log'
    log_path.write_text(log_path.read_text().rstrip() + '\n')
    (args.output / 'integration.json').write_text(json.dumps(results, indent=2) + '\n')
    raise SystemExit(0 if all(row['passed'] for row in results) else 1)


if __name__ == '__main__':
    main()
