# Vertical assembly and wiring review guide

This is the separate compact-Princeton / Kowa LM6HC vertical candidate. It does not reuse the horizontal candidate's drawings or declare a fabrication release. All 56 inherited physical gates and M1 remain open.

## Rebuild

From repository root:

```
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/guide/build_guide_vertical.py
```

The generator reads candidate exported meshes, the current routing study, assembly/BOM documents, inherited electrical and assembly rules, and verification reports. It outputs numbered PNG pages (count recorded in the receipt), an A4-landscape PDF and a source-hash receipt in `out/`. The source mesh export and route study must be frozen together before the guide is treated as the current review snapshot. The receipt also records page-image hashes and the source-matched status controlling each limited computed-pass caption.

After visual review, run `package_guide.py` with the same Python environment. It checks source, PDF, image and mesh hashes before creating `D2-vertical-guide-source-and-pages.zip`, which contains the editable renderer, its frozen inputs and pinned guide dependencies.

`software_lineart.py` preserves the existing guide's image-space line-art treatment while replacing its display-server-dependent VTK renderer with a CPU triangle Z-buffer. `raster.cpp` builds locally with g++. `raster.so` is a reproducible cache, not a source dependency. Actual tessellated CAD meshes are used; arrows are explanatory proposals, never continuous swept-volume proofs.

## Required review

- Render every page; inspect for clipping, text overflow and misleading diagrams.
- Page 00 must show a closed camera while the pack is withdrawn. An open-body illustration here would contradict isolation-before-opening.
- Read J2 as the two official Pi power-button pads, not GPIO or a battery-current switch.
- Keep physical J8 pin numbering separate from BCM GPIO numbers.
- Never turn a centerline or empty slack reservation into a full cable fit claim.
- Use full-width ribbon geometry, correct adapter orientation, actual rigid heads and physically conserved length in both installed and pre-mating poses.
- Show any missing carried-motion, tool-access, retention or connector-contact-face evidence as an open STOP.
- Freeze the latest exported CAD, route study and verification evidence together; regenerate after source changes.
- Source only approval is not a physical gate closure.

## Guide-driven findings sent to the builder

1. Bare-carrier motion excludes pre-mated HDMI heads and the ribbon. It cannot authorize the intended pre-mated insertion.
2. The original 178.845 mm route + 20 mm allowance consumed 198.845 mm of a 200 mm ribbon, but the allowance was not modeled as deployable material. That 200 mm checkpoint models the whole strip but remains fragile for both-heads-free service. The preferred provisional compact route now uses an intact 300 mm Adafruit 3562 ribbon, with selected installed / EVF-unplugged full-material snapshots. Pi remains mated; both-unplugged service is rejected because of the power-wire conflict. Exact current-source tests and physical qualification remain required.
3. EVF head must mate upward after the driver seats. Its final position alone does not establish connector insertion, fingers or plier access. Recording storage must remain absent until this action is qualified.
4. Fixed pigtail ties cannot be treated as freely unfolding slack. Battery must be physically disconnected with the body closed. If that cannot be done, service sequence must stop and geometry/retention must change.
5. Wall-facing GPIO housings cannot simply be unplugged in situ. The revised service proposal detaches panel-side QT/J2 and EVF-end HDMI/5V, then stages the carrier with headers, supported FPS switch and its entire mated harness carried. Run-lead reach, FPC latch access and pigtail/fuse passage must be proved. Camera-end FPC must be free before camera motion.

6. Real Lorlin CK1044 geometry replaced the inherited inconsistent switch proxy. FPS knob/nut/mounting washer come off while preserving the separate stop washer; support the shaft axially for the first panel movement, then the bushing. Carry the complete switch and still-mated genuine PicoBlade harness with the Pi/HDMI group.
7. Official Pi geometry supersedes the wrongly oriented CSI proxy and exposes the corrected lower USB head/boss clash. Only manifest-matched selected checks can enable limited pass captions. CSI operation remains HOLD even when cylindrical tool reserves clear.
