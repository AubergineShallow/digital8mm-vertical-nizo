# Reproduce the concealed-vent review

This is a frozen shadow-plenum review candidate, not a fabrication, energization or complete-service release. Read [REVIEW.md](REVIEW.md) and the [assembly STOPs](ASSEMBLY-VERTICAL.md) first. The supplied compact-Kowa manifest is `53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77`; [current-review-evidence.json](out/compact-kowa_lm6hc/current-review-evidence.json) identifies the selected scoped reports. Upstream baseline commit `d38468e58eb2b02d56743e2e0cfdd8f780818a65` and [reviewed export18](history/reviewed-export18/README.md) remain preserved.

Work from the repository root. Use the pinned Python 3.12.14 / CadQuery 2.6.1 environment. `python3 tools/bootstrap_cad.py` recreates `.venv-cad` from the pinned dependency lock. Do not substitute an arbitrary CadQuery version. Run CAD and render jobs serially through `run_locked.py`; do not nest the lock wrapper inside the batch runners.

## Inspect the supplied snapshot

These commands do not rebuild geometry. The BOM and structural `--check` options verify their generated outputs; the documentation audit writes a fresh identity report. They do not establish physical qualification.

```sh
python3 cad/gs8-d2-v1/candidate-vertical/make_bom_vertical.py --check
python3 cad/gs8-d2-v1/candidate-vertical/structural-review/update_concealed_vent_structure.py --check
python3 cad/gs8-d2-v1/candidate-vertical/review_docs_audit.py
```

## Rebuild geometry and scoped evidence

Use a separate checkout or copy to retain the supplied review snapshot. Exporting rewrites outputs and timestamped receipts, so a new run will have a new manifest hash even with unchanged geometry. Rerun and rebind every dependent report; do not paste the supplied `53e668d4` identity onto regenerated files.

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/make_corrected_pi.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/export_candidate.py --storage compact --lens kowa_lm6hc
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/verify_shadow_plenum.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/verify_shadow_outlet_context.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/run_shadow_checks.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/export_shadow_alternatives.py
python3 cad/gs8-d2-v1/candidate-vertical/reconcile_review_evidence.py
```

`make_corrected_pi.py` creates the source-bound, overlapping named-component Pi assembly. Its raw solid-volume sum is not occupied union material. `export_candidate.py` then writes individual and assembly STEP, print-oriented STL, regenerable mesh JSON, and source/file-bound manifests. Mesh checks establish limited geometric properties, not slicing or strength.

The plenum and finite exterior-mouth checks are separate from `run_shadow_checks.py`. That batch runs mesh, CSI cylinder, rigid and static power, full-material HDMI, supported FPS, current whole-tub USB-head, rigid assembly, rejected closed-panel microSD, and compact core-void checks. It preserves per-check exit codes in `review-check-run.json`; the batch completing is not an aggregate pass. The main audit retains the unresolved cooler/source-Pi conflict as a failure. The new USB checker requires the complete tub and canonical support-source hashes; the earlier missing-extract attempt remains historical.

`export_shadow_alternatives.py` exports compact Fujinon and original-storage Kowa, checks their print meshes, calculates their core-void intervals, then computes fresh untessellated STEP bounds for all three variants. It does not rerun alternative service/harness audits. The compact-Kowa service results must not be transferred to alternatives. Bounding boxes are reported to 0.1 mm, not as measured camera volume. Empty-model core intervals include useful plenum/cooling, cable and service space and the Pi proxy-representation caveat; they are not removable waste.

`reconcile_review_evidence.py` checks already-written report, source and manifest identities and preserves the one active rigid failure. It does not execute CAD. It rejects a changed evidence set rather than certifying a new design automatically. Inspect failures and every report's scope before updating the top-level checkpoint or documentation.

For a new export, refresh the BOM and structural supplement without `--check`, then run their checks and the document audit. The structural script accepts only tub/panel row changes relative to the retained reference. Any other geometry, mass or carried-part change requires a fresh engineering calculation. Regenerating its PDF requires renewed visual review and receipt validation.

## Renders, coupons and pictorial guide

[run_shadow_renders.py](run_shadow_renders.py) invokes Blender on the saved meshes for hero, rear, cooler-side and front ventilation views. It does not rebuild CAD or demonstrate hand occlusion, thermal performance or complete flexible service.

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/run_shadow_renders.py
```

The two plenum coupon crops and their reproduction instructions are in [vent-study/shadow-plenum-coupon](vent-study/shadow-plenum-coupon/README.md). The nine retained structural coupon pieces have a separately restored, hash-verified [reproducer](structural-review/coupons/README.md#reproduce-retained-coupon-geometry). Neither set is part of the nine compact production parts. No slicing, printing, mechanical testing or closed-body cleanout has been demonstrated. The front mouth removes frame support over Z5..40; the nominal 10.7 mm distance is not a two-ended supported bridge, and raster paths may require about 35 mm bridging.

Use [the concealed-vent guide instructions](guide/README-CONCEALED-VENTS.md) and `build_guide_concealed_vents.py`. The original `build_guide_vertical.py`, 29-page guide, `refresh_primary_evidence.py`, `refresh_alternatives.py` and `render_views.py` are preserved earlier workflows, not the selected shadow-plenum reproduction sequence.

For the supplied unchanged snapshot only:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/package_concealed_guide.py
```

After a rebuild, nominate the exact new manifest SHA-256 instead, freeze all guide inputs, and visually inspect every rendered page before packaging. The guide receipt guards sources, reports, PDF and page images; it is not a physical release. The new structural PDF and source remain separate from the unchanged historical structural report.

Files named `probe*` and rejected routing/ventilation studies are development history. Some require recorded temporary inputs. Their presence does not make them selected evidence. All 56 inherited physical gates, M1, actual cooler registration, complete FPC/EVF feed, whole flexible service, bridge/cleanout and thermal/occlusion holds remain open. Install the OS microSD on the bench before carrier insertion, or use the documented panel-off service; closed-panel withdrawal remains rejected.
