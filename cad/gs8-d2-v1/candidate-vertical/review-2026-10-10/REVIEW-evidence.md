# Evidence and check-integrity review: vertical-Pi candidate (dot, 9ced753)

Dimension: evidence. Reviewer: evidence agent, 2026-10-10. Read-only. Nothing in the clone was changed.

Scope read: `run_shadow_checks.py`, `verify_candidate.py`, `verify_shadow_plenum.py`, `verify_shadow_usb_head.py`,
`verify_csi_source.py`, `verify_wire_solids.py`, `verify_hdmi.py`, `verify_power_service.py`, `verify_print_meshes.py`,
`verify_wall_probe_context.py`, `reconcile_review_evidence.py`, `review_docs_audit.py`, `refresh_primary_evidence.py`,
and the JSON they wrote (`out/compact-kowa_lm6hc/*.json`, `out/review-docs-audit.json`, `CHECKPOINT-STATUS.json`,
`history/*`). Compared with the r7 suite (`checks.py`, `build_d2.py`, `out/checks.json`).

Probes (scratch, not in the repo): `rehash.py` (hash bindings, no CAD) and `probe_evidence.py`
(run once under `run_locked.py`; result `probe_result.json`).

## What holds up

- Every headline number in README/REVIEW/ASSEMBLY matches its JSON: main 292/1/18, cooler 79.902671 mm3,
  plenum 49/0/21, HDMI 6/0/0, FPS 332 + 9 with zero hits, power 201 poses / 659 queries, microSD 23 of 46 poses,
  hot sampled section minimum 299.4 mm2.
- The selected reports all bind manifest `53e668d4...` and their current verifier hashes.
- The reconciler asserts that the only rigid failure is `pi5/cooler`. It does not waive the failure.
- The PT-screw pilot allowances are real: the 20.3 to 21.6 mm3 overlaps equal the 1.25 to 1.5 mm pilot ring
  over the engaged length.
- Interference uses the r7 tolerance (VOL_TOL 0.05 mm3).

## Headline count

The 292 passes are 45 STEP-integrity + 45 volume round-trip + 71 source-hash rows (161 bookkeeping rows),
108 interference pairs, 10 rigid motions, 12 material rays and 1 "aperture is empty" row. Only 23 rows test
service motion or wall material. The r7 summary counted 34 categories. The two numbers are not comparable.

## Findings

