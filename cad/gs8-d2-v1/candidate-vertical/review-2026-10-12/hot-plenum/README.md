# Hot-plenum corrective study, 2026-10-12

This directory retains rejected candidates, an isolated geometry/print study, and scoped proofs against the selected saved whole-tub exports. It is not a physical release. The baseline is commit `bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f`; frozen copies of its two plenum sources are under `baseline/`. `study-index.json` binds those copies. The active model remains in the candidate root, not here.

## Selected same-envelope correction

Keep the original 6 mm gap, 1.6 mm outer skin, four hot wall ports totalling 510 mm², CSI sleeve, purchased cooler and external dimensions. Extend the front edge opening as three clear rectangles:

| Z interval (mm) | Y interval (mm) | Area (mm²) |
|---|---|---:|
| 5–20.4 | −34 to −28 | 92.4 |
| 21.6–48.4 | −34 to −28 | 160.8 |
| 49.6–58 | −34 to −31.5 | 21.0 |

The lower and upper 1.2 mm mullions are centred at Z21 and Z49. The existing Z49 roof-support row is continued through the front frame; beam thickness and all other support rows stay unchanged. The upper slot occupies only the outer 2.5 mm of the existing gap, outside the collar's nominal Y minimum of −30.8. The 0.7 mm nominal separation is geometry, not an as-printed clearance measurement.

`probe_supported_step.json` records candidate capacities. `supported-step-validation.json` records the selected simplified CadQuery body: valid single solid; hot minimum cut 509.999996 mm² against the unchanged 510 mm² requirement and 0.002 mm² tolerance; no blocked wall-port area; minimum front neck 274.2 mm², inboard section 304.0 mm²; overhang, single-direction bridge and bed-chamfer checks pass, longest computed bridge 27.1 mm.

`check-scope-flow-compact-kowa_lm6hc.json` repeats the area and flow measurements on the saved whole-tub STEP from manifest `294220bc7e1babc507e00d41542d108bfbf172250e45f20ba828e83437634ae4`: hot cut 509.999996 mm², cold cut 420.0 mm², zero blocked port area, hot branch series sum 575.2 mm². All four unchanged area gates pass. The saved primary mouth report confirms the 274.2 mm² minimum front neck. The saved outlet-context report also passes its strengthened front entry/continuation prisms from X−2.7 to X+12 mm, with zero collar or screw intersection. These are geometric results, without an installed fan operating point.

The scoped `check-scope-flow-*.json` reports retain the old baseline-drift failure as a diagnostic. `refresh_flow_baselines.py` writes the reasoned baselines only after all three exports pass the fixed area gates, retaining the complete prior baseline objects. The final full check-scope reports must then be regenerated to prove those refreshed baselines.

`flow-baseline-refresh.json` records the completed three-variant run. Compact Kowa, compact Fujinon and original-length Kowa all return the same hot/cold cuts, hot branch sum and front neck above. The original-length cold-bottom mouth is 503.28 mm² with a 705.0 mm² minimum series section; both compact versions are 370.44 mm² and 543.0 mm². All three retain the 522.0 mm² cold-rear series minimum. Each baseline keeps its prior history and the 1e−6 drift tolerance; the primary chain remains trial4 → trial3 → FP-11a.

`final-plenum-proof-receipt.json` binds all three scoped proofs and refreshed baselines by full SHA-256, records the final source/test hashes and exact commands, and retains the resolved numerical-consistency finding. `focused-test-results.json` remains the earlier 18-test geometry/print snapshot with its original source hashes. The later rounding-bound tests pass 2/2 and the refreshed baseline/history test passes 1/1. The narrow trial4 full-report expectation is updated, pending the final combined check-scope run.

Frozen production/verifier source SHA-256 values:

