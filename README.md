# D2 vertical Pi camera

A restrained, Nizo-inspired development of [digital8mm](https://github.com/AubergineShallow/digital8mm), preserving its Git history. The Raspberry Pi stack stands vertically; a plain exterior side hides the cooling passages behind an integral plenum. Rear, front-edge and underside openings remain visible from their access directions.

**Review candidate only.** This is not a fabrication, energization, complete-service or production release. No physical build or thermal test is claimed. Every r7 physical gate that still applies to this layout ([gate map](cad/gs8-d2-v1/candidate-vertical/GATES-VERTICAL.md)), the candidate's own G-V-* gates and collar M1 remain open, together with the candidate's measured-part, wiring, cooling and printing holds.

## Current design

The current followup (commit `a0bfed9` by the delivering agent `dot`, starting from reviewed commit `f9704ac`) is published on the GitHub branch `review/vn-catch-qt-20261013` with the 2026-10-13 review-and-fix commit on top; `main` is untouched; see [the followup record](cad/gs8-d2-v1/candidate-vertical/review-2026-10-12-followup/FOLLOWUP-REVIEW.md) and [the 2026-10-13 fix-pass record](cad/gs8-d2-v1/candidate-vertical/review-2026-10-12-followup/FIX-PASS-2026-10-13.md). The earlier published branches below remain historical checkpoints.

Start with the [vertical candidate overview](cad/gs8-d2-v1/candidate-vertical/README.md), then the [review and comparison](cad/gs8-d2-v1/candidate-vertical/REVIEW.md), [assembly and wiring plan](cad/gs8-d2-v1/candidate-vertical/ASSEMBLY-VERTICAL.md), [bill of materials](cad/gs8-d2-v1/candidate-vertical/BOM-VERTICAL.md) and [wiring specification](cad/gs8-d2-v1/candidate-vertical/WIRING-VERTICAL.md).

The candidate retains silent recording, the 18/24 fps selector, exposure dial, record control and rear electronic viewfinder. Compact storage has ten physical production prints across nine assembly rows because the tub body and bonded catch stub print separately; original storage has eleven prints across ten rows. The gauge and coupons are excluded. Purchased hardware and cable selections are conditional on the documented receipt and bench checks.

The concealed-vent revision preserves the internal cooler cavity and replaces visible broad-side grilles with separate exterior air passages. Its edge openings, bridge/cleanout coupons and hand-occlusion tests are documented explicitly. Geometric continuity is not a cooling guarantee.

## History and reproduction

- The starting upstream commit is `d38468e58eb2b02d56743e2e0cfdd8f780818a65`.
- [The upstream README](https://github.com/AubergineShallow/digital8mm/blob/d38468e58eb2b02d56743e2e0cfdd8f780818a65/README.md) is retained as historical documentation; its earlier dimensions, gate counts and print guidance do not supersede the current review.
- [Export18 reference](cad/gs8-d2-v1/candidate-vertical/history/reviewed-export18/README.md) preserves the preceding reviewed vertical-board checkpoint.
- [Reproduction](cad/gs8-d2-v1/candidate-vertical/REPRODUCE.md) gives the selected Linux reference environment ([candidate lock](cad/gs8-d2-v1/candidate-vertical/requirements-candidate-lock.txt)), inspect/rebuild commands and Windows comparison limits. Cross-platform STEP formatting and mesh triangulation/order differ; full byte identity is not claimed. [Cloud setup](CLOUD-START-HERE.md) is the upstream r5/r6 text, kept for history.
- [Repository index](cad/gs8-d2-v1/candidate-vertical/REPO-INDEX.md): the selected pipeline, helper modules, studies, evidence with no in-repo producer, and the Windows path-length note.

The original upstream repository is unchanged. This development is published as its own history-preserving repository, [AubergineShallow/digital8mm-vertical-nizo](https://github.com/AubergineShallow/digital8mm-vertical-nizo) ([publication notes](cad/gs8-d2-v1/candidate-vertical/PUBLISHING.md)), not as an in-place upstream update.

## Review 2026-10-10

An independent review is recorded in [the issue register](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/ISSUE-REGISTER.md), [phase-1 status](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/PHASE1-STATUS.md) and [fix log](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/FIX-LOG.md). The published branch `review/vn-fixes-20261012` at `bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f` is the preserved starting checkpoint for the 12 October corrections. Earlier phase-1 and intermediate review branches remain historical.

## Corrective review 2026-10-12

The 12 October corrective work is on the review branch `review/vn-corrective-20261012` of this repository. It holds two commits on top of the starting checkpoint `bdfd44f`:

- the delivered commit `1b593952cd1b864b9d5bf4d879b0688dbaf70d4d` (author `dot`, delivered as the local branch `review/vn-corrective-local-20261012`), published unchanged so that its hash still matches the one the delivery package cites;
- the review-and-fix commit directly on top of it.

The review of the delivered commit (reproduction, four review dimensions and adversarial verification), its finding register and the open user decisions are in the [corrective review record](cad/gs8-d2-v1/candidate-vertical/review-2026-10-12-corrective/CORRECTIVE-REVIEW.md). See also the [review handoff](cad/gs8-d2-v1/candidate-vertical/REVIEW-HANDOFF.md) and [publication notes](cad/gs8-d2-v1/candidate-vertical/PUBLISHING.md). `main` is unchanged at `9ced753`; merging any review branch into `main` is the user's decision 15. A review branch can stay blocked by recorded engineering failures, and publication never closes a physical gate. Generated summaries: [check coverage](cad/gs8-d2-v1/candidate-vertical/COVERAGE-VERTICAL.md) and the [r7 gate and BX map](cad/gs8-d2-v1/candidate-vertical/GATES-VERTICAL.md).
