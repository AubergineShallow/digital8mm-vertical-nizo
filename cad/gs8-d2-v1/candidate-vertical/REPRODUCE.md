# Reproduce the concealed-vent review

This is a frozen shadow-plenum review candidate, not a fabrication, energization or complete-service release. Read [REVIEW.md](REVIEW.md) and the [assembly STOPs](ASSEMBLY-VERTICAL.md) first. The supplied compact-Kowa manifest was `53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77`; the review's FX re-export (phase-2 fix-up) replaced it with `dbea5ca508bf172a6ad0f34e5517ceeaed162c9cd3cf3431a0193de79ace0810`, which every refreshed report binds. [current-review-evidence.json](out/compact-kowa_lm6hc/current-review-evidence.json) still identifies the supplied snapshot's reports: the reconciler writes a new one only when every gate passes, and on the FP-16 export it reports 12 gate failures (see [the fix log](review-2026-10-10/FIX-LOG.md), RF). Upstream baseline commit `d38468e58eb2b02d56743e2e0cfdd8f780818a65` and [reviewed export18](history/reviewed-export18/README.md) remain preserved.

Work from the repository root. Use the pinned Python 3.12.14 / CadQuery 2.6.1 environment. `python3 tools/bootstrap_cad.py` recreates `.venv-cad` from the pinned dependency lock. Do not substitute an arbitrary CadQuery version. Run CAD and render jobs serially through `run_locked.py`; do not nest the lock wrapper inside the batch runners.

## Windows and POSIX (review VN-12, VN-18)

