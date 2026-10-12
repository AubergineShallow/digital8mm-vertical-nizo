# D2 2026-10-12 corrective assembly and wiring: blocked review

This guide covers the compact Princeton and Kowa LM6HC vertical candidate. It is an unqualified review, not a fabrication, energization or complete-service release. All inherited physical gates, M1 and the candidate holds remain open. The original reviewed 29-page guide and its source bundle remain separate historical artifacts.

Use a PDF only when its `guide-receipt.json` binds the current assembly, guide sources, nominated mechanical manifest and scoped reports. A receipt from an earlier source state is stale even when its PDF opens normally.

## Final source nomination

Freeze geometry, exported files, routing checks and source documents before rendering. The builder requires the exact lowercase SHA-256 of `out/compact-kowa_lm6hc/manifest.json`. Its preflight rejects changed source/STEP bindings and requires current main, plenum, outlet-context, print, path-aware flow, harness and structural evidence plus the three-coupon index. Report failures are retained; current evidence does not mean a passing or qualified camera.

```sh
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/vent_guide_support.py --manifest-sha256 NOMINATED_HASH
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 NOMINATED_HASH
```

Windows without 64-bit g++ uses `guide/run_with_numpy_raster.py -- --manifest-sha256 NOMINATED_HASH` through the same lock. The selected result is `out-concealed-vents/D2-vertical-concealed-vents-review.pdf`, numbered PNG pages and `guide-receipt.json`. The receipt binds sources, reports, PDF, images, meshes and the two separately illustrated tub print STLs. Successful generation does not establish visual review.

Inspect every rendered page for clipping, overlap, wrong arrows, unreadable labels and misleading assembly claims. Then run the separate build-order check and package:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/record_post_guide_check.py
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/package_concealed_guide.py
```

The [separate post-guide receipt](out-concealed-vents/post-guide-build-order-check.json) and [raw log](out-concealed-vents/post-guide-build-order-check.log) bind the actual 23-test rerun to this manifest, final guide receipt and tested sources/documents. They supplement the original primary-batch stale-banner failure, which stays preserved. Re-running this repository test requires its historical Git fixture; the guide-only archive does not include Git history.

The packager verifies all receipt-bound inputs and writes `D2-vertical-concealed-vents-source-and-pages.zip`. The PDF and editable source bundle are the two review deliverables. Preserve their confirmed Library identities when updating an existing delivered version.

## Corrective content

- Inventory: 10 compact physical printed pieces represented by 9 CAD assembly rows. The tub body and bonded catch stub are distinct prints. Original storage adds a sleeve, giving 11 pieces / 10 rows. Gauge and three plenum coupons are separate qualification aids.
- Sections 03v–03x: current windowed beams, pillars, cold-mouth lintels and stepped front-mouth support replace the historical post grid. Net mouth necks are separated from gross openings and path-aware minimum cuts. The bonded stub is shown in its own exported print pose. Actual slice quality, bond/creep, support removal and full-body cleanout remain HOLD.
- Sections 04, 08b, 11 and 13: the official camera instructions recommend seating the Pi CSI end before the cooler. The camera end is mated while both assemblies are supported immediately before camera insertion. The complete 200 mm linked ribbon is absent from the rigid camera/carrier sweeps. Actual latch service with the cooler retained and complete flexible motion remain HOLD.
- Section 05: J2 uses the conditional Micro-Fit 3.0 class from the BOM, with exact SKU, roots, latch and stow unqualified. The obsolete FPS-identical PicoBlade proposal is not drawn as the J2 selection.
- Section 15q: the complete nominal QT stored length is distinct from the shorter free curve plus 24 mm reach allowance. Existing round bundle/branch envelopes do not prove actual four-core packing, splice geometry or a continuous flexible transition.
- Sections 06g and 15: the 270 mm pigtail remains blocked by reach and hot-drop. The high-case drop is quoted from the bound report; no substitute wire, fuse, connector or cutoff is adopted.
- Section 17v: source-bound path-aware area checks do not establish airflow, fan operating point, recirculation, hand/strap occlusion or closed-body cooling.

The separate [bonded-catch local study](../structural-review/bonded-catch-coupon/README.md) has two test pieces, retained outside production counts. Its [bound receipt](../structural-review/bonded-catch-coupon/receipt.json) and exact files are included in the source bundle. It screens local seating, tilt, adhesion and creep; it does not qualify the whole-tub 0.5 N m case.

The 300 mm HDMI ribbon, official 200 mm camera FPC and native OLED flex retain unknown manufacturer bend-radius and flex-cycle limits. Connector cycle ratings are not ribbon durability evidence. The analytical plenum sections omit support detail and show intended flow only. No dust, water, all-angle concealment or thermal rating is implied.
