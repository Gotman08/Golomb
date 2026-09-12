# Algorithm notes

A Golomb ruler consists of increasing integer marks whose positive pairwise differences are all distinct. The objective is to minimize its final mark when the first is zero. The local sequential solver returned `[0, 1, 4, 6]` for order four; its differences are `{1, 2, 3, 4, 5, 6}`. The returned marks and an independent validity check are recorded in [the validation data](../bench/results/validation/integration.json).

The implementation extends partial rulers in depth-first order, tracks used differences with a bitset, and rejects collisions. A greedy construction gives an initial feasible length. Bounds on the remaining marks reject branches that cannot improve the best length found so far. OpenMP and MPI variants divide this search into prefix subtrees and propagate better bounds.

See [design and tradeoffs](design.md) for the actual decomposition, state representation, and limits. No general complexity classification or near-linear scaling claim is inferred from the small local benchmark.
