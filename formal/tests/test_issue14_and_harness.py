"""Regression tests for Issue #14 (#14.3, #14.4, #14.5) and differential harness length checks.

Runs with stdlib-only under ``-I -B``, ``-I -O -B``, and ``-I -B -W error`` (zero bare ``assert``s).
Verifies both the Python oracle and, when built, the Lean ``plantgate`` binary on every witness.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
FORMAL_DIR = TESTS_DIR.parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import oracle  # noqa: E402
import run_tests  # noqa: E402

EXE = FORMAL_DIR / ".lake" / "build" / "bin" / "plantgate"
LIMIT = 1_000_000

REF_PLANT = dict(run_tests.PLANT)
REF_YEAR = dict(run_tests.YEAR)
REF_START = dict(pcm_kwh=2500, capture_ppm=850_000, wall_u_mw=132, floor_kw=600, shed_ppm=300_000)


def _run_lean(lines: list[str]) -> list[str] | None:
    if not EXE.is_file():
        return None
    proc = subprocess.run(
        [str(EXE)],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    return run_tests.split_output_lines(proc.stdout)


class TestHarnessLineCountCheck(unittest.TestCase):
    """Bug #12: differential harness must fail closed on extra or missing stdout lines."""

    def test_exact_single_trailing_newline_passes(self) -> None:
        failures = run_tests.compare_outputs(["c1", "c2"], ["ok 9", "distance 9"], "ok 9\ndistance 9\n")
        self.assertEqual(failures, [])

    def test_extra_trailing_line_fails_closed(self) -> None:
        failures = run_tests.compare_outputs(["c1"], ["ok 9"], "ok 9\nEXTRA LINE\n")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], "output line count mismatch")
        self.assertIn("got 2 lines, expected 1", failures[0][1])

    def test_extra_blank_line_fails_closed(self) -> None:
        failures = run_tests.compare_outputs(["c1"], ["ok 9"], "ok 9\n\n")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], "output line count mismatch")

    def test_missing_line_fails_closed(self) -> None:
        failures = run_tests.compare_outputs(["c1", "c2"], ["ok 9", "ok 8"], "ok 9\n")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], "output line count mismatch")

    def test_empty_stdout_for_nonempty_expected_fails(self) -> None:
        failures = run_tests.compare_outputs(["c1"], ["ok 9"], "")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], "output line count mismatch")


class TestIssue14LexTieBreaker(unittest.TestCase):
    """Issue #14.3: equal-objective headroom decay refused; equal-objective headroom widening admitted."""

    def test_four_step_equal_objective_decay_zero_admitted(self) -> None:
        decay_chain = [
            dict(REF_START, pcm_kwh=2450),
            dict(REF_START, pcm_kwh=2420),
            dict(REF_START, pcm_kwh=2410),
            dict(REF_START, pcm_kwh=2405),
        ]
        eta0 = oracle.objective(REF_PLANT, REF_YEAR, REF_START)
        state = (REF_START, 64)
        for cand in decay_chain:
            self.assertEqual(oracle.objective(REF_PLANT, REF_YEAR, cand), eta0)
            state, verdict = oracle.design_step(REF_PLANT, REF_YEAR, LIMIT, state, cand)
            self.assertEqual(verdict, "headroom")
            self.assertEqual(state, (REF_START, 64))

        (held, left), taken = oracle.run_designs(REF_PLANT, REF_YEAR, LIMIT, (REF_START, 64), decay_chain)
        self.assertEqual(held, REF_START)
        self.assertEqual(left, 64)
        self.assertEqual(taken, 0)

        lean_lines = [oracle.design_line(LIMIT, 64, REF_PLANT, REF_YEAR, REF_START, c) for c in decay_chain]
        lean_lines.append(oracle.loop_line(LIMIT, 64, REF_PLANT, REF_YEAR, REF_START, decay_chain))
        lean_out = _run_lean(lean_lines)
        if lean_out is not None:
            want = [oracle.design_expected(LIMIT, 64, REF_PLANT, REF_YEAR, REF_START, c) for c in decay_chain]
            want.append(oracle.loop_expected(LIMIT, 64, REF_PLANT, REF_YEAR, REF_START, decay_chain))
            self.assertEqual(lean_out, want)

    def test_equal_objective_headroom_widening_admitted(self) -> None:
        wider = dict(REF_START, pcm_kwh=2580)
        self.assertEqual(
            oracle.objective(REF_PLANT, REF_YEAR, wider),
            oracle.objective(REF_PLANT, REF_YEAR, REF_START),
        )
        self.assertGreater(
            oracle.headroom(LIMIT, oracle.margins(REF_PLANT, REF_YEAR, wider)),
            oracle.headroom(LIMIT, oracle.margins(REF_PLANT, REF_YEAR, REF_START)),
        )
        (held, left), verdict = oracle.design_step(REF_PLANT, REF_YEAR, LIMIT, (REF_START, 64), wider)
        self.assertEqual(verdict, "ok")
        self.assertEqual(held, wider)
        self.assertEqual(left, 63)

        lean_out = _run_lean([oracle.design_line(LIMIT, 64, REF_PLANT, REF_YEAR, REF_START, wider)])
        if lean_out is not None:
            self.assertEqual(lean_out, [oracle.design_expected(LIMIT, 64, REF_PLANT, REF_YEAR, REF_START, wider)])


