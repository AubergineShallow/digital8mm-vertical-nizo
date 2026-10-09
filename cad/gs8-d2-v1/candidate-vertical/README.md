# D2 vertical Pi concealed vent review candidate

This directory contains the compact Kowa / Princeton vertical-Pi camera candidate derived from [AubergineShallow/digital8mm](https://github.com/AubergineShallow/digital8mm), with upstream baseline commit `d38468e58eb2b02d56743e2e0cfdd8f780818a65` retained for traceability. The current ventilation study uses a plain integral outer skin and separate intake/exhaust shadow plenums. Broadside grilles are concealed; edge mouths remain visible in direct front/rear views. Nine compact printed production parts and the reviewed purchased BOM selections/quantities are retained.

**This is an unqualified review candidate, not a fabrication, energization or service release.** All 56 inherited physical gates and collar M1 remain open. Actual cooler registration, complete FPC/EVF wiring, real tool access, printed strength, plenum manufacture and closed-body thermal performance remain unresolved. Geometric openings and scoped CAD passes do not establish useful airflow or physical safety.

**Print hold:** the front mouth interrupts first-roof support over Z5..40; depending on raster direction this may require about 35 mm bridging. The expanded coupon contains the region, but no slicer or physical bridge/cleanout result exists.

## Start here

- [Design review and open holds](REVIEW.md): geometry, dimensions, alternatives, evidence limits and decisions still needed
- [Assembly and service proposal](ASSEMBLY-VERTICAL.md): dependencies and STOP points, including physical battery isolation
- [Complete BOM](BOM-VERTICAL.md) and [CSV](BOM-VERTICAL.csv): installed versus purchased quantities, included kit contents, spares and qualification notes
- [Received-part measurement plan](MEASUREMENTS-TO-CLOSE.md): the measurements needed to replace proxies and close interface holds
- [Pictorial concealed-vent guide PDF](guide/out-concealed-vents/D2-vertical-concealed-vents-review.pdf), [reproduction instructions](guide/README-CONCEALED-VENTS.md) and [STEP review map](guide/STEP-REVIEW-CONCEALED-VENTS.md): source-bound assembly and wiring review
- [Two-page structural supplement PDF](structural-review/output/pdf/D2-shadow-plenum-structural-supplement.pdf) and [editable text](structural-review/CONCEALED-VENT-STRUCTURAL.md): manifest-bound mass/load sensitivity, retained-section assumptions and print implications; no FEA or physical strength claim
- [Retained structural coupons](structural-review/coupons/README.md): nine separate test pieces, with the unchanged [generator](structural-review/make_coupons.py), selected/optional STEP inputs and a [verified restoration receipt](structural-review/coupon-reproducer-recovery.json)
- [Two plenum inspection coupons](vent-study/shadow-plenum-coupon/README.md): generated regular-grid and expanded port/CSI/edge crops, with a [source-bound index](vent-study/shadow-plenum-coupon/coupon-index.json). They remain separate from production parts and earlier structural coupons and do not prove closed-body cleanout or every unsupported span. No slicing, print or test is claimed.

## Evidence and preserved history

The current compact-Kowa [manifest](out/compact-kowa_lm6hc/manifest.json) identifies source files, STEP/mesh exports, estimated mass and print poses. Only reports whose manifest and verifier/source hashes match that export are current. The [documentation audit](out/review-docs-audit.json) distinguishes stale reports and checks BOM preservation. A report can contain known failures; binding a report does not convert them into passes.

[Reviewed export18](history/reviewed-export18/README.md) is the frozen reference before concealed-vent changes. Its raw 288 pass / 2 fail / 18 info result and prior service evidence remain historical. The new main checker distinguishes the intentionally empty CSI aperture from adjacent wall measurements; the actual cooler/source conflict remains an open hold.

The [visible angled-channel trial](vent-study/angled-channel-trial/manifest.json) is preserved as a rejected visual alternative. Its slot mouths remained visible, so its 59 mm core and throat/check results must not be used as the shadow-plenum result. Fresh [three-variant STEP comparisons](out/comparison/assembled-comparison.json) and core-void reports bind the current Kowa, Fujinon and original-storage exports. Compact Kowa/Fujinon bounding volumes are about 6.8% below matching baseline; original-storage Kowa is about 3.3% larger. Alternative exports and meshes have current identity checks, but compact-Kowa service results do not transfer.

## Reproduce a review snapshot

Use the repository's pinned CadQuery environment from [the dependency lock](../../gs8-pxl-v3/cad-requirements-lock.txt) and the [CAD execution wrapper](../run_locked.py). Read the scripts' arguments before running them, and keep all geometry sources fixed during export/checking.

1. Export the chosen compact Kowa source with [export_candidate.py](export_candidate.py). Geometry is defined by [model.py](model.py), [vent_geometry.py](vent_geometry.py) and their recorded dependencies.
2. Run [verify_shadow_plenum.py](verify_shadow_plenum.py), then the serial [shadow review checks](run_shadow_checks.py). Preserve failures and inspect the report scope; do not inherit a historical pass count.
3. Refresh [the BOM generator](make_bom_vertical.py), [the CAD-free structural sensitivity](structural-review/update_concealed_vent_structure.py), and [the document/BOM audit](review_docs_audit.py). The structural calculation accepts only tub/panel changes relative to its frozen reference; a changed carried or lower component needs a new free-body calculation.
4. Rebuild [the structural PDF](structural-review/build_shadow_structural_pdf.py) from its bound JSON and text. For the pictorial guide, run [build_guide_concealed_vents.py](guide/build_guide_concealed_vents.py) under the CAD wrapper with `--manifest-sha256 53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77`. Inspect every rendered page, then use [package_concealed_guide.py](guide/package_concealed_guide.py) to verify the guide package. A source change requires renewed bindings and renders.

The guide and reports are review artifacts. Slicing, representative plenum/coupon tests, actual part measurements and powered qualification are separate work that has not been completed by these scripts.
