# D2 vertical candidate: issue register and fix plan

Review of AubergineShallow/digital8mm-vertical-nizo at 9ced753 (on top of r7 d38468e), selected manifest 53e668d4 (compact-Kowa).
Built 2026-10-10 from seven inputs: the reproduction run and six review dimensions (physical, evidence, print-structure-thermal, electrical-bom, repo-hygiene, design-regression), each with an adversarial verification pass.
Nothing has been fixed yet. The snapshot clone is still clean (`git status` empty).

## How this register was built

- Refuted findings are dropped and listed in Appendix A with the reason.
- Confirmed and uncertain findings are kept. Where the verifier changed the severity, the verifier's severity is used.
- Duplicates across dimensions are merged. Every entry lists its source ids.
- Items the verifiers found that the reviewers missed are added and marked **unverified-by-second-pass**. Reviewer items that the verifiers did not cover are marked **not second-pass verified**.
- Every hold the candidate documents itself is included (main-audit failure, print hold, G-V-* gates in REVIEW s6, ASSEMBLY STOPs, MEASUREMENTS-TO-CLOSE rows). Section G and the coverage map in Appendix B show where each one lives.
- **Status**: *existing* means the candidate already documents it; *latent* means it does not (or documents it wrongly).
- **Closable-by**: `cad`, `checks`, `docs`, `repo`, `bom` can be closed in the repo by a later session. `measurement` needs received hardware. `user_decision` needs the user.

## Headline

- The candidate's computed numbers are honest and reproduce: main audit 292 pass / 1 fail / 18 info, the 79.902671 mm3 pi5/cooler overlap, plenum 49/0/21, HDMI 6/0, FPS 332+9, power 201 poses / 659 queries. The r7 baseline verifies on a byte-exact checkout.
- No finding survives as a BLOCKER. The plenum-roof finding was downgraded to major because the candidate already holds printing (G-V-PRINT).
- The main problems are latent:
  1. **Reproducibility on Windows is broken.** Line-ending attributes, path separators and locale encoding each break the evidence on the user's own machine. Gitignored mesh caches stop any clone from re-verifying the bindings.
  2. **Most r7 rule checks were never ported.** That includes the straight-driver audit, J7-R float, roll catch, lens clamp, print overhang and the harness checks. 161 of the 292 passes are bookkeeping.
  3. **The written build order is wrong in several places.** The camera goes in before the collar gauge (927.75 mm3 overlap). The lens is fitted after the panel closes, so the r7 turn-back step is lost. The FPS switch sequence contradicts itself.
  4. **Several printed parts fail r7's own print rules.** These are the plenum roof, all four mouths, the tub tab-catch tines, the carrier frame, the grip pocket and the collar LR foot.

## Counts

84 issues: 0 blocker, 30 major, 47 minor, 7 info. 63 latent, 21 existing.
59 can be closed in the repo now (cad 10, checks 24, docs 11, repo 12, bom 2). 25 need hardware (18) or a user decision (7). 5 findings were refuted (Appendix A).

## Index

| ID | Sev | Status | Closable | Title |
|---|---|---|---|---|
| VN-01 | major | latent | repo | .gitattributes regression: default Windows clone rewrites 702 text files and breaks hash bindings |
| VN-02 | major | latent | checks | Manifest keys and recorded paths use OS separators; every verifier fails on Windows |
| VN-03 | major | latent | checks | Text I/O uses the locale code page and writes CRLF; checks crash, falsely report stale or write invalid UTF-8 |
| VN-04 | major | latent | repo | Bound mesh JSONs (136) and guide pages (32) are gitignored; the snapshot cannot verify itself |
| VN-05 | minor | latent | checks | Docs audit can never fail, guide field mis-scoped, inspect commands rewrite committed evidence |
| VN-06 | minor | latent | checks | Structural refresh uses exact float equality and rejects an identical rebuild |
| VN-07 | minor | latent | repo | No committed run record of the current batch runner; logs in /tmp |
| VN-08 | minor | latent | checks | Hard-coded or stale numbers in generators (79.902671, 32.3614, 625, 56) |
| VN-09 | minor | latent | repo | Stale reports bound to other manifests sit in the selected folder (incl. a rejected CSI "pass") |
| VN-10 | minor | latent | repo | Author's absolute sandbox paths in selected evidence |
| VN-11 | minor | latent | repo | Evidence produced by code not in the repo (/tmp audit scripts, Pi extractor) |
| VN-12 | minor | latent | repo | Toolchain undeclared: pypdf, scipy, Blender version, Linux-only raster.so, POSIX commands |
| VN-13 | minor | latent | repo | Raspberry Pi MIT notice not carried with derived Pi STEPs; no NOTICE file |
| VN-14 | minor | latent | docs | Entry documents stale or contradictory |
| VN-15 | minor | latent | docs | 214 broken relative links (159 new) |
| VN-16 | minor | latent | user_decision | 652 MB added; assembly STEPs over 50 MiB; duplicated Pi STEP |
| VN-17 | info | latent | repo | STEP header timestamps change every hash on re-export (not second-pass verified) |
| VN-18 | info | latent | repo | Tracked paths up to 132 chars risk Windows MAX_PATH (not second-pass verified) |
| VN-19 | info | latent | repo | Contributor friction: stray tmp PNGs, studies at top level (not second-pass verified) |
| VN-20 | minor | latent | repo | Structural supplement base JSON has no generator in the repo |
| VN-21 | major | latent | checks | Main audit lacks most r7 check categories; 292 headline is mostly bookkeeping |
| VN-22 | major | latent | checks | No assembly-state model; motion obstacle sets are hand-typed and omit present parts |
| VN-23 | major | latent | checks | No straight-driver audit for the vertical geometry (user rule) |
| VN-24 | major | latent | checks | J7-R float, roll catch, lens clamp/support and collar gauge not re-run after collar/catch changes |
| VN-25 | major | latent | checks | print_overhang / thin_wall / critical_features not run; r7 rule fails 4 of 10 parts |
| VN-26 | major | latent | checks | Harness checks not ported (cable_routes, mate_reach, lead_access, cable_stow, header_housings) |
| VN-27 | major | existing | checks | Fujinon and original-storage variants have no interference/motion audit |
| VN-28 | minor | latent | checks | Signal-lead reach unchecked; routes stretched to stock length; orphan route report |
| VN-29 | minor | latent | checks | microSD path check mis-scoped; collar blocks the straight path; front slit has no use |
| VN-30 | minor | latent | checks | Wire and HDMI checks narrowed to some obstacles |
| VN-31 | minor | latent | checks | Broad info classes; reconciler does not bound the info set |
| VN-32 | minor | latent | checks | Mesh check row omits its hash-binding result (unverified-by-second-pass) |
| VN-33 | minor | latent | checks | 0.95 N m J4 screen does not cover the original-storage fallback |
| VN-34 | minor | latent | checks | EVF axis moved 5 mm in / 4 mm back; evf_restraint not re-run |
| VN-35 | minor | existing | checks | HDMI conductor face / clocking not checked by the 6 HDMI passes |
| VN-36 | minor | existing | checks | CSI slot is a large intake beside the fan; flow split can be computed now |
| VN-37 | info | latent | checks | Hot-bay area parity ignores its own 299.4 mm2 series section |
| VN-38 | minor | existing | checks | r7 keeper and stack_retention check gone; stack hangs on two diagonal screws |
| VN-39 | major | latent | docs | Step 2 fits the camera before the collar gauge; gauge overlaps the adapter 927.75 mm3 |
| VN-40 | major | latent | docs | FPS switch / panel sequence contradicts itself (B3 vs step 4 vs step 6) |
| VN-41 | major | latent | docs | Lens fitted after the panel closes; r7 turn-back and float check lost; camera unretained |
| VN-42 | major | latent | user_decision | Camera, FPC, collar and lens-change service now need the whole carrier out |
| VN-43 | minor | latent | docs | EVF HDMI and 5 V mated at step 3 before their ends exist; carried head drop 0 mm margin |
| VN-44 | minor | latent | docs | Camera-end FPC mating moment unstated |
| VN-45 | minor | latent | docs | Grip service row impossible as written (run-lead header unreachable) |
| VN-46 | minor | latent | docs | "Thin spanner" allowance for the power-switch nut conflicts with the straight-driver rule |
| VN-47 | major | existing | checks | Battery isolation reach only rigid, at the 15 mm floor; ties reintroduced against r7 BX-3 |
| VN-48 | minor | existing | measurement | Step 4 hand coordination unproven |
| VN-49 | minor | existing | measurement | USB 5 V donor head 2.72 mm from the wall; overmold/exit unmeasured |
| VN-50 | minor | latent | docs | No mapping of r7 gates and BX fixes; "56 open gates" includes deleted parts |
| VN-51 | major | latent | cad | Plenum roof not post-supported: single-direction bridges 44-128 mm; no cleanout |
| VN-52 | major | latent | cad | Rear and underside mouths (54-71 mm) repeat the front-mouth hold; hold names only the front |
| VN-53 | major | latent | cad | Tab-catch tines become downward overhangs in the tub print pose |
| VN-54 | major | latent | cad | Carrier print pose floats the frame 2 mm above the bed |
| VN-55 | major | latent | cad | Collar lug: s_c4 washer tangent to the bit relief, support footprint past the lug face |
| VN-56 | minor | latent | cad | Carrier counterbores dia 6.4 (r7: 7.0; r7 bit 6.5) |
| VN-57 | minor | latent | cad | Grip power-passage pocket roof unsupported next to the J4 tongue |
| VN-58 | minor | latent | cad | Collar LR foot overhangs the reduced R25 body |
| VN-59 | minor | latent | cad | Integral skin has no r7 bed chamfer |
| VN-60 | minor | latent | cad | EVF option C, diode sleeve and RCY junction volumes unplaced; stale ko_5v_up/PH text |
| VN-61 | major | latent | docs | No candidate wiring specification; ASSEMBLY points to r7 WIRING |
| VN-62 | major | latent | user_decision | Pigtail drop margin uses solid-wire resistance; no G-W5 fallback left |
| VN-63 | minor | latent | bom | J2 and FPS use the same unkeyed Molex pair |
| VN-64 | minor | latent | bom | BOM spares, SKUs and purchase view gaps |
| VN-65 | minor | latent | user_decision | Power button unguarded, 5 mm proud of the panel |
| VN-66 | minor | latent | measurement | 20 AWG RCY tails soldered onto small EVF pads |
| VN-67 | minor | latent | measurement | Cooler fin exhaust aims at the camera rear |
| VN-68 | minor | latent | measurement | Front hot-mouth plume rises over the collar clamp lug (M1) |
| VN-69 | major | existing | measurement | Main-audit failure: pi5/cooler overlap 79.902671 mm3 |
| VN-70 | major | existing | measurement | G-V-PRINT: slicer, coupons and support review not run |
| VN-71 | major | existing | measurement | G-V-THERMAL: concealed-plenum thermal path unproven |
| VN-72 | major | existing | measurement | G-V-PIGTAIL: 270 mm path cuts and flexible withdrawal STOP |
| VN-73 | major | existing | measurement | G-V-POWER: 1505 switch, nut/tool, J2 pads and connector unplaced |
| VN-74 | major | existing | measurement | G-V-SERVICE: camera FPC unplaced, latch only via 12 x 27 slot, STOPs |
| VN-75 | minor | existing | measurement | G-V-HDMI: DIY HDMI assembly physically unqualified |
| VN-76 | minor | existing | measurement | G-V-STORAGE: compact body depends on an unproven SSD |
| VN-77 | minor | existing | measurement | G-V-STACK: real standoffs, screws and carrier retention |
| VN-78 | minor | existing | measurement | G-V-STRAP: grip lock, strap anchors, tool reach with strap |
| VN-79 | minor | existing | measurement | CK1044/FPS donor parts behind the 332-check result |
| VN-80 | minor | existing | user_decision | EVF 5 V diode feed kept; option C pending |
| VN-81 | info | existing | measurement | Inherited power envelope: 27 W peak vs X1203 25.5 W (not second-pass verified) |
| VN-82 | major | existing | measurement | Collar M1 and all 56 inherited physical gates open |
| VN-83 | info | latent | user_decision | Balance differs by lens (not second-pass verified) |
| VN-84 | info | latent | user_decision | Panel fixings now visible on the control face (not second-pass verified) |

