# Final status: review 2026-10-10 of the vertical-Pi D2 candidate

This page closes the review of AubergineShallow/digital8mm-vertical-nizo at 9ced753 (on top of r7 d38468e).
The fixes are on the local branch `review/vn-fixes-20261010`: phase 1 = 44f8131, phase 2 + fix-up = 4f9e029 (HEAD).
This is a **review branch**. It is not `main`, not a release, and nothing in it has been printed, powered or measured.
Only the snapshot branch `review/vn-fixes-intermediate-20261011` (4d160f7, marked INTERMEDIATE) has been pushed; `origin/main` is still 9ced753.

Written 2026-10-12 from the committed reports at 4f9e029. Numbers come from the JSON reports named in each row. The reconciler and the docs audit were re-run read-only (`--check`) on 2026-10-12 to confirm their results. The full test suite was re-run the same night on a fresh clone (section 3.5).

Records: [ISSUE-REGISTER.md](ISSUE-REGISTER.md) (VN-01..VN-84, user decisions 1-17), [PHASE1-STATUS.md](PHASE1-STATUS.md), [FIX-LOG.md](FIX-LOG.md) (every lane; later lines win), [fx/FX-RUN-RECORD.json](fx/FX-RUN-RECORD.json) (fix-up run, log hashes), candidate [REVIEW.md](../REVIEW.md), [CHECKPOINT-STATUS.json](../CHECKPOINT-STATUS.json), [README.md](../README.md).

## 1. Headline

**What the review found.** 84 issues: 0 blockers, 30 major, 47 minor, 7 info. 63 were latent (the candidate did not document them) and 21 were existing holds. 5 more findings were refuted. The candidate's computed numbers were honest and reproduced. The real problems were latent:
1. Reproducibility on Windows was broken (line endings, path separators, locale encoding, git-ignored mesh caches).
2. Most r7 rule checks were never ported (straight driver, J7-R float, roll catch, lens clamp, print rules, harness).
3. The written build order was wrong in places (camera before the collar gauge, lens fitted after the panel closed, FPS switch sequence contradicting itself).
4. Several printed parts failed r7's own print rules (plenum roof and mouths, tab-catch tines, carrier frame, grip pocket, collar foot).

**What was fixed.** 48 of the 84 entries are closed in the repository, each with a check, test or generated document as proof (table in section 2). The Windows problems are fixed and tested. The missing r7 categories are ported: the main audit now has 21 categories and 666 rows (it had 10 categories and 311 rows). Every printed part of all three variants passes every print check. The build order is now a data model (`steps.py`) that the docs, the motions and the guide builders follow. The wiring specification is generated. The Fujinon and original-storage variants now have their own exports and audits.

**What remains.** 36 entries are still open:
- **7 checks are ported and still fail.** They are VN-24, VN-26, VN-27, VN-28, VN-37, VN-47 and VN-62. Section 2 gives the exact rows.
- **2 entries still have repository work left.** VN-04: the guide's bound pages cannot be re-verified until the guide is rebuilt. VN-21: 9 r7 check categories are still not ported.
- **9 entries need a user decision.**
- **18 entries need hardware or a bench test.**

The main audit fails 14 rows in each variant. One is the inherited pi5/cooler overlap, 79.902671 mm3 (hardware). The other 13 are the roll-catch window rows for the bonded tab-catch stub when it sits tilted (worst gap 0.055 mm, rule 0.10 mm). The reconciler fails 10 gates and the docs audit fails 11. Section 3.4 explains each one. None of them is a weakened check.

### Counts

| Final status (first word) | Count | IDs |
|---|---|---|
| closed | 48 | VN-01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23, 25, 29, 30, 31, 32, 33, 34, 35, 38, 39, 40, 41, 43, 44, 45, 46, 50, 51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 64 |
| check ported, still failing | 7 | VN-24, 26, 27, 28, 37, 47, 62 |
| open, repository work left | 2 | VN-04 (guide part), VN-21 (9 r7 categories) |
| user decision | 9 | VN-16, 36, 42, 53, 63, 65, 80, 83, 84 |
| hardware gate | 18 | VN-48, 49, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 81, 82 |
| **total** | **84** | |

Some entries have a second status as well. User decisions also sit on VN-04 [2], 13 [3], 29 [7], 37 [17], 45 [11], 47 [6], 48 [12], 53 [16], 60 [10] and 62 [4]. Hardware gates also sit on VN-35, 36, 47 and 57 (grip slide).

At the phase-1 closeout the split was 22 closed, 19 failing by design, 18 left for phase 2, 7 user decisions and 18 hardware gates. Since then 26 more entries have closed: 11 of the 19 failing checks now pass, and 15 of the 18 phase-2 entries are done. A few entries moved category:
- VN-53: its print rows pass, so it now waits only on user decision 16.
- VN-63: its BOM part is done, so it now waits only on user decision 13.
- VN-04: it moved to "repository work left" (the guide).
- VN-27: its variant audits now exist and fail on the same rows as the compact variant.

## 2. Every register entry

How each status was decided: [PHASE1-STATUS.md](PHASE1-STATUS.md) section 5 is the starting point. [FIX-LOG.md](FIX-LOG.md) overrides it, and later lines win. The committed reports at 4f9e029 are checked last.

Unless a row says otherwise, the reports are `../out/<variant>/*.json`:
- compact-kowa_lm6hc: manifest dbea5ca5
- compact-fujinon_hf6xa: manifest 1ef16c87
- original-kowa_lm6hc: manifest 13d4c85a

Test counts are from the 2026-10-12 re-run (section 3.5).

### A. Repository and reproducibility

