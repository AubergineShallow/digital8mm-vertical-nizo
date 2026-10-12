# Factory 14 AWG lead study — 2026-10-12

**Outcome: CAB0244 is a credible termination candidate, but no complete passing
loom or final parts substitution has been established.** The authorized study
uses isolated files and preserves selected parts, exterior size, electrical
limits, current, cutoff and fuse assumptions. Nothing here authorizes purchase
or fabrication.

## Concrete candidate and supplier evidence

Investigate one [Pimoroni CAB0244 XT30 lead][cab], vendor variant
`41199325249619`. The supplier describes a 250 mm, 14 AWG silicone lead rated
15 A continuous / 30 A peak. Its [photo][cab-photo] visibly shows two recessed
socket contacts. This matches the **declared camera-side contact role only**.
The custom D2-13 pack is not a measured, received item: actual contact gender,
polarity, protection and cross-mating remain receipt gates. The similarly named
variant `41199325282387` is CAB0245, an XT60-to-XT30 adapter, and is not this lead.

Factory assembly is evidence that this vendor supplies a terminated 14 AWG
lead. It does not establish the exact connector envelope, exit pitch, solder
construction, copper area, insulation OD, bend limit or usable wire length.
Those are not published in the retrieved listing. In particular, **PRC's
400 × 0.08 mm construction and 3.5 mm OD are not attributed to CAB0244**.

The catalog's **250 mm is not established as 250 mm of exposed usable wire**.
The isolated 250 mm finished-path target requires 250 mm negative wire and a
nominal 230 mm sum of positive wire segments plus its 20 mm rigid fuse/joint
zone, excluding the connector body. Within this specific family, the mathematical
minimums preserving the 10% allowance are 248.304 / 244.668 mm finished positive /
negative paths, equivalent to 228.304 / 244.668 mm outside the positive rigid
zone. These are geometric requirements, not cut lengths: unspecified stripping,
solder overlap, factory-joint rigid length and real pad datums can increase the
required stock. In particular, the inherited 4 mm housing-to-fuse lead station
must be reconciled with the real factory joint before proposing an assembly.

The [Amass XT30U specification][xt30-spec] still does not document a 14 AWG
bare-cup termination. The proposal does not require hand-fitting thicker wire
to an unsupported cup or reducing strand count.

## Electrical margin is conditional

The equation and all unchanged inputs are in [README.md](README.md) and
[termination-options.json](termination-options.json). For a **comparison wire**
with 2.010619 mm² copper and 8.832413 mΩ/m at 20°C including the existing lay
factor, 250 mm per polarity gives:

| Mated connector loop assumption | Drop at 8.6 A | Margin below 0.150 V |
|---|---:|---:|
| Historical 1.0 mΩ | 0.130540 V | 19.460 mV |
| Sensitivity 1.2 mΩ | 0.132260 V | 17.740 mV |
| Sensitivity 2.4 mΩ | 0.142580 V | 7.420 mV |

These are not measured CAB0244 values. Both 1.2 and 2.4 mΩ cases remain because
the retrieved manufacturer's resistance scope does not resolve per-contact
versus total loop. Factory joints and actual end joints cannot be treated as
zero resistance; the built complete path must meet the unchanged hot-load gate.
The 60 mm assumed 18 AWG pack leads, 60°C copper, 1.03 lay factor and 5.798 mΩ
hot fuse contribution remain unchanged. No copper-displacement credit is taken
for the positive 20 mm fuse/joint zone.

## Isolated geometry results

All dimensions below are mathematical design reservations, not hardware
measurements: Ø3.7 mm wire, R9.25 centerline bends, the existing hypothetical pad
roots and 5 mm connector exit pitch. Both cores retain a 250 mm finished-path
allocation, a 25 mm service allowance and 15 mm face-out.

The [first service-corridor screen](factory250-cad.json) proved that a different
front-edge family can be shorter than the old rear-hump family. It cleared the
base grip, microSD and checked source solids, but intersected the tub floor and
both run leads. Its positive nominal insulation clearance at the Pi was only
0.15 mm, or 0.05 mm beyond the extra screening reserve. That is inadequate
evidence for a robust fit.

The subsequent [isolated variant](factory250_variant.py) moves the front
corridors and provides complete installed power-core curves:

