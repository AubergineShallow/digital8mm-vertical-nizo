# Delivery self-review: header-aware Innomaker D2 reconstruction (not independent)

> **Status (2026-10-13 fix pass).** This file was written by the delivering agent in the same commit series as the work it describes (fork commits c6a040f..d319a35). It names no separate reviewer, so it is a self-review, not an independent review; it was renamed from `INDEPENDENT-REVIEW.md`. Its numbers describe the delivered export (manifest `e0a5b3b6...`) and its 38/38 tally, which counted bookkeeping and self-confirming rows and kept the 24.164166 mm3 camera/lens overlap outside the count. Both are superseded: see [the 2026-10-13 fix record](review-2026-10-13/FIX-PASS-2026-10-13.md) and the current report `checks/compact-kowa_lm6hc/innomaker-checks.json`. The "supplied photo" below was not committed and cannot be checked from this repository.


**Disposition: suitable for delivery as a source/header-aware engineering review artifact. Actual camera fit and all release qualifications remain HOLD. This is a source and evidence review, not fabrication, optical, assembly, printing, retention-strength or capture qualification.**

## Scope and identity

Reviewed the recovered fork against official-camera baseline `a0bfed9f7ed88dad78ad1a5fcb6fc7504712b338`, including `model.py`, `innomaker_geometry.py`, the exporter, fresh validators, conditional assembly guide and derived BOM/print records. This review did not rebuild or independently rerun the full CAD assembly. It used source inspection, analytic geometry and read-only checks of saved evidence. The earlier lost fork's pass counts are not current evidence.

Current exported manifest: `e0a5b3b613490053a7c1afc70aa248dc1d3a8f5bdba93580a919ab7875dab1ab`. Independent file inspection found all 107 bound files and 76 bound sources matching that manifest, including a final recheck after validation. Its core dimensions and complete exterior bounds exactly match the retained official-camera manifest. Final report identities are recorded below.

The manufacturer STEP remains bound to SHA-256 `3d53cc2b16f4c4bd91776e57548dcf191689a6d4f7ee4962411cfb3f1b496b51`. Its reconstructed PCB follows R3.5 corners and all eight source-derived openings. The excluded upper solid, native Z13.2 CS reference, converter geometry, sensor/filter registration and received-part revision remain explicit assumptions.

## Known source incompleteness: rear headers

The supplied photo evidence identifies two rear 2-pin trigger/strobe headers opposite CSI. This review does not derive dimensions from that photograph. The public STEP omits the headers, their housings and solder-side details. No pin removal, bending or desoldering is assumed. Ordinary CSI operation requiring no extra trigger/strobe wires does not remove the hardware clearance requirement.

The 3/6/9/12/15/18 mm full-board rear prisms are hypothetical sensitivity cases, not measured heights or bounds on the received camera. Their XY coverage is conservative only if the actual hardware remains within the assumed footprint. The opposite-CSI half-board cases introduce an additional assumed XY region. Neither family qualifies the real headers.

A full-board prism extending more than 0.5 mm behind the PCB necessarily reaches the panel's rear-corner stops. Thus a collision in every full-board case does not prove the actual opposite-CSI headers collide, and must not be reported as a maximum permissible real pin height. Results must identify their assumed region, projection, obstacles and pose.

The static and insertion evidence must be described as covering the **complete saved public-STEP camera, with rear headers omitted**, rather than the complete photographed product.

## Passive guides: exact nominal source dimensions

All dimensions below are nominal source geometry in millimetres, not measured print dimensions.

| Feature | Source dimensions / interpretation |
|---|---|
| PCB axial limits | Rear X = -16.7; front X = -15.1 |
| Lower / upper guide bands | Z = 40.1 to 46.0 / 74.0 to 81.0; heights 5.9 / 7.0 |
| Tub side-rail X range | -17.9 to -12.2; width 5.7 |
| Tub rail / tab Y limits | Root starts at -25.55; side face ends at -20.0; front-tab tip ends at -17.0 |
| Tub fusion overlap | 0.05 into the wall, because cavity inner face is Y = -25.5 |
| Tub nominal wall thickness | 2.5, from Y = -28.0 to -25.5 |
| Tub tab reach | 8.5 from the wall inner face to Y = -17.0 |
| Panel side-rail X range | -19.6 to -12.2; width 7.4 |
| Panel rail / tab Y limits | Rail starts at 20.0; tab tips start at 17.0; roots reach 25.4 |
| Panel fusion overlap | 0.20 into the final panel, whose inner face is Y = 25.2 |
| Panel nominal skin thickness | 2.8, from final Y = 25.2 to 28.0 |
| Panel tab reach | 8.2 from its inner face to Y = 17.0 |
| Front/rear axial tab stock | 2.4 |
| Nominal side and axial clearance | 0.5; this is not a qualified tolerance allowance |

