# INTERMEDIATE RESULT: review fixes in progress (not final, not verified)

**This branch is a work-in-progress snapshot taken on 2026-10-11 at about 17:20 (UTC+8).** It is not a release and it is
not the final result of the review. Nothing in it is verified end to end, and nothing has been printed, bought or
measured. Do not use it for fabrication.

- Branch: `review/vn-fixes-intermediate-20261011`.
- It is based on `9ced753`, the vertical-Pi candidate, which sits on top of the digital8mm r7 release `d38468e`.
- `main` in this repository is unchanged.

## What this snapshot contains

1. **Phase 1, complete and verified (commit `44f8131`).**
   - A review of `9ced753` that rebuilt the candidate and reproduced every number it claims. The issue register lists
     84 entries (VN-01 to VN-84): 0 blocker, 30 major, 47 minor, 7 info.
   - Fixes for 22 entries:
     - Windows-safe repository and I/O;
     - `.gitattributes` restored to byte-exact `* -text`;
     - third-party licence notices;
     - deterministic exports;
     - hardened evidence tooling;
     - an assembly-state model with a corrected build order;
     - r7 checks ported to the vertical geometry. They then failed on that geometry, as intended.
   - Tests: 240 OK. The r7 suite is intact.
2. **Phase 2, work in progress (this commit).** The source, check, test and document changes of nine work lanes:

| Lane | Closes (computed) | State |
|---|---|---|
| T1 plenum roof, mouths, skin | VN-51, VN-52, VN-59, VN-37 | done |
| T2 tab catch, EVF -Z stop, tub print minors | VN-53, VN-34, VN-25 (tub regions) | done |
| C1 carrier bed face, counterbores, third locator | VN-54, VN-56, VN-38 | done |
| C2 collar washer and LR foot, grip pocket, feather edge | VN-55, VN-58, VN-57 | partial: j4_screen newly fails |
| H1 run-lead reroute, usb_5v / pack_lead routes, EVF feed volumes | VN-26 (route part), VN-60 | done |
| H2 QT fan-in, HDMI margin, free-lead routes, pigtail | VN-43, VN-28 (part) | partial: pigtail rows wait on user decisions 4 and 6 |
| D1 generated WIRING-VERTICAL.md, BOM | VN-61, VN-63, VN-64 | done (J2 connector is a default) |
| D2 repo hygiene and entry docs | VN-10, VN-11, VN-12, VN-14, VN-15, VN-18 to VN-21, VN-50 | done |
| CF critical-feature probes re-nominated | VN-21, VN-25 (probe part) | partial: carrier_tie_bar_3 too thin |

The full lane log with real numbers is in
[`cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/FIX-LOG.md`](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/FIX-LOG.md).
Phase-1 results are in [`PHASE1-STATUS.md`](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/PHASE1-STATUS.md), the
register in [`ISSUE-REGISTER.md`](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/ISSUE-REGISTER.md).

## What is deliberately NOT in this snapshot

**`cad/gs8-d2-v1/candidate-vertical/out/` is still the phase-1 state.** That folder holds the exports and evidence:
STEP, STL, manifests and check reports.
- **It does not match the phase-2 sources in this commit.**
- The final evidence refresh is running: re-export of all three variants, the full check batch and the variant audits.
  Its results will be pushed with the final result.
- Until then:
  - the reconciler and the docs audit fail by design on this branch;
  - generated numbers in the candidate README, REVIEW and CHECKPOINT-STATUS may be stale.

## Known open rows at the time of the snapshot

- **pi5 vs Active Cooler overlap, 79.902671 mm3.** Needs the real cooler measured (hardware, VN-69).
- **Pigtail:**
  - length 251.8 / 250.9 + 27 mm > the 270 mm stock;
  - G-W5 drop 0.1625 V > 0.150 V;
  - ties and XT30 mouth rows.

  These wait on user decisions 4 (G-W5 fail branch) and 6 (ties or RTV-only). The 0.150 V limit is not relaxed.
- **Routes:**
  - the QT installed route touches the HDMI ribbon U-turn (4.94 mm3);
  - mate_reach j2_btn (cooler fin 1.95 mm3);
  - mate_reach xt30_pack.
- **Other rows:**
  - j4_screen fails on both compact variants after the grip change;
  - `carrier_tie_bar_3` is 0.877 mm against a 1.6 mm floor (tied to decision 6);
  - `no_added_material_in_original_cavity` has 1279 mm3 at the carrier floor seat rib; it is a scope question;
  - the new bed-edge chamfer rows fail for the panel, base_grip, collar and eyecup.
- **Fujinon and original-storage variant audits are running now.** Their results are not in this snapshot.

## Defaults taken that need the user's decision

- **13, J2 connector family:** default Molex Micro-Fit 3.0, 2-circuit, wire-to-wire.
- **10, EVF option C:** the reserve volume is kept free on the usb_5v route; the BOM quantity is 0.
- **16 (new), retention of the +Y tab-catch stub:** default is two-part epoxy.

Not decided and still open: 4, 6 and the others in the register's "User decisions".

## Next steps

1. The final evidence refresh.
2. An adversarial verification of every phase-2 fix, then a fix-up.
3. `FINAL-STATUS.md`, covering all 84 register entries.
4. A final push. This file will then be replaced by the final status.
