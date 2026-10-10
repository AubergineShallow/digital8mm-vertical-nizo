# Phase 1 status (review 2026-10-10 fixes)

Closeout of phase 1 on branch `review/vn-fixes-20261010` of the vertical-Pi clone (base 9ced753 on r7 d38468e, selected manifest 53e668d4, compact Kowa). Phase 1 ran FP-01 to FP-10 and FP-12 plus fixup-1 (see [FIX-LOG.md](FIX-LOG.md)). This file gives the status of all 84 register entries, the test and check results measured on 2026-10-11 (04:16-05:29 local, UTC+8), the failures that are now expected by design, and what phase 2 must do. Nothing here is a physical qualification. Nothing was committed.

## 1. Headline

- **84 entries: 22 closed in phase 1, 19 with a ported check that fails by design (waiting for CAD or the FP-16 re-export), 18 open for phase 2, 7 user decisions, 18 hardware.**
- **Tests: 19 files, 240 tests, all OK** in the final state (3 marked expected failures in test_collar_r7_mechanical). Right after the batch, 2 tests failed on the refreshed records. Neither was fixed by weakening a check: one report the batch had written with a local absolute path was restored, and the refreshed main audit is now held to the reconciler's own accepted info set, still exactly (section 3.1). The candidate's own older test_routes_source.py still fails 2 of 10, as it did on 9ced753.
- **r7 suite intact:** test_r3_regressions 82/82, unittest list 73 OK (4 POSIX skips), audit_cloud_release --final-release pass (20/20, 86/86, 4/4, 35 categories, 58 gates: 56 open, 2 withdrawn).
- **Main audit 481 pass / 16 fail / 32 info** in 20 categories (9ced753: 292 / 1 / 18 in 10). The 16 failures are all expected: pi5/cooler 79.902671 mm3, 7 source bindings changed by phase-1 edits, 4 carrier driver rows, 4 collar washer rows.
- **Batch: 15 checks, 6 exit 0, 9 exit 1.** 4 are ported checks failing on the geometry (print, harness, main audit, check_scope), 1 is the missing mesh cache, 4 are verifiers that refuse a manifest whose sources changed (power_rigid, fps, void; plus plenum and outlet outside the batch). Docs audit exit 1 (27), reconciler exit 1 (18), BOM and structural --check exit 0, cache status exit 1.
- Changes in this closeout: refreshed batch records and the new run record, one BOM line regenerated, one test assertion pointed at the reconciler's accepted info set, the usb_head report restored. Nothing committed.

## 2. How this was measured

- Tree: the clone's working tree as the phase-1 lanes left it (FIX-LOG last entry 04:11), no other CAD job running. Python `8mm/.venv-cad` (pinned CadQuery 2.6.1), `PYTHONUTF8=1` set by the runner (the I/O code itself no longer needs it: test_windows_smoke).
- Every test and CAD job went through `cad/gs8-d2-v1/run_locked.py`, one at a time. Runner script and raw logs: session scratchpad `vnfix/closeout/` (`run_closeout.sh`, `summary.txt`, `pre/`, `r7/`, `batch/`, `post/`, `extra/`).
- Order: (1) the 19 phase-1 test files under `candidate-vertical/tests/`; (2) the REPRODUCE.md inspect commands (`make_bom_vertical.py --check`, structural `--check`, `review_docs_audit.py --check` and `--out`, `reconcile_review_evidence.py --check` and `--out`, `export_cache.py status`); (3) the r7 suite carried in the repo (`test_r3_regressions.py`, the 9-module unittest list from validation/README.md, `audit_cloud_release.py --final-release` with the Fujinon alternate); (4) the candidate batch `run_shadow_checks.py` (15 checks; its `rigid` step is the full main audit `verify_candidate.py`); (5) all tests and inspect commands again on the refreshed records; (6) a final stage: `verify_shadow_plenum.py` and `verify_shadow_outlet_context.py` (REPRODUCE runs them outside the batch), `make_bom_vertical.py` (regenerate), the candidate's own `test_routes_source.py`, the two tests that failed in (5), and the inspect commands once more.
- Before the batch, every text evidence file under candidate-vertical (214 files) was copied to `vnfix/snap/phase1-closeout/`, and SHA-256 lists of the whole folder were taken before and after (`batch/hash-before.txt`, `hash-after.txt`).


## 3. Results

### 3.1 Phase-1 tests (`candidate-vertical/tests/`, 19 files, 240 tests)

| File | Before batch | After batch | Lane |
|---|---|---|---|
| test_assembly_state.py | 11 OK | 11 OK | FP-05 |
| test_build_order_docs.py | 23 OK | 23 OK | FP-06 |
| test_check_scope.py | 21 OK | 21 OK | FP-12 |
| test_collar_r7_mechanical.py | 15 OK, 3 expected failures | 15 OK, 3 expected failures | FP-08 |
| test_cross_platform_io.py | 12 OK | 1 failure (no backslash in any JSON: the batch-written usb_head report held an absolute Windows path); after restoring the committed report: 12 OK | FP-02 |
| test_deterministic_export.py | 20 OK | 20 OK | FP-03 |
| test_driver_checks.py | 18 OK | 18 OK | FP-07 |
| test_evidence_numbers.py | 8 OK | 8 OK | FP-04 |
| test_evidence_tooling.py | 15 OK | 1 failure (test_exact_info_set compared the refreshed main audit with the static 18-row set); after pointing it at the reconciler's accepted set: 15 OK | FP-04 |
| test_export_plan.py | 6 OK | 6 OK | fixup-1 (FP-03) |
| test_guide_scenes.py | 3 OK | 3 OK | FP-06 |
| test_harness_checks.py | 24 OK | 24 OK | FP-10 |
| test_j7_collar.py | 14 OK | 14 OK | FP-08 |
| test_print_checks.py | 11 OK | 11 OK | FP-09 |
| test_refit_state.py | 15 OK | 15 OK | fixup-1 (FP-05/06) |
| test_repo_eol.py | 7 OK (145 s; includes the r7 final-release audit on an emulated autocrlf clone) | 7 OK (171 s) | FP-01 |
| test_third_party_notices.py | 9 OK | 9 OK | FP-01 |
| test_windows_smoke.py | 3 OK | 3 OK | FP-02 |
| test_wire_terminal_rules.py | 5 OK | 5 OK | fixup-1 (FP-12) |