| ID | Sev | Final status | Proof, or the exact failing rows | Left |
|---|---|---|---|---|
| VN-01 | major | closed | test_repo_eol 7/7: `check-attr text` is unset on every file; an emulated autocrlf checkout changes 0 files (the 9ced753 attributes changed 717); the r7 final-release audit passes on that clone | none |
| VN-02 | major | closed | test_cross_platform_io 12/12: 0 backslashes in any key of the JSON evidence; a planted Windows manifest is caught | none |
| VN-03 | major | closed | `cv_io` plus an AST I/O lint of every live script (test_cross_platform_io); test_windows_smoke 3/3 gives identical results under cp1252 and UTF-8 | none |
| VN-04 | major | open, repository work left (+ user 2) | Variants: `export_cache.py status --no-guide` exits 0 after `regenerate`. This was shown in FX step 54 and again on a fresh clone on 2026-10-12 (exit 3 before the rebuild, 0 after; section 3.5). The batch row `bound_files` exits 0 ([review-check-run.json](../out/compact-kowa_lm6hc/review-check-run.json)). Covered by test_deterministic_export | The guide receipt still binds the 53e668d4 pages and meshes: docs audit `bound_files guide mismatch`. Clears when the guide is rebuilt. Committing or splitting the caches is decision 2 (default used: not committed, rebuildable) |
| VN-05 | minor | closed | review_docs_audit exits 0, 3 or 1; `--check` and the default run write nothing (test_evidence_tooling) | none |
| VN-06 | minor | closed | structural `--check` exits 0 (FX X4b); the tolerance fixtures are in test_evidence_numbers 8/8 | none |
| VN-07 | minor | closed | committed run record `review-check-run.json` (runner 15238fc4, manifest dbea5ca5, 15 rows with log SHA-256, sha 2a673ba6 = the value in FX-RUN-RECORD) and [fx/FX-RUN-RECORD.json](fx/FX-RUN-RECORD.json) | none |
| VN-08 | minor | closed | test_evidence_numbers 8/8: the generators hold no typed figures; the gate count 58 / 56 open / 2 withdrawn is read from the r7 receipt | none |
| VN-09 | minor | closed | stale reports moved to `history/stale-selected-reports-2026-10-10/` (INDEX.json); a planted foreign report fails the reconciler | none |
| VN-10 | minor | closed | writers record repo-relative POSIX paths; test_repo_hygiene `test_selected_evidence_holds_no_absolute_path` passes on the regenerated usb_head report | 4 frozen and 2 labelled non-reproducible JSONs keep their old paths, by design |
| VN-11 | minor | closed (labelled) | [REPO-INDEX.md](../REPO-INDEX.md) lists each evidence file whose producer is not in the repo and says what still checks it; the extraction hashes tie to the 9 native STEPs (tested) | re-deriving needs the official Pi archive (a download) |
| VN-12 | minor | closed | `requirements-candidate-lock.txt`; Windows/POSIX section in [REPRODUCE.md](../REPRODUCE.md); numpy rasterizer fallback (test_raster_fallback 7/7); render receipts now record the Blender version | pypdf and scipy are declared optional but not installed; installing them needs the user's permission |
| VN-13 | minor | closed (+ user 3) | test_third_party_notices 9/9: THIRD-PARTY-NOTICES.md and the Pi licence beside every derived STEP, written by `export_candidate.py` | a licence for the project's own content is decision 3 |
| VN-14 | minor | closed | PUBLISHING.md, root README, banners on CLOUD-START-HERE.md and HANDOFF.md, publication record (FIX-LOG 21:45 FX-D item 1) | none |
| VN-15 | minor | closed | `check_links_vertical` exits 0 with 0 broken links in live documents. The 214 broken links are 55 inherited from r7 files plus 159 in frozen copies, which now carry FROZEN-LINKS.md banners | none |
| VN-16 | minor | user decision 2 | unchanged | dedupe the Pi STEP; Release assets or LFS (default used: nothing moved) |
| VN-17 | info | closed | test_deterministic_export: fixed header time, canonical colour section. The RF and FX full re-exports reproduce byte for byte | none |
| VN-18 | info | closed | the longest path (132 characters) is documented (`core.longpaths`, or a clone root of at most 120 characters); test_repo_hygiene fails if any path grows past 132 | none |
| VN-19 | info | closed | REPO-INDEX.md separates the pipeline (40 entry scripts), the helpers, the superseded runners and the studies. The "stray" PNGs are bound by the structural PDF receipt (that part was refuted) | none |
| VN-20 | minor | closed (labelled) | `verify_reference_binding.py` re-derives everything that can be re-derived (23/23 rows with `--cad`); the critical-region and load blocks are labelled non-reproducible | none |

### B. Check coverage and check scope

