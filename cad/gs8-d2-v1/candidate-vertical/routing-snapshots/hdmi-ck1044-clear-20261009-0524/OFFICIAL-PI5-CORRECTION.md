# Official Pi 5 registration and neighboring ribbon addendum

This supplements the preserved HDMI/FPC studies. It does not revise their
inputs or turn their conditional geometry checks into hardware approval.

## Source and registration

The official [RP-010083-CA-1 STEP archive](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-010083-CA-1-rpi-5%203D%20STEP%20-%20No%20Graphics%20small%20file.zip)
is retained in `official-fpc-sources/`. The extracted board STEP SHA-256 is
`78164070c1cc7ab854382950d2e85926c6e35432f1e5a146b733397a7c6afb44`.
Preserve its `LICENSE.txt` when redistributing source-derived components. The
manufacturer describes the model as guidance without an accuracy guarantee.

Native X runs from the button end toward the USB edge; native Y56 is the GPIO
edge. The candidate transform, in mm, is:

`candidate = (−34−native X, 3.7−native Z, 63−native Y)`.

This is a proper rigid rotation and translation. Native board Z0 maps to the
existing kit underside datum, local Z18.5. All four source Ø2.7 hole axes match
the inherited four kit axes with maximum residual **0.000000 mm** at the
extracted coordinate precision. Source native hole centres are
(3.5,3.5), (3.5,52.5), (61.5,3.5), (61.5,52.5).

The source substrate spans native Z0.03..1.306; mating pads start at1.336.
The existing kit PCB proxy is1.6mm thick. The helper preserves that kit datum
and offers connector envelopes spanning source substrate-bottom alignment and
source substrate-top alignment, a0.324mm Y bracket. This is an explicit
registration uncertainty, not a tolerance specification or a stack movement.

## Isolated correction helpers

- `../../official_pi5_csi.py`: both complete48-solid CSI assemblies, their
  unchanged native STEP extracts, nominal placement and bracket envelopes.
- `../../official_pi5_geometry.py`: source-derived port envelopes, exact USB,
  Ethernet and GPIO components when requested, six-hole PCB proxy, real cooler
  hole axes, static latch bounds, USB2 head reservation and storage registration.
- Frozen copies are `source-official_pi5_csi.py` and
  `source-official_pi5_geometry.py` in this directory.
- `../../official_pi5_assembly.py` composes the corrected source components with
  explicit underside/SoC/button proxies and can reuse already imported parts.
  Its assembly compound is a container, not an occupied-volume sum. Optional
  `occupied_union()` performs a real Boolean union and fails explicitly if
  invalid. This helper is syntax checked; whole-Pi integration/union validation
  belongs to the parent export and is not claimed by the isolated landmark test.
- `official-pi5-geometry-checks-v2.json` is the final bound validation. The
  earlier `official-pi5-geometry-checks.json` is preserved as a preliminary run
  before storage/HDMI datum fields were added. The v2 run rejects changes to
  either helper while validating.

### Source-based corrections

| Feature | Official candidate placement or finding |
|---|---|
| CAM/DISP1, J4 | Complete X[−84.65225,−81.105], Y[−1.586,2.364], Z[46.155,62.855] |
| CAM/DISP0, J3 | Complete X[−90.85225,−87.305], same Y/Z |
| CSI opening | Native +Z becomes candidate−Y; width runs along candidate Z |
| CAM1 latch | X[−84.105,−81.105], Y[−1.586,2.064], Z[46.155,62.855], static pose |
| CAM0 latch | X[−90.305,−87.305], same Y/Z, static pose |
| USB2 stack | GPIO-side, candidate Z8.75032..23.25032, centre16.00032 |
| Ethernet | Opposite row, candidate Z44.785..60.715; inherited USB2/RJ45 identities were reversed |
| USB3 stack | Middle row, centre Z33.999895; inherited storage centre Z34 is within0.000105mm |
| HDMI0 | Native X25.8 becomes candidate X−59.8, agreeing with the selected head's X centre |
| HDMI1 | Native X39.2 becomes candidate X−73.2; inherited second proxy at−46.3 had wrong-sign spacing |
| GPIO | Source X[−91.9,−41.1], Z[7.96,13.04]; inherited footprint agrees within0.1mm |
| Cooler holes | Native(3.5,9.5),(61.5,46.5), Ø3.1, candidate XZ(−37.5,53.5),(−95.5,16.5) |