The three expected failures in test_collar_r7_mechanical are marked `expectedFailure`, so a fixed collar shows up as an unexpected success (a failed run): the two washer tests (VN-55, FP-11d) and r7 `prepare_print` on the candidate Fujinon collar (the candidate prints through `model.collar_print_stock`, which a separate test holds to the r7 contract and which passes).

Final re-run on the finished tree (after the BOM regeneration, the test change, this file and the FIX-LOG lines): test_evidence_numbers 8, test_build_order_docs 23, test_windows_smoke 3, test_cross_platform_io 12, test_evidence_tooling 15 and test_repo_eol 7 (144 s), all OK.

The candidate's own older test `candidate-vertical/test_routes_source.py` (not in the phase-1 set): 10 tests, 2 fail. test_frozen_mechanical_geometry_unchanged differs in the last float digit of a frozen polyline; test_full_rigid_connectors_retained finds the p_usb_pi box at x [-152.78, -121.78] where it expects [-153, -122]. FP-02 recorded the same two failures on the unchanged 9ced753 snapshot, so they are inherited, not phase-1 regressions.

### 3.2 REPRODUCE.md inspect commands

| Command | Before batch | After batch (final state) |
|---|---|---|
| `make_bom_vertical.py --check` | exit 0 (131 rows, 70 baseline lines) | exit 1 straight after the batch (the BOM text quotes whether the main audit is bound to the current verifier); regenerated with `make_bom_vertical.py` (one line of BOM-VERTICAL.md changed, CSV unchanged), then exit 0 |
| structural `update_concealed_vent_structure.py --check` | exit 0 | exit 0 |
| `review_docs_audit.py --check` | exit 1, 34 failures: binding 8, bound_files 4, stale_selected_report 17, report_input 2, cooler_witness_number 3 | exit 1, 27 failures: binding 8, bound_files 4, stale_selected_report 11, checkpoint_number 1 (CHECKPOINT-STATUS still says 292 / 1 / 18), cooler_witness_number 3 |
| `reconcile_review_evidence.py --check` | exit 1, 38 failures: source_binding 7, export_files 1 (bound cache missing), report verifier changed 12, fps_dependency 1, check_scope_dependency 1, missing_info_row 14, print_failures_differ 1, harness_failures_differ 1 | exit 1, 18 failures: source_binding 7, export_files 1, report verifier changed 6 (power_rigid, fps, usb_head, plenum, exterior_mouths, void), fps_dependency 1, rigid 1 ("New active rigid fault": exactly the 16 main-audit failures of section 7), print_failures_differ 1, harness_failures_differ 1. The 14 missing info rows are gone |
| `export_cache.py status` | exit 1: compact-kowa 45, compact-fujinon 45, original-kowa 46 mesh JSON and the guide (32 pages, 45 meshes) `cache_missing_unregenerable` | exit 1, unchanged |

All of the docs-audit and reconciler failures are expected at this point. They are the I/O-only source edits of FP-02 (7 manifest sources changed: export_candidate, make_corrected_pi, model, official_pi5_assembly, official_pi5_csi, official_pi5_geometry, power_geometry), reports written by verifiers that phase 1 changed, git-ignored caches the 53e668d4 snapshot cannot rebuild, the manifests' "Retain 32.3614 mm3" text that FP-04 fixed at its source, and the ported checks' failures (section 7). Each one clears only through the FP-16 re-export and rebind or the CAD fixes, never by editing a hash or an accepted set.

### 3.3 Upstream r7 suite carried in the repo (cwd `cad/gs8-d2-v1`)

| Check | Result | r7 expectation |
|---|---|---|
| `test_r3_regressions.py` | exit 0, 82 of 82 cases pass (161 s) | 82 of 82 |
| unittest list (9 modules from validation/README.md) | exit 0, Ran 73 tests, OK (skipped=4, the POSIX kernel-lock tests in test_run_locked) | 73 OK, 4 POSIX skips |
| `audit_cloud_release.py --out cad/gs8-d2-v1/out --final-release --alternate-out cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007` | exit 0, pass: sources 20/20, outputs 86/86, gate docs 4/4, 35 categories, 58 physical gates (56 open, 2 withdrawn), 0 failures | same |

The r7 baseline is intact after phase 1.


## 4. Candidate check batch and main audit

`run_shadow_checks.py` (runner 15238fc4) on manifest 53e668d4, 20:28-21:15 UTC (47 min; the main audit took 28 min). The run record is the new `out/compact-kowa_lm6hc/review-check-run.json`; its logs are in `out/compact-kowa_lm6hc/check-logs/` and are git-ignored (`*.log`).