| id | sev | kind | title | evidence | failure scenario | fix | closable-by |
|---|---|---|---|---|---|---|---|
| EVI-1 | major | latent | `.gitattributes` regression breaks every hash binding on a default Windows clone | r7 had `* -text` with the comment that receipts hash exact bytes. 9ced753 keeps only binary rules. This machine has `core.autocrlf=true` (system gitconfig). `git -c core.autocrlf=true checkout-index` gives `model.py` sha `0c24d237...` (manifest binds `61382452...`) and `manifest.json` `3bd82641...` (status binds `53e668d4...`). | A user clones on Windows. Every verifier asserts on source/manifest hashes and stops. The reconciler and docs audit report all evidence stale. | Restore `* -text` as the first rule; keep `-diff` on binaries. | repo |
| EVI-2 | major | latent | Manifests bind 136 gitignored mesh caches, so the committed evidence cannot be re-verified | Each manifest `files` binds `meshes/*.json` (45/45/46). `.gitignore` excludes `candidate-vertical/out/*/meshes/`. The clone lacks all of them. `reconcile_review_evidence.py:9` asserts every `files` hash and will raise FileNotFoundError. `review_docs_audit.py` would write `files.pass=false`. | `CHECKPOINT-STATUS.json` says `source_and_export_hashes_verified: true`, but no clone can reproduce that. | Commit the caches, or bind them in a separate cache manifest outside `files`. Make the reconciler rebuild caches instead of asserting on them. | repo |
| EVI-3 | major | latent | No straight-driver audit for the vertical geometry (user rule) | r7 `check_driver` (bit 6.5x40, handle 30x100, per-step audit set) is not run. No candidate script has a driver check (grep). It applies to 7 PT screws (`p_panel1-4`, `p_carrier1-2`, `p_grip`) and 4 collar M3s. `p_grip` moved 2 mm and the carrier screws are new. ASSEMBLY step 4 defers the carrier screws to "the qualified assembly sequence". | A screw cannot be reached with a straight driver at its install step. Nothing would flag it. | Port `check_driver` with the candidate install order. See probe B. | checks |
| EVI-4 | major | latent | J7-R float, roll catch and collar clamp/support are not re-established after the collar and catch changed | `model.py:195-210` changes the collar: `body_r` 30 to 25, LL foot (28,36) to (18,30), lug moved. `model.py:237-239` moves the r7 hood tab catch onto the tub roof (z to 98). No candidate script has `j7_float`, `roll_catch`, `lens_clamp`, `lens_support` or `collar_gauge` (grep). The main audit has no camera-gap rows; interference passes any overlap under 0.05 mm3, so contact passes. REVIEW.md:55 admits only that the clamp needs requalifying. | The camera touches a printed part, or lens-thread torque reaches the camera cover because the moved catch does not engage. Both break user rules. Neither would show. | Run r7 `check_j7_float`, `check_roll_catch`, `check_lens_clamp`, `check_lens_support` and `check_collar_gauge` on the candidate rows. See probe A. | checks |
| EVI-5 | major | latent | Service motions leave out obstacles that are present | `verify_candidate.py:106-107`: `carrier_out` fixes only tub/camera/adapter/EVF. It omits `xt30_pair`, although ASSEMBLY step 4 says to feed past the "XT30 body". Its bbox overlaps the sweep (z 4..9.9). It also omits `lens_collar`, `s_c1-3`, `eyepiece` and `eyecup`. `panel_out` omits `x1203_kit`, `microsd` (bbox overlaps the panel), `xt30_pair` and `usb_stick`. | A sweep passes only because the part it would hit is not listed. | Build each fixed set from the install order: every part present at that step, minus the movers. See probe C. | checks |
| EVI-6 | major | existing | The Fujinon and original-storage variants have no interference or motion audit | `out/compact-fujinon_hf6xa/` and `out/original-kowa_lm6hc/` have no `verification.json`. Only mesh, bounds and void reports exist. REVIEW.md:289 says the audits were "not rerun". r7 reached 0 fail on both lenses. | Someone builds the Fujinon variant. Lens/collar/tub interference is unchecked. | Run `verify_candidate.py --variant` on both and bind the results. | checks |
| EVI-7 | major | existing | Print bridging is unchecked; the r7 `print_overhang` check exists but was not run | No overhang check in the candidate. The tub prints outer face down with a sealed 6 mm plenum. REVIEW gives "about 35 mm" bridging as an estimate. `print-mesh-checks.json` tests only watertightness, volume and bed fit. | The tub fails to print, or traps support in the plenum. | Run r7 `check_print_overhang` on every changed printed part in its manifest pose. Keep the coupon gate. | checks |
| EVI-8 | major | existing | Harness checks are not re-established (FPC, USB feed, loom) | r7 `lead_access`, `mate_reach`, `mate_paths`, `cable_stow`, `header_housings` and `keepouts` (109 rows) have no counterpart. The candidate documents the FPC and USB feed as STOPs. | Complete service is not proven. | Port the r7 harness checks. Keep the STOPs until then. | checks |
| EVI-9 | minor | latent | CSI right-wall ray: the correction is legitimate, but it is counted as a pass and the adjacent-wall evidence is stale | The export18 ray (-80,-32..-20,50) sat in the designed 12x27 slot (`model.py` box -89..-77, z 41..68), so relocating it is fair. But `verify_candidate.py:173-175` adds an "aperture is empty" row that counts toward the 292. The only rays next to the slot are in `wall-probe-context.json`, which binds export18 manifest `c9e1e207`, not `53e668d4`. The current audit probes the wall only at X-110. See probe D. | Wall loss next to the slot would go unseen. The headline count gains a pass for a hole. | Record the aperture row as info. Add the above/ahead/behind rays to `verify_candidate.py` for the current manifest. | checks |
| EVI-10 | minor | latent | `review_docs_audit.py` cannot fail | It writes booleans and always exits 0, with no assert (`review_docs_audit.py:1-119`). Its output supports "hashes verified". | A changed source or a missing file still gives a green run. | Exit non-zero on any binding with pass=false, a missing link or a stale selected report. | checks |
| EVI-11 | minor | latent | The current runner has no run record; the plenum and outlet verifiers are not in it | `review-check-run.json` is absent. The only record is `history/shadow-first-check-run` (runner `db538169`, usb_head exit 1). The current `run_shadow_checks.py` is `a59d5f5c`. Its command list lacks `verify_shadow_plenum.py` and `verify_shadow_outlet_context.py`. `refresh_*` scripts and `final-check-run.json` log to `/tmp/...`. | The "separately executed current checker" cannot be traced to a run. | Run the current runner once on the frozen manifest. Commit the run record and logs. Add the two verifiers. Use repo-relative log paths. | repo |
| EVI-12 | minor | latent | Wire and HDMI checks are narrowed to some obstacles | `verify_wire_solids.py:15-17` loads printed parts only, so power wires are never tested against the Pi, cooler, X1203, camera or ribbon. `verify_hdmi.py:96` drops all `p_`/`s_` screws from the ribbon obstacles. The hard heads are tested only against printed parts (`:98`). | A wire through the cooler proxy, or a ribbon over a screw shank, passes. | Add COTS and hardware solids to the obstacle sets. List the exclusions in the report. | checks |
| EVI-13 | minor | latent | The info classes are broad and the reconciler does not bound them | `verify_candidate.py:79-81` makes any keepout overlap with a non-printed part info, not only its own mating port. `reconcile_review_evidence.py:69-70` checks only the fail list. | A storage reserve that starts to overlap the cooler would become a silent info row. | Restrict the keepout rule to the named mating partner. Assert the exact info id set. | checks |
| EVI-14 | minor | latent | The hot-bay area check ignores its own series section | `hot_summed_sampled_mouth_necks` passes 534 >= 510. But `hot_interior_horizontal_section_z8` = 299.4 mm2 lies between the ports (z>=16) and the 324 mm2 bottom mouth. So 299.4+210 = 509.4 < 510. It is labelled info. | The exhaust area is slightly below the stated parity. This is a margin point, not a cooling result. | Use min(mouth, series section) per branch, or state the shortfall. | checks |
| EVI-15 | info | latent | A stale hard-coded overlap number is in every manifest | `official_pi5_geometry.py:131`: "Retain 32.3614 mm3 CSI/coarse-cooler conflicts". The computed `pi5/cooler` is 79.902671 mm3. | A reader takes the wrong conflict size from the manifest. | Compute it or drop the number. | docs |
| EVI-16 | info | latent | Stale "pass" reports sit in the current output folder | `csi-access-checks.json` has status pass but binds manifest `e8648073`. The docs audit does not list it. `assembly.step` is not in the manifest `files`. | Someone cites an old pass as current. | Move stale reports to `history/`, or audit every JSON in the folder. | repo |
| EVI-17 | info | latent | Re-export changes every hash | The STEP header has a wall-clock time (`'2026-10-09T22:57:35'`). Following REPRODUCE.md re-exports and invalidates all bound evidence. The guide command hard-codes `--manifest-sha256 53e668d4...`. r7 has the same limit (not a regression). | "Reproduce" cannot regenerate the frozen hashes. | Normalise the STEP header time, or say in REPRODUCE that hashes will change. | repo |
| EVI-18 | major | existing | Active cooler/Pi overlap of 79.902671 mm3 | `verification.json` `pi5/cooler` fail. It is correctly retained and asserted. | The real cooler may not fit with the vertical CSI parts. | Measure cooler registration (MEASUREMENTS-TO-CLOSE.md). | measurement |

