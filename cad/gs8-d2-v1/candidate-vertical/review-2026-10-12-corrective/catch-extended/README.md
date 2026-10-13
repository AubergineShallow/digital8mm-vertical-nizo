# Extended bonded-stub cases for the +Y tab catch

> **Restored by the 2026-10-13 fix pass (review 2026-10-13 R-02).** This README is again the corrective reviewer's `f9704ac` text; the delivered followup had prepended its own section and rewritten the tool in place. The reviewer's tool is preserved byte-exact as [`catch_extended_cases_f9704ac.py`](catch_extended_cases_f9704ac.py) (git blob `8b6c189`); the section "What this is" below describes that file. The file now at `catch_extended_cases.py` is the delivering agent's (`dot`) rewrite, which calls the main audit's own pose generator `roll_catch_stub_rows`. It stays at this path for now because the guide receipt, the three `catch-acceptance-*.json` receipts and the structural PDF receipt bind it by this path and hash; moving it, and `catch_saved_receipt.py`, to the followup folder needs a guide and structural PDF rebuild and is an open item. The three `catch-acceptance-*.json` receipts record the purpose "Independent rerun of main bonded-catch acceptance"; that label is inaccurate. They are a same-implementation rerun by the delivering agent, bound to the previous path and label. The delivering agent's notes are kept unchanged at the end of this file. To reproduce the historical witness, use `catch_extended_cases_f9704ac.py` in place of `catch_extended_cases.py` in the command below, with the frozen `f9704ac` source and STEP snapshot; the delivering agent had replaced the reproduce heading with a warning to the same effect.

Review 2026-10-12 (corrective), findings GEO-1, GEO-2 and CHE-2. **Result: FAIL. The catch is OPEN and user decision 16 (bonded stub) is not closed.**

## What this is

The +Y camera tab catch is a separate printed stub. It is bonded into a tenon pocket under the tub roof (`model.tab_catch_split`). The main audit grades the bonded stub in five displaced poses (`j7_collar_checks.STUB_CASES`): x +-0.1, film +y 0.05, and two tilts about x of 0.1 mm over the 10 mm tenon. With the 1b59395 tenon, the window passes in those poses with a worst gap of 0.106 mm against the 0.10 mm rule, a margin of 6 um.

`catch_extended_cases.py` adds the poses that the five cases leave out. It uses the same machinery without changes. It rebuilds the tub as print stock plus the displaced stub, as `roll_catch_stub_rows` does, and grades each pose with `j7_collar_checks.roll_catch_rows`. That is r7 `check_roll_catch` with its rules unchanged, over the full BFAR range of the variant lens. It keeps the rows that `roll_catch_stub_rows` gates: window and first contact. The design is not touched: the script loads the committed STEPs of one variant and checks each one against the manifest.

| Case | Pose | Basis |
|---|---|---|
| `tilt_on_joint_edge` | about x, -atan(0.1/h), pivot at the datum joint edge | the committed STUB_CASES pose. Validation: its rows must equal the committed `stub_tilt_on_joint_edge:*` rows |
| `T02_tilt_on_joint_edge` | about x, -atan(0.2/h), same pivot | full pocket y clearance (`TAB_CATCH_POCKET_CLEAR` y 0.2) |
| `T02_tilt_on_tenon_top_edge` | about x, +atan(0.2/h), pivot at the upper datum edge | full pocket y clearance |
| `Y1_yaw_pivot_xminus`, `Y2_yaw_pivot_xplus` | about z, +-atan(0.1/3.1), pivot on either x edge of the datum | the same 0.1 mm film variation, across the tenon width |
| `R1/R2_roll_film_*` | about y, +-atan(0.1/6.3), pivot on either x edge of the joint face | 0.1 mm film variation across the joint face |
| `R3/R4_roll_clear_*` | about y, +-atan(0.1/h), same pivots | pocket x clearance over the tenon height |
| `info_committed_tilt_on_tenon_top_edge` | the committed upper-pivot pose | feasibility only, not graded |

A pose whose displaced stub overlaps the print stock by more than 0.001 mm3 cannot occur inside the pocket and ceiling clearances. Such a pose is recorded as infeasible, with its overlap, and is not graded.

## Result (compact-kowa_lm6hc, manifest 294220bc)

- Validation: 26 of 26 `tilt_on_joint_edge` rows equal the committed main-audit rows (worst window gap 0.106).
- **T02 tilt at the full 0.2 mm y clearance: feasible (overlap 0), worst window gap 0.084 mm at all 13 BFAR positions (s 0 to 3.0), FAIL** (rule: worst offset >= 0.10, r7 `J7_TOL` 1e-3).
- **Y2 yaw of the 0.1 mm film variation about the +X datum edge: feasible (overlap 0), worst window gap 0.078 mm at s 0. FAIL at 7 of 13 BFAR positions (s 0 to 1.50), pass from s 1.75 up (0.099 at s 1.75 passes within `J7_TOL` 1e-3).**
- First-contact rows pass in every graded pose.
- Y1 (mirror yaw) passes at 0.129. The clearance-limited roll about y (R3, R4) passes.
- The 0.1 mm film roll across the joint face (R1, R2) and the upper-pivot T02 tilt are blocked by the ceiling and pocket walls (overlap > 0), so they are not graded.

