# Corrective issue register: commit 1b59395 (vertical-nizo)

> **Record note (2026-10-12, main session).** This is the merged issue register as written by the review workflow *before* the fix round. Entries are CR-01.. with their source IDs (REPRO/CHE/GEO/PUB/ELE). Paths such as `vnc/...` name the review session's working files, which are not part of this repository. "It is not on origin" was true when written; `1b59395` is now published unchanged on the review branch `review/vn-corrective-20261012`. What the fix commit closed, and what stays open, is in [CORRECTIVE-REVIEW.md](CORRECTIVE-REVIEW.md) (Final status).

Commit under review: `1b59395` "Improve catch clearance, QT routing and concealed plenum; retain review holds".
It sits on the main session's review tip `bdfd44f` and is fetched as `delivery/vn-corrective-local-20261012`.
It is not on origin. Register date: 2026-10-12.

## Inputs merged

| Dimension | Review | Adversarial verdict |
|---|---|---|
| Reproduction | `vnc/repro/REPRODUCTION.md` (REPRO-01..10) | 7 confirmed (REPRO-07 downgraded to info); 5 missed items |
| Check integrity | `vnc/check-integrity/REVIEW-check-integrity.md` (CHE-1..12) | 9 confirmed (CHE-5 and CHE-7 downgraded to info); 6 missed items |
| Geometry | `vnc/geometry/REVIEW-geometry.md` (GEO-1..6) | GEO-1..5 confirmed (GEO-2 raised to major); GEO-6 not verified; 2 missed items |
| Publication | `vnc/publication/REVIEW-publication.md` (PUB-1..11) | 7 confirmed, **PUB-5 refuted** (PUB-7 downgraded to info); 6 missed items |
| Electrical | `vnc/electrical/REVIEW-electrical.md` (ELE-1..11) | 8 confirmed; ELE-8/9/10 not verified; 3 missed items |

Merge rules used:
- Duplicates are merged into one CR entry. Source IDs are listed in each entry.
- Where merged findings had different severities, the verifier's severity wins. When two verifiers disagree, the higher severity is kept and the reason is noted.
- Items found only by a verifier ("missed") are marked **[single-pass]**. Findings that no verifier covered are marked **[unverified]**.
- Refuted findings and verifier corrections are in Appendix A and Appendix B.

Spot check by the register author (git only, no CAD):
- `guide/out-concealed-vents/guide-receipt.json` (287 sources) binds `REVIEW.md`, `BOM-VERTICAL.csv/.md`, `WIRING-VERTICAL.md`, `steps.py`, `harness_rules.py`, `verify_harness_checks.py`, both STEP-REVIEW docs, and the compact-Kowa `verification.json`, `harness-checks.json`, `print-checks.json` and `check-scope-checks.json`. **Almost every code or doc fix below therefore needs a guide rebuild before `review_docs_audit --check` can pass.**
- `review-2026-10-10/FIX-LOG.md`, `PUBLISHING.md`, `REVIEW-HANDOFF.md` and `REVIEW-FIXES-STATUS.md` are bound by no receipt. One test fixture string names FIX-LOG. They can be edited freely.

## Headline claims of 1b59395: verdict

| Claim | Verdict | Register |
|---|---|---|
| Catch worst nominal tilt gap 0.106 mm vs the unchanged 0.100 mm rule | **Reproduced, but not tolerance-robust.** The rule is unchanged. Yaw from the same 0.1 mm film basis gives 0.078 (FAIL). The pocket-clearance tilt, which is the pose the written seating instruction produces, gives 0.084 (FAIL). | CR-02, CR-03, CR-23 |
| Main audit compact Kowa 633/1/32 (only pi5/cooler, 79.902671 mm3) | **Reproduced on Windows** (0 status differences, 0 drift above 1e-6) | Appendix C |
| Main audit Fujinon 628/1/32, original 636/1/32 | Reports bind the current verifier, steps and manifests, but they **were not re-run**. They came from an unlocked, concurrent, Linux-only lane, and the helper that ran is not the committed one. | CR-12 |
| Harness 30/12/20; three QT checks pass | Numbers reproduced. `mate_reach/qt_enc` and `cable_stow/qt` pass on real geometry fixes. **`cable_routes/qt` passes only because the gate input changed** (released pose instead of the installed family). Under the r7 basis the installed route needs 263.99 mm against 240 mm stock (fail). | **CR-01** |
| Concealed hot-path capacity 510 mm2 | Reproduced: 509.999996 on port faces, within the unchanged 0.002 mm2 tolerance. Rounding to 510 is legitimate (PUB-5 refuted). | Appendix A |
| Bonded catch insert printed separately | Printable and insertable (GEO P2). But it has no BOM row, no adhesive vent, and a seating instruction that drives the failing tilt. | CR-27, CR-23, CR-03 |
| Research DOCX/PDF added | Publishable: own words, no images. Caveats: one unofficial paywalled-copy link, and the committed PDF is a re-render of the supplied one. | CR-31, CR-39 |

## Push blockers (must not go to the public repo as is)

No hard publication blocker was found: no secrets, personal data, local paths or vendor redistribution, and no file over GitHub's 100 MB rejection limit (largest 68.2 MB). The blockers are claim-integrity and record-integrity problems:

1. **PB-1 / CR-01. A weakened check is presented as a pass.** `cable_routes/qt` changed its gate basis from the shortest member of the installed family to a hand-authored released pose: the old top56/low38/cross65 route. This flips fail to pass. `EXPECTED_FAILING` drops the row, and REVIEW.md:315 says the route "passes its installed geometric screen". The handoff does not disclose the change.
2. **PB-2 / CR-02 + CR-03. The catch is presented as fixed while computed failing cases exist on the model's own basis.** Yaw of the 0.1 mm film basis gives 0.078 mm. The clearance-limited tilt from the steps.py:94 instruction gives 0.084 mm. Either fix the geometry (FX-03), or publish with these cases added (failing) and the hold stated. Do not publish it as closed.
3. **PB-3 / CR-09 + CR-11. Publication-state documents become false on push.** README.md:29, PUBLISHING.md:5/:13, candidate README.md:15/28/32, REVIEW-HANDOFF.md:3 and REVIEW.md:24 say the work is unpublished, the user will push later, and "No message is being sent to Claude". REVIEW-FIXES-STATUS.md and FINAL-STATUS.md describe a different tip.
4. **PB-4 / CR-10. The independent reviewer's record has been edited by the reviewed agent.** review-2026-10-10/FIX-LOG.md gains 9 unmarked 2026-10-12 entries. One of them ("structural write and --check each exit 0") is false on the Windows reference platform (CR-07).