| Check | Positive | Negative |
|---|---:|---:|
| Finished allocation | 250 mm | 250 mm |
| Stored excess above this family minimum | 26.526 mm | 29.798 mm |
| Minimum designed / sampled bend radius | 9.25 mm | 9.25 mm |

The conservative pair insulation gaps are 0.296 mm stored and approximately
0.600 mm deployed; see the JSON for exact values. A 90° negative
wrap gives 9.813 mm sampled minimum curvature and 0.650 mm nominal clearance
from the unchanged Ø5 mm fuse sleeve. The positive fuse remains a 20 mm rigid
zone. These checks do not validate unknown pad/cup construction or a continuous
deformation between stored and withdrawn states.

The [complete proxy/neighbour receipt](factory250-remedy-proxy.json) remains
**blocked**: the stored loops overlap other signal leads. It also flags
camera-FPC/FPS-header source proxies; the subsequent kernel distance checks
clear their tested housing boxes, so those proxy flags alone are not claimed
as exact housing collisions. An isolated alternate route for the existing 250 mm run wires
also fails mutual separation: approximately 1.087 mm centerline distance where
1.6 mm is required by the conservative test. The unsimplified polyline distance
is 1.188 mm; including both arc-chord error bounds still gives only 1.201 mm,
confirming the modeled overlap. These failures are preserved, not waived. Thus length alone
does not establish a usable CAB0244 installation.

The final [bounded CAD receipt](factory250-remedy-cad.json), produced under the
shared CAD lock, **rejects this remedy**. Its inputs did not drift during the run.
The proposed tub and base passages remained valid single solids with unchanged
bounding boxes, removing 141.166 and 3.269 mm³ respectively. The critical
results are:

| Exact geometric screen | Result | Interpretation |
|---|---:|---|
| New cutters to front loaded neck | 8.846 mm | Above the 1.6 mm keep-away screen |
| New cutters to rear loaded neck | 0.997 mm | Fails the 1.6 mm keep-away screen |
| Installed negative core to microSD, nominal insulation clearance | −1.080 mm | Overlap |
| Service negative core to tub, nominal insulation clearance | −0.450 mm | Overlap above the proposed floor passage |
| Positive core to Pi, minimum over each complete installed/service curve | 0.250 mm | Only 0.150 mm beyond the screening reserve |
| Installed fuse to base grip / tub | 0.220 / 0.503 mm | No modeled intersection; tight unqualified clearances |
| Installed negative insulation to fuse sleeve | 0.650 mm | No modeled intersection |

The modest front corridor offset improves its local Pi spacing, but the full
positive route still approaches the Pi near the assumed root. It does not
establish a robust tolerance allowance. The cutter-to-neck result is a spatial
distance screen, not a measured residual ligament or a strength calculation.
The inspected wire geometry is a sampled polyline; the extra 0.100 mm screening
reserve exceeds its arc-chord approximation error. It does not cover unknown
hardware dimensions, manufacturing tolerances or motion.

The isolated [tub](variant-step/tub.step) and [base grip](variant-step/base_grip.step)
STEP files are **rejected study artifacts only**. A retained bounding box does
not establish unchanged exterior surfaces or adequate strength. This closes the
bounded attempt without qualifying a complete route. Full loaded-wall
verification, retention, all service poses and hand access remain unresolved.

## Other termination paths screened

- **16 AWG cup tails plus two splices:** [TE SOLISTRAND 31819][te-catalog] is a
  concrete 16–14 AWG splice candidate. Its catalog gives a 14.40 mm bare length,
  4.06 mm OD and 2.26 mm barrel ID. Insulation adds length/diameter, and actual
  fine-strand tooling, pull performance and hot resistance remain unqualified.
  At 280 mm total with 40 mm 16 AWG tails, the 2.4 mΩ loop case reaches
  0.152074 V before either added joint. The shorter 250 mm route budget changes
  that arithmetic, as shown below, so this remains a conditional alternative.
- **Amass UH60 pair:** the [manufacturer explicitly supports 14/12 AWG][uh60].
  The [2026V1E drawing][uh60-drawing] gives 26.7 × 16.4 × 9.2 mm bare mated or
  35.2 × 16.4 × 9.2 mm with rear covers. At the current 21° yaw / 45° pitch,
  the tolerance-maximum covered bounding box is 35.82 × 27.04 × 31.96 mm,
  exceeding the 25 mm grip width and 26.8 mm pack headroom. The bare pair is
  30.21 × 24.89 × 25.95 mm at that pose, leaving only 0.85 mm vertical space
  before bends or extraction. The 7.7 mm nominal overlap inferred from the
  drawings is not a published extraction stroke. This would need a new pack
  interface and pose, not just thicker wire.