## A. Repository and reproducibility

### VN-01 · major · reproducibility · latent · closable: repo
**.gitattributes regression: a default Windows clone rewrites 702 text files and breaks the hash bindings**
- Sources: R-1, EVI-1, REP-1 (all confirmed). Plus two verifier-missed items (unverified-by-second-pass): the review clone and the rebuild worktree will themselves turn files into CRLF during the fix phase; the rebuild worktree is in flux.
- Evidence: 9ced753 replaced r7's `* -text` (with its "receipts hash exact bytes" comment) with binary-only rules. The system gitconfig sets `core.autocrlf=true`. 702 tracked LF files would convert (371 py, 188 json, 120 md). With an emulated clone, the r7 Kowa receipt drops to sources 1/20, outputs 81/86, gate docs 0/4, and the candidate manifest hashes 3bd82641 instead of 53e668d4. Correction: 60 of 71 candidate sources break, not 71; 11 are STEP/TTF files that keep `-text`. `git status` stays clean, so the cause is invisible. The rebuild worktree already has CRLF files that git does not list as modified.
- Fix: put `* -text` back as the first rule and keep the binary `-diff` rules after it. Set `core.autocrlf=false` in both local trees and re-check out any file that is already CRLF before regenerating anything. Restoring the attribute does not repair files already converted.

### VN-02 · major · reproducibility · latent · closable: checks
**Manifest keys and recorded paths use OS separators; every verifier fails on Windows**
- Sources: R-2, R-4 (confirmed; same root cause); evidence verifier missed item "source keys depend on the OS" (unverified-by-second-pass).
- Evidence: export_candidate.py:18,55,66 and make_corrected_pi.py:15,19 build keys with `os.path.relpath` / `str(relative_to)`. Verifiers look up forward-slash keys (verify_shadow_plenum.py:43, verify_hdmi.py:17, verify_print_meshes.py:33). Native run: KeyError in plenum, outlet, csi, fps, hdmi, power and usb_head checks; all 10 mesh rows fail; the alternatives export stops. update_concealed_vent_structure.py:38 writes a backslash path, so its `--check` fails on the unchanged snapshot. The docs audit records 29 backslash paths.
- Fix: record every key and path with `.as_posix()`; normalise when reading. Add a regression test that no manifest or report key contains a backslash and that every verifier lookup resolves.

### VN-03 · major · reproducibility · latent · closable: checks
**Text I/O uses the locale code page and writes CRLF; checks crash, falsely report stale, or write invalid UTF-8**
- Sources: R-3, ELE-10, REP-3 (confirmed); repro verifier missed item on silent cp1252 writes (unverified-by-second-pass).
- Evidence: Python here runs cp1252 with utf8_mode 0. Only 1 of 99 candidate scripts passes `encoding=`. review_docs_audit.py:40 crashes on byte 0x9d. `make_bom_vertical.py --check` reports "Stale output" although the BOM is current (passes with `-X utf8`, 131 rows). make_bom_vertical.py would write byte 0x92 for U+2019 without error. update_concealed_vent_structure.py would raise UnicodeEncodeError on U+2212. 122 `write_text(` calls set no `newline=`, so they write CRLF. r7 build_d2.py:62 uses `encoding='utf-8', newline='\n'`.
- Fix: `encoding='utf-8'` on every read and write and `newline='\n'` on text writes, through one shared helper. As a guard, have run_locked.py set PYTHONUTF8=1. Add a lint test that fails on bare `read_text()` / `write_text()` / `open()` in text mode.

### VN-04 · major · reproducibility · latent · closable: repo
**Bound mesh JSONs (136) and guide pages (32) are gitignored, so the snapshot cannot verify itself**
- Sources: R-6 (minor), EVI-2, REP-2 (major; majority verifier severity used).
- Evidence: .gitignore:29,31 exclude `out/*/meshes/` and guide `page-*.png`. The manifests bind 45/45/46 mesh JSONs; guide-receipt.json binds 45 meshes and 32 pages. On a clone, reconcile_review_evidence.py:9 raises FileNotFoundError and review_docs_audit gives `files.pass false`, while the committed audit says true. Only 8 of 45 rebuilt mesh JSONs match the committed hashes, so "regenerable" is false at byte level. The history/reviewed-export18 and angled-channel manifests bind 102 missing files each. The mesh caches are about 34 MB per variant.
- Fix: commit the bound caches and pages for 53e668d4, or split them out of the bound file set into a cache manifest and say so in REPRODUCE.md. Never drop a binding to make a check pass. The choice affects repo size (see VN-16).

### VN-05 · minor · checks-integrity · latent · closable: checks
**Docs audit can never fail; guide field mis-scoped; inspect commands rewrite committed evidence**
- Sources: R-7, EVI-10 (confirmed); REP-10 (not second-pass verified); repro verifier missed item on overwriting committed evidence (unverified-by-second-pass).
- Evidence: review_docs_audit.py has no assert, raise or exit path. It exited 0 with 60 of 71 sources changed. `guide_receipt_current` only compares the receipt file hash with CHECKPOINT-STATUS, so it stayed true after a rebuild. Line 119 rewrites out/review-docs-audit.json, which CHECKPOINT-STATUS cites as the binding evidence for all variants. reconcile_review_evidence.py:53 rewrites its output. run_shadow_checks.py moves a committed head-check file into history/. Mitigation: `same_primary_manifest` does show staleness elsewhere in the report.
- Fix: exit non-zero on any failed binding, missing link or stale selected report. Compare the guide receipt's `nominated_manifest_sha256` with the current manifest. Add `--check` (read-only) and `--out` modes, and make inspection read-only by default.

### VN-06 · minor · checks-integrity · latent · closable: checks
**Structural refresh uses exact float equality and rejects a geometrically identical rebuild**
- Sources: R-5 (confirmed).
- Evidence: update_concealed_vent_structure.py:19 compares whole row dicts. After a rebuild it lists six unchanged parts as changed; their largest relative difference is 1.4e-13. The same script already uses a 1e-7 tolerance at line 23.
- Fix: compare numeric fields with a stated tolerance (1e-6 mm absolute, 1e-9 relative). Keep exact comparison for ids, kinds and sources. Add a unit test: a 1e-13 perturbation passes and a 1e-3 change fails.

### VN-07 · minor · provenance · latent · closable: repo
**No committed run record of the current batch runner; logs in /tmp**
- Sources: R-8 (info), EVI-11 (minor; minor used).
- Evidence: out/compact-kowa_lm6hc has no review-check-run.json. The only 53e668d4 batch record is history/shadow-first-check-run (old runner db538169, usb_head exit 1, no microSD step); the current runner is a59d5f5c. final-check-run.json and primary-refresh.json bind export18 and log to /tmp. microsd-service-dependency.json was written after that batch ended. Refuted sub-point: plenum and outlet verifiers run separately by design (REPRODUCE.md:33).
- Fix: at the next evidence refresh, run the current runner once on the frozen manifest. Commit the run record with log hashes and repo-relative log paths.

### VN-08 · minor · checks-integrity · latent · closable: checks
**Hard-coded or stale numbers in generators**
- Sources: R-9 (confirmed), repro verifier missed item on make_bom_vertical.py:315 (unverified-by-second-pass), EVI-15 (not second-pass verified), ELE-11 (625-query part), DES-10 ("56" literal part).
- Evidence: reconcile_review_evidence.py:49 holds the literal "Cooler/source overlap79.902671mm3". CHECKPOINT-STATUS.json:35 and make_bom_vertical.py:315 repeat 79.902671. official_pi5_geometry.py:131 says "Retain 32.3614 mm3" in every manifest. BOM D2-14F says 625 queries; the report and BOM line 10 say 659. "56" open gates is a literal at verify_candidate.py:176 and reconcile_review_evidence.py:47.
- Fix: format every such figure from the source JSON row (overlap_mm3, query counts, gate list length). Add a test that greps generated docs for numbers that do not match their source report.

### VN-09 · minor · evidence-hygiene · latent · closable: repo
**Stale reports bound to other manifests sit in the selected output folder**
- Sources: R-10 and EVI-16 (not second-pass verified), PHY-12 stale-report part (confirmed), physical verifier missed item (unverified-by-second-pass).
- Evidence: out/compact-kowa_lm6hc/csi-access-checks.json says "pass" but binds manifest e8648073. The guide calls it a rejected old proxy, yet delivery-core-paths.json:64 still lists it. ventilation-checks.json (c392feab) and wall-probe-context.json (c9e1e207) are labelled historical by the docs audit. assembly.step is not in the manifest file list.
- Fix: move stale reports under history/. Make the reconciler fail on any JSON in the selected folder whose manifest hash is not the selected one, unless it is explicitly marked historical.

### VN-10 · minor · provenance · latent · closable: repo
**Author's absolute sandbox paths recorded in selected evidence**
- Sources: R-11 (not second-pass verified), repo verifier missed item (unverified-by-second-pass).
- Evidence: routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json, the selected usb_head case (reconcile_review_evidence.py:18), records `/workspace/scratch/8ece9a785de6/...`. Four JSONs contain `/workspace/`; four scripts reference /tmp.
- Fix: writers record repo-relative POSIX paths. Do not hand-edit hashed JSONs; regenerate and rebind.