| ID | Sev | Final status | Proof, or the exact failing rows | Left |
|---|---|---|---|---|
| VN-21 | major | open, repository work left | Reporting done: [COVERAGE-VERTICAL.md](../COVERAGE-VERTICAL.md) and CHECKPOINT `check_coverage` classify every row by kind. Compact main audit: 442 geometric passes, 164 bookkeeping passes, 14 coverage/state passes. r7 categories: 21 ported, 5 partly ported, 1 report only, 9 not ported | port or retire boss_geometry, contract, cots_containment, engrave_groove, handling, layout_self_check, print_modifiers, release_access, removals |
| VN-22 | major | closed | test_assembly_state 11/11, test_refit_state 15/15. Main audit in every variant: motion 16/16; motion_coverage 10 pass + 6 open info; assembly_state 3/3 | none |
| VN-23 | major | closed | verification.json in all three variants: driver 11/11, service_driver 11/11, driver_coverage 1/1 (the 6.5 mm bit fits the 7.0 mm counterbores); test_driver_checks 18/18 | none |
| VN-24 | major | **check ported, still failing** | All variants pass j7_float 50/50, lens_support 41 + 5 info, lens_clamp 8 + 2 info and inserts 4/4. roll_catch is 175 pass / **13 fail** / 1 info. The 13: `roll_catch/stub_tilt_on_joint_edge:window@s0.00` .. `@s3.00` (every 0.25 of s). Worst gap **0.055 mm < 0.10** (centred 0.4 >= 0.30), window ±1.4°, catch host tub. Same rows in all three variants | stub geometry change and re-export (section 4.2); linked to decision 16 |
| VN-25 | major | closed | print-checks.json, all three variants: print_overhang 11/11 (original 12/12), print_bridge_direction 11/11 (12/12), thin_wall 11/11 (12/12), bed_contact 1/1, bed_chamfer 11/11 (12/12), critical_features 116 pass / 0 fail / 7 info, 0 unclassified thin spots | slicer and coupons are VN-70 |
| VN-26 | major | **check ported, still failing** | [harness-checks.json](../out/compact-kowa_lm6hc/harness-checks.json) (compact-kowa only): **27 pass / 15 fail / 20 info**. The 15 rows are in section 4.4 | route redesign, measured lead exits, decisions 4, 6, 13 |
| VN-27 | major | **check ported, still failing** | Audits now exist. compact-fujinon (1ef16c87): main 615 / 14 / 32. original-kowa (13d4c85a): main 623 / 14 / 32. Each has its own print and check-scope reports (see VN-25, VN-37). They fail on the same rows as compact (pi5/cooler + the 13 stub rows), so the reconciler's `variant_audit` gates fail | the harness verifier refuses other variants by design (only compact routes are solved); a per-variant route solve is still needed |
| VN-28 | minor | **check ported, still failing** | `cable_routes/qt`: the installed route meets hdmi_ribbon, **5.10 mm3**. `cable_stow/qt`: the members storing 250 / 260 mm meet hdmi_ribbon, **5.20 / 56.06 mm3**. `mate_reach/qt_enc`: the free route meets pi5, **7.27 mm3** at panel_prop. The orphan route report is archived | QT route or cut length (H2 options); QT lead measurement |
| VN-29 | minor | closed (+ user 7) | [microsd-service-dependency.json](../out/compact-kowa_lm6hc/microsd-service-dependency.json): the dog-leg (+X 18, then +Y 40) is clear; panel-off 4 pass / 0 fail / 2 info; the closed-panel path is REJECTED (23 hits) | whether to close the front slit is decision 7 |
| VN-30 | minor | closed | wire-solid-checks.json passes against 44 material obstacles; hdmi-solid-checks.json 16 pass / 0 fail; test_wire_terminal_rules 5/5 | none |
| VN-31 | minor | closed | the reconciler asserts the exact info set (MAIN_AUDIT_INFO + the 6 open motions); the main audit has 32 info rows in every variant | none |
| VN-32 | minor | closed | print-mesh-checks.json 11/11 (original 12/12), each row with `manifest_file_binding` and its expected hash | none |
| VN-33 | minor | closed | check_scope j4_screen 4/4 in every variant, using the new direct J4 free body. Equal share + wiring: **0.9368** (compact-Kowa), **0.7699** (Fujinon), **0.9822** (original-Kowa) N m, against the stated 1.00 N m covering screen | the J4 physical test stays with the inherited gates |
| VN-34 | minor | closed | check_scope evf_restraint 9/9 in every variant (its -Z row failed at phase 1); evf_face 12 pass + 3 info | none |
| VN-35 | minor | closed (+ hardware) | hdmi_face 4 pass / 2 info | the contact-side rows stay HOLD until the HDMI heads are measured |
| VN-36 | minor | user decision 8 (+ hardware) | flow_network nominal: CSI is **48.6 %** of the intake (323.1 of 665.0 mm2 eq). With the CSI slot plugged the system figure drops from 285.6 to 232.2 mm2 eq. baseline_drift passes against each variant's own baseline | the CSI plug is decision 8; an operating point needs the fan curve |
| VN-37 | info | **check ported, still failing** (+ user 17) | `area_parity/hot_branch_series` **498.2 < 510 mm2** (−11.8). `area_parity/hot_path_min_cut` **444.5 < 510** (shortfall 65.5; empty-bay bound 493.2). All three variants. The cold side passes: path 420.0 of 420, series 703.1 | decision 17 (default used: keep the ports and mouths and report the rows as failing) |
| VN-38 | minor | closed | check_scope `stack_retention/vertical_carrier` passes (CoM 5.83 mm inside the hull; third locating feature, no new screw); post_root_bending passes | real standoffs are VN-77 |

### C. Assembly procedure and service

| ID | Sev | Final status | Proof, or the exact failing rows | Left |
|---|---|---|---|---|
| VN-39 | major | closed | `steps.py` puts the collar and gauge before the camera; the lint shows the gauge is never present with the camera or adapter in any state (test_assembly_state); the ASSEMBLY blocks are generated (test_build_order_docs 23/23) | the guide PDF still shows the old order; it carries a STALE banner and its rebuild is open (4.6) |
| VN-40 | major | closed | B3 has no FPS hardware; step 6 is panel_in, panel_screws, fps_washer_on, fps_nut_on, knob_fps_on (test_build_order_docs, test_refit_state) | none |
| VN-41 | major | closed | lens and s_c4 are in step 2, before the carrier; r7 `lens_turn_back_lint` (byte-identical source) passes on ASSEMBLY step 2 and fails on 9ced753 | none |
| VN-42 | major | user decision 5 | service matrix with both lens-change rows: same collar = closed body, safety only; other collar = 35 ids, 9 screws, 7 cables, 22 refit ops. Options A and B are in ASSEMBLY 5.3 | decision 5 (no default taken) |
| VN-43 | minor | closed | EVF HDMI and 5 V now mate at step 5. The carried sweep runs at stroke + 3 mm (9.0 mm drop), and there are pliers-corridor rows for unplugging: hdmi-solid-checks.json carried_sweep 1/1, service_access 3/3 | none |
| VN-44 | minor | closed | B0 bench pre-mate of the camera-end FPC (steps.py, ASSEMBLY B0) | none |
| VN-45 | minor | closed (+ user 11) | grip service row = Pi module out first (default used) | an inline run-lead junction is decision 11 |
| VN-46 | minor | closed | a deep socket on the axis for both nuts; test_build_order_docs finds no un-negated "spanner" in ASSEMBLY, the FPS study, steps.py or the BOM | the V-62 socket size waits for the measured 1505 nut (the BOM row is gated) |
| VN-47 | major | **check ported, still failing** (+ user 6, + hardware) | `lead_access/pigtail_ties_on_route`: no allocated tie slot reaches either core (nearest **31.76 mm** positive, **4.89 mm** negative; capture 2.3 mm). `lead_access/pigtail_xt30_mouth`: XT30 face-out is none for the positive core and **−53.53 mm** for the negative core, against the required 15.0; the positive corridor meets base_grip 18.96, microsd 10.90 and tub 1.47 mm3 at pack_in. `mate_reach/xt30_pack` fails on the same reach problems | ties or RTV-only is decision 6; flexible reach and finger force are bench gates (VN-72) |
| VN-48 | minor | hardware gate (+ user 12) | unchanged | coordinated-hand trial; a clip or helper is decision 12 |
| VN-49 | minor | hardware gate | unchanged | measure the 4448 overmold and exit |
| VN-50 | minor | closed | [GATES-VERTICAL.md](../GATES-VERTICAL.md) maps all 58 r7 gates and BX-1..BX-17 once: 39 carried, 11 re-scoped, 3 replaced, 5 retired; 53 of the 56 open gates still apply. Generated, `--check` exits 0 (test_coverage_gates 8/8) | the r7 BX-13 and BX-14 procedures are not yet written into ASSEMBLY (new docs item, 4.7) |

