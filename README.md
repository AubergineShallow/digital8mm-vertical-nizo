# D2 vertical Pi camera

A restrained, Nizo-inspired development of [digital8mm](https://github.com/AubergineShallow/digital8mm), preserving its Git history. The Raspberry Pi stack stands vertically; a plain exterior side hides the cooling passages behind an integral plenum. Rear, front-edge and underside openings remain visible from their access directions.

**Review candidate only.** This is not a fabrication, energization, complete-service or production release. No physical build or thermal test is claimed. Every r7 physical gate that still applies to this layout ([gate map](cad/gs8-d2-v1/candidate-vertical/GATES-VERTICAL.md)), the candidate's own G-V-* gates and collar M1 remain open, together with the candidate's measured-part, wiring, cooling and printing holds.

## Current design

Start with the [vertical candidate overview](cad/gs8-d2-v1/candidate-vertical/README.md), then the [review and comparison](cad/gs8-d2-v1/candidate-vertical/REVIEW.md), [assembly and wiring plan](cad/gs8-d2-v1/candidate-vertical/ASSEMBLY-VERTICAL.md), [bill of materials](cad/gs8-d2-v1/candidate-vertical/BOM-VERTICAL.md) and [wiring specification](cad/gs8-d2-v1/candidate-vertical/WIRING-VERTICAL.md).

The candidate retains silent recording, the 18/24 fps selector, exposure dial, record control and rear electronic viewfinder. Nine production printed pieces are modeled for compact storage. Purchased hardware and cable selections are conditional on the documented receipt and bench checks.

The concealed-vent revision preserves the internal cooler cavity and replaces visible broad-side grilles with separate exterior air passages. Its edge openings, bridge/cleanout coupons and hand-occlusion tests are documented explicitly. Geometric continuity is not a cooling guarantee.

## History and reproduction

- The starting upstream commit is `d38468e58eb2b02d56743e2e0cfdd8f780818a65`.
- [The upstream README](https://github.com/AubergineShallow/digital8mm/blob/d38468e58eb2b02d56743e2e0cfdd8f780818a65/README.md) is retained as historical documentation; its earlier dimensions, gate counts and print guidance do not supersede the current review.
- [Export18 reference](cad/gs8-d2-v1/candidate-vertical/history/reviewed-export18/README.md) preserves the preceding reviewed vertical-board checkpoint.
- [Reproduction](cad/gs8-d2-v1/candidate-vertical/REPRODUCE.md) gives the pinned environment ([candidate lock](cad/gs8-d2-v1/candidate-vertical/requirements-candidate-lock.txt)), the Windows and POSIX commands and the inspect commands. [Cloud setup](CLOUD-START-HERE.md) is the upstream r5/r6 text, kept for history.
- [Repository index](cad/gs8-d2-v1/candidate-vertical/REPO-INDEX.md): the selected pipeline, helper modules, studies, evidence with no in-repo producer, and the Windows path-length note.

The original upstream repository is unchanged. This development is published as its own history-preserving repository, [AubergineShallow/digital8mm-vertical-nizo](https://github.com/AubergineShallow/digital8mm-vertical-nizo) ([publication notes](cad/gs8-d2-v1/candidate-vertical/PUBLISHING.md)), not as an in-place upstream update.

## Review 2026-10-10

An independent review of this candidate is recorded in [the issue register](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/ISSUE-REGISTER.md) (84 entries, fix plan and the user decisions), with [the phase-1 status](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/PHASE1-STATUS.md) and [the fix log](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/FIX-LOG.md). The fixes are on the local branch `review/vn-fixes-20261010` and are not pushed (user decision 15). Generated summaries: [check coverage](cad/gs8-d2-v1/candidate-vertical/COVERAGE-VERTICAL.md) (per category, geometric rows apart from bookkeeping rows) and the [r7 gate and BX map](cad/gs8-d2-v1/candidate-vertical/GATES-VERTICAL.md).