| Check | Exit | Result | Why |
|---|---|---|---|
| bound_files | 1 | 45 mesh JSON missing, not rebuildable | VN-04: 53e668d4 predates FP-03; FP-16 re-export |
| mesh | 0 | 10 / 0; rows now carry `expected_sha256` and `manifest_file_binding` (VN-32) | |
| print | 1 | see section 7 | ported r7 print rules fail on the current parts (VN-25, VN-51..58) |
| build_order_docs | 0 | 23 OK | |
| csi | 0 | 2 CSI tool rows | |
| power_rigid | 1 | refused: `Stale source: candidate-vertical/model.py`; nothing written | the verifier refuses a manifest whose sources changed (FP-02/04/12 edits); FP-16 re-export |
| power_static | 0 | pass, 44 obstacles (every material row), 3 runs and 3 fixtures (VN-30) | |
| hdmi | 0 | 13 pass / 0 fail (was 6): heads against printed and all material, screw fixtures, full ribbon installed and premate, carried sweep (VN-30) | |
| fps | 1 | refused: source list changed; nothing written | as power_rigid |
| harness | 1 | 20 pass / 15 fail / 20 info, byte-identical to the committed record | VN-26, VN-28, VN-47, VN-62 (section 7) |
| usb_head | 0 | `pass_for_bounded_head_reservation` | its report recorded this machine's absolute Windows path (verify_shadow_usb_head.py:88); test_cross_platform_io failed on it, so the committed 53e668d4 report was restored byte-for-byte (sha abd3a4d1) and the batch copy kept only in the scratchpad. The run record still lists this run |
| rigid (main audit) | 1 | **481 pass / 16 fail / 32 info, 529 rows, 20 categories** (9ced753: 292 / 1 / 18, 311 rows, 10 categories) | 16 failures, all expected (section 7) |
| microsd_rejected_closed_path | 0 | closed-panel path REJECTED as before (23 hit samples, max 42.414 mm3); panel-off 4 pass / 2 info | |
| check_scope | 1 | 31 pass / 3 fail / 14 info, byte-identical to the committed record | VN-34, VN-37, VN-38 |
| void | 1 | refused: `Source binding mismatch: candidate-vertical/model.py`; nothing written | as power_rigid |

`verify_shadow_plenum.py` and `verify_shadow_outlet_context.py` also refuse (`Source-stale export: model.py`) and write nothing. Every verifier now runs natively on Windows: no KeyError, no decode error (the reproduction saw KeyErrors in 7 of them).

Main-audit categories now: assembly_state 3 pass; driver 9 pass / 2 fail; service_driver 9 / 2; driver_coverage 1; inserts 4; integrity 46; interference 108 pass / 1 fail / 9 info; j7_float 50; lens_clamp 4 pass / 2 info / 4 fail; lens_support 41 / 5 info; motion 16; motion_coverage 10 / 6 info; nominal_features 7 info; non_material_keepout 1 info; physical 1 info; roll_catch 58 / 1 info; roundtrip 45; source_binding 64 / 7 fail; step_aperture_probes 1; step_material_probes 12. The 32 info rows are exactly `evidence_rules.expected_main_info()` (18 accepted rows + 6 open motions + 8 FP-08 rows).

Records the batch refreshed in the clone: verification.json, print-checks.json, print-mesh-checks.json, csi-source-tool-checks.json, hdmi-solid-checks.json, wire-solid-checks.json, microsd-service-dependency.json, plus the new review-check-run.json. harness-checks.json and check-scope-checks.json came out byte-identical. Before-images of all of them are in `vnfix/snap/phase1-closeout/`.

## 5. Status of every register entry

Status words: **closed** (closed in phase 1, with the proof named); **check fails by design** (the check is ported and fails on the current geometry; the CAD fix or re-export comes in phase 2; never weaken it); **phase 2** (not done yet); **user** (needs a user decision from the register list, number in brackets); **hardware** (needs received parts or a bench test). An entry with two parts names both; the first word is the one counted in section 6.

### A. Repository and reproducibility

| ID | Status | Phase-1 lane | Proof now | What is left |
|---|---|---|---|---|
| VN-01 | closed | FP-01 | test_repo_eol 7/7: `check-attr text` unset on every file, 0 untracked CR outside the 73-entry frozen allowlist, emulated autocrlf checkout of the next-commit tree changes 0 files (9ced753 attributes: 717), r7 final-release audit passes on that emulated clone | none |
| VN-02 | closed | FP-02 | test_cross_platform_io 12/12 (0 backslashes in any key of 150 JSON files, planted Windows manifest caught); every batch verifier ran natively on Windows in this closeout with no KeyError (section 4) | none |
| VN-03 | closed | FP-02 | cv_io + AST lint of 114 live scripts (test_cross_platform_io); test_windows_smoke 3/3 (cp1252 and UTF-8 mode give identical results). run_locked.py was not edited (r7 hash-bound source); the guard is child_env in the batch runners | none |
| VN-04 | check fails by design + user [2] | FP-03 (default: deterministic export, caches not committed) | test_deterministic_export 20/20; `export_cache.py status` exit 1: all three variants and the guide `cache_missing_unregenerable` (53e668d4 predates FP-03); batch row `bound_files` fails | FP-16 re-export makes the caches rebuildable; then a fresh clone must give `export_cache.py status` exit 0 after `regenerate`. Commit-or-split stays user decision 2 |
| VN-05 | closed | FP-04 | test_evidence_tooling 15/15 (tampered source exits 1, guide nomination compared, default and `--check` write nothing) | none |
| VN-06 | closed | FP-04 | structural `--check` exit 0; tolerance fixture (1e-13 passes, 1e-3 fails) | none |
| VN-07 | phase 2 | (this closeout ran the current runner once) | `out/compact-kowa_lm6hc/review-check-run.json` now exists for runner 15238fc4 on manifest 53e668d4 with the known source drift; its logs are git-ignored (`*.log`) and not hashed | FP-16: run on the re-exported manifest, record log SHA-256 and repo-relative paths, commit the record |
| VN-08 | closed | FP-04 + fixup-1 | test_evidence_numbers 8/8 (generated figures equal their source rows; gate count from the r7 receipt: 58 / 56 open / 2 withdrawn) | none |
| VN-09 | closed | FP-04 | stale reports moved to history/stale-selected-reports-2026-10-10 with INDEX.json; planted foreign-manifest report fails the reconciler (test_evidence_tooling) | none |
| VN-10 | phase 2 | none | unchanged: the selected usb_head report still records the author's `/workspace/` path. This closeout's batch rewrote it with this machine's absolute Windows path (verify_shadow_usb_head.py:88 `manifest_path=str(mp)`); test_cross_platform_io caught it and the committed report was restored | FP-15/FP-16: writers record repo-relative POSIX paths; regenerate and rebind, never hand-edit |
| VN-11 | phase 2 | none | not started | FP-15: commit the Pi extractor and audit scripts or label the JSONs non-reproducible |
| VN-12 | phase 2 | FP-06 added STALE banners to the guide READMEs only | not started (no pypdf/scipy lock, no Blender version, rasterizer still Linux-only) | FP-15 toolchain lock and Windows commands; FP-16 guide rebuild needs the rasterizer |
| VN-13 | closed + user [3] | FP-01 + fixup-1 | test_third_party_notices 9/9 (THIRD-PARTY-NOTICES.md, LICENSE-RaspberryPi.txt beside every Pi-derived STEP; export_candidate.py now writes the copies) | project-content licence is user decision 3 |
| VN-14 | phase 2 | none | not started | FP-15 entry documents |
| VN-15 | phase 2 | none | not started | FP-15 repo-wide link check and banners |
| VN-16 | user [2] | none | unchanged | user decision 2 (dedupe Pi STEP, Release assets or LFS) |
| VN-17 | closed | FP-03 + fixup-1 | test_deterministic_export 20/20 (fixed header time, canonical colour section, receipt-bound STEP writers normalised, RAW_STEP_WRITERS allowlist) | FP-16 proves it on a full re-export |
| VN-18 | phase 2 | none | not started | FP-15 (shorten names or document core.longpaths) |
| VN-19 | phase 2 | none | not started | FP-15 (studies/ folder, stray tmp PNGs) |
| VN-20 | phase 2 | none | not started | FP-15 structural generator |

