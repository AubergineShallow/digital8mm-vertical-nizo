# Concealed vent structural supplement

This supplement updates mass and quasi-static load sensitivity for the selected shadow-plenum compact Kowa candidate. It uses the retained export18 section models and the current manifest. It is not FEA, a drop rating, a physical strength result, or permission to print/energize. All 56 inherited physical gates and M1 remain open.

**PRINT HOLD:** all four plenum edge mouths (rear Z5..75, cold underside, hot underside, front Z5..40) and the trial3 roof (1.2 mm beams on pillars, at most 14 mm beam bridges, roof spans computed by print_bridge_direction) need slicer, bridge and cleanout evidence from the three plenum coupons (the third covers all four mouths); none exists yet.

## Exact scope

Current manifest: `dbea5ca508bf172a6ad0f34e5517ceeaed162c9cd3cf3431a0193de79ace0810`, built unrecorded (deterministic build, FP-03). Frozen export18 reference: `c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76`. The reproducible calculation is `update_concealed_vent_structure.py`; exact inputs and unrounded results are in `concealed-vent-structural.json` and the copied reference `reference-export18-structural-binding.json`.

Only the s_c4, base_grip, eyecup, carrier, tub, panel, lens_collar manifest rows change; all 38 other rows are identical. This checks metadata, not occupied-solid equivalence. The retained carrier, grip and J4 sections are conditional inputs to the calculation and must stay tied to the independent source/STEP preservation checks. The former whole-tub and whole-panel zero-difference bindings are historical and do not apply to this revision. The new integral skin, cold/hot plenums, divider, support posts, CSI sleeve and panel surface are outside those old whole-part claims.

## Mass and applied loads

| Quantity | Reviewed export18 | Concealed candidate |
|---|---:|---:|
| Estimated complete Kowa mass | 831.38 g | 870.42 g |
| Tub proxy mass | 122.58 g | 155.88 g |
| Panel proxy mass | 37.41 g | 38.19 g |
| Upper-body free-body mass | 640.43 g | 679.28 g |
| Upper-body 5g floor moment | 1.7201 N·m | 1.8147 N·m |
| Conservative grip 5g moment | 4.4751 N·m | 4.6728 N·m |

The net modeled mass increase is 39.04 g (4.70%). Current complete CoM is (-46.46, 1.02, 29.96) mm. Core is 158.0 × 63.6 × 100.0 mm. Manifest mesh-derived complete bounds are 248.83 × 72.82 × 216.82 mm; these are not fresh untessellated STEP measurements or a measured camera envelope.

Tub/panel mass uses the inherited ASA density 1.07 g/cm³ and empirical 0.85 mass factor. These are not slicer measurements or stiffness multipliers. The legacy 12 g connector/fuse/pigtail lump has an unresolved real distribution; other harness masses remain omitted. Weigh the printed parts, loaded body and actual harness before setting final qualification loads.

A J4 lower row changed (base_grip), so the export18 transfer is not used: the upper free body is the complete manifest (mass × CoM) minus the eight J4 lower rows, each row mass × the centre of mass of its manifest-bound STEP (check_scope.j4_direct; on the phase-1 export, whose lower rows equal those of export18, this reproduces the export18 transfer, tests/test_fx_fixup.py). The 5g floor moment uses upper mass only, avoiding false credit from the low battery as a counterbalance across J4. Grip screening conservatively places the whole new assembly mass at upper-body Z54.48 with hand reaction Z−55. The 1g/3g/5g cases are quasi-static handling sensitivities, not drop or life ratings.

## Retained sections under changed load

With the same equal tongue sharing and local strip assumptions, J4 nominal lip/head stresses become 8.98/9.92 MPa, a 5.50% increase. The 30–70% station-sharing sensitivity multiplies these by 0.6–1.4. Joint contact, local notches, anisotropy, wear and creep are not solved. Grip gross nominal stresses become 1.59/1.69 MPa, a 4.42% increase; tub/floor compliance and joint slip remain excluded.

