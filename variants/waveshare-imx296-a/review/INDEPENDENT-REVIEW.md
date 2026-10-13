# Independent source and artifact review: Waveshare IMX296 Global Camera (A)

Reviewed 2026-10-12 against local baseline `80a8059b607cc1ceda56553d99e952b8fc49d27e`.

> **Note added by the 2026-10-13 fix pass (review R-05).** The baseline `80a8059b…` exists in
> no published repository and cannot be verified. The reviewer is not named, so the
> "independent" label is the delivering agent's and is unverified. The STEP and drawing
> hashes below refer to the 2026-10-12 delivery, before header normalisation and before the
> drawing was removed from the repository. The body is kept as delivered. Current status and
> hashes: [FIX-PASS-2026-10-13.md](FIX-PASS-2026-10-13.md).

## Disposition

**No unresolved must-fix source or bounded-artifact defect was found after the correction below.** This
is a bounded review of the separate, deliberately blocked SKU 32501 study. It is
not approval of an installed mount, complete D2 assembly, manufacture, purchases,
optical performance, electrical operation or physical qualification.

**The seven standalone STEP artifacts pass the bounded consistency review below.**
The exporter subsequently completed behind the shared CAD lock and recorded its
own six-part and three-solid assembly read-backs. I independently checked the
receipt, all output/input hashes, STEP text/entity structure, and analytic
dimensions/volumes. I did not run a second CAD-kernel import, visualize the STEP
files in a CAD application, or run full baseline geometry checks. Full package
and transfer round-trip review remains separate.

## Finding and correction

### WS-R1 — P2, unsupported optical measurement claim accepted — corrected

The initial `camera_profile.py` validator checked the unknown optical dimensions
but did not check `optics.optical_backfocus_measured`. An in-memory copy with that
flag changed to `true` was accepted by both `validate_profile()` and
`release_status()`. This allowed an unsupported measurement assertion into a
validated profile. The release state itself stayed blocked; this was not a
physical-release bypass.

The implementation now requires the flag to be exactly `False` at
`camera_profile.py:56–57`. The regression test
`tests/test_profile.py::ProfileContract.test_no_unmeasured_backfocus_claim`
rejects `True`, `0`, `None`, and the string `false`. I reread the correction and
reran the complete profile suite: **15 tests passed**. Finding closed for the
reviewed source below.

## What was checked

- **Source correspondence:** the current vendor product page identifies SKU
  32501, colour IMX296, 1456 × 1088 RAW10, C/CS support, an included adapter, and
  both cable types. The included drawing visually matches the linked vendor
  drawing and its stored SHA-256. Board size/tolerance, hole pattern, housing
  envelope, front projection, PCB thickness, rear projection and rear attachment
  pitch correspond to its dimension callouts. No sensor or installed C-mount
  shoulder datum is established by that drawing.
- **Datum discipline:** PCB-front X=0 is kept separate from sensor and shoulder.
  The `0.6 - d` exploratory pose remains labelled an unmeasured sensitivity
  calculation and cannot generate a placed or released assembly. Unspecified
  tolerances remain unspecified. The drawing's Ø25 front-view feature is not
  used as a through-bore or optical-clearance result.
- **Retention and load path:** the old BFAR ring/tab/rear-cover catch cannot
  transfer. The U-frame is consistently labelled unanchored and unapproved.
  Housing-to-PCB strength, contact annuli, torque, creep, enclosure anchor,
  datum mismatch and assembly/service access remain explicit holds. The broad
  rear connector reserve is not treated as demonstrated clearance for the
  stand-offs.
- **BOM:** the proposed four screws, four nuts and four washers remain
  unselected, with purchase approval deferred until viability is known. The
  cited supplier item identities, dimensions and unit prices agree with the
  pages checked. The $0.96 parts-only sum, 8.60–8.95 mm stack and stated screw-tip
  projection arithmetic are consistent with the proposal. Shipping, tax, tools,
  tolerances, electrical insulation and locking are not silently included.
- **FPC and optics:** cable length, contact orientation, endpoint/latch geometry,
  bend/slack budget, complete service route, adapter geometry, lens engagement
  and optical qualification are unresolved, with no fitted route or optical
  result supplied. The retained baseline actually names Pi CAM/DISP 1. Keeping
  the original exterior and official Active Cooler is a design constraint, not
  a claimed clearance or thermal result.