### B. Check coverage and check scope

| ID | Status | Phase-1 lane | Proof now | What is left |
|---|---|---|---|---|
| VN-21 | phase 2 | FP-05/07/08/09/10/12 ported the categories | main audit now 20 categories and 529 rows (481 pass / 16 fail / 32 info) (was 10 categories); print, harness and check-scope batch reports added | FP-15 per-category coverage table in REVIEW/CHECKPOINT; nominal_features still analytical; critical_features probes need re-nomination on the moved geometry |
| VN-22 | closed | FP-05 + fixup-1 | test_assembly_state 11/11, test_refit_state 15/15; motions re-run from steps.py (batch main audit: motion 16/16 pass, motion_coverage 10 pass + 6 open info, assembly_state 3/3) | none |
| VN-23 | check fails by design | FP-07 | driver 9 pass / 2 fail, service_driver 9 / 2, driver_coverage pass: the 6.5 mm bit enters the 6.4 mm carrier counterbores (p_carrier1 2.432 mm3, p_carrier2 0.405 mm3) at build and at service | FP-11c (counterbores 7.0 mm); FP-13 Fujinon and original-storage runs |
| VN-24 | check fails by design | FP-08 | j7_float 50/50, roll_catch 58 pass + 1 info, lens_support 41 + 5 info, inserts 4/4; lens_clamp 4 pass / 2 info / 4 fail (washer_flat_support 0.33 mm2 unsupported and washer_free_seat at dy +0.2, Kowa and Fujinon) | FP-11d (washer clearance and flat support); FP-13 variant runs |
| VN-25 | check fails by design | FP-09 | print_overhang 6 pass / 4 fail (tub, carrier, base_grip, lens_collar), print_bridge_direction 6 / 4, thin_wall 9 / 0, critical_features 49 / 56 / 37 | FP-11a/b/c/d/e; re-nominate critical features |
| VN-26 | check fails by design | FP-10 + fixup-1 | harness 20 pass / 15 fail / 20 info (re-run byte-identical): cable_routes 7, cable_stow 2, mate_reach 3, lead_access 3 fail | route/CAD work (run-lead route inside the tub, pigtail length, usb_5v and pack_lead installed routes); free-lead routes for mate_reach |
| VN-27 | phase 2 | none | not run | FP-13 |
| VN-28 | check fails by design | FP-10 | cable_routes/qt fails (fan-in gap 8.55 mm > 1.0); mate_reach qt_enc and j2_btn fail (free lead, no obstacle-checked route); orphan signal_routes_review.json archived; MTC rows for QT and RCY added | route work in phase 2; QT measurement row stays |
| VN-29 | closed + user [7] | FP-12 | dog-leg microsd_out motion passes (30 samples at 2 mm, 0 hits); the straight +X path fails as FP-05 recorded (72.794 mm3 against the collar); closed-panel path stays REJECTED | front slit is user decision 7; tool reach stays a hold |
| VN-30 | closed | FP-12 + fixup-1 | wire and HDMI obstacle sets now every material row, exclusions listed; terminal-run rule tested (test_wire_terminal_rules 5/5) ; batch: wire-solid pass against 44 obstacles, HDMI 13 pass / 0 fail (was 6) | none |
| VN-31 | closed | FP-04 | keepout info limited to the named partner; reconciler asserts the exact info set | none |
| VN-32 | closed | FP-04 | mesh rows carry expected/actual hash fields | none |
| VN-33 | closed | FP-12 | j4_screen per variant: equal share 0.931 (compact Kowa), 0.976 (original Kowa), 0.764 (Fujinon) N m against the restated 1.00 N m screen; refusal fixture (test_check_scope 21/21) | J4 physical test stays with the inherited gates |
| VN-34 | check fails by design | FP-12 | evf_restraint 7 of 8 rows equal r7; -Z fails (receptacle zone meets the tub at 0.27 mm); evf_face 12/12 pass | phase 2 CAD (not in FP-11a-f; see section 8) |
| VN-35 | closed + hardware | FP-12 | hdmi_face strip normal continuous and ends on both exits: pass | contact-side rows stay HOLD until the HDMI heads are measured (MTC HDMI row) |
| VN-36 | user [8] + hardware | FP-12 + fixup-1 | flow_network report (CSI = 48.2 % of intake; CSI plugged: system 0.815) and baseline_drift row | CSI plug is user decision 8; operating point needs the fan curve |
| VN-37 | check fails by design | FP-12 | area_parity/hot_branch_series 509.4 < 510 mm2 (fails by 0.6 mm2) | phase 2 CAD with FP-11a (plenum section or mouth) |
| VN-38 | check fails by design | FP-12 | stack_retention fails (two diagonal screws, no hull, CoM 6.11 mm off the diagonal); post_root_bending passes (2.01 / 2.81 MPa <= 5 MPa) | phase 2 CAD: third printed locating feature, no new screw (not in FP-11a-f) |


