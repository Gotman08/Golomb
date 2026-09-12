# HPC deployment notes

The scripts in `scripts/hpc/` and the SLURM jobs in `jobs/` are retained from the historical Romeo work present at revision `d533cab` on 2026-03-31. Their cluster configuration and performance recommendations have not been revalidated in the local WSL session. They require an account and resource allocation on the intended cluster.

## Local MPI validation

The following local commands compile and exercise the distributed implementations without submitting a cluster job:

```bash
make v3 v4
mpirun --oversubscribe -np 2 ./build/golomb_v3 7 --threads 2
mpirun --oversubscribe -np 4 ./build/golomb_v4 8 --threads 2
```

The second solver invocation uses a power-of-two rank count for the hypercube topology. Passing these cases checks returned rulers and termination on one machine. It does not establish network scalability or fault tolerance.

## Historical cluster workflow

Review site-specific paths, account settings, partitions and allocations in the existing scripts before using them. Configure the existing `ROMEO_USER`, `ROMEO_HOST` and related settings for the intended site. The published project still contains historical account defaults; they are not needed for any local command in the README or benchmark harness.

No cluster submission, SSH connection or credential change is part of `bench/run.sh` or CI. A future cluster campaign needs recorded compiler and MPI versions, node topology, placement, warmups, repetitions and failed jobs before publishing scaling claims. See [the archive catalogue](archive.md) for the old datasets.