The 0.05 and 0.20 fusion overlaps are Boolean construction overlaps. They are **not** the load-bearing wall thickness. The nominal guide blocks are rooted over a broader rectangular patch in their parent walls; they are not attached by a free-standing 0.05 mm membrane. No obvious detached root or sub-minimum rectangular tab stock appears in this source review.

There is a small local separation worth retaining as an inspection gate: the top side-exhaust cutter ends at Z = 40.0, and the lower guide starts at Z = 40.1. Their X ranges overlap from -17.9 to -16.5. The resulting **0.1 mm nominal vertical separation** avoids the earlier cut into the guide root, but needs print/tolerance inspection. It is not evidence of a qualified 0.1 mm load-bearing ligament; the guide remains attached over the wall above and beside the opening.

### What this does not establish

Integrated containment proves that intended material survives the saved geometry. It does not measure the whole part's minimum wall, local stress, fatigue, impact, creep, layer bonding, extrusion layout, support removal or PCB-safe contact force. The unfilleted roots and approximately 8.5 / 8.2 mm projecting tab reaches remain plausible stress-concentration and bending concerns. Tub and panel print orientations place importance on real layer adhesion. No strength or print-manufacture acceptance follows from nominal rectangular stock or a watertight STL.

## Roll, axial contact and load path

For an ideal 39 mm square PCB with R3.5 corners and a side rail at absolute Y = 20 mm, analytic first contact under pure roll is approximately **1.81969 degrees**. Its tangent lies at absolute Z-offset 15.48386 mm from the optical axis, within the revised guide bands. This is an unloaded nominal geometric result; it is not a tolerance, torque or retention rating. Actual PCB corner shape, edge rounds, traces, components and header geometry remain unmeasured.

The front and rear axial stop faces nominally provide 0.5 mm free motion on each side of the PCB. The rear stop is part of the removable panel. Any fresh axial-contact test therefore applies only to the tested unloaded pose with the panel installed. It cannot establish pull-out strength, coupled roll/tilt/translation restraint or safe support with the panel removed.

The intended working load path remains camera/holder to threaded converter, lens, retained collar and tub seats. Guides receive no normal camera-weight, preload or lens-thread torque credit. Safe direct holder support, material/grip suitability, thread engagement, collar band, stiffness and all inherited structural gates remain open.

## Assembly and service review

The revised guide correctly requires identification and measurement of the headers, safe holder-supported lens threading, physical disconnection of power, and no force-through-interference closure. It retains Pi-end CSI mating on a supported bench module before the official Active Cooler; only later camera-end mating is proposed. Complete ribbon deployment and retained-cooler latch access remain unresolved.

Collar centring must occur with camera and converter absent: fit/centre the retained collar with its gauge, remove the gauge, then insert the camera. The guide was corrected to preserve this empty-optical-bay order. Gauge/camera coexistence must not be inferred.

The guide stages camera insertion with the carrier/module removed. The validation approach screen retains that module as additional obstacles. A clear result against those extra obstacles is conservative for the guide's isolated camera step. A hypothetical-header approach collision with the retained module does not prove the guide's module-absent step fails. The later carrier insertion, complete linked assembly, continuous motion, hand/tool access and actual header service remain unverified unless separately demonstrated.

## Records and remaining gates

The separate fork records retain SC1148, nine production prints, and no additional purchased parts. They remove the inapplicable bonded stub, its epoxy operation and the official-camera tripod-block detail; the unrelated retained tripod hardware is distinct. Inherited BOM statements are marked historical/unqualified.