### C. Assembly procedure and service

| ID | Status | Phase-1 lane | Proof now | What is left |
|---|---|---|---|---|
| VN-39 | closed | FP-05/06 | collar + gauge before the camera in steps.py and ASSEMBLY; lint: gauge never present with camera or adapter over 290 states (seated overlap 927.752 mm3 recorded as a tool exclusion) | FP-16 guide PDF/page rebuild (guide marked STALE; needs the rasterizer, VN-12) |
| VN-40 | closed | FP-06 + fixup-1 | B3 without FPS hardware; step 6 panel_in, panel_screws, fps_washer_on, fps_nut_on, knob_fps_on; refit lint (test_build_order_docs 23/23, test_refit_state 15/15) | none |
| VN-41 | closed | FP-06 | lens + s_c4 in step 2 before the carrier; r7 lens_turn_back_lint (byte-identical source) passes on ASSEMBLY step 2 and fails on 9ced753 | none |
| VN-42 | user [5] (docs part closed) | FP-06 | service matrix with both lens-change rows (same collar: closed body; other collar: 35 ids, 9 screws, 7 cables, 22 refit ops); options A/B documented | user decision 5 |
| VN-43 | phase 2 (docs part closed) | FP-06 | EVF HDMI and RCY matings moved to step 5 | the carried sweep in verify_hdmi.py still lowers the head 6 mm (0 mm margin over the 6.0 mm stroke): re-run at stroke + 3 mm and add the unplug finger/pliers corridor |
| VN-44 | closed | FP-05/06 | B0 bench camera-end FPC pre-mate | none |
| VN-45 | closed + user [11] | FP-06 | grip row = Pi module out first (default) | inline run-lead junction is user decision 11 |
| VN-46 | closed | FP-06 | deep socket on the axis for both nuts; BOM tool lines; test: no "spanner" in tool text | socket size for V-62 needs the measured 1505 nut (G-V-POWER) |
| VN-47 | check fails by design + user [6] + hardware | FP-10 | lead_access/pigtail_ties_on_route (nearest slot 31.76 mm), pigtail_xt30_mouth and mate_reach/xt30_pack (face out not reached, < 15.0 mm) fail; RTV-only alternative computed | FP-15: record the no-tie departure in REVIEW; ties vs RTV is user decision 6; flexible reach and finger force are bench gates |
| VN-48 | hardware + user [12] | none | unchanged | coordinated-hand trial; transport clip or helper is user decision 12 |
| VN-49 | hardware | none | unchanged | measure the 4448 overmold and exit |
| VN-50 | phase 2 | FP-04 generates the gate count from the r7 receipt | count no longer literal | FP-15 gate and BX mapping table (retired / carried / re-scoped / replaced) |

### D. Print and CAD geometry

| ID | Status | Phase-1 lane | Proof now | What is left |
|---|---|---|---|---|
| VN-51 | check fails by design | FP-09 | plenum-roof regions fail the single-direction rule (largest 1162.2 mm2 at print z 7.6; cold bay worst run 43.8 mm, hot bay 47.0 mm) | FP-11a |
| VN-52 | check fails by design | FP-09 | mouth regions 665.9 + 417.9 mm2 unsupported (print z 7.6) | FP-11a (45 degree lintels, all four mouths in the hold text, coupon) |
| VN-53 | check fails by design | FP-09 | tab-catch regions 48.0 / 16.3 / 15.0 mm2 | FP-11b |
| VN-54 | check fails by design | FP-09 | carrier 1963.09 mm2 unsupported at print z 2.0 (frame floats); single-direction 2041.7 mm2 | FP-11c |
| VN-55 | check fails by design | FP-08 | washer_flat_support (0.33 mm2 unsupported) and washer_free_seat (0.1564 mm3 at dy +0.2) fail for Kowa and Fujinon; r7 mechanical test: 2 expected failures | FP-11d |
| VN-56 | check fails by design | FP-07 | driver and service_driver p_carrier1 2.432 mm3, p_carrier2 0.405 mm3 (6.5 mm bit, 6.4 mm bore) | FP-11c |
| VN-57 | check fails by design | FP-09 | base_grip 102.94 mm2 unsupported at print z 5.4 (single-direction 266.0 mm2) | FP-11e |
| VN-58 | check fails by design | FP-09 | lens_collar 11.0 mm2 unsupported at print z 8.2 | FP-11d |
| VN-59 | phase 2 | none | no bed-edge chamfer check exists yet | FP-11a: add the 0.6 mm chamfer and a per-part bed-edge chamfer check |
| VN-60 | phase 2 | none | not started | FP-11f |

### E. Electrical and BOM