Pre-push gates (not blockers by definition, but required for a clean push):
- the full candidate suite green on Windows (CR-08, CR-13, CR-14, CR-15, CR-21)
- `check_links_vertical.py` run (CR-43)
- `review_docs_audit --check` and `reconcile --check` green (CR-06)

## Counts

43 active entries: **9 major, 22 minor, 12 info**. In addition, 1 refuted finding is in Appendix A.

Classification of the 43 active entries:
- Closable now: cad 4, checks 14, docs 12, repo 7, bom 1.
- Not closable now: measurement 2, user_decision 3.
- 10 of the closable entries also carry a measurement or user-decision residual (CR-01, 02, 03, 06, 07, 17, 18, 23, 26, 30); see the end of the fix plan.

## Register: major

### CR-01 QT `cable_routes/qt` length gate moved from the installed family to a separate released pose (weakened check)
- **Sources:** CHE-1 (major, confirmed), GEO-5 (minor, confirmed), ELE missed #1 (major) [single-pass], CHE missed #6 (docs overstate the pass) [single-pass]. **Severity: major. Kind: latent (undisclosed). Push blocker PB-1.**
- **Evidence:**
  - Delivered `harness_rules.min_route` (about lines 628-645) returns `released_minimum_curve` + branch whenever that curve is present. The curve is `signal_routes.qt_released`, which is the old top56/low38/cross65 route (old family minimum 160.468 mm).
  - `FAMILIES['qt']` changed from var top 56..87.5 to var low 44..55.2. The module docstring and the comment at :174 still state the r7 rule: judge at the shortest member of the family's own route.
  - Committed compact-Kowa row: installed family min 195.919 + branch 43.072 + allowance 25 = **263.99 > 240 (fail)**. Released pose: 203.54 + 25 = 228.54 (pass).
  - At bdfd44f the row failed (top run at Z79.2 hit the HDMI U, 5.10 mm3).
  - `test_fxh_harness...test_the_stored_family_cannot_replace_the_released_reach_pose` asserts the row fails without the released curve.
  - `test_recompute_and_minima` keeps `mins['qt']==203.54` with a stale "top-run family" comment.
  - `EXPECTED_FAILING` drops `cable_routes/qt`. REVIEW.md:315 says "passes its installed geometric screen". START-HERE says the harness results "remain".
- **Physical consequence:** a 240 mm lead (BOM 250 +/-10) sits at low = 54.69 against the 55.2 bound. That leaves about 1 mm of length adjustment instead of the 25 mm r7 allowance.
  - The move from the stored Z90.5 run to the released Z56 pose passes the HDMI U apex (y -22.35) and has not been swept.
  - GEO-5 magnitude, corrected by the verifier: about 0.05 mm (OD) / 0.25 mm (capsule) of ribbon deflection, not 0.6 mm. The physical risk is low, because the ribbon is flexible.
- **What is legitimate:** the other two QT rows (`mate_reach/qt_enc`, `cable_stow/qt`) and the interference fixes are real. They clear the bdfd44f Pi crossing (7.27 mm3) and the HDMI hit.
- **Fix (checks):**
  - Gate `cable_routes/qt` on the installed family again; the row fails honestly. Expected harness result 29/13/20 (derived, not re-run).
  - Report the released pose as a separate, named row (info/HOLD), with its own reachability or transition sweep (GEO-5).
  - Restore `cable_routes/qt` to `EXPECTED_FAILING`.
  - Make `test_recompute_and_minima` pin the installed-family minimum (238.99). This makes the test stricter.
  - Correct REVIEW.md:315 and the comments in `test_harness_checks`.
  - Re-run the harness lane for all variants, then run reconcile and rebuild the guide (harness_rules.py, harness-checks.json and REVIEW.md are guide-bound).
- **Residual (user decision):** re-route the stored family to keep the 25 mm allowance, specify a longer QT lead, or explicitly relax the allowance for stored loops as a recorded relaxation.

