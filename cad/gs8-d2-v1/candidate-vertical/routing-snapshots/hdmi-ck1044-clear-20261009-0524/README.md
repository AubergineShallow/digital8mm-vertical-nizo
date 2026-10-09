# Corrected CK1044 / complete 300 mm HDMI study

This is a separate, unadopted route hypothesis. It preserves the failed selected
input and earlier generator snapshots. It does not approve a cable fold, the
laminate strain, a printed support, EMI performance, or a physical service
procedure. The baseline 56 and M1 physical gates remain open.

## Narrow change and conserved geometry

The legacy selected HDMI clips corrected CK1044 PCB pins 4 and 9 in the installed
pose, and pin 9 in premate. Exact pin contact localization is preserved at
`../../out/fps-service-study/fixed-switch-contact-diagnosis.json`.

The replacement natural U radius is `max(3.0, 5.5 - lift/2)` instead of
`max(3.0, 5.0 - lift/2)`. This raises both installed upper serpentine rows by
1 mm; raising only the middle row would leave less than the 10 mm diameter
required by the existing R5 turn. The left turn is solved again against the
complete 300 mm stock. Neither the cable length nor its width is reduced.

| Pose | Full material | Natural U | Miter | Post bends | Top/middle Z | Left turn X |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Installed | 300.000 mm | R5.5 | R3 | R5 | 94.5 / 84.5 mm | −125.127394 mm |
| EVF premate, drop 6 mm | 300.000 mm | R5.5 | R3 | R5 | 94.5 / 84.5 mm | −122.127394 mm |
| Both heads unplugged, lift/drop 6 mm | 300.000 mm | R3 | R3 | R5 | 95.5 / 85.5 mm | −125.554385 mm |

The complete strip is 10 mm wide with the existing unmeasured 0.4 mm thickness
allowance. The cylinder-based 45-degree miter preserves the mid-surface metric
analytically; that does not establish acceptable copper or outer-laminate strain.
The unchanged R3 material allowance still implies the existing 6.67% outer-layer
strain proxy for 0.4 mm total thickness. Actual neutral-axis placement, minimum
radius, permitted fold lifetime and electrical performance require hardware data.

`sampled-50-poses.json` covers EVF drop 0–6 mm and Pi lift 0–6 mm in 0.25 mm
increments. Every sample has exactly 300.0 mm analytical material length, no
listed wall hit, and no listed source-proxy hit, including corrected outer pins
and both unresolved common-A mirror positions. This is discrete sampling, not a
proof of a tolerance-robust continuous service motion.

## Geometry evidence

- `input.json`: all three full-material shapes, unchanged hard heads and headers.
  SHA256 `7c02b81255cbc9806e8ab6ada9cd24860ef3cd383882ea2c12afd94e772cabbb`.
- `manifest.json`: original frozen generation inputs and archived sources.
- `reproduction-check.json`: all three full dictionaries and all 50 length/radius
  samples reproduced from archived math, without importing live route geometry.
- `solid-checks.json`: exact convex sampled-material cells against source STEP
  geometry, the explicit corrected switch, and the separate cradle/web hypothesis.
  Mechanical manifest SHA256
  `e86480734edd35d097720f761012b05b208d73a982217fee0daaec67d44ab495`.
- `corrected-fps-context-0528.json`: exact copied diagnostic FPS wire/pair input,
  SHA256 `4b84b54c820103406e3b84e9f2479f9ab71c2fe6e59ed26f612a958be76b891c`.

The solid audit has eight passes: three hard-head/printed-part checks, all three
full-material poses, carrier/headers/premate translation through Y+70 mm, and
both-unplugged HDMI-only translation through Y+60 mm. Translation sampling is
2 mm. Panel and switch are removed first. Other flexible looms are not assumed
to disappear: their staging and crossings are checked separately.

`context-checks.json` confirms all three static full-material shapes clear the
modeled neighboring wires, corrected FPS pair/splices, modeled full power cores
and explicit stock reservation boxes. Its first-witness policy fully tests every
non-hit object and stops counting an obstacle after a positive contact is found.
The orientation-independent FPC envelope overlaps; this neither proves an actual
ribbon collision nor clears that incompletely modeled loom. See
`FPC-NEXT-DATUM.md` for its precise material, root and stock limits.

