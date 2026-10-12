# Power-pigtail repair options — 2026-10-12

**Exploratory assessment only.** No selected part, external dimension, cutoff,
current, fuse, resistance assumption, route, tie or printed geometry is changed
by this assessment. No hardware measurement or physical qualification was
performed. Baseline: `bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f`.

## Current decision status

The exploratory 14 AWG routing/termination study was authorized. Its subsequent
[factory-lead study](FACTORY-LEAD-STUDY.md) identifies Pimoroni CAB0244 as a
conditional, factory-terminated 250 mm candidate. A different routing family
meets individual length/bend budgets, but the final bounded CAD attempt fails
the rear-neck keep-away screen, installed microSD clearance, a service tub
clearance and other cable separations. **No final BOM substitution is ready.**

The original 280–285 mm generic-wire comparison below remains useful electrical
sensitivity evidence. It is **not a purchase recommendation, approved cut list,
drop-in wire substitution or fabrication release**. The final parts decision
still requires documented or measured terminations, contact resistance and full
geometry evidence.

The source-backed wire candidate is [PRC 14 AWG silicone][wire14], red SW-14R and
black SW-14B, in 36-inch stock. Its page specifies 3.5 mm OD and more than 400
strands of 0.08 mm copper; the [vendor variant feed][wire14variants] confirms the
two SKUs. The calculation conservatively uses 400 strands. The retrieved source
does not supply dimensional tolerances or a minimum bend radius.

## Why the existing selection is not resolved by tie changes

The existing 270 mm 16 AWG electrical upper case is **0.16253577 V**, against
0.150 V. Under exactly those assumptions, the maximum per-polarity copper/path
allocation is **225.432846 mm**. Routing or tie edits cannot change that result
while retaining 270 mm of charged copper.

The installed route family has minima 251.834878 mm positive and 250.916096 mm
negative. With the unchanged 10% finished-length allowance, these require
279.816531 mm and 278.795663 mm stock, respectively. These are minima of the
declared family, **not a proof of the globally shortest physically possible
route**. No complete passing 16 AWG route has been demonstrated.

An isolated arithmetic probe shortened rear X coordinates from −100/−104 to
−95/−99. This produced 241.834878/240.916096 mm route minima and positive
1.165122/2.083904 mm margins at a 270 mm allocation. However, consuming the
remaining wire in the existing positive hump raised its centerline to Z99.94982,
beyond the Z97.5 interior; 84 sampled points overran the wall. It is rejected as a
complete repair. The source-proxy check reports only the own XT30 housing, but
this does not establish exact solid or cable-neighbour clearance.

The baseline [harness report](../../out/compact-kowa_lm6hc/harness-checks.json)
also records that no allocated carrier tie reaches either core. Merely selecting
RTV-only leaves positive face-out at 12.86 mm instead of 15 mm, and both declared
service corridors intersect the microSD, tub and base grip and overlap the run
leads/FPC. Retention, storage and service routing all require an actual redesign.

## Exact electrical model and inputs

All path lengths below are **per polarity**; the factor 2 charges both conductors.
Lengths are in mm, areas in mm², `r` in mΩ/m, remaining resistances in mΩ:

```text
A(n) = n × pi/4 × (0.08)^2
k = 1 + 0.00393 × (60 − 20) = 1.1572
r(gauge) = (1000/58) × 1.03 / A(gauge)

Vdrop = 8.6/1000 × [
  2 × k × ((L14/1000) × r14 + (L16/1000) × r16
             + (60/1000) × r18)
  + 4.46 × 1.30 + R_XT30_loop + sum(R_added_splices)
]
L14 + L16 = total finished path allocation per polarity
```

| Input | Value | Basis / unresolved distinction |
|---|---:|---|
| Peak current / drop limit | 8.6 A / 0.150 V | Existing design requirements; unchanged |
| Copper resistivity at 20°C | 1/58 Ω·mm²/m | Existing IACS model assumption |
| Copper temperature / coefficient | 60°C / 0.00393 K⁻¹ | Existing model assumptions; not measured assembly temperature |
| Lay multiplier | 1.03 | Existing conservative assumption; not measured |
| PRC 16 AWG area | 250 × π/4 × 0.08² = 1.256637 mm² | Conservative interpretation of [vendor strand statement][wire16], not measured strand count/tolerance |
| PRC 14 AWG area | 400 × π/4 × 0.08² = 2.010619 mm² | Same interpretation of [vendor strand statement][wire14] |
| Pack-side lead | 60 mm per polarity, 150 × 0.08 mm strands = 0.753982 mm² | Existing 18 AWG lead; strand count is an assumption, MP-PACK open |
| Fuse | 4.46 mΩ cold × 1.30 = 5.798 mΩ hot | Existing Littelfuse 0251015.MXL model; hot multiplier is assumed, not measured |
| XT30 mated-loop resistance | Historical 1.0 mΩ; sensitivity 1.2 and 2.4 mΩ | Scope of retrieved manufacturer's ≤1.2 mΩ figure is unresolved |
| Added splice resistance in table | 0 mΩ | Arithmetic baseline only; real added joints consume the reported budget |

The positive 270 mm allocation currently includes a 20 mm rigid fuse/joint zone.
The electrical model intentionally takes no copper-displacement or solder-overlap
credit. Do not interpret the proposed finished allocation as an independently
qualified flexible-wire cut length.

