# Biomimetic × Global-Historical Exact-$\mathbb{Q}$ Mechanics Study

Self-contained, zero-dependency, pure-$\mathbb{Z}/\mathbb{Q}$ structural and hydraulic verification study certifying **exact operator equivalences and provable algebraic obstructions** across six biomimetic geometries and mechanisms (beaver-dam cascades, spider orb webs, subterranean ant/termite tunnel networks, tailorbird stitched seams, *Euplectella aspergillum* sponge lattices, coupled auxetic fold-sheaf mechanisms) and seven global-historical engineering systems (Petra Nabataean cascades & vented conduits, Gier Roman inverted siphon, Machu Picchu hydraulic jumps & ashlar masonry, Tipón Inca stepped hydraulic-jump terraces, Casarabe & Upano Amazonian networks, Chinese *Dougong* timber brackets), directly aligned with `optifab/q/inertia.py` (`Inertia(pos, neg, zero)`).

## Scope & Measurement Policy

- **`claim_scope`:** `model_and_checker_only_no_bench_measurement` — all theorems and witnesses are exact algebraic computations over $\mathbb{Z}$ and $\mathbb{Q}$ (`int` and strict two-argument `fractions.Fraction(num, den)`), including a first-principles pure-$\mathbb{Q}$ Machin alternating-series $\pi$ bracket.
- **`energy_power_status`:** `UNCONTROLLED_LAPTOP_NOT_CLAIMED` — zero uncontrolled laptop wattage, thermal-power, or per-token energy claims are read, emitted, or permitted by the verifier.
- **Zero-Float & Non-Escape Trust Path:** Enforced both by construction and by a counter-derived in-module AST self-audit (`U6`) verifying `has_nonempty_ast`, `0` float/complex literals, a strict 14-module pure-stdlib import allowlist (`0` disallowed imports), `0` forbidden float/format/dunder calls, `f-string` format specs, or unguarded `json.loads(...)` calls (requiring explicit non-`None` `parse_int`, `parse_float`, and `parse_constant`), `0` `ast.Div`/`FloorDiv`/`Mod` (`/`, `//`, `%`) nodes, `0` unsafe `ast.Pow` (`**`) nodes (bounded non-nested literal exponents in `[0, 64]`), `0` non-integer-pair or rebound `Fraction(...)` references, `0` bare `assert` statements, and `0` dynamic/module escapes (`__builtins__`, `sys.modules`, `getattr`, `literal_eval`, `__truediv__`, disallowed `os.*` attributes, `float`/`sys`/`os`/`json`/`type` rebinding, relative imports).

## Bundle Contents

| File | Role |
|---|---|
| [biomimetic_historical_mechanics_audit.py](biomimetic_historical_mechanics_audit.py) | Pure-$\mathbb{Z}/\mathbb{Q}$ verifier & exact-operator engine (`--standalone`, `--write`, `--check <json>`, with `--expected-source-sha256 <hex64>` enforced uniformly across all modes), ancestor-symlink + `O_NOFOLLOW`/`O_NONBLOCK` + `fstat(S_ISREG)` regular-file IO, `-0` JSON token rejection, linear-time $O(N)$ energy-claim guard, duplicate-key rejection, live recomputation, and counter-derived AST self-audit |
| [biomimetic_historical_mechanics_certificate.json](biomimetic_historical_mechanics_certificate.json) | Canonical self-bound zero-float JSON certificate (`payload_sha256` + `certificate_sha256`, `6/6` gates PASS) |
| [test_biomimetic_historical_mechanics_r5.py](test_biomimetic_historical_mechanics_r5.py) | Assertion-free R5 adversarial, boundary, `optifab.q.inertia.Inertia` parity (SPD & PSD kernels), ancestor-symlink/`O_NOFOLLOW`/FIFO/BOM/CRLF/dup-key/`-0`, linear-time ReDoS energy-guard, all-mode CLI pin, and AST negative-control test suite |
| [REPORT.md](REPORT.md) | Full mathematical analysis, three-tier exact-$\mathbb{Q}$ classification taxonomy, honest scope boundaries, and cross-repository operator-transfer table |

## Self-Bound Certificate & Verifier Digests

- **`payload_sha256`:** `491e47c109048e2415de73638bd0c473492102839e2ec4f37acbbff8b383c61c`
- **`certificate_sha256`:** `4f80fea31d4ca9a52924378510e12773abb2fcd7597cdf14ddd650425cda2876`
- **Raw file bytes SHA-256 (`biomimetic_historical_mechanics_certificate.json`):** `6c62691a8bc3fa5f0c67630febc4461f3c1ced4e36cc3d47df3ce6d32e8640e4`
- **Verifier source SHA-256 (`biomimetic_historical_mechanics_audit.py`):** `f2b965ffb885835c8f0b4459c32ab3bbecb4ec76939df7c8e7ace540b99b6947`

## Reproducibility & Offline Verification Commands

Run from the repository root with zero external dependencies across all three isolated Python modes (`-I -B`, `-I -O -B`, `-I -B -W error`):

```bash
# 1. Byte-identical deterministic certificate reproduction (must match 6c62691a... across all 3 modes)
python3 -I -B studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_audit.py --standalone | sha256sum
python3 -I -O -B studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_audit.py --standalone | sha256sum
python3 -I -B -W error studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_audit.py --standalone | sha256sum

# 2. Fail-closed verification of the committed JSON certificate + pinned verifier source SHA-256
python3 -I -B studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_audit.py \
  --check studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_certificate.json \
  --expected-source-sha256 f2b965ffb885835c8f0b4459c32ab3bbecb4ec76939df7c8e7ace540b99b6947
python3 -I -O -B studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_audit.py \
  --check studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_certificate.json \
  --expected-source-sha256 f2b965ffb885835c8f0b4459c32ab3bbecb4ec76939df7c8e7ace540b99b6947
python3 -I -B -W error studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_audit.py \
  --check studies/biomimetic-historical-exact-mechanics/biomimetic_historical_mechanics_certificate.json \
  --expected-source-sha256 f2b965ffb885835c8f0b4459c32ab3bbecb4ec76939df7c8e7ace540b99b6947

# 3. Full R5 adversarial, optifab.q.inertia parity, energy-guard, CLI, & AST negative-control test suite
python3 -I -B studies/biomimetic-historical-exact-mechanics/test_biomimetic_historical_mechanics_r5.py
python3 -I -O -B studies/biomimetic-historical-exact-mechanics/test_biomimetic_historical_mechanics_r5.py
python3 -I -B -W error studies/biomimetic-historical-exact-mechanics/test_biomimetic_historical_mechanics_r5.py
```
