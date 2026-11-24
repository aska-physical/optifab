#!/usr/bin/env python3
"""Assertion-free verification, mutation-killing & adversarial test suite
for Pure-Z/Q Schur Recursive Optical/Lithography Metrology Closure.

100% pure Python 3 stdlib unittest, zero bare asserts, zero AST floats, zero float(),
zero .isdigit(), zero islink, scratch os.mkfifo only, zero mathematical RNG.
"""
from __future__ import annotations

import ast
import copy
import ctypes
from fractions import Fraction
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import optifab_schur_metrology_audit as audit  # noqa: E402
import optifab_schur_metrology_oracle as oracle  # noqa: E402


def _resign_payload(payload: dict[str, object]) -> dict[str, object]:
    p_sha = audit._sha256_canonical(payload)
    outer = {
        "schema_version": oracle.SCHEMA_VERSION,
        "track_id": oracle.TRACK_ID,
        "payload_sha256": p_sha,
        "payload": payload,
    }
    c_sha = audit._sha256_canonical(outer)
    return {
        "schema_version": oracle.SCHEMA_VERSION,
        "track_id": oracle.TRACK_ID,
        "payload_sha256": p_sha,
        "certificate_sha256": c_sha,
        "payload": payload,
    }


def _call_main(argv: list[str]) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with mock.patch.object(sys, "stdout", out_buf), mock.patch.object(sys, "stderr", err_buf):
        rc = audit.main(argv)
    return rc, out_buf.getvalue(), err_buf.getvalue()