### VN-11 · minor · provenance · latent · closable: repo
**Evidence produced by code that is not in the repo**
- Sources: REP-9 (confirmed).
- Evidence: independent-audit.json:766-768 lists `/tmp/xt30_independent_audit/*.py` (absent). probe_power_boolean2.py reads /tmp/oldvalid-base_grip.step. No committed script writes `*-native.step` or connector-extraction.json; only readers exist.
- Fix: commit the Pi component extractor and the audit scripts, or label those JSONs as non-reproducible provenance.

### VN-12 · minor · reproducibility · latent · closable: repo
**Toolchain undeclared: pypdf, scipy, Blender version, Linux-only rasterizer, POSIX-only commands**
- Sources: REP-8 (confirmed), R-13 (not second-pass verified).
- Evidence: cad-requirements-lock.txt has no pypdf or scipy; build_shadow_structural_pdf.py needs pypdf; 8 screen_fps_*.py need scipy. No Blender version is recorded. guide/software_lineart.py builds raster.so with `g++ -fPIC`; the MinGW g++ here is 32-bit, so 64-bit CPython cannot load it. The guide therefore cannot be rebuilt on this machine. REPRODUCE.md has 14 POSIX-only commands.
- Fix: add a candidate lock (or add pypdf and scipy to the shared lock after checking r7 impact). Record the Blender version. Give Windows commands and mark Linux-only steps, or add a pure-numpy raster fallback.

### VN-13 · minor · licensing · latent · closable: repo
**Raspberry Pi MIT notice not carried with derived Pi STEPs; no repo NOTICE file**
- Sources: REP-4 (verifier downgraded to minor).
- Evidence: the MIT LICENSE.txt sits only in one routing-snapshot folder. Seven derived STEPs (pi5-corrected.step, three variant pi5.step, three assembly.step) have no notice beside them. The repo is public. tools/ and software/gs8-camera-evf carry MIT licences; the CAD and docs content has none.
- Fix: add THIRD-PARTY-NOTICES.md (Pi MIT text, source URL and hash, derived files, DejaVu licence). Copy LICENSE.txt into each folder holding Pi geometry. The project-content licence is a user decision.

### VN-14 · minor · docs · latent · closable: docs
**Entry documents are stale or contradict each other**
- Sources: REP-6 (confirmed).
- Evidence: PUBLISHING.md:3 says publication is not complete, but the repo is public; it points to a bundle that is not in the repo. README.md:22 says "intended for a separate repository" (it already is). CLOUD-START-HERE.md is unchanged r5/r6 text. cad/gs8-d2-v1/HANDOFF.md still presents r7 as current. history/reviewed-export18/README.md cites an off-repo "Library". README.md already names the vertical candidate as current.
- Fix: update or retire PUBLISHING.md; fix the README line; add pointer banners to CLOUD-START-HERE.md and HANDOFF.md; replace the "Library" reference.

### VN-15 · minor · docs · latent · closable: docs
**214 broken relative links (159 new, 55 inherited from r7)**
- Sources: REP-7 (confirmed).
- Evidence: of 577 relative links, 214 are broken. The new ones are in frozen copies (two copied BOMs with 64 each, UPSTREAM-README with 11, and others). The live candidate docs are clean.
- Fix: add a "links relative to original location" banner, or rewrite frozen-copy links to d38468e on GitHub. Add a repo-wide link check (tools/check_local_links.py exists in the 8mm repo as a model).

### VN-16 · minor · repo-size · latent · closable: user_decision
**652 MB added; assembly STEPs over GitHub's 50 MiB warning; duplicated Pi STEP**
- Sources: REP-5 (confirmed).
- Evidence: the tree grows from 131.6 MB to 783.8 MB, with 517.7 MB of STEP; the pack is 156.6 MiB. Three assembly.step files are 63 MiB each. The three variant pi5.step files differ only in a 5-byte timestamp. The largest file has 37% headroom to the 100 MiB hard limit.
- Fix: keep one Pi STEP and reference it by hash. Move assembly STEPs to Release assets or regenerate them on demand. Make STEP headers deterministic (VN-17). The user chooses.

### VN-17 · info · reproducibility · latent · closable: repo
**STEP header timestamps change every hash on re-export** (not second-pass verified)
- Sources: EVI-17. Same limit as r7, so not a regression.
- Evidence: tub.step FILE_NAME carries a wall-clock time. REPRODUCE.md re-exports, then hard-codes `--manifest-sha256 53e668d4`.
- Fix: normalise the STEP header time in export_candidate.py (fixed epoch), or state in REPRODUCE.md that hashes will change.

### VN-18 · info · reproducibility · latent · closable: repo
**Tracked paths up to 132 characters risk Windows MAX_PATH** (not second-pass verified)
- Sources: R-12. A checkout into the deep session scratch folder failed with "Filename too long".
- Fix: shorten routing-snapshot folder names, or document `core.longpaths=true`.