### D. Print and CAD geometry

| ID | Sev | Final status | Proof, or the exact failing rows | Left |
|---|---|---|---|---|
| VN-51 | major | closed | trial3 roof (hanging beams on pillars, flow windows): the tub passes print_overhang and print_bridge_direction in every variant | slicer, coupons and cleanout are VN-70 |
| VN-52 | major | closed | the mouth regions pass both print rules; the print hold names all four mouths; the coupon has a third crop, all_four_mouths (3 crops, manifest dbea5ca5) | coupon print (VN-70) |
| VN-53 | major | user decision 16 | the +Y tine is now a separate stub, bonded into the tub at B1 `print_inserts` (default used: two-part epoxy, BOM V-68). The tub print rows pass | The bond stack-up fails 13 roll-catch rows per variant; they are counted under VN-24. The alternatives are a press fit with a detent or the panel-held block |
| VN-54 | major | closed | carrier print_overhang, print_bridge_direction and bed_contact pass (the frame sits on the bed) | none |
| VN-55 | major | closed | lens_clamp washer_flat_support and washer_free_seat pass for Kowa and Fujinon (lens_clamp 8 pass / 2 info) | none |
| VN-56 | minor | closed | carrier counterbores are now 7.0 mm; driver and service_driver pass p_carrier1 and p_carrier2 | none |
| VN-57 | minor | closed (+ hardware) | base_grip passes the print rules (the pocket ends inside its declared support zone; 0.2 mm scar allowance); main-audit clearance 4/4 (J4 slide) | the physical slide gate stays |
| VN-58 | minor | closed | lens_collar passes the print rules (LR foot support) | none |
| VN-59 | minor | closed | new bed_chamfer check, 11/11 (original 12/12). The r7 0.6 mm chamfer is now on the panel, eyecup and stick sleeve. One declared exception: collar upper-lug top A1, 7.85 of a maximum 8.5 mm, tied to lens_clamp | none |
| VN-60 | minor | closed (+ user 10) | the EVF feed, diode sleeve and RCY volumes are placed on the installed usb_5v route: harness feed_volumes 6/6. The stale ko_5v_up text is gone from the BOM. The option-C reserve is kept free | option C is decision 10 |

### E. Electrical and BOM

| ID | Sev | Final status | Proof, or the exact failing rows | Left |
|---|---|---|---|---|
| VN-61 | major | closed | [WIRING-VERTICAL.md](../WIRING-VERTICAL.md) is generated by `make_wiring_vertical.py` (`--check` 0, test_wiring_bom 20/20); ASSEMBLY points to it | none |
| VN-62 | major | **check ported, still failing** (+ user 4) | `lead_access/pigtail_drop`: drop_hi **0.1625 V > 0.150 V** at 8.6 A (hot fuse ×1.30, vendor minimum strands, lay 1.03). `cable_routes/pigtail_positive` and `pigtail_negative`: shortest route **251.8 / 250.9 mm** + 27.0 allowance > 270.0 mm stock. H2 found shorter service corridors (~207 / 196 mm), but RTV reach then needs L >= 237.0 | the G-W5 branch is decision 4; never relax 0.150 V |
| VN-63 | minor | user decision 13 | BOM V-28 is now a keyed 2-circuit set of a family no other junction uses (default used: Molex Micro-Fit 3.0 class; SKU recorded at order); test_wiring_bom | there is no modeled stow home for the J2 pair: `cable_stow/power_button_j2_pair` needs 1227.3-1797.3 mm3 against a capacity of 777.6 mm3 (section 4.4) |
| VN-64 | minor | closed | BOM: D2-26 black SKU, spare policy (V-23S, V-27S, V-28S, V-22OS), consolidated buy view (BUY-VERTICAL.csv), V-62 gated; BOM `--check` 0 (135 rows); test_wiring_bom | none |
| VN-65 | minor | user decision 9 | unchanged (button 5 mm proud, no guard) | decision 9 |
| VN-66 | minor | hardware gate | unchanged | measure the EVF pads |

### F. Thermal

| ID | Sev | Final status | Proof | Left |
|---|---|---|---|---|
| VN-67 | minor | hardware gate | unchanged | MTC row, thermocouple |
| VN-68 | minor | hardware gate | unchanged | powered thermal test |

### G. Documented holds

| ID | Sev | Final status | Current computed state | Left |
|---|---|---|---|---|
| VN-69 | major | hardware gate | `interference/pi5/cooler` **79.902671 mm3** still fails in all three variants (unchanged) | measure the cooler registration; never reclassify |
| VN-70 | major | hardware gate | every computed print check passes (VN-25) | slicer, the 3 plenum coupon crops, the tine/bond coupon, support review |
| VN-71 | major | hardware gate | the flow model is the pre-check (VN-36, VN-37) | closed-body thermal test |
| VN-72 | major | hardware gate | the pigtail rows fail (VN-47, VN-62) | routing mock-up |
| VN-73 | major | hardware gate | `cable_routes/power_button` fails on the hypothetical J2-pad route (cooler 28.60, pi5 1.27 mm3) | measure the 1505 switch, nut and J2 pads |
| VN-74 | major | hardware gate | `cable_routes/fpc` fails as a round-envelope screen (16 mm, not proof of a conflict) | measure the FPC ends and lay |
| VN-75 | minor | hardware gate | hdmi-solid-checks 16 pass / 0 fail | qualify the HDMI assembly |
| VN-76 | minor | hardware gate | unchanged | SSD on a Pi 5 |
| VN-77 | minor | hardware gate | stack_retention now passes computationally (VN-38) | real standoffs, screws and carrier retention |
| VN-78 | minor | hardware gate | unchanged | strap trial |
| VN-79 | minor | hardware gate | integrated FPS: 332 material checks, 0 hits (status geometric_pass_only) | CK1044 and donor parts |
| VN-80 | minor | user decision 10 | default used: diode feed kept; option-C reserve kept free, BOM qty 0 | decision 10 |
| VN-81 | info | hardware gate | unchanged | power envelope |
| VN-82 | major | hardware gate | M1 open; 58 inherited gates (56 open, 2 withdrawn), 53 of the open ones still apply (GATES-VERTICAL.md) | M1 and the gates |
| VN-83 | info | user decision 14 | unchanged | balance rule |
| VN-84 | info | user decision 14 | unchanged | press-in caps |

