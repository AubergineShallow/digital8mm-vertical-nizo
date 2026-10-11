# Reproduction of the D2 vertical candidate (9ced753) and the inherited r7 baseline

Reviewer label: repro. Date: 2026-10-10. Read-only on the snapshot clone; all runs in the rebuild worktree.

## Summary

- **The candidate's numbers reproduce.** Geometry of all three variants rebuilds to the same solids: bounding boxes within 3.6e-15 mm, volumes within 1.5e-12 relative, identical STL face counts. Main audit 292 pass / 1 fail / 18 info, with the same 79.902671 mm3 `pi5/cooler` overlap and bbox. Plenum 49 / 0 / 21. Exterior mouths 4 / 0. Print meshes 10 / 10 / 11 with no failures. HDMI 6 / 0, power pass, FPS `geometric_pass_only`, USB head pass, microSD closed path REJECTED, core-void and envelope figures (and the REVIEW.md table) all match.
- **Files are not byte-identical.** STEP files differ by the FILE_NAME timestamp and, in 9 of 47 files, by last-digit float formatting (largest parsed change 1.2e-7 mm). STL bytes differ with identical meshes. 37 of 45 mesh JSON files differ. Manifest hashes therefore change on every rebuild, as REPRODUCE.md says.
- **The r7 baseline still verifies on a byte-exact checkout:** 82/82 regression cases, 73 unittests OK (4 POSIX skips), final-release audit pass (20/20, 86/86, 4/4, 35 categories, 56 open + 2 withdrawn gates).
- **But the documented procedure does not reproduce on the user's Windows machine as shipped.** Four defects stop it: (1) the new `.gitattributes` lets Git for Windows' default `core.autocrlf=true` rewrite 702 text files, which breaks the r7 receipts (sources 1/20, gate docs 0/4) and every candidate source binding; (2) `export_candidate.py` writes backslash manifest keys on Windows, so every verifier fails with `KeyError`; (3) the scripts read and write text in the locale code page, so `review_docs_audit.py` crashes without `PYTHONUTF8=1`; (4) the structural refresh uses exact float equality and refuses a rebuild. I got past (1) to (3) with environment-only steps and a key rewrite; (4) remains.
- **Evidence that cannot be rechecked from the repo:** the 45 mesh JSON files and 32 guide page images that the manifests and guide receipt bind are gitignored, and the mesh files are not byte-reproducible. The docs audit reports this as `files.pass: false` but exits 0.

## Setup

