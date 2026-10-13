# BOM delta and unselected retention hardware

**Camera substitution is a study delivered by the delivering agent (dot); not adopted. No extra hardware is selected,
ordered or incorporated into an approved build.** Prices below are research
references checked 2026-10-12, not a checkout total or purchase request.
The fastener proposal serves retention option B, which is **rejected as drawn under
J7-R float** and has no straight-driver access shown (fix pass 2026-10-13, review R-21;
see [MECHANICAL-REVIEW](MECHANICAL-REVIEW.md), holds WS-07 and WS-08).

## Proposed camera substitution (study; not adopted)

| Item | Official-camera baseline | Waveshare review variant | Status |
|---|---|---|---|
| Camera | Raspberry Pi Global Shutter Camera, SC0926 class | Waveshare IMX296 Global Camera (A), SKU 32501 | Study delivered by the delivering agent (dot); not adopted; physical integration unqualified |
| Adapter | Official camera's modelled C-CS adapter | Included Waveshare C-CS adapter | Must measure shoulder/engagement; no inherited dimensions |
| CSI cable | Baseline assumes official 200 mm cable | Included 15-to-22-pin cable proposed for Pi 5 CAM1 | Length/contact orientation/fit unconfirmed; no extra cable selected |
| Retention | BFAR lip/tab/rear-cover catches and bonded insert | Unresolved; standalone four-hole frame study | Old retention is not applicable; production count unavailable |
| Cooler | Official Raspberry Pi 5 Active Cooler | Same selection | Existing source/fit/thermal holds remain |
| Exterior/lens collar | Existing D2 geometry | Preserved design target | No exterior change approved or claimed necessary yet |

All remaining baseline purchased selections and their existing approval/qualification
holds remain; the camera substitution does not approve any other outstanding part
proposal. Do not combine the old production-print count with the new frame to claim
a completed Waveshare parts count.

## Unselected 12-piece M2 proposal

This is a concrete candidate **only if** measured PCB contact keepouts, optics datum
and shell-anchor viability support the four-hole design. It is not an additional
approved shopping list and should not be put to a purchase decision before that.

| Qty | Candidate | Source / unit price USD | Parts subtotal USD |
|---:|---|---|---:|
| 4 | M2×0.4×10 mm A2 socket cap screws, DIN 912 / ISO 4762 | [Bolt Depot 6365](https://boltdepot.com/Product-Details?product=6365), $0.12 | $0.48 |
| 4 | M2×0.4 A2 hex nuts, DIN 934 | [Bolt Depot 7362](https://boltdepot.com/Product-Details?product=7362), $0.07 | $0.28 |
| 4 | M2 A2 flat washers, DIN 125 | [Bolt Depot 7364](https://boltdepot.com/Product-Details?product=7364), $0.05 | $0.20 |
| | **Parts-only reference** | **Tax, shipping, minimum-order effects and 1.5 mm Allen driver excluded** | **$0.96** |

Seller dimensions: screw head Ø3.62–3.98×1.86–2.00 mm, 1.5 mm hex drive;
nut 3.82–4.00 mm across flats×1.35–1.60 mm high; washer Ø5 mm,
ID2.20–2.34 mm×0.25–0.35 mm thick. These values inform the proposal, not a
manufacturing tolerance for the printed frame.

With nominal PCB1.6 + proposed stand-off3 + rear web2.4 + washer0.25–0.35 +
nut1.35–1.6 mm, nominal stack is 8.60–8.95 mm. A 10 mm screw would project
approximately 1.05–1.40 mm past the nut, ignoring unspecified PCB/print/fastener
length tolerances. The rear screw tip can reach PCB-front X=-9.75 mm, **5.65 mm
behind the drawing's nominal rear connector reserve**. This is why shell-clearance
and tool access must precede adoption. The local frame alone does not prove room.

The front washer's Ø5 contact annulus and rear support's Ø6 annulus need verified
clear copper/component lands. If electrical insulation or larger supports are
necessary, revise this proposal and cost rather than silently adding parts.
No locking adhesive, insulating washers, extra standoffs or extra enclosure
fasteners are selected. Clamp torque, loosening resistance and the enclosure
anchor are unresolved. Prototype screws must not be tightened on an unknown
component or an unsupported PCB.