compact-fujinon_hf6xa and original-kowa_lm6hc have not been run yet: `--variant compact-fujinon_hf6xa` / `--variant original-kowa_lm6hc`, about 10 min each on Windows. The lens and its BFAR range differ per variant, so their rows must be computed and cannot be carried over.

The per-variant records are `catch-extended-<variant>.json` (every row, bound to the manifest, the STEP and verification hashes, and the sources). `tests/test_catch_extended.py` checks the bindings and that the catch is reported as failing.

## Proposed geometry fix (next re-export)

1. Recess the stub catch face +Y by 0.05 to 0.1 mm. The worst cases fall 0.016 to 0.022 mm short of the 0.10 rule, so a 0.05 mm recess with margin, or 0.1 mm, covers them, provided the centred window (>= 0.30) and the first-contact rows still pass. And/or tighten the pocket y clearance (`TAB_CATCH_POCKET_CLEAR` y 0.2), or add a +Y locating rib, so that the tenon cannot tilt beyond what the catch tolerates.
2. Fold these cases into `j7_collar_checks.STUB_CASES`: yaw about z on both datum edges, tilt at the full pocket y clearance, and the clearance-limited roll about y. Add an overlap check so that a pose blocked by the pocket is reported rather than graded. The main audit then gates them, and this folder becomes a historical record.
3. Until then, the steps.py `print_inserts` text and the physical gate (MEASUREMENTS-TO-CLOSE, tine coupon: datum seating and tilt) carry the risk. A cure fixture that holds the datum face flat removes the tilt but not a wedge-shaped bond line (yaw).

Reproduce (repository root, Windows):

```
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/review-2026-10-12-corrective/catch-extended/catch_extended_cases.py --variant compact-kowa_lm6hc
.venv-cad\Scripts\python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_catch_extended.py
```

## Later additions by the delivering agent (dot, followup `a0bfed9`)

Kept as written by the delivering agent. "Same implementation" below means the delivering agent's rerun, not an independent check.

The `catch-extended-compact-kowa_lm6hc.json` below is now an immutable historical
failure witness, pinned by `tests/test_catch_extended.py`. Its 0.084 mm T02 and
0.078 mm Y2 minima describe the reviewed geometry, not later exports. Do not
regenerate it using a changed model with the old assembly STEP.

Current acceptance is integrated in `j7_collar_checks.roll_catch_stub_rows` and
therefore in each variant's main `verification.json`. It preserves the original
five cases, adds translation endpoints/corners, both signs at both bearing edges
about X, Y and Z, eight full-pocket yaw boundary hypotheses, and thirty-two
half/quarter-allowance coupled XYZ poses. X/Y limits come from transformed tenon
corners and the actual rectangular pocket. Z underseating is an explicit
0.1 mm numerical screen, not the cutter-overlap epsilon, a mechanical stop or a
qualified production tolerance. The adhesive escape groove does not enlarge
those bounds. Further withdrawal and bond retention remain unqualified. Every
pose records retained axial engagement, joint-face gap range and intersection between the
production host and transformed production insert (0.001 mm3 maximum); blocked
poses are explicitly identified. A rectangular-core fit is diagnostic only:
the actual open mouth/relief can admit a clear pose outside that proxy, and such
a pose must still receive all functional checks. Original blocked cases retain their legacy
diagnostic rows, with infeasibility stated. They provide no feasible-pose credit.
All feasible poses retain every BFAR sample and the original 0.30 mm centred,
0.10 mm worst-offset window and 1.0 degree first-contact margin. This is finite
sampling, not a continuous tolerance proof or a cure-fixture qualification.

`catch_extended_cases.py --variant ...` separately reruns those same main
checks and writes `catch-acceptance-<variant>.json`. It compares all its rows
against the current main audit, binds the separate production insert STEP as
well as the assembly STEPs, and fails on stale sources or missing rows. Run it
only after the final export and main verification. This checks reproducibility
with the same implementation; it is not an independent geometric algorithm.

`catch_saved_receipt.py --variant ... [--out ...]` is a CAD-free alternative
after that variant's full main audit has completed. It writes an explicitly
derived receipt (`evidence_mode: saved_full_audit`, `geometry_recomputed: false`),
retains every saved stub row and failure, checks the complete 69-pose policy,
all 13 BFAR samples and all window/contact offsets, and verifies the exact main
verifier, helper, export-source, manifest and STEP bytes before and after
derivation. The original CAD verdicts remain the execution evidence; the writer
does not remeasure intersections, distances or contact locations. A partial
audit, missing row, changed input, weakened threshold or inconsistent summary
is rejected. It refuses to overwrite an existing receipt. The guide identifies
saved-main evidence separately from an actual same-implementation rerun.

Neither receipt mode qualifies physical seating, continuous tolerances or bond
retention. No alternate variant inherits another variant's computed rows. The
historical results and original proposed corrective actions below remain
preserved for review.
