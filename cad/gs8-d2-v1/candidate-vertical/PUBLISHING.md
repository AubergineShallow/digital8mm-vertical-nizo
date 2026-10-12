# Publication

The independent, history-preserving repository is [AubergineShallow/digital8mm-vertical-nizo](https://github.com/AubergineShallow/digital8mm-vertical-nizo). The published starting checkpoint for the 12 October corrective review is branch `review/vn-fixes-20261012`, commit `bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f`.

## 12 October corrective branch

The corrective work is published on the review branch `review/vn-corrective-20261012`:

| Order | Commit | Author | Content |
|---|---|---|---|
| Base | `bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f` | main review session | Reviewed checkpoint of the 2026-10-10 review (`review/vn-fixes-20261012`) |
| 1 | `1b593952cd1b864b9d5bf4d879b0688dbaf70d4d` | `dot` (delivering agent) | Delivered corrective commit, published unchanged; the delivery package cites this hash. Its local branch name was `review/vn-corrective-local-20261012` |
| 2 | the commit directly on top of `1b59395` | main review session | Review-and-fix commit: review record and the fixes listed in it |

The review of commit 1 is recorded in [CORRECTIVE-REVIEW.md](review-2026-10-12-corrective/CORRECTIVE-REVIEW.md): what was reproduced, the verified findings, what the fix commit changed and what stays open. `main` is unchanged at `9ced753`. Merging any review branch into `main` is the user's decision 15.

When this branch was pushed, GitHub warned that three `assembly.step` files are larger than its recommended 50 MB file size. They are kept as delivered, because removing them in a later commit would not remove them from the published history. Whether to keep such files in Git, move them to Git LFS or stop tracking them is a user decision (see the review record).

The original [digital8mm repository](https://github.com/AubergineShallow/digital8mm) and its upstream history remain preserved. Do not publish this candidate to that original repository.

## Evidence before publication

Complete the [reproduction and audit workflow](REPRODUCE.md), including current source/export/report identities, visual inspection of every final document page, and a receipt that preserves every failed engineering gate. The explicit reconciler `--record-blocked` mode writes current review evidence while retaining failures and nonzero acceptance status. A clean identity audit and a blocked engineering review can coexist; neither should be described as a fully passing design. Keep computed failures and all physical holds visible when committing or publishing the review.

Before reporting any later publication as done, compare the intended local commit and target branch with the actual remote commit.

## Earlier public checkpoints

The initial independent-repository review was `9ced753` on top of upstream r7 `d38468e58eb2b02d56743e2e0cfdd8f780818a65`. Phase 1 was `44f8131`. The requested intermediate branch `review/vn-fixes-intermediate-20261011` held `4d160f7`, expressly a work-in-progress snapshot whose omitted candidate exports did not match its changed sources. Those statements describe historical checkpoints, not the current corrective evidence.

The earlier local Git-bundle handoff is superseded by the public repository. The 84-issue [review register](review-2026-10-10/ISSUE-REGISTER.md), [phase-1 status](review-2026-10-10/PHASE1-STATUS.md) and [fix log](review-2026-10-10/FIX-LOG.md) retain the development history.

## What publishing does not mean

Publishing source does not authorize printing, energizing or fabrication release. Keep the review designation visible. The cooler/source conflict, unresolved power and flexible wiring/service checks, print and bond qualification, thermal validation, every applicable r7 physical gate ([gate map](GATES-VERTICAL.md)), the candidate G-V-* gates and collar M1 remain open.