## r7 guarantees not re-established for the vertical geometry

driver (straight-driver audit), service_driver, j7_float, roll_catch, lens_support, lens_clamp, collar_gauge,
print_overhang, critical_features / thin_wall (r7 141 + 12 rows; candidate has 12 local rays), handling
(press fits, rest stability), lead_access, mate_reach, mate_paths, cable_stow, header_housings, keepouts (109),
evf_restraint, stack_retention, boss_geometry, inserts, engrave_groove, removals (r7 13 with service context;
candidate 10 rigid motions with partial obstacle sets), and both-lens coverage. Re-established in some form:
interference, STEP integrity, mesh/bed fit, rigid sweeps (partial), HDMI ribbon, rigid power service, FPS carry.

## Probe status (A to D)

`probe_evidence.py` was queued under `run_locked.py` at about 11:15 UTC. It was still waiting for another
agent's CAD lock at 11:55 UTC, so it never ran. EVI-3, -4, -5 and -9 stand on code evidence alone: the checks
are missing or the obstacle lists are short. The probe would show whether real hits exist. To run it later
(read-only; it writes only into this scratch folder):

`python run_locked.py -- probe_evidence.py <candidate-vertical dir> probe_result.json`

- A: minimum gap from `gs_camera` and `c_cs_adapter` to every non-lens part (J7-R float).
- B: r7-size driver cylinders on all 11 screws against every final part. Classify each hit by install step.
- C: `panel_out` and `carrier_out` swept against the omitted obstacles (2 mm step, 70 mm, +Y).
- D: rays above, ahead of and behind the CSI slot on the current tub.

## Bottom line

The candidate does not fake its numbers: every quoted figure matches its JSON, and the one active failure is
kept. Three things are weak. (1) The evidence cannot be re-verified from a clone (EVI-1, EVI-2, EVI-11).
(2) The "292 pass" headline is mostly bookkeeping rows. (3) Most r7 guarantees, including the user-rule
checks for the straight driver and J7-R float/roll catch, were never re-run for the changed geometry
(EVI-3 to EVI-8).
