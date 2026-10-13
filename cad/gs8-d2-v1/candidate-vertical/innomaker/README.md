# Innomaker D2 header-aware review fork

**HOLD: SOURCE REVISION AND REAR-HEADER CLEARANCE. This is an unqualified engineering candidate, not a fabrication, fit, assembly, energization or service release.**

This isolated fork targets the colour **Innomaker CAM-IMX296Color-GS / CAM-MIPI296Color**, Amazon ASIN **B0CQ4DTQZ2**, in the compact Kowa LM6HC / Princeton-storage D2 layout. The official Raspberry Pi 5 Active Cooler remains selected. No exterior growth or additional purchased parts are adopted.

## 2026-10-13 fix pass (read first)

- **Branch layout.** `model.py` and `export_candidate.py` are byte-identical to the official commit, so the official Raspberry Pi GS camera build and its manifests are unchanged on this branch. `innomaker_model.py` applies the Innomaker delta to the text of `model.py` at import time (it fails closed if the official file changes in a patched region); only `export_innomaker.py` uses it. The patched text is byte-identical to the delivered fork's `model.py`, so the geometry is the delivered geometry.
- **Third-party files are not committed.** The manufacturer STEP and the manufacturer README state no licence; the Raspberry Pi driver copy is GPL-2.0 without the licence text. They are removed and listed in `.gitignore`. Download them into `innomaker/fetch/` (see [Fetch prerequisites](#fetch-prerequisites)); the tools check SHA-256 and stop with a fetch message when a file is missing. Exports that contain the manufacturer camera geometry (`assembly.step`, `step/gs_camera.step`, `step/innomaker-as-supplied-reference.step`) are regenerated locally and never published; the manifest still records their hashes.
- **Checks no longer write into the export.** Reports and header-study STEPs are in `checks/compact-kowa_lm6hc/`. Rows that cannot fail are INFO, not PASS. New gating rows FAIL today: camera/lens thread-proxy interference (24.164166 mm3), J7 float centring stack to the panel, C-flange to sensor plane, image orientation, lens-torque reaction before PCB contact, board outline against the product page. See [the fix record](review-2026-10-13/FIX-PASS-2026-10-13.md).
- **This variant is not buildable as modelled.** The open items above need measurements of the received camera and user decisions (lens-hold design, clocking, converter purchase).

## What prevents a real fit claim

The manufacturer documentation names **two 2-pin trigger/strobe headers opposite the CSI connector** (XTR/GND and TOUT1/TOUT2), and a photograph supplied with the delivery (not committed) shows them. The public manufacturer STEP does not model them. Actual header location, housings, pin projection and dimensional tolerance are unmeasured. Pins are neither removed nor bent in this proposal. A pin-free camera model cannot qualify the photographed camera.

The 3, 6, 9, 12, 15 and 18 mm rear-projection cases are **sensitivity assumptions only**. Each uses a full-board rear prism, whose XY coverage is conservative only if the real headers remain inside the PCB outline. None is an adopted pin height, a manufacturer bound, or evidence that the actual camera fits. Any case result must remain attached to its exact assumed dimensions and obstacles.

Ordinary free-running CSI operation does not require trigger/strobe wires in the manufacturer's Pi quick start. Leaving the headers electrically unused does not remove their physical clearance requirement. See [source and software evidence](SOURCE-AND-SOFTWARE.md).

## Recovery and evidence boundary

- Restored baseline: `a0bfed9f7ed88dad78ad1a5fcb6fc7504712b338`, tree `21fa959bd62c3b62735fbada30db929e068c1243`, recovered from the preserved Library full-history bundle after the cloud workspace was replaced.
- Header-aware source checkpoint: `c6a040f9654faa9bdb761b1ae7b70cc14a9e3453`, saved as work in progress.
- The earlier local `5736870` checkout and exports were lost before delivery. Its previous pass counts are not current evidence.
- Official-camera files and images outside this directory remain historical/unqualified for this fork. Their earlier passes do not transfer to Innomaker hardware.
- Fresh export location: `out/compact-kowa_lm6hc/manifest.json`. Only source-bound files and scoped reports accompanying that manifest may describe the new reconstruction. They still cannot qualify the missing headers or physical hardware.

## What the geometry assumes

The manufacturer STEP has a 39 × 39 × 1.6 mm PCB (the product page says 38 × 38 mm; the outline is an open measurement), R3.5 corners and four Ø2 mm corner holes on a 34 × 34 mm pitch. The PCB material is reconstructed from the source, including four additional holder/secondary holes. The manual's R2 corner description conflicts with the STEP; this reconstruction follows R3.5. The upper closed-disk solid at index 4 is omitted only under an **unverified protective-cap interpretation**.

The holder mouth at native Z = 13.2 mm is an **unverified CS reference**. A nominal 5 mm C/CS register difference places that reference at global X = −4.4 mm while preserving the original C-lens flange at X = +0.6 mm. This is a conditional placement convention, not measured sensor/filter position, optical back focus, real converter seating, thread engagement or camera clocking. The converter's OD 30.75 / ID 25.5 mm annulus is an unmeasured reservation. Camera mass is a 15 g placeholder.

The proposed load path is camera/holder → C-CS converter (not in the manufacturer packing list; confirm on receipt or buy one) → lens → retained collar → tub seats. Passive PCB-edge safety guides have nominal 0.5 mm clearances. They receive **no normal weight-support, preload, lens-thread torque or verified anti-rotation credit**. The old BFAR catches and bonded stub are absent. Safe direct holder support during lens assembly remains HOLD because the holder material and safe grip surface are unconfirmed.

## Regenerated primary deliverables

Under `out/compact-kowa_lm6hc/`:

- `assembly.step`: assembled conditional fork; the real rear headers are absent from this source model. Local only (contains the manufacturer camera geometry).
- `step/`: separate assembled-position parts. `gs_camera.step` and the as-supplied camera reference are local only for the same reason.
- `stl/`: nine production print-position meshes plus the centring gauge. No print release is implied.
- `renders/hero.png` and `renders/optics.png` (with their receipts) are removed from the published tree on 2026-10-13: they were stale (bound to the delivered manifest `e0a5b3b6...`) and were rendered from the manufacturer camera geometry, which has no stated redistribution licence. Re-render locally after fetching the vendor STEP. The packager now excludes `meshes/` and `renders/` as well.

Under `checks/compact-kowa_lm6hc/`: `innomaker-checks.json` (69 rows: 59 PASS, 6 FAIL, 4 INFO), `innomaker-stl-checks.json`, `innomaker-interpretation.json`, the official `official-print-checks.json` and `official-check-scope.json` run on this export, and `header-sensitivity/` (assumption-only prisms, short file names; the assumption label is in the report rows). No PASS closes a hardware hold.

Other lens/storage variants have not been regenerated or qualified for this fork and remain pending. Read the [delivery self-review](DELIVERY-SELF-REVIEW.md) (written by the delivering agent, not independent) and the validation interpretation addendum alongside the numerical reports.

## Review files

- [Assembly and print plan](ASSEMBLY-AND-PRINT.md): conditional insertion sequence, official cooler order, service and release gates.
- [Source and software note](SOURCE-AND-SOFTWARE.md): source identities, documentation limits and unchanged 48/54 fps RAW/DNG acceptance.
- `BOM-INNOMAKER.csv`: separate compact-fork BOM derived from `../BOM-VERTICAL.csv`; inherited status and notes are explicitly historical/unqualified.
- `PRINT-INVENTORY.csv`: nine production prints derived from the fresh manifest, with saved STL hashes and print poses. The centring gauge and coupons are excluded.
- `records.json`: hashes binding the BOM and print inventory to their inputs. The presence of a file alone does not prove it is current; run the records check below.

The production tub is one piece. `I-tub-stub` and its dedicated `V-68` epoxy are removed; no substitute adhesive or additional purchased support is introduced. Unrelated adhesive, heat-shrink, tape and RTV provisions are retained. Only the obsolete official-camera PCB tripod-block detail `I-05B` is removed; it already had zero installed and purchase quantities. **The functional D2 grip tripod socket is retained**, including `D2-31`, one installed 1/4-20 UNC steel nut, and its existing base-grip pocket. D2-20 retains the existing 200 mm Standard-Mini camera cable provision until the Innomaker kit's included cable is verified for equivalence.

## Fetch prerequisites

Not committed (no stated redistribution licence, or licence text not shipped). Put each file in `innomaker/fetch/` (git-ignored):

| File | Source | SHA-256 |
|---|---|---|
| `IMX296 With CS.stp` | extract from https://www.inno-maker.com/wp-content/uploads/2021/06/IMX296-With-CS.zip | `3d53cc2b16f4c4bd91776e57548dcf191689a6d4f7ee4962411cfb3f1b496b51` |
| `manufacturer-README-46d6d217.md` | https://raw.githubusercontent.com/INNO-MAKER/cam-imx296raw-trigger/46d6d217f0d754921503ef64a3d801aa935563d6/README.md | `48c939936fc59d5865c9445b29baef24b2d91ad1796538429e7f77b34f1cfdc3` |
| `raspberrypi-imx296-f1c327d2.c` | https://raw.githubusercontent.com/raspberrypi/linux/f1c327d2ae5c1ffdb7a17660bf87b4a22d2ae313/drivers/media/i2c/imx296.c | `2af91529cefa4510602ad6b28355207fde7ef89e105d3d54a786b853b17e50b8` |

## Reproduce records without rewriting the baseline

Use Python 3.12.14 / CadQuery 2.6.1 with the repository lock for heavy CAD work. From `candidate-vertical`, invoke the pinned interpreter with `../run_locked.py -- export_innomaker.py --storage compact --lens kowa_lm6hc`. Use a clean output folder when re-exporting; do not overwrite a folder while another process is writing it. `export_candidate.py` builds the official camera only; `export_innomaker.py` builds this variant through `innomaker_model.py`. Then run, each through `run_locked.py`: `verify_innomaker.py`, `verify_innomaker_stl.py` and `verify_innomaker_interpretation.py` (defaults: `--export innomaker/out/compact-kowa_lm6hc`, `--out innomaker/checks/compact-kowa_lm6hc`; `--out` must be outside the export). Windows exports do not byte-match the Linux-delivered files.

After the complete fresh manifest exists, run `python make_innomaker_records.py`, then `python make_innomaker_records.py --check`. This lightweight generator does not import or rebuild CAD. It rejects missing/stale manifest-bound sources, mismatched production STL hashes, wrong camera/variant, changed header assumptions, extra purchases or inconsistent nine-piece counts before writing records. It never edits the baseline BOM.

## Holds carried forward

**The original QT −23.99 mm failure remains unresolved.** No new camera geometry closes that reach failure. All unrelated physical, power, hot-drop, thermal/airflow, cooler registration, harness, flexible-service, structural, tooling, print and software gates remain open. The cooler proxy conflict does not demonstrate incompatibility of the official cooler; actual fit and service remain unqualified.

The full CSI route, contact orientation, ribbon width, stiffeners, latch travel, bends, slack and complete camera/module service are HOLD. The Pi end is connected on the supported bench **before the official Active Cooler**; only later camera-end access with the panel off is proposed. No software capture code is changed, and no physical 48/54 fps capture, raw-buffer, timestamp, DNG, display, power or temperature acceptance has been performed here.