- **Software:** the explicit CAM1 `imx296` overlay and CAM0 alternative correspond
  to the vendor setup guidance and upstream overlay reference. The connection
  is described as one camera, avoiding a false CAM1-to-Picamera2-index guarantee.
  No new runtime/driver or EEPROM programming is claimed. The examples remain
  separate, uncalibrated and `not_run`; calibration alone does not permit adapter
  import. The documented 48/54 FPS, manual controls, colour RAW10, queues, timing,
  DRM and DNG obligations are software contracts or pending measurements.
- **Isolation and strict gates:** baseline CAD/runtime sources and original D2
  configuration/commissioning examples have no diff from `80a8059`. The selected
  baseline hash verifier passes. The variant does not alter the QT checker or
  present original-camera receipts as Waveshare passes. All still-applicable
  original physical gates remain open.
- **CAD source scope:** six individual envelope/interface studies plus a clearly
  named unanchored study assembly are supplied, with no production STL. The code
  checks individual solid validity and STEP read-back volume. The receipt
  hashes all STEP outputs and records the runtime and stable input hashes. The
  combined assembly now has an exporter-run read-back check for validity, exactly
  three solids and agreement with the component-volume sum. This review verifies
  that receipt and its bindings, rather than repeating the CAD-kernel import. Exact connector,
  sensor, thread/adapter, fasteners, anchor, cable and D2 integration are omitted.

## Final artifact review, 2026-10-12 17:47 UTC

The detailed machine-readable result is
[`INDEPENDENT-ARTIFACT-CHECK.json`](INDEPENDENT-ARTIFACT-CHECK.json). Its pass is
limited to standalone-study artifact consistency, and retains
`physical_release: false` and `integrated_assembly_generated: false`.

- The receipt SHA-256 is
  `f1ba287aff1567de0e989c587e641469eacc249ff7a969768a9908db0fea56db`.
  Every one of its seven STEP hashes matches the delivered file; all four
  referenced source/drawing hashes match the current inputs. The STEP file set
  is exact, with no unlisted STEP or production STL.
- All seven files have complete STEP exchange wrappers and millimetre units.
  Text/entity checks find one `MANIFOLD_SOLID_BREP` in each individual file and
  three in the combined study. These entity counts do not independently prove
  topological validity; that result comes from the hash-bound exporter read-back.
- Nominal board hole surfaces are radius 1.25 mm on Y/Z ±15 mm axes. The two
  housing envelopes have radius 14.25 mm. The proposed frame has radius 3.6 mm
  corner bosses, radius 3 mm stand-offs, and radius 1.1 mm clearance holes on
  the same four axes. These dimensions appear in the STEP cylindrical surfaces.
- The six receipt bounds match the source construction. Independently calculated
  box/cylinder/subtracted-hole volumes, including the U-frame bar/arc union,
  match every reported proxy volume within 1e-7 mm³. This verifies construction
  arithmetic, not actual component material volume or structural strength.

| STEP file | Local X range, mm | Y/Z envelope or role |
|---|---:|---|
| `pcb_nominal_hole_pattern.step` | -1.6 to 0 | 38 × 38 mm square proxy, four nominal holes; unspecified corner radii bounded square |
| `housing_nominal_envelope.step` | 0 to 12.5 | Ø28.5 mm solid envelope; not a bore, thread or physical-material model |
| `rear_connector_unlocated_reserve.step` | -4.1 to -1.6 | 38.2 × 38.2 mm conservative non-material reserve; exact connector unlocated |
| `pcb_max_side_envelope.step` | -1.6 to 0 | 38.2 × 38.2 mm maximum-side envelope; no hole/edge fit result |
| `housing_max_depth_envelope.step` | 0 to 12.7 | Ø28.5 mm envelope with maximum specified depth; diameter tolerance unspecified |
| `UNAPPROVED_four_hole_frame_study.step` | -7 to -1.6 | 37.2 × 37.2 mm proposed U-frame envelope; unanchored and no fasteners included |
| `UNANCHORED-interface-study.step` | nominal three-part study | Board, nominal housing envelope and proposed frame only; no D2 placement |