| ID | Status | Phase-1 lane | Proof now | What is left |
|---|---|---|---|---|
| VN-61 | phase 2 | none | not started (ASSEMBLY still points to r7 WIRING) | FP-14 |
| VN-62 | check fails by design + user [4] | FP-10 | lead_access/pigtail_drop: drop_hi 0.1625 V > 0.150 V at 8.6 A (hot fuse x1.30, vendor minimum strands, lay 1.03) | user decision 4 (G-W5 branch); never relax 0.150 V |
| VN-63 | phase 2 + user [13] | none | not started | FP-14 BOM row; connector family is user decision 13 |
| VN-64 | phase 2 | none | not started | FP-14 |
| VN-65 | user [9] | none | unchanged | user decision 9 |
| VN-66 | hardware | none | unchanged | measure the EVF pads |

### F. Thermal

| ID | Status | Phase-1 lane | Proof now | What is left |
|---|---|---|---|---|
| VN-67 | hardware | none | unchanged | MTC row and thermocouple |
| VN-68 | hardware | none | unchanged | powered thermal test |

### G. Documented holds

| ID | Status | Proof now | What is left |
|---|---|---|---|
| VN-69 | hardware | main audit still fails interference pi5/cooler 79.902671 mm3 (unchanged) | measure cooler registration; never reclassify |
| VN-70 | hardware | unchanged (FP-11a/b first) | slicer and coupons |
| VN-71 | hardware | unchanged (VN-36 model is the pre-check) | closed-body thermal test |
| VN-72 | hardware | pigtail rows fail by design (VN-47, VN-62) | routing mock-up |
| VN-73 | hardware | unchanged | measure the 1505 and J2 |
| VN-74 | hardware | unchanged | measure FPC ends and cable |
| VN-75 | hardware | unchanged | qualify the HDMI assembly |
| VN-76 | hardware | unchanged | SSD on a Pi 5 |
| VN-77 | hardware | stack_retention now fails by design (VN-38) | real standoffs and screws |
| VN-78 | hardware | unchanged | strap trial |
| VN-79 | hardware | unchanged | CK1044 and donor parts |
| VN-80 | user [10] | unchanged | option C |
| VN-81 | hardware | unchanged | power envelope |
| VN-82 | hardware | 58 inherited gates (56 open, 2 withdrawn) counted from the r7 receipt | M1 and the gates |
| VN-83 | user [14] | unchanged | balance rule |
| VN-84 | user [14] | unchanged | press-in caps |

## 6. Counts

| Status (first word) | Count | IDs |
|---|---|---|
| closed in phase 1 | 22 | VN-01, 02, 03, 05, 06, 08, 09, 13, 17, 22, 29, 30, 31, 32, 33, 35, 39, 40, 41, 44, 45, 46 |
| check ported, fails by design | 19 | VN-04, 23, 24, 25, 26, 28, 34, 37, 38, 47, 51, 52, 53, 54, 55, 56, 57, 58, 62 |
| open for phase 2 | 18 | VN-07, 10, 11, 12, 14, 15, 18, 19, 20, 21, 27, 43, 50, 59, 60, 61, 63, 64 |
| user decision | 7 | VN-16, 36, 42, 65, 80, 83, 84 |
| hardware | 18 | VN-48, 49, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 81, 82 |
| total | 84 | |

Second parts: user decisions also sit on VN-04 [2], 13 [3], 29 [7], 45 [11], 47 [6], 48 [12], 62 [4], 63 [13]; hardware also on VN-35, 36, 47; phase-2 work also on VN-39 (guide rebuild), 47 (REVIEW text) and the FP-13 variant runs behind VN-23 and VN-24.

## 7. Expected failures now (by design; never accept, never weaken)

Every row below fails on the current geometry or evidence state and must keep failing until its fix lands. The reconciler and docs audit fail on them as designed (`EXPECTED_PRINT_FAILURES` and `EXPECTED_HARNESS_FAILURES` stay empty).

| Where | Row | Number now | Clears with |
|---|---|---|---|
| main audit | interference pi5/cooler | 79.902671 mm3 | hardware (VN-69) |
| main audit | source_binding x7 (export_candidate, make_corrected_pi, model, official_pi5_assembly, official_pi5_csi, official_pi5_geometry, power_geometry) | sources edited in phase 1 (I/O, wording) | FP-16 re-export |
| main audit | driver + service_driver p_carrier1, p_carrier2 | bit in bore 2.432 / 0.405 mm3 | FP-11c |
| main audit | lens_clamp washer_flat_support kowa_lm6hc, fujinon_hf6xa | 0.33 mm2 (0.0165 mm3) unsupported, footprint r 3.9 | FP-11d |
| main audit | lens_clamp washer_free_seat kowa_lm6hc, fujinon_hf6xa | overlap at dy +0.2 (relief margin 0.0) | FP-11d |
| print | print_overhang + print_bridge_direction: tub | 10 regions: 665.92 + 417.86 mm2 (mouths), 48.04 / 16.34 / 14.96 (tab catch), 13.66 / 7.81 (EVF support), 7.98 (rear panel-screw landing), 2.82, 1.72 (LL insert boss); single-direction largest 1162.2 mm2 at z 7.6 | FP-11a, FP-11b, 8.2 |
| print | same: carrier | 1963.09 mm2 at z 2.0; 2041.7 mm2 | FP-11c |
| print | same: base_grip | 102.94 mm2 at z 5.4; 266.0 mm2 | FP-11e |
| print | same: lens_collar | 11.0 mm2 at z 8.2 | FP-11d |
| print | critical_features | 49 pass / 56 fail / 37 info | re-nomination (8.2) |
| harness | cable_routes qt, run_pin37, run_pin39, pigtail_positive, pigtail_negative, usb_5v, pack_lead | fan-in 8.55 mm; tub 64.87 / 38.71 mm3; 251.8 / 250.9 + 27.0 > 270 mm; no installed route x2 | 8.2 |
| harness | cable_stow run_pin37, run_pin39 | tub 58.90 / 37.27 mm3 | 8.2 |
| harness | mate_reach qt_enc, j2_btn, xt30_pack | free lead with no checked route x2; XT30 face out not reached (< 15.0 mm) | 8.2 |
| harness | lead_access pigtail_ties_on_route, pigtail_xt30_mouth, pigtail_drop | nearest slot 31.76 mm; face out < 15.0 mm; 0.1625 V > 0.150 V | 8.2, user decisions 4 and 6 |
| check_scope | area_parity/hot_branch_series | 509.4 < 510 mm2 | FP-11a (8.2) |
| check_scope | evf_restraint/-Z | receptacle zone meets the tub at 0.27 mm | 8.2 |
| check_scope | stack_retention/vertical_carrier | no hull; CoM 6.11 mm off the screw diagonal | 8.2 |
| batch | bound_files, power_rigid, fps, void, plenum, outlet | missing caches or refused on changed sources | FP-16 |
| tests | test_collar_r7_mechanical: 3 expected failures | washer x2, r7 prepare_print on the Fujinon collar | FP-11d |
| candidate test | test_routes_source.py 2 of 10 | float last digit; p_usb_pi box -152.78 vs -153 | FP-15 (inherited from 9ced753) |