## 3. Final numbers

All reports bind their own variant's manifest. The manifest hashes are dbea5ca5 (compact-kowa), 1ef16c87 (compact-fujinon) and 13d4c85a (original-kowa), and each equals the SHA-256 of `out/<variant>/manifest.json`. `physical_qualified` is false in every report.

### 3.1 Main audit (`verification.json`), per category

| Category | compact-kowa | compact-fujinon | original-kowa |
|---|---|---|---|
| integrity | 46 pass | 46 pass | 47 pass |
| roundtrip | 45 pass | 45 pass | 46 pass |
| source_binding | 73 pass | 73 pass | 73 pass |
| interference | 108 pass / **1 fail** / 9 info | 103 / **1** / 9 | 109 / **1** / 9 |
| non_material_keepout | 1 info | 1 info | 1 info |
| assembly_state | 3 pass | 3 pass | 3 pass |
| motion | 16 pass | 16 pass | 16 pass |
| motion_coverage | 10 pass / 6 info | 10 / 6 | 10 / 6 |
| driver | 11 pass | 11 pass | 11 pass |
| service_driver | 11 pass | 11 pass | 11 pass |
| driver_coverage | 1 pass | 1 pass | 1 pass |
| j7_float | 50 pass | 50 pass | 50 pass |
| lens_support | 41 pass / 5 info | 41 / 5 | 41 / 5 |
| lens_clamp | 8 pass / 2 info | 8 / 2 | 8 / 2 |
| roll_catch | 175 pass / **13 fail** / 1 info | 175 / **13** / 1 | 175 / **13** / 1 |
| inserts | 4 pass | 4 pass | 4 pass |
| clearance | 4 pass | 4 pass | 4 pass |
| nominal_features | 7 info | 7 info | 7 info |
| step_material_probes | 13 pass | 13 pass | 13 pass |
| step_aperture_probes | 1 pass | 1 pass | 1 pass |
| physical | 1 info | 1 info | 1 info |
| **total (21 categories)** | **620 / 14 / 32** | **615 / 14 / 32** | **623 / 14 / 32** |

The failing rows are the same in all three variants:
- `interference/pi5/cooler`, 79.902671 mm3;
- 13 rows `roll_catch/stub_tilt_on_joint_edge:window@s0.00..s3.00`, worst gap 0.055 mm against the 0.10 mm rule.

At 9ced753 the main audit was 292 / 1 / 18 in 10 categories.

### 3.2 Other reports

| Report | compact-kowa | compact-fujinon | original-kowa |
|---|---|---|---|
| print-checks.json | every category passes: overhang 11/11, bridge direction 11/11, thin_wall 11/11, bed_contact 1/1, bed_chamfer 11/11, critical_features 116 / 0 / 7, unclassified thin spots 0 | same as compact | overhang, bridge, thin_wall, bed_chamfer 12/12 each; bed_contact 1/1; critical_features 116 / 0 / 7 |
| print-mesh-checks.json | 11 pass | 11 pass | 12 pass |
| check-scope-checks.json | 34 / **2** / 14 (area_parity 2 pass / 2 fail; evf_face 12 / 3 info; evf_restraint 9; flow_network 1 / 9 info; hdmi_face 4 / 2 info; j4_screen 4; post_root_bending 1; stack_retention 1) | 34 / **2** / 14 | 34 / **2** / 14 |
| shadow-plenum-checks.json | 49 pass / 0 fail / 21 info (outlet context 4 / 0) | not run per variant | not run per variant |
| harness-checks.json | 27 / **15** / 20 (cable_routes 4 / 7 / 2, cable_stow 2 / 2 / 10, feed_volumes 6, header_housings 7, lead_access 1 / 3 / 2, mate_reach 2 / 3 / 5, signal_routes 5 / 1 info) | refused by design (no route solve) | refused by design |
| hdmi-solid-checks.json | 16 pass / 0 fail (carried_sweep 1, full_ribbon_vs_solids 2, hard_head_vs_material 3, hard_head_vs_printed 3, obstacle_fixture 4, service_access 3) | - | - |
| integrated-fps-checks.json | geometric_pass_only: 332 material checks, 0 hits; 9 non-material diagnostics, 0 hits | - | - |
| power-service-checks.json | pass: 201 poses, 659 exact intersections | - | - |
| wire-solid-checks.json | pass, 44 material obstacles | - | - |
| microsd-service-dependency.json | closed-panel path REJECTED (23 hits); panel-off dog-leg 4 / 0 / 2 | - | - |
| csi-source-tool-checks.json | declared rigid reservation clear; operational HOLD | - | - |

The check-scope failures are `area_parity/hot_branch_series` (498.2 < 510) and `area_parity/hot_path_min_cut` (444.5 < 510).

### 3.3 Batch run record