class TestIssue14WellFormed(unittest.TestCase):
    """Issue #14.4: WellFormed rejects shed > 1_000_000, floor == 0, and malformed plant/scenario."""

    def test_well_formed_witnesses_and_lean_parity(self) -> None:
        self.assertTrue(oracle.well_formed(REF_PLANT, REF_YEAR, REF_START))

        bad_shed = dict(REF_START, shed_ppm=2_000_000)
        self.assertLess(oracle.outage_num(REF_PLANT, REF_YEAR, bad_shed), 0)
        self.assertFalse(oracle.well_formed(REF_PLANT, REF_YEAR, bad_shed))

        bad_floor = dict(REF_START, floor_kw=0)
        self.assertFalse(oracle.well_formed(REF_PLANT, REF_YEAR, bad_floor))

        bad_pcm = dict(REF_START, pcm_kwh=0)
        self.assertFalse(oracle.well_formed(REF_PLANT, REF_YEAR, bad_pcm))

        bad_capture = dict(REF_START, capture_ppm=1_000_001)
        self.assertFalse(oracle.well_formed(REF_PLANT, REF_YEAR, bad_capture))

        bad_year = dict(REF_YEAR, outage_min=0)
        self.assertFalse(oracle.well_formed(REF_PLANT, bad_year, REF_START))

        bad_plant = dict(REF_PLANT, p_it_w=-1)
        self.assertFalse(oracle.well_formed(bad_plant, REF_YEAR, REF_START))

        cases = [
            (REF_PLANT, REF_YEAR, REF_START, "ok"),
            (REF_PLANT, REF_YEAR, bad_shed, "malformed"),
            (REF_PLANT, REF_YEAR, bad_floor, "malformed"),
            (REF_PLANT, REF_YEAR, bad_pcm, "malformed"),
            (REF_PLANT, REF_YEAR, bad_capture, "malformed"),
            (REF_PLANT, bad_year, REF_START, "malformed"),
            (bad_plant, REF_YEAR, REF_START, "malformed"),
        ]
        for p, y, g, exp in cases:
            self.assertEqual(oracle.well_formed_expected(p, y, g), exp)

        lean_out = _run_lean([oracle.well_formed_line(p, y, g) for p, y, g, _ in cases])
        if lean_out is not None:
            self.assertEqual(lean_out, [exp for _, _, _, exp in cases])