## 8. What phase 2 must do

Order: CAD fixes first (each one turns its by-design failure into a pass without touching the check), then the variant audits, wiring and BOM, docs, and one final refresh. All CAD work goes through `run_locked.py`, one job at a time. Never edit a check, a fixture, an accepted-set constant (`evidence_rules.MAIN_AUDIT_INFO`, `EXPECTED_PRINT_FAILURES`, the harness failing set in tests) or a baseline to make a row pass; a changed baseline needs a written reason and a geometry change behind it.

### 8.1 CAD fixes FP-11a to FP-11f

| Step | Closes | Must turn these rows to pass | Also re-run |
|---|---|---|---|
| FP-11a plenum roof, mouths, skin | VN-51, VN-52, VN-59 (and VN-37, see 8.2) | print_overhang tub: the plenum-roof and four mouth regions (665.9 + 417.9 mm2 today) under the per-region single-direction 30 mm rule; new per-part bed-edge chamfer check (does not exist yet; write it first and watch it fail on the current skin) | plenum and mouth verifiers, area_parity, flow_network (baseline rewrite with a reason), coupon extended to the rear mouth, hold text in README/REVIEW/CHECKPOINT names all four mouths |
| FP-11b tab catch | VN-53 | print_overhang tub catch regions (48.0 / 16.3 / 15.0 mm2) | roll_catch (58 pass today must stay pass), j7_float |
| FP-11c carrier | VN-54, VN-56 | print_overhang carrier; driver/p_carrier1 and p_carrier2 plus their service_driver rows (bit enters the 6.4 mm bores); a new bed-contact-area row | boss wall from the STEP, stack_retention, motions |
| FP-11d collar | VN-55, VN-58 | lens_clamp washer_flat_support and washer_free_seat (Kowa and Fujinon); print_overhang lens_collar; test_collar_r7_mechanical: the 2 washer expected failures must become passes (remove their expected-failure marks only when they pass) | j7_float, roll_catch, collar_gauge, inserts |
| FP-11e grip pocket | VN-57 | print_overhang base_grip (passage roof) | J4 slide clearance row, j4_screen |
| FP-11f EVF feed volumes | VN-60 | new interference rows for the diode sleeve, RCY pair and option-C reserve on the usb_5v route; grep test for stale ko_5v_up / PH text | harness cable_routes/usb_5v (needs an installed route) |

### 8.2 Ported checks that fail and have no FP-11 step yet

These came out of the phase-1 ports. Phase 2 must schedule them (CAD or route work), or the user must decide; they must not be accepted as info.

| Row(s) | Register | Needed |
|---|---|---|
| check_scope area_parity/hot_branch_series (509.4 < 510 mm2) | VN-37 | widen the z 8.0 post-row section or the front mouth; natural to do inside FP-11a |
| check_scope evf_restraint/-Z (receptacle zone meets the tub at 0.27 mm; r7 passed with the PCB alone) | VN-34 | a CAD change so the PCB, not the receptacle, takes the -Z stop (for example a local tub relief); the check stays as ported |
| check_scope stack_retention/vertical_carrier (no hull, CoM 6.11 mm off the screw diagonal) | VN-38 | third printed locating feature (tongue or slot), no new screw |
| harness cable_routes and cable_stow run_pin37 / run_pin39 (lead capsules inside the tub; the route itself is in tub material, 35.88 / 25.34 mm3) | VN-26 | re-route the run lead (floor lay above the floor face, riser out of the wall) or cut a lane |
| harness cable_routes/qt (fan-in gap 8.55 mm > 1.0) | VN-28 | model the QT fan-in |
| harness cable_routes/pigtail_positive and _negative (251.8 / 250.9 + 27.0 > 270 mm stock) | VN-47, VN-72 | shorter path or stock length; tied to user decision 4 |
| harness cable_routes/usb_5v and pack_lead (no installed route) | VN-26, VN-60 | installed full-core routes |
| harness mate_reach qt_enc, j2_btn, xt30_pack; lead_access pigtail_ties_on_route, pigtail_xt30_mouth | VN-26, VN-28, VN-47 | obstacle-checked free-lead routes; tie slots on the route or RTV-only (user decision 6) |
| harness lead_access/pigtail_drop (0.1625 V > 0.150 V) | VN-62 | user decision 4; never relax 0.150 V |
| print critical_features: 56 fail: 44 r7 probes on moved geometry (tub 21, panel 16, base_grip 4, lens_collar 3); 10 joint rows (J1/J2/J9 cover removed parts, J3/J7/J8/J12/J13 stale probes, J4 s_b1/s_b2 head floors); the carrier has no structural entry; one base_grip thin spot 0.373 mm (feather edge) | VN-21, VN-25 | re-nominate the r7 probes on the moved geometry (tub, panel, base_grip, lens_collar) and add the candidate's own joints; never invent origins |
| HDMI carried sweep at 6 mm (0 mm margin) | VN-43 | lower the head stroke + 3 mm and re-run; add the unplug corridor |
| print_overhang tub: EVF support 13.66 / 7.81 mm2, rear panel-screw landing 7.98 mm2, 2.82 mm2 at x -55, LL insert boss 1.72 mm2 | VN-25 | no FP-11 step names them: fix in FP-11a/b or declare a support zone with its reason, as r7 did |

