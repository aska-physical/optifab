# Test results

Written by `tests/run_tests.py`. Rerun it to check these numbers.

- Oracle: Python 3.14.8 exact gate and plant model in `tests/oracle.py`
- Lean: Lean (version 4.35.0, x86_64-unknown-linux-gnu, commit eb6cafb7290e8bd5f2937522d8d804f58f02bafc, Release)
- Seed: 20261117
- Inputs: 430000
- Gate inputs: 300000
- Mutated: 243383 of the gate inputs sit on, just inside or just outside a radius, a limit or a length
- Verdicts: budget 56291, cost 93741, distance 58205, ok 72974, radius 17382, shape 1407
- Design inputs: 100000, each a proposed design run through the model, the bounds, the gate and the objective
- Design edges: 88514 of the design inputs have a gene on or just past a bound, or a margin on or just past its limit
- Design verdicts: bounds 21372, budget 17719, distance 17399, headroom 2880, ok 1479, radius 30449, same 8145, worse 557
- Loop inputs: 5000, each a whole run through `loop` and `changes`: 27628 proposals in all, 1592 taken up
- Asymmetric gate inputs: 25000
- Asymmetric verdicts: budget 5737, cost 9391, distance 2491, noImprovement 1477, ok 5087, okRecovery 815, shape 2
- Failures: 0