class TestIssue14AsymmetricGateAndRecovery(unittest.TestCase):
    """Issue #14.5: pure safety moves admitted without distance penalty; OOB recovered via Lyapunov descent."""

    def test_pure_safety_move_admitted_and_symmetric_refused(self) -> None:
        base_m = oracle.margins(REF_PLANT, REF_YEAR, REF_START)
        safe_g = dict(REF_START, pcm_kwh=5000)
        safe_m = oracle.margins(REF_PLANT, REF_YEAR, safe_g)

        # Symmetric gate refuses this huge safety improvement as "distance"
        sym_verdict, sym_rem = oracle.gate(base_m, safe_m, oracle.headroom(LIMIT, base_m), 64, 1)
        self.assertEqual(sym_verdict, "distance")
        self.assertEqual(sym_rem, 64)

        # Asymmetric gate sees pos_dist_sq == 0 and admits as "ok"
        self.assertEqual(oracle.pos_dist_sq(base_m, safe_m), 0)
        asym_verdict, asym_rem = oracle.gate_asymmetric(LIMIT, base_m, safe_m, 64, 1)
        self.assertEqual(asym_verdict, "ok")
        self.assertEqual(asym_rem, 63)
        self.assertTrue(all(x <= LIMIT for x in safe_m))

        lean_out = _run_lean([oracle.asym_line(LIMIT, 64, 1, base_m, safe_m)])
        if lean_out is not None:
            self.assertEqual(lean_out, ["ok 63"])

    def test_oob_baseline_single_and_multistep_lyapunov_recovery(self) -> None:
        oob_g = dict(REF_START, pcm_kwh=2350)
        mid_g = dict(REF_START, pcm_kwh=2400)
        oob_m = oracle.margins(REF_PLANT, REF_YEAR, oob_g)
        mid_m = oracle.margins(REF_PLANT, REF_YEAR, mid_g)
        ref_m = oracle.margins(REF_PLANT, REF_YEAR, REF_START)

        self.assertEqual(oob_m[-1], 1_023_079)
        self.assertEqual(mid_m[-1], 1_001_765)
        self.assertEqual(ref_m[-1], 961_695)
        self.assertLess(oracle.headroom(LIMIT, oob_m), 0)

        # Single-step OOB recovery 2350 -> 2500 kWh
        v1, rem1 = oracle.gate_asymmetric(LIMIT, oob_m, ref_m, 64, 1)
        self.assertEqual(v1, "okRecovery")
        self.assertEqual(rem1, 63)
        self.assertGreaterEqual(oracle.headroom(LIMIT, ref_m), 0)

        # Two-step strict Lyapunov descent 2350 -> 2400 -> 2500 kWh
        st, va = oracle.evolve_asymmetric(LIMIT, (oob_m, 64), mid_m, 1)
        self.assertEqual(va, "okRecovery")
        self.assertEqual(st, (mid_m, 63))
        st2, vb = oracle.evolve_asymmetric(LIMIT, st, ref_m, 1)
        self.assertEqual(vb, "okRecovery")
        self.assertEqual(st2, (ref_m, 62))

        # OOB move that creates a new violation on another coordinate must be refused
        bad_rec = list(ref_m)
        bad_rec[0] = LIMIT + 1
        v_bad, rem_bad = oracle.gate_asymmetric(LIMIT, oob_m, bad_rec, 64, 1)
        self.assertEqual(v_bad, "noImprovement")
        self.assertEqual(rem_bad, 64)

        # OOB move with no headroom gain must be refused
        v_flat, rem_flat = oracle.gate_asymmetric(LIMIT, oob_m, oob_m, 64, 1)
        self.assertEqual(v_flat, "noImprovement")
        self.assertEqual(rem_flat, 64)

        lean_lines = [
            oracle.asym_line(LIMIT, 64, 1, oob_m, ref_m),
            oracle.asym_line(LIMIT, 64, 1, oob_m, mid_m),
            oracle.asym_line(LIMIT, 63, 1, mid_m, ref_m),
            oracle.asym_line(LIMIT, 64, 1, oob_m, bad_rec),
            oracle.asym_line(LIMIT, 64, 1, oob_m, oob_m),
        ]
        lean_out = _run_lean(lean_lines)
        if lean_out is not None:
            self.assertEqual(
                lean_out,
                ["okRecovery 63", "okRecovery 63", "okRecovery 62", "noImprovement 64", "noImprovement 64"],
            )


if __name__ == "__main__":
    unittest.main()