- Snapshot clone: `<snapshot clone>`, a local clone of `digital8mm-vertical-nizo` on the review machine (main at 9ced753). Left byte-identical (only the ignored `.cad.lock` appears in `git status --ignored`).
- Rebuild worktree: `<rebuild worktree>`, a sibling folder `digital8mm-vertical-nizo-rebuild` next to the clone, made with `git worktree add ... HEAD` (detached at 9ced753).
- Interpreter: `8mm\.venv-cad\Scripts\python.exe` (CPython 3.12.14, CadQuery 2.6.1). Windows 11. Every CAD job ran through the clone's `run_locked.py` (serial, shared lock with other review agents).
- Git for Windows sets `core.autocrlf=true` in the system gitconfig. This matters (section 1).
- Logs and probe scripts: `scratchpad\vn\repro\logs\` and `scratchpad\vn\repro\*.py`.

## 1. Line endings: a default Windows clone breaks every hash binding

The candidate replaced r7's `.gitattributes` rule `* -text` ("store every file byte-for-byte; build receipts hash exact bytes") with binary-only rules (`*.step/*.stl/*.png/... -text`). Text files are now subject to `core.autocrlf`.

What happened in practice:

- The first `git worktree add` (default config, `core.autocrlf=true`) wrote **702 text files with CRLF** although the index holds LF (`git ls-files --eol`: 702 `i/lf w/crlf`: 371 `.py`, 188 `.json`, 120 `.md`, 7 `.csv`, ...). `git status` still reports clean, so nobody notices.
- The snapshot clone itself is LF (it was evidently cloned with autocrlf off). A collaborator's plain `git clone` on Windows would not be.
- I re-checked the worktree out with `git -c core.autocrlf=false reset --hard` (index removed first). After that: 897 `i/lf w/lf`, 0 converted. All later runs use this LF tree.

Effect on the inherited r7 receipts (probe `probe_r7_crlf_clone.py`, which runs `git -c core.autocrlf=true checkout-index` for the 164 files the two r7 `build-receipt.json` files hash):

| r7 receipt group | LF tree | autocrlf=true checkout |
|---|---|---|
| Kowa sources | 20/20 | 1/20 |
| Kowa outputs | 86/86 | 81/86 (`checks.json`, `print-manifest.json`, `parts-manifest.json`, `coupons-r1-manifest.json`, `checks-fujinon-sweep1mm.json`) |
| Kowa gate docs | 4/4 | 0/4 |
| Fujinon sources / outputs / gate docs | 20/20, 55/55, 4/4 | 1/20, 52/55, 0/4 |

So `audit_cloud_release.py --final-release` would fail on a default Windows clone of this repo, while it cannot fail that way on a clone of r7. `validation/software-verification.json` is affected the same way (34 of its 42 present files would convert).

Effect on the candidate's own bindings, in the CRLF worktree (`logs/docs_audit_crlf_utf8.log`, `logs/review-docs-audit.crlf.json`): every variant reports `sources.changed` for 71 of 71 bound sources (`model.py`, `layout.py`, ...), and the compact-Kowa manifest hashes to `3bd82641...` instead of `53e668d4...`. `update_concealed_vent_structure.py --check` fails at once with `Reference structural binding is not export18` (the export18 manifest JSON was converted). `reconcile_review_evidence.py` would stop at the first source assertion.

## 2. "Inspect the supplied snapshot" commands

Run from the rebuild root with the pinned interpreter, before any rebuild.

| Command | CRLF tree (default clone), no `PYTHONUTF8` | CRLF tree, `PYTHONUTF8=1` | LF tree, `PYTHONUTF8=1` |
|---|---|---|---|
| `make_bom_vertical.py --check` | exit 1, `Stale output: BOM-VERTICAL.md` (the BOM embeds manifest/report hashes) | exit 1, same | exit 0: "131 explicit rows; all 70 baseline source lines covered" |
| `structural-review/update_concealed_vent_structure.py --check` | exit 1, `Reference structural binding is not export18` | not rerun | exit 1, `Stale structural output: concealed-vent-structural.json` |
| `review_docs_audit.py` | exit 1: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d` | exit 0, but 71/71 sources per variant "changed" | exit 0, but every variant reports `files.pass: false` |

Causes, each confirmed with a probe:

- **cp1252 default encoding.** `review_docs_audit.py` (and most candidate scripts) call `read_text()` / `write_text()` without `encoding=`. On Windows that is cp1252 unless `PYTHONUTF8=1`. Nothing in the repo sets UTF-8 mode, and `run_locked.py` does not either. All later runs here set `PYTHONUTF8=1`.
- **Windows path separators.** The structural `--check` differs from the committed JSON in exactly one line: `"path": "out\compact-kowa_lm6hc\shadow-plenum-checks.json"` (from `str(vp.relative_to(C))`). The Markdown is identical (`probe_struct_diff.py`). The same `str(Path)` pattern puts backslashes into 29 path fields of the fresh docs audit. On POSIX the check would pass.
- **Gitignored bound files.** Each manifest binds 45 (46 for original storage) `meshes/*.json` files. `.gitignore` excludes `out/*/meshes/`, so a clone lacks them and the docs audit reports 45/45/46 missing. Apart from those and the separators, the fresh docs audit equals the committed one: all 71 sources per variant match, all STEP/STL hashes match, BOM 131/70 matches.
- **The docs audit never fails.** It records `"pass": false` but always exits 0 (`review_docs_audit.py` has no failing exit path). REPRODUCE.md lists it as an inspection step, so a reader sees success.

Committed checkpoint identities all hash correctly in the LF tree: manifest `53e668d4...`, `current-review-evidence.json` `4f898587...`, reconciler `9b350bc4...`, guide receipt `d03df5f2...`, export18 checkpoint `13af0ab0...`, Fujinon `c31096ed...`, original storage `ecb18336...`.

Guide receipt (`guide/out-concealed-vents/guide-receipt.json`): 197/197 sources and the PDF hash match. Its 45 mesh files and 32 page images are gitignored, so those 77 bindings cannot be checked from the repository.

## 3. Rebuild per "Rebuild geometry and scoped evidence"

### 3a. Native Windows run (as documented, `PYTHONUTF8=1`)

| Step | Exit | Run time |
|---|---|---|
| `make_corrected_pi.py` | 0 | 62 s |
| `export_candidate.py --storage compact --lens kowa_lm6hc` | 0 | 275 s |
| `verify_shadow_plenum.py` | 1: `KeyError: 'candidate-vertical/model.py'` | 4 s |
| `verify_shadow_outlet_context.py` | 1: `KeyError: 'candidate-vertical/model.py'` | 2 s |
| `run_shadow_checks.py` | every check exit 1 (stopped by me during `rigid`, see below) | 103 s to that point |

Cause: `export_candidate.py` builds the manifest keys with `os.path.relpath(...)` and `str(f.relative_to(out))`. On Windows these are `candidate-vertical\model.py` and `step\pi5.step`. Every verifier looks the keys up with forward slashes:

- `csi`, `fps`, `hdmi`, `power_rigid`: `KeyError: 'step/pi5.step'`; `power_static`: `KeyError: 'step/base_grip.step'`; `usb_head`: `KeyError: 'candidate-vertical/fps_fixed_support.py'`.
- `mesh` does not crash, but all 10 rows fail because `m['files'].get('stl/<name>.stl')` returns None. The row records no reason; watertight, volume and bed fields all read true.
- `rigid` (`verify_candidate.py`) runs on and marks the integrity rows `fail` with `manifest_file_binding: false`. I stopped it (process tree killed; the next queued job then took the lock) because its result would only repeat the key defect.

`make_corrected_pi.py` writes the same backslash keys into `pi5-corrected.json`; that is harmless on one platform but makes a Windows receipt differ from a POSIX one. The r7 tree works on Windows (`CLOUD-START-HERE.md` gives the Windows interpreter path; `run_locked.py` has a Windows lock), and the candidate does not say it is POSIX-only. So the documented rebuild is not reproducible on the user's own platform.

### 3b. Geometry of the compact-Kowa rebuild (before any key rewrite)

Compared with `compare_variant.py` (manifest rows, file hashes, STEP text, STL meshes):

- Corrected Pi: `valid`, 149 solids, raw solid volume sum 24187.427381817084 mm3 and bbox are exactly equal. The STEP differs in two lines of 1,076,751: the FILE_NAME timestamp and one direction component at 1e-16.
- 45/45 manifest rows. Bounding boxes agree to 3.6e-15 mm, volumes to 1.5e-12 relative. Total mass 864.10292147 g, CoM (-46.367, 0.920, 29.905) mm: same to 1e-9.
- 71/71 manifest sources hash the same except `pi5-corrected.json` and `pi5-corrected.step`, which carry the new timestamp (expected).
- STEP: 47 files differ in bytes. 38 differ only in the FILE_NAME timestamp. 9 also differ in last-digit float formatting and `-0.` versus `0.` (3,722 lines in all; largest parsed coordinate change 1.2e-7 mm, in `tub.step`).
- STL: all 10 print STLs differ in bytes, but face counts are identical and volumes agree to 1e-4 mm3; bounds agree to 3.6e-15 mm.
- Mesh JSON: only 8 of 45 are byte-identical to the hashes in the committed manifest. Together with the gitignore (section 2) this means the 45 mesh bindings in the committed manifest and guide receipt cannot be re-verified, even by a rebuild.

Conclusion: the compact-Kowa geometry reproduces. The manifest hash cannot reproduce (timestamps, platform float formatting), which REPRODUCE.md states.

### 3c. POSIX-emulated continuation

To get past the key defect without touching code or geometry, `posixify_manifest.py` rewrote only the path keys of `sources` and `files` in each rebuilt `manifest.json` and `meshes/manifest.json` from `\` to `/` (130, 130 and 133 keys). Everything else, including every hash, is the exporter's own output. The Windows originals are kept in `scratchpad\vn\repro\win-manifests\`. Before this run I restored the two files the native `run_shadow_checks.py` had touched (it had moved the committed `shadow-plenum-head-checks.json` into `history/head-checks/` before its USB-head check failed).

| Step | Exit | Run time | Result vs committed |
|---|---|---|---|
| `verify_shadow_plenum.py` | 0 | 15 s | **49 pass / 0 fail / 21 info**, same 70 row ids and statuses; one number differs at 5.7e-13 relative |
| `verify_shadow_outlet_context.py` | 0 | 37 s | **4 pass / 0 fail**, identical rows |
| `run_shadow_checks.py` | see 3d | | |
| alternatives (sub-steps of `export_shadow_alternatives.py`) | see 3e | | |
| `reconcile_review_evidence.py` | see 3f | | |

The native `export_shadow_alternatives.py` run (step 6 of the driver) exported Fujinon and original storage (exit 0 each, 570 s for the batch) and then stopped at `fujinon_mesh` (exit 1, the same binding defect). Its geometry was compared before the key rewrite:

- Compact Fujinon: 45/45 rows, bbox within 3.6e-15 mm, volume within 1.5e-12 relative; mass 750.68370263 g; 38/47 STEP differ only by timestamp; 10 STL with identical face counts and volumes.
- Original-storage Kowa: 46/46 rows, bbox within 3.6e-15 mm, volume within 6.4e-14 relative; mass 906.36674354 g; 39/48 STEP differ only by timestamp; 11 STL (including `stick_sleeve`) with identical face counts and volumes.

### 3d. `run_shadow_checks.py` (POSIX-emulated), 1,156 s

Per-check exit codes in the fresh `review-check-run.json`: mesh 0 (4 s), csi 0 (43 s), power_rigid 0 (271 s), power_static 0 (16 s), hdmi 0 (192 s), fps 0 (125 s), usb_head 0 (33 s), **rigid 1** (428 s, the documented failure), microsd_rejected_closed_path 0 (4 s), void 0 (41 s). This is the first record of the current runner completing on one manifest.

| Report | Committed | Rebuilt |
|---|---|---|
| `verification.json` (main audit) | 292 pass / 1 fail / 18 info | **292 / 1 / 18**; same 311 row ids and statuses |
| the one failure | `pi5/cooler`, 79.902671 mm3, bbox [-100.8, -56.2036, -1.2, 4.5, 15.05, 56.25] | **identical** (value and bbox) |
| `print-mesh-checks.json` | 10 / 0 | 10 / 0 (lens-collar volume error 7.59523 vs 7.59524 mm3) |
| `csi-source-tool-checks.json` | 2 rows | identical |
| `power-service-checks.json`, `wire-solid-checks.json` | pass | pass, identical numbers |
| `hdmi-solid-checks.json` | 6 / 0 / 0 | identical |
| `integrated-fps-checks.json` | `geometric_pass_only` | same; numbers within 4.7e-15 relative |
| `shadow-plenum-head-checks.json` | `pass_for_bounded_head_reservation`, 10 rows | same; numbers within 1.4e-13 relative |
| `microsd-service-dependency.json` | REJECTED closed-panel path | same |
| `volume-compact-kowa_lm6hc.json` | core-void interval | same within 6.5e-13 relative |

The only non-numeric differences in `verification.json` are the order of the source-integrity rows (they come from `glob('*.py')`, whose order differs between platforms) and new hashes for the corrected-Pi STEP/receipt. The committed USB-head report also records the author's absolute path `/workspace/scratch/8ece9a785de6/digital8mm_hidden_vents/...` as `mechanical.manifest_path`.

### 3e. Alternatives (sub-steps run one by one, POSIX-emulated)

| Step | Exit | Run time | Result |
|---|---|---|---|
| `verify_print_meshes.py --variant compact-fujinon_hf6xa` | 0 | 3 s | 10 / 0, same as committed |
| `verify_print_meshes.py --variant original-kowa_lm6hc` | 0 | 3 s | 11 / 0, same as committed |
| `measure_volume.py compact-fujinon_hf6xa` | 0 | 43 s | same within 6.5e-13 |
| `measure_volume.py original-kowa_lm6hc` | 0 | 41 s | same within 2.3e-13 |
| `measure_comparison.py` | 0 | 94 s | `assembled-comparison.json` same within 2.6e-8 relative |

The REVIEW.md envelope table matches both the committed and the rebuilt comparison: baseline Kowa 244.8 x 79.4 x 216.8 mm (4.213 L), compact Kowa 248.8 x 72.8 x 216.8 (3.926 L, -6.8%), baseline Fujinon 239.2 x 79.4 x 216.8 (4.117 L), compact Fujinon 243.2 x 72.8 x 216.8 (3.838 L, -6.8%), original-storage Kowa 275.8 x 72.8 x 216.8 (4.352 L, +3.3%).

### 3f. `reconcile_review_evidence.py` and the post-rebuild refresh

- Reconciler: exit 0, 1 s. New manifest `b0dccdee...`, 12 reports bound, one active rigid failure (`pi5/cooler`). The fresh `current-review-evidence.json` differs from the committed one only in hashes and timestamps.
- `make_bom_vertical.py` then `--check`: exit 0 both; 131 rows, 70 baseline lines.
- `structural-review/update_concealed_vent_structure.py` (refresh, as REPRODUCE.md says to do after a new export): **exit 1**, `Unexpected changed components: ['eyepiece', 'xt30_pair', 'tripod_nut', 'base_grip', 'knob_fps', 'tub', 'panel', 'lens_collar']`. The script compares manifest rows with exact dict equality. The six extra rows differ from export18 only in the last float digit (for example knob_fps volume 2168.466251538382 vs 2168.4662515383825; eyepiece bbox in the 15th digit). So the documented refresh cannot be completed after a rebuild on this platform, and the structural supplement stays bound to the old manifest.
- `review_docs_audit.py` after the rebuild: exit 0; all three variants bind sources and files. It reports `checkpoint_status.guide_receipt_current: true` although the guide receipt still nominates `53e668d4...`. That field only checks that the receipt file matches the hash recorded in CHECKPOINT-STATUS.json, not that the guide matches the current manifest.

## 4. Inherited r7 baseline (rebuild worktree, LF bytes)

All through the clone's `run_locked.py`, `PYTHONUTF8=1`. The r7 release was not rebuilt; the carried outputs were checked.

| Check | Result | Expected (validation/README.md, r7) |
|---|---|---|
| `test_r3_regressions.py` (cwd `cad/gs8-d2-v1`) | exit 0, **82 of 82 cases pass**, 118 s | 82 of 82 |
| unittest list (9 modules) | exit 0, **Ran 73 tests, OK (skipped=4)**; the 4 skips are the POSIX kernel-lock tests in `test_run_locked`; 20 s | 73 OK, 4 POSIX-only skips |
| `audit_cloud_release.py --out cad/gs8-d2-v1/out --final-release --alternate-out .../_fujinon-cloud-polish-20261007` | exit 0, **pass**: sources 20/20, outputs 86/86, gate docs 4/4, 35 categories, 58 physical gates (56 open, 2 withdrawn), no failures | same |

The tests left no files behind (`git status` clean outside `candidate-vertical`).

Changes outside `candidate-vertical` since d38468e: `.gitattributes`, `.gitignore`, `README.md` and a new `cad/gs8-d2-v1/fonts/DejaVuSans.ttf`. No r7 source, output or gate document changed, which is why the r7 audit still passes on byte-exact checkouts. The r7 pass depends on byte-exact checkout, which the new `.gitattributes` no longer guarantees (section 1).

Inherited, not caused by the candidate: `validation/software-verification.json` already disagrees with this tree for `tests/test_d2_app.py` and `README.md`, and names `SETUP.md` and `REPRODUCING.md`, which this D2-only repo does not carry.

## 5. Other reproducibility observations

- **Windows-written evidence is CRLF.** The candidate scripts write reports with `write_text()`, which emits CRLF on Windows (`git ls-files --eol`: rebuilt `print-mesh-checks.json` is `w/crlf`). Under the old `* -text` rule git stored those bytes as written. Under the new rules, `git add` with `core.autocrlf=true` stores LF, so every `report_sha256` / `manifest_sha256` computed on Windows would disagree with the committed blob on any LF checkout. Restoring `* -text` (or writing with `newline='\n'`) avoids this.
- **Run records do not cover the selected evidence.** `review-docs-audit.json` cites `out/final-check-run.json` (logs in `/tmp/d2-final-*.log`, no manifest field) and `out/primary-refresh.json` (bound to manifest `c9e1e207...`, not `53e668d4...`). The only batch record for `53e668d4...` is `history/shadow-first-check-run/review-check-run.json`, which used the older `verify_corrected_usb_head.py` and has no microSD step. No committed record shows the current `run_shadow_checks.py` completing on the selected manifest; the reports were evidently produced by separate runs (for example `microsd-service-dependency.json` at 15:36Z, after that batch ended at 15:22Z). Check logs are gitignored (`*.log`).
- **Stale reports sit next to current ones** in `out/compact-kowa_lm6hc/`: `ventilation-checks.json` (manifest `c392feab...`), `wall-probe-context.json` (`c9e1e207...`), `csi-access-checks.json` (`e8648073...`). The docs audit labels the first two as historical. `csi-access-checks.json` is only named in the export18 history checkpoint and in `delivery-core-paths.json`, with no label in the current evidence.
- **Reconciler text is hard-coded.** `reconcile_review_evidence.py` asserts only that exactly one rigid failure exists with id `pi5/cooler`; the volume `79.902671mm3` in `prominent_holds` is a string literal, not read from `verification.json`. A rebuild with a different overlap would still print the old number.
- **Tools absent here.** `run_shadow_renders.py` calls `blender` (not installed). `guide/software_lineart.py` compiles `raster.cpp` with `g++ -shared -fPIC` into `raster.so` and loads it with ctypes; that targets POSIX, and `raster.so` is gitignored. Neither is in the core rebuild sequence; both stay unverified here.
- **Path length.** The longest tracked path is 132 characters (r7: 92). With the clone at `<snapshot clone>\` (a 69-character folder prefix on the review machine) the full path is about 200 characters; a clone more than about 60 characters deeper fails on Windows without `core.longpaths` (seen when I tried to export the tree into the scratch directory).
- **Mesh check hides its binding result.** `verify_print_meshes.py` folds the STL hash binding into `status` but does not write it to the row, so a binding failure looks like an unexplained fail with every listed property true.

## 6. Findings

| ID | Severity | Kind | Finding | Fix |
|---|---|---|---|---|
| R-1 | major | latent | New `.gitattributes` dropped r7's `* -text`. With Git for Windows' default `core.autocrlf=true`, 702 text files check out as CRLF; r7 receipts drop to 1/20 sources, 81/86 outputs, 0/4 gate docs (Fujinon 1/20, 52/55, 0/4); all 71 candidate source bindings and the export18 structural binding break. Windows-written reports would be normalized on commit. | Restore `* -text` at the top of `.gitattributes`; keep the binary `-diff` lines. |
| R-2 | major | latent | `export_candidate.py` (and `make_corrected_pi.py`) build manifest keys with `os.path.relpath` / `str(Path)`; on Windows the keys contain `\` and every verifier (`verify_shadow_plenum`, `verify_shadow_outlet_context`, csi, power x2, hdmi, fps, usb_head) fails with `KeyError`; the mesh check silently fails all rows. | Use `.as_posix()` / `PurePosixPath` for every recorded key and path; add a test that runs the key lookups on Windows. |
| R-3 | minor | latent | Text I/O uses the locale code page. `review_docs_audit.py` crashes on Windows (`UnicodeDecodeError ... 0x9d`) unless `PYTHONUTF8=1`; nothing in the repo or `run_locked.py` sets it. | Pass `encoding='utf-8'` (and `newline='\n'` on writes), or set `PYTHONUTF8=1` in `run_locked.py` and document it. |
| R-4 | minor | latent | `str(Path)` in recorded report paths gives backslashes on Windows, so `update_concealed_vent_structure.py --check` fails on the committed snapshot (one line differs) and the docs audit records 29 backslash paths. | Same as R-2. |
| R-5 | minor | latent | `update_concealed_vent_structure.py` refresh compares manifest rows with exact equality; a rebuild flags 6 unchanged parts as changed (last-digit float differences) and refuses to refresh, so REPRODUCE.md's post-rebuild step cannot complete. | Compare numeric fields with a stated tolerance (for example 1e-6 mm and 1e-9 relative); keep exact comparison of ids, kinds and sources. |
| R-6 | minor | latent | Bound but unshipped evidence: 45 (46) `meshes/*.json` per manifest and 32 guide page images are gitignored; mesh JSON is not byte-reproducible (8/45 identical after rebuild). The committed `review-docs-audit.json` shows `files.pass: true`, which a clone cannot reproduce. | Either commit the bound files, or stop hashing regenerable caches in the manifest/receipt and bind a deterministic digest (for example rounded vertex data) instead; say so in REPRODUCE.md. |
| R-7 | minor | latent | `review_docs_audit.py` exits 0 even when bindings fail; `checkpoint_status.guide_receipt_current` only checks the receipt file hash, so it stays true after the manifest changes. | Exit non-zero on any binding failure; rename or redefine the guide field to compare the receipt's nominated manifest with the current one. |
| R-8 | minor | latent | No committed run record of the current `run_shadow_checks.py` on the selected manifest; cited run records are for other manifests or point to `/tmp` logs; check logs are gitignored. | Commit the fresh `review-check-run.json` (and logs, or their hashes) with the next evidence refresh. |
| R-9 | minor | latent | `reconcile_review_evidence.py` writes the 79.902671 mm3 hold as a literal string; it does not read the value from `verification.json`. | Format the hold text from the failing row's `overlap_mm3`. |
| R-10 | info | latent | Stale reports bound to other manifests sit in the selected output folder (`ventilation-checks.json`, `wall-probe-context.json`, `csi-access-checks.json`); the first two are labeled historical. | Move them under `history/` or label all three. |
| R-11 | info | latent | Committed USB-head report embeds the author's absolute path `/workspace/scratch/8ece9a785de6/...`; four probe/refresh scripts reference `/tmp`. | Record repo-relative paths. |
| R-12 | info | latent | Longest tracked path is 132 characters (r7: 92); deep Windows clone locations hit MAX_PATH without `core.longpaths`. | Shorten routing-snapshot folder names or document `core.longpaths=true`. |
| R-13 | info | latent | Renders need Blender; the guide needs `g++ -fPIC` and a POSIX `raster.so` (gitignored). Not reproducible on this host; outside the core sequence. | Document the platform requirement or add a Windows path. |
| R-14 | info | existing | Confirmed: geometry, main audit (292/1/18, 79.902671 mm3), plenum (49/0/21), mouths (4/0), meshes, HDMI, power, FPS, USB head, microSD rejection, void and envelope figures all reproduce. | None. |
| R-15 | info | existing | Confirmed: inherited r7 baseline verifies on a byte-exact checkout (82/82; 73 OK, 4 skips; audit pass 20/20, 86/86, 4/4, 35 categories, 56 + 2 gates). No r7 source, output or gate doc changed. | None. |

Run times on this host (wall clock excludes lock waits): corrected Pi 62 s; compact-Kowa export 275 s; Fujinon plus original-storage export 570 s together; plenum 15 s; mouths 37 s; batch checks 1,156 s (main audit 428 s); alternative meshes 3 s each; voids about 42 s each; comparison 94 s; reconciler 1 s. r7: regression cases 118 s; unittests 20 s; audit 2 s.

## Files

- Logs: `scratchpad\vn\repro\logs\` (`rb_*` native run, `px_*` POSIX-emulated run, `r7_*` baseline, `cmp_*` comparisons, `post_*` post-rebuild refresh).
- Native-run evidence: `scratchpad\vn\repro\native-run\`. Windows-original manifests: `scratchpad\vn\repro\win-manifests\`.
- Probes: `compare_variant.py`, `compare_checks.py`, `probe_r7_crlf_clone.py`, `probe_r7_receipt_eol.py`, `probe_struct_diff.py`, `posixify_manifest.py`, drivers `rebuild_driver.sh`, `posix_driver.sh`, `r7_driver.sh`.
- The rebuild worktree now holds the rebuilt outputs (manifest `b0dccdee...` for compact Kowa); nothing was committed.
