# Publication

**Published.** This candidate is public at <https://github.com/AubergineShallow/digital8mm-vertical-nizo>. Its `main` and `redesign/vertical-pi-hidden-vents` branches both point at commit `9ced753` ("Add vertical Pi D2 review with concealed ventilation"), on top of the upstream r7 release `d38468e58eb2b02d56743e2e0cfdd8f780818a65` (as fetched on 2026-10-10). It is an independent repository that keeps the original project's history, not a same-owner GitHub fork.

The original repository is <https://github.com/AubergineShallow/digital8mm>. Do not push this candidate there; the upstream r7 line stays unchanged.

## Review fixes (not published)

The 2026-10-10 review ([issue register](review-2026-10-10/ISSUE-REGISTER.md)) is fixed on the local branch `review/vn-fixes-20261010`: phase 1 is commit `44f8131`, phase 2 is in progress and uncommitted ([fix log](review-2026-10-10/FIX-LOG.md), [phase-1 status](review-2026-10-10/PHASE1-STATUS.md)). Whether and when these fixes are pushed to the public repository is user decision 15 in the register. Before any push: run the FP-16 refresh, confirm `reconcile_review_evidence.py --check` and `review_docs_audit.py --check` exit 0 on a fresh clone and on an emulated `core.autocrlf=true` clone (REPRODUCE.md), and compare the remote commit with the local one after pushing.

## Historical handoff (superseded)

The 9ced753 handoff described a local Git bundle (`D2-vertical-nizo-history.bundle`) and said publication was not complete. That bundle is not part of this repository and is no longer needed: clone the public repository instead.

## What publishing does not mean

Publishing source does not authorize printing, energizing or fabrication release. Keep the review designation visible in the repository description and README. The cooler/source conflict, the plenum roof and mouth print holds, slicer and coupon tests, the complete flexible wiring and service checks, thermal validation, every r7 physical gate that still applies ([gate map](GATES-VERTICAL.md)), the candidate's G-V-* gates and collar M1 remain open.