The combined file explicitly names its root
`Waveshare_UNANCHORED_STUDY_NOT_D2_ASSEMBLY` and its three intended members. The
six individual STEP internal product labels are generic Open CASCADE translator
names; retain their descriptive filenames and companion receipt when sharing.
No generic internal label claims that the file is approved hardware.

The combined read-back reports three solids and proxy volume
12149.979289048486 mm³; the independent analytical component sum is
12149.97928904818 mm³. The rear reserve and tolerance envelopes are intentionally
separate and are not part of that three-solid study. In particular, omission of
the rear reserve from the combined view does not establish stand-off/connector
clearance. The `nominal_local_bounds` rear span is 38 mm; its exported conservative
reserve is 38.2 mm. This difference is consistent with the source and is not a
measured connector dimension.

The six WS holds remain present and blocked. No integrated assembly, positive
enclosure anchor, actual cable route, optical datum, physical pass or production
release was found in the receipt or STEP scope labels.

## Independently executed checks

Commands were run from this checkout using host Python, with no CadQuery build.

1. `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s variants/waveshare-imx296-a/tests -v`
   — **15 passed** after WS-R1 was corrected. This includes the temporary-output
   release command check: intentional exit 2 with `physical_release: false`.
2. `PYTHONDONTWRITEBYTECODE=1 python variants/waveshare-imx296-a/verify_baseline.py`
   — unchanged baseline constraints, no mismatches, `camera_fit_result: NOT TESTED`.
3. From `software/gs8-camera-evf`,
   `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`
   — **263 run, 255 passed, 8 skipped**. The skipped post-contract tests are not
   counted as passes. These are host tests with fake hardware; no physical frame
   acquisition, DNG round-trip, electrical test or FPS measurement occurred.
4. `git diff --quiet 80a8059 -- cad software/gs8-camera-evf/gs8_camera_evf software/gs8-camera-evf/examples/d2.config.example.json software/gs8-camera-evf/examples/d2.commissioning.example.json`
   — exit 0.

## Reviewed source identities

| File, relative to the variant unless otherwise stated | SHA-256 |
|---|---|
| `camera-profile.json` | `919ad356f61d7acd13d348c7f6e160a7a04a42da43d04573173027ed15d1d1e4` |
| `camera_profile.py` | `baaa1364c196e05f900287511a93ef265cca831dfd97a8bcb3d4d5800a8c268b` |
| `verify_baseline.py` | `bc040fceee37585b44a3af21e1c6c523adf2b078b95091ad3671196651f66f1e` |
| `tests/test_profile.py` | `d60ff952ea46bef29cda1aab611663c80503d35d6d4349c9e354e1ddef48b613` |
| `cad/export_study.py` | `b607b50d629ba87fb1804cc0966a5936d1b10b22564b832bb3c24e75faa37b1a` |
| Repository `software/gs8-camera-evf/WAVESHARE-IMX296-A.md` | `de235fb6498723b6b957f5a49cca736824520c43254b5f1d70989ba3286ff901` |
| Repository `software/gs8-camera-evf/tests/test_waveshare_profile.py` | `f0c436bd8adb3e2432a76c296a780ed3d69e07cc212f6a9542a0541d9730324f` |

## Primary references checked

- [Waveshare SKU 32501 product specification and package contents](https://www.waveshare.com/product/raspberry-pi/cameras/global-shutter-cameras/imx296-global-camera-a.htm)
- [Waveshare dimensional drawing](https://www.waveshare.com/img/devkit/accBoard/IMX296-Global-Camera-A/IMX296-Global-Camera-A-details-size.jpg)
- [Waveshare setup wiki](https://www.waveshare.com/wiki/IMX296_Global_Camera_%28A%29): direct retrieval was blocked; the search-indexed vendor text supplied the setup evidence, consistent with the implementation's own disclosure.
- [Raspberry Pi firmware overlay reference](https://raw.githubusercontent.com/raspberrypi/firmware/master/boot/overlays/README), IMX296 section.
- Bolt Depot [6365 screw](https://boltdepot.com/Product-Details?product=6365), [7362 nut](https://boltdepot.com/Product-Details?product=7362), and [7364 washer](https://boltdepot.com/Product-Details?product=7364).

No implementation files were edited by this review. No CAD process, external
message, purchase, boot change or repository push was performed.
