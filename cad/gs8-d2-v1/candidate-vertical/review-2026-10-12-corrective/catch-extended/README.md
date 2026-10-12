# Extended bonded-stub cases for the +Y tab catch

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