### VN-19 · info · repo-hygiene · latent · closable: repo
**Contributor friction** (not second-pass verified)
- Sources: REP-11. structural-review/tmp/pdfs/*.png committed and unreferenced; 50 study scripts beside the selected pipeline; 264 lines over 300 characters; a one-line message for a 636-file commit.
- Fix: move studies under studies/, delete the stray tmp files, add a short pipeline index.

### VN-20 · minor · provenance · latent · closable: repo
**Structural supplement base JSON has no generator in the repo**
- Sources: PRI-8 (confirmed in part; verifier minor).
- Evidence: update_concealed_vent_structure.py:14-29 scales everything from reference-export18-structural-binding.json, and no script writes that file. Refuted part: the "2.25x higher J4 model" is the r7 1.6/1.8 mm lip/head geometry ((2.4/1.6)^2 = 2.25), not a dropped severer model.
- Fix: commit the generator, bind its hash in the supplement, and add a note that "inherited" means the r7 1.6/1.8 mm geometry.

## B. Check coverage and check scope

### VN-21 · major · check-coverage · latent · closable: checks
**Main audit lacks most r7 check categories; the 292-pass headline is mostly bookkeeping**
- Sources: PHY-3, DES-2 (confirmed); PRI-1 (coverage part). Verifier-missed items (unverified-by-second-pass): "many more r7 categories not ported; nominal_features are constants", "292 headline mostly bookkeeping", "r7 harness categories not run; no electrical rows".
- Evidence: verification.json has 311 rows in 10 categories. integrity 45 + roundtrip 45 + source_binding 71 = 161 of the 292 passes. The rest are 108 pairwise interference rows, 10 motions and 13 probes. r7 out/checks.json has 35 categories (990 rows). Not run on the candidate: driver, service_driver, j7_float, roll_catch, lens_support, lens_clamp, mate_paths, mate_reach, header_housings, lead_access, handling, evf_restraint, stack_retention, print_overhang, critical_features, boss_geometry, inserts, removals, clearance, thin_wall, cable_routes, cable_stow. verify_candidate.py:150-151 nominal_features are "not extracted from the current STEP". The candidate never says which r7 categories it did not port. Nuance: a new design that never ported the suite, not an edit of r7's checks; some side reports partly stand in.
- Fix: port the categories (VN-23 to VN-26, VN-34, VN-38). Report per-category coverage, and keep geometric counts separate from bookkeeping counts in REVIEW, README and CHECKPOINT. Replace constant nominal_features with values measured from the STEP.

### VN-22 · major · check-coverage · latent · closable: checks
**No assembly-state model; motion obstacle sets are hand-typed and omit present parts**
- Sources: design-regression verifier missed item (unverified-by-second-pass), EVI-5 (confirmed, minor: no collision is hidden today).
- Evidence: manifest rows have no step field; the candidate has no STEPS or present_at. verify_candidate.py:104-113 lists fixed sets by hand. carrier_out omits xt30_pair, lens_collar, s_c1-3, eyepiece and eyecup. panel_out omits x1203_kit, microsd, xt30_pair and usb_stick. A shadow screen found no hidden hit today. r7 derives contexts from layout.present_at(step) (layout.py:1493). This is why the build-order errors in VN-39, VN-41 and VN-43 passed 292 checks.
- Fix: add a STEPS / present_at table for the candidate's own build order. Derive every motion fixed set and every driver context from it. Add lints: the centring gauge never coexists with the camera or adapter; each motion's obstacle set equals present parts minus movers.

### VN-23 · major · check-coverage · latent · closable: checks
**No straight-driver audit for the vertical geometry (user rule)**
- Sources: EVI-3 (confirmed); print verifier missed item on moved collar screws s_c3/s_c4 (unverified-by-second-pass).
- Evidence: no candidate script ports r7 check_driver (bit 6.5 x 40, handle 30 x 100). It should cover 7 PT screws (p_panel1-4, p_carrier1-2, p_grip) and 4 collar M3s, two of which moved (s_c3 to (18,30), s_c4 to screw_y -26.3). The physical review hand-probed all 11 at their steps and found them clear except the carrier counterbore case (VN-56). The p_grip handle is 1.37 mm from the strap (r7: 2.35).
- Fix: port check_driver and check_service_driver with contexts from VN-22. Bind to the manifest and add them to the main audit.

### VN-24 · major · check-coverage · latent · closable: checks
**J7-R float, roll catch, lens clamp/support and collar gauge not re-run after the collar and catch changed**
- Sources: EVI-4 (confirmed), PRI-7 check part (confirmed); print verifier missed item on the BFAR screw-out range (unverified-by-second-pass).
- Evidence: model.py:201-204 changes collar body_r 30 to 25, LL foot (28,36) to (18,30), and moves the lug. model.py:237-239 grows the tab-catch boxes from the tub roof to Z98. The camera is checked at one nominal pose for overlap only. Interference passes anything under 0.05 mm3, so contact passes. r7 j7_float has 50 rows over the BFAR range with 0.5 mm lateral and 0.4 mm axial gaps; r7's camera-to-tub axial gap was exactly 0.4 at s 0. Nominal gaps measured on the saved STEP: camera-tub 0.5, adapter-tub 0.825, panel 2.25, collar 3.48, carrier 3.91 mm. No actual violation is shown, but the s range, roll and clamp cases are unverified. Recompute: polygon margin 14.43 mm (r7 16.01), max anchor reaction 50.7 N (r7 59.3).
- Fix: port check_j7_float (full s range, min gaps), check_roll_catch, check_lens_support, check_lens_clamp, check_collar_gauge and inserts, and report per-obstacle minimum gaps. Run r7's mechanical unit tests (test_mechanical_refinements.py) on the candidate collar values.

### VN-25 · major · check-coverage · latent · closable: checks
**print_overhang, thin_wall and critical_features not run; r7's rule fails 4 of 10 parts**
- Sources: PRI-1 (confirmed), EVI-7 (confirmed, existing hold part). Print verifier missed item (unverified-by-second-pass): the r7 per-pixel best-of-8 metric would not catch the plenum roof.
- Evidence: r7 out/checks.json has print_overhang 13/13, thin_wall 12/12, critical_features 131 pass / 10 info. A read-only re-run of r7 check_print_overhang on the candidate print-pose STLs fails tub (12 regions; 2 are the declarable J4 tongue wings), carrier (1963.1 mm2), base_grip (102.9 mm2) and lens_collar (11.0 mm2). r7 _classify (checks.py:4914-4921) accepts a pixel if any of 8 directions bridges within 30 mm, so both bay roofs pass at exactly 30.0 mm, while a slicer lays one direction per region.
- Fix: port check_print_overhang, thin_wall and critical_features into run_shadow_checks.py for every production part, with declared support zones. Add a rule per connected bridge region: pick one raster direction and require every run in it to be at most 30 mm. Re-run r7's tub to confirm the stricter rule still passes there.

### VN-26 · major · check-coverage · latent · closable: checks
**Harness checks not ported**
- Sources: EVI-8 (confirmed; partial substitutes exist), electrical verifier missed item (unverified-by-second-pass).
- Evidence: r7 lead_access (9), mate_reach (6), cable_stow (7), header_housings (10) and cable_routes have no vertical counterpart; no candidate script imports checks.py. verify_hdmi, verify_power_service, verify_wire_solids, verify_fps_integrated and verify_shadow_usb_head port part of the harness.
- Fix: port cable_routes, mate_reach (minimum stock length plus service pose), lead_access and pigtail_drop (computed G-W5 row), cable_stow and header_housings. Run them from run_shadow_checks.py, bound to the manifest. Keep the STOPs until they pass.

### VN-27 · major · check-coverage · existing · closable: checks
**Fujinon and original-storage variants have no interference/motion audit**
- Sources: EVI-6 (confirmed).
- Evidence: out/compact-fujinon_hf6xa and out/original-kowa_lm6hc hold only manifest, print-mesh checks and assembly.step. REVIEW.md:289 says the audits were not rerun. r7 released at 0 fail for both lenses.
- Fix: run verify_candidate.py --variant for both, about 430 s each, and bind the results in the reconciler.

### VN-28 · minor · check-coverage · latent · closable: checks
**Signal-lead reach unchecked; routes stretched to stock length; orphan route report**
- Sources: ELE-3 (verifier minor; panel-off failure refuted), PHY-13 (existing, confirmed); electrical verifier missed item: signal_routes_review.json is an orphan (unverified-by-second-pass).
- Evidence: signal_routes.py:60-66 solves QT so main + branch = 250 mm; :137 does the same for the run lead. The QT minimum in the candidate's own route family is about 239.2 mm, under 1 mm of slack at the 240 mm stock minimum. Run-lead cores bottom out at 214.3/209.5 mm. signal_routes_review.json binds power_source_sha256 3b7db74a, which matches no tracked file, and no runner or document uses it. ASSEMBLY:259-261 says the propped-panel reach must still be measured. An estimate says it probably fits (about 194 mm needed vs 240).
- Fix: add a manifest-bound signal-route verifier to run_shadow_checks.py: minimum path plus service allowance at minimum stock length, plus a mate_reach row for QT and J2 in the propped-panel pose. Archive the stale JSON. Add QT, run-lead, RCY and EVF-pad rows to MEASUREMENTS-TO-CLOSE.

### VN-29 · minor · check-scope · latent · closable: checks
**microSD path check mis-scoped; the collar blocks the straight path; the front slit has no use**
- Sources: PHY-2, DES-8 (both verifiers minor); missed items: dog-leg route exists (unverified-by-second-pass, two verifiers agree).
- Evidence: verify_candidate.py:112 fixed set is only tub, gs_camera and c_cs_adapter. A straight +X move hits lens_collar from dx 32 (max 75.55 mm3). REVIEW.md:54,294 and ASSEMBLY:15-16,306 rely on panel-off +X. Two probes found a clear dog-leg: +X 12-24 mm, then +Y out of the open panel side (dx 10 hits the carrier, dx 26 the tub). The front slit (model.py:273) passes no card. The closed-panel case stays REJECTED, as documented. Physical tool and finger reach remain an MTC row.
- Fix: replace microsd_out with the dog-leg motion, with obstacles from VN-22 (collar, lens, carrier, x1203, Pi). Name the tool and keep reach as a hold. Close the slit or justify it (user decision).

### VN-30 · minor · check-scope · latent · closable: checks
**Wire and HDMI checks narrowed to some obstacles**
- Sources: EVI-12 (confirmed; wire limit partly disclosed).
- Evidence: verify_wire_solids.py:15-17 tests power wires against printed parts only (disclosed in scope). verify_hdmi.py:96 drops every p_/s_ screw from the ribbon obstacles (not disclosed; the nearest screw is 2.12 mm away today).
- Fix: add COTS and hardware solids to both obstacle sets and list any exclusion in the report.

### VN-31 · minor · check-scope · latent · closable: checks
**Broad info classes; the reconciler does not bound the info set**
- Sources: EVI-13 (confirmed).
- Evidence: verify_candidate.py:79-81 turns any keepout overlap with a non-printed part into info, not only the reserve's own mating port. The reconciler checks only the fail list, so new info rows pass silently. One such row exists today (usb_storage_plug_reserve 195.9 mm3).
- Fix: limit the keepout rule to the named mating partner. Have the reconciler assert the exact info id set.

### VN-32 · minor · check-scope · latent · closable: checks
**Mesh check row omits its hash-binding result** (unverified-by-second-pass)
- Sources: repro verifier missed item.
- Evidence: verify_print_meshes.py:33-35 folds `bound` into status but writes no field, so a binding failure shows as "fail" with watertight and bed fit both true.
- Fix: add expected and actual hash fields to each row.

### VN-33 · minor · structure · latent · closable: checks
**0.95 N m J4 screen does not cover the original-storage fallback**
- Sources: PRI-9 (verifier minor).
- Evidence: the first-moment transfer applied to original-kowa gives 0.976 N m (equal share) and 1.367 N m (70% share). The supplement covers only compact Kowa, and the script asserts on other variants, so nothing warns about the 2.7% gap.
- Fix: compute the screen per variant, or raise it to cover the fallback. State the coverage in the supplement.

### VN-34 · minor · check-coverage · latent · closable: checks
**EVF axis moved 5 mm inboard and 4 mm rearward; evf_restraint not re-run**
- Sources: DES-11 (confirmed).
- Evidence: r7 barrel at Y16 Z78, F-154 (layout.py:440-443). Candidate EY=11 and F-158. REVIEW.md:46 lists only the new value under "Preserved / revised". Relative to the left face the move is about 2 mm.
- Fix: show r7 and candidate values side by side. Port evf_restraint (8 rows) and add an eye/face clearance check.

### VN-35 · minor · check-coverage · existing · closable: checks
**HDMI conductor face and clocking not checked by the 6 HDMI passes**
- Sources: ELE-9 (confirmed, existing under G-V-HDMI).
- Evidence: hdmi_routes.py:9-16 uses a U turn and a 45 degree miter fold, which flips the strip face. verify_hdmi.py has no contact-face or pin-1 test. The BOM already names the R-bend 3557 head.
- Fix: track the conductor-face normal along the route and assert it matches each head's contact side. Confirm on real parts before ordering the Pi head.

### VN-36 · minor · thermal · existing · closable: checks
**CSI slot is a large intake beside the fan; the flow split can be computed now**
- Sources: PRI-10 (verifier minor; existing, REVIEW.md:7,116 calls it a bypass), PRI-15 (not second-pass verified).
- Evidence: the 323 mm2 CSI slot (model.py:263) is at least 0.86x the conductance of the whole concealed cold path (about 376 mm2 effective). It sits beside the fan inlet. A laminar estimate for the 6 mm gap gives under 1 Pa. Caution: a plug would remove about 46% of the effective intake area and could raise temperatures.
- Fix: add a flow-network model (mouths, channels, posts, ports, CSI slot, fan-curve band) as a computed gate, with occlusion cases. Decide on any CSI plug only after it.

### VN-37 · info · thermal · latent · closable: checks
**Hot-bay area parity ignores its own series section**
- Sources: EVI-14 (verifier info).
- Evidence: 299.4 mm2 section + 210 mm2 = 509.4 < 510 mm2. The row already says it is not a series-minimum proof.
- Fix: use min(mouth, series section) per branch, or state the 0.1% shortfall.

### VN-38 · minor · structure · existing · closable: checks
**r7 keeper and stack_retention check gone; the stack hangs on two diagonal screws**
- Sources: DES-19 (confirmed; G-V-STACK lists carrier retention as open).
- Evidence: two diagonal PT screws go into 42.75 mm posts (model.py:241-243). The posts print along the build axis, so side loads bend them across layers. The structural note screens only the arm at 5 g.
- Fix: port stack_retention and a post-root bending screen. Consider a third printed locating feature (tongue or slot) with no new screw.

## C. Assembly procedure and service

### VN-39 · major · assembly-order · latent · closable: docs
**Step 2 fits the camera before the collar gauge; the seated gauge overlaps the adapter by 927.75 mm3**
- Sources: PHY-1, DES-1 (confirmed by two verifiers); physical verifier missed item: both guide builders and the published PDF repeat the order (unverified-by-second-pass).
- Evidence: ASSEMBLY-VERTICAL.md:176-186 seats the camera, then fits the collar with the gauge. The seated centring_gauge overlaps c_cs_adapter by 927.752 mm3 (two probes). Its rear cone references the tub lip, "camera not yet in" (printed_collar.py:190-193). r7 ASSEMBLY.md:206 says "Lens collar first, camera still out". The candidate's own camera_in motion already treats the collar as fitted (verify_candidate.py:108). guide/build_guide_vertical.py:344 and build_guide_concealed_vents.py:396 carry the same order into the review PDF.
- Fix: reorder step 2: inserts, collar + gauge + s_c1..s_c3 with the camera out, gauge out forward, then camera in. Fix both guide builders. Add the VN-22 lint (gauge never present with camera or adapter). Rebuild the guide only in the rebuild worktree, which needs the Linux rasterizer (VN-12).

### VN-40 · major · assembly-order · latent · closable: docs
**FPS switch / panel sequence contradicts itself (B3 vs step 4 vs step 6)**
- Sources: PHY-5 (confirmed).
- Evidence: B3 (:154-156) seats the panel over the CK1044 bushing and fits washer, nut and both knobs on the bench. Step 4 (:197-199) carries the switch with the carrier, hand-supported. Step 6 (:258-266) slides the panel over the switch and never refits the FPS washer, nut or knob. The panel hole is r5 and knob_fps is about 24 mm across. The service row (:301) and guide (build_guide_vertical.py:303) treat the switch as carrier-side, so B3 is the outlier. B3 also drops r7's "thumb behind the encoder" (BX-5).
- Fix: B3 = encoder, knob_exp with thumb backing and paper shim, and power button only. Step 6 = guide bushing and peg into the panel, fit washer and nut with an on-axis socket, then knob_fps with the shim. Add a sequence lint that every part removed in a service row is refitted in its reverse.

### VN-41 · major · assembly-order · latent · closable: docs
**Lens fitted after the panel closes; r7 turn-back and float check lost; camera unretained in steps 2-3**
- Sources: DES-5 (major), PHY-9 (minor), DES-12 (minor), all confirmed; merged because one reorder fixes all three. Verifier severity major used.
- Evidence: s6 (panel) comes before s7 (lens). :278-281 only cites the "inherited floating-camera seating method". r7 ASSEMBLY.md:222 fits the lens with the panel off: fingertip push, turn to the other tine and back half way, confirm no contact, then s_c4. r7 lens_turn_back_lint (checks.py:3950) would fail on this text. Once the carrier is in, the camera can only move back 3.9 mm, so the fingertip push is impossible. Before step 4 nothing stops an 11 mm retreat (:186 "Lens final installation can wait until step 7").
- Fix: fit the lens and s_c4 in step 2, right after the camera and before the EVF and carrier. Copy r7 step 8 wording, including turn-back and the look-and-feel float check. Run r7's lens_turn_back_lint on ASSEMBLY-VERTICAL.md.

### VN-42 · major · serviceability · latent · closable: user_decision (docs part closable now)
**Camera, FPC, collar and lens-change service now need the whole carrier out**
- Sources: DES-6, PHY-12 regression part (confirmed); design-regression verifier missed item: no lens-change service row (unverified-by-second-pass).
- Evidence: with the carrier in, the camera can move back 3.9 mm, then meets the carrier (5.45 mm3). Lifting at -3.9 mm hits the tub (208.9 mm3); at -11.1 mm it hits the carrier (517 mm3), x1203 and kit. So removal always needs the carrier out, which passes through six STOPs. The service row says "where the reviewed clearance requires it". r7 camera service needed only the pack out and panel off. Collars and gauges differ per lens, and the gauge needs the lip empty, so a lens change means a full electronics teardown. Each panel removal also cycles the 30-cycle J2 pair.
- Fix now (docs): r7-vs-candidate service matrix; a lens-change row with its real dependency chain; correct the "where required" wording. User decision: accept the trade, or redesign so the camera leaves ahead of the carrier front (X-29) or the gauge seats without entering the lip.

### VN-43 · minor · assembly-order · latent · closable: docs
**EVF HDMI and 5 V junction mated at step 3 before their source ends exist; carried head drop has 0 mm margin**
- Sources: PHY-6 (confirmed).
- Evidence: step 3 (:191-193) mates the EVF HDMI head and sets up the EVF power junction. The 3556 head and USB donor ride in with the carrier at step 4 (verify_hdmi.py:125), and step 4 says "Keep the EVF HDMI end free". The carried sweep lowers the head 6 mm, equal to the 6.0 mm stroke (snapshot path dropped 12 mm). Service pliers corridor not re-measured.
- Fix: move both matings to step 5 (push-up from below). Re-run the carried sweep with the head at least stroke + 3 mm low. Add an unplug finger/pliers corridor.

### VN-44 · minor · assembly-order · latent · closable: docs
**Camera-end FPC mating moment unstated**
- Sources: PHY-4 (verifier minor; slack store is an existing hold, see VN-74).
- Evidence: step 5 (:215) "Connect the camera FPC ... Check both end contacts" reads as mating both ends in place. The carrier plate blocks a +Y approach to the camera socket (3.91 mm gap). STEP-REVIEW row 08 and the guide's service order imply bench pre-mating.
- Fix: say the camera end is mated and pre-folded on the bench before step 2, and keep the FPC clear of the 3.9 mm gap during the carrier slide.

### VN-45 · minor · serviceability · latent · closable: docs
**Grip service row cannot be done as written**
- Sources: PHY-10 (confirmed).
- Evidence: :307 says "free run ... leads before sliding the grip off". The run lead's Pi end is a header housing at pins 37/39 on the cooler-side face, reachable only with the carrier out. The button end is pre-wired. The module row lists run-lead reach as a STOP.
- Fix: state "Pi module out first" in the grip row, or add a removable inline junction near the grip mouth (user choice).

### VN-46 · minor · user-rule · latent · closable: docs
**"Thin spanner" allowance for the power-switch nut conflicts with the straight-driver rule**
- Sources: DES-18 verifier reason (confirmed).
- Evidence: ASSEMBLY-VERTICAL.md:56,68 allow a thin spanner. A spanner is not a straight driver along the axis. A socket up to OD 28 clears the panel (physical probe).
- Fix: replace with a deep socket on axis and add the tool to the BOM tool list.

### VN-47 · major · power-isolation · existing · closable: checks (physical part: measurement)
**Battery isolation reach checked rigid only, at the 15 mm floor; ties reintroduced against r7 BX-3**
- Sources: PHY-11 (confirmed).
- Evidence: power-270-yaw21.json: the female XT30 face ends 15 mm below the grip mouth, exactly r7's face_out_min (r7 BX-3 reached about 28.4 mm). r7 SPEC-C3.md:63 says "no tie anywhere else". The candidate reintroduces four carrier ties (:223-226) without citing the departure. Flexible deployment and finger force stay in power-service-checks.json remaining_stop.
- Fix: model ties as fixed points and run an r7-style lead_access check with flexible cores (part of VN-26). Record the departure from the no-tie rule in REVIEW. Ties vs RTV-only retention is a design choice for the user.

### VN-48 · minor · assembly · existing · closable: measurement
**Step 4 hand coordination unproven**
- Sources: PHY-8 (uncertain; existing per FPS-SERVICE-STUDY.md:24).
- Evidence: switch and carrier are "separately hand-supported" while the pigtail, fuse and XT30 feed down the floor passage. A printed central switch rest exists.
- Fix: coordinated-hand trial. Option: a printed transport clip, a named helper, a defined body rest pose, and feeding the XT30 before the end of the slide.

### VN-49 · minor · electrical-fit · existing · closable: measurement
**USB 5 V donor head 2.72 mm from the rear wall; overmold and exit unmeasured**
- Sources: PHY-7 (uncertain); MTC 4448 row; STOP checkpoint (EVF feed unplaced).
- Evidence: the head box sits 2.72 mm from the tub with 287.9 mm3 of wall behind it. The box is r7's plug-plus-bend allowance, and the -Y and upper side zones are empty, so a sideways exit is not ruled out. usb2-head-reservation.json already says "lateral departure required".
- Fix: measure the 4448 overmold and exit. If axial, use a right-angle USB-A lead or reserve bend room. Add a cable-exit capsule to the head check.

### VN-50 · minor · docs · latent · closable: docs
**No mapping of r7 gates and BX fixes; "56 open gates" includes gates for deleted parts**
- Sources: DES-10 (confirmed).
- Evidence: the candidate never cites BX-1..BX-17. "56" is a literal with no list behind it. It still counts G-SNAP-1/2, G-PLG-1/2 and G-KEEP-1/1r, which belong to the deleted hood, plunger and keeper.
- Fix: add a gate and BX table marking each one retired, carried, re-scoped or replaced by a G-V-* gate. Generate the count from it (VN-08).

## D. Print and CAD geometry

### VN-51 · major · printability · latent · closable: cad
**Plenum roof is not post-supported; single-direction bridges far exceed 30 mm; no cleanout**
- Sources: PRI-2 (blocker downgraded to major: printing is already held), PRI-13 (existing, minor).
- Evidence: at print z 7.6 the reviewer's STL raster needs 43.8 mm (cold) and 47.1 mm (hot) bridges in the best direction and 93-97 mm along the axes. The verifier's line-span calculation gives 50.7 mm best and 90-95 mm along axes in the cold bay. An 8 mm square grid of 1.6 mm posts cannot keep all one-direction lines under 30 mm. The candidate never claims 9.71 mm is a span and sets support_free_claim false. The farthest bay points are 85-99 mm from any mouth through a 6 mm gap with 188 posts; cleanout_qualified is false.
- Fix: replace the post grid with continuous ribs along the flow (x) at 10 mm pitch or less, giving two-ended bridges under 9 mm, with rib-free lanes to the mouths. Or use a 45 degree self-supporting roof. Prove it with the per-region bridge rule (VN-25) and the plenum section checks, then a coupon.

### VN-52 · major · printability · latent · closable: cad
**Rear and underside mouths repeat the front-mouth hold and are larger; the hold names only the front**
- Sources: PRI-3 (confirmed; ASSEMBLY:116 asks to check all four mouths, so partly documented).
- Evidence: vent_geometry.py:16-20 opens rear Z5..75 (70 mm), cold underside X-154..-83 (71 mm), hot underside X-59..-5 (54 mm), front Z5..40 (35 mm). README, REVIEW and CHECKPOINT name only the front mouth. The expanded coupon (make_shadow_plenum_coupon.py:89, X-110..0) misses the rear mouth and 44 of 71 mm of the cold underside.
- Fix: give every mouth a 45 degree lintel or teardrop section. List all four mouths in the hold text and extend the coupon. Fix with VN-51.

### VN-53 · major · printability · latent · closable: cad
**Tab-catch tines become downward overhangs in the -Y-down tub print pose**
- Sources: DES-4 (confirmed).
- Evidence: model.py:237-239 grows the r7 tab-catch boxes from the integral tub roof to Z98. The tub prints -Y down. r7's tines were on the hood, printed roof-down, so they rose from the bed. The +Y catch face (57.6 + 11.0 mm2) faces down. The panel-screw boss at (-10.8, 91.7) anchors the upper part, but Z78.5..about 87.2 is a 9 mm cantilever with nothing below, and that zone holds the tab contact (camera top Z82.1). Support in the 16.6 mm slot would scar the catch faces and the r7 roll window (0.679/0.129 mm). No print hold mentions the tines.
- Fix: a separate upright-printed catch block that slides in from +Y and is held by the panel (no new screw), or a self-supporting chamfer under the faces. Prove it with print_overhang (VN-25) and roll_catch (VN-24); add a tine coupon to G-V-PRINT.

### VN-54 · major · printability · latent · closable: cad
**Carrier print pose floats the whole frame 2 mm above the bed**
- Sources: PRI-4 (confirmed).
- Evidence: the frame is at y 17.2..20.2 (model.py:176-194). Only the arm and root pads reach y 22.2 (structure_geometry.py:29-33). The carrier prints +Y down, so the frame starts at print z 2.0: 1963.1 mm2 unsupported. print-mesh-checks only tests min z.
- Fix: thicken the frame on +Y to y 22.2 for a continuous bed face, then re-check stiffness and boss walls. Prove it with print_overhang and a bed-contact-area row.

### VN-55 · major · structure · latent · closable: cad
**Collar lug: s_c4 washer tangent to the bit relief; flat-support footprint past the lug face**
- Sources: PRI-7 CAD part (confirmed; verifier says worse than reported).
- Evidence: screw_y -26.3 with a 7.0 mm washer reaches -22.8, exactly the relief face (r7 had 0.5 mm). At float dy +0.2 it is 0.2 mm into the wall. The flat-support footprint (r 3.9) reaches y -30.2, 0.2 mm past the lug face at -30. The lug wall around the insert is 1.7 mm. r7's test_mechanical_refinements.py:26-45 would fail on these values. Collar values change only inside model._build, so no r7 test runs on them.
- Fix: restore at least 0.5 mm washer clearance and a full flat support (move screw_y or the relief, or widen the lug). Run r7's mechanical tests and lens_clamp on the candidate values (VN-24). Collar M1 stays open.

### VN-56 · minor · fastener-access · latent · closable: cad
**Carrier counterbores dia 6.4 (r7: 7.0; r7 bit 6.5)**
- Sources: DES-3 (verifier minor); evidence verifier missed item (major, unverified-by-second-pass).
- Evidence: model.py:191 cuts r 3.2. The bores are 2.4 mm deep at p_carrier1 and 0.5 mm at p_carrier2. A 6.5 mm bit overlaps the carrier by 2.43 and 0.41 mm3. The head top sits flush, so the shank need not enter. The larger risk is fit: a 6.0 mm head in a printed 6.4 mm bore may not seat (FDM holes print small). BOM D2-77 allows a 6.5 mm shank.
- Fix: open both bores to 7.0 mm as on the panel, re-check boss wall and carrier stiffness, and prove with the ported driver check (VN-23).

### VN-57 · minor · printability · latent · closable: cad
**Grip power-passage pocket roof unsupported next to the J4 tongue**
- Sources: PRI-5 (confirmed).
- Evidence: the power box (power_geometry.py:62) cuts into the J4 base pocket and removes the roof's +X anchor; the roof spans 36.5 mm. 102.9 mm2 unsupported. r7 base_grip passed. The pocket floor sits 0.25 mm below the tongue head, so sag can block the J4 slide.
- Fix: slope the passage roof at 45 degrees, or declare a support zone off the J4 mating faces. Prove with print_overhang.

### VN-58 · minor · printability · latent · closable: cad
**Collar LR compression foot overhangs the reduced R25 body**
- Sources: PRI-6 (confirmed).
- Evidence: the LR foot reaches 28.64 mm from the axis, 3.64 mm outside body_r 25. Only bolted feet get ears (printed_collar.py:115-117). 11.0 mm2 unsupported. The r7 collar passed.
- Fix: add an ear or 45 degree fillet under LR. Prove with print_overhang.

### VN-59 · minor · printability · latent · closable: cad
**Integral skin has no r7 bed chamfer**
- Sources: PRI-14 (confirmed).
- Evidence: vent_geometry.py:39 adds the skin as a sharp box on the bed face. r7 applies BED_CHAMFER 0.6 on every printed part.
- Fix: add the 0.6 mm 45 degree chamfer to the skin outline. Add a bed-edge chamfer check per part.

### VN-60 · minor · electrical-fit · latent · closable: cad
**EVF option C, diode sleeve and RCY junction volumes unplaced; stale ko_5v_up and PH text**
- Sources: ELE-6 (confirmed).
- Evidence: BOM D2-16P says "inside ko_5v_up", a keep-out that exists only in r7. No diode, RCY or LDO volume exists in the candidate geometry. routes.py:611,737 still mention a PH pair. ASSEMBLY:248 names a provisional 32 x 7 x 7 reserve that is not placed.
- Fix: place and check volumes for the diode sleeve, RCY pair and an option-C carrier on the usb_5v route. Replace the stale text.

## E. Electrical and BOM

### VN-61 · major · wiring-docs · latent · closable: docs
**No candidate wiring specification; ASSEMBLY points to r7 WIRING**
- Sources: ELE-2 (confirmed).
- Evidence: the commit did not touch electronics/ or software/. WIRING.md still describes the plunger (:43, :64), the JST PH pigtail on the 18/24 lugs (:371) and a PH plug on the EVF lead (:373). ASSEMBLY-VERTICAL.md:137 says "Prepare the baseline EVF feed, 18/24 lead and QT lead"; :220 says "within qualified lanes" (none exist). J2 genders, RCY polarity colours and the diode band are not stated. routes.py:651 says "lower USB2"; the geometry uses the upper port.
- Fix: write a generated WIRING-VERTICAL.md: block diagram, header and J2 table, harness schedule (both ends, lengths with tolerance, genders, colours, polarity), plug and unplug order. Mark r7 WIRING as superseded for this fork and fix the port naming. Add a test that the generated schedule matches the BOM and route sources.

### VN-62 · major · power · latent · closable: user_decision (computed row closable now)
**Pigtail drop margin uses solid-wire resistance; no G-W5 fallback left**
- Sources: ELE-1 (confirmed major), DES-17 (existing, minor).
- Evidence: make_bom_vertical.py:273-274 uses 13.17/21 mohm/m and only asserts equality to a constant. The PRC page gives "over 250 x 0.08 mm" strands, so at least 13.6-13.7 mohm/m. That cuts the 7.19 mV margin to about 4.8 mV from the pigtail alone. A hot fuse would likely use up the rest. r7's fallback ladder ended at 16 AWG, already used here, and 250 mm was rejected for service. Not a regression in modelling: r7's cold-only model at 60 C gives about 0.156 V.
- Fix now: a computed row from vendor strand area and a stated resistance range that asserts drop_hi <= 0.150 V. Never relax 0.150 V. User decision: the G-W5 fail branch (shorter path, 14 AWG with lane re-check, or a higher software cut-off).

### VN-63 · minor · connector-safety · latent · closable: bom
**J2 and FPS use the same unkeyed all-black Molex pair**
- Sources: ELE-4 (confirmed).
- Evidence: BOM D2-27 and V-28 both use Molex 2181110202 + 2181120201. REVIEW.md:213-214 relies on labels. J2 gender is unstated, so one J2 half can mate an FPS half. Both are open together during panel removal. A cross-mate can hold PWR_BUT to ground (shutdown, then boot cycling). D2-23 changed family for the EVF to prevent exactly this.
- Fix: a different family or circuit count for J2 (for example a 3-circuit housing with a blanked cavity, or GH/SH). Otherwise fixed genders plus coloured sleeves. Add a BOM check row that no two junctions share an unkeyed mateable pair.

### VN-64 · minor · bom · latent · closable: bom
**BOM spares, SKUs and purchase-view gaps**
- Sources: ELE-11 (confirmed parts; the D2-61 socket and missing prices were refuted).
- Evidence: V-23S is qty 0 (r7 bought a spare pair). D2-27 and V-28 order the same SKUs on separate lines, with no combined total or spare for 30-cycle contacts. No spare 3562 ribbon or heads. D2-26 "black colour selection" has no SKU. The 625-query figure is in VN-08.
- Fix: a consolidated buy view grouped by SKU, a spare policy (RCY, PicoBlade, ribbon) and a black-wire SKU. Add a BOM check that duplicate SKUs are summed.

### VN-65 · minor · usability · latent · closable: user_decision
**Power button unguarded, about 5 mm proud of the side panel**
- Sources: ELE-5 (confirmed).
- Evidence: model.py:423 places the 1505 cap Y28..33 on a panel face at Y28. r7 recessed the plunger face 1.3 mm behind a guard rim (layout.py:530-537). A 2 s hold ends a take.
- Fix: user chooses a printed guard ring or recess, or a flush switch. Add the choice to G-V-POWER.

### VN-66 · minor · electrical-fit · latent · closable: measurement
**20 AWG RCY tails soldered directly onto the EVF board's small EXT+/GND pads**
- Sources: ELE-7 (confirmed).
- Evidence: ASSEMBLY:240-245 joins 20 AWG silicone tails to two traced pads. r7 used a 24-26 AWG pigtail there. No pad-size row in MEASUREMENTS-TO-CLOSE.
- Fix: measure the pads. Prefer a short 24-26 AWG pigtail to the 2181 tail, with strain relief at the board edge. Add an MTC row.

## F. Thermal

### VN-67 · minor · thermal · latent · closable: measurement
**Cooler fin exhaust aims at the camera rear**
- Sources: DES-7 (verifier minor).
- Evidence: in the proxy the fin exit is at X-36.05, Z13.75..56.25 and the camera rear at X-25.09, Z40.25..82.1. That is 37.6% of the exit height at a 10.96 mm gap with a clear path. The +X exit direction comes from the datasheet, not a measurement. No candidate doc mentions it.
- Fix: add the cooler exhaust direction to the Pi/cooler MTC row and a camera thermocouple to G-V-THERMAL. Consider a deflector toward the hot slots if confirmed.

### VN-68 · minor · thermal · latent · closable: measurement
**Front hot-mouth plume rises over the collar clamp lug (M1)**
- Sources: PRI-11 (confirmed).
- Evidence: the front hot mouth (Z5..40) exhausts +X. The s_c4 lug sits about 10 mm above and overlaps it over y -30..-28. Neither G-V-THERMAL nor M1 mentions lug temperature.
- Fix: add lug temperature and preload retention to the powered thermal test.

## G. Existing documented holds (hardware or user)

### VN-69 · major · interference · existing · closable: measurement
**Main-audit failure: pi5/cooler overlap 79.902671 mm3**
- Sources: EVI-18, DES-14 (confirmed); MTC row "Pi 5 plus official Active Cooler".
- Evidence: the only failure in verification.json, bbox x -100.8..-56.2. The reconciler keeps it as the single failure. The cooler is an illustrative proxy (model.py:364).
- Fix: measure cooler registration and outline, re-model and re-run. Never reclassify the failure.

### VN-70 · major · printability · existing · closable: measurement
**G-V-PRINT: slicer, coupons and support review not run**
- Sources: DES-15 (confirmed); README print hold; REVIEW s5 rows; MTC plenum row.
- Evidence: front mouth may need about 35 mm bridging; slicer_state "NOT RUN"; coupons and dry assembly not run.
- Fix: after VN-51 to VN-54 and VN-57 to VN-59, slice and print the plenum coupons plus a tine coupon before any tub.

### VN-71 · major · thermal · existing · closable: measurement
**G-V-THERMAL: the concealed-plenum thermal path is unproven**
- Sources: DES-16 (confirmed); MTC airflow row. The PRI-12 claim that hand/strap occlusion is the normal case was refuted (Appendix A); occlusion cases are already required.
- Evidence: smallest sampled hot section 299.4 mm2 vs 510 mm2 of wall slots; 210 mm2 front mouth only if the underside is blocked; the CSI slot is an unsealed bypass.
- Fix: closed-body thermal test with hand, strap and support cases, with VN-36 as the computed pre-check.

### VN-72 · major · power · existing · closable: measurement
**G-V-PIGTAIL: 270 mm path cuts and flexible withdrawal STOP**
- Sources: ELE-12 (confirmed); ASSEMBLY:127-136 STOP; STOP checkpoint; MTC pack/XT30 row.
- Evidence: power-service-checks.json has remaining_stop = 5, physical_qualified false; only rigid poses checked.
- Fix: non-energised routing mock-up, then the flexible-core reach check (VN-47) and the G-W5 row (VN-62).

### VN-73 · major · power · existing · closable: measurement
**G-V-POWER: 1505 switch, nut and tool, J2 pads and connector unplaced**
- Sources: ELE-13 (major), PHY-14, DES-18 (minor), all confirmed; MTC 1505/J2 row; REVIEW s5 "other tool reach pending".
- Evidence: model.py:424 "UNVERIFIED nut reserve OD22x3"; the J2 position is a hypothesis; V-62 tool qty 0; 30-cycle connector. The microSD closed-panel path is REJECTED because of this switch.
- Fix: measure the real 1505 and J2, then place the J2 pair and run a manifest-bound check. See VN-46 for the tool rule.

### VN-74 · major · harness · existing · closable: measurement
**G-V-SERVICE: camera FPC unplaced; Pi CSI latch reachable only via the 12 x 27 slot; module-removal STOPs**
- Sources: DES-21 (confirmed), PHY-12 STOP part, PHY-4 slack-store part; ASSEMBLY:214, :237 and :302 STOPs; MTC camera-cable and 200 mm FPC rows.
- Evidence: REVIEW.md:27,295 say the full FPC is unplaced. Only a strip about 3.9 mm wide remains for slack. r7 BX-8 (FPC S-fold) never landed either.
- Fix: measure both FPC ends and the real cable, then place the full FPC with a reserved slack store and a route/stow check. Bench-test the latch through the slot.

### VN-75 · minor · harness · existing · closable: measurement
**G-V-HDMI: DIY HDMI assembly physically unqualified**
- Sources: ELE-14 (confirmed); MTC HDMI row. Fix covered by G-V-HDMI and G-W7; new: buy a spare ribbon (VN-64) and add the face check (VN-35).

### VN-76 · minor · storage · existing · closable: measurement
**G-V-STORAGE: compact body depends on an unproven SSD**
- Sources: ELE-15, DES-20 (confirmed); MTC Princeton row. Linux is not on the vendor's OS list; G-W10 warm write test open. Fix: bench the SSD on a Pi 5 first and log bus current with the EVF lead.

### VN-77 · minor · structure · existing · closable: measurement
**G-V-STACK: real standoffs, screws and carrier retention**
- Sources: REVIEW s6 G-V-STACK; MTC X1203 row; DES-19 physical part. Fix: measure the stack hardware and run coupon/torque trials; VN-38 is the computed part.

### VN-78 · minor · structure · existing · closable: measurement
**G-V-STRAP: grip lock, strap anchors and tool reach with the strap fitted**
- Sources: REVIEW s6 G-V-STRAP (no reviewer flagged it). The p_grip driver handle clears the strap by 1.37 mm (r7: 2.35), noted under DES-3. Fix: load test; include the strap in the driver check (VN-23).

### VN-79 · minor · harness · existing · closable: measurement
**CK1044 and FPS donor parts behind the 332-check scoped result**
- Sources: MTC CK1044 row (no reviewer flagged it). Terminal, donor-head, solder-root and support datums are provisional. Fix: measure, then re-run verify_fps_integrated.

### VN-80 · minor · power · existing · closable: user_decision
**EVF 5 V diode feed kept although r7 expects G-W6 to fail; option C at qty 0**
- Sources: ELE-16 (confirmed). Fix: user decides on option C before build; if adopted, place volumes (VN-60).

### VN-81 · info · power · existing · closable: measurement
**Inherited power envelope: 27 W planning peak above the X1203's 25.5 W** (not second-pass verified)
- Sources: ELE-17. 8.6 A sizing assumes a 3.3 V software cut-off; 25.5 W at 3.0 V draws 9.44 A. Fix: keep G-W12/G-W5 and test low-cell shutdown.

### VN-82 · major · release-gates · existing · closable: measurement
**Collar M1 and all 56 inherited physical gates open**
- Sources: REVIEW s5 (no reviewer flagged it as new). M1 collar creep and the revised collar's load and clamp validation are open. See VN-50 for the stale gate list. Fix: physical gates; the computed collar checks are VN-24 and VN-55.

### VN-83 · info · handling · latent · closable: user_decision
**Balance differs by lens** (not second-pass verified)
- Sources: PRI-16. CoM vs grip axis: compact Kowa 0.63 mm ahead, Fujinon 11.19 mm behind, original Kowa 6.99 mm behind (r7 Kowa 1.55 mm ahead). Fix: state per-lens balance in REVIEW; a balance rule is the user's call.

### VN-84 · info · appearance · latent · closable: user_decision
**Panel fixings now visible on the control face** (not second-pass verified)
- Sources: DES-13. r7 hid them below and on the right; the candidate puts four PH1 heads on the +Y face. Service is simpler. Fix: user choice; printed press-in caps if hidden heads matter.

## Appendix B. Documented-hold coverage map

| Candidate hold | Register entry |
|---|---|
| Main audit fail pi5/cooler 79.902671 mm3 | VN-69 |
| Print hold (front mouth ~35 mm) | VN-52, VN-70 |
| G-V-STACK | VN-77, VN-38 |
| G-V-STORAGE | VN-76 |
| G-V-POWER | VN-73, VN-46, VN-65 |
| G-V-HDMI | VN-75, VN-35 |
| G-V-PIGTAIL | VN-72, VN-47, VN-62 |
| G-V-SERVICE | VN-74, VN-42 |
| G-V-PRINT | VN-70, VN-51 to VN-54 |
| G-V-THERMAL | VN-71, VN-36, VN-67, VN-68 |
| G-V-STRAP | VN-78 |
| STOP checkpoint (FPC/EVF feed unplaced, storage reservation, flexible withdrawal, hand/tool access) | VN-74, VN-49, VN-76, VN-72 |
| ASSEMBLY:130 pigtail cut STOP | VN-72 |
| ASSEMBLY:214 FPC latch STOP; :237 loom/FPC release STOPs | VN-74 |
| Module-removal STOPs (FPC release, pigtail withdrawal, run-lead reach) | VN-74, VN-72, VN-45 |
| REVIEW s5: tool reach pending | VN-23, VN-73 |
| REVIEW s5: slicer, coupons, dry assembly not run | VN-70, VN-77 |
| REVIEW s5: powered, storage, thermal, electrical, EMC not run | VN-71, VN-75, VN-76 |
| REVIEW s5: 56 inherited gates, M1 | VN-82, VN-50 |
| MTC: Pi 5 + Active Cooler | VN-69, VN-67 |
| MTC: camera cable interfaces; 200 mm camera cable | VN-74 |
| MTC: HDMI heads and ribbon | VN-75 |
| MTC: 4448 USB donor | VN-49 |
| MTC: Princeton drive | VN-76 |
| MTC: X1203 kit, carrier screws, coupons | VN-77 |
| MTC: 1505 switch and J2 harness | VN-73 |
| MTC: CK1044 and FPS donor parts | VN-79 |
| MTC: pack, XT30, fuse, pigtail | VN-72, VN-62 |
| MTC: microSD and panel switch | VN-29 (check scope), VN-73 |
| MTC: plenum and panel coupons | VN-70 |
| MTC: airflow and handling | VN-71 |
| FPS hand coordination (FPS-SERVICE-STUDY) | VN-48 |

## Appendix A. Refuted findings (dropped)

| Finding | Why it was dropped |
|---|---|
| PHY-15 battery pigtail called "camera pigtail" | Project naming is device-side vs pack-side and is used consistently (BOM-VERTICAL.md:99). The camera ribbon is always "camera FPC". Wording only. |
| EVI-9 CSI adjacent-wall evidence stale | Current shadow-plenum-checks.json (bound to 53e668d4) has csi_sleeve rays 1 mm outside the slot box with 5.8 mm material. The aperture row tests a real requirement. |
| ELE-8 silver contacts on a dry-circuit GPIO | Same Lorlin CK family as r7. Rotary wafer contacts wipe on every turn; the ~50 kohm pull-up reads low up to ~16 kohm. An external pull-up is optional only. |
| PRI-12 hand/strap occlusion is the normal case | The strap envelope ends 6.3-12.3 mm inboard of the mouth band. It overlaps 20 of 71 mm of the cold underside mouth and none of the hot one. Occlusion cases are already required. |
| DES-9 size gain hides the storage swap | REVIEW s2 already lists same-drive +3.3% / +9.1% and the 7.6 mm plenum cost next to the -6.8%. |

Partial refutations folded into kept entries: R-1 count is 60 of 71 sources, not 71 (VN-01). PHY-2 "panel-off service impossible": a dog-leg path is clear (VN-29). EVI-5: no collision is hidden today (VN-22). PRI-2 "blocker": printing is already held, so major (VN-51). PRI-8 "2.25x J4 model dropped": it is the r7 geometry (VN-20). ELE-3 panel-off reach failure: about 115 mm needed vs 240 (VN-28). ELE-10 "--check still passes after CRLF regeneration": it fails anyway on encoding (VN-03). ELE-11 D2-61 socket and missing prices are deliberate (VN-64). EVI-11 plenum/outlet verifiers outside the runner is by design (VN-07). PHY-4 r7 ko_fpc_loop occupancy argument used bounding boxes only (VN-44). REP-4 project content partly licensed (tools/, gs8-camera-evf are MIT) (VN-13). REP-5 duplication is about 104 MB in the working tree; the pack delta-compresses it (VN-16).

## Fix plan (everything closable now)

There are no blockers. Order: repo safety first, because every regeneration depends on it. Then evidence tooling, the assembly-state model and build order, the ported checks (each one must fail on the known defect before the CAD fix lands), the CAD fixes, and finally one full evidence refresh. All CAD work runs serially through run_locked.py in the rebuild worktree, never in the snapshot clone.

| Step | Closes | Approach and files | Proof (a check that catches a regression) | Depends | Hours |
|---|---|---|---|---|---|
| FP-01 Repo-level safety | VN-01, VN-13 (size VN-16 after decision) | .gitattributes: `* -text` first, binary `-diff` after. `core.autocrlf=false` in both trees; re-check out CRLF files. THIRD-PARTY-NOTICES.md plus LICENSE.txt beside every Pi-derived STEP. Size actions only after the user decides. | test_repo_eol.py: `git check-attr text` unset for every tracked file; no CR in tracked text; emulated `-c core.autocrlf=true checkout-index` tree gives identical hashes; r7 `audit_cloud_release.py --final-release` passes on it. Notice test: every folder with pi5*.step has LICENSE.txt. | none | 2 |
| FP-02 Cross-platform I/O | VN-02, VN-03 | New candidate-vertical/_io.py (utf-8 read, utf-8 + `\n` write, posix relpath). Replace bare calls in all 108 scripts (script-assisted). export_candidate.py, make_corrected_pi.py, update_concealed_vent_structure.py:38 use `.as_posix()`. run_locked.py sets PYTHONUTF8=1 as a guard. | AST lint test: no text I/O without encoding/newline, no `str(relative_to)` in recorded paths. Key test: no backslash in any manifest or report key. Windows smoke: make_bom --check, structural --check and docs-audit --check pass on the unchanged snapshot. | FP-01 | 5 |
| FP-03 Bound files and deterministic export | VN-04, VN-17 | Normalise the STEP header time in export_candidate.py. Then, per the user's choice, commit mesh JSONs and guide pages for the nominated manifest (~100 MB), or move them to a separate optional cache manifest. No binding is deleted. | Fresh `git clone` to temp: reconciler and docs-audit --check exit 0. Two exports in a row give byte-identical STEP. | FP-01, FP-02, decision | 3 |
| FP-04 Evidence tooling hardening | VN-05, VN-06, VN-08, VN-09, VN-31, VN-32 | Docs audit: non-zero exit, `--check`/`--out`, guide manifest comparison. Structural refresh with numeric tolerance. Numbers formatted from source rows. Reconciler rejects foreign-manifest reports in the selected folder and asserts the exact info set. Mesh rows get binding fields. Stale reports move to history/. | Fixture tests: tampered source makes the audit exit 1; 1e-13 passes and 1e-3 fails; a planted foreign-manifest JSON fails the reconciler; a grep test finds no generated number that differs from its source. | FP-02 | 4 |
| FP-05 Assembly-state model | VN-22 | candidate-vertical/steps.py with STEPS / present_at for the corrected order (built together with FP-06). Motion fixed sets and driver contexts derived from it. | Test: each motion's obstacles = present parts minus movers. Lint: gauge never present with camera or adapter. Motions re-run. | FP-02 | 4 |
| FP-06 Build order and service text | VN-39, VN-40, VN-41, VN-43, VN-44, VN-45, VN-46; VN-42 docs part | ASSEMBLY-VERTICAL.md, FPS-SERVICE-STUDY.md, both guide builders: collar + gauge before camera; lens + s_c4 with turn-back before the carrier; FPS nut/washer/knob refit in step 6; EVF matings in step 5; bench FPC pre-mate; grip row prerequisite; socket instead of spanner; service matrix with a lens-change row. Mark the guide PDF stale until it can be rebuilt (VN-12). | r7 lens_turn_back_lint on the doc. Order lint against steps.py. Lint that every service removal has its refit. No "spanner" in tool text. | FP-05 | 5 |
| FP-07 Straight-driver check | VN-23 | Port check_driver and check_service_driver for the 11 screws with FP-05 contexts. Strap included for p_grip. | Rows in the main audit. Test: a 6.0 mm counterbore fixture fails. Expected first result: carrier bores fail until FP-11c. | FP-05 | 3 |
| FP-08 J7-R and collar checks | VN-24 | Port j7_float (full BFAR range, 0.5/0.4 mm gaps), roll_catch, lens_support, lens_clamp, collar_gauge, inserts. Run r7 test_mechanical_refinements.py on the candidate collar values. | Rows in the main audit with per-obstacle minimum gaps. The washer case fails until FP-11d. | FP-05 | 5 |
| FP-09 Print checks | VN-25 | Port check_print_overhang, thin_wall, critical_features into run_shadow_checks.py. Add the per-region single-direction bridge rule. Declare the J4 wing zones. | r7 tub still passes the stricter rule. Candidate tub, carrier, grip and collar fail now. A long-bridge fixture fails. | FP-02 | 6 |
| FP-10 Harness and power checks | VN-26, VN-28; VN-47 and VN-62 check parts | Port cable_routes, mate_reach (minimum stock length, propped panel), lead_access/pigtail_drop (flexible cores, ties as fixed points), cable_stow, header_housings. Manifest-bound signal-route verifier; archive the orphan JSON. G-W5 drop row from vendor strand data with a range. | Rows in the main audit. A lead shortened 10 mm fails mate_reach. The drop row reports fail honestly for the hot-fuse case. | FP-05 | 6 |
| FP-11a Plenum roof and mouths | VN-51, VN-52, VN-59 | vent_geometry.py: flow-direction ribs at 10 mm pitch or less with lanes to the mouths, or a 45 degree roof; 45 degree lintels at all four mouths; 0.6 mm skin bed chamfer. Extend the coupon to the rear mouth. Fix hold text in README, REVIEW and CHECKPOINT. | FP-09 bridge rule passes. Plenum section and area checks re-run. Coupon covers all four mouths. | FP-09 | 5 |
| FP-11b Tab-catch printability | VN-53 | Separate upright-printed catch block held by the panel (no screw), or self-supporting chamfers. | print_overhang passes on the catch region; roll_catch passes. | FP-08, FP-09 | 3 |
| FP-11c Carrier | VN-54, VN-56 | Continuous +Y bed face to y 22.2; counterbores to 7.0 mm. | print_overhang and a bed-contact-area row pass; driver check passes; boss wall measured from the STEP. | FP-07, FP-09 | 2 |
| FP-11d Collar | VN-55, VN-58 | Restore at least 0.5 mm washer clearance and full flat support; ear under LR. | r7 mechanical tests and lens_clamp pass; print_overhang passes. | FP-08, FP-09 | 2 |
| FP-11e Grip pocket | VN-57 | 45 degree passage roof or declared zone off the J4 faces. | print_overhang passes; J4 slide clearance row. | FP-09 | 1 |
| FP-11f EVF feed volumes | VN-60 | Place diode sleeve, RCY pair and option-C reserve on the usb_5v route; remove stale ko_5v_up/PH text. | Interference rows for the new volumes; grep test. | FP-02 | 2 |
| FP-12 Check scope fixes | VN-29, VN-30, VN-33, VN-34, VN-35, VN-36, VN-37, VN-38 | microSD dog-leg motion; full obstacle sets for wires and HDMI; per-variant J4 screen; evf_restraint; HDMI face normal; flow-network model; area parity; stack_retention. | Each as a manifest-bound row in the batch, with a regression fixture. | FP-05 | 7 |
| FP-13 Variant audits | VN-27 | verify_candidate.py --variant for Fujinon and original storage on the final geometry. | Reconciler requires verification.json for every variant. | FP-11 | 1.5 |
| FP-14 Wiring and BOM | VN-61, VN-63, VN-64 | Generated WIRING-VERTICAL.md; distinct J2 connector; consolidated buy view, spares, black-wire SKU. | Consistency test between wiring, BOM and routes. BOM tests: duplicate SKUs summed; no two junctions share an unkeyed pair. | FP-02 | 5 |
| FP-15 Repo hygiene and docs | VN-07, VN-10, VN-11, VN-12, VN-14, VN-15, VN-18, VN-19, VN-20, VN-50, VN-21 reporting | Entry docs; link banners; toolchain lock and Windows commands; provenance labels; structural generator; studies/ folder; gate and BX mapping; per-category coverage in REVIEW/CHECKPOINT. | Repo-wide link check (live docs 0 broken, frozen copies bannered). Import test for pypdf and scipy in the pinned venv. Coverage table generated from verification.json. | FP-02 | 6 |
| FP-16 Final evidence refresh | rebinding for all of the above | In the rebuild worktree: re-export all variants, full batch, reconciler, BOM, structural, CHECKPOINT and guide receipt. Commit the run record. | Reconciler and docs-audit --check exit 0 on a fresh clone and on an emulated autocrlf clone. | all | 3 |

Total about 80 hours, plus about 40 minutes of CAD time per full refresh. Given the usage budget, a sensible split is: Phase 1 FP-01 to FP-06 (about 23 h: reproducible repo and correct build order). Phase 2 FP-07 to FP-10 and FP-12 (ported checks). Phase 3 FP-11, FP-13 to FP-16 (CAD, docs, refresh).

## User decisions

1. Whether to keep developing the vertical fork or treat r7 as the build baseline. The candidate is not yet an improvement over r7 and carries a large check debt.
2. VN-04 / VN-16: commit about 100 MB of mesh caches and guide pages, or split them out. Repo size: dedupe the Pi STEP; move assembly STEPs to Release assets or LFS.
3. VN-13: a licence for the project's own CAD and docs content.
4. VN-62: the G-W5 fail branch (shorter path, 14 AWG, or a higher software cut-off).
5. VN-42: accept carrier-out camera and lens-change service, or redesign the camera exit or the gauge.
6. VN-47: carrier ties or r7's RTV-only retention.
7. VN-29: close the front microSD slit or keep it.
8. VN-36: a CSI plug only after the flow model.
9. VN-65: power-button guard ring, recess or flush switch.
10. VN-80: EVF option C.
11. VN-45: an inline run-lead junction, or "module out first".
12. VN-48: printed transport clip or a helper for step 4.
13. VN-63: which J2 connector family.
14. VN-83 / VN-84: a balance rule; press-in caps over the panel screws.
15. Whether and when to push fixes to the public repo.
16. VN-53 / FP-11b (added 2026-10-11, proposed by the T2 lane; see the T2 lines in the fix log): how the separate +Y tab-catch stub is retained in the tub. **Default pending user decision 16:** the stub is bonded into the tub at B1 `print_inserts` with two-part epoxy (BOM consumable V-68). The bond holds at `lens_in`, where the panel is still off, and keeps the computed catch faces identical. Alternatives: (a) a press fit with a printed detent; (b) the panel-held block from FP-11b, which is valid only if the lens is fitted with the panel on (today `lens_in` runs panel-off). The G-V-PRINT tab-catch tine coupon in MEASUREMENTS-TO-CLOSE.md tests the bond.
17. VN-37 (added 2026-10-11, from the fix-up orchestrator FX): the hot plenum bay cannot reach full path-aware area parity with the current hot wall ports and mouths. Even the bound for an empty bay is below the 510 mm2 of hot wall ports: the region that holds the ports (x -62..-2.5, z 16..40) is bounded by about 493.2 mm2 of free section (plenum_flow nominal empty-bay bound), and the trial3 ribs leave a path minimum of 444.5 mm2 on the saved STEP (check_scope area_parity hot_path_min_cut; cold 420 of 420 passes). Options: (a) enlarge the hot mouths, for example by removing the front-mouth mullion or widening the mouth rectangles; (b) make the hot wall ports smaller or move them; (c) accept the measured path minimum and rely on a thermal test (G-V-THERMAL); (d) a different 2.5D roof support (e.g. a 45 degree self-supporting roof) that needs fewer ribs, which still cannot exceed the empty-bay bound. **Default pending user decision 17:** keep the current ports and mouths and report the hot `path_min_cut` row as failing.

## Other suggestions

- Run r7 checks.py on candidate rows through one adapter, so later r7 fixes reach both lines.
- Add a Windows CI job (and the emulated-autocrlf clone test) that runs every `--check` command.
- Bench order: Pi plus cooler measurement first (it closes the only failure), then the SSD on a Pi 5, then the plenum and tine coupons, then FPC lengths.
- Add a pure-numpy rasterizer fallback so the guide can be rebuilt on Windows.
- Consider keeping the vertical line as a branch of digital8mm instead of a separate repo, to avoid drift between two working copies.