Unstaged HDMI-only extraction does have modeled loom conflicts: ribbon/QT at
Y+4 through +14 mm and ribbon/corrected-FPS-main at Y+12 through +24 mm. The Pi
hard head also conflicts with the positive power core in the fully unplugged
pose at Y0 and again during Y+6 through +24 mm extraction. An independent exact
original-polyline-to-head-box distance check, without capsule inflation, finds
1.350 mm centerline distance versus 1.6 mm nominal wire radius at Y0, or 0.250 mm
nominal penetration. Thus the switch-pin correction succeeds, but a complete
HDMI service sequence still requires explicit QT/FPS/power release and parking
or a new route. See `power-head-distance-check.json`.

This both-heads-free operation is a rejected diagnostic, not the selected
carrier sequence. The selected candidate keeps the Pi head mated, drops only the
EVF head and carries the ribbon with the stack. `SERVICE-SCOPE.md` distinguishes
the passed rigid candidate from the missing full carried/stowed loom proof.
`power-head-distance-complete.json` additionally verifies the installed/mated Pi
head has a nominal 2.242431 mm gap to the positive power tube. Do not introduce
an in-body Pi-head unplugging step into the selected carrier procedure.

The closest measured installed sampled-material distances are approximately
0.299 mm to pin 11 and 0.600 mm to the corrected body. These nominal clearances
are not tolerance margins or hardware fit certification.

Four test-only FPC-tool checks remain failed. Each proposed tool corridor clips
the Pi5 source solid by approximately 1.6843 mm³ even after HDMI removal. With
HDMI installed, it also intersects 40 sampled ribbon cells. These tool hypotheses
were retained unchanged; this route correction does not claim to solve FPC access.

The tested independent cradle is X[−112,−98.5], Y[21,24.5], Z[64.4,72.8], with
the R14 body cutout. Its beam is X[−101.5,−97.3], Y[−27,24.5], Z[64.4,66.9].
The underside web reaches Z58 through Y−4.5 and slopes 45 degrees to Z64.4 at
Y1.9. This audit tests its geometry only; structure, positive switch retention,
print orientation and actual bearing surfaces are separate studies.

## Reproduce

From the checkout root, use the pinned `.venv-cad/bin/python`:

1. Run this directory's `reproduce.py` for the archived geometry checks.
2. Run this directory's `verify_solids.py --snapshot <this-directory>/input.json`
   through `cad/gs8-d2-v1/run_locked.py` for the bound exact solid audit.
3. Run this directory's `verify_context_fast.py` through the same lock for the
   neighboring wire, reservation and extraction diagnostic checks.
   The original slower source is retained with an explicit aborted-run record.

An exact audit must be repeated against any subsequently changed mechanical
export; the earlier manifest does not validate a later integrated design.

## Sources and limits

- [Lorlin CK rotary drawing](https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf):
  corrected Ø27.5 mm body, 14.1 mm body depth, and pins reaching 18.1 mm rearward
  from the mounting face. Installed face is Y25.2, hence body Y11.1–25.2 and pins
  Y7.1–11.1. The 0.85 mm terminal radius is a conservative hole-derived reserve;
  it is not a measured pin cross section. Actual pin mapping/mirror remains gated.
- [Adafruit 3562](https://www.adafruit.com/product/3562): retained 300 mm ribbon.
- [Adafruit 3557](https://www.adafruit.com/product/3557) and
  [Adafruit 3556](https://www.adafruit.com/product/3556): retained Pi/EVF hard-head
  source family. Inferred exit clocking, complete actual housing dimensions and
  insertion depth remain physical gates.

Other open gates include the full 16 mm camera FPC shape and remaining stock,
complete USB/power-button/OLED stock stow, every loom's release/staging sequence,
real terminal/root datums, actual tool access, positive retention, abrasion,
tolerance stack, electrical isolation and a real assembly/disassembly trial.