### CR-02 Bonded-stub check models tilt about x only; a yaw of the same 0.1 mm film variation fails the catch window
- **Sources:** GEO-1 (major, confirmed by the verifier's own probe `geometry-verify/v1_stub_refute`). **Severity: major. Kind: latent. Push blocker PB-2.**
- **Evidence:**
  - `model.py:234` tenon h 3.5 -> 10 mm. Tenon width unchanged at 3.1 mm.
  - `j7_collar_checks.py:451-453` defines five STUB_CASES (x +/-0.1, film +y, two tilts about +X); `:466` sets ang = atan(0.1/h). `study_catch.py` / `catch-h10.json` used the same five.
  - Case Y2 is a yaw of atan(0.1/3.1) = 1.848 deg about the datum +X edge. It fits inside the clearances (0 mm3 overlap; the wrong-direction yaw overlaps 1.55 mm3, so the probe is sensitive). Results: 0.078 at s0.00 and s0.25, 0.087 at s1.25, 0.129 at s3.00. **FAIL against the unchanged 0.10 rule.**
  - All committed audits still report 130/130 stub passes. The coupon gate (MEASUREMENTS row 28) checks only "the current specified tilt/BFAR cases".
  - The main session rated the same mechanism (VN-24) major in its own FINAL-STATUS.
- **Fix (cad):**
  - Add yaw cases (and roll about y) to STUB_CASES with the stated film basis. This adds a check and relaxes none.
  - Restore margin with geometry: recess the stub catch face +Y by 0.05-0.1 mm (stub only; this is FINAL-STATUS option 4.2), widen the datum in x, or add a second datum.
  - Re-run first-contact and window rows for all variants, and confirm that catch engagement is still met.
  - **Needs re-export.**

### CR-03 Catch margin is 0.006 mm; the pocket allows twice the modelled tilt, and the written seating instruction produces that tilt
- **Sources:** GEO-2 (raised to major by the verifier), CHE-2 (minor, confirmed), GEO missed #1 (major) [single-pass]. **Severity: major. Kind: existing. Push blocker PB-2 (together with CR-02).**
- **Evidence:**
  - Pocket clearance `TAB_CATCH_POCKET_CLEAR` y = 0.2 (`model.py:239/253`), with the -Y face as datum.
  - T02 (0.2 mm over 10 mm, 1.146 deg, joint-edge pivot) is feasible: 0 overlap at 0.2 mm, while 0.25 mm overlaps 0.15 mm3. Its worst gap is **0.084** at s0, s0.25, s1.25 and s3.0 (FAIL).
  - steps.py:94 and ASSEMBLY-VERTICAL.md:134 (unchanged since bdfd44f) say only "stub pressed toward the camera axis (-Y) onto the pocket datum while it cures". The push lands on the stub body below the joint plane, so the couple rotates the tenon top +Y until it meets the pocket wall, which is exactly T02.
  - The pocket opens downward (-Z), so gravity also unseats the stub. No cure orientation or fixture is specified.
  - The coupon seating gate exists (MEASUREMENTS row 28), but there is no per-build check.
- **Fix (cad + docs):**
  - Rewrite print_inserts and the guide: cure the tub inverted, with a +Z seating load on the joint face, and use a fixture that holds the datum face flat rather than a push on the stub body.
  - Add a per-build feeler/gauge check of both catch-face positions and of joint closure.
  - Add T02 to STUB_CASES, or close it with geometry (the CR-02 recess, or a reduced y clearance).
  - **Needs re-export** (shared with CR-02).
- **Residual (measurement):** the as-bonded tilt on the bonded-catch coupon.

### CR-04 CSI FPC links the camera in the body to the complete Pi module outside it through six build ops; the machine model and the test lock in an incomplete HOLD set
- **Sources:** ELE-2 (major, confirmed), CHE-8 (minor, confirmed). **Severity: major. Kind: latent.**
- **Evidence:**
  - The `camera_fpc` endpoints changed. At bdfd44f: cam = optics_bench, pi = evf_mate (after carrier_in). At 1b59395: cam = camera_fpc_mate (op 2), pi = module_bench (steps.py:289).
  - `supported_groups=['module']` exists only on `camera_fpc_mate`. The new lint allowance is at steps.py:896.
  - `flexible_scope()` returns {camera_in, carrier_in}, and `test_assembly_state.py:212` asserts exactly that set. The verifier's rerun gives 11 OK.
  - s_c4_start, lens_in (body on its side), lens_float (J7-R float check), eyepiece_in, evf_in and module_staged run with the module hanging on 200 mm of FPC.
  - The only mitigation is prose in the ASSEMBLY-VERTICAL overview (:112-115) and steps.py:86-87.
- **Risks:** CSI latch strain, FPC crease or trap at evf_in, and ESD. A loaded FPC can also bias the floating camera during the J7-R float check (user rule: the camera touches no printed part in the final pose).
- **Fix (checks):**
  - Declare module support and an FPC HOLD on every op from camera_fpc_mate to carrier_in.
  - Extend the test to the full set, which makes it stricter.
  - Restrict `supported_groups` to the declared prop op.
  - Alternatively, restore a sequence that mates one end after insertion.
  - Changing steps.py re-binds the main audits for 3 variants and the FP-07 driver record. **No re-export.**

### CR-05 G-W5 drop model uses a 1.0 mOhm XT30 loop, below the datasheet maximum the delivery itself cites; joints are charged 0
- **Sources:** ELE-1 (major, confirmed), ELE missed #3 (joints charged 0 in the gating model) [single-pass]. **Severity: major. Kind: existing (r7 heritage, layout.py:620 at d38468e).**
- **Evidence:**
  - `harness_rules.py:37` sets `xt30_mohm=1.0`.
  - power-options/README.md:84,125 and termination-options.json cite Amass XT30U <= 1.2 mOhm per contact, scope unresolved.
  - `make_bom_vertical` drop_note calls the model "source-bound".
  - At a 1.0 loop: 0.16254 V, max path 225.4 mm, cut-off raise 0.01254 V (WIRING section 8). At a 2.4 loop: 0.17458 V, 182.6 mm, 0.02458 V, and the nominal lo case fails too (0.15481 V).
  - A 225 mm path passes at 1.0 (0.14988 V) and fails at 2.4 (0.16192 V).
  - The row already fails, so there is no false pass today. The data for user decision 4 is understated.
- **Fix (checks; stricter only):**
  - Gate at the 2.4 mOhm loop, or report 1.0/1.2/2.4 with the gate at 2.4.
  - Add a named joint reserve: 2 fuse-splice joints and 2 X1203 pad joints.
  - Update the TestDrop expectations (stricter) and the WIRING decision-4 data. Remove "source-bound".
  - Harness re-run and guide rebuild. The 0.150 V limit is unchanged.

### CR-06 Evidence regenerated on Linux; the documented Windows inspect path cannot pass, and Fujinon/original mesh caches exist nowhere
- **Sources:** REPRO-01 (major, confirmed), REPRO missed #3 (export_cache status exit 3 says the caches are rebuildable) [single-pass]. **Severity: major. Kind: existing.**
- **Evidence:**
  - All 3 manifests record linux-x86_64 (294220bc / e3a652e7 / 0b467d10); at bdfd44f they were win32-amd64.
  - On Windows, `regenerate` rebuilds only 7/45 meshes byte-identically. The vertex coordinates agree to 1.4e-14; face index order differs.
  - Results on Windows: `export_cache status` exit 3, `review_docs_audit --check` 1, `reconcile --check` 1 (committed_evidence_stale), `make_coverage --check` 1, `test_coverage_gates` red.
  - The committed review-docs-audit (106/106/109 files, none missing) was produced with all three Linux caches present, but only the Kowa caches were shipped.
  - export_cache.py:12-14 and REPRODUCE.md:63 call platform differences "last-digit formatting". The lock file names Windows `8mm/.venv-cad` as the reference interpreter.
- **Fix (repo):**
  - Regenerate the full export and evidence chain on the Windows reference runtime, as bdfd44f was. Shipping Linux caches for the alternatives is impossible because none exist.
  - Correct the wording: tessellation order is platform-dependent.
  - Make `export_cache status` compare `runtime.platform` and report cross-platform caches as not regenerable (exit 1 with the reason).
  - Do not relax any binding. **Needs re-export** (combine with CR-02/03).

### CR-07 Structural `--check` fails on Windows over a 1e-16 centroid (`test_windows_smoke` red)
- **Sources:** REPRO-02 (major, confirmed). **Severity: major. Kind: existing.**
- **Evidence:**
  - update_concealed_vent_structure.py:301 compares exact text.
  - base_grip `centre_mm[1]` is 1.6918e-16 on Windows and 1.6668e-16 on Linux, from importStep().Center() (:176-179).
  - The file was Linux-regenerated in 1b59395. The FIX-LOG claim "exit 0" holds only on Linux.
- **Fix (repo):** regenerate on Windows with the CR-06 chain.
- **Residual (user decision):** canonicalising float output before the comparison (snap |x| < 1e-12, fixed precision) changes a check's comparison rule, so it needs explicit user approval.

### CR-08 Records the delivery did not refresh fail 4 test files on any platform
- **Sources:** REPRO-03 (major, confirmed), CHE missed #2 (driver record) [single-pass], CHE missed #3 (C2 record) [single-pass]. **Severity: major. Kind: existing.**
- **Evidence:** these files still bind the old hashes:
  - `c2/main-c2-compact-kowa_lm6hc.json` and `fp08/j7-compact-kowa_lm6hc.json`: manifest dbea5ca5 / state model 5387da30
  - `fp07/driver-compact-kowa_lm6hc.json`: state model 5387da30
  - `history/stale-selected-reports-2026-10-10/INDEX.json`: dbea5ca5

  The current values are 294220bc / 7e08f11a. The change to `test_driver_checks` is stricter, not weaker. The straight-driver record therefore has not been re-proven for the changed sequence.
- **Fix (checks):**
  - Re-run `verify_candidate.py --only` for c2, j7 and driver against the selected manifest and confirm zero straight-driver failures.
  - Update the INDEX binding. Do not edit test expectations.
  - Do this after any re-export.

### CR-09 Publication-state documents become false on push, and carry agent-to-agent chatter
- **Sources:** PUB-1 (major, confirmed), PUB missed #1 (REVIEW.md is guide-bound) [single-pass]. **Severity: major. Kind: existing. Push blocker PB-3.**
- **Evidence:**
  - README.md:29, PUBLISHING.md:5/:13, candidate README.md:15/:28/:32, REVIEW-HANDOFF.md:3 ("No message is being sent to Claude") and REVIEW.md:24 say the work is unpublished, local-only, and that the user pushes later.
  - REVIEW.md (aeab7be0) is bound in guide-receipt `sources`. Editing it trips the `evidence_rules.py:737-738` binding failure unless the guide is rebuilt.
- **Fix (docs):**
  - In the publishing commit, rewrite these lines as a factual publication record: branch, commit, date, base bdfd44f, and that another agent authored 1b59395.
  - Remove the chatter about push authority and messaging Claude.
  - Edit REVIEW.md:24 only together with a guide rebuild (a rebuild is required anyway).
  - Rerun `review_docs_audit` and `check_links_vertical` through run_locked.

## Register: minor

### CR-10 The reviewed agent wrote into the independent reviewer's record folder
- **Sources:** CHE-12, REPRO missed #2, PUB missed #3, PUB-9 (info). Kind: existing. **Push blocker PB-4.** Closable: **docs**.
- **Evidence:**
  - `review-2026-10-10/FIX-LOG.md` gains 9 unmarked 2026-10-12 entries by "dot". One says "Structural write and --check each exit 0", which is false on Windows (CR-07).
  - The `review-2026-10-10/fp12/flow-network-baseline*.json` regression pins (VN-36) were rewritten by `review-2026-10-12/hot-plenum/refresh_flow_baselines.py`. rel_tol 1e-6 is unchanged and now asserted, and the reason chain trial4 -> trial3 -> FP-11a is kept.
  - check-scope and plenum figures reproduce exactly from a Windows re-export (REPRO-09), so the re-pins match the reproduced geometry. No one compared them independently.
- **Fix:**
  - Mark the 2026-10-12 entries "authored by the corrective agent (unverified by reviewer)" and add the Windows result, or move them to `corrective-2026-10-12/`.
  - Re-verify the fp12 baselines against the reproduced flow numbers before keeping them.
  - Record the provenance in PUBLISHING.

### CR-11 REVIEW-FIXES-STATUS.md and FINAL-STATUS.md misdescribe the branch tip
- **Sources:** PUB missed #2 [single-pass]. Closable: **docs**. Part of PB-3.
- **Fix:** add a dated header stating that the file describes bdfd44f, superseded on this branch by 1b59395 and the publishing commit. Keep the body as history.

### CR-12 Fujinon and original full audits came from an unlocked, concurrent, Linux-only lane run by a helper that is not the committed one
- **Sources:** REPRO-06 (confirmed), REPRO missed #1 [single-pass], CHE-11 (info) [unverified]. Kind: existing. Closable: **checks**.
- **Evidence:**
  - `run_isolated_rigid.py` starts `verify_candidate` with `subprocess.Popen` and has no lock code. It reads `/proc/meminfo`, so it cannot run on Windows.
  - The primary Kowa audit finished at 03:12:46Z, inside the Fujinon run (02:45:43-03:13:38Z), so two CAD audits ran at once. This breaks the one-lock rule.
  - Receipt `helper_sha256` 0e13cd5b is the `.executed.py.txt`. The committed b7218ce4 adds validate_result and a fresh-workspace guard after the fact; the tests cover those guards.
  - The receipt keys were rewritten after the runs.
  - The reports do bind the current verifier, steps and manifests.
- **Fix:**
  - Re-run both variant audits serially through run_locked.py (`verify_candidate.py --variant`). This happens anyway with the CR-06 re-export.
  - Label `run_isolated_rigid.py` non-standard/Linux-only and remove it from the documented path.

### CR-13 Stale test pins: J4 O_EQUAL/O_SEVENTY, fx_fixup literal, refit fixture
- **Sources:** REPRO-04 a/c/d (confirmed), CHE missed #4 (J4 part) [single-pass]. Closable: **checks**.
- **Evidence:**
  - `test_check_scope` pins 0.982164/1.375030; the committed values are 0.9819834/1.3747768 (more than places=4 apart). The J4 envelope is unchanged at 1.00 N m.
  - `test_fx_fixup` searches for the literal `frange(16.05, 42.95, .5)`. The new sampling is a superset and `TOL_MM2` is unchanged.
  - The `test_refit_state` fixture is shifted by the new leading module_bench op. Shifted by one op, it raises CAMERA_RETAINED again.
- **Fix:**
  - Re-pin J4 from the manifests (after re-export) with a review note. This is a value tracking geometry; no limit changes.
  - Update the literal check to the new expression.
  - Index the fixture on `order.index('camera_in')`.
  - The refit-route question itself is CR-17.

### CR-14 The critical-feature probe for the tenon-pocket +X wall no longer measures the thin wall
- **Sources:** REPRO-04 b (confirmed), CHE missed #1 [single-pass]. Kind: existing. Closable: **checks**.
- **Evidence:**
  - `tub_stock_tenon_pocket_wall_xp` measured 1.5 at bdfd44f and 7.0 at 1b59395, in all variants; xm stays 1.5.
  - The probe z = SPLIT_Z + (h+0.1)/2 = 88.55 (`critical_features_vertical.py:311`) now lands in the panel-screw boss column.
  - `test_critical_features_cf` fails (7.0 != 1.5). The delivery did not run it.
- **Fix:** probe the thinnest z between the joint plane and the boss underside, or take the minimum over the pocket height. Keep the design value at 1.5 and re-run print checks. **Do not re-pin to 7.0.**

### CR-15 New scripts break the cross-platform I/O lint and the deterministic-STEP rule; bound study STEPs carry wall-clock stamps
- **Sources:** REPRO-05 (confirmed), PUB-8 (confirmed), CHE missed #4 (lint part) [single-pass]. Closable: **repo**.
- **Evidence:**
  - 8 lint hits: `aggregate_status.py:59` (backslash keys on Windows), `inspect_vendor_models.py:24,62`, `record_post_guide_check.py:43,62,88`.
  - `probe_remedy.py:163` writes STEP raw and is not in RAW_STEP_WRITERS.
  - Tracked `power-options/variant-step/tub.step` (2026-10-12T11:19:14) and `base_grip.step` (11:19:35) are bound in `factory250-remedy-cad.json`. The other 37 STEPs use the 1970 stamp.
- **Fix:**
  - Use rel_posix and the cv_io helpers in the three scripts.
  - Route probe_remedy through `export_cache.export_step` (STEP_STAMP), regenerate the two STEPs, and rebind the receipt.

### CR-16 `termination_options.py --check` fails on Windows (unrounded sin/cos products, exact text compare)
- **Sources:** ELE-11 (confirmed). Closable: **repo**.
- **Fix:** round the derived floats at generation (as `reproduce.py` does with round(...,6)), regenerate, and keep the exact comparison. FACTORY-LEAD-STUDY.md:202 documents this command.

### CR-17 The service route contradicts the new FPC build order
- **Sources:** GEO-4 (confirmed), ELE missed #2 [single-pass], REPRO missed #5 [single-pass]. Kind: existing (HOLD-marked). Closable: **checks**, with a user-decision/measurement residual.
- **Evidence:**
  - `svc_module_unplug` (steps.py:364-371) has `reverse_of=['evf_mate']`, but evf_mate no longer connects camera_fpc; module_bench does. The lint does not catch this.
  - The remate at module_bench says "do not repeat cooler installation", while the build seats the Pi end before the cooler.
  - `route_refit('camera')` now starts with module_bench.
  - MEASUREMENTS row 12 does not say "with the cooler fitted".
- **Fix:**
  - Set `reverse_of` to module_bench.
  - Add a lint check that each service disconnect's `reverse_of` op actually connects the token.
  - Document that module or camera service may need the cooler off if the HOLD fails.
- **Residual:** the CSI strategy (user decision), and latch access with the cooler fitted (measurement).

### CR-18 Reconciler evidence rule changed: blocked receipts are written, and `source_and_export_hashes_verified` is narrowed
- **Sources:** CHE-3 (confirmed). Closable: **checks** (rename or restore the field), with a user-decision residual.
- **Evidence:**
  - `--record-blocked` replaces the FP-04 rule "nothing is written while any gate fails".
  - The field now means "no source/export failures"; CHECKPOINT flips false -> true while the status is blocked.
  - `make_coverage_vertical.py:276` consumes the field. There are disclosure fields (evidence_gates_pass=false), but there is no user decision.
- **Fix:** rename it to `source_export_identity_verified`, or restore the old meaning and add the new field separately.
- **Residual:** the user decides whether to keep `--record-blocked`.

### CR-19 The original-storage plenum cavity-intrusion check has no valid reference and is not gated
- **Sources:** CHE-4 (confirmed). Kind: existing (documented). Closable: **cad**.
- **Evidence:** `original-kowa shadow-plenum` is 48/1/21 (8893.78 mm3 undeclared) against the compact export18 tub (`historical_tub_sha256` dc81c424 is identical). Only compact is gated.
- **Fix:** build a variant-matched pre-plenum original reference, rerun `verify_shadow_plenum`, and add the report to the variant gates. This is one CAD job; no full re-export.

### CR-20 The front-mouth print hold is stale after trial4
- **Sources:** CHE-9 (confirmed). Closable: **docs** (BOM generator).
- **Evidence:** `BOM-VERTICAL.md:15` and `make_bom_vertical.py:469` state the trial3 "Z5..40 / about 35 mm bridging" hold. The reconciler hold is generic. Trial4 spans are 15.4/26.8/8.4 mm. REVIEW.md:7 says Z49..58; the aperture is Z49.6..58.
- **Fix:** restate the hold for trial4 in the BOM, the reconciler and REVIEW, then rebuild the guide (BOM and REVIEW are guide-bound).

### CR-21 Delivered test evidence is partial: 7 changed test modules have no current full receipt
- **Sources:** CHE-10 (confirmed), ELE-5 (confirmed; count corrected 8 -> 7). Closable: **checks**.
- **Evidence:**
  - `software-checks/summary.json` covers 7 suites, "not the full suite".
  - `test_assembly_state`, `test_driver_checks`, `test_evidence_tooling` and `test_harness_checks` (which carries the EXPECTED_FAILING change) have no receipt.
  - `test_check_scope` is hashed but was never run. `test_fx_fixup` and `test_plenum_trial2` are partial at the current hash.
  - In the repro run, 14 of 39 candidate files did not pass: 10 on any platform, 2 Windows-only (coverage_gates, windows_smoke) and 2 environment-limited (repo_hygiene, repo_eol).
- **Fix:** after all fixes, run the full candidate suite through run_locked on Windows and receipt it with source hashes.

### CR-22 The lock pins pypdf 6.1.1 for a reference interpreter that lacks it
- **Sources:** REPRO missed #4 [single-pass], CHE-10 (pypdf part), REPRO-08 (info). Closable: **repo**.
- **Evidence:**
  - pypdf moved from optional to "pinned-in-candidate", but `8mm/.venv-cad` has no pypdf.
  - `test_candidate_pins_match_installed_versions` errors.
  - `build_shadow_structural_pdf.py` imports pypdf unconditionally, so the structural PDF rebuilt in 1b59395 cannot be rebuilt on the declared reference interpreter.
- **Fix:** install pypdf 6.1.1 in a copy of the reference venv and record the overlay. Or declare the PDF build optional/Linux-only in the lock and REPRODUCE.md. Changing the user's venv is a user call.

### CR-23 The 10.1 mm blind tenon pocket has no adhesive vent; seating depth is not modelled
- **Sources:** GEO-3 (confirmed, partly overstated). Kind: latent. Closable: **cad**, with a measurement residual.
- **Evidence:**
  - Pocket 60.0 mm3, tenon 49.6 mm3, gap 10.4 mm3 (was 4.0). The only exits are 0.1/0.2 mm side gaps along 10 mm.
  - All STUB_CASES have dz = 0. Nothing is under the start pose.
  - Coupon seating is recorded (MEASUREMENTS row 28), but there is no per-build check.
- **Fix:** add a vent groove on the tenon +Y face or the pocket end, a dosing note, and a seated-depth gauge check. Combine with CR-03. **Needs re-export** (shared).
- **Residual:** hydraulic stand-off can only be settled on hardware.

### CR-24 The factory-lead (CAB0244) acceptance budget charges 0 for the known joints
- **Sources:** ELE-3 (confirmed). Closable: **docs**.
- **Evidence:** r20 max 10.3235 mOhm/m uses fixed = drop(0, 2.4) and no joint term. 4 non-factory joints remain: 2 fuse splice and 2 pad.
- **Fix:** state it as a combined wire-plus-joints budget, or reserve an explicit per-joint allowance and name the joints.

### CR-25 TE 31819 splice dimensions are non-conservative
- **Sources:** ELE-4 (confirmed against te.com). Closable: **docs**.
- **Evidence:** the JSON gives OD 4.06 / ID 2.26 mm; TE gives OD 4.19 / ID 2.16.
- **Fix:** use the larger OD and the smaller ID in studies, with TE as the cited source.

### CR-26 BOM J2 class text (28-24 AWG, two colours) is not reconciled with the J2 proposal
- **Sources:** ELE-6 (confirmed). Closable: **docs** (pointer), with a user-decision residual (decision 13).
- **Evidence:**
  - V-28/V-28S say 28-24 AWG, but the proposed contacts take 20-24 AWG with 1.85 mm maximum insulation.
  - `J2_PAIR_CLASS` core OD is 1.6 mm. WIRING-VERTICAL.md:130 requires two colours; path A is one colour per half and path B is all black.
- **Fix:** add a pointer in V-28 to the limits and the colour conflict, pending decision 13.

### CR-27 The separately printed `tab_catch_insert` has no BOM line
- **Sources:** ELE-7 (confirmed). Closable: **bom**.
- **Evidence:** the manifest lists 10 production prints; the CSV has 9 P- rows. The insert appears only in the P-tub note and as the V-68 layout_id.
- **Fix:** add a P-tab_catch_insert row (or a section-G included-piece row) with its material, then rebuild the guide.

### CR-28 The push adds three blobs over GitHub's 50 MiB warning; `pi5.step` is re-versioned only by float noise
- **Sources:** PUB-2 (confirmed, corrected), PUB missed #5 [single-pass]. Closable: **user_decision**.
- **Evidence:**
  - Three `assembly.step` files, 67.7-68.2 MB, will warn; none exceeds 100 MB.
  - `pi5.step` at 49.58 MiB is under the warning threshold. It differs by 7 bytes on line 260851, and its sha is bound in 15 files.
  - The push adds 332 MB raw / 59 MB packed.
  - Any follow-up commit still publishes these blobs; only rewriting the unpublished 1b59395 avoids that, and the package cites that hash.
- **Fix:** accept for this push (recommended). Later, normalise OCCT floats or move the regenerable STEPs to LFS or release assets.

### CR-29 Two `.log` evidence files are force-added despite `.gitignore *.log`; one duplicates another evidence file
- **Sources:** PUB-3 (confirmed). Closable: **repo**.
- **Evidence:** `fxh-regression.log` is the same blob as `software-checks/fxh_harness.txt`. `post-guide-build-order-check.log` is bound at :42.
- **Fix:** add `!` negations, or rename to .txt and rebind. Keep a single fxh evidence lane.

### CR-30 Unreferenced or superseded QA images are tracked; guide page_images are cache-only
- **Sources:** PUB-4 (confirmed). Closable: **repo**, with a user-decision residual (retention).
- **Evidence:**
  - `qa-oct12/contact-01..10.png` (5.0 MB) are new in 1b59395 and unbound.
  - The old `guide/out-concealed-vents/qa/` (40 files, 13.9 MB) and `structural-review/tmp/pdfs` have been public since 9ced753.
  - The 38 page_images are git-ignored. `export_cache.guide_report` already classifies them as cache.
- **Fix:** remove or historise the unbound images with a note, and label page_images cache-only.

### CR-31 The research cites an unofficial full-text copy of a paywalled Elsevier paper
- **Sources:** PUB-6 (confirmed). Closable: **user_decision**.
- **Evidence:** S10 links `dataset-dl.liris.cnrs.fr/...j.ijadhadh.2020.102602.pdf`, while S9 is the DOI. Crossref shows no CC licence. The `.txt` is bound by `guide-receipt:67` and `structural-supplement-pdf-receipt:19`.
- **Fix:** drop S10 or point it at the DOI (requires a rebind and guide rebuild), or accept it, since it is a link only.

## Register: info

| ID | Sources | Item | Closable | Action |
|---|---|---|---|---|
| CR-32 | CHE-5 (downgraded to info) | Verifier mouth rectangles now come from `VG.HOT_FRONT_Z`/`hot_front_apertures()`, so the measurement is not independent of the design declaration. Nothing is hidden today: the saved-STEP free area of 274.2 equals the sum of the apertures. | checks | Optionally keep a fixed outer rectangle and assert there is no free area outside the declared apertures. |
| CR-33 | CHE-7 (downgraded to info) | `guide/README.md` STALE banner dropped from StaleGuideBanner, and no replacement test ties it to the `build_guide_vertical.py` outputs. Dropping the old assertion was correct. | checks | Add a banner-to-builder assertion. |
| CR-34 | GEO-6 [unverified] | The front lip bridge is now 26.8 mm (rule 30 unchanged, passes). The upper aperture is 0.7/1.2 mm from lens_collar/s_c4, so exhaust heating of the collar pinch clamp has not been assessed. | measurement | Include the 26.8 mm lip in the plenum coupon. Add collar temperature to the thermal gate. |
| CR-35 | REPRO-07 (info; main session's own wording) | FINAL-STATUS.md:292 and FIX-LOG quote `audit_cloud_release.py --final-release` without `--out`. Every instruction document gives the full form. | docs | Quote the full command. |
| CR-36 | PUB-7 (downgraded to info), ELE-8 [unverified] | J2 `sources.json` local name 2147611101 does not match the URL 2147612105. Vendor files are git-ignored, so the bounds need a re-download. The Anderson SBS Mini datasheet URL returns 404. Commands use the POSIX venv path. | docs | Fix the name, document the re-download, record a working URL, and give both venv paths. |
| CR-37 | ELE-9 [unverified] | Package START-HERE says the harness results "remain" 30/12/20, but they changed from 27/15 (the three QT rows flipped). The package is out of scope (do not modify). | docs | State the 27/15 -> 30/12 transition (and the CR-01 restoration) in the repo's REVIEW/PUBLISHING records. |
| CR-38 | ELE-10 [unverified] | Neither J2 sourcing path can be stored uncut: intact leads give a 2104-2813 mm3 loop against 1999.2 mm3 capacity. | user_decision | Add this to decision 13 and the J2 proposal. |
| CR-39 | PUB missed #4 [single-pass] | The committed research PDF (59,517 B) is a re-render of the supplied one (84,480 B). The text is identical; the DOCX is byte-identical. | docs | Note "re-rendered copy, identical text" in RESEARCH-INTEGRATION.md. |
| CR-40 | PUB missed #6 [single-pass] | The dated routing snapshot `hdmi-export17-selected-20261009-0704` holds current-run results (a pre-existing pattern). | docs | Add a README note, or write current results elsewhere. |
| CR-41 | CHE-6 [unverified, justified] | The fx_fixup monotonicity tolerance was replaced by an arithmetically derived quantisation bound (about 2.3e-4 mm2, all-port cuts only), with a negative test. No acceptance gate uses it. | checks | No change. Record only. |
| CR-42 | REPRO-08 (env part) | `test_repo_eol` cannot be judged in a linked worktree. | measurement | Run it in a normal clone before push. |
| CR-43 | PUB-11 | The official `check_links_vertical.py` has not been run on 1b59395. The ad-hoc check found 0 broken links in the 24 changed .md files. | checks | Run it through run_locked before push. |

## Appendix A: refuted findings

| ID | Claim | Why refuted |
|---|---|---|
| PUB-5 | Hot-path 509.999996 mm2 shown as "510.0 / 510" overstates a tolerance-only pass. | check-scope `cut_composition`: port 510.0 / mouth 0 / internal 0. The min cut lies wholly on the wall-port faces (509.9999999999922), and the 4e-6 shortfall is below the recorded `selected_cut_abs_error_bound_mm2` = 0.000117. The rounding is correct. `extracted-text.txt:116` gives the wall-slot requirement, not the capacity. The tolerance of 0.002 is unchanged since bdfd44f. |

## Appendix B: verifier corrections to confirmed findings (merged text above uses the corrected form)

- **REPRO-01:** the "values differ by ~2000" refers to face indices only. Vertex coordinates agree to 1.4e-14 mm.
- **REPRO-07:** the short form is only a result label in the main session's own bdfd44f records, so this is info, not a broken procedure.
- **CHE-5 and CHE-7:** downgraded to info (see CR-32, CR-33).
- **GEO-2:** a coupon seating/tilt measurement exists (MEASUREMENTS row 28). What is missing is a per-build fixture or check. Raised to major because the written instruction produces the failing pose.
- **GEO-3:** "seating not gated" is partly wrong (coupon row 28).
- **GEO-5:** the HDMI transition deflection is about 0.05-0.25 mm, not 0.6 mm (inner wall at Y-25.5).
- **ELE-2:** prose mitigation exists in the ASSEMBLY-VERTICAL overview (:112-115) and steps.py:86-87. The machine model, the per-op text and the guide do not carry it.
- **ELE-5:** 7 modules, not 8, lack a current full receipt (`test_build_order_docs` has one).
- **PUB-1:** REVIEW.md:24 does not name the branch. REVIEW.md is guide-bound.
- **PUB-2:** only the 3 assembly STEPs exceed the 50 MiB warning (pi5 is 49.58 MiB). The pi5 sha is bound in 15 files, not 4.
- **PUB-3:** the post-guide log is bound at :42, not :41. No in-repo script writes `fxh-regression.*`.
- **PUB-4:** the contact sheets total 5.0 MB. The old qa/ and tmp/pdfs have been public since 9ced753.
- **PUB-7:** downgraded to info.
- **Review-process note (not a repo defect):** the geometry reviewer's P2 JSON records the wrong panel screw (z 8.3). The 3.0 mm pocket-to-bore wall is right by hand (bore y 13.1 vs pocket ymax 10.08), but the probe has to be re-run with the z 91.7 screw before it is quoted as evidence (GEO missed #2).

## Appendix C: confirmed (no action)

- **REPRO-09:** a Windows re-export reproduces compact-Kowa verification 633/1/32 (only pi5/cooler 79.902671), roll_catch 188 pass/1 info, 130/130 stub rows, min worst_gap 0.106, harness 30/12/20 with an identical failing set, check-scope 36/0/14, hot path 509.999996, cold 420, plenum 49/0/21, outlet 4/0, and print 161/0/7. All 0 status differences, 0 drift above 1e-6.
- **REPRO-10:**
  - identity: HEAD 1b59395, tree 4a71efaf
  - generators pass; two Windows exports are byte-identical; make_corrected_pi is byte-identical
  - r7 suite 82/82, 73 OK, final-release audit passes (56 gates open)
  - J4 envelope 1.00 N m; guide PDF d383b996 and structural PDF 59a8771f equal their receipts and the package copies
  - Fujinon print spot check 0/67 differences
- **PUB-10:** no secrets, PII, local paths or vendor redistribution. The research is in the agent's own words, with no images. 0 CRLF; `.gitattributes` is unchanged.
- **PUB-11 (numbers):** every report count and binding in the docs agrees with the JSON reports; CHECKPOINT 5/5 bindings OK.
- **Check integrity:** the r7 roll-catch rule, the 510 mm2 requirement and its tolerance, the print rules, the accepted info/print/harness sets (`ER.EXPECTED_HARNESS_FAILURES` = {}), the 0.150 V drop limit and the J2 rules are all unchanged. The J2 accounting and the driver and check-scope gates are stricter.

## Fix plan (push blockers first)

"Re-export" means the expensive Windows chain: exports of 3 variants, the batch (shadow, plenum, outlet, print, harness, structural), and serial full variant audits through run_locked. It takes about 3-4 h of wall time; the repro run took 308 s for the export and 5424 s for the shadow checks per variant. **Every re-export item below shares one re-export.** Do it once, after all CAD and steps changes, and never in parallel with another CAD job.

| # | Fix | Register | Severity | Closable | Re-export | Est h |
|---|---|---|---|---|---|---|
| FX-01 | Restore the `cable_routes/qt` gate on the installed family. Add a separate released-pose row with a transition sweep. Restore EXPECTED_FAILING. Pin 238.99 in `test_recompute_and_minima` (stricter). Fix REVIEW.md:315 and the comments. Re-run the harness for 3 variants. | CR-01 (PB-1) | major | checks | no | 3 |
| FX-02 | Catch. (a) Add yaw Y1/Y2, roll about y, and T02 to STUB_CASES, so the rows fail honestly. (b) CAD: recess the stub catch face +Y 0.05-0.1 mm and/or reduce the pocket y clearance, add a vent groove, and re-check first contact. (c) Rewrite print_inserts and the guide: cure inverted, +Z seat, a datum-face fixture, and a per-build feeler check. If the user defers the re-export, the minimum before push is (a) plus an explicit HOLD. | CR-02, CR-03, CR-23 (PB-2) | major | cad | **yes** | 6 |
| FX-03 | Publication record. Rewrite README.md:29, PUBLISHING.md, the candidate README and REVIEW-HANDOFF as a factual record. Add tip notes to REVIEW-FIXES-STATUS and FINAL-STATUS. Mark the 2026-10-12 FIX-LOG entries as the corrective agent's, with the Windows result. Edit REVIEW.md:24 only together with the guide rebuild. Do this in the final publishing commit. | CR-09, CR-11, CR-10 (PB-3, PB-4) | major | docs | no | 1.5 |
| FX-04 | steps.py FPC sequence. Add HOLD and module support on every op from camera_fpc_mate to carrier_in. Restrict `supported_groups` to the prop op. Set `svc_module_unplug.reverse_of` to module_bench, and add a lint that `reverse_of` connects the token. Extend `test_assembly_state` (stricter). Document the cooler-off service fallback. The main audits re-bind through FX-10. | CR-04, CR-17 | major | checks | no (re-binds audits) | 3 |
| FX-05 | G-W5 drop model. Gate at the 2.4 mOhm XT30 loop (also report 1.0/1.2) plus a named joint reserve. Make TestDrop stricter. Update the WIRING decision-4 data and remove "source-bound". | CR-05 | major | checks | no | 2 |
| FX-06 | CF tenon-pocket +X wall: probe the minimum over the pocket height. Keep design 1.5. Re-run print checks. | CR-14 | minor | checks | no | 1.5 |
| FX-07 | Lint fixes (rel_posix, cv_io). Route probe_remedy through `export_step` and regenerate and rebind the two study STEPs. Round derived floats in termination_options at generation. | CR-15, CR-16 | minor | repo | no | 2 |
| FX-08 | Reconciler: rename the narrowed field or restore its meaning. Keep `--record-blocked` until the user decides. | CR-18 | minor | checks | no | 1 |
| FX-09 | BOM: add a `tab_catch_insert` row and restate the trial4 front-mouth hold (BOM, reconciler, REVIEW Z49.6..58). | CR-27, CR-20 | minor | bom/docs | no | 1 |
| FX-10 | One serial Windows re-export plus the full evidence chain. It includes the structural write and the Fujinon/original full audits through run_locked. Add a platform guard to `export_cache status` and correct the "last-digit" wording. Label `run_isolated_rigid.py` non-standard. | CR-06, CR-07, CR-12 | major | repo | **yes** | 4.5 |
| FX-11 | After FX-10: regenerate the c2/j7/driver records and the stale INDEX against the new manifests (zero driver failures). Re-pin J4 O_EQUAL/O_SEVENTY with a note. Update the fx_fixup literal. Index the refit fixture on `camera_in`. | CR-08, CR-13 | major | checks | after re-export | 2 |
| FX-12 | Build a variant-matched original pre-plenum reference and gate the original plenum report. | CR-19 | minor | cad | no (1 CAD job) | 2.5 |
| FX-13 | Rebuild the guide (guide-bound sources changed). Rebuild the structural PDF (needs pypdf, CR-22). Then run `review_docs_audit`, `reconcile --check` and `make_coverage --check`. | CR-06, CR-22, CR-09 | major | repo | after re-export | 2 |
| FX-14 | Run the full candidate suite on Windows through run_locked and receipt it with hashes. Run `check_links_vertical`. Run `test_repo_eol` in a normal clone. | CR-21, CR-43, CR-42 | minor | checks | after all | 2.5 |
| FX-15 | Repo hygiene: `.log` negation or rename, unbound QA images (retention decision), pypdf declaration. | CR-29, CR-30, CR-22 | minor | repo | no | 1 |
| FX-16 | Docs batch: CR-24, CR-25, CR-26 pointer, CR-35, CR-36, CR-37, CR-39, CR-40, CR-31 (if decided). Optional tests for CR-32 and CR-33. Make guide-bound edits before FX-13. | listed | minor/info | docs | no | 2 |

**Execution order.** The table is in priority order; this is the dependency order:

1. FX-01, 02a, 04, 05, 06, 07, 08, 09, 15, 16 (code and docs, no CAD)
2. FX-02b/c (CAD)
3. FX-10 (single re-export), then FX-12
4. FX-11, then FX-13
5. FX-14
6. FX-03 (publishing commit), then push

Push recommendation, pending user decision UD-6:
- Push to a review branch, never to main.
- Keep 1b59395 unchanged, because the package cites that hash, and put the main session's fix commits on top so authorship stays clear.

Total is about 37 h, including about 4.5 h of re-export wall time in FX-10.

## Not closable now

- **Measurement:**
  - as-bonded stub tilt and yaw on the bonded-catch coupon (CR-02/03 residual)
  - adhesive hydraulic stand-off (CR-23)
  - CSI latch access with the Active Cooler fitted (CR-17)
  - front lip sag and collar exhaust heating (CR-34)
  - `test_repo_eol` in a normal clone (CR-42)
- **User decision:**
  - QT route, lead or allowance (CR-01 residual)
  - CSI build/service strategy (CR-17)
  - structural float canonicalisation (CR-07)
  - `--record-blocked` policy (CR-18)
  - large STEPs and whether to rewrite before push (CR-28)
  - LIRIS link (CR-31)
  - J2 decision 13 inputs (CR-26, CR-38)
  - QA image retention (CR-30)
  - pypdf in the reference venv (CR-22)

## User decisions needed

- **UD-1 QT:** the restored gate fails (263.99 > 240). Choose one:
  - re-route the stored family to keep the 25 mm allowance,
  - specify a longer QT lead,
  - explicitly relax the allowance for stored loops, which would be recorded as a relaxation.
- **UD-2 Catch:** approve the geometry option (stub catch-face recess, tighter pocket, or second datum) and the 3-4 h re-export now. Otherwise push with the added yaw/T02 cases failing and a HOLD.
- **UD-3 CSI strategy:** the build seats the Pi end before the cooler, while service re-mates it with the cooler on. Either measure latch access with the cooler fitted, or accept cooler removal in service. Also accept or revert the camera refit that now starts with module_bench.
- **UD-4 Evidence platform:** regenerate all evidence on the Windows reference runtime (recommended; the Fujinon/original caches do not exist), or declare Linux evidence.
- **UD-5 Structural check:** canonicalise floats (a comparison-rule change) or rely on Windows regeneration only.
- **UD-6 Push form:** push 1b59395 as delivered plus fix commits (this publishes 3 STEPs over 50 MiB and 5 MB of unbound images), or rewrite before the first push. Also choose the branch name.
- **UD-7 Large STEPs:** a later strategy (LFS, release assets, or OCCT float normalisation).
- **UD-8 Research link S10 (LIRIS copy):** drop it (needs a rebind and guide rebuild) or accept it.
- **UD-9 Reconciler `--record-blocked`:** keep it with the renamed field, or revert to FP-04.
- **UD-10 QA images:** retain or remove the superseded and unbound images.
- **UD-11 J2 (decision 13):** contact range 20-24 AWG versus the BOM's 28-24, the two-colour rule, and the measured-trim critical path.
- **UD-12 pypdf:** install 6.1.1 in the reference venv, or keep the PDF build optional/Linux-only.
- **UD-13 (inform):** gating G-W5 at the 2.4 mOhm loop is stricter. It shortens the decision-4 maximum path to 182.6 mm and doubles the cut-off raise to 0.0246 V.