class TestOptifabSchurMetrologyR5(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cert = audit.build_standalone_certificate()
        cls.payload = cls.cert["payload"]

    def _expect_err(self, code: str, fn, *args, **kwargs) -> oracle.OptifabSchurError:
        with self.assertRaises(oracle.OptifabSchurError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)
        return ctx.exception

    # ------------------------------------------------------------------
    # 1. Static AST & Hygiene (Zero Floats, Asserts, secret* Vars, DevNull)
    # ------------------------------------------------------------------
    def test_01_static_ast_hygiene(self) -> None:
        files = (
            _THIS_DIR / "optifab_schur_metrology_oracle.py",
            _THIS_DIR / "optifab_schur_metrology_audit.py",
            _THIS_DIR / "test_optifab_schur_metrology_r5.py",
        )
        for fp in files:
            src = fp.read_text(encoding="utf-8")
            self.assertNotIn("\r", src)
            tree = ast.parse(src, filename=str(fp))
            for node in ast.walk(tree):
                self.assertNotIsInstance(node, ast.Assert, f"bare assert in {fp.name}")
                if isinstance(node, ast.Constant):
                    self.assertIsNot(type(node.value), float, f"float literal in {fp.name}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotEqual(node.func.id, "float", f"float() call in {fp.name}")
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ("isdigit", "islink", "is_symlink"), f"forbidden attr in {fp.name}")
                if isinstance(node, ast.Name) and node.id != "secrets":
                    self.assertFalse(node.id.lower().startswith("secret"), f"forbidden var {node.id} in {fp.name}")
                if isinstance(node, ast.arg):
                    self.assertFalse(node.arg.lower().startswith("secret"), f"forbidden arg {node.arg} in {fp.name}")

    # ------------------------------------------------------------------
    # 2. Strict Primitives, Bit Caps & Exact Formatters
    # ------------------------------------------------------------------
    def test_02_strict_primitives_and_formatters(self) -> None:
        oracle.require_ok(True, "OK", "ok")
        self._expect_err("BOOM", oracle.require_ok, False, "BOOM", "fail")
        self._expect_err("INVALID_CONDITION_TYPE", oracle.require_ok, 1, "X", "bad")
        self.assertIs(oracle.require_exact_bool(True), True)
        self.assertIs(oracle.require_exact_bool(False), False)
        self._expect_err("INVALID_BOOL_TYPE", oracle.require_exact_bool, 1)

        max_ok = (1 << oracle.MAX_INT_BITS) - 1
        self.assertEqual(oracle.require_exact_int(max_ok, "m", lo=0, hi=max_ok), max_ok)
        self.assertEqual(oracle.require_exact_int(0, "z", lo=0, hi=0), 0)
        self._expect_err("INVALID_INT_TYPE", oracle.require_exact_int, True)
        self._expect_err("INT_BIT_LIMIT", oracle.require_exact_int, 1 << oracle.MAX_INT_BITS)
        self._expect_err("INVALID_BOUND_TYPE", oracle.require_exact_int, 5, lo="0")
        self._expect_err("INVALID_BOUND_TYPE", oracle.require_exact_int, 5, hi="9")
        self._expect_err("INT_OUT_OF_RANGE", oracle.require_exact_int, -1, lo=0)
        self._expect_err("INT_OUT_OF_RANGE", oracle.require_exact_int, 10, hi=9)

        self.assertEqual(oracle.require_exact_fraction(Fraction(max_ok, 1)), Fraction(max_ok, 1))
        self.assertEqual(oracle.require_exact_fraction(Fraction(1, max_ok)), Fraction(1, max_ok))
        self._expect_err("INVALID_FRACTION_TYPE", oracle.require_exact_fraction, 3)
        self._expect_err("RATIONAL_BIT_LIMIT", oracle.require_exact_fraction, Fraction(1 << oracle.MAX_RATIONAL_BITS, 1))
        self._expect_err("RATIONAL_BIT_LIMIT", oracle.require_exact_fraction, Fraction(1, 1 << oracle.MAX_RATIONAL_BITS))

        self.assertEqual(oracle.format_rational(Fraction(5, 1)), "5")
        self.assertEqual(oracle.format_rational(Fraction(-3, 4)), "-3/4")
        self.assertEqual(oracle.format_decimal(Fraction(1, 200), 2), "0.01")
        self.assertEqual(oracle.format_decimal(Fraction(1, 201), 2), "0.00")
        self.assertEqual(oracle.format_decimal(Fraction(-1, 10000), 2), "0.00")
        self.assertEqual(oracle.format_decimal(Fraction(-7, 2), 0), "-4")
        self.assertEqual(oracle.format_decimal(Fraction(7, 2), 0), "4")
        self.assertEqual(oracle.format_decimal(Fraction(0), 0), "0")
        self.assertEqual(oracle.format_decimal(Fraction(1, 8), 12), "0.125000000000")
        self._expect_err("INT_OUT_OF_RANGE", oracle.format_decimal, Fraction(1), -1)
        self._expect_err("INT_OUT_OF_RANGE", oracle.format_decimal, Fraction(1), 13)

    # ------------------------------------------------------------------
    # 3. Exact Q Linear Algebra, Bareiss, Sylvester Inertia & PlantGate
    # ------------------------------------------------------------------
    def test_03_linear_algebra_bareiss_inertia_and_gate(self) -> None:
        self._expect_err("INVALID_MATRIX", oracle.require_square_q_matrix, "bad")
        self._expect_err("INVALID_MATRIX", oracle.require_square_q_matrix, [])
        self._expect_err("NON_SQUARE_MATRIX", oracle.require_square_q_matrix, ["a"])
        self._expect_err("NON_SQUARE_MATRIX", oracle.require_square_q_matrix, [[Fraction(1), Fraction(2)]])
        self._expect_err("INVALID_FRACTION_TYPE", oracle.require_square_q_matrix, [[1]])

        m1 = [[Fraction(3, 2)]]
        m2 = [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]
        m2_ns = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        self._expect_err("DIM_MISMATCH", oracle.mat_mul_q, m1, m2)
        self.assertEqual(oracle.mat_mul_q(m2, m2_ns), [[Fraction(3), Fraction(4)], [Fraction(1), Fraction(2)]])

        self._expect_err("VEC_DIM_MISMATCH", oracle.mat_vec_q, m2, "ab")
        self._expect_err("VEC_DIM_MISMATCH", oracle.mat_vec_q, m2, [Fraction(1)])
        self.assertEqual(oracle.mat_vec_q(m2_ns, [Fraction(2), Fraction(5)]), [Fraction(12), Fraction(26)])
        self.assertEqual(oracle.quad_form_q([Fraction(2), Fraction(3)], [[Fraction(2), Fraction(1)], [Fraction(1), Fraction(5)]]), Fraction(65))

        # Bareiss determinant on 1x1, row-swap 2x2, dense fractional 3x3 (exercises prev_pivot != 1), and singular
        self.assertEqual(oracle.bareiss_det_exact(m1), Fraction(3, 2))
        self.assertEqual(oracle.bareiss_det_exact(m2), Fraction(-1))
        m3 = [
            [Fraction(2, 3), Fraction(1, 2), Fraction(1, 5)],
            [Fraction(1, 4), Fraction(3, 5), Fraction(1, 3)],
            [Fraction(1, 7), Fraction(2, 3), Fraction(4, 5)],
        ]
        det3, inv3 = oracle.exact_det_and_inv_q(m3)
        self.assertEqual(det3, oracle.bareiss_det_exact(m3))
        ident3 = [[Fraction(1 if i == j else 0) for j in range(3)] for i in range(3)]
        self.assertEqual(oracle.mat_mul_q(m3, inv3), ident3)
        self.assertEqual(oracle.mat_mul_q(inv3, m3), ident3)

        det_swap, inv_swap = oracle.exact_det_and_inv_q(m2)
        self.assertEqual(det_swap, Fraction(-1))
        self.assertEqual(inv_swap, m2)
        sing = [[Fraction(1), Fraction(1)], [Fraction(1), Fraction(1)]]
        self.assertEqual(oracle.bareiss_det_exact(sing), Fraction(0))
        self._expect_err("SINGULAR_MATRIX", oracle.exact_det_and_inv_q, sing)

        # Sylvester inertia: asymmetric, hyperbolic, zero matrix, pivot swap, 3x3 delayed off-diagonal pair
        self._expect_err("ASYMMETRIC_MATRIX", oracle.sylvester_inertia_exact, [[Fraction(1), Fraction(2)], [Fraction(0), Fraction(1)]])
        hyp = oracle.sylvester_inertia_exact(m2)
        self.assertEqual(hyp["inertia_pos_zero_neg"], [1, 0, 1])
        self.assertIsNotNone(hyp["negative_witness_vec_q"])
        z2 = oracle.sylvester_inertia_exact([[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]])
        self.assertEqual(z2["inertia_pos_zero_neg"], [0, 2, 0])
        self.assertIsNone(z2["negative_witness_vec_q"])
        sw = oracle.sylvester_inertia_exact([[Fraction(0), Fraction(0)], [Fraction(0), Fraction(3)]])
        self.assertEqual(sw["inertia_pos_zero_neg"], [1, 1, 0])
        m3_pair = [
            [Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(2)],
            [Fraction(0), Fraction(2), Fraction(0)],
        ]
        in3 = oracle.sylvester_inertia_exact(m3_pair)
        self.assertEqual(in3["inertia_pos_zero_neg"], [1, 1, 1])
        self.assertTrue(in3["congruence_exact"])

        # Block Schur & assemble guards (distinct type vs length failures kill every BoolOp & M027)
        self._expect_err("INVALID_BLOCK_B", oracle.block_schur_complement_q, m1, {(Fraction(1),)}, m1)
        self._expect_err("INVALID_BLOCK_B", oracle.block_schur_complement_q, m1, "x", m1)
        self._expect_err("INVALID_BLOCK_B", oracle.block_schur_complement_q, m1, [], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.block_schur_complement_q, m1, ["x"], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.block_schur_complement_q, m1, [[Fraction(1), Fraction(2)]], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, {(Fraction(1),)}, m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, "x", m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, [[Fraction(1)], [Fraction(2)]], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, [[]], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, [123], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, ["x"], m1)
        self._expect_err("INVALID_BLOCK_B", oracle.assemble_block_matrix_q, m1, [[Fraction(1), Fraction(2)]], m1)
        self._expect_err("INVALID_FRACTION_TYPE", oracle.assemble_block_matrix_q, m1, [[1]], m1)

        # Collatz-Wielandt guards (including exact zero entry killing >= vs >)
        self._expect_err("NEGATIVE_MATRIX_ENTRY", oracle.collatz_wielandt_bounds_q, [[Fraction(-1)]], [Fraction(1)])
        self._expect_err("NONPOSITIVE_WITNESS", oracle.collatz_wielandt_bounds_q, [[Fraction(1)]], [Fraction(0)])
        self.assertEqual(
            oracle.collatz_wielandt_bounds_q(m2, [Fraction(1), Fraction(1)]),
            (Fraction(1), Fraction(1)),
        )

        # _evaluate_schur_regime parameter guards
        a_m, b_m, d_m = oracle._optifab_coupled_blocks()
        self._expect_err("NONPOSITIVE_TAU", oracle._evaluate_schur_regime, a_m, b_m, d_m, tau=Fraction(0))
        self._expect_err("INVALID_CALIBRATION", oracle._evaluate_schur_regime, a_m, b_m, d_m, tau=Fraction(1, 2), eta_cal=Fraction(-1))

        # Exact integer PlantGate boundaries (exact len-1 str kills DEL_0 and DEL_1)
        self._expect_err("INVALID_GATE_VECTORS", oracle.optifab_plant_gate_exact, [], [], 100, 10, 1)
        self._expect_err("INVALID_GATE_VECTORS", oracle.optifab_plant_gate_exact, [10], [10, 20], 100, 10, 1)
        self._expect_err("INVALID_GATE_VECTORS", oracle.optifab_plant_gate_exact, "a", [10], 100, 10, 1)
        self._expect_err("INVALID_GATE_VECTORS", oracle.optifab_plant_gate_exact, [10], "a", 100, 10, 1)
        g_zero_cost = oracle.optifab_plant_gate_exact([50], [50], 100, 10, 0)
        self.assertFalse(g_zero_cost["admitted"])
        self.assertEqual(g_zero_cost["remaining_budget"], 10)
        g_exact_bud = oracle.optifab_plant_gate_exact([50], [100], 100, 5, 5)
        self.assertTrue(g_exact_bud["admitted"])
        self.assertEqual(g_exact_bud["remaining_budget"], 0)
        self.assertFalse(g_exact_bud["all_cand_below_limit"])
        g_over_bud = oracle.optifab_plant_gate_exact([50], [50], 100, 5, 6)
        self.assertFalse(g_over_bud["admitted"])
        g_over_rad = oracle.optifab_plant_gate_exact([50], [101], 100, 5, 1)
        self.assertFalse(g_over_rad["admitted"])
        g_at_lim = oracle.optifab_plant_gate_exact([100], [100], 100, 5, 1)
        self.assertTrue(g_at_lim["admitted"])
        g_past_lim = oracle.optifab_plant_gate_exact([101], [101], 100, 5, 1)
        self.assertFalse(g_past_lim["admitted"])
        self.assertEqual(oracle._ceil_ppm(Fraction(3, 10), 100), 30)
        self.assertEqual(oracle._ceil_ppm(Fraction(1, 3), 100), 34)

    # ------------------------------------------------------------------
    # 4. Exact Four-Pillar Mathematical Payload Checks
    # ------------------------------------------------------------------
    def test_04_four_pillars_exact_values(self) -> None:
        pl = self.payload
        self.assertEqual(pl["track_id"], oracle.TRACK_ID)
        self.assertEqual(pl["portal_ref"], "Portal 56")
        self.assertEqual(pl["novelty_class"], "N1")

        p1 = pl["pillar1_optifab_physical_anchors"]
        self.assertTrue(p1["all_verified"])
        self.assertEqual(p1["limit_state_count"], 12)
        self.assertEqual(p1["binding_headroom_q"], "27419/137820")
        self.assertEqual(p1["plant_radius_floored_q"], "1989/10000")
        self.assertEqual(p1["second_tightest_headroom_q"], "692/3003")
        self.assertEqual(p1["recooling_max_15C_dec6"], "40.109177")
        self.assertEqual(p1["recooling_max_18C_dec6"], "41.457941")
        self.assertEqual(p1["load_floor_p_min_mw_dec6"], "0.564156")
        self.assertEqual(p1["euv_rayleigh_metrology"]["cd_min_nm_q"], "81/11")
        self.assertEqual(p1["euv_rayleigh_metrology"]["dof_nm_q"], "2700/121")
        self.assertEqual(p1["euv_rayleigh_metrology"]["overlay_budget_nm_q"], "81/55")

        p2 = pl["pillar2_schur_offbrane_inertia_closure"]
        self.assertTrue(p2["all_verified"])
        r2 = p2["rank2_coupled_n3_n4"]
        self.assertEqual(r2["tau_crit_sturm_bracket_q"], ["186073/250000", "744293/1000000"])
        self.assertEqual(r2["subcritical_tau_1_2"]["schur_inertia_pos_zero_neg"], [4, 0, 0])
        self.assertEqual(r2["supercritical_collapsed_tau_1"]["schur_inertia_pos_zero_neg"], [3, 0, 1])
        self.assertEqual(r2["supercritical_collapsed_tau_1"]["full_inertia_pos_zero_neg"], [5, 0, 1])
        self.assertEqual(r2["insufficient_calibration_eta_1_4"]["schur_inertia_pos_zero_neg"], [3, 0, 1])
        self.assertEqual(r2["restored_calibration_eta_1_2"]["schur_inertia_pos_zero_neg"], [4, 0, 0])
        self.assertTrue(r2["s37_dark_shadow_energy"]["energy_decomposition_exact"])
        cm = p2["exact_common_mode_bifurcation"]
        self.assertEqual(cm["subcritical_spd"]["schur_inertia_pos_zero_neg"], [4, 0, 0])
        self.assertEqual(cm["critical_zero_det_boundary"]["schur_inertia_pos_zero_neg"], [3, 1, 0])
        self.assertEqual(cm["critical_zero_det_boundary"]["schur_det_q"], "0")
        self.assertEqual(cm["supercritical_collapsed"]["schur_inertia_pos_zero_neg"], [3, 0, 1])
        self.assertEqual(cm["calibration_above_min_restored_spd"]["schur_inertia_pos_zero_neg"], [4, 0, 0])

        p3 = pl["pillar3_leontief_euv_consumables_closure"]
        self.assertTrue(p3["all_verified"])
        self.assertEqual(p3["bulk_det_I_minus_ALL_q"], "17923/32000")
        self.assertEqual(p3["unclosed_consumables_blocked"]["schur_complement_S_VV_q"], "-25333/89615")
        self.assertEqual(p3["critical_leverage_scale_alpha_q"], "71692/97025")
        self.assertEqual(p3["critical_zero_det_boundary"]["det_I_minus_A5_q"], "0")
        self.assertEqual(p3["design_for_closure_restored"]["schur_complement_S_VV_q"], "72614/89615")
        self.assertEqual(p3["s46_bridge04_crosscheck"]["s46_schur_blocked_q"], "-331139/833770")

        p4 = pl["pillar4_plantgate_vs_schur_gate"]
        self.assertTrue(p4["all_verified"])
        self.assertTrue(p4["diagonal_plant_gate_result"]["admitted"])
        self.assertEqual(p4["candidate_uncalibrated_schur_regime"]["schur_inertia_pos_zero_neg"], [3, 0, 1])
        self.assertEqual(p4["candidate_calibrated_eta_1_schur_regime"]["schur_inertia_pos_zero_neg"], [4, 0, 0])
        self.assertFalse(p4["venturi_collar_dual_sensor_power_closure"]["single_collar_supports_n3_plus_n4"])
        self.assertEqual(p4["venturi_collar_dual_sensor_power_closure"]["min_collars_for_continuous_n3_n4"], 2)

    # ------------------------------------------------------------------
    # 5. Strict Parsers, Binding 3,321-Bit Cap & Canonical JSON
    # ------------------------------------------------------------------
    def test_05_parsers_binding_bit_cap_and_canonical_json(self) -> None:
        self.assertEqual(audit.require_hex64_lower_ascii("a" * 64), "a" * 64)
        self._expect_err("INVALID_HEX64", audit.require_hex64_lower_ascii, "a" * 63)
        self._expect_err("INVALID_HEX64", audit.require_hex64_lower_ascii, "A" * 64)
        self._expect_err("INVALID_HEX64", audit.require_hex64_lower_ascii, "g" * 64)
        self._expect_err("INVALID_STR", audit.require_hex64_lower_ascii, 123)

        self.assertEqual(audit.parse_exact_rational("0"), Fraction(0))
        self.assertEqual(audit.parse_exact_rational("-5"), Fraction(-5))
        self.assertEqual(audit.parse_exact_rational("-7/11"), Fraction(-7, 11))
        for bad in ("-0", "01", "", "-", "1/0", "1/1", "2/4", "1/2/3", "\u0661", "1/02", "9" * 1001):
            with self.assertRaises(oracle.OptifabSchurError):
                audit.parse_exact_rational(bad)

        max_ok = (1 << oracle.MAX_INT_BITS) - 1
        self.assertEqual(len(str(max_ok)), oracle.MAX_INT_DIGITS)
        rt = audit.parse_strict_json_text(f'{{"x":{max_ok}}}')
        self.assertEqual(rt["x"], max_ok)
        self.assertEqual(audit.canonical_json_bytes(rt), f'{{"x":{max_ok}}}'.encode("ascii"))

        self._expect_err("INT_BIT_LIMIT", audit._parse_bounded_int, "9" * 1000)
        self._expect_err("INT_BIT_LIMIT", audit.canonical_json_bytes, {"x": 1 << oracle.MAX_INT_BITS})
        self._expect_err("INT_BIT_LIMIT", audit.parse_strict_json_text, f'{{"x":{1 << oracle.MAX_INT_BITS}}}')
        self._expect_err("INT_DIGIT_LIMIT", audit.parse_strict_json_text, '{"x":1' + "0" * 4300 + "}")
        self._expect_err("FLOAT_LITERAL_FORBIDDEN", audit.parse_strict_json_text, '{"x":1.5}')
        self._expect_err("FLOAT_LITERAL_FORBIDDEN", audit.parse_strict_json_text, '{"x":1e2}')
        self._expect_err("NONFINITE_LITERAL_FORBIDDEN", audit.parse_strict_json_text, '{"x":NaN}')
        self._expect_err("DUPLICATE_JSON_KEY", audit.parse_strict_json_text, '{"a":1,"a":2}')
        self._expect_err("JSON_PARSE_ERROR", audit.parse_strict_json_text, '{"a":')
        self._expect_err("JSON_ROOT_NOT_OBJECT", audit.parse_strict_json_text, "[1,2]")
        self.assertEqual(audit.parse_strict_json_text("[1,null,true,false]", require_object=False), [1, None, True, False])
        self.assertEqual(audit.parse_strict_json_text('{"a":1}', max_bytes=7), {"a": 1})
        self._expect_err("JSON_TOO_LARGE", audit.parse_strict_json_text, '{"a":"0123456789"}', max_bytes=10)
        self._expect_err("INT_OUT_OF_RANGE", audit.parse_strict_json_text, "{}", max_bytes=1 << 100)
        self._expect_err("NUL_BYTE_FORBIDDEN", audit.parse_strict_json_text, '{"a":"\x00"}')
        self._expect_err("INVALID_UTF8_SURROGATE", audit.parse_strict_json_text, '{"a":"\ud800"}')
        self._expect_err("FORBIDDEN_JSON_TYPE", audit.canonical_json_bytes, {"a": {1, 2}})

        d64 = "[" * 64 + "0" + "]" * 64
        d65 = "[" * 65 + "0" + "]" * 65
        self.assertIsInstance(audit.parse_strict_json_text(d64, require_object=False), list)
        self._expect_err("JSON_DEPTH_LIMIT", audit.parse_strict_json_text, d65, require_object=False)
        self.assertEqual(audit.canonical_json_bytes({"b": "\u00e9", "a": 1}), b'{"a":1,"b":"\\u00e9"}')

    # ------------------------------------------------------------------
    # 6. Deep Secondary Auditor & 48 Re-Signed full_replay=False Tampers
    # ------------------------------------------------------------------
    def test_06_secondary_audit_and_resigned_tamper_matrix(self) -> None:
        self.assertTrue(audit.verify_certificate_dict(self.cert, full_replay=True)["valid"])
        self.assertTrue(audit.verify_certificate_dict(self.cert, full_replay=False)["valid"])
        self._expect_err("INVALID_BOOL_TYPE", audit.verify_certificate_dict, self.cert, full_replay=1)

        self._expect_err("INVALID_CERT_TYPE", audit.verify_certificate_dict, [])
        c_extra = copy.deepcopy(self.cert)
        c_extra["rogue"] = 1
        self._expect_err("INVALID_CERT_KEYS", audit.verify_certificate_dict, c_extra, full_replay=False)
        c_sch = copy.deepcopy(self.cert)
        c_sch["schema_version"] = "bad"
        self._expect_err("INVALID_SCHEMA", audit.verify_certificate_dict, c_sch, full_replay=False)
        c_tid = copy.deepcopy(self.cert)
        c_tid["track_id"] = "bad"
        self._expect_err("INVALID_TRACK_ID", audit.verify_certificate_dict, c_tid, full_replay=False)
        c_pt = copy.deepcopy(self.cert)
        c_pt["payload"] = []
        self._expect_err("INVALID_PAYLOAD_TYPE", audit.verify_certificate_dict, c_pt, full_replay=False)
        c_psha = copy.deepcopy(self.cert)
        c_psha["payload_sha256"] = "0" * 64
        self._expect_err("PAYLOAD_SHA256_MISMATCH", audit.verify_certificate_dict, c_psha, full_replay=False)
        c_csha = copy.deepcopy(self.cert)
        c_csha["certificate_sha256"] = "0" * 64
        self._expect_err("CERT_SHA256_MISMATCH", audit.verify_certificate_dict, c_csha, full_replay=False)
        self._expect_err("INVALID_SCHEMA_DICT", audit._req_dict, [], "row", frozenset())

        def mutate_and_expect(mutator, exp_code: str) -> None:
            pl = copy.deepcopy(self.payload)
            mutator(pl)
            resigned = _resign_payload(pl)
            self._expect_err(exp_code, audit.verify_certificate_dict, resigned, full_replay=False)

        tampers = [
            (lambda p: p.__setitem__("track_id", "WRONG"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p.__setitem__("portal_ref", "Portal 99"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p.__setitem__("novelty_class", "N0"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p.__setitem__("prior_literature_n0", ["forged"]), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p.__setitem__("extra_top", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar1_optifab_physical_anchors"].__setitem__("extra_p1", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar1_optifab_physical_anchors"]["euv_rayleigh_metrology"].__setitem__("extra_euv", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar1_optifab_physical_anchors"]["euv_rayleigh_metrology"].__setitem__("cd_min_nm_q", "7"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar1_optifab_physical_anchors"]["limit_states"][0].__setitem__("extra_row", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar1_optifab_physical_anchors"]["limit_states"][0].__setitem__("utilisation_q", "1/2"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar1_optifab_physical_anchors"]["limit_states"][0].__setitem__("headroom_q", "1/2"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar1_optifab_physical_anchors"]["limit_states"][0].__setitem__("capacity_q", "0"), "INVALID_CAPACITY"),
            (lambda p: p["pillar1_optifab_physical_anchors"].__setitem__("limit_states", {str(k): k for k in range(12)}), "INVALID_SCHEMA_LIST"),
            (lambda p: p["pillar1_optifab_physical_anchors"].__setitem__("limit_states", []), "INVALID_SCHEMA_LIST"),
            (lambda p: p["pillar1_optifab_physical_anchors"].__setitem__("limit_state_count", True), "INVALID_INT_TYPE"),
            (lambda p: p["pillar1_optifab_physical_anchors"].__setitem__("all_verified", 1), "INVALID_BOOL_TYPE"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"].__setitem__("extra_p2", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"].__setitem__("extra_r2", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["subcritical_tau_1_2"].__setitem__("extra_sr", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["subcritical_tau_1_2"].__setitem__("schur_det_q", "1/2"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["subcritical_tau_1_2"].__setitem__("schur_inertia_pos_zero_neg", [3, 0, 0]), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["subcritical_tau_1_2"].__setitem__("full_inertia_pos_zero_neg", [5, 0, 0]), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["subcritical_tau_1_2"].__setitem__("schur_strictly_spd", 1), "INVALID_BOOL_TYPE"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["s37_dark_shadow_energy"].__setitem__("extra_sh", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["rank2_coupled_n3_n4"]["s37_dark_shadow_energy"].__setitem__("full_energy_q", "99"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["exact_common_mode_bifurcation"].__setitem__("extra_cm", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar2_schur_offbrane_inertia_closure"]["exact_common_mode_bifurcation"].__setitem__("null_vector_exact_zero_residual", 1), "INVALID_BOOL_TYPE"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"].__setitem__("extra_p3", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["bulk_matrix_q"][0].__setitem__(0, "1/5"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["unclosed_consumables_blocked"].__setitem__("extra_b", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["unclosed_consumables_blocked"].__setitem__("schur_complement_S_VV_q", "1/2"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["unclosed_consumables_blocked"].__setitem__("schur_strictly_positive", True), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["critical_zero_det_boundary"].__setitem__("extra_c", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["critical_zero_det_boundary"].__setitem__("det_I_minus_A5_q", "1/2"), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["design_for_closure_restored"].__setitem__("extra_r", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["design_for_closure_restored"].__setitem__("rho_strictly_lt_1", 1), "INVALID_BOOL_TYPE"),
            (lambda p: p["pillar3_leontief_euv_consumables_closure"]["s46_bridge04_crosscheck"].__setitem__("extra_s46", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"].__setitem__("extra_p4", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["diagonal_plant_gate_result"].__setitem__("extra_g", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["diagonal_plant_gate_result"].__setitem__("dist_sq_ppm2", 99_999_999_999), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["diagonal_plant_gate_result"].__setitem__("radius_sq_ppm2", 1), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["diagonal_plant_gate_result"].__setitem__("remaining_budget", 64), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["diagonal_plant_gate_result"].__setitem__("admitted", 1), "INVALID_BOOL_TYPE"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["venturi_collar_dual_sensor_power_closure"].__setitem__("extra_v", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["venturi_collar_dual_sensor_power_closure"].__setitem__("single_collar_supports_n3_plus_n4", True), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["pillar4_plantgate_vs_schur_gate"]["venturi_collar_dual_sensor_power_closure"].__setitem__("min_collars_for_continuous_n3_n4", 1), "SECONDARY_AUDIT_FAILED"),
            (lambda p: p["summary"].__setitem__("extra_s", 1), "INVALID_SCHEMA_KEYS"),
            (lambda p: p["summary"].__setitem__("pillar_count", True), "INVALID_INT_TYPE"),
            (lambda p: p["summary"].__setitem__("all_four_pillars_verified", 1), "INVALID_BOOL_TYPE"),
            (lambda p: p["summary"].__setitem__("float_count_on_trust_path", 1), "SECONDARY_AUDIT_FAILED"),
        ]
        self.assertGreaterEqual(len(tampers), 48)
        for mutator, exp_code in tampers:
            mutate_and_expect(mutator, exp_code)

        with mock.patch.object(audit, "build_standalone_certificate", return_value={"payload_sha256": "0" * 64}):
            self._expect_err("REPLAY_MISMATCH", audit.verify_certificate_dict, self.cert, full_replay=True)

        # Direct secondary_audit_payload rejects same-value runtime floats, subclasses, and bool-in-int
        class _SubInt(int):
            pass

        class _SubStr(str):
            pass

        class _SubList(list):
            pass

        class _SubDict(dict):
            pass

        pl_flt = copy.deepcopy(self.payload)
        pl_flt["pillar4_plantgate_vs_schur_gate"]["baseline_u0_ppm"][0] = 801053 / 1
        self._expect_err("FORBIDDEN_JSON_TYPE", audit.secondary_audit_payload, pl_flt)

        pl_si = copy.deepcopy(self.payload)
        pl_si["pillar4_plantgate_vs_schur_gate"]["baseline_u0_ppm"][0] = _SubInt(801053)
        self._expect_err("FORBIDDEN_JSON_TYPE", audit.secondary_audit_payload, pl_si)

        pl_ss = copy.deepcopy(self.payload)
        pl_ss["track_id"] = _SubStr(oracle.TRACK_ID)
        self._expect_err("FORBIDDEN_JSON_TYPE", audit.secondary_audit_payload, pl_ss)

        pl_sl = copy.deepcopy(self.payload)
        pl_sl["prior_literature_n0"] = _SubList(pl_sl["prior_literature_n0"])
        self._expect_err("FORBIDDEN_JSON_TYPE", audit.secondary_audit_payload, pl_sl)

        pl_sd = copy.deepcopy(self.payload)
        pl_sd["summary"] = _SubDict(pl_sd["summary"])
        self._expect_err("FORBIDDEN_JSON_TYPE", audit.secondary_audit_payload, pl_sd)

    # ------------------------------------------------------------------
    # 7. Zone-B File I/O (Scratch mkfifo ONLY), Symlink/PWD/Hardlink & CLI
    # ------------------------------------------------------------------
    def test_07_zone_b_io_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            cert_path = root / "sub" / "cert.json"
            wres = audit.write_certificate_file(cert_path)
            self.assertTrue(wres["written"])
            self.assertEqual(stat.S_IMODE(os.lstat(cert_path).st_mode), 0o600)
            active_umask = os.umask(0o022)
            os.umask(active_umask)
            self.assertEqual(stat.S_IMODE(os.lstat(root / "sub").st_mode), 0o755 & ~active_umask)
            cres = audit.check_certificate_file(cert_path, full_replay=True)
            self.assertTrue(cres["valid"])
            self.assertEqual(cres["file_sha256"], wres["file_sha256"])

            missing_dir = root / "never_created"
            self._expect_err("FILE_READ_ERROR", audit.read_regular_bytes_capped, missing_dir / "x.json")
            self.assertFalse(missing_dir.exists())

            crlf_p = root / "crlf.json"
            crlf_p.write_bytes(cert_path.read_bytes().replace(b"\n", b"\r\n"))
            self._expect_err("CRLF_FORBIDDEN", audit.check_certificate_file, crlf_p)

            nolf_p = root / "nolf.json"
            nolf_p.write_bytes(cert_path.read_bytes()[:-1])
            self._expect_err("MISSING_TRAILING_LF", audit.check_certificate_file, nolf_p)

            badu_p = root / "badu.json"
            badu_p.write_bytes(b"\xff\xfe\n")
            self._expect_err("INVALID_UTF8", audit.check_certificate_file, badu_p)

            pretty_p = root / "pretty.json"
            pretty_p.write_bytes((json.dumps(self.cert, indent=2) + "\n").encode("utf-8"))
            self._expect_err("NON_CANONICAL_BYTES", audit.check_certificate_file, pretty_p)

            sym_leaf = root / "sym_leaf.json"
            os.symlink(cert_path, sym_leaf)
            self._expect_err("SYMLINK_FORBIDDEN", audit.read_regular_bytes_capped, sym_leaf)
            self._expect_err("SYMLINK_FORBIDDEN", audit.write_regular_bytes_safe, sym_leaf, b"x")

            sym_dir = root / "sym_dir"
            os.symlink(root / "sub", sym_dir)
            self._expect_err("SYMLINK_FORBIDDEN", audit.read_regular_bytes_capped, sym_dir / "cert.json")
            self._expect_err("SYMLINK_FORBIDDEN", audit.write_regular_bytes_safe, sym_dir / "new.json", b"x")

            self._expect_err("NOT_A_REGULAR_FILE", audit.read_regular_bytes_capped, root / "sub")
            self._expect_err("NOT_A_REGULAR_FILE", audit.write_regular_bytes_safe, root / "sub", b"x")
            self._expect_err("NOT_A_REGULAR_FILE", audit.read_regular_bytes_capped, Path("/"))
            self._expect_err("NOT_A_REGULAR_FILE", audit.read_regular_bytes_capped, missing_dir / "..")

            # Scratch FIFO ONLY (zero host device node touches)
            fifo_p = root / "pipe.fifo"
            os.mkfifo(fifo_p)
            self._expect_err("NOT_A_REGULAR_FILE", audit.read_regular_bytes_capped, fifo_p)
            self._expect_err("NOT_A_REGULAR_FILE", audit.write_regular_bytes_safe, fifo_p, b"x")

            hl_p = root / "hardlink.json"
            os.link(cert_path, hl_p)
            self._expect_err("HARDLINK_FORBIDDEN", audit.write_regular_bytes_safe, hl_p, b"x")
            os.unlink(hl_p)

            big_p = root / "big70k.bin"
            big_p.write_bytes(b"A" * 70_000)
            self.assertEqual(len(audit.read_regular_bytes_capped(big_p, "exact", 70_000)), 70_000)
            self._expect_err("FILE_TOO_LARGE", audit.read_regular_bytes_capped, big_p, "big", 65_536)
            if Path("/proc/kallsyms").exists():
                self._expect_err("FILE_TOO_LARGE", audit.read_regular_bytes_capped, Path("/proc/kallsyms"), "ks", 1024)

            fake_st = os.stat_result((stat.S_IFREG | 0o600, 1, 1, 2, 0, 0, 1, 0, 0, 0))
            with mock.patch.object(os, "fstat", return_value=fake_st):
                self._expect_err("HARDLINK_FORBIDDEN", audit.write_regular_bytes_safe, root / "race_nlink.bin", b"x")

            self._expect_err("INVALID_PATH_TYPE", audit.read_regular_bytes_capped, str(cert_path))  # type: ignore[arg-type]
            self._expect_err("INVALID_PAYLOAD_BYTES", audit.write_regular_bytes_safe, root / "t.bin", "str")  # type: ignore[arg-type]

            orig_cwd = os.getcwd()
            orig_pwd = os.environ.get("PWD")
            try:
                os.chdir(root)
                os.environ["PWD"] = str(root)
                rel_p = Path("rel_out.json")
                audit.write_regular_bytes_safe(rel_p, b"{}\n")
                self.assertEqual(audit.read_regular_bytes_capped(rel_p), b"{}\n")

                os.environ["PWD"] = str(root / "stale_nonexistent_pwd")
                self.assertEqual(audit.read_regular_bytes_capped(rel_p), b"{}\n")
                os.environ["PWD"] = str(root / "sub")
                self.assertEqual(audit.read_regular_bytes_capped(rel_p), b"{}\n")

                os.chdir(root / "sub")
                os.environ["PWD"] = str(sym_dir)
                self._expect_err("SYMLINK_ANCESTOR_FORBIDDEN", audit.read_regular_bytes_capped, Path("cert.json"))

                ghost = root / "ghost_dir"
                ghost.mkdir()
                os.chdir(ghost)
                os.environ["PWD"] = str(ghost)
                ghost.rmdir()
                self._expect_err("CWD_UNAVAILABLE", audit.read_regular_bytes_capped, Path("rel.json"))
            finally:
                os.chdir(orig_cwd)
                if orig_pwd is None:
                    os.environ.pop("PWD", None)
                else:
                    os.environ["PWD"] = orig_pwd

            root_lnk = SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_uid=0)
            root_dir = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
            user_lnk = SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_uid=1000)

            def _fake_readlink(p: str) -> str:
                if p == "/var":
                    return "private/var"
                if p == "/tmp":
                    return "/private/tmp"
                if p == "/etc":
                    return "private/etc"
                raise OSError("unexpected readlink")

            with (
                mock.patch.object(audit.sys, "platform", "darwin"),
                mock.patch.object(audit.os, "lstat", return_value=root_lnk),
                mock.patch.object(audit.os, "readlink", side_effect=_fake_readlink),
            ):
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/var/folders/xx/cert.json")),
                    Path("/private/var/folders/xx/cert.json"),
                )
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/tmp/cert.json")),
                    Path("/private/tmp/cert.json"),
                )
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/etc/cert.json")),
                    Path("/private/etc/cert.json"),
                )
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/opt/cert.json")),
                    Path("/opt/cert.json"),
                )
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("a/var/folders/xx/cert.json")),
                    Path("a/var/folders/xx/cert.json"),
                )
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/tmp"), allow_exact=True),
                    Path("/private/tmp"),
                )
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/"), allow_exact=True),
                    Path("/"),
                )
                self.assertEqual(audit._normalize_darwin_system_prefix(Path("/tmp")), Path("/tmp"))
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/tmp/../etc/passwd")),
                    Path("/tmp/../etc/passwd"),
                )
            for bad_stat in (root_dir, user_lnk):
                with (
                    mock.patch.object(audit.sys, "platform", "darwin"),
                    mock.patch.object(audit.os, "lstat", return_value=bad_stat),
                    mock.patch.object(audit.os, "readlink", side_effect=_fake_readlink),
                ):
                    self.assertEqual(
                        audit._normalize_darwin_system_prefix(Path("/var/folders/xx/cert.json")),
                        Path("/var/folders/xx/cert.json"),
                    )
            with (
                mock.patch.object(audit.sys, "platform", "darwin"),
                mock.patch.object(audit.os, "lstat", return_value=root_lnk),
                mock.patch.object(audit.os, "readlink", return_value="private/evil"),
            ):
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/var/folders/xx/cert.json")),
                    Path("/var/folders/xx/cert.json"),
                )
            with (
                mock.patch.object(audit.sys, "platform", "darwin"),
                mock.patch.object(audit.os, "lstat", side_effect=OSError("no access")),
            ):
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/var/folders/xx/cert.json")),
                    Path("/var/folders/xx/cert.json"),
                )
            with (
                mock.patch.object(audit.sys, "platform", "linux"),
                mock.patch.object(audit.os, "lstat", return_value=root_lnk),
                mock.patch.object(audit.os, "readlink", side_effect=_fake_readlink),
            ):
                self.assertEqual(
                    audit._normalize_darwin_system_prefix(Path("/var/folders/xx/cert.json")),
                    Path("/var/folders/xx/cert.json"),
                )

            rc, out, err = _call_main([])
            self.assertEqual((rc, err), (0, ""))
            self.assertIn("OK ", out)

            rc, out, err = _call_main(["--standalone", "--json"])
            self.assertEqual((rc, err), (0, ""))
            self.assertEqual(json.loads(out)["certificate_sha256"], self.cert["certificate_sha256"])

            cli_w = root / "cli_w.json"
            rc, out, err = _call_main(["--write", str(cli_w), "--json"])
            self.assertEqual((rc, err), (0, ""))
            self.assertTrue(json.loads(out)["written"])

            rc, out, err = _call_main(["--check", str(cli_w), "--json"])
            self.assertEqual((rc, err), (0, ""))
            self.assertTrue(json.loads(out)["valid"])

            cli_w2 = root / "cli_w2.json"
            rc, out, err = _call_main([f"--write={cli_w2}"])
            self.assertEqual((rc, err), (0, ""))
            rc, out, err = _call_main([f"--check={cli_w2}", "--json"])
            self.assertEqual((rc, err), (0, ""))
            self.assertTrue(json.loads(out)["valid"])

            for bad_argv, exp_code in (
                (["--unknown"], "UNKNOWN_FLAG"),
                (["--json", "--json"], "DUPLICATE_FLAG"),
                (["--standalone", "--check", str(cli_w)], "CONFLICTING_MODE"),
                (["--check", str(cli_w), "--standalone"], "CONFLICTING_MODE"),
                (["--standalone", f"--check={cli_w}"], "CONFLICTING_MODE"),
                (["--check"], "MISSING_PATH_ARG"),
                (["--check", ""], "INVALID_PATH_ARG"),
                (["--check", "-bad"], "INVALID_PATH_ARG"),
                (["--check="], "INVALID_PATH_ARG"),
                (["--write=-bad"], "INVALID_PATH_ARG"),
                (["--check", "a\x00b"], "NUL_BYTE_FORBIDDEN"),
            ):
                rc, _o, e = _call_main(bad_argv)
                self.assertEqual(rc, 2)
                self.assertEqual(json.loads(e)["error_code"], exp_code)

            rc, _o, e = _call_main("not-a-list")  # type: ignore[arg-type]
            self.assertEqual(rc, 2)
            self.assertEqual(json.loads(e)["error_code"], "INVALID_ARGV")

    # ------------------------------------------------------------------
    # 8. Concurrency & Kernel Races (16T/80T + 550 renameat2 + 550 hardlink)
    # ------------------------------------------------------------------
    def test_08_concurrency_and_kernel_races(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()

            errs: list[Exception] = []
            def w_distinct(idx: int) -> None:
                try:
                    p = root / f"d_{idx}.bin"
                    audit.write_regular_bytes_safe(p, f"payload-{idx}\n".encode("ascii"))
                    if stat.S_IMODE(os.lstat(p).st_mode) != 0o600:
                        raise RuntimeError("bad mode")
                except Exception as exc:
                    errs.append(exc)

            ts = [threading.Thread(target=w_distinct, args=(i,)) for i in range(16)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            self.assertEqual(errs, [])

            shared = root / "shared.bin"
            def w_same(idx: int) -> None:
                try:
                    audit.write_regular_bytes_safe(shared, f"v-{idx}\n".encode("ascii"))
                except Exception as exc:
                    errs.append(exc)

            for count in (16, 80):
                ts = [threading.Thread(target=w_same, args=(i,)) for i in range(count)]
                for t in ts:
                    t.start()
                for t in ts:
                    t.join()
            self.assertEqual(errs, [])
            self.assertEqual([p.name for p in root.iterdir() if p.name.endswith(".tmp")], [])

            if sys.platform == "linux":
                libc = ctypes.CDLL(None, use_errno=True)
                renameat2 = getattr(libc, "renameat2", None)
            else:
                renameat2 = None
            if renameat2 is not None:
                rename_exchange = 2
                at_fdcwd = -100
                victim_dir = root / "victim_outside"
                victim_dir.mkdir()
                real_sub = root / "race_slot_a"
                real_sub.mkdir()
                sym_sub = root / "race_slot_b"
                os.symlink(victim_dir, sym_sub)

                stop_flag = threading.Event()
                b_a = os.fsencode(str(real_sub))
                b_b = os.fsencode(str(sym_sub))

                def flipper() -> None:
                    while not stop_flag.is_set():
                        renameat2(at_fdcwd, b_a, at_fdcwd, b_b, rename_exchange)

                fl = threading.Thread(target=flipper)
                fl.start()
                try:
                    for i in range(550):
                        try:
                            audit.write_regular_bytes_safe(real_sub / "x.bin", f"{i}\n".encode("ascii"))
                        except oracle.OptifabSchurError:
                            pass
                finally:
                    stop_flag.set()
                    fl.join()
                self.assertEqual(list(victim_dir.iterdir()), [])

            hl_dir = root / "hl_race"
            hl_dir.mkdir()
            hl_target = hl_dir / "target.bin"
            hl_victim = hl_dir / "victim.bin"
            hl_victim.write_bytes(b"ORIGINAL_VICTIM\n")

            stop_hl = threading.Event()
            def hl_attacker() -> None:
                while not stop_hl.is_set():
                    try:
                        os.unlink(hl_target)
                    except OSError:
                        pass
                    try:
                        os.link(hl_victim, hl_target)
                    except OSError:
                        pass

            ha = threading.Thread(target=hl_attacker)
            ha.start()
            try:
                for i in range(550):
                    try:
                        audit.write_regular_bytes_safe(hl_target, f"safe-{i}\n".encode("ascii"))
                    except oracle.OptifabSchurError:
                        pass
            finally:
                stop_hl.set()
                ha.join()
            self.assertEqual(hl_victim.read_bytes(), b"ORIGINAL_VICTIM\n")


if __name__ == "__main__":
    unittest.main()
