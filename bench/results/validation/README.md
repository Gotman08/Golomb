# Validation evidence

All files in this directory come from the September 2026 local WSL validation of unchanged solver source revision `d533cab`.

| Files | Meaning |
|---|---|
| `build.log`, `unit-tests.log`, `environment.txt` | Initial builds and component tests: successful |
| `initial-integration.json`, `initial-integration.log` | Initial independent CLI checks: all passed |
| `integration.json`, `integration.log` | Portable CLI checker: one inconsistent v3 result detected among the cases |
| `v3-regression/` | Follow-up runs of that v3 configuration: all passed; the defect remains intermittent |

The current checker is [tests/check_cli.py](../../../tests/check_cli.py). See [the detailed failure analysis](../../../docs/results.md#validation-and-known-failure). The successful earlier campaign is retained as provenance, not substituted for the later failure. These validation runs are not performance benchmarks.
