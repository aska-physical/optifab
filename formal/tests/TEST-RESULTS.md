# Test results

Written by `tests/run_tests.py`. Rerun it to check these numbers.

- Oracle: Python 3.13.18 exact gate and plant model in `tests/oracle.py`
- Lean: Lean (version 4.35.0, x86_64-unknown-linux-gnu, commit eb6cafb7290e8bd5f2937522d8d804f58f02bafc, Release)
- Seed: 20261117
- Inputs: 405000
- Gate inputs: 300000
- Mutated: 243383 of the gate inputs sit on, just inside or just outside a radius, a limit or a length
- Verdicts: budget 56291, cost 93741, distance 58205, ok 72974, radius 17382, shape 1407
- Design inputs: 100000, each a proposed design run through the model, the bounds, the gate and the objective
- Design edges: 88514 of the design inputs have a gene on or just past a bound, or a margin on or just past its limit
- Design verdicts: bounds 21702, budget 19676, distance 17684, ok 7116, radius 33263, worse 559
- Loop inputs: 5000, each a whole run through `loop` and `changes`: 27628 proposals in all, 3602 taken up
- Failures: 0
