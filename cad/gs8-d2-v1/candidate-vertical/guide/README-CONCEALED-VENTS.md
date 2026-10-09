# D2 concealed ventilation assembly and wiring review

This revised guide covers the compact Princeton and Kowa LM6HC vertical candidate with an integral outer shadow-gap plenum. It has a distinct output identity from the original reviewed 29-page guide. The original generator, `out/` PDF, receipt and page images are preserved. The revised guide remains an unqualified review: all 56 inherited physical gates, M1 and the candidate-specific holds stay open.

## Final source nomination

Do not render while geometry, exported files, routing checks or source documents are still being revised. The builder must nominate an exact final `out/compact-kowa_lm6hc/manifest.json` SHA-256. The guide requires this hash explicitly and rejects source, saved-STEP or ventilation-report mismatches. `vent_geometry.py` is the geometry authority; `shadow-plenum-checks.json` must bind the same source, verifier, saved manifest and historical tub comparison. The earlier `ventilation-checks.json` belongs to the archived angled-channel trial and is not selected plenum evidence.

Lightweight input review does not render or invoke CadQuery:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/vent_guide_support.py --manifest-sha256 NOMINATED_HASH
```

After source nomination, use the shared CAD lock for the CPU guide render:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 NOMINATED_HASH
```

The result is `out-concealed-vents/D2-vertical-concealed-vents-review.pdf`, numbered PNG pages and a separate `guide-receipt.json`. The receipt records the nominated mechanical manifest, all guide inputs, PDF/page hashes, saved-STEP ventilation report and limited computed-caption status. The cover dimensions come from the current manifest. Successful generation does not establish completed visual review.

After every page is visually inspected, package the revised guide with:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/package_concealed_guide.py
```

The package is `out-concealed-vents/D2-vertical-concealed-vents-source-and-pages.zip`. The packager verifies source, report, PDF, mesh and image hashes. Publish or save this as a new revised identity; do not replace the original reviewed PDF or original source bundle.

## Added review content

- Section 03v shows representative cold and hot plenum sections: exterior skin, gap, original inner wall and internal slots. Rear/underside perimeter mouths feed the cold bay; front/underside mouths serve the hot bay. Gross mouth and wall-slot areas are reported separately. Section 17v shows the smallest recorded hot-bay horizontal cut and explicitly rejects summed mouth area as a global flow minimum.
- Section 03w records the exported print orientation, layer/bridge review, representative plenum coupon and cleanout/inspection of both bays, four perimeter mouths and eight inner-wall slots. The integral posts are an unsliced roof-support proposal. The front mouth removes frame support across Z5..40: 10.7 mm is not a supported bridge there, and front-edge toolpaths may require about 35 mm bridging. The expanded coupon must screen this under a prominent print HOLD; failure requires local webs and renewed airflow-section checks. No trapped internal supports are acceptable; no support-free printing is claimed.
- Section 17v keeps the separating baffle and passage mouths clear during assembly, retains the straight CSI service bypass and states the actual cooler, hand/strap occlusion and closed-body thermal gates.
- The printed inventory stays at nine parts and purchased parts do not change. The four old panel grooves had 0.2 mm floors and were blind reliefs, not through-vents. The revised panel restores its plain 2.8 mm skin.
- The full camera FPC, EVF feed, complete flexible looms, real cooler geometry, CSI latch/jaws, retention and electrical qualification holds remain unchanged. Saved-STEP ventilation geometry checks do not close them.

## Visual and evidence review

Inspect every page for clipping, text overflow, misplaced arrows, unreadable labels and misleading drawings. The two plenum sections are analytical diagrams derived from the source/report, not saved-STEP cutaway renders. Their arrows indicate intended paths, not measured flow. The exterior has blank broad faces, perimeter mouths and the required CSI service aperture. Direct front and rear views expose mouths; no light, dust or water rating is implied.

Recheck isolation-before-opening on page 00, physical J8 versus BCM pin numbering, J2's normally-open circuit, exact full-material HDMI snapshots, preserved FPC and EVF-feed holds, and the complete supported FPS service sequence. Review all new section, print and thermal pages against `STEP-REVIEW-CONCEALED-VENTS.md`.
