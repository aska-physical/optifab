# Bar report

The output of the Proven Commons bar check on this project, run on 2026-11-17 with
`python3 bar/check.py formal --offline` from Proven-Commons/mission at commit
`7b22e542f0db0f3013ab1439cf5d1947676a5083`. Rerun it to check. Item 7 reads SKIP because the run was
offline, so the branch rule on GitHub was not read.

## Verified bar 2: plantgate

**In progress: no failures, some items still open. Do not call it verified.**
Project status in bar.toml: `in-progress`.

| # | Item | Status | Detail |
|---|------|--------|--------|
| 1 | Specification public, approved by a separate reviewer, and pinned | OPEN | no approval recorded; the current spec hash is 504d8f56a9fa49307c42ec462a76883db50c35ab6feb0e94ea84e92ef37cd455 |
| 2 | Each public claim names the theorem behind it | PASS | 'What is proved' names all 8 theorems; that the claims match them would rest on a spec approval (item 1), which is not in place |
| 3 | Proofs match the approved statements, in one command | PASS | `lake comparator --paranoid` accepts all 8 theorems under every bundled kernel, and each statement depends only on the spec files, the code under proof, and code outside the project |
| 4 | The code that runs is the code that was proved | PASS | 4 Lean files, none uses a forbidden feature; that the entry points call the proved functions would rest on a spec approval (item 1), which is not in place |
| 5 | Differential tests ran, with the record in the repo | PASS | 300,000 inputs, seed 20261117, 0 failures, oracle Python 3.13.18 exact gate in `tests/oracle.py` |
| 6 | The public page lists what is outside the proof | PASS | all sections present; that they are accurate would rest on a spec approval (item 1), which is not in place |
| 7 | The check runs in CI | SKIP | .github/workflows/bar.yml calls the verified-bar workflow; the branch rule was not read (--offline) |

