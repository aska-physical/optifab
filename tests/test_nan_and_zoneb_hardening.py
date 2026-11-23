"""Regression and Zone-B hardening test suite for aska-physical/optifab.

Runs with stdlib-only under ``-I -B``, ``-I -O -B``, and ``-I -B -W error`` (zero bare ``assert``s).
If ``sympy`` is not installed in a clean-room environment, stubs ``sympy`` solely to import
the non-SymPy functions and ``main()`` from ``verify.py`` without altering any symbolic checks.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import verify_guards  # noqa: E402


class _EvilPath(type(Path("."))):
    """Adversarial Path subclass that must be rejected by coerce_exact_path."""


class _FloatSubclass(float):
    """Adversarial float subclass that must be rejected by require_finite."""


def _import_verify_module():
    if "verify" in sys.modules:
        return sys.modules["verify"]
    try:
        return importlib.import_module("verify")
    except ModuleNotFoundError as exc:
        if exc.name != "sympy":
            raise
        stub = types.ModuleType("sympy")
        with mock.patch.dict(sys.modules, {"sympy": stub}):
            return importlib.import_module("verify")


class TestVerifyGuardsUnit(unittest.TestCase):
    def test_constants_pinned(self) -> None:
        self.assertEqual(verify_guards.MAX_JSON_BYTES, 10485760)
        self.assertEqual(verify_guards.MAX_JSON_DEPTH, 64)
        self.assertEqual(verify_guards.MAX_INT_DIGITS, 1000)

    def test_require_finite_and_strict_max(self) -> None:
        val_int = verify_guards.require_finite(5, "x")
        self.assertIs(type(val_int), float)
        self.assertEqual(val_int, 5.0)
        self.assertEqual(verify_guards.require_finite(-2.25, "y"), -2.25)

        for bad in (
            True,
            False,
            None,
            "1.0",
            1 + 0j,
            float("nan"),
            float("inf"),
            float("-inf"),
            10**400,
            -(10**400),
            _FloatSubclass(1.0),
        ):
            with self.assertRaises(ValueError):
                verify_guards.require_finite(bad, "bad")

        @verify_guards.fail_closed_cli
        def _ok_cli() -> int:
            return 0

        @verify_guards.fail_closed_cli
        def _bad_cli() -> int:
            raise ValueError("planted cli failure")

        self.assertEqual(_ok_cli(), 0)
        self.assertEqual(_bad_cli(), 1)

        self.assertEqual(verify_guards.strict_finite_max(0.0, 0.5), 0.5)
        self.assertEqual(verify_guards.strict_finite_max(0.5, 0.0), 0.5)
        self.assertEqual(verify_guards.strict_finite_max(-2.0, -2), -2.0)

        for pair in (
            (0.0, float("nan")),
            (float("nan"), 0.0),
            (0.0, float("inf")),
            (float("-inf"), 0.0),
            (1.0, True),
            (False, 1.0),
        ):
            with self.assertRaises(ValueError):
                verify_guards.strict_finite_max(*pair)

        self.assertEqual(verify_guards.strict_finite_max_iter([0.2, 0.8, 0.4]), 0.8)
        self.assertEqual(verify_guards.strict_finite_max_iter(x for x in (-3, -1)), -1.0)
        with self.assertRaisesRegex(ValueError, "must be non-empty"):
            verify_guards.strict_finite_max_iter([])
        for bad_seq in ([0.2, float("nan")], [float("nan"), 0.2], [0.2, float("inf")], [0.2, True]):
            with self.assertRaises(ValueError):
                verify_guards.strict_finite_max_iter(bad_seq)

    def test_coerce_exact_path(self) -> None:
        p1 = verify_guards.coerce_exact_path("results/certificate.json")
        self.assertEqual(p1, Path("results/certificate.json"))
        p2 = Path("results/certificate.json")
        self.assertIs(verify_guards.coerce_exact_path(p2), p2)

        for bad in ("", "a\x00b", Path("a\x00b"), _EvilPath("results/certificate.json"), b"abc", 42, None):
            with self.assertRaises(ValueError):
                verify_guards.coerce_exact_path(bad)

    def test_reject_symlinks_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real_dir = root / "real"
            real_dir.mkdir()
            real_file = real_dir / "ok.json"
            real_file.write_text("{}\n", encoding="utf-8")

            verify_guards.reject_symlinks_on_path(real_file)

            file_link = root / "link.json"
            file_link.symlink_to(real_file)
            with self.assertRaises(ValueError):
                verify_guards.reject_symlinks_on_path(file_link)

            broken_link = root / "broken.json"
            broken_link.symlink_to(root / "does_not_exist.json")
            with self.assertRaises(ValueError):
                verify_guards.reject_symlinks_on_path(broken_link)

            dir_link = root / "dir_link"
            dir_link.symlink_to(real_dir)
            with self.assertRaises(ValueError):
                verify_guards.reject_symlinks_on_path(dir_link / "ok.json")

            traversal = dir_link / ".." / "real" / "ok.json"
            with self.assertRaises(ValueError):
                verify_guards.reject_symlinks_on_path(traversal)

    def test_strict_loads_json_zone_b_matrix(self) -> None:
        self.assertEqual(verify_guards.strict_loads_json('{"a": 1, "b": [-2.5, "ok"]}'), {"a": 1, "b": [-2.5, "ok"]})

        exact_10 = '{"a":1234}'
        self.assertEqual(len(exact_10), 10)
        self.assertEqual(verify_guards.strict_loads_json(exact_10, max_bytes=10), {"a": 1234})
        with self.assertRaisesRegex(ValueError, "text length out of bounds"):
            verify_guards.strict_loads_json(exact_10 + " ", max_bytes=10)

        for bad in (b"{}", None, 123):
            with self.assertRaisesRegex(ValueError, "must be str"):
                verify_guards.strict_loads_json(bad)
        with self.assertRaisesRegex(ValueError, "text length out of bounds"):
            verify_guards.strict_loads_json("")
        with self.assertRaisesRegex(ValueError, "UTF-8 BOM rejected"):
            verify_guards.strict_loads_json("\ufeff{}")
        for cr_bad in ("{}\r", "{\r\n}"):
            with self.assertRaisesRegex(ValueError, "CR/CRLF"):
                verify_guards.strict_loads_json(cr_bad)

        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json('{"k": 1, "k": 2}')
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json('{"outer": {"k": 1, "k": 2}}')

        for bad_num in ("NaN", "Infinity", "-Infinity", "1e500", "-1e500"):
            with self.assertRaises(ValueError):
                verify_guards.strict_loads_json(f'{{"x": {bad_num}}}')

        max_pos = "9" * 1000
        max_neg = "-" + max_pos
        self.assertEqual(verify_guards.strict_loads_json(f'{{"n": {max_pos}}}')["n"], int(max_pos))
        self.assertEqual(verify_guards.strict_loads_json(f'{{"n": {max_neg}}}')["n"], int(max_neg))
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json(f'{{"n": {"9" * 1001}}}')
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json(f'{{"n": -{"9" * 1001}}}')

        list_64 = "[" * 64 + "0" + "]" * 64
        list_65 = "[" * 65 + "0" + "]" * 65
        self.assertIsInstance(verify_guards.strict_loads_json(list_64), list)
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json(list_65)

        dict_64 = '{"a":' * 64 + "0" + "}" * 64
        dict_65 = '{"a":' * 65 + "0" + "}" * 65
        self.assertIsInstance(verify_guards.strict_loads_json(dict_64), dict)
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json(dict_65)

        self.assertEqual(verify_guards.strict_loads_json("[[1]]", max_depth=2), [[1]])
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json("[[[1]]]", max_depth=2)

        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json("{")
        with self.assertRaises(ValueError):
            verify_guards.strict_loads_json("[" * 5000 + "]" * 5000)

    def test_strict_parse_json_bytes_and_read_regular(self) -> None:
        utf8_omega = b'{"a":"\xce\xa9"}'
        self.assertEqual(len(utf8_omega), 10)
        self.assertEqual(verify_guards.strict_parse_json_bytes(utf8_omega, max_bytes=10), {"a": "\u03a9"})
        with self.assertRaisesRegex(ValueError, "byte length out of bounds"):
            verify_guards.strict_parse_json_bytes(utf8_omega, max_bytes=9)
        with self.assertRaisesRegex(ValueError, "byte length out of bounds"):
            verify_guards.strict_parse_json_bytes(b"")

        self.assertEqual(verify_guards.strict_parse_json_bytes(b"[1]", max_depth=1), [1])
        with self.assertRaises(ValueError):
            verify_guards.strict_parse_json_bytes(b"[[1]]", max_depth=1)

        for bad in ("{}", bytearray(b"{}")):
            with self.assertRaisesRegex(ValueError, "must be bytes"):
                verify_guards.strict_parse_json_bytes(bad)
        with self.assertRaisesRegex(ValueError, "UTF-8 BOM rejected"):
            verify_guards.strict_parse_json_bytes(b"\xef\xbb\xbf{}")
        with self.assertRaisesRegex(ValueError, "CR/CRLF"):
            verify_guards.strict_parse_json_bytes(b"{}\r")
        with self.assertRaisesRegex(ValueError, "invalid UTF-8"):
            verify_guards.strict_parse_json_bytes(b"\xff\xfe")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            good = root / "good.json"
            good.write_bytes(b'{"a":1}\n')
            self.assertEqual(verify_guards.strict_read_json(good), {"a": 1})
            self.assertEqual(verify_guards.strict_read_json(str(good)), {"a": 1})
            self.assertEqual(verify_guards._read_regular_bytes(good, max_bytes=8), b'{"a":1}\n')

            with self.assertRaisesRegex(ValueError, "file size out of bounds"):
                verify_guards.strict_read_json(good, max_bytes=7)
            with self.assertRaises(ValueError):
                verify_guards.strict_read_json(good, max_depth=0)

            empty = root / "empty.json"
            empty.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "file size out of bounds"):
                verify_guards._read_regular_bytes(empty)

            with self.assertRaisesRegex(ValueError, "cannot stat"):
                verify_guards.strict_read_json(root / "missing.json")
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                verify_guards.strict_read_json(root)

            fifo = root / "pipe.json"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                verify_guards.strict_read_json(fifo)

            if os.geteuid() != 0:
                locked = root / "locked.json"
                locked.write_bytes(b"{}\n")
                locked.chmod(0)
                try:
                    with self.assertRaises(ValueError):
                        verify_guards._read_regular_bytes(locked)
                finally:
                    locked.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_canonical_bytes_and_verify_file(self) -> None:
        payload = {"b": 1, "a": 0.0, "flag": True, "u": "\u03a9"}
        raw_default = verify_guards.canonical_json_bytes(payload)
        self.assertEqual(
            raw_default,
            (json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n").encode("utf-8"),
        )
        raw_sorted = verify_guards.canonical_json_bytes(payload, indent=1, sort_keys=True, ensure_ascii=True)
        self.assertEqual(
            raw_sorted,
            (json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8"),
        )
        with self.assertRaises(ValueError):
            verify_guards.canonical_json_bytes({"x": float("nan")})

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f_def = root / "cert.json"
            f_def.write_bytes(raw_default)
            expected_sha = hashlib.sha256(raw_default).hexdigest()
            self.assertEqual(verify_guards.verify_canonical_json_file(f_def, payload), expected_sha)

            f_sort = root / "sorted.json"
            f_sort.write_bytes(raw_sorted)
            self.assertEqual(
                verify_guards.verify_canonical_json_file(f_sort, payload, indent=1, sort_keys=True, ensure_ascii=True),
                hashlib.sha256(raw_sorted).hexdigest(),
            )

            arr_file = root / "arr.json"
            arr_file.write_bytes(verify_guards.canonical_json_bytes([1, 2]))
            with self.assertRaises(ValueError):
                verify_guards.verify_canonical_json_file(arr_file, [1, 2])

            for tampered in (
                raw_default + b" ",
                raw_default.replace(b"\n", b"\r\n"),
                raw_default.replace(b'"flag": true', b'"flag": 1'),
                raw_default.replace(b'"a": 0.0', b'"a": -0.0'),
                raw_default.replace(b'"b": 1', b'"b": 1.0'),
                (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
            ):
                bad_file = root / "tampered.json"
                bad_file.write_bytes(tampered)
                with self.assertRaises(ValueError):
                    verify_guards.verify_canonical_json_file(bad_file, payload)

            with self.assertRaises(ValueError):
                verify_guards.verify_canonical_json_file(f_def, payload, max_bytes=4)
            with self.assertRaises(ValueError):
                verify_guards.verify_canonical_json_file(f_def, payload, max_depth=0)


class TestOptifabVerifyIntegration(unittest.TestCase):
    def test_committed_artifacts_and_non_sympy_reproduction(self) -> None:
        verify = _import_verify_module()
        cert_path = REPO_ROOT / "results" / "certificate.json"
        ledger_path = REPO_ROOT / "results" / "ledger.json"

        cert = verify_guards.strict_read_json(cert_path)
        ledger = verify_guards.strict_read_json(ledger_path)

        cert_sha = verify_guards.verify_canonical_json_file(cert_path, cert, indent=2, ensure_ascii=False)
        ledger_sha = verify_guards.verify_canonical_json_file(ledger_path, ledger, indent=1, ensure_ascii=False)
        self.assertEqual(len(cert_sha), 64)
        self.assertEqual(len(ledger_sha), 64)

        inp = verify.load_inputs()
        margins = verify.margin_vector(inp)
        self.assertEqual(margins, cert["margins"]["vector"])

        pr = verify.plant_radius(margins)
        self.assertEqual(pr["plant_radius"], cert["margins"]["plant_radius"])
        self.assertEqual(pr["binding_limit_state"], cert["margins"]["binding_limit_state"])
        self.assertEqual(pr["second_tightest"], cert["margins"]["second_tightest"])

        ball = verify.ball_in_box_check([m["utilisation"] for m in margins], pr["plant_radius"], samples=20000)
        self.assertEqual(ball, cert["margins"]["ball_in_box"])

    def test_nan_swallowing_regressions_fail_closed(self) -> None:
        verify = _import_verify_module()
        # Previously returned all_within_limits=True when a coordinate was NaN!
        with self.assertRaises(ValueError):
            verify.ball_in_box_check([0.1791, float("nan"), 0.25], 0.1989, samples=50)
        with self.assertRaises(ValueError):
            verify.ball_in_box_check([0.1791, 0.25], float("nan"), samples=50)
        with self.assertRaises(ValueError):
            verify.ball_in_box_check([0.1791, float("inf")], 0.1989, samples=50)
        with self.assertRaisesRegex(ValueError, "must be non-empty"):
            verify.ball_in_box_check([], 0.1989, samples=10)

        # plant_radius must reject NaN / Inf / bool utilisations and < 2 margins (accepting exact len==2)
        valid_two = [
            {"limit_state": "a", "source": "s", "utilisation": 0.5},
            {"limit_state": "b", "source": "s", "utilisation": 0.8},
        ]
        pr2 = verify.plant_radius(valid_two)
        self.assertEqual(pr2["binding_limit_state"], "b")
        self.assertEqual(pr2["second_tightest"], "a")

        base_margins = [
            {"limit_state": "a", "source": "s", "utilisation": 0.5},
            {"limit_state": "b", "source": "s", "utilisation": float("nan")},
        ]
        with self.assertRaises(ValueError):
            verify.plant_radius(base_margins)
        with self.assertRaises(ValueError):
            verify.plant_radius([base_margins[0]])
        with self.assertRaises(ValueError):
            verify.plant_radius([base_margins[0], {"limit_state": "c", "source": "s", "utilisation": True}])

    def test_main_canonical_and_zone_b_guards(self) -> None:
        verify = _import_verify_module()
        cert = verify_guards.strict_read_json(REPO_ROOT / "results" / "certificate.json")
        ledger = verify_guards.strict_read_json(REPO_ROOT / "results" / "ledger.json")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c_path = root / "certificate.json"
            l_path = root / "ledger.json"
            c_bytes = verify_guards.canonical_json_bytes(cert, indent=2, ensure_ascii=False)
            l_bytes = verify_guards.canonical_json_bytes(ledger, indent=1, ensure_ascii=False)
            c_path.write_bytes(c_bytes)
            l_path.write_bytes(l_bytes)

            with mock.patch.object(verify, "CERT_PATH", c_path), mock.patch.object(
                verify, "LEDGER_PATH", l_path
            ), mock.patch.object(verify, "build_certificate", return_value=(cert, ledger)):
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 0)

                # Formatting tampering that Python dict == dict accepts must be rejected by canonical check
                c_path.write_bytes(c_bytes + b" ")
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 1)

                # Symlink, directory, and malformed JSON on CERT_PATH must fail closed with rc=1 (no traceback)
                real_cert = root / "real_cert.json"
                real_cert.write_bytes(c_bytes)
                c_path.unlink()
                c_path.symlink_to(real_cert)
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 1)
                c_path.unlink()
                c_path.mkdir()
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 1)
                c_path.rmdir()
                c_path.write_bytes(b"{corrupt")
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 1)
                c_path.write_bytes(c_bytes)

                l_path.write_bytes(l_bytes + b" ")
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 1)

                # Symlink on ledger.json must fail closed with rc=1
                real_ledger = root / "real_ledger.json"
                real_ledger.write_bytes(l_bytes)
                l_path.unlink()
                l_path.symlink_to(real_ledger)
                with mock.patch.object(sys, "argv", ["verify.py"]):
                    self.assertEqual(verify.main(), 1)


if __name__ == "__main__":
    unittest.main()