CSI identities come from the [manufacturer's labelled launch photograph](https://www.raspberrypi.com/app/uploads/2023/09/58f150c0-bd72-4e42-a77f-6be0890c8a80-1024x685.png),
used for identity only. No dimensions were inferred from photographs. Body,
latch, pins and tabs are preserved from the source solids. The latch is source
solid1262 for CAM0 and1310 for CAM1. The manufacturer specifies pulling and
tilting the flap, but the STEP has only one pose and does not establish travel,
opening angle, actual jaws or a permitted tool sweep.

## USB registration and mating limitation

Source transverse sections in `official-fpc-sources/usb-opening-sections.json`
and the accompanying PNG distinguish both USB stacks and their receptacles.
Upper USB2 shell-window centre is native Z13.92600077, candidate Y−10.22600077.
Its source front is candidate X−121.77999926. Retaining the original31×15.5×9.8mm
exterior allowance gives:

X[−152.779999,−121.779999], Y[−15.126001,−5.326001],
Z[8.250319,23.750319].

The source locates the socket, not the received cable head, inserted metal
length or strain relief. The whole allowance is outside the source face. Its
full200mm 5V lead must be rerouted, including a lateral departure before rising
past the middle storage body. The old wrong-row USB lead remains a diagnostic.

For the upper USB3 storage socket, use nominal translation
`[0,−0.365999995665,−0.000105]` from the inherited storage centre. The thickness
bracket remains a gate. Exact source USB solids retain their contacts and
cavities. Conservative whole-component envelopes fill those cavities. A coarse
plug reservation overlapping exact source contacts does not prove an incorrect
real connector, and does not justify deleting contacts or silently treating
the mating envelope as clear.

## HDMI registration limit

`official-fpc-sources/hdmi-mouth-inspection.json` records the official HDMI0
shell sections. At native Y−1, the straight shell window spans native
Z1.7355..4.0355, centre2.8855, hence candidate Y0.8145. This differs by+0.4645mm
from the inherited adapter's inferred port centre Y0.35. The outer shell lip
reaches candidate Z64.63035, whereas the PCB edge is Z63.

The Adafruit3557 catalogue does not define its body/ribbon-exit offset relative
to the inserted micro-HDMI plug. Therefore the existing full300mm proof remains
conditional on its frozen adapter pose. The socket correction alone cannot
authorize translating the whole adapter or claim a verified mating depth.
Any such change needs a separate named geometry study or received-part datum.

## Exact CSI context and cooler hold

`official-csi-context-checks.json` checks both exact source assemblies and the
registration bracket against the saved candidate solids, reinforced carrier,
selected full HDMI material, selected full mated FPS branches, modeled round
wires and full power capsules. Only the inherited cooler proxy intersects.

Each exact CSI assembly has32.3614367mm³ summed positive overlap with that
proxy, at Y[−1.2,0.6], Z[46.155,56.25]. CAM0 overlap X is
[−90.355,−87.305]; CAM1 is[−84.155,−81.105]. The broader registration boxes also
intersect; those results are reservation conflicts, not extra actual material.

The [official Active Cooler portal](https://pip.raspberrypi.com/categories/993-raspberry-pi-active-cooler)
provides an approximate drawing and product brief, with overall dimensions and
fan size, but no dimensioned fan-to-pin offsets, complete outline or public CAD.
The real cooler is intended for Pi5; the reported conflict diagnoses the coarse
proxy. Replace the four invented foot locations with the two actual board axes,
while keeping push-pin profile, spring/head height, fan/perimeter geometry and
actual CSI cable/latch corridor as a received-part measurement hold. No local
clearance cut has been invented here.

## FPC consequence

The earlier `FPC-NEXT-DATUM.md` remains the frozen diagnosis of its original
route:112.880754mm of unoriented centreline and87.119246mm of disconnected stock
allocation. After source correction, even that centreline has an unsupported
Pi departure: +Z instead of the real−Y opening. It is not a rooted full cable.

Retain the complete200mm stock with conservative16mm width throughout and the
0.3mm planning thickness allowance. The actual thickness/stiffener and bend
capability are unqualified. The [official GS camera mechanical drawing](https://pip-assets.raspberrypi.com/categories/810-raspberry-pi-global-shutter-camera/documents/RP-008195-DS-1-gs-camera-mechanical-drawing.pdf)
does not locate its15-pin mating plane, cable centre/exit frame or fully inserted
stiffener/free-flex boundary. Pi cable insertion/stiffener boundaries and contact
clocking also remain unknown. Those specific data prevent a source-grounded,
complete16mm-wide strip solve without adding unmeasured root assumptions.

The16.6×16.5×10.3mm old stock box is only the largest declared local reservation;
there is no demonstrated larger connected stock volume. Static source CSI and
a straight−Y approach reservation can be represented now. Neither these nor
the old87mm volume are a full200mm cable or a latch/tool clearance pass. R1 is
not qualified. All baseline56 and M1 physical gates remain open.