- **Anderson SBS Mini:** [documented contacts][sbs] can accept the two gauges,
  but its 49.7 mm mated length is substantially larger than the selected
  26 mm proxy. Published resistance is an average rather than a guaranteed
  mixed 14/18 AWG loop bound. It has no demonstrated advantage here.

### Sourced wire with 16 AWG tails at the shorter 250 mm budget

This alternative combines PRC's documented 14 AWG construction with 16 AWG
XT30U terminal tails and **two additional transition splices**, one per core.
It avoids assigning undocumented copper properties to CAB0244. All previous
electrical inputs remain unchanged, including the 2.4 mΩ connector-loop case:

| Allocation per polarity | Drop before new joints | Combined hot budget for two splices | Equal budget per splice |
|---|---:|---:|---:|
| 226 mm 14 AWG + 24 mm 16 AWG | 0.145112 V | 0.568387 mΩ | 0.284194 mΩ |
| 210 mm 14 AWG + 40 mm 16 AWG | 0.146800 V | 0.372146 mΩ | 0.186073 mΩ |

Those maximum budgets leave **zero** additional margin. For the 40 mm-tail case,
even 0.1 mΩ per added splice would give 0.148520 V, leaving only 1.480 mV.
The catalog does not guarantee such hot splice resistance. Tail dimensions,
the crimp process for this fine-strand wire, insulation, strain relief and
actual rigid joint lengths are unresolved. The bare splice is already larger
than the Ø3.7 mm wire reservation; its insulated assembly needs separate space.
The 250 mm allocation is not permission to add a splice's physical length on
top of a 250 mm cut. Positive fuse placement and real cut/overlap conventions
must be reconciled. No selected part or geometry is changed by this comparison.

## Remaining decision and measurements

Keep CAB0244 as the preferred **exploratory factory-termination candidate**.
Do not change the selected BOM yet. The next useful evidence is:

1. Actual CAB0244 housing, wire OD, exposed usable length, joint/strain-relief
   lengths, conductor resistance and temperature behavior. Reconcile the vendor
   length convention with the positive fuse zone and both real cuts.
2. Received pack contacts, polarity, protective construction and direct mating;
   actual X1203 pads and both wire exit directions.
3. A complete stored/service route that clears all signal wires and housings,
   with deployable retention and valid internal passages preserving the loaded
   material. The present isolated remedy fails the rear-neck screen, microSD,
   tub and wire-neighbour checks and is not that complete route.
4. Measured complete hot-path drop at 8.6 A, including fuse, contacts, factory
   joints and end joints, against the unchanged 0.150 V requirement.

No further connector/pack change is justified as a selected purchase by the
present evidence. Any such change needs its own concrete parts proposal.

## Reproduce

From the repository root, using the existing CAD environment:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/corrective-2026-10-12/power-options/termination_options.py --check
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/corrective-2026-10-12/power-options/probe_remedy.py
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/corrective-2026-10-12/power-options/probe_remedy.py --cad
```

The first two are CAD-free. The last reads manifest-bound STEP solids and writes
only this report directory. Source drawings are linked rather than redistributed.

[cab]: https://shop.pimoroni.com/products/xt30-adapter-cables?variant=41199325249619
[cab-photo]: https://cdn.shopify.com/s/files/1/0174/1800/files/xt30-1.jpg?v=1701882162
[xt30-spec]: https://www.china-amass.net/uploads/XT30U-MF.rar
[te-catalog]: https://www.te.com/content/dam/te-com/documents/appliances/global/solistrand-terminals-and-splices-qrg.pdf
[uh60]: https://www.china-amass.net/uh60-fgold-plating-product/
[uh60-drawing]: https://www.china-amass.net/uploads/121.UH60-M-Product-Specification-Gold-Plated-2026V1E-Solder-cup-facing-positive-and-negative-terminals.pdf
[sbs]: https://www.andersonpower.com/content/dam/app/ecommerce/product-pdfs/SBS-Mini/ds-sbsmini.pdf
