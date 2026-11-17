# Test results

Written by `tests/run_tests.py`. Rerun it to check these numbers.

- Oracle: Python 3.13.18 exact gate in `tests/oracle.py`
- Lean: Lean (version 4.35.0, x86_64-unknown-linux-gnu, commit eb6cafb7290e8bd5f2937522d8d804f58f02bafc, Release)
- Seed: 20261117
- Inputs: 300000
- Mutated: 243383 of the inputs sit on, just inside or just outside a radius, a limit or a length
- Verdicts: budget 56291, cost 93741, distance 58205, ok 72974, radius 17382, shape 1407
- Failures: 0