### 8.3 FP-13 variant audits (VN-27)

Run for compact-fujinon_hf6xa and original-kowa_lm6hc after the CAD fixes: `verify_candidate.py --variant ...` (full main audit: interference, motion, assembly_state, driver, j7), `verify_print_checks.py --variant ...`, and the harness and check-scope verifiers where their variant guards allow it (today they refuse other variants by design). The reconciler must require a verification.json for every variant. VN-23 and VN-24 close only when every variant passes.

### 8.4 FP-14 wiring and BOM (VN-61, VN-63, VN-64)

Generated WIRING-VERTICAL.md from steps.py, harness_rules and the route sources; a distinct J2 connector (family is user decision 13); consolidated buy view with spares and a black-wire SKU; tests that the wiring, BOM and routes agree and that no two junctions share an unkeyed mateable pair. Set V-62's purchase quantity only after the 1505 nut is measured.

### 8.5 FP-15 hygiene and docs

VN-10 (repo-relative paths in writers; verify_shadow_usb_head.py:88 writes `manifest_path=str(mp)`, an absolute path; fix the writer, then regenerate in FP-16), VN-11, VN-12 (pypdf/scipy lock, Blender version, Windows commands, rasterizer fallback), VN-14, VN-15, VN-18, VN-19, VN-20, VN-21 per-category coverage table generated from verification.json, VN-47 docs (record the departure from r7's no-tie rule in REVIEW), VN-50 gate and BX mapping table.

### 8.6 FP-16 final refresh

In order, through `run_locked.py`: `make_corrected_pi.py`; `export_candidate.py` for all three variants; `export_cache.py regenerate` then `status` exit 0; plenum and outlet verifiers; `run_shadow_checks.py` (it runs the main audit); `export_shadow_alternatives.py`; BOM and structural refresh then `--check`; `reconcile_review_evidence.py --write` (only possible with 0 failures); `review_docs_audit.py --write`; guide rebuild on a machine with the rasterizer, visual review of every page, then `package_concealed_guide.py`; commit the run record with log hashes. Then repeat the inspect commands on a fresh clone and on an emulated `core.autocrlf=true` clone: all must exit 0. The source_binding failures listed in section 7 disappear only through this re-export, never by pasting hashes.


## 9. Found during phase 1 and this closeout (not in the register)

| Finding | Where it stands |
|---|---|
| OCCT's XCAF writer orders the assembly-STEP colour section by memory address, so two identical exports differed in 1358 lines | fixed in FP-03 (content-keyed canonicaliser, tested) |
| The grip-route refit re-threaded the strap with the tub on (the strap pass lies in the recess the seated tub closes) | fixed in fixup-1 (steps.TRAVELS_WITH, lint) |
| The run-lead route itself runs inside tub material (run_pin37 35.88 mm3, run_pin39 25.34 mm3 with a 1.8 mm capsule), not only its bound family members | open, phase 2 route/CAD work (section 8.2) |
| After r7 `prepare_print` has run on an in-memory Fujinon collar, `model.collar_print_stock` rejects that same shape ("Invalid collar print union"); a fresh shape passes | open (tests copy the collars); look at it with FP-11d |
| An eyepiece drop-in from +Y collides with the tub rear wall (worst 337.942 mm3); the r7 +X push clears, and steps.py now declares it | closed in FP-05 (this was a session assumption, not a candidate claim) |
| `cad/gs8-d2-v1/run_locked.py` is an r7 hash-bound source, so it cannot set PYTHONUTF8 without breaking the r7 audit | worked around: `cv_io.child_env` in the batch runners; the I/O code no longer needs the flag (test_windows_smoke) |
| The candidate's own `test_routes_source.py` fails 2 of 10 tests, identically on the unchanged 9ced753 snapshot (FP-02 note) | re-run in this closeout: same 2 failures. Phase 2 (FP-15) must find out whether the test or the geometry is right; do not loosen the test to pass |
| verify_shadow_usb_head.py:88 records `manifest_path=str(mp)`, so a run on this machine wrote the local absolute Windows path (with the user name) into a tracked report | this closeout: caught by test_cross_platform_io, committed report restored; fix in FP-15 (VN-10) |
| print critical_features: a 0.373 mm feather edge on the -Y side of the narrowed base_grip at (-112.87, -24.96, -6.38) (FP-09 note) | open, CAD phase |
| test_evidence_tooling.test_exact_info_set compared the committed main audit with the static 18-row set, which held only for the 9ced753 audit | this closeout: the test now uses `evidence_rules.expected_main_info()`, the set the reconciler gates on; extra and missing rows still fail |
| BOM-VERTICAL.md quotes whether the main audit is bound to the current verifier, so every main-audit refresh makes `make_bom_vertical.py --check` stale | expected; regenerate after each refresh (done here) |