- `vent_geometry.py`: `05faaebd36dcc48d450f99d49733c00798891e409054b1b514ba892b106f5f84`
- `plenum_flow.py`: `e76cabf5f90b1ea0b6c7676c9c01b7c1999a6a998e17cf1723fe64af40fb4d89`
- `verify_check_scope.py`: `e9479e6d589baea68a16ef47d773357560fa15a4b796d67277efd1574ee98566`
- `verify_shadow_plenum.py`: `ce776a21cf6e6bd899f74cb0f56852577da0d7eb23b43adb4a1712d38ecb3485`
- `verify_shadow_outlet_context.py`: `590a8f76b66aeb5d06074dbed88b4cf332763ee79e2f1c7984437bbe1cf720c6`

## Rejected or diagnostic candidates

- Original trial3: hot path 444.5 mm²; even the empty bay reaches only 493.2 mm². Deleting internal posts/ribs cannot solve the original geometry.
- Full-gap front extension to Z54: nominal path reaches 510 mm², but its outward 12 mm prism intersects the saved collar by 76.8113 mm³ and screw by 6.8383 mm³. Rejected.
- Short full-gap outlet to Z49.8 with an upper support row moved to Z54: 503.3 mm². Reducing the beam from five to three layers reaches only 508.38 mm². Rejected.
- A stepped outlet without a second mullion can reach 510 mm², but that was not selected: the second mullion supplies a clear two-ended support for the upper lip's first bridge.

The current mouth metadata measures nominal inboard rib material as well as the visible face. A regression restoring the original mouth reproduces face 202.8 mm² and true smaller inboard neck 197.2 mm²; the old 5.6 mm² overstatement is not hidden by the new geometry.

The first complete section regression also exposed a pre-existing cold-rear sampling miss: the regular planes reported 534 mm² while an interval through a narrow pillar measured 522 mm². `plenum_flow.section_sample_planes` retains the original planes and adds source rib-face interval midpoints. This is a checker correction, with no cold geometry change and no threshold reduction. The saved-STEP minimum-cut gate remains independent.

The graph uses integer capacities at 10,000,000 units/mm². Independent nominal and empty-bay subdivisions return raw hot totals of 510.0000052 and 509.999995 mm² even though both cuts are the same 510 mm² source-port surface. Each selected cut reports its capacity count and accumulated rounding bound, at most one half-unit per capacity. The nominal-versus-empty consistency test uses only the sum of those two bounds (0.000229 mm² here); an excess beyond it still fails. This arithmetic diagnostic never changes the 510/420 mm² requirements or their 0.002 mm² acceptance tolerance, and raw graph values remain in the reports.

## Reproduce

From the repository root, use the pinned CAD interpreter and serialize each command:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/review-2026-10-12/hot-plenum/probe_supported_step.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_plenum_trial2.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_fx_fixup.py MinCutFixtures Trial3Nominal Trial3Layout
```

After all three selected exports exist, the exact final proof/baseline and focused regression commands are:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/review-2026-10-12/hot-plenum/refresh_flow_baselines.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_fx_fixup.py MinCutFixtures.test_quantization_allowance_rejects_a_larger_excess Trial3Nominal.test_hot_value_and_empty_bay_bound
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_plenum_trial2.py Wiring.test_flow_baseline_rewritten_with_reason
```

The first command holds one lock while running the three area/flow verifiers serially, then writes the baselines only after all pass. Its child commands are recorded in the final receipt and intentionally do not take nested locks. The rejected trial3 path/empty-bay values, pre-refresh baseline-drift rows, old mouth-area overstatement, missed cold section, and initial numerical-consistency assertion failure remain explicit diagnostics rather than being deleted or accepted by relaxed thresholds.

The other `probe_*.py` files reproduce the rejected diagnostic scans from frozen baseline sources. Their timings are incidental. Actual slicing, printing, cleanout, surface concealment from all viewing angles, real CSI service, fan operating point, pressure loss, warm-air recirculation, hand/strap occlusion and temperatures remain unqualified. Geometric area is not delivered airflow or cooling.