FP-11c thickened the carrier frame to its continuous 22.2 bed face and opened its counterbores, so the carrier payload rises by 4.67 g to 127.27 g. The reinforced arm section is unchanged, so its retained 5g, half-reaction screen scales with payload to 3.52 MPa and 0.414 mm (export18: 3.39 MPa, 0.399 mm) at assumed E=1600 MPa. This does not qualify the arm, boss roots, screws or service pulls. Lens/collar mass, preload cautions, FPS-rest load cases and 100 N strap comparison inputs are unchanged; thermal and physical tests remain necessary.

The old 0.90 N·m per-front-joint coupon target does not cover the new equal-share floor moment plus the retained 12 g-at-Z100 wiring-location sensitivity. The calculated minimum is 0.9368 N·m; use 0.95 N·m as the rounded proposed equal-share screening target after fixture review. A 70% station reaction with that same wiring sensitivity would be 1.3115 N·m and is a separate unqualified case. Existing C08/C09 geometry can screen the retained local mating surfaces; it omits the rear joint, independent lock and full tub. Do not turn a local coupon result into a whole-camera rating.

Variant coverage (FP-12, VN-33; FX). The same first-moment transfer applies to every exported variant whose lower grip/battery rows are unchanged, and a variant whose lower rows changed gets the new free body from its bound STEPs (check_scope.j4_direct); 3 of 3 qualify. Equal-share plus wiring targets: compact-fujinon_hf6xa 0.7699 N·m (70% share 1.0779 N·m); compact-kowa_lm6hc 0.9368 N·m (70% share 1.3115 N·m); original-kowa_lm6hc 0.9822 N·m (70% share 1.3750 N·m). The 0.95 N·m compact value covers compact-fujinon_hf6xa, compact-kowa_lm6hc and does not cover original-kowa_lm6hc. Use 1.00 N·m (governed by original-kowa_lm6hc) as the rounded equal-share screen that covers every variant. The 70% cases remain separate unqualified cases.

## Print material and thermal implications

Retain the current broad-face starting poses and 0.20 mm layer baseline: tub −Y face down, panel/carrier +Y face down, grip +Z top down and collar +X front down. The selected 1.6 mm skin and windowed ribs, 6 mm plenum gap, divider and CSI sleeve change toolpath transitions, warping and local cooling; they do not establish greater shell stiffness or printability. The retained 2.5 mm inner wall forms a roof over the plenum in this print pose. Its spans around post exclusions and ports require section coupons, contiguous toolpaths, bridge/sag inspection and verified cleanout. Concealment of broadside grilles does not establish a self-supporting roof.

The plain panel restores material where four blind grooves previously retained only 0.2 mm floors. This removes those local thin floors but does not prove panel flatness, screw-seat strength or clamp performance. The CSI access slot remains straight and unsealed, so its bypass must remain in the airflow and thermal interpretation. Actual cooler profile, fan operating point, separate normal-hand/strap/stand occlusion cases and closed-body battery temperature remain open. Blocking the hot underside mouth leaves only the 210 mm² front mouth against 510 mm² wall ports, before internal losses; no minimum useful airflow or rated blocked-vent operation is established.

Use the earlier independent E=0.8/1.6/2.4 GPa sensitivity (deflection multipliers 2/1/0.667) and 5/10/20/30 MPa normal-strength scenarios only to expose dependence, never as material allowables. Print direction, dense local sections, conditioning, layer bonds and warm creep need measured evidence. No infill factor, catalogue tensile result or heat-deflection temperature establishes a safe service temperature or factor of safety.

The nine original structural coupon pieces stay separate from nine production camera parts. A preliminary regular-grid open-edge plenum coupon STEP/STL is generated separately, with its source receipt in `../vent-study/shadow-plenum-coupon/receipt.json`; it is not print-released, sliced or tested. Open cut edges allow access absent in the closed plenum, and that crop omits ports, the CSI sleeve and some post exclusions. The second generated crop spans X−110..0 / Z0..100, nominal 110 × 100 × 10.1 mm, covering both port banks, the CSI sleeve, edge spans and the lower support row. Its receipt and the two-coupon index are in the same directory. It omits the complete rear region and does not prove a maximum global roof span. Both crops are valid saved-STEP single solids and have STEP/STL exports, but neither has been sliced, printed or tested. The two plenum coupons remain separate from the prior nine structural pieces. Record every stopped/failed test. Purchased BOM selections and quantities remain unchanged.
