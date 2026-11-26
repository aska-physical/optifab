#!/usr/bin/env python3
"""R5 Fail-Closed Adversarial & Boundary Test Suite for Biomimetic x Historical Mechanics.

Zero external dependencies (stdlib unittest only), zero bare asserts, safe across
`python3 -I -B`, `-I -O -B`, and `-I -B -W error`. Cross-checks Sylvester inertia
outputs (both SPD and PSD kernel cases) directly against `optifab/q/inertia.py`.
"""

from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Dict
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import biomimetic_historical_mechanics_audit as mod
from optifab.q.inertia import Inertia


def _rehash(cert: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(cert)
    p_sha = hashlib.sha256(mod.canonical_json_bytes(out["payload"])).hexdigest()
    out["payload_sha256"] = p_sha
    body = {k: out[k] for k in out if k != "certificate_sha256"}
    out["certificate_sha256"] = hashlib.sha256(mod.canonical_json_bytes(body)).hexdigest()
    return out


class TestBiomimeticHistoricalMechanicsR5(unittest.TestCase):
    def _assert_err(self, code: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        with self.assertRaises(mod.MechanicsAuditError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    # 1. Committed on-disk certificate, optifab/q/inertia parity (SPD & PSD kernels), & tamper/CLI controls
    def test_01_committed_certificate_and_tamper_controls(self) -> None:
        cert_path = HERE.joinpath("biomimetic_historical_mechanics_certificate.json")
        res_disk = mod.check_certificate_file(cert_path)
        self.assertEqual(res_disk["status"], "PASS")
        self.assertTrue(res_disk["all_gates_passed"])
        self.assertTrue(mod.is_hex64(res_disk["verifier_source_sha256"]))
        self.assertEqual(
            mod.check_certificate_file(
                cert_path,
                expected_source_sha256=res_disk["verifier_source_sha256"],
            )["status"],
            "PASS",
        )
        self._assert_err("BAD_SOURCE_SHA", mod.check_certificate_file, cert_path, expected_source_sha256="bad")
        self._assert_err("SOURCE_SHA_MISMATCH", mod.check_certificate_file, cert_path, expected_source_sha256="0" * 64)

        cert = mod.build_certificate()
        self.assertEqual(res_disk["certificate_sha256"], cert["certificate_sha256"])
        gates = cert["payload"]["gates"]
        for gid in ("U1", "U2", "U3", "U4", "U5", "U6"):
            self.assertTrue(gates[gid]["passed"], f"Gate {gid} failed")

        # Cross-check named inertia dicts directly against optifab/q/inertia.py Inertia (SPD, PSD kernels, & indefinite)
        in_vent = Inertia(**gates["U1"]["vented_haynsworth_inertia"])
        in_gier = Inertia(**gates["U1"]["gier_haynsworth_inertia"])
        in_volk = Inertia(**gates["U3"]["volkersen_m6_inertia"])
        in_orb8 = Inertia(**gates["U4"]["orb_8d_tension_only_inertia"])
        in_comp8 = Inertia(**gates["U4"]["orb_8d_compression_neg_ctrl_inertia"])
        in_casarabe = Inertia(**gates["U4"]["casarabe_laplacian_inertia"])
        in_h8 = Inertia(**gates["U4"]["h8_auxetic_fold_sheaf_inertia"])
        in_hyp = Inertia(**gates["U4"]["zero_diag_hyperbolic_2x2_inertia"])
        self.assertTrue(in_vent.is_pos_def)
        self.assertTrue(in_volk.is_pos_def)
        self.assertTrue(in_orb8.is_pos_def)
        self.assertEqual((in_orb8.pos, in_orb8.neg, in_orb8.zero, in_orb8.dim), (8, 0, 0, 8))
        self.assertEqual((in_comp8.pos, in_comp8.neg, in_comp8.zero, in_comp8.dim), (0, 8, 0, 8))
        self.assertFalse(in_gier.is_pos_def)
        self.assertEqual((in_gier.pos, in_gier.neg, in_gier.zero, in_gier.dim), (10, 0, 1, 11))
        self.assertEqual(in_gier.to_dict(), gates["U1"]["gier_haynsworth_inertia"])
        self.assertFalse(in_casarabe.is_pos_def)
        self.assertEqual((in_casarabe.pos, in_casarabe.neg, in_casarabe.zero, in_casarabe.dim), (12, 0, 1, 13))
        self.assertEqual(in_casarabe.to_dict(), gates["U4"]["casarabe_laplacian_inertia"])
        self.assertFalse(in_h8.is_pos_def)
        self.assertEqual((in_h8.pos, in_h8.neg, in_h8.zero, in_h8.dim), (4, 4, 0, 8))
        self.assertFalse(in_hyp.is_pos_def)
        self.assertEqual((in_hyp.pos, in_hyp.neg, in_hyp.zero, in_hyp.dim), (1, 1, 0, 2))
        self.assertEqual(gates["U4"]["equal_order_dim"], 8)

        # Key mathematical witnesses
        self.assertEqual(gates["U1"]["petra_k36_moment_collapse"], "46656/1")
        self.assertEqual(gates["U1"]["petra_beaver_vented_surge_q"], "64/1365")
        self.assertEqual(gates["U1"]["belanger_k4_over_k2_nonlinear_ratio_q"], "27/2")
        self.assertTrue(gates["U2"]["g_orb_6_2_exact_isomorphic_to_casarabe_c2_6"])
        self.assertEqual(gates["U2"]["ventilation_tree_power_q"], "0/1")
        self.assertEqual(gates["U2"]["ventilation_ring_power_q"], "1/13")
        self.assertEqual(gates["U2"]["c4_upwind_skew_frob_sq_q"], "2/1")
        self.assertTrue(gates["U2"]["convective_operator_rejected_by_symmetric_inertia"])
        self.assertEqual(gates["U3"]["tailorbird_m_star"], 4)
        self.assertEqual(gates["U3"]["tailorbird_graded_gain_ratio_q"], "55/49")
        self.assertEqual(gates["U3"]["elastic_closed_cycle_e_diss_q"], "0/1")
        self.assertEqual(gates["U3"]["machu_picchu_stout_over_slender_q"], "9248/2197")
        self.assertTrue(gates["U4"]["non_congruence_proven"])
        self.assertEqual(gates["U5"]["pin_checker1_floppy"], 1)
        self.assertEqual(gates["U5"]["pin_checker1_bridge_diags"], 9)
        self.assertEqual(gates["U5"]["pin_checker1_bridge_floppy"], 0)
        self.assertEqual(gates["U5"]["continuous_spicule_checker1_floppy"], 0)

        # Certificate top-level validation rejections
        self._assert_err("BAD_ROOT", mod.verify_certificate_dict, [])
        bad = copy.deepcopy(cert)
        bad["extra"] = 1
        self._assert_err("BAD_KEYS", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["schema"] = "wrong"
        self._assert_err("BAD_SCHEMA", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["claim_scope"] = "bench_claim"
        self._assert_err("BAD_CLAIM_SCOPE", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["energy_power_status"] = "CLAIMED"
        self._assert_err("BAD_ENERGY_STATUS", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["payload_sha256"] = "\u00e9" * 64
        self._assert_err("BAD_PAYLOAD_SHA", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["certificate_sha256"] = "\u00e9" * 64
        self._assert_err("BAD_CERT_SHA", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["payload_sha256"] = "0" * 64
        self._assert_err("PAYLOAD_SHA_MISMATCH", mod.verify_certificate_dict, bad)
        bad = copy.deepcopy(cert)
        bad["certificate_sha256"] = "0" * 64
        self._assert_err("CERT_SHA_MISMATCH", mod.verify_certificate_dict, bad)

        # Re-hashed tampered payload MUST fail live recomputation check
        tampered = copy.deepcopy(cert)
        tampered["payload"]["gates"]["U3"]["tailorbird_m_star"] = 5
        tampered = _rehash(tampered)
        self._assert_err("RECOMPUTATION_MISMATCH", mod.verify_certificate_dict, tampered)

        # Dynamic live all_gates_passed enforcement (fails closed even if live_cert hash matches)
        failed_live = copy.deepcopy(cert)
        failed_live["payload"]["all_gates_passed"] = False
        failed_live = _rehash(failed_live)
        with patch.object(mod, "build_certificate", return_value=failed_live):
            self._assert_err("LIVE_GATES_FAILED", mod.verify_certificate_dict, failed_live)

        # File write/check, BOM/CRLF/newline/whitespace raw-bytes mismatch, nested & escaped dup-keys, & CLI paths
        self._assert_err("BAD_PATH", mod.check_certificate_file, "x.json")  # type: ignore[arg-type]
        self._assert_err("BAD_PATH", mod.write_certificate_file, "x.json")  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            p = tdir.joinpath("cert.json")
            mod.write_certificate_file(p)
            valid_bytes = p.read_bytes()
            self.assertEqual(mod.check_certificate_file(p)["status"], "PASS")

            # Compact rewrite, CRLF, missing/extra trailing newline, UTF-8 BOM (reusing verified `cert`)
            with patch.object(mod, "build_certificate", return_value=cert):
                p_compact = tdir.joinpath("compact.json")
                p_compact.write_text(json.dumps(cert, separators=(",", ":")), encoding="utf-8")
                self._assert_err("RAW_BYTES_MISMATCH", mod.check_certificate_file, p_compact)

                p_crlf = tdir.joinpath("crlf.json")
                p_crlf.write_bytes(valid_bytes.replace(b"\n", b"\r\n"))
                self._assert_err("RAW_BYTES_MISMATCH", mod.check_certificate_file, p_crlf)

                p_nonl = tdir.joinpath("nonl.json")
                p_nonl.write_bytes(valid_bytes.rstrip(b"\n"))
                self._assert_err("RAW_BYTES_MISMATCH", mod.check_certificate_file, p_nonl)

                p_extranl = tdir.joinpath("extranl.json")
                p_extranl.write_bytes(valid_bytes + b"\n")
                self._assert_err("RAW_BYTES_MISMATCH", mod.check_certificate_file, p_extranl)

                p_bom = tdir.joinpath("bom.json")
                p_bom.write_bytes(b"\xef\xbb\xbf" + valid_bytes)
                self._assert_err("JSON_PARSE_ERR", mod.check_certificate_file, p_bom)

                # Nested & \u0061-escaped duplicate keys on disk
                p_nested_dup = tdir.joinpath("nested_dup.json")
                p_nested_dup.write_text('{"outer": {"k": 1, "k": 2}}', encoding="utf-8")
                self._assert_err("JSON_DUP_KEY", mod.check_certificate_file, p_nested_dup)

                p_esc_dup = tdir.joinpath("esc_dup.json")
                p_esc_dup.write_text('{"a": 1, "\\u0061": 2}', encoding="utf-8")
                self._assert_err("JSON_DUP_KEY", mod.check_certificate_file, p_esc_dup)

                # Bad UTF-8, symlink, missing file, unwritable path, symlink write refusal
                p_bin = tdir.joinpath("bad.bin")
                p_bin.write_bytes(b"\xff\xfe\xfd")
                self._assert_err("READ_ERR", mod.check_certificate_file, p_bin)
                p_sym = tdir.joinpath("sym_cert.json")
                p_sym.symlink_to(p)
                self._assert_err("READ_ERR", mod.check_certificate_file, p_sym)
                self._assert_err("WRITE_ERR", mod.write_certificate_file, p_sym)
                self._assert_err("READ_ERR", mod.check_certificate_file, tdir.joinpath("missing.json"))
                self._assert_err("WRITE_ERR", mod.write_certificate_file, tdir.joinpath("no_such_dir").joinpath("c.json"))
                fifo_out = tdir.joinpath("out.fifo")
                os.mkfifo(fifo_out)
                self._assert_err("WRITE_ERR", mod.write_certificate_file, fifo_out)
                gp_real = tdir.joinpath("gp_real")
                gp_real.joinpath("sub").mkdir(parents=True)
                gp_cert = gp_real.joinpath("sub", "cert.json")
                gp_cert.write_bytes(valid_bytes)
                gp_link = tdir.joinpath("gp_link")
                gp_link.symlink_to(gp_real)
                self._assert_err("READ_ERR", mod.check_certificate_file, gp_link.joinpath("sub", "cert.json"))
                self._assert_err("WRITE_ERR", mod.write_certificate_file, gp_link.joinpath("sub", "out.json"))
                with patch.object(mod, "verify_self_source_pin", return_value=res_disk["verifier_source_sha256"]), patch.object(
                    mod.os, "fstat", return_value=os.stat_result((0o010600, 0, 0, 1, 0, 0, 0, 0, 0, 0))
                ):
                    self._assert_err("WRITE_ERR", mod.write_certificate_file, tdir.joinpath("nonreg_fstat.json"))
                with patch.object(mod.os, "write", side_effect=OSError("disk full")):
                    self._assert_err("WRITE_ERR", mod.write_certificate_file, tdir.joinpath("write_fail.json"))

                real_os_write = os.write
                partial_chunks = []

                def _write_10_bytes(fd: int, data: bytes) -> int:
                    chunk = bytes(data)[:10]
                    partial_chunks.append(len(chunk))
                    return real_os_write(fd, chunk)

                p_short_ok = tdir.joinpath("short_ok.json")
                with patch.object(mod.os, "write", side_effect=_write_10_bytes):
                    mod.write_certificate_file(p_short_ok)
                self.assertEqual(len(valid_bytes), 7695)
                self.assertEqual(p_short_ok.read_bytes(), valid_bytes)
                self.assertEqual(sum(partial_chunks), 7695)
                self.assertEqual(len(partial_chunks), 770)
                self.assertEqual(mod.check_certificate_file(p_short_ok)["status"], "PASS")

                zero_write_calls = 0

                def _write_zero_once(fd: int, data: bytes) -> int:
                    nonlocal zero_write_calls
                    zero_write_calls += 1
                    if zero_write_calls > 1:
                        raise AssertionError("os.write called again after 0-byte return")
                    return 0

                with patch.object(mod.os, "write", side_effect=_write_zero_once):
                    self._assert_err("IO_SHORT_WRITE", mod.write_certificate_file, tdir.joinpath("zero_write.json"))
                self.assertEqual(zero_write_calls, 1)

                p_tz_calls = 0

                def _write_10_then_0(fd: int, data: bytes) -> int:
                    nonlocal p_tz_calls
                    p_tz_calls += 1
                    if p_tz_calls == 1:
                        return real_os_write(fd, bytes(data)[:10])
                    if p_tz_calls == 2:
                        return 0
                    raise AssertionError("os.write called again after 0-byte return")

                with patch.object(mod.os, "write", side_effect=_write_10_then_0):
                    self._assert_err("IO_SHORT_WRITE", mod.write_certificate_file, tdir.joinpath("partial_zero.json"))
                self.assertEqual(p_tz_calls, 2)

                with patch.object(mod.os, "write", return_value=-1):
                    self._assert_err("IO_SHORT_WRITE", mod.write_certificate_file, tdir.joinpath("neg_write.json"))

                class _BrokenStream:
                    def write(self, _s: str) -> int:
                        raise BrokenPipeError(32, "Broken pipe")

                    def flush(self) -> None:
                        raise BrokenPipeError(32, "Broken pipe")

                class _BrokenFlushOnly:
                    def __init__(self) -> None:
                        self.chunks = []

                    def write(self, s: str) -> int:
                        self.chunks.append(s)
                        return len(s)

                    def flush(self) -> None:
                        raise BrokenPipeError(32, "Broken pipe")

                broken_err = io.StringIO()
                with patch.object(sys, "stdout", _BrokenStream()), patch.object(sys, "stderr", broken_err):
                    rc_bp = mod.main(["--standalone"])
                self.assertEqual(rc_bp, 2)
                self.assertIn("STDOUT_WRITE_ERR", broken_err.getvalue())

                flush_err = io.StringIO()
                with patch.object(sys, "stdout", _BrokenFlushOnly()), patch.object(sys, "stderr", flush_err):
                    rc_bf = mod.main(["--standalone"])
                self.assertEqual(rc_bf, 2)
                self.assertIn("STDOUT_WRITE_ERR", flush_err.getvalue())

                with patch.object(sys, "stdout", _BrokenStream()), patch.object(sys, "stderr", _BrokenStream()):
                    rc_both = mod.main(["--standalone"])
                self.assertEqual(rc_both, 2)

                with patch.object(sys, "stderr", _BrokenStream()):
                    rc_err_bp = mod.main(["--check", str(tdir.joinpath("missing.json"))])
                self.assertEqual(rc_err_bp, 2)

                for argv in (
                    [],
                    ["--standalone"],
                    ["--standalone", "--expected-source-sha256", res_disk["verifier_source_sha256"]],
                    ["--write", str(p)],
                    ["--write", str(p), "--expected-source-sha256", res_disk["verifier_source_sha256"]],
                    ["--check", str(p)],
                    ["--check", str(p), "--expected-source-sha256", res_disk["verifier_source_sha256"]],
                ):
                    buf = io.StringIO()
                    with patch.object(sys, "stdout", buf):
                        rc = mod.main(argv)
                    self.assertEqual(rc, 0)
                    self.assertIsInstance(json.loads(buf.getvalue()), dict)

                unwritten = tdir.joinpath("must_not_exist.json")
                for bad_argv in (
                    ["--expected-source-sha256", "0" * 64],
                    ["--standalone", "--expected-source-sha256", "0" * 64],
                    ["--standalone", "--expected-source-sha256", "bad"],
                    ["--write", str(unwritten), "--expected-source-sha256", "0" * 64],
                    ["--write", str(unwritten), "--expected-source-sha256", "bad"],
                ):
                    err_pin = io.StringIO()
                    with patch.object(sys, "stderr", err_pin):
                        rc_pin = mod.main(bad_argv)
                    self.assertEqual(rc_pin, 2)
                self.assertFalse(unwritten.exists())

            err_buf = io.StringIO()
            with patch.object(sys, "stderr", err_buf):
                rc = mod.main(["--check", str(tdir.joinpath("missing.json"))])
            self.assertEqual(rc, 2)
            self.assertIn("READ_ERR", err_buf.getvalue())

            # Real isolated subprocess CLI checks (--check & --standalone & --write with pin + mismatch)
            extra_flags = ["-W", "error"] if "error" in sys.warnoptions else []
            script = str(HERE.joinpath("biomimetic_historical_mechanics_audit.py"))
            proc_ok = subprocess.run(
                [sys.executable, "-I", "-B", *extra_flags, script, "--check", str(p), "--expected-source-sha256", res_disk["verifier_source_sha256"]],
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(proc_ok.returncode, 0)
            self.assertEqual(json.loads(proc_ok.stdout)["status"], "PASS")

            for sub_args in (
                ["--check", str(p), "--expected-source-sha256", "0" * 64],
                ["--standalone", "--expected-source-sha256", "0" * 64],
                ["--write", str(tdir.joinpath("sub_unwritten.json")), "--expected-source-sha256", "0" * 64],
            ):
                proc_bad = subprocess.run(
                    [sys.executable, "-I", "-B", *extra_flags, script, *sub_args],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                self.assertEqual(proc_bad.returncode, 2)
                self.assertIn("SOURCE_SHA_MISMATCH", proc_bad.stderr)

            # Closed stdout/stderr pipe BrokenPipeError controls (RC=2, zero tracebacks, never RC=120)
            p_pipe_write = tdir.joinpath("pipe_write_cert.json")
            for pipe_args in (
                ["--standalone"],
                ["--check", str(p)],
                ["--write", str(p_pipe_write)],
            ):
                r_fd, w_fd = os.pipe()
                os.close(r_fd)
                try:
                    proc_pipe = subprocess.run(
                        [sys.executable, "-I", "-B", *extra_flags, script, *pipe_args],
                        stdout=w_fd,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=20,
                    )
                finally:
                    os.close(w_fd)
                self.assertEqual(proc_pipe.returncode, 2, f"Closed stdout pipe failed for {pipe_args}: rc={proc_pipe.returncode}")
                self.assertNotIn("Traceback", proc_pipe.stderr)
                self.assertNotIn("Exception ignored", proc_pipe.stderr)
                self.assertIn("STDOUT_WRITE_ERR", proc_pipe.stderr)

            r_out, w_out = os.pipe()
            os.close(r_out)
            r_err, w_err = os.pipe()
            os.close(r_err)
            try:
                proc_both_closed = subprocess.run(
                    [sys.executable, "-I", "-B", *extra_flags, script, "--standalone"],
                    stdout=w_out,
                    stderr=w_err,
                    timeout=20,
                )
            finally:
                os.close(w_out)
                os.close(w_err)
            self.assertEqual(proc_both_closed.returncode, 2)

    # 2. Hardened counter-derived AST guard (floats, ast.Div, ast.Pow, bare assert, dunder/dynamic escapes, _read_source_file)
    def test_02_hardened_ast_zero_float_guard(self) -> None:
        self_src, self_sha = mod._read_source_file(Path(mod.__file__))
        self.assertTrue(mod.is_hex64(self_sha))
        res = mod.audit_source_zero_float_ast(self_src)
        self.assertTrue(all(res.values()))
        self.assertEqual(len(res), 9)
        ok_snippet = (
            "from typing import Any\n"
            "import json\n"
            "import os\n"
            "x = Fraction(1, 2)\n"
            "y = Fraction(5, 2)\n"
            "w = x + y\n"
            "z0 = x ** 0\n"
            f"z64 = x ** {mod.MAX_SAFE_POW_EXP}\n"
            "zp = (x + y) ** 2\n"
            f"big_ok = {'9' * mod.MAX_INT_DIGITS}\n"
            "fd = os.open('f', 0)\n"
            "doc = json.loads('{}', parse_int=pi, parse_float=pf, parse_constant=pc)\n"
        )
        self.assertTrue(all(mod.audit_source_zero_float_ast(ok_snippet).values()))

        self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, "x.py")  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, tdir)
            fifo_f = tdir.joinpath("pipe.py")
            os.mkfifo(fifo_f)
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, fifo_f)
            real_f = tdir.joinpath("ok.py")
            real_f.write_bytes(b"x = 1\n")
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, str(real_f))  # type: ignore[arg-type]
            with patch.object(mod.os, "read", side_effect=OSError("io fail")):
                self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, real_f)
            txt, sha = mod._read_source_file(real_f)
            self.assertEqual(txt, "x = 1\n")
            self.assertEqual(sha, hashlib.sha256(b"x = 1\n").hexdigest())
            exact_cap_f = tdir.joinpath("exact_cap.py")
            exact_cap_bytes = b"#" * (mod.MAX_JSON_BYTES - 6) + b"\nx = 1"
            self.assertEqual(len(exact_cap_bytes), mod.MAX_JSON_BYTES)
            exact_cap_f.write_bytes(exact_cap_bytes)
            _, cap_sha = mod._read_source_file(exact_cap_f)
            self.assertTrue(mod.is_hex64(cap_sha))
            over_cap_f = tdir.joinpath("over_cap.py")
            over_cap_f.write_bytes(exact_cap_bytes + b"\n")
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, over_cap_f)
            link_f = tdir.joinpath("link.py")
            link_f.symlink_to(real_f)
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, link_f)
            gp_src_real = tdir.joinpath("gp_src_real")
            gp_src_real.joinpath("sub").mkdir(parents=True)
            gp_src_real.joinpath("sub", "ok.py").write_bytes(b"x = 1\n")
            gp_src_link = tdir.joinpath("gp_src_link")
            gp_src_link.symlink_to(gp_src_real)
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, gp_src_link.joinpath("sub", "ok.py"))
            crlf_f = tdir.joinpath("crlf.py")
            crlf_f.write_bytes(b"x = 1\r\n")
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, crlf_f)
            bad_utf = tdir.joinpath("badutf.py")
            bad_utf.write_bytes(b"\xff\xfe")
            self._assert_err("BAD_SELF_SOURCE", mod._read_source_file, bad_utf)

        self._assert_err("BAD_SOURCE", mod.audit_source_zero_float_ast, 123)  # type: ignore[arg-type]
        self._assert_err("BAD_BOOL", mod.audit_source_zero_float_ast, "x = 1\n", raise_on_violation=1)  # type: ignore[arg-type]
        self._assert_err("AST_SYNTAX_ERR", mod.audit_source_zero_float_ast, "def (:")
        self._assert_err("AST_EMPTY", mod.audit_source_zero_float_ast, "")
        self._assert_err("AST_EMPTY", mod.audit_source_zero_float_ast, "# comment only\n")
        self._assert_err("AST_FLOAT_LITERAL", mod.audit_source_zero_float_ast, "x = 1.5\n")
        self._assert_err("AST_FLOAT_LITERAL", mod.audit_source_zero_float_ast, "x = 1j\n")
        self._assert_err("AST_ASSERT_FORBIDDEN", mod.audit_source_zero_float_ast, "assert True\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x = a / b\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x /= 2\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x = 1 // 2\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x //= 2\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x = '%f' % 1\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x = a % b\n")
        self._assert_err("AST_DIV_FORBIDDEN", mod.audit_source_zero_float_ast, "x %= 2\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x = 2 ** -1\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, f"x = 2 ** {mod.MAX_SAFE_POW_EXP + 1}\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x = 10 ** 999999999\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x = (2 ** 2) ** 2\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, f"x = {'9' * (mod.MAX_INT_DIGITS + 1)}\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x = 2 ** n\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x = 2 ** 'a'\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x = 2 ** True\n")
        self._assert_err("AST_UNSAFE_POW", mod.audit_source_zero_float_ast, "x **= 2\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import math\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import math as m\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "from math import sqrt\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import operator\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import builtins\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import io\n")
        self._assert_err("AST_FRACTION_ALIAS", mod.audit_source_zero_float_ast, "from fractions import Fraction as F\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from . import foo\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import sys\nx = sys.modules['math'].pi\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import sys as s\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import os as o\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from sys import modules\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from sys import argv\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from os import path\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from os import open\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import sys\ns = sys\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import os\no = os\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import fractions\nm = fractions\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "p = pow\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "m = memoryview\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import struct\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import time\nx = time.time()\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "import random\nx = random.random()\n")
        self._assert_err("AST_FLOAT_IMPORT", mod.audit_source_zero_float_ast, "from random import random\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'f = float\nx = f("1.5")\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "c = complex\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = float.real\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = (1).real\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = ().__class__.__base__.__subclasses__()\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'x = float.fromhex("0x1.0p0")\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'x = f"{1:.3f}"\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = format(1, '.3f')\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = '{:.3f}'.format(1)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "f = format\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "f = '{:.3f}'.format\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = divmod(5, 2)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "d = divmod\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = (5).__floordiv__(2)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = type(Fraction(1, 2))(1, 2)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "t = type(1)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = (type() is int)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = (type('X', (), {}) is int)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = (type(*a) is int)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = (type(1, k=2) is int)\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = obj.Fraction(1, 2)\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import json\nj = json\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import json as j\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from json import loads\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5")\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5", parse_int=pi, parse_float=pf)\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5", parse_int=pi, parse_constant=pc)\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5", parse_float=pf, parse_constant=pc)\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5", parse_int=None, parse_float=pf, parse_constant=pc)\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5", parse_int=pi, parse_float=None, parse_constant=pc)\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1.5", parse_int=pi, parse_float=pf, parse_constant=None)\n')
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, 'import json\nx = json.loads("1", **kw)\n')
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import os\nos.execv('/bin/true', ['true'])\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import os\nx = os.environ\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from typing import modules\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "from ast import literal_eval\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "f = (1).__truediv__\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = __builtins__\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = compile('1.5', '', 'eval')\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = (1).__truediv__(2)\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "import ast\nx = ast.literal_eval('1.5')\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = getattr(__builtins__, 'float')(1)\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = float(1)\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = Fraction.from_float(1)\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = Fraction.from_decimal(1)\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = obj.round(1)\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = open('f')\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = p.open('f')\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "x = a.b.open('f')\n")
        self._assert_err("AST_FLOAT_CALL", mod.audit_source_zero_float_ast, "import os\nos.system('true')\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, 'x = Fraction("1/2")\n')
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = Fraction(val)\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = Fraction(numerator=1, denominator=2)\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, 'x = Fraction("1", 2)\n')
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = Fraction(1, True)\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = Fraction(*pair, 2)\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, 'F = Fraction\nx = F("0.5")\n')
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "import fractions\nF = fractions.Fraction\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x: (F := Fraction) = 1\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "import fractions as fr\n")
        self._assert_err("AST_DYNAMIC_ESCAPE", mod.audit_source_zero_float_ast, "x = object.__getattribute__(1, '__float__')\n")
        self.assertTrue(
            all(
                mod.audit_source_zero_float_ast(
                    "import fractions\ndef f(x: Fraction) -> Fraction:\n    y: Fraction = fractions.Fraction(1, 2)\n    return y if type(x) is Fraction and type(y) is not Fraction else y\n"
                ).values()
            )
        )
        self.assertTrue(
            all(
                mod.audit_source_zero_float_ast(
                    "async def af(x: Fraction) -> Fraction:\n    return Fraction(1, 2)\n"
                ).values()
            )
        )
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = (1 == Fraction)\n")
        self._assert_err("AST_UNSAFE_FRACTION", mod.audit_source_zero_float_ast, "x = (1 is Fraction is 2)\n")

        # Counter-derived boolean flags MUST flip to False (never hardcoded True)
        flag_cases = (
            ("", "has_nonempty_ast"),
            ("x = 1.5\n", "zero_float_literals"),
            ("x = 1 / 2\n", "zero_ast_div"),
            ("x = 2 ** -1\n", "zero_unsafe_pow"),
            ("x = 10 ** 999999999\n", "zero_unsafe_pow"),
            ('x = Fraction("1/2")\n', "zero_unsafe_fraction_calls"),
            ("import math\n", "zero_float_imports"),
            ("x = float(1)\n", "zero_float_calls"),
            ("assert True\n", "zero_bare_asserts"),
            ("x = (1).__truediv__(2)\n", "zero_dynamic_escapes"),
            ("import sys\nx = sys.modules['math'].pi\n", "zero_dynamic_escapes"),
        )
        for snippet, flag_key in flag_cases:
            report = mod.audit_source_zero_float_ast(snippet, raise_on_violation=False)
            self.assertFalse(report[flag_key], f"Flag {flag_key} stayed True on {snippet!r}")

    # 3. Reference Energy-Claim Guard (89/89 bad incl. spelled-out, power 45, A-at-V, rapl_uj, W/ token; 56/56 good incl. j = 3, 3 w/o pinning, w/ tokens) + strict JSON
    def test_03_energy_guard_and_strict_json(self) -> None:
        bad = [
            "45.2 W", "45W", "45.2 W.", "45.2W!", "W?", "[W]", "45.2\u00d7W", "45.2-W",
            "45.2 [W]", "W: 45.2", "W=45.2", "45.2 kilowatts", "45.2\u200bW", "45.2 k\u200bW",
            "5 GW", "5 TW", "5 pW", "5 kilo watts", "5 kilo-watts", "5 m W", "15 watthours",
            "15 watt hours", "15 watt-hour", "5\u2013W", "12\u00b7W", "3.9e2 W", "1.5E-3W",
            "0.5 kWh", "1.2 J/tok", "joules per token", "MJ per token", "mJ/tok", "15 TDP",
            "TDP 15", "TDP", "70% less energy", "70 percent less power", "energy use dropped",
            "power savings", "5 \u051d", "\u0435nergy", "3 \u043a\u0412\u0442", "\uff11\uff12\uff37",
            "45 milliwatts", "1.2 megawatts", "12.5 kilojoules", "W: 45.2 drain",
            "45.2[W] drain", "J: 5", "cap_45_w", "45_watts", "limit_45_w", "draw_45w",
            "45 Whr", "130w_psu", "max_45w", "45w", "5 PW", "45.2 \u03c9", "\u051datt",
            "45.2\u2219W", "0x2D W", "5 hp", "1.5hp", "10 tok/J", "measured with RAPL",
            "nvml telemetry", "nvidia-smi draw", "energy per token", "power per token",
            "energy/tok", "250 W/ token", "250 W / token", "5 J/ token",
            "forty-five watts", "fortyfive watts", "twenty joules", "five kilowatts",
            "energy: 12", "energy 12", "power = 12", "power 45", "wattage: 45",
            "rapl_uj", "nvml_power", "rapluj", "nvmlDeviceGetTotalEnergyConsumption",
            "2.25 A at 20 V", "20 V @ 2.25 A",
        ]
        good = [
            "5 ms", "latency 12", "70 C", "78\u00b0C", "70/78/85 C knees", "5 C deadband",
            "5 deg C deadband", "135/2", "45.0%", "0.5 mm", "ac", "battery", "unknown",
            "temp_c", "gpu_temp_exceeded", "not_on_ac_power", "UNCONTROLLED_LAPTOP_NOT_CLAIMED",
            "grad_W_q", "stdlib_sha256_chain", "cpu_jiffies_total", "a" * 64,
            "129,279.00 tok/s", "469.41 us/tok", "8.113 MiB", "sm_86", "W10-REV-61", "wmma",
            "window 20", "warp 32", "16 warps/SM", "h256", "rows 1024", "tdp_like_free_text_no",
            "W13-REV-CHECK", "J2000 epoch-like", "J2000.0", "item W10", "2024-W05",
            "sprint-W12", "node-w10", "q4-w3", "W-2", "W12", "kW12", "bench w/ perf counters",
            "taskset -c 3 w/ 5 reps", "12 ms/tok", "sm_clock 2100 MHz", "0.9 V", "1024 MiB/s",
            "j = 3", "w = 4", "3 w/o pinning", "1 w/o cache", "w/ tokens", "eval w/ tokens",
        ]
        self.assertEqual(len(bad), 89)
        self.assertEqual(len(good), 56)
        for sample in bad:
            self.assertTrue(mod.is_forbidden_energy_value(sample), f"Missed: {sample!r}")
        for sample in good:
            self.assertFalse(mod.is_forbidden_energy_value(sample), f"FP: {sample!r}")

        # Adversarial O(N) non-backtracking ReDoS regression guard (< 0.10s CPU time on 10,000-char inputs vs > 2.0s quadratic)
        for hostile in (
            "1" + "." * 10000,
            "1" + "," * 10000,
            "1" + " " * 10000,
            "1" * 10000,
            "1." * 4000,
            "1," * 4000,
            "watt" + "-" * 10000 + "x",
            "-" * 10000 + "x",
        ):
            t0 = time.process_time()
            matched = mod.is_forbidden_energy_value(hostile)
            elapsed = time.process_time() - t0
            self.assertFalse(matched, f"Unexpected match on {hostile[:24]!r}")
            self.assertLess(elapsed, 0.10, f"Slow regex ({elapsed:.4f}s CPU) on hostile input")

        self.assertFalse(mod.has_non_ascii_letter("abc 5\u20136 \u03bc \u00b5"))
        self.assertTrue(mod.has_non_ascii_letter("\u03c9"))
        self._assert_err("BAD_TEXT", mod.normalize_text, 1)  # type: ignore[arg-type]
        self._assert_err("BAD_TEXT", mod.has_non_ascii_letter, None)  # type: ignore[arg-type]
        self._assert_err("BAD_KEY", mod.is_forbidden_energy_key, 1)  # type: ignore[arg-type]
        for bad_key in (
            "cap_45_w",
            "myWatts",
            "cpu_rapl_uj",
            "nvml_sensor",
            "power_w",
            "energy_j",
            "total_wh",
            "gpu_mj",
            "energy",
            "power",
            "cpu_uj",
            "milliwatts_avg",
            "kilojoules",
            "powerdraw",
            "wattage",
            "maxwatts",
        ):
            self.assertTrue(mod.is_forbidden_energy_key(bad_key), f"Missed key: {bad_key!r}")
            self._assert_err("FORBIDDEN_ENERGY_KEY", mod.validate_json_value, {bad_key: 45})
        for allowed_key in mod._ALLOWED_MODEL_ENERGY_KEYS:
            self.assertFalse(mod.is_forbidden_energy_key(allowed_key))
        for benign_key in ("normal_key", "tokens_per_window", "tokens_per_worker", "wrapLimit", "scrapLog"):
            self.assertFalse(mod.is_forbidden_energy_key(benign_key), f"FP key: {benign_key!r}")
        self._assert_err("FORBIDDEN_ENERGY_VALUE", mod.validate_json_value, {"val": "energy per token"})

        self.assertTrue(mod.is_hex64("0123456789abcdef" * 4))
        self.assertFalse(mod.is_hex64(123))
        self.assertFalse(mod.is_hex64("a" * 63))
        self.assertFalse(mod.is_hex64("a" * 65))
        self.assertFalse(mod.is_hex64("g" * 64))

        max_int = int("9" * mod.MAX_INT_DIGITS)
        mod.validate_json_value(1, max_depth=0)
        mod.validate_json_value([True, None, max_int, -max_int, "a" * mod.MAX_STRING_CHARS], max_depth=mod.MAX_JSON_DEPTH)
        self._assert_err("STRING_TOO_LARGE", mod.validate_json_value, "a" * (mod.MAX_STRING_CHARS + 1))
        self._assert_err("INT_LOW", mod.validate_json_value, 1, max_depth=-1)
        self._assert_err("INT_HIGH", mod.validate_json_value, 1, max_depth=mod.MAX_JSON_DEPTH + 1)
        self._assert_err("JSON_DEPTH", mod.validate_json_value, [1], max_depth=0)
        self._assert_err("INT_TOO_LARGE", mod.validate_json_value, max_int + 1)
        self._assert_err("FLOAT_FORBIDDEN", mod.validate_json_value, 1.5)
        self._assert_err("BAD_JSON_TYPE", mod.validate_json_value, (1, 2))
        self._assert_err("FORBIDDEN_ENERGY_VALUE", mod.validate_json_value, {"a": "45 W"})
        self._assert_err("FORBIDDEN_ENERGY_KEY", mod.validate_json_value, {"gpu_watts": 1})
        for leak_val in (
            "/" + "home" + "/u",
            "/" + "Users" + "/alice/f",
            "/" + "root" + "/f",
            "$" + "HOME/f",
            "C:\\" + "Users" + "\\alice\\f",
            "c:/" + "users" + "/alice/f",
            "aa:bb:cc:dd:ee:ff",
            "alice" + "@" + "example.org",
        ):
            self._assert_err("FORBIDDEN_LEAK", mod.validate_json_value, {"a": leak_val})
        self._assert_err("FORBIDDEN_LEAK", mod.validate_json_value, {"/" + "home" + "/k": 1})

        self.assertEqual(mod._parse_int_tok("0"), 0)
        self.assertEqual(mod._parse_int_tok("-1"), -1)
        self._assert_err("NEG_ZERO_FORBIDDEN", mod._parse_int_tok, "-0")
        self._assert_err("NEG_ZERO_FORBIDDEN", mod.parse_strict_json, '{"x": -0}')
        self._assert_err("INT_DIGIT_LIMIT", mod._parse_int_tok, "")
        self._assert_err("INT_DIGIT_LIMIT", mod._parse_int_tok, "-")
        self._assert_err("INT_DIGIT_LIMIT", mod._parse_int_tok, "1\u06623")
        self.assertEqual(
            mod.parse_strict_json('{"a": -1, "b": ' + "9" * mod.MAX_INT_DIGITS + "}"),
            {"a": -1, "b": max_int},
        )
        self.assertEqual(mod.parse_strict_json(" " * (mod.MAX_JSON_BYTES - 2) + "{}"), {})
        self._assert_err("BAD_JSON_INPUT", mod.parse_strict_json, 123)  # type: ignore[arg-type]
        self._assert_err("JSON_TOO_LARGE", mod.parse_strict_json, " " * (mod.MAX_JSON_BYTES + 1))
        self._assert_err("JSON_FLOAT_FORBIDDEN", mod.parse_strict_json, '{"x": 1.0}')
        self._assert_err("JSON_CONST_FORBIDDEN", mod.parse_strict_json, '{"x": NaN}')
        self._assert_err("INT_DIGIT_LIMIT", mod.parse_strict_json, '{"x": ' + "9" * (mod.MAX_INT_DIGITS + 1) + "}")
        self._assert_err("JSON_DUP_KEY", mod.parse_strict_json, '{"a": 1, "a": 2}')
        self._assert_err("JSON_DUP_KEY", mod.parse_strict_json, '{"a": 1, "\\u0061": 2}')
        self._assert_err("JSON_DUP_KEY", mod.parse_strict_json, '{"outer": {"k": 1, "k": 2}}')
        self._assert_err("JSON_PARSE_ERR", mod.parse_strict_json, "{bad")

    # 4. Arithmetic, Machin pi bracket, linear algebra, Schur, inertia, & physics operator boundary controls
    def test_04_math_and_operator_boundaries(self) -> None:
        self.assertEqual(mod.q_frac(3, 4), Fraction(3, 4))
        self.assertEqual(mod.wrap_index(-4, 4), 0)
        self.assertEqual(mod.wrap_index(-1, 4), 3)
        self.assertEqual(mod.wrap_index(0, 4), 0)
        self.assertEqual(mod.wrap_index(3, 4), 3)
        self.assertEqual(mod.wrap_index(4, 4), 0)
        self.assertEqual(mod.wrap_index(7, 4), 3)
        self._assert_err("BAD_INT", mod.wrap_index, "0", 4)  # type: ignore[arg-type]
        self._assert_err("INT_LOW", mod.wrap_index, 0, 0)
        self._assert_err("INT_HIGH", mod.wrap_index, 0, mod.MAX_MATRIX_DIM + 1)
        self._assert_err("IDX_RANGE", mod.wrap_index, -5, 4)
        self._assert_err("IDX_RANGE", mod.wrap_index, 8, 4)
        self._assert_err("BAD_INT", mod.require_int, True, "x")
        self._assert_err("ZERO_DEN", mod.q_frac, 1, 0)
        self._assert_err("BAD_FRAC", mod.require_frac, 1, "x")
        self._assert_err("NON_POS_FRAC", mod.require_pos_frac, Fraction(0, 1), "x")
        self._assert_err("ZERO_DIV", mod.q_div, Fraction(1, 1), Fraction(0, 1))
        self.assertEqual(mod.int_comb(5, 0), 1)
        self.assertEqual(mod.int_comb(5, 5), 1)
        self._assert_err("INT_HIGH", mod.int_comb, 3, 4)

        # First-principles pure-Q Machin pi bracket boundaries
        self.assertEqual(mod._atan_inv_partial_q(2, 1), Fraction(1, 2))
        self._assert_err("INT_LOW", mod._atan_inv_partial_q, 1, 1)
        self._assert_err("INT_LOW", mod._atan_inv_partial_q, 5, 0)
        self._assert_err("INT_HIGH", mod._atan_inv_partial_q, 5, 33)
        self.assertGreater(mod._atan_inv_partial_q(5, 32), Fraction(0, 1))
        self.assertTrue(Fraction(3141592653589793, 10**15) < mod.PI_LO < mod.PI_HI < Fraction(3141592653589794, 10**15))

        self._assert_err("BAD_DIM", mod.solve_linear_multi_q, [], [])
        self._assert_err("DIM_MISMATCH", mod.solve_linear_multi_q, [[Fraction(1, 1)]], [[Fraction(1, 1)], [Fraction(2, 1)]])
        self._assert_err("BAD_DIM", mod.solve_linear_multi_q, [[Fraction(1, 1)]], [[]])
        self._assert_err("RAGGED_MAT", mod.solve_linear_multi_q, [[Fraction(1, 1), Fraction(0, 1)]], [[Fraction(1, 1)]])
        self._assert_err("SINGULAR_MATRIX", mod.solve_linear_q, [[Fraction(1, 1), Fraction(1, 1)], [Fraction(1, 1), Fraction(1, 1)]], [Fraction(1, 1), Fraction(1, 1)])
        self.assertEqual(
            mod.solve_linear_q([[Fraction(0, 1), Fraction(1, 1)], [Fraction(1, 1), Fraction(0, 1)]], [Fraction(2, 1), Fraction(3, 1)]),
            [Fraction(3, 1), Fraction(2, 1)],
        )
        self._assert_err("BAD_DIM", mod.rank_and_nullspace_q, [], 1)
        self._assert_err("RAGGED_MAT", mod.rank_and_nullspace_q, [[Fraction(1, 1)]], 2)
        rk_z, basis_z = mod.rank_and_nullspace_q([[Fraction(0, 1), Fraction(1, 1)]], 2)
        self.assertEqual((rk_z, len(basis_z)), (1, 1))

        self._assert_err("BAD_DIM", mod.sylvester_inertia_q, [])
        self._assert_err("RAGGED_MAT", mod.sylvester_inertia_q, [[Fraction(1, 1), Fraction(0, 1)]])
        self._assert_err("NON_SYMMETRIC", mod.sylvester_inertia_q, [[Fraction(1, 1), Fraction(1, 1)], [Fraction(0, 1), Fraction(1, 1)]])
        m_mix = [
            [Fraction(0, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)],
            [Fraction(0, 1), Fraction(0, 1), Fraction(0, 1), Fraction(2, 1)],
            [Fraction(0, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)],
            [Fraction(0, 1), Fraction(2, 1), Fraction(0, 1), Fraction(0, 1)],
        ]
        self.assertEqual(mod.sylvester_inertia_q(m_mix), (1, 1, 2))
        self.assertEqual(mod.sylvester_inertia_q([[Fraction(0, 1), Fraction(0, 1)], [Fraction(0, 1), Fraction(-1, 1)]]), (0, 1, 1))

        # U4 non-diagonal coupled H_8 fold-sheaf Hessian & anchored orb-web dimension bounds
        h8 = mod.build_coupled_auxetic_h8_hessian_q()
        self.assertEqual(len(h8), 8)
        self.assertTrue(all(h8[i][i] == Fraction(0, 1) for i in range(8)))
        self.assertEqual(h8[0][4], Fraction(2, 1))
        self.assertEqual(h8[0][5], Fraction(-1, 1))
        self.assertEqual(mod.sylvester_inertia_q(h8), (4, 4, 0))
        self._assert_err("INT_LOW", mod.build_anchored_orb_stress_int_q, 2, Fraction(1, 1), Fraction(1, 1), Fraction(1, 1))
        self._assert_err("INT_HIGH", mod.build_anchored_orb_stress_int_q, 25, Fraction(1, 1), Fraction(1, 1), Fraction(1, 1))
        self.assertEqual(
            mod.sylvester_inertia_q(mod.build_anchored_orb_stress_int_q(3, Fraction(1, 1), Fraction(5, 1), Fraction(5, 1))),
            (4, 0, 0),
        )
        self.assertEqual(len(mod.build_anchored_orb_stress_int_q(24, Fraction(1, 1), Fraction(5, 1), Fraction(5, 1))), 25)

        self._assert_err("BAD_GRAPH", mod.build_grounded_laplacian_q, 2, [])
        self._assert_err("SELF_LOOP", mod.build_grounded_laplacian_q, 2, [(0, 0, Fraction(1, 1))])
        self._assert_err("NEG_SHUNT", mod.build_grounded_laplacian_q, 2, [(0, 1, Fraction(1, 1))], [(0, Fraction(-1, 1))])
        self.assertEqual(
            mod.build_grounded_laplacian_q(2, [(0, 1, Fraction(1, 1))], [(0, Fraction(0, 1))])[0][0],
            Fraction(1, 1),
        )
        self._assert_err("BAD_DIM", mod.schur_pushforward_q, [[Fraction(1, 1)]], (0,))
        self._assert_err("BAD_BOUNDARY", mod.schur_pushforward_q, [[Fraction(1, 1), Fraction(-1, 1)], [Fraction(-1, 1), Fraction(1, 1)]], (0, 0))
        self._assert_err("BAD_BOUNDARY", mod.schur_pushforward_q, [[Fraction(1, 1), Fraction(-1, 1)], [Fraction(-1, 1), Fraction(1, 1)]], (0, 1))
        self._assert_err("BAD_BOUNDARY", mod.schur_pushforward_q, [[Fraction(1, 1), Fraction(-1, 1)], [Fraction(-1, 1), Fraction(1, 1)]], ())

        self._assert_err("BAD_STAGES", mod.analyze_head_cascade_q, Fraction(1, 1), [])
        self._assert_err("HEAD_SUM", mod.analyze_head_cascade_q, Fraction(2, 1), [Fraction(1, 1)])
        self._assert_err("NON_SUPERCRITICAL", mod.evaluate_belanger_jump_q, Fraction(1, 1), Fraction(1, 5))
        self._assert_err("BAD_MODE", mod.simulate_conductance_feedback_q, Fraction(1, 1), Fraction(1, 4), 1, "bad")
        self._assert_err("DIM_MISMATCH", mod.solve_kirchhoff_ventilation_q, 2, [(0, 1)], [Fraction(1, 1)], [])
        self._assert_err("BAD_GRAPH", mod.exact_cut_survival_q, 2, [(0, 1), (0, 1)])
        self._assert_err("BAD_BAYS", mod.solve_volkersen_discrete_q, [], Fraction(1, 1))
        self._assert_err("NO_SLIP", mod.dougong_hysteresis_q, Fraction(1, 1), Fraction(2, 1), Fraction(2, 1), Fraction(0, 1))
        self.assertTrue(mod.dougong_hysteresis_q(Fraction(12, 1), Fraction(2, 1), Fraction(3, 1), Fraction(0, 1))["in_15_to_30_pct"])
        self.assertFalse(mod.dougong_hysteresis_q(Fraction(12, 1), Fraction(10, 1), Fraction(11, 1), Fraction(0, 1))["in_15_to_30_pct"])
        self.assertFalse(mod.dougong_hysteresis_q(Fraction(12, 1), Fraction(1, 1), Fraction(10, 1), Fraction(0, 1))["in_15_to_30_pct"])
        self._assert_err("BAD_ALPHA", mod.dougong_hysteresis_q, Fraction(1, 1), Fraction(1, 1), Fraction(2, 1), Fraction(-1, 10))
        self._assert_err("BAD_ALPHA", mod.dougong_hysteresis_q, Fraction(1, 1), Fraction(1, 1), Fraction(2, 1), Fraction(11, 10))
        self._assert_err("NON_ROCKING", mod.housner_rocking_q, Fraction(2, 1))
        self._assert_err("BAD_PAT", mod.analyze_euplectella_4x4_q, "unknown", False)
        self._assert_err("BAD_BOOL", mod.analyze_euplectella_4x4_q, "none", 1)  # type: ignore[arg-type]

        d_max = mod.MAX_MATRIX_DIM
        id_max = [[Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(d_max)] for i in range(d_max)]
        self.assertEqual(mod.solve_linear_multi_q(id_max, id_max)[0][0], Fraction(1, 1))
        self.assertEqual(mod.sylvester_inertia_q(id_max), (d_max, 0, 0))
        rk_max, _ = mod.rank_and_nullspace_q([[Fraction(1, 1)]] * (mod.MAX_GRAPH_EDGES * 2), 1)
        self.assertEqual(rk_max, 1)
        self.assertEqual(mod.exact_cut_survival_q(3, [(0, 1), (1, 2), (2, 0)]), (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)))
        self.assertEqual(mod.housner_rocking_q(Fraction(1, 1))["restitution_r"], Fraction(1, 16))
        self.assertFalse(mod.shifted_laplacian_pd_q(2, [(0, 1)], Fraction(2, 1)))
        self.assertFalse(mod.shifted_laplacian_pd_q(2, [(0, 1)], Fraction(3, 1)))
        self.assertTrue(mod.shifted_laplacian_pd_q(2, [(0, 1)], Fraction(1, 1)))


if __name__ == "__main__":
    unittest.main()