## Electrical sensitivity, before extra splice losses

All other model inputs remain identical across columns. The 1.2 and 2.4 mΩ
columns are explicit sensitivity cases, not a resolved interpretation of the
connector specification.

| Construction per polarity | 1.0 mΩ loop | 1.2 mΩ loop | 2.4 mΩ loop |
|---|---:|---:|---:|
| 280 mm all 14 AWG | 0.135814 V | 0.137534 V | 0.147854 V |
| 285 mm all 14 AWG | 0.136693 V | 0.138413 V | 0.148733 V |
| 300 mm all 14 AWG | 0.139330 V | 0.141050 V | **0.151370 V** |
| 280 mm total: 240 mm 14 AWG + 40 mm 16 AWG | 0.140034 V | 0.141754 V | **0.152074 V** |
| 285 mm total: 245 mm 14 AWG + 40 mm 16 AWG | 0.140913 V | 0.142633 V | **0.152953 V** |
| 300 mm total: 260 mm 14 AWG + 40 mm 16 AWG | 0.143549 V | 0.145269 V | **0.155589 V** |

All-14-AWG maximum path lengths are 360.692554, 350.908650 and 292.205225 mm for
the three connector assumptions. Thus **300 mm is not a robust recommendation**
under the unresolved 2.4 mΩ loop case. At 285 mm all-14 AWG and 2.4 mΩ, the entire
remaining voltage margin is only 1.26667 mV.

The mixed-gauge option introduces **two additional transition splices**, one per
core, relative to an otherwise equivalent uninterrupted conductor. For 285 mm
total with 40 mm tails and a 1.2 mΩ connector loop, the combined hot resistance
budget of those two joints is at most 0.856686 mΩ, or 0.428343 mΩ each if divided
equally. Spending the whole budget leaves zero additional margin. The 2.4 mΩ
connector case fails even before the splice loss. Tail lengths here are sensitivity
inputs, not fitted joint locations or approved termination instructions.

## Termination and source evidence

The [official Amass XT30U page][xt30] links the [XT30U-MF archive][xt30archive]. Its
female 2025V0 A.06.1 and male 2025V0 A.01.1 specifications were downloaded and the
female drawing visually inspected. They rate the connector with 16 AWG and state
contact resistance ≤1.2 mΩ. The retrieved drawing does **not** specify solder-cup
diameter or approve 14 AWG. Direct termination is therefore unsupported by the
present evidence. No strand reduction or guessed cup fit is proposed.

The alternatives requiring proof are (a) a documented compatible direct
termination, or (b) retained 16 AWG cup tails with separately supported, insulated,
strain-relieved transition joints whose dimensions, process, pull performance
and hot resistance are verified. Any additional purchased termination parts need
a subsequent explicit parts decision. Source drawings are linked, not redistributed;
their redistribution license has not been established.

## Geometry and qualification work still required

1. Locate and measure the real pads, wire exits, XT30 solder cups, fuse joints and
   complete insulated rigid lengths. Reconcile total path versus actual cuts.
2. Investigate Ø3.7 mm reservations for 3.5 mm nominal wire, retaining the existing
   +0.2 mm diameter allowance. Preserving the present R8/Ø3.2 ratio suggests an
   **analysis** centerline radius of R9.25; this is not a vendor-qualified bend limit.
   The existing negative wrap has only R8.325 minimum curvature.
3. Redesign installed slack storage and explicit per-core retention. The current
   hump cannot simply accept the longer allocation. Tie bands/heads, splice
   sleeves and strain relief must have physical homes.
4. Recheck installed cores, both neighbouring cores, fuse sleeve and every other
   cable/part; update passages only after proving valid single solids and at least
   1.6 mm loaded ligaments. Preserve the external size and selected hardware.
5. Prove the flexible service corridor and retained deployment, 15 mm face-out,
   unchanged service allowance, hand access and stow. Repeat the 201 rigid service
   poses if local wire/pocket geometry changes; rigid motion alone is insufficient.
6. Reconcile connector loop resistance and measure the built assembly at G-W5 hot
   8.6 A, including copper, contacts, fuse and any new splices. Existing pad,
   pack-lead, construction and physical-service gates remain open.

## Reproduction

From the repository root:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/candidate-vertical/corrective-2026-10-12/power-options/reproduce.py --check
```

[reproduce.py](reproduce.py) contains the complete equation/inputs and an isolated
in-memory two-coordinate route probe; [assessment.json](assessment.json) records
all numeric cases and route-source hashes. It imports no CAD and requires no CAD
lock. `--check` writes nothing and detects input/source/result drift. Run without
`--check` only to deliberately regenerate this exploratory assessment, or use
`--out /tmp/power-options.json` to keep its saved evidence intact. It does not run
the selected harness verifier or certify the current exported geometry.

[wire16]: https://www.progressiverc.com/products/prc-silicone-wire-16-awg
[wire14]: https://www.progressiverc.com/products/prc-silicone-wire-14-awg
[wire14variants]: https://www.progressiverc.com/products/prc-silicone-wire-14-awg.json
[xt30]: https://www.china-amass.net/xt30u-f-product/
[xt30archive]: https://www.china-amass.net/uploads/XT30U-MF.rar
