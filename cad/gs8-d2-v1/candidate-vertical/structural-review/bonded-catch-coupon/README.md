# Bonded catch local joint study

This is a separate two-piece study of local seating, datum tilt, adhesion and warm creep. It is not released for printing, bonding or load testing. It cannot qualify whole-tub or whole-camera strength, including the separate 0.5 N·m full-body design-torque case.

The [generator](../make_bonded_catch_coupon.py) crops a host from the selected saved tub's reconstructed production print stock and copies the exact production `tab_catch_insert` STEP and STL. The host crop is X−20..0, full tub Y extent, Z76..100 mm. It retains the pocket, ceiling/pad, both catch faces, roof connection and original bed-side skin. It adds no clamp block, support, reinforcement or alternative joint. An invalid or disconnected crop stops generation.

The resulting `receipt.json` records the selected manifest, input/source hashes, exact joint dimensions, crop bounds, geometry/mesh checks and exported file hashes. It separately identifies the host and exact production insert copy. Read the receipt's actual print dimensions and joint fields; dimensions from earlier catch trials do not apply. Production files and their counts are unchanged. These two test pieces are additional to the nine retained structural pieces and three plenum crops; the centring gauge is also separate.

[Four review views](coupon-review.png) show the nominal source assembly, its opposite view, an illustrative exploded placement and the distinct production print orientations. [The render receipt](review-render-receipt.json) binds those views to the geometry files.

## Orientations and assembly frame

The host STL preserves the tub's -Y-down production layer direction. The insert STL is an exact copy of its -Z-down production export. The host is translated only to put its cropped bounding box on the bed. Keeping these layer directions does not prove coupon bed adhesion, support removal or slicer quality.

STEP files retain the source assembly coordinates. The two bed-oriented STL files have different translations and rotations and must not be treated as already assembled. Use the receipt's host transform and the recorded production insert pose to return them to their source positions. The nominal assembled host/insert material-overlap check is geometric only; clearance and actual seating still require measurement.

## Physical evidence still needed

Freeze the actual filament grade/lot, conditioning, printer, 0.20 mm baseline layer process, walls and local fill. Freeze the epoxy SKU, preparation, mixing, bondline, cure and environmental conditions. Follow the selected adhesive maker's instructions; no generic epoxy or surface-preparation method is qualified here.

Measure the printed pocket, tenon, ceiling and both catch-face positions. Record the datum seating and the geometric window over the current specified tilt/BFAR cases. The inherited 0.129 mm offset allowance is not retained. Read the current main audit's manifest-bound `roll_catch` window/contact rows for the modeled limits.

For an inert local fixture, document where it reacts against the crop, the applied force and lever arm, loaded deflection, permanent movement and any failure mode. Keep fixture contact away from the pocket, bond and measured faces. Set the test method, stop conditions, fixture capacity and conditioning before loading. A clamp can change the crop's stiffness; a local result cannot be transferred to the complete tub.

Relevant warm-dwell and creep tests remain necessary after choosing the actual adhesive and intended service conditions. No slicing, print, bond, mechanical, fatigue, impact or thermal test has been performed. All applicable physical gates remain open. See [the measurement gates](../../MEASUREMENTS-TO-CLOSE.md) and [research applicability](../../corrective-2026-10-12/RESEARCH-INTEGRATION.md).

## Reproduction

From the repository root, after the selected production export has finished:

```text
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/structural-review/make_bonded_catch_coupon.py
```

The generator checks every selected manifest source and the bound tub/insert STEP/STL inputs. It reconstructs tub print stock through the same existing helper and 0.5% tessellation-volume rule used by the print checker. Saved host STEP reimport must remain valid and connected; both STLs receive the existing mesh topology, positive-volume, bed-position and size checks. The exact insert files must remain byte-identical to production. These checks do not replace slicer review or physical qualification.
