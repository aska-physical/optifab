#!/usr/bin/env python3
"""Phase P0 + L0 (`optifab/q/`) pure-Q regression, golden replay, mutation, and AST guard suite.

Pure stdlib `unittest` (Python 3.10+ compatible, zero bare `assert`s, zero external runtime
dependencies, passes across `-I -B`, `-I -O -B`, and `-I -B -W error`).
"""

from __future__ import annotations

import ast
import copy
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from optifab.q import (  # noqa: E402
    Inertia,
    MAX_DEPTH,
    MAX_INPUT_BITS,
    MAX_NODES,
    MAX_PREC_BITS,
    MAX_TERMS,
    MIN_SQRT_TOL,
    OPTIFAB_CERT_PROFILE_ID,
    PI_QI,
    QI,
    QError,
    ZONE_CANON_V1_ASCII_PREFIX,
    block_split,
    encode_zone_canon_v1_ascii,
    exp_q,
    ldlt_exact,
    ldlt_reconstruct,
    legacy_tuple_agree,
    ln_q,
    mat_vec,
    of_ldlt_diag,
    of_pivot,
    of_s99,
    of_s102,
    permute_symmetric,
    profile_digest,
    q_from_int,
    q_from_str,
    q_to_str,
    qi_exp,
    qi_ln,
    qi_pow,
    qi_sqrt,
    quad_form,
    sha256_hex,
    signed_laplacian,
    solve_ldlt,
    sqrt_q,
    verify_farkas_eq,
    verify_farkas_ineq,
    verify_ldlt_admit,
    verify_refuse_witness,
)

GOLDEN_DIR = REPO_ROOT / "tests" / "golden"

_ALLOWED_L0_IMPORTS = frozenset({
    "__future__",
    "collections.abc",
    "dataclasses",
    "fractions",
    "hashlib",
    "typing",
})

_FORBIDDEN_L0_IMPORTS = frozenset({
    "cmath",
    "decimal",
    "math",
    "numpy",
    "os",
    "random",
    "scipy",
    "subprocess",
    "sympy",
    "sys",
})


def _load_json(name: str) -> dict:
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


def _parse_mat(rows: list[list[str]]) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(q_from_str(cell) for cell in row) for row in rows)


def _parse_vec(items: list[str]) -> tuple[Fraction, ...]:
    return tuple(q_from_str(cell) for cell in items)