The batch runner is `run_shadow_checks.py` (runner 15238fc4). Its committed record is `out/compact-kowa_lm6hc/review-check-run.json` (sha 2a673ba6), with 15 rows. 12 rows exit 0: bound_files, mesh, print, build_order_docs, csi, power_rigid, power_static, hdmi, fps, usb_head, microsd, void. 3 rows exit 1:
- harness (the 15 rows in 4.4);
- rigid (the main audit's 14 rows);
- check_scope (the 2 hot plenum rows).

### 3.4 Reconciler and docs audit (re-run read-only on 2026-10-12, through run_locked)

`reconcile_review_evidence.py --check` exits 1 with **10 gate failures**. Nothing is written.

| Gate | Count | Reason |
|---|---|---|
| foreign_manifest_report | 6 | `current-review-evidence.json` still binds 53e668d4, because the reconciler rewrites it only when there are 0 failures. The 5 render receipts bind 53e668d4 because rendering needs Blender, which is not on this machine |
| rigid | 1 | new active rigid faults: the 13 stub-tilt rows next to the accepted pi5/cooler row (4.2) |
| variant_audit:compact-fujinon_hf6xa, variant_audit:original-kowa_lm6hc | 2 | the same 13 stub-tilt rows in each variant |
| harness_failures_differ | 1 | the 15 honest harness failures against the empty accepted set (`EXPECTED_HARNESS_FAILURES = {}`) |

`review_docs_audit.py --check` exits 1 with **11 failures**. The committed `out/review-docs-audit.json` is current.

| Failure | Count | Reason |
|---|---|---|
| foreign_manifest_report | 6 | the same 6 reports as above |
| stale_selected_report + binding (structural PDF receipt) | 2 | the structural PDF was not rebuilt: pypdf is not installed. Its 7 bound sources changed |
| binding + guide_manifest_stale + bound_files (guide) | 3 | the guide still nominates 53e668d4 (61 bound sources changed) and needs trial3 diagrams before a rebuild |

No accepted set was widened to make either tool pass. `EXPECTED_PRINT_FAILURES` and `EXPECTED_HARNESS_FAILURES` are both empty.

### 3.5 Tests

**Where these numbers come from.** A separate verification lane made a fresh clone of 4f9e029 the same night (2026-10-12, 01:48-02:15; scratchpad vnfinal). It first rebuilt the git-ignored mesh caches of all three variants with `export_cache.py regenerate`. Then it ran the whole suite through run_locked, one file at a time.

Before the rebuild, `export_cache.py status --no-guide` exited 3 (only rebuildable caches missing). After it, status exited 0. This is the fresh-clone proof for VN-04's variant part.

This page also re-ran 13 of the files on the working tree. They gave identical results. That run was stopped so it would not compete with the fresh-clone lane for the CAD lock.

**Candidate suite (36 files, 495 tests):** 32 files pass and 4 files fail, with 1 failing test each (after the 02:25 fixture fix below; the fresh clone of 4f9e029 had 31 and 5). One further failure is an expected one (`test_collar_r7_mechanical`: r7 `prepare_print`, see 4.7).

| Red file | Failing test | Cause | Owner |
|---|---|---|---|
| test_j7_collar (14 tests) | the exact failing-set record test | the 13 stub-tilt rows (4.2) | geometry, decision 16 |
| test_c2_collar_grip (18) | `test_main_audit_c2_record` (asserts no j7 failure) | the same 13 rows | geometry, decision 16 |
| test_plenum_trial2 (17) | `test_sections_parity_and_sampling` | the hot front neck is 197.2 mm2 at the saved tub against the 202.8 metadata (4.3) | next export |
| test_evidence_tooling (15) | `test_live_selected_folders_are_clean` | the 6 foreign-manifest reports in the selected folder (3.4) | guide/render rebuild, reconciler write |
| test_deterministic_export (21) | none: fixed at 02:25 | the fixture read the working-tree `tub.step`, which carries the normalised FP-03 header, so its premise had expired. It now reads the raw OCCT header from the 9ced753 blob, and a new test checks that normalising the committed export is a no-op. 21 OK |

The other 32 files pass, for example:
- test_assembly_state 11, test_build_order_docs 23, test_refit_state 15
- test_check_scope 21, test_print_checks 11, test_driver_checks 18
- test_carrier_fp11c 20, test_critical_features_cf 11, test_tub_print_t2 8, test_fx_fixup 33
- test_harness_checks 24, test_fxh_harness 25, test_h1_feed_routes 17, test_h2_harness 21, test_wire_terminal_rules 5, test_wiring_bom 20
- test_evidence_numbers 8, test_doc_figures_checkpoint 8, test_reconciler_variants 6, test_coverage_gates 8
- test_cross_platform_io 12, test_windows_smoke 3, test_repo_eol 7, test_repo_hygiene 19, test_third_party_notices 9, test_raster_fallback 7, test_export_plan 6, test_guide_scenes 3, test_routes_source_fix 7
- the candidate's original `test_routes_source.py` 10 (it was 8/10 at 9ced753; the two tests were wrong, not the geometry)

**r7 suite (unchanged r7 code, same fresh-clone run):**
- `test_r3_regressions.py`: 82 of 82 cases pass.
- The `validation/README.md` unittest list: Ran 73, OK (4 POSIX skips).
- `audit_cloud_release.py --final-release`: failures [], 58 gates (56 open, 2 withdrawn).

These are the same results the FX fix-up recorded ([FIX-LOG.md](FIX-LOG.md), 01:09 and 01:37 lines).

## 4. Open items

### 4.1 Hot plenum bay (VN-37, user decision 17)

Rows: `area_parity/hot_path_min_cut` is 444.5 mm2 against 510 mm2 of hot wall ports (shortfall 65.5). `area_parity/hot_branch_series` is 498.2 against 510 (−11.8). Both fail in all three variants. The cold side passes (path 420.0 of 420, series 703.1).

Cause: the hot bay cannot reach 510 mm2 even when empty. The region that holds the hot ports (x −62..−2.5, z 16..40) has about 493.2 mm2 of free section (`plenum_flow` empty-bay bound). The trial3 roof ribs (hanging beams on pillars, needed by the print rules) bring the path minimum down to 444.5. The series figure is set by the hot_bottom minimum of 301.0 mm2 at the z 21 port-band plane plus the front neck at 197.2 mm2.

Options (register decision 17):
- (a) enlarge the hot mouths, for example by removing the front-mouth mullion or widening the mouths;
- (b) make the hot wall ports smaller, or move them;
- (c) accept the measured path minimum and rely on the G-V-THERMAL test;
- (d) use a different roof support that needs fewer ribs. Even then the result can never exceed the 493.2 bound.

**Default used: keep the ports and mouths, and report the rows as failing.** No check was relaxed. To pass, the design needs (a) or (b), plus a re-export.

### 4.2 Bonded tab-catch stub: tilt stack-up (VN-24 / VN-53, linked to user decision 16)

Rows: `roll_catch/stub_tilt_on_joint_edge:window@s0.00` .. `@s3.00`, **13 rows per variant, 39 in all**. The case modelled is the stub tilted 0.1 mm over the 3.5 mm tenon, about the lower edge of the datum on the joint plane. In that pose the worst window gap is **0.055 mm**, below r7's 0.10 mm rule. The centred gap is 0.4 mm against its 0.30 mm rule, the window is ±1.4°, and first contact still passes.

The other four displaced-stub cases keep the nominal window (worst 0.129 mm).

Fix options, all geometry:
- recess the stub's catch face +Y by 0.05-0.1 mm (stub only);
- lengthen the tenon datum, so the same film variation tilts the stub less;
- retain the stub with a press-fit detent instead of a bond.

After any of these, re-export and re-run roll_catch. These 13 rows are why test_j7_collar and test_c2_collar_grip are red, and why the reconciler's `rigid` and both `variant_audit` gates fail.

### 4.3 vent_geometry metadata (fix with the next export)

`vent_geometry.py` is a manifest source, so it could not be edited without a re-export. Two of its statements disagree with its own geometry:
- **Cold keep-out comment.** The comment says the cold rows keep no pillar in `COLD_WINDOW_X`. In the code, `rib_boxes` applies that keep-out only to rows ending at x <= −65 (rows 43-67). The geometry is correct for its gate (the saved-STEP cold path minimum is 420.0 = ports). Only the comment is wrong.
- **Hot front neck.** `mouth_nominal` says hot_front = 202.8 mm2. The saved tub measures 197.2 mm2 at the x −2.62 plane, because the lip rib (x −3.8..−2.6) crosses the inboard neck plane. The metadata overstates the area by 5.6 mm2. This is the cause of the red test_plenum_trial2.

The same next export should also fix `export_cache.py`'s guide-rebuild message, which names only the Linux rasterizer (also a manifest source; deferred by FX-D).

### 4.4 Harness rows (VN-26, VN-28, VN-47, VN-62, VN-63, VN-73, VN-74)

`harness-checks.json` (compact-kowa, dbea5ca5): 27 pass / 15 fail / 20 info. Several rows are stricter screens added by FX-H, and they say so in their own text.

| Row | Measured | What settles it |
|---|---|---|
| cable_routes/qt | installed route meets hdmi_ribbon 5.10 mm3 | QT route redesign or a different QT cut length (VN-28) |
| cable_routes/power_button | meets cooler 28.60, pi5 1.27 mm3; envelope 2.97 < 9.60 mm from the FPC | measured J2 pads and 1505 (VN-73, G-V-POWER) |
| cable_routes/fpc | 16 mm round envelope meets cooler 1280.32, hdmi_ribbon 4093.10, pi5 891.58 mm3 and others; **screen, not proof of a conflict** | developable FPC model or the measured lay (VN-74) |
| cable_routes/fan | meets cooler 103.79 mm3 (the estimated lead runs inside the cooler model) | re-draw from the measured lead exit |
| cable_routes/oled_flex | 12.4 mm round envelope meets evf_board 4799.93, panel 2614.30 mm3 and others; **screen, not proof** | developable ribbon model or the measured lay |
| cable_routes/pigtail_positive / pigtail_negative | shortest 251.8 / 250.9 + 27.0 allowance > 270.0 stock | decision 4 (VN-62) |
| cable_stow/qt | members storing 250 / 260 mm meet hdmi_ribbon 5.20 / 56.06 mm3 (240 mm clear) | QT cut length or storage (VN-28) |
| cable_stow/power_button_j2_pair | demand 1227.3-1797.3 mm3 > capacity 777.6 mm3 | decision 13 (J2 family) and a J2 stow space (VN-63) |
| mate_reach/qt_enc | free route meets pi5 7.27 mm3 at panel_prop | QT free-lead route (VN-28) |
| mate_reach/j2_btn | free route meets cooler 1.70 mm3; envelope 5.75 < 8.80 mm from the FPC | J2 route after decision 13 |
| mate_reach/xt30_pack | XT30 face-out not reached (positive none, negative −53.53 < 15.0) | decision 6, pigtail mock-up (VN-47, VN-72) |
| lead_access/pigtail_ties_on_route | nearest tie slot 31.76 / 4.89 mm vs 2.3 mm capture | decision 6 (VN-47) |
| lead_access/pigtail_xt30_mouth | as xt30_pack; positive corridor meets base_grip 18.96, microsd 10.90, tub 1.47 mm3 | decision 6 (VN-47) |
| lead_access/pigtail_drop | drop_hi 0.1625 V > 0.150 V at 8.6 A | decision 4 (VN-62) |

The harness verifier runs only on compact-kowa. The other two variants have no route solve (VN-27).

### 4.5 pi5/cooler overlap (VN-69)

`interference/pi5/cooler` is **79.902671 mm3** in all three variants. The value is unchanged since 9ced753 and inherited from the corrected Pi/cooler source data. It is the one failing row that is allowed in every variant audit. It can only be closed by measuring the cooler's registration on a real Pi 5 with an Active Cooler. Never reclassify it.

### 4.6 Guide, renders, structural PDF

These are the causes of 9 of the 11 docs-audit failures and 5 of the reconciler's 6 foreign-manifest reports.
- **Guide.** The concealed guide still nominates 53e668d4, and its diagrams predate trial2 and trial3. `vent_guide_support.py` refuses with "Plenum topology changed". The guide needs trial3 diagrams first, then a rebuild with `guide/run_with_numpy_raster.py`. Its READMEs carry STALE banners.
- **Renders.** The five render receipts need Blender, which is not installed on this machine.
- **Structural PDF.** The PDF needs pypdf. It is optional and not installed; installing it needs the user's permission.
- **Selected evidence.** `current-review-evidence.json` is rewritten only when the reconciler has 0 failures, so it still binds 53e668d4.

### 4.7 Found during the fixes, not in the register

| Finding | State |
|---|---|
| r7 BX-13 (proud shafts before the knobs) and BX-14 (18/24 shaft cut) procedures are not written into ASSEMBLY-VERTICAL.md (GATES-VERTICAL rows say so) | open, docs |
| switch_1824 sits 0.466 mm from the p_carrier1 boss (clearance passes; the r 5.1 ear boss was considered and not changed) | noted |
| Recorded `bbox_mm` values are inflated by the triangulation (~0.01-0.69 mm), not by the B-rep (FP-03) | not changed (would move REVIEW and structural figures) |
| Part STEP PRODUCT names carry OCCT's per-process counter, so a single-part re-export differs from a full export (full exports are deterministic) | documented |
| r7 `prepare_print` invalidates the in-memory Fujinon collar shape (cause found by C2; geometry not at fault; r7 code read-only) | tests use copies; 1 expected failure in test_collar_r7_mechanical |
| FPS pair-guide corbel hit the switch bundle (7 hits up to 23.131 mm3), and `verify_fps_integrated.py` never exited non-zero | fixed in FX (bundle lane; exit code) |
| Plenum cavity row 1279.487 mm3; J4 screen refusal; carrier tie bar 3 at 0.877 mm; tenon pocket walls 0.9 mm; original-variant flow baseline | fixed in FX (FIX-LOG 23:31 lines) |
| Run-lead route inside tub material; base_grip 0.373 mm feather edge; the old `test_routes_source.py` 2/10 (the tests were wrong) | fixed in phase 2 (H1, C2, FP-15) |
| The FIX-LOG 01:09 line lists check_scope among the exit-0 batch rows; the committed run record (sha 2a673ba6) records check_scope exit 1 (the two hot rows) | the run record is the authority; this page uses it |

## 5. User decisions

None of these was decided by the review. "Default used" means the state the files are in now, which the user can change.

| # | Entries | Question and options | Default used |
|---|---|---|---|
| 1 | all | keep developing the vertical fork, or treat r7 as the build baseline | none; the review only repaired the fork |
| 2 | VN-04, VN-16 | commit about 100 MB of mesh caches and guide pages, or split them out; dedupe the Pi STEP; Release assets or LFS for the assembly STEPs | caches not committed (rebuildable with `export_cache.py regenerate`); nothing moved |
| 3 | VN-13 | a licence for the project's own CAD and docs | none (the Raspberry Pi MIT notice is carried) |
| 4 | VN-62 | G-W5 fail branch: shorter path, 14 AWG, or a higher software cut-off | none; pigtail_drop fails |
| 5 | VN-42 | A: accept carrier-out camera / other-collar lens service; B: redesign (B1 camera exits ahead of the carrier front, B2 lip-free gauge) | none; the routes model option A, which is what the current geometry allows |
| 6 | VN-47 | carrier cable ties (heads at the rail edges) or r7's RTV-only retention | none; four provisional ties stay in the text, RTV-only computed |
| 7 | VN-29 | close the front microSD slit or keep it | slit kept (unchanged) |
| 8 | VN-36 | a CSI plug, decided after the flow model | no plug |
| 9 | VN-65 | power-button guard ring, recess or flush switch | unchanged (no guard) |
| 10 | VN-80, VN-60 | EVF option C | diode feed kept; option-C reserve kept free, BOM qty 0 |
| 11 | VN-45 | inline run-lead junction, or "module out first" | module out first |
| 12 | VN-48 | printed transport clip or a helper for step 4 | none |
| 13 | VN-63 | J2 connector family | Molex Micro-Fit 3.0 class, keyed 2-circuit, SKU recorded at order |
| 14 | VN-83, VN-84 | a balance rule; press-in caps over the panel screws | none |
| 15 | all | whether and when to push the fixes to the public repo | not pushed; only the INTERMEDIATE snapshot 4d160f7 is public |
| 16 | VN-53 | retention of the +Y tab-catch stub: bond, press fit with a detent, or the panel-held block (valid only if the lens is fitted with the panel on) | bonded at B1 `print_inserts` with two-part epoxy (V-68); its tilt stack-up fails (4.2) |
| 17 | VN-37 | hot plenum: (a) larger hot mouths, (b) smaller or moved hot wall ports, (c) accept and rely on G-V-THERMAL, (d) another roof support (still under the 493.2 bound) | keep ports and mouths; report the hot rows as failing |

## 6. Recommended bench order and suggestions

Bench and desk order. Each step names what it closes.
1. **Measure the Pi 5 + Active Cooler registration.** This closes or re-scopes VN-69, the only inherited rigid failure. It needs only parts already on the shopping list.
2. **Desk work, then one export cycle.** Decide 16 and 17, and choose the stub fix (4.2). In the same re-export, correct the vent_geometry metadata (4.3) and the export_cache message. Then re-run the batch, the variant audits, the reconciler and the docs audit.
3. **SSD on a Pi 5** (VN-76, G-V-STORAGE). The compact body depends on it.
4. **Print the coupons.** That means the 3 plenum crops and the tine/bond coupon, plus a slicer and support review (VN-70). Only do this after step 2, because the plenum and stub geometry may change.
5. **Measure the leads and heads.** Covers the 1505 switch, nut and J2 pads (VN-73; this also sizes the V-62 socket and the J2 stow space), the QT lead, the fan lead exit, the FPC ends and lay (VN-74), the HDMI head contact sides (VN-35), the 4448 overmold (VN-49) and the EVF pads (VN-66). These settle most of the harness rows in 4.4.
6. **Pigtail routing mock-up** after decisions 4 and 6 (VN-72, VN-47, VN-62).
7. **Closed-body thermal test with thermocouples** (VN-71, VN-67, VN-68), after decision 17.
8. **Stack, strap and hand trials** (VN-77, VN-78, VN-48); CK1044 donor parts (VN-79); power envelope (VN-81); M1 and the inherited gates (VN-82).

Suggestions:
- Decision 1 is still the main question. The fork now has its checks, but it carries 7 failing checks and the same physical gates as r7, plus its own.
- Build the guide only after trial3 diagrams exist, then re-run the docs audit. Run the renders on a machine with Blender.
- Solve the harness routes per variant before trusting the Fujinon or original-storage builds (VN-27).
- Port or formally retire the 9 r7 categories that are not ported (VN-21).
- Add a Windows CI job that runs every `--check` command and the emulated-autocrlf clone test.
- Push only on decision 15. If pushed, push the review branch, not `main`.
- Keep `EXPECTED_PRINT_FAILURES` and `EXPECTED_HARNESS_FAILURES` empty. Never accept a failing row to make a gate pass.

