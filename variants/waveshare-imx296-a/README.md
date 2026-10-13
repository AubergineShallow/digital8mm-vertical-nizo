# D2 · Waveshare IMX296 Global Camera (A)

**Separate review variant, SKU 32501. Not a drop-in replacement, fabrication release, or hardware-validated build.**

**Status 2026-10-13: study delivered by the delivering agent (dot); not adopted. BLOCKED, and not applied to the
official design.** This branch carries the study as a Waveshare-only delta on `a0bfed9`; the
official-camera files are exactly that commit's. See the [fix-pass record](review/FIX-PASS-2026-10-13.md).

The official-camera design is preserved. This variant adds a source-backed camera profile,
standalone PCB-datum CAD study, a four-hole carrier interface study (rejected as drawn under
J7-R float), separate software
setup/configuration, tests, and an explicit hold register. **There is no integrated Waveshare
D2 assembly yet.** The sensor and C-mount shoulder are not located by the vendor drawing,
so translating the module to the old sensor plane would invent a fit.

## Start here

1. [Mechanical and retention decision](MECHANICAL-REVIEW.md)
2. [Cable route and service plan](FPC-ROUTE.md)
3. [BOM changes and unapproved fastener proposal](BOM-DELTA.md)
4. [Measurement checklist](MEASUREMENTS.md)
5. [Waveshare software setup](../../software/gs8-camera-evf/WAVESHARE-IMX296-A.md)
6. [Tests, reproduction and provenance](REPRODUCE.md)
7. [Machine-readable blocked status](review/status.json)

The nominal enclosure and lens collar stay unchanged as the **design target**. That is
not a clearance result. The official Raspberry Pi 5 Active Cooler remains selected;
its existing geometry/thermal holds are not closed by this camera substitution.

## What the primary drawing establishes

The [Waveshare drawing](https://www.waveshare.com/img/devkit/accBoard/IMX296-Global-Camera-A/IMX296-Global-Camera-A-details-size.jpg)
(vendor artwork, kept local and not in this repository; SHA-256 pinned in `camera-profile.json`,
see [sources](evidence/SOURCES.md)) gives a 38 ±0.2 mm square PCB,
a 30 mm square hole pattern with Ø2.5 holes, a Ø28.5 housing, 12.5 ±0.2 mm from
PCB front to housing front, 1.6 mm PCB thickness, and 2.5 mm rear connector projection.
The profile preserves unspecified tolerances as unspecified. The drawn Ø25 opening
is not used as a through-bore, optical-clearance or sensor datum.

The [product specification](https://www.waveshare.com/product/raspberry-pi/cameras/global-shutter-cameras/imx296-global-camera-a.htm)
identifies colour IMX296, 1456×1088 RAW10, C/CS lens support, an included C-CS adapter
and both cable types. Those statements do not establish sustained D2 frame rate,
thread engagement, lens focus or mechanical retention.

## No official-camera pass inheritance

The plain housing has no official-camera BFAR ring or lock tab. The old front lip,
anti-roll tab catch, bonded insert and rear cover catch cannot be credited as this
module's retention. Their existing files and receipts remain historical official-camera
content. The Waveshare release command deliberately returns **exit 2 / BLOCKED**.

Source tests may pass while all physical gates remain open. In particular, a new
camera does not fix or relax the original QT harness clearance gate, source-camera
connector/tool sweeps, cooler, power, thermal, print, structural or bench holds.

## Deliverable boundary

CAD files, when generated, are under `cad/out-study/`: nominal/max drawing envelopes
and an **unanchored, unapproved** four-hole frame. They are local PCB-front-datum
studies, not positioned in D2. No production STL is supplied. The frame is not an
installed retention solution until its anchor, fasteners and measured keepouts are
approved and checked. As delivered on 2026-10-12, no purchase, boot edit, repository push or
Windows work had occurred. On 2026-10-13 only the STEP header time stamps were normalised
(on Windows); the geometry was not re-exported.