The original QT -23.99 mm failure remains unresolved. Source-header completeness, cap identity, optical registration, converter/lens intrusion, safe holder access, PCB strain, full CSI/harness service, print/load/thermal/power qualification and 48/54 fps RAW/DNG hardware acceptance remain HOLD. No scalar PASS count may close those gates.

## Final fresh evidence disposition

The completed fresh records were read and their identities independently checked:

- `innomaker-checks.json`: SHA-256 `c66d752774c11b66582beb267dbeb2ebf69dda53e22aa8e06ed88085120befe4`.
- Its validator: SHA-256 `035d1b1ad9e7204ecd61d774cff5e69f90d7f5b768a118762048dcd243d36e7e`.
- `innomaker-stl-checks.json`: SHA-256 `fd3e5c2f33208f831d8e17a306a242c305c24102b744bf210a6eac76a5567b13`.
- Shared STL helper: SHA-256 `66bd1d7ad96eaa1302b7f5810da125d32706bfa24bfa5c88f7181ebca9c0403e`.
- Staging/interpretation addendum: SHA-256 `b8f4866bb08fe3110ace6d082c7bb4557fed3b16fec779e1fd56a489608bb44b`.

All report-to-manifest, validator/helper, addendum-input and 12 header-study STEP bindings matched the current files. The separate BOM, print-inventory and records-generator hashes also matched. No earlier lost report or pass count was substituted.

### Exact-crop method audit

The fixed-scene crop is approximately X [-40.91, 0.620752], Y [-19.512448, 79.512448], Z [40.487552, 79.512448] mm. Source inspection and analytic bounds confirmed that this region covers the saved camera, declared service-envelope primitives, converter and both hypothetical header families throughout the specified translations.

The final validator additionally enforces **704 finite, ordered, in-region moving-bound assertions** before screening: four camera/converter/envelope representations at 44 poses and both six-case header families at 44 poses. It also checks actual moving bounds at runtime. Fixed material is clipped by exact individual-solid intersections; subsequent queries use individual retained solids. Original saved STEPs are unchanged. This is a bounded exact-interference computation, not a bounding-box substitute for clearance. No minimum distance to every complete obstacle is claimed.

### What the fresh reports establish

- **38 scoped computational checks PASS; 0 FAIL; qualification remains HOLD.** Thirteen listed static targets have zero reported intersection with the complete saved public-STEP camera, with headers omitted.
- Both guide sets are contained in the saved parent parts and nominally clear of the reconstructed PCB. Fresh unloaded roll and axial-interference samples agree with the declared nominal guide arrangement; they do not establish safe contact forces or structural retention.
- The regularized service envelope contains every saved public-camera solid with zero uncovered volume. All 44 declared discrete camera/converter approach poses report zero interference against their listed fixed obstacles. The panel/finishing hardware, lens and flexible cables are absent; the carrier/module is retained as an extra obstruction condition.
- Ten STL files pass the reported topology/bounds checks: nine production pieces plus one centring gauge. This does not establish self-intersection freedom, slicer manufacture, minimum wall, strength or physical print quality.
- The camera/lens thread-proxy intersection remains **24.164166 mm3, HOLD**. It is neither erased nor treated as verified thread engagement.

### Header sensitivity disposition

- Every full-board prism intersects the panel rear stops, with 66 mm3 of reported panel intersection. That is a consequence of the intentionally broad XY assumption, not proof that the real opposite-CSI headers collide.
- The assumed opposite-CSI half-board prisms at 3, 6, 9, 12 and 15 mm show no installed intersection against the listed targets. The assumed 18 mm half-board prism intersects Pi material by 0.69 mm3.
- Both prism families at 3 and 6 mm clear the sampled approach. Cases from 9 mm encounter the extra-retained carrier/module during that screen. They do not establish failure of the guide's module-out camera-insertion step.
- **None of these numbers is a permissible real header-height limit.** Actual XY, housing/solder envelope, projection, tolerances, seated clocking and the later module-insertion path remain unknown or unverified.

No additional blocking inconsistency was found within this explicitly scoped review artifact. Delivery is appropriate only with the missing-header and release holds prominent. Complete-product fit, optical registration, safe holder access, full assembly/service, physical print/load/thermal/power qualification, the original QT -23.99 mm failure and hardware capture acceptance remain unresolved.