- **Clone.** The longest repository path is 132 characters ([REPO-INDEX.md](REPO-INDEX.md)). On Windows either clone into a folder whose own path is at most 120 characters or run `git config --global core.longpaths true` before cloning. `.gitattributes` (`* -text`) keeps every file byte-exact, whatever `core.autocrlf` says.
- **Interpreter.** POSIX: `.venv-cad/bin/python`. Windows (PowerShell): `.venv-cad\Scripts\python.exe`. Below, `python3 X` means `.venv-cad\Scripts\python.exe X` on Windows, and `.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- X` means `.venv-cad\Scripts\python.exe cad\gs8-d2-v1\run_locked.py -- X`. Paths with `/` work in both shells.
- **Packages.** The pinned base lock plus the candidate notes in [requirements-candidate-lock.txt](requirements-candidate-lock.txt): `pypdf` (structural PDF page check) and `scipy` (historical `screen_fps_*.py` studies) are optional and not in the reference environment.
- **Text encoding.** The candidate scripts read and write UTF-8 with LF through `cv_io.py` on every platform; the batch runners also pass `PYTHONUTF8=1` to their children. The three restored coupon reproducers in `structural-review/` are byte-frozen: run them with `python -X utf8` on Windows.
- **POSIX-only steps and their Windows form.** The guide builder compiles `guide/raster.cpp` with a 64-bit `g++` at import; on Windows run it through [guide/run_with_numpy_raster.py](guide/run_with_numpy_raster.py) (pure numpy, tested bit-identical to `raster.cpp`). Blender renders need `blender` on the PATH on any platform; render receipts now record the Blender version (the 9ced753 renders do not).
- **Fresh clone.** The mesh caches the manifests bind are git-ignored ([bound caches](#bound-caches-that-git-does-not-carry)). On a fresh clone, run `export_cache.py regenerate` through `run_locked.py` (first line below) before `review_docs_audit.py --check` and `reconcile_review_evidence.py --check`. It writes only the git-ignored caches. Without them the docs audit lists the missing caches under `bound_cache` (exit 3 when nothing else fails) and the reconciler stops with `Bound cache missing`.

Windows inspect commands (PowerShell, repository root):

```powershell
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/export_cache.py regenerate
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/candidate-vertical/make_bom_vertical.py --check
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/candidate-vertical/review_docs_audit.py --check
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/candidate-vertical/reconcile_review_evidence.py --check
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/candidate-vertical/check_links_vertical.py
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_repo_hygiene.py
```

## Inspect the supplied snapshot

These commands do not rebuild geometry and write nothing; on a fresh clone run `export_cache.py regenerate` first ([bound caches](#bound-caches-that-git-does-not-carry)). The BOM and structural `--check` options verify their generated outputs. The documentation audit and the reconciler are read-only by default (review FP-04): they list every failed binding, missing link, stale selected report, foreign-manifest report in the selected folder and repeated figure that differs from its source row, and exit 0 (clean), 3 (docs audit only: nothing but rebuildable git-ignored caches missing) or 1 (any failure). `--check` also fails when the committed `out/review-docs-audit.json` or `current-review-evidence.json` differs from a fresh run; `--out PATH` writes the result elsewhere; `--write` rewrites the committed file. They do not establish physical qualification.

```sh
python3 cad/gs8-d2-v1/candidate-vertical/make_bom_vertical.py --check
python3 cad/gs8-d2-v1/candidate-vertical/make_wiring_vertical.py --check
python3 cad/gs8-d2-v1/candidate-vertical/structural-review/update_concealed_vent_structure.py --check
python3 cad/gs8-d2-v1/candidate-vertical/review_docs_audit.py --check
python3 cad/gs8-d2-v1/candidate-vertical/reconcile_review_evidence.py --check
python3 cad/gs8-d2-v1/candidate-vertical/make_coverage_vertical.py --check
python3 cad/gs8-d2-v1/candidate-vertical/make_gates_vertical.py --check
python3 cad/gs8-d2-v1/candidate-vertical/make_repo_index.py --check
python3 cad/gs8-d2-v1/candidate-vertical/check_links_vertical.py
python3 cad/gs8-d2-v1/candidate-vertical/structural-review/verify_reference_binding.py
```

The last five (review FP-15) check the generated coverage table, the r7 gate and BX map, the repository index, every relative Markdown link in the repository (frozen copies are allowed only with their banner) and the re-derivable fields of the structural base JSON.

Inspect commands that currently fail on this working tree, and why: after the FX refresh (selected manifest `dbea5ca5`) two of them exit 1, both for reasons recorded in the fix log. `review_docs_audit.py --check` reports 11 failures: six foreign-manifest reports (`out/compact-kowa_lm6hc/current-review-evidence.json`, which the reconciler rewrites only with zero gate failures, and the five render receipts, which need Blender), two for the structural PDF receipt (its builder needs pypdf, which the CAD venv lacks) and three for the concealed guide (rebuild pending). `reconcile_review_evidence.py --check` reports 10 gate failures: the same six foreign-manifest reports, the main audit of each variant (pi5/cooler plus the 13 open roll_catch stub_tilt_on_joint_edge window rows) and `harness_failures_differ` (the FX-H installed sweeps add honest harness failures). The other eight commands exit 0. `export_cache.py status` (with the guide) exits 1 for the guide bindings; `status --no-guide` exits 0.

## Bound caches that git does not carry

The manifests bind every `out/<variant>/meshes/*.json` file and the guide receipt binds every `guide/out-concealed-vents/page-*.png`, by SHA-256. Both are git-ignored (about 34 MB of meshes per variant) and are not committed; the bindings stay. [export_cache.py](export_cache.py) sorts each binding into tracked file or git-ignored cache, checks the caches that are present, and prints what must be rebuilt (exit 0 complete, 3 only caches missing, 1 anything else):

```sh
python3 cad/gs8-d2-v1/candidate-vertical/export_cache.py status
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/export_cache.py regenerate
```

`regenerate` rebuilds each missing mesh JSON from its bound, tracked STEP file and writes it only if its SHA-256 equals the binding; a non-matching rebuild goes to `meshes/_mismatch/` for inspection. Page images come from the guide build below; it rewrites the tracked receipt and PDF, so after it `git diff` must show no change. The reconciler stops with `Bound cache missing` (not a traceback) and the same command when a cache is absent; the docs audit reports it under `bound_cache` and `guide_bound_cache`. The guide rebuild command that `export_cache.py status`, the reconciler and the docs audit print names `build_guide_concealed_vents.py` and says the rasterizer builds only on Linux. On Windows run the same build through [guide/run_with_numpy_raster.py](guide/run_with_numpy_raster.py) instead (command under [pictorial guide](#renders-coupons-and-pictorial-guide)).

The supplied `53e668d4` snapshot predates this (review FP-03): its meshes were tessellated in memory on the author's machine and its guide page 20 printed the build time, so they cannot be rebuilt byte-for-byte, and `status` says so. The next full re-export (FP-16) makes them rebuildable.

## Rebuild geometry and scoped evidence

Use a separate checkout or copy to retain the supplied review snapshot, or pass `--out <scratch folder>` to `export_candidate.py`. Exports are deterministic (FP-03): the STEP header time is fixed at `1970-01-01T00:00:00`, manifests and receipts record no wall-clock time, keys are sorted, and mesh JSON is made from the saved STEP. Two exports from the same sources on the same platform and pinned runtime (Python, CadQuery, OCP; recorded in each manifest) are byte-identical. A different platform can still change last-digit float formatting, and any source change gives a new manifest hash. Rerun and rebind every dependent report; do not paste the supplied `53e668d4` identity onto regenerated files.

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/make_corrected_pi.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/export_candidate.py --storage compact --lens kowa_lm6hc
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/verify_shadow_plenum.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/verify_shadow_outlet_context.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/run_shadow_checks.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/export_shadow_alternatives.py
python3 cad/gs8-d2-v1/candidate-vertical/reconcile_review_evidence.py --write
python3 cad/gs8-d2-v1/candidate-vertical/make_coverage_vertical.py --write
python3 cad/gs8-d2-v1/candidate-vertical/make_gates_vertical.py --write
python3 cad/gs8-d2-v1/candidate-vertical/make_repo_index.py --write
python3 cad/gs8-d2-v1/candidate-vertical/review_docs_audit.py --write
```

`make_corrected_pi.py` creates the source-bound, overlapping named-component Pi assembly. Its raw solid-volume sum is not occupied union material. `export_candidate.py` then writes individual and assembly STEP, print-oriented STL, regenerable mesh JSON, and source/file-bound manifests. Mesh checks establish limited geometric properties, not slicing or strength.

The plenum and finite exterior-mouth checks are separate from `run_shadow_checks.py`. That batch runs mesh, CSI cylinder, rigid and static power, full-material HDMI, supported FPS, current whole-tub USB-head, rigid assembly, rejected closed-panel microSD, and compact core-void checks. It preserves per-check exit codes in `review-check-run.json`; the batch completing is not an aggregate pass. The main audit retains the unresolved cooler/source-Pi conflict as a failure. The new USB checker requires the complete tub and canonical support-source hashes; the earlier missing-extract attempt remains historical.

`export_shadow_alternatives.py` exports compact Fujinon and original-storage Kowa, checks their print meshes, calculates their core-void intervals, then computes fresh untessellated STEP bounds for all three variants. It does not rerun alternative service/harness audits. The compact-Kowa service results must not be transferred to alternatives. Bounding boxes are reported to 0.1 mm, not as measured camera volume. Empty-model core intervals include useful plenum/cooling, cable and service space and the Pi proxy-representation caveat; they are not removable waste.

`reconcile_review_evidence.py` checks already-written report, source and manifest identities and preserves the one active rigid failure. It does not execute CAD. It rejects a changed evidence set rather than certifying a new design automatically: the main audit's info rows must be exactly the accepted set in `evidence_rules.py` (new info rows are never accepted silently), print-check failures must equal the accepted set (empty), and any JSON in `out/compact-kowa_lm6hc/` bound to another manifest fails unless `evidence_rules.DECLARED_HISTORICAL` names it with the manifest it must bind. Stale reports moved out of the selected folder are indexed in `history/stale-selected-reports-2026-10-10/INDEX.json`. It writes only with `--write` and only when every gate passes. Inspect failures and every report's scope before updating the top-level checkpoint or documentation.

For a new export, refresh the BOM and structural supplement without `--check`, then run their checks and the document audit. Relative to the retained reference, the structural script accepts changes to the upper-body rows `tub`, `panel`, `carrier`, `lens_collar`, `s_c4` and `eyecup` (`ALLOWED_CHANGED_ROWS` in `structural-review/update_concealed_vent_structure.py`). When the lower row `base_grip` changes (`ALLOWED_CHANGED_LOWER_ROWS`), it does not use the export18 first-moment transfer. It computes a new J4 upper free body from the bound STEPs instead (`check_scope.j4_direct`). Any other row change, a changed component inventory, or any other geometry, mass or carried-part change requires a fresh engineering calculation. Regenerating its PDF requires renewed visual review and receipt validation.

STEP writers outside the exporter (fixup-1, VN-17): `make_shadow_plenum_coupon.py`, `verify_fps_contact_pad.py` and `verify_fps_pair_guide.py` write their receipt-bound STEP files through `export_cache.export_step` (fixed header time; the coupon receipts record no wall-clock time), so a re-run reproduces the bound hashes on the same runtime. Their committed STEP files and receipts predate this and are rebound by the FP-16 rebuild. Every other live script that writes a STEP file keeps OCCT's wall-clock header and is listed with its reason in `tests/test_deterministic_export.py` (`RAW_STEP_WRITERS`): exploratory probes and study proposals that no live receipt binds, the retained structural-review coupon reproducer and the rejected angled-channel trial. Their STEP bytes are not reproducible; never bind them as current evidence.

## Renders, coupons and pictorial guide

[run_shadow_renders.py](run_shadow_renders.py) invokes Blender on the saved meshes for hero, rear, cooler-side and front ventilation views. It does not rebuild CAD or demonstrate hand occlusion, thermal performance or complete flexible service.

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/run_shadow_renders.py
```

The two plenum coupon crops and their reproduction instructions are in [vent-study/shadow-plenum-coupon](vent-study/shadow-plenum-coupon/README.md). The nine retained structural coupon pieces have a separately restored, hash-verified [reproducer](structural-review/coupons/README.md#reproduce-retained-coupon-geometry). Neither set is part of the nine compact production parts. No slicing, printing, mechanical testing or closed-body cleanout has been demonstrated. The front mouth removes frame support over Z5..40; the nominal 10.7 mm distance is not a two-ended supported bridge, and raster paths may require about 35 mm bridging.

Use [the concealed-vent guide instructions](guide/README-CONCEALED-VENTS.md) and `build_guide_concealed_vents.py`. The original `build_guide_vertical.py`, 29-page guide, `refresh_primary_evidence.py`, `refresh_alternatives.py` and `render_views.py` are preserved earlier workflows, not the selected shadow-plenum reproduction sequence.

For the supplied unchanged snapshot only:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/package_concealed_guide.py
```

On Windows (no 64-bit `g++`), the same build with the numpy rasterizer; it also writes `guide/out-concealed-vents/raster-backend.json`:

```powershell
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/run_with_numpy_raster.py -- --manifest-sha256 <nominated manifest SHA-256>
```

After a rebuild, nominate the exact new manifest SHA-256 instead, freeze all guide inputs, and visually inspect every rendered page before packaging. The guide receipt guards sources, reports, PDF and page images; it is not a physical release. The new structural PDF and source remain separate from the unchanged historical structural report.

Files named `probe*` and rejected routing/ventilation studies are development history ([REPO-INDEX.md](REPO-INDEX.md) lists the selected pipeline apart from them). Some require recorded temporary inputs. Their presence does not make them selected evidence. Every r7 physical gate that still applies ([GATES-VERTICAL.md](GATES-VERTICAL.md)), M1, actual cooler registration, complete FPC/EVF feed, whole flexible service, bridge/cleanout and thermal/occlusion holds remain open. Install the OS microSD on the bench before carrier insertion, or use the documented panel-off service; closed-panel withdrawal remains rejected.
