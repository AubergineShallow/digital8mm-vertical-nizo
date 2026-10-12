# J2 exact-parts proposal, 2026-10-12

**Proposal only. No selected BOM, CAD, route, or purchase is changed. No finished wire cut is authorized.**

The existing Micro-Fit 3.0 family can be retained. Use **0430250200 receptacle housing on the Pi side** and **0430200201 plug housing on the switch side**. The existing 7.5 × 11 × 20 mm class box is **not a manufacturer-supported upper bound**: this exact pair is **24.77 mm long when mated**. Actual placement, latch access, wire roots, installed storage and service remain unresolved.

There are two sourcing paths. The 24 AWG path preserves the present gauge class but relies on discontinued distributor value-added leads with remaining stock. The current manufacturer lead path is readily orderable in small quantities but changes the proposed wire to 22 AWG; it requires explicit parts/gauge approval and fresh route checks. No current manufacturer-made 24–28 AWG Micro-Fit 3.0 precrimp pair was verified in this research. Micro-Fit Plus leads are not silently substituted.

## Exact parts and compatibility

| Function | Exact part | Quantity per installed J2 | Evidence |
|---|---|---:|---|
| Pi-side socket housing | Molex **0430250200** (43025-0200), dual-row 2-circuit | 1 | [Manufacturer product](https://www.molex.com/en-us/products/part-detail/0430250200); [customer drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/430/43025/430250200_sd.pdf) |
| Switch-side pin housing | Molex **0430200201** (43020-0201), 2-circuit, without panel ears | 1 | [Manufacturer product](https://www.molex.com/en-us/products/part-detail/0430200201); [customer drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/430/43020/430200201_sd.pdf) |
| Female contact used in both lead paths below | **0430300001** tin, reel contact; loose equivalent **0430300007** | 2, already crimped to leads | [Molex terminal specification](https://www.molex.com/en-us/products/part-detail/0430300007) |
| Male contact used in both lead paths below | **0430310001** tin, reel contact; loose equivalent **0430310007** | 2, already crimped to leads | [Molex terminal specification](https://www.molex.com/en-us/products/part-detail/0430310007) |

The housing drawings explicitly pair 43025 with 43020 and specify 43030 female / 43031 male terminals. Both contacts accept 20, 22 and 24 AWG, with **1.85 mm maximum insulation OD** and a catalog durability of 30 mating cycles. That OD is a contact compatibility limit, not a measured lead diameter. These contacts do not support all of the generic BOM's 28–24 AWG range: 26/28 AWG would require the appropriate smaller-wire terminal variants.

The housings are polarized and positively latched, but Molex lists **“Keying to mating part: No.”** Describe this as a distinct polarized connector family, not independently keyed circuits. Retain the receipt cross-mating check against FPS, RCY and headers. Keep socket contacts at the Pi side, identify both circuits at both ends, and use tin-to-tin mating.

## Sourcing paths

### A. Preserve 24 AWG: remaining-stock distributor precrimps

| Item | Exact lead | Qty installed / with one spare set | Distributor evidence viewed 2026-10-12 |
|---|---|---:|---|
| Pi-side leads | **0430300001-12-L4**, single socket to blunt end, blue, 24 AWG | 2 / 4 | [DigiKey](https://www.digikey.com/en/products/detail/molex/0430300001-12-L4/5962949): 259 shown in stock, discontinued at DigiKey, first price break 10 at USD 0.841 each |
| Switch-side leads | **0430310001-12-R4**, single pin to blunt end, red, 24 AWG | 2 / 4 | [DigiKey](https://www.digikey.com/en/products/detail/molex/0430310001-12-R4/5963765): 441 shown in stock, discontinued at DigiKey, first price break 10 at USD 0.846 each |

These are DigiKey value-added assemblies using Molex terminals, not current Molex OTS lead SKUs. This is a feasible one-off stock lead, with no assured replenishment. Both cores in a half share one color, so color alone cannot identify the circuit. Do not order a `-D` double-ended variant and assume cutting in half leaves the required purchased length.

[DigiKey's lead-length convention](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7159/Molex%20Jumper%20Wires%20Length%20rev2.pdf) defines 12 inches as **304.8 mm of wire before stripping and adding contacts**, tolerance **+6.35 / −0 mm**; the free end is blunt. It is not a housing-exit datum. Verify ≥231 mm exposed after housing insertion on receipt; do not import 304.8 mm directly as flexible installed length.

The [pin lead's component list](https://www.digikey.lu/en/products/detail/molex/0430310001-12-R4/5963765) identifies Alpha Wire 3050 RD001. The corresponding blue wire is Alpha 3050 BL001. Alpha's [official wire brochure](https://www.alphawire.com/-/media/Project/AlphaWire/AlphaWire/Files/Brochures/AL_1998_HUWbro_web-12-2023.pdf?rev=79d6cabfc6834683a0ba2b57af729242) gives 3050 as stranded 24 AWG, PVC, **1.42 mm nominal OD**. No manufacturing OD tolerance was verified; this is not proof of a 1.6 mm worst-case bound. Confirm the socket lead's exact wire build and measure OD before using existing cable clearance.

### B. Prefer current manufacturer precrimps: explicit 22 AWG option

Use **2 × Molex 2147611104** female-to-pigtail and **2 × Molex 2147631104** male-to-pigtail per installed pair, with the same housings above. Double those quantities for V-28S. Both are current catalog 22 AWG, black UL10002 stranded leads with tin contacts: [Molex female](https://www.molex.com/en-us/products/part-detail/2147611104), [Molex male](https://www.molex.com/en-us/products/part-detail/2147631104).

The official [female lead drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/214/214761/2147612105_sd.pdf) and [male lead drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/214/214763/2147631101_sd.pdf), both revision A1, give **L = 300 ±5 mm**, measured from the rear of the insulation crimp to the strip boundary, plus **5 ±1 mm** stripped/tinned free end (tinned diameter ≤0.9 mm). Part numbers 2147611104 and 2147631104 are explicitly in their tables. The housing rear datum and crimp rear datum must remain separate.

[DigiKey female](https://www.digikey.com/en/products/detail/molex/2147611104/12352892) showed 2,903 and [DigiKey male](https://www.digikey.com/en/products/detail/molex/2147631104/12352886) 2,093 in stock, active, quantity-one pricing USD 1.26 per lead. Both [receptacle](https://www.digikey.com/en/products/detail/molex/0430250200/252496) and [plug](https://www.digikey.com/en/products/detail/molex/0430200201/1132437) were in stock at quantity-one USD 0.36. One installed set therefore has a displayed parts subtotal of **USD 5.76**, or **USD 11.52** including one complete spare, before delivery, tax or tariff. Prices and stock are observations, not a quote or reservation.

This option changes the selected gauge class. A conservative new study must charge **two independent OD1.85 mm wire envelopes** until a smaller finished-wire maximum is documented. Keep the existing minimum bend-radius requirement unless the actual wire specification or testing requires a larger value; do not infer that larger-gauge wire will tolerate the old bend or that the 300 mm purchased lead determines a finished cut.

## Mechanical datums and service limits

- **Mated axial length: 24.77 mm nominal**, from both housing drawings. The old 20 mm estimate is 4.77 mm short.
- **Unmated halves: plug 16.89 mm REF; receptacle 14.00 mm.** They are not equal half-boxes. Their nominal housing overlap is 16.89 + 14.00 − 24.77 = **6.12 mm**. This is an inferred lower bound on axial withdrawal to separate the housing faces, not a qualified service stroke; tolerances, a separation gap and access still have to be added.
- The rear wire paths are parallel to the mating axis, **two centerlines 3.00 mm apart**, one column in the dual-row two-circuit housing. The local terminal orientation and pin-1 mark must follow the drawing; the world-space roots and clocking have not been selected.
- Molex's [application specification 430450001-AS A1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/applicationspecificationspdf/430/43045/430450001-AS-000.pdf), pages 2–3, recommends **12.7 mm free, unbiased wire per 2–6 circuit housing before a bend, tie or twist**. It is a wire-dependent recommendation, not a bend radius. A straight-exit study therefore starts with **24.77 + 2 × 12.7 = 50.17 mm** of nominal axial housing-plus-root length before bends. This is not a solid box and does not claim a D2 fit.
- **Latch travel and finger/tool envelope are not dimensionally established.** The receptacle drawing's 1.6 mm label is a measurement datum, not travel. Its 11.0 mm “for latching” detail depicts a board-header assembly; it is not a complete wire-to-wire access envelope. The application specification requires full latch release and straight axial withdrawal; pulling a single wire is not a service plan.

The supplier STEP imports completed through the pinned CAD interpreter and repository lock. Both contain one valid solid. [Measured results](vendor-model-bounds.json):

| Housing | Nominal STEP size: transverse X × axial Y × transverse Z, mm | Source |
|---|---|---|
| 0430200201 plug | **5.26 × 16.89 × 8.95** | [Molex STEP archive](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/3dcadmodels/430/43020/430200201_stp.zip) |
| 0430250200 receptacle | **5.28 × 14.00 × 10.83** | [Molex STEP archive](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/3dcadmodels/430/43025/430250200_stp.zip) |

These are nominal free-standing housing bounds, not maximum tolerance bounds, a registered mated assembly, contacts, wire roots, a moved latch or a device fit check. Nominal plastic solid volume is not usable wire-storage capacity.

### Bounded assessment of the earlier clear reserve

The earlier gross reserve is X[−33,−9], Y[−24,−7], Z[15,39.5], or **24 × 17 × 24.5 mm**. At 24.77 mm, the nominal mated pair cannot lie along any one of those axes. A diagonal placement is worth a separate study.

[Arithmetic results](reserve-arithmetic.json) use a **5.28 × 13.4 × 24.77 mm study box**, centered at (−21, −15.5, 27.25), with the mating axis 45° in XZ. The transverse 13.4 mm is deliberately 2 × the largest absolute supplier-Z extent, covering either sign before the halves' actual mating registration is established; it is not a measured mated height. The projected box is:

- X[−31.6243, −10.3757]
- Y[−22.2, −8.8]
- Z[16.6257, 37.8743]

This leaves arithmetic per-side margins of **1.3757 mm X, 1.8000 mm Y and 1.6257 mm Z** inside the old reserve. It suggests a concrete housing orientation to investigate; it does not prove the real pair fits, because no actual mating registration, tolerance stack, latch actuation, finger access, guide or exact D2 obstruction check was performed.

The two 12.7 mm free-root zones are **outside** that box assessment. Their outer pair-axis stations would be (−38.7378, −15.5, 9.5122) and (−3.2622, −15.5, 44.9878). Both are outside the earlier clear reserve even before adding the two 3 mm-spaced wire roots and wire radii. Consequently the reserve does not qualify roots, lead storage, service deployment or finished cuts. No new selected placement is made.

## Finished-cut gate

Place both exact housing halves and both wire exit pairs against corrected Pi J2 pads and measured Adafruit 1505 terminal roots first. For **each of four wires**, record housing/crimp hidden length, exposed installed centerline, terminal approach, solder and sleeve allowance, relaxed root segment, retained service slack, and offcut. Charge all remaining material. Then check closed storage, supported-panel disconnect access and full-material motion before accepting any cut.

The legacy 150 mm allocation, inherited 363–387 mm combined-half comparison and this proposal's 300 mm stock values are **not finished cuts**. No 20% fill-factor change, shorter bend radius, smaller-core substitution or unplaced-housing credit is justified here.

## Reproducibility and publication

`sources.json` retains verified source URLs and SHA-256 hashes. Downloaded vendor STEP/PDF files in `sources/` are local research inputs excluded by this folder's `.gitignore`; no redistribution license is inferred. Do not add them to a commit or publication bundle. `inspect_vendor_models.py` reads only these vendor models and writes nominal bounds and reserve arithmetic; it imports no D2 selected geometry. Run it through the repository's `run_locked.py` using the pinned CAD interpreter. This proposal does not certify manufacturing, energization or complete service.
