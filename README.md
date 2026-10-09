# D2 vertical Pi camera

A restrained, Nizo-inspired development of [digital8mm](https://github.com/AubergineShallow/digital8mm), preserving its Git history. The Raspberry Pi stack stands vertically; a plain exterior side hides the cooling passages behind an integral plenum. Rear, front-edge and underside openings remain visible from their access directions.

**Review candidate only.** This is not a fabrication, energization, complete-service or production release. No physical build or thermal test is claimed. All 56 inherited physical gates and M1 remain open, together with the candidate's measured-part, wiring, cooling and printing holds.

## Current design

Start with the [vertical candidate overview](cad/gs8-d2-v1/candidate-vertical/README.md), then the [review and comparison](cad/gs8-d2-v1/candidate-vertical/REVIEW.md), [assembly and wiring plan](cad/gs8-d2-v1/candidate-vertical/ASSEMBLY-VERTICAL.md), and [bill of materials](cad/gs8-d2-v1/candidate-vertical/BOM-VERTICAL.md).

The candidate retains silent recording, the 18/24 fps selector, exposure dial, record control and rear electronic viewfinder. Nine production printed pieces are modeled for compact storage. Purchased hardware and cable selections are conditional on the documented receipt and bench checks.

The concealed-vent revision preserves the internal cooler cavity and replaces visible broad-side grilles with separate exterior air passages. Its edge openings, bridge/cleanout coupons and hand-occlusion tests are documented explicitly. Geometric continuity is not a cooling guarantee.

## History and reproduction

- The starting upstream commit is `d38468e58eb2b02d56743e2e0cfdd8f780818a65`.
- [The upstream README](https://github.com/AubergineShallow/digital8mm/blob/d38468e58eb2b02d56743e2e0cfdd8f780818a65/README.md) is retained as historical documentation; its earlier dimensions, gate counts and print guidance do not supersede the current review.
- [Export18 reference](cad/gs8-d2-v1/candidate-vertical/history/reviewed-export18/README.md) preserves the preceding reviewed vertical-board checkpoint.
- [Cloud setup](CLOUD-START-HERE.md) and the [candidate overview](cad/gs8-d2-v1/candidate-vertical/README.md) describe the pinned CAD environment and reproduction entry points.

The original upstream repository is unchanged. This development is intended for a separate history-preserving repository, not an in-place upstream update.