class TestL0StaticGuards(unittest.TestCase):
    """AST enforcement: zero bare `assert`s, zero floats, strict L0 import DAG."""

    def test_zero_bare_asserts_zero_floats_and_strict_l0_imports(self) -> None:
        l0_files = sorted((REPO_ROOT / "optifab").rglob("*.py"))
        self.assertGreaterEqual(len(l0_files), 7)

        for py_path in l0_files + [Path(__file__).resolve()]:
            rel = py_path.relative_to(REPO_ROOT).as_posix()
            tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=rel)
            asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
            self.assertEqual(asserts, [], f"bare assert found in {rel}")

            if rel.startswith("optifab/"):
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, float):
                        self.fail(f"float literal {node.value!r} forbidden in {rel}:{node.lineno}")
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "float"
                    ):
                        self.fail(f"float() call forbidden in {rel}:{node.lineno}")

            if rel.startswith("optifab/q/"):
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            top = alias.name.split(".")[0]
                            self.assertNotIn(top, _FORBIDDEN_L0_IMPORTS, f"forbidden import {alias.name} in {rel}")
                            self.assertIn(alias.name, _ALLOWED_L0_IMPORTS, f"unallowlisted L0 import {alias.name} in {rel}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.level > 0:
                            continue
                        mod = node.module or ""
                        top = mod.split(".")[0]
                        self.assertNotIn(top, _FORBIDDEN_L0_IMPORTS, f"forbidden from-import {mod} in {rel}")
                        self.assertIn(mod, _ALLOWED_L0_IMPORTS, f"unallowlisted L0 from-import {mod} in {rel}")


class TestIntervalEnclosures(unittest.TestCase):
    """Exact QI arithmetic, type guards, pre-int() digit caps, and certified enclosures."""

    def test_qi_and_parser_reject_floats_bools_and_oversized_digits(self) -> None:
        with self.assertRaises(QError):
            QI(0, Fraction(1))  # type: ignore[arg-type]
        with self.assertRaises(QError):
            QI(float("0.5"), Fraction(1))  # type: ignore[arg-type]
        with self.assertRaises(QError):
            QI(Fraction(2), Fraction(1))
        with self.assertRaises(QError):
            q_from_int(True)
        with self.assertRaises(QError):
            q_from_int(float("1.0"))
        with self.assertRaises(QError):
            of_pivot(float("1.0"))  # type: ignore[arg-type]
        with self.assertRaises(QError):
            ldlt_exact([[float("1.0")]])  # type: ignore[list-item]
        with self.assertRaises(QError):
            q_from_str("1/0")
        with self.assertRaises(QError):
            q_from_str("1/2\n")
        with self.assertRaises(QError):
            q_from_str("+3/4")
        with self.assertRaises(QError):
            q_from_str("3/-4")

        # Reject non-canonical rationals and Fraction subclasses.
        for noncanon in ("-0", "007", "01/2", "1/02", "2/4", "3/1"):
            with self.assertRaises(QError) as ctx_nc:
                q_from_str(noncanon)
            self.assertEqual(ctx_nc.exception.code, "NONCANONICAL_RATIONAL")

        class _SubFraction(Fraction):
            pass

        sub = _SubFraction(1, 2)
        with self.assertRaises(QError):
            QI(sub, Fraction(1))
        with self.assertRaises(QError):
            of_pivot(sub)
        with self.assertRaises(QError):
            ldlt_exact([[sub]])

        # Pre-int() digit cap must block >4300-digit DoS strings even when int_max_str_digits=0.
        huge = "9" * 5000
        old_limit = sys.get_int_max_str_digits() if hasattr(sys, "get_int_max_str_digits") else None
        if old_limit is not None:
            sys.set_int_max_str_digits(0)
        try:
            for bad in (huge, f"{huge}/1", f"1/{huge}"):
                with self.assertRaises(QError) as ctx:
                    q_from_str(bad)
                self.assertEqual(ctx.exception.code, "DIGIT_CAP")
        finally:
            if old_limit is not None:
                sys.set_int_max_str_digits(old_limit)

        # Division by interval containing zero fails closed.
        with self.assertRaises(QError) as ctx_div:
            _ = QI.from_ints(1, 2) / QI.from_ints(-1, 1)
        self.assertEqual(ctx_div.exception.code, "DIV_BY_ZERO_INTERVAL")

    def test_interval_arithmetic_and_pi_enclosure(self) -> None:
        a = QI(Fraction(-2), Fraction(3))
        b = QI(Fraction(-4), Fraction(5))
        prod = a * b
        self.assertEqual(prod, QI(Fraction(-12), Fraction(15)))
        quot = QI(Fraction(2), Fraction(6)) / QI(Fraction(2), Fraction(3))
        self.assertEqual(quot, QI(Fraction(2, 3), Fraction(3)))
        self.assertEqual(PI_QI, QI(Fraction(103993, 33102), Fraction(355, 113)))
        self.assertLess(PI_QI.width, Fraction(3, 10_000_000))

    def test_certified_sqrt_exp_ln_and_pow_enclosures(self) -> None:
        for x in (
            Fraction(0),
            Fraction(1),
            Fraction(2),
            Fraction(3),
            Fraction(9, 16),
            Fraction(1, 10**12),
            Fraction(10**18 + 7, 13),
        ):
            iv = sqrt_q(x)
            self.assertLessEqual(iv.lo * iv.lo, x)
            self.assertGreaterEqual(iv.hi * iv.hi, x)
            self.assertLessEqual(iv.width, Fraction(1, 10**12))

        with self.assertRaises(QError):
            sqrt_q(Fraction(-1))
        with self.assertRaises(QError):
            ln_q(Fraction(0))
        with self.assertRaises(QError):
            ln_q(Fraction(-2))

        # Round-trip containment across wide dynamic range including deep negative exponents (B2/N1).
        for x in (
            Fraction(1, 10**200),
            Fraction(1, 100),
            Fraction(1, 3),
            Fraction(1),
            Fraction(2),
            Fraction(7, 3),
            Fraction(1000),
            Fraction(10**200),
        ):
            rt = qi_exp(ln_q(x))
            self.assertTrue(rt.contains(x), f"exp(ln(x)) does not contain x (bits={x.numerator.bit_length()})")

        for y in (
            Fraction(-500),
            Fraction(-100),
            Fraction(-67),
            Fraction(-66),
            Fraction(-10),
            Fraction(-3, 2),
            Fraction(-1, 10**200),
            Fraction(0),
            Fraction(1, 10**200),
            Fraction(1, 2),
            Fraction(1),
            Fraction(7),
            Fraction(100),
            Fraction(500),
        ):
            ey = exp_q(y)
            self.assertGreater(ey.lo, 0, f"exp_q({y}) collapsed lo to 0")
            self.assertLess((ey.hi - ey.lo) / ey.lo, Fraction(1, 1 << 80))
            rt = qi_ln(ey)
            self.assertTrue(rt.contains(y), f"ln(exp({y})) does not contain {y}")

        # B1 regression: 300-digit and 800-digit legal inputs must NOT hit default 4300-digit ValueError.
        ln10 = ln_q(Fraction(10))
        for power, huge_pos in (
            (300, Fraction(10**300)),
            (799, q_from_str("1" + "0" * 799)),
            (-799, q_from_str("1/" + "1" + "0" * 799)),
        ):
            ln_iv = ln_q(huge_pos)
            self.assertLessEqual(ln_iv.lo, ln_iv.hi)
            self.assertTrue(ln_iv.overlaps(QI.point(Fraction(power)) * ln10), f"ln(10^{power}) mismatch")
        for huge_tiny in (
            Fraction(1, 10**200),
            q_from_str("1/" + "1" + "0" * 799),
        ):
            ex_iv = exp_q(huge_tiny)
            self.assertGreaterEqual(ex_iv.lo, 1)
            self.assertGreater(ex_iv.hi, 1)
            self.assertTrue(qi_ln(ex_iv).contains(huge_tiny))
        sq_big = sqrt_q(q_from_str("1" + "0" * 799))
        self.assertLessEqual(sq_big.lo * sq_big.lo, q_from_str("1" + "0" * 799))
        self.assertGreaterEqual(sq_big.hi * sq_big.hi, q_from_str("1" + "0" * 799))

        # N2: upper ceilings on terms, prec_bits, tol, and input bit-length fail closed with QError.
        with self.assertRaises(QError):
            exp_q(Fraction(1), terms=MAX_TERMS + 1)
        with self.assertRaises(QError):
            exp_q(Fraction(1), prec_bits=MAX_PREC_BITS + 1)
        with self.assertRaises(QError):
            ln_q(Fraction(2), terms=MAX_TERMS + 1)
        with self.assertRaises(QError):
            sqrt_q(Fraction(2), tol=MIN_SQRT_TOL / 10)
        with self.assertRaises(QError):
            ln_q(Fraction(1 << (MAX_INPUT_BITS + 1)))

        # Algebraic identities: exp(a + b) overlaps exp(a) * exp(b); 2^(1/2) overlaps sqrt(2).
        e_sum = exp_q(Fraction(3, 2))
        e_prod = exp_q(Fraction(1, 2)) * exp_q(Fraction(1))
        self.assertTrue(e_sum.overlaps(e_prod))
        self.assertTrue(qi_pow(QI.point(Fraction(2)), QI.point(Fraction(1, 2))).overlaps(qi_sqrt(QI.point(Fraction(2)))))
        with self.assertRaises(QError):
            qi_pow(QI.point(Fraction(-2)), QI.point(Fraction(2)))


class TestInertiaAdapters(unittest.TestCase):
    """Named Inertia record and Lean-matching `legacy_tuple_agree` property."""

    def test_legacy_tuple_agree_exhaustive_and_pivot(self) -> None:
        for a in range(7):
            for b in range(7):
                for c in range(7):
                    self.assertEqual(legacy_tuple_agree(a, b, c), b == c)
                    s99 = of_s99(a, b, c)
                    s102 = of_s102(a, b, c)
                    self.assertEqual(s99.pos, a)
                    self.assertEqual(s99.zero, b)
                    self.assertEqual(s99.neg, c)
                    self.assertEqual(s102.pos, a)
                    self.assertEqual(s102.neg, b)
                    self.assertEqual(s102.zero, c)
                    self.assertEqual(s99.dim, a + b + c)

        self.assertEqual(of_pivot(Fraction(1, 7)), Inertia(pos=1, neg=0, zero=0))
        self.assertEqual(of_pivot(Fraction(-1, 7)), Inertia(pos=0, neg=1, zero=0))
        self.assertEqual(of_pivot(Fraction(0)), Inertia(pos=0, neg=0, zero=1))

        with self.assertRaises(QError):
            Inertia(pos=-1, neg=0, zero=0)
        with self.assertRaises(QError):
            Inertia(pos=True, neg=0, zero=0)  # type: ignore[arg-type]


class TestPhaseP0Goldens(unittest.TestCase):
    """Exact pure-Q replay of all Phase P0 golden witnesses and zone-canon-v1:ascii: vectors."""

    def _verify_receipt(self, doc: dict) -> None:
        body = {k: v for k, v in doc.items() if k != "receipt_sha256"}
        self.assertEqual(doc["profile_id"], OPTIFAB_CERT_PROFILE_ID.decode("ascii"))
        self.assertEqual(doc["receipt_sha256"], profile_digest(OPTIFAB_CERT_PROFILE_ID, body))

    def test_s99_schur_golden_exact_replay(self) -> None:
        doc = _load_json("s99_schur_golden.json")
        self._verify_receipt(doc)
        sys_block = doc["system"]
        self.assertEqual(doc["system_sha256"], profile_digest(OPTIFAB_CERT_PROFILE_ID, sys_block))

        A = _parse_mat(sys_block["A"])
        B0 = _parse_mat(sys_block["B0"])
        D = _parse_mat(sys_block["D"])

        # eta = 1 ADMIT
        M1 = block_split(A, B0, D, eta=Fraction(1))
        L1_gold = _parse_mat(doc["eta1_admit"]["L"])
        d1_gold = _parse_vec(doc["eta1_admit"]["d"])
        L1_calc, d1_calc = ldlt_exact(M1)
        self.assertEqual(L1_calc, L1_gold)
        self.assertEqual(d1_calc, d1_gold)
        self.assertTrue(verify_ldlt_admit(M1, L1_gold, d1_gold))
        self.assertEqual(of_ldlt_diag(d1_calc).to_dict(), {"pos": 6, "neg": 0, "zero": 0})
        self.assertEqual(of_ldlt_diag(d1_calc[:4]).to_dict(), {"pos": 4, "neg": 0, "zero": 0})
        self.assertEqual(of_ldlt_diag(d1_calc[4:]).to_dict(), {"pos": 2, "neg": 0, "zero": 0})

        # eta = 3 REFUSE_SCHUR
        M3 = block_split(A, B0, D, eta=Fraction(3))
        v3 = _parse_vec(doc["eta3_refuse"]["v"])
        ok_ref, qv = verify_refuse_witness(M3, v3)
        self.assertTrue(ok_ref)
        self.assertEqual(qv, Fraction(-464071, 1247200))
        self.assertEqual(q_to_str(qv), doc["eta3_refuse"]["vTMv"])
        _, d3 = ldlt_exact(M3)
        self.assertEqual(of_ldlt_diag(d3).to_dict(), {"pos": 5, "neg": 1, "zero": 0})
        self.assertEqual(of_ldlt_diag(d3[4:]).to_dict(), {"pos": 1, "neg": 1, "zero": 0})

        # Headroom cross-product & residency cliff
        hr = doc["headroom_comparison"]
        vram_h = q_from_str(hr["vram_headroom"])
        floor_h = q_from_str(hr["floor_punching_headroom"])
        self.assertEqual(vram_h, Fraction(1635789, 8388608))
        self.assertEqual(floor_h, Fraction(27419, 137820))
        self.assertEqual(vram_h.numerator * floor_h.denominator, 225444439980)
        self.assertEqual(floor_h.numerator * vram_h.denominator, 230007242752)
        self.assertLess(vram_h, floor_h)
        self.assertEqual(q_from_str(hr["b_crit_bpw"]), Fraction(325, 171))

    def test_cx6_farkas_and_s102_supergraph_golden_exact_replay(self) -> None:
        doc = _load_json("cx6_farkas_golden.json")
        self._verify_receipt(doc)
        sys_block = doc["system"]
        self.assertEqual(doc["system_sha256"], profile_digest(OPTIFAB_CERT_PROFILE_ID, sys_block))
        self.assertEqual(
            sys_block["anchor_payload_sha256"],
            "f72c14e984f0c247fb44f9d5049a7575d8962eef6f16cacd243231f2a6a553ad",
        )

        L_cx = signed_laplacian(sys_block["cx6_dale_signed_synapses"])
        ones6 = tuple(Fraction(1) for _ in range(6))
        self.assertEqual(quad_form(L_cx, ones6), Fraction(514732))
        self.assertEqual(doc["cx6_farkas"]["ones_T_L_ones"], 514732)

        L_f, d_f = ldlt_exact(L_cx)
        q_calc = solve_ldlt(L_f, d_f, ones6)
        q_gold = _parse_vec(doc["cx6_farkas"]["q"])
        self.assertEqual(q_calc, q_gold)
        self.assertEqual(mat_vec(L_cx, q_calc), ones6)
        sum_q = sum(q_calc, Fraction(0))
        self.assertEqual(sum_q, Fraction(3290626468374561095072, 13565664147358331824076959))
        self.assertEqual(q_to_str(sum_q), doc["cx6_farkas"]["ones_T_q"])

        A_aug = list(L_cx) + [ones6]
        b_aug = tuple(Fraction(0) for _ in range(6)) + (Fraction(1),)
        p_gold = _parse_vec(doc["cx6_farkas"]["p"])
        ok_f, msg_f = verify_farkas_eq(A_aug, b_aug, p_gold)
        self.assertTrue(ok_f, msg_f)

        # EPG|PFL Schur pivots
        L_perm = permute_symmetric(L_cx, doc["cx6_farkas"]["epg_pfl_order"])
        _, d_perm = ldlt_exact(L_perm)
        self.assertEqual(d_perm[4], Fraction(23216477313908228763757, 699500715061237130))
        self.assertEqual(d_perm[4] * d_perm[5], Fraction(27131328294716663648153918, 69950071506123713))
        self.assertEqual(q_to_str(d_perm[4]), doc["cx6_farkas"]["epg_pfl_a"])
        self.assertEqual(q_to_str(d_perm[4] * d_perm[5]), doc["cx6_farkas"]["epg_pfl_delta"])

        # S102 8-module supergraph inertia
        L8 = signed_laplacian(sys_block["supergraph8_dale_signed_synapses"])
        L8_perm = permute_symmetric(L8, doc["supergraph8_inertia"]["order_interior_then_boundary"])
        _, d8 = ldlt_exact(L8_perm)
        self.assertEqual(of_ldlt_diag(d8).to_dict(), {"pos": 8, "neg": 0, "zero": 0})
        self.assertEqual(of_ldlt_diag(d8[:5]).to_dict(), {"pos": 5, "neg": 0, "zero": 0})
        self.assertEqual(of_ldlt_diag(d8[5:]).to_dict(), {"pos": 3, "neg": 0, "zero": 0})

    def test_v04_pins_and_zone_canon_v1_del_and_dos_guards(self) -> None:
        pins = _load_json("v04_pins.json")
        self._verify_receipt(pins)
        s99 = _load_json("s99_schur_golden.json")
        cx6 = _load_json("cx6_farkas_golden.json")
        self.assertEqual(pins["golden_files"]["s99_schur_golden.json"], s99["receipt_sha256"])
        self.assertEqual(pins["golden_files"]["cx6_farkas_golden.json"], cx6["receipt_sha256"])
        self.assertEqual(
            pins["optifab_anchors"]["historical_pre_p2_baseline"]["commit"],
            "401e081f72476b13fdbf3d8fe7a1686c3a4be851",
        )
        self.assertEqual(
            pins["optifab_anchors"]["post_pr21_main_base"]["commit"],
            "012f8bbf757849d0fffa2057ef2bb7bbb755760d",
        )
        self.assertEqual(pins["lean_toolchains"]["existing_formal_dir"], "leanprover/lean4:v4.35.0")
        self.assertEqual(pins["lean_toolchains"]["target_v04_l3"], "leanprover/lean4:v4.36.0")

        # 0x7F DEL vector must escape to \u007f and match stdlib json.dumps(ensure_ascii=True).
        dv = pins["zone_canon_v1_del_vector"]
        raw = encode_zone_canon_v1_ascii(dv["input"])
        self.assertIn(b"\\u007f", raw)
        self.assertNotIn(b"\x7f", raw)
        self.assertEqual(raw.decode("ascii"), dv["canonical_ascii"])
        self.assertEqual(profile_digest(OPTIFAB_CERT_PROFILE_ID, dv["input"]), dv["profile_digest_sha256"])
        self.assertEqual(
            raw.decode("ascii"),
            json.dumps(dv["input"], sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False),
        )

        # Astral code point surrogate pair parity (U+1F600 -> \ud83d\ude00) and mixed-plane code-point sort (N4).
        astral = {"emoji": "\U0001f600"}
        self.assertEqual(
            encode_zone_canon_v1_ascii(astral).decode("ascii"),
            json.dumps(astral, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False),
        )
        mixed_plane = {"\U0001f600": 2, "\ue000": 1}
        mp_enc = encode_zone_canon_v1_ascii(mixed_plane).decode("ascii")
        self.assertEqual(
            mp_enc,
            json.dumps(mixed_plane, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False),
        )
        self.assertTrue(mp_enc.startswith('{"\\ue000":1,"\\ud83d\\ude00":2}'))

        # N6/N9: profile_digest requires ZONE_CANON_V1_ASCII_PREFIX + non-empty profile name; sha256_hex requires bytes.
        with self.assertRaises(QError):
            profile_digest(b"wrong-prefix", {"a": 1})
        with self.assertRaises(QError):
            profile_digest(ZONE_CANON_V1_ASCII_PREFIX, {"a": 1})
        with self.assertRaises(QError):
            sha256_hex(bytearray(b"abc"))  # type: ignore[arg-type]

        # Reject NUL, lone surrogate, float, Fraction, out-of-range int256, non-str key, depth>64, nodes>4096.
        for bad_obj, expected_code in (
            ({"a": "x\x00y"}, "NUL_FORBIDDEN"),
            ({"a": "\ud800"}, "SURROGATE_FORBIDDEN"),
            ({"a": float("1.5")}, "UNSUPPORTED_TYPE"),
            ({"a": Fraction(1, 2)}, "UNSUPPORTED_TYPE"),
            ({"a": 1 << 255}, "INT_OUT_OF_RANGE"),
            ({1: "bad"}, "NON_STR_KEY"),
        ):
            with self.assertRaises(QError) as ctx:
                encode_zone_canon_v1_ascii(bad_obj)
            self.assertEqual(ctx.exception.code, expected_code)

        # N5: Exact depth boundary (empty [] at depth 64 allowed; scalar inside depth-64 container is depth 65 -> rejected).
        at_64: object = []
        for _ in range(MAX_DEPTH):
            at_64 = [at_64]
        self.assertTrue(len(encode_zone_canon_v1_ascii(at_64)) > 0)
        deep: object = 1
        for _ in range(MAX_DEPTH + 1):
            deep = [deep]
        with self.assertRaises(QError) as ctx_d:
            encode_zone_canon_v1_ascii(deep)
        self.assertEqual(ctx_d.exception.code, "DEPTH_EXCEEDED")

        # N3: Pre-expansion node and astral byte-cap rejections.
        wide = [0] * (MAX_NODES + 1)
        with self.assertRaises(QError) as ctx_n:
            encode_zone_canon_v1_ascii(wide)
        self.assertEqual(ctx_n.exception.code, "NODES_EXCEEDED")
        wide_dict = {f"k{i}": 0 for i in range(MAX_NODES + 1)}
        with self.assertRaises(QError) as ctx_nd:
            encode_zone_canon_v1_ascii(wide_dict)
        self.assertEqual(ctx_nd.exception.code, "NODES_EXCEEDED")
        with self.assertRaises(QError) as ctx_sz:
            encode_zone_canon_v1_ascii({"big": "\U0001f600" * 100_000})
        self.assertEqual(ctx_sz.exception.code, "INPUT_TOO_LARGE")

        # N7/N8: permute_symmetric rejects generator/set with QError; of_ldlt_diag rejects empty sequence.
        m2 = ((Fraction(2), Fraction(0)), (Fraction(0), Fraction(3)))
        with self.assertRaises(QError):
            permute_symmetric(m2, (i for i in range(2)))  # type: ignore[arg-type]
        with self.assertRaises(QError):
            permute_symmetric(m2, {0, 1})  # type: ignore[arg-type]
        with self.assertRaises(QError):
            of_ldlt_diag([])


class TestWitnessMutationKills(unittest.TestCase):
    """Fail-closed mutation gate: perturbing any entry of L, d, v, p, or system_sha256 breaks replay."""

    def test_perturbing_every_s99_ldlt_and_refuse_entry_is_rejected(self) -> None:
        doc = _load_json("s99_schur_golden.json")
        A = _parse_mat(doc["system"]["A"])
        B0 = _parse_mat(doc["system"]["B0"])
        D = _parse_mat(doc["system"]["D"])
        M1 = block_split(A, B0, D, eta=Fraction(1))
        L1 = _parse_mat(doc["eta1_admit"]["L"])
        d1 = _parse_vec(doc["eta1_admit"]["d"])

        # Perturb every single entry of L1 -> verify_ldlt_admit MUST return False.
        for i in range(6):
            for j in range(6):
                mut_L = [list(row) for row in L1]
                mut_L[i][j] += Fraction(1, 1000)
                self.assertFalse(verify_ldlt_admit(M1, mut_L, d1), f"L[{i}][{j}] mutation survived")

        # Perturb every single pivot of d1 -> verify_ldlt_admit MUST return False.
        for k in range(6):
            mut_d = list(d1)
            mut_d[k] += Fraction(1, 1000)
            self.assertFalse(verify_ldlt_admit(M1, L1, mut_d), f"d[{k}] mutation survived")
            neg_d = list(d1)
            neg_d[k] = -neg_d[k]
            self.assertFalse(verify_ldlt_admit(M1, L1, neg_d), f"sign-flipped d[{k}] survived")

        # Non-zero witness on positive-definite M1 must be rejected; zero vector on M3 must be rejected.
        M3 = block_split(A, B0, D, eta=Fraction(3))
        v3 = _parse_vec(doc["eta3_refuse"]["v"])
        ok_m1, qv_m1 = verify_refuse_witness(M1, v3)
        self.assertFalse(ok_m1)
        self.assertGreater(qv_m1, 0)
        ok_zero, qv_zero = verify_refuse_witness(M3, (Fraction(0),) * 6)
        self.assertFalse(ok_zero)
        self.assertEqual(qv_zero, 0)

        # System hash binding: mutating any entry of A breaks system_sha256.
        mut_sys = copy.deepcopy(doc["system"])
        mut_sys["A"][0][0] = "3"
        self.assertNotEqual(profile_digest(OPTIFAB_CERT_PROFILE_ID, mut_sys), doc["system_sha256"])

        # Reconstruction exactness check.
        self.assertEqual(ldlt_reconstruct(L1, d1), M1)

    def test_farkas_eq_and_ineq_reject_hollow_and_perturbed_witnesses(self) -> None:
        doc = _load_json("cx6_farkas_golden.json")
        L_cx = signed_laplacian(doc["system"]["cx6_dale_signed_synapses"])
        ones6 = tuple(Fraction(1) for _ in range(6))
        A_aug = list(L_cx) + [ones6]
        b_aug = tuple(Fraction(0) for _ in range(6)) + (Fraction(1),)
        p_gold = _parse_vec(doc["cx6_farkas"]["p"])

        # Perturbing any single entry of p breaks verify_farkas_eq.
        for idx in range(len(p_gold)):
            mut_p = list(p_gold)
            mut_p[idx] += Fraction(1, 10**6)
            ok_m, _ = verify_farkas_eq(A_aug, b_aug, mut_p)
            self.assertFalse(ok_m, f"Farkas p[{idx}] mutation survived")

        # Hollow witness p = (0, 1) on an incompatible 2x1 system where p^T A != 0 MUST fail.
        A_hollow = ((Fraction(1),), (Fraction(1),))
        b_hollow = (Fraction(0), Fraction(1))
        ok_h, _ = verify_farkas_eq(A_hollow, b_hollow, (Fraction(0), Fraction(1)))
        self.assertFalse(ok_h)

        # Valid Farkas inequality witness for x <= -1, -x <= 0 (infeasible): p = (1, 1) -> p^T A = 0, p^T b = -1 < 0.
        A_in = ((Fraction(1),), (Fraction(-1),))
        b_in = (Fraction(-1), Fraction(0))
        ok_in, msg_in = verify_farkas_ineq(A_in, b_in, (Fraction(1), Fraction(1)))
        self.assertTrue(ok_in, msg_in)
        # Negative p entry rejected even if p^T A = 0 and p^T b < 0.
        ok_neg, _ = verify_farkas_ineq(A_in, (Fraction(1), Fraction(0)), (Fraction(-1), Fraction(-1)))
        self.assertFalse(ok_neg)
        # Non-negative p^T b >= 0 rejected.
        ok_posb, _ = verify_farkas_ineq(A_in, (Fraction(1), Fraction(0)), (Fraction(1), Fraction(1)))
        self.assertFalse(ok_posb)
        # p^T A != 0 rejected.
        ok_bad_a, _ = verify_farkas_ineq(A_in, b_in, (Fraction(2), Fraction(1)))
        self.assertFalse(ok_bad_a)


if __name__ == "__main__":
    unittest.main()
