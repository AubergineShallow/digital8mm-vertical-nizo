# Shadow plenum inspection coupons

**UNQUALIFIED TEST GEOMETRY. No fabrication or physical release is granted.**

This directory contains three open-edge inspection crops from the saved tub. The [coupon index](coupon-index.json) binds each receipt; the receipts bind the source manifest, tub STEP, plenum report and exported STEP/STL files. Read their hashes before transferring a geometry result to a later tub revision. The current three crops bind corrective manifest `294220bc7e1babc507e00d41542d108bfbf172250e45f20ba828e83437634ae4`.

The crop names are retained file identities. “Regular grid” is a legacy name and does not mean that the selected tub uses the trial1 post grid. Current corrective geometry uses windowed beams on pillars and a stepped hot-front opening; the current saved-export reports establish its geometry. No supports or reinforcement are added merely to make a crop work.

<!-- coupon dimensions: source is coupon-index.json and its bound receipts -->
| Inspection crop | Source bounds, mm | Bed dimensions, mm | Files and receipt |
|---|---|---|---|
| Small inspection crop (legacy regular-grid name) | X -152..-104; Y -35.6..-25.5; Z 8..40 | 48 × 32 × 10.1 | [plenum-bridge-open-edge-coupon.step](plenum-bridge-open-edge-coupon.step), [plenum-bridge-open-edge-coupon.stl](plenum-bridge-open-edge-coupon.stl); [receipt.json](receipt.json) |
| Ports, service opening and edges | X -110..0; Y -35.6..-25.5; Z 0..100 | 110 × 100 × 10.1 | [plenum-port-service-open-edge-coupon.step](plenum-port-service-open-edge-coupon.step), [plenum-port-service-open-edge-coupon.stl](plenum-port-service-open-edge-coupon.stl); [port-service-receipt.json](port-service-receipt.json) |
| Whole plenum with all four mouths | X -158..0; Y -35.6..-25.5; Z 0..100 | 158 × 100 × 10.1 | [plenum-all-mouths-coupon.step](plenum-all-mouths-coupon.step), [plenum-all-mouths-coupon.stl](plenum-all-mouths-coupon.stl); [all-mouths-receipt.json](all-mouths-receipt.json) |

All three current saved STEP crops are valid single solids according to their receipts. The STL files have the tub's **-Y face down**; STEP files retain assembly coordinates. These are geometry/export checks, not slicing or physical tests.

The small crop omits wall ports, the CSI sleeve and much of the edge geometry. The port-service crop retains both port banks, CSI sleeve, front/bottom/top edge regions and support interruptions, but omits the complete rear region. The all-four-mouths crop includes the cold rear, cold underside, hot underside and hot front openings; it opens the inner wall face and excludes the tub body. Its cut access and stiffness differ from the closed housing. No crop is proof of a global worst print span or full-body cleanout.

Keep these three coupons and the nine retained structural coupon pieces separate from production counts. Compact has nine printed assembly rows but ten physical production prints, because the tub body and bonded catch stub print separately. Original storage adds a sleeve, giving ten assembly rows and eleven prints. The centring gauge and [two-piece bonded-catch local study](../../structural-review/bonded-catch-coupon/README.md) are also excluded from production counts.

## Print and inspection gates

Inspect actual first roof layers, one-direction roof paths, beam bridges, pillar bonds, sag, mouth area and support-removal paths in the slicer. All four edge mouths interrupt the frame in different ways. Use the current saved-STEP overhang and bridge reports for their stated geometric screens; neither proves an executable toolpath or real bridge quality. Automatic support trapped inside the complete plenum is unacceptable.

None of the crops has been sliced, printed or tested. Their cut edges permit access absent in the complete enclosure. Even a successful crop cannot establish closed-body debris removal, channel cleanliness, hand/strap/stand occlusion, complete assembly fit, mechanical strength, useful airflow, pressure loss or cooling. Those physical gates remain open. Record stopped or failed tests as well as completed observations.

## Reproduction

From the repository root, after the selected compact-Kowa export and matching plenum report:

```text
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/make_shadow_plenum_coupon.py
```

The exporter requires the matching successful `shadow-plenum-checks.json` and stops for an invalid or disconnected crop. Regenerate the structural calculation after these receipts, then check-scope and the structural PDF. Refresh the table above from the three bound receipts when crop bounds change. Do not reuse a prior PDF or coupon pass for a different saved tub. See [reproduction instructions](../../REPRODUCE.md) and [research applicability](../../corrective-2026-10-12/RESEARCH-INTEGRATION.md).
