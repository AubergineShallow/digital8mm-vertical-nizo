# Review fixes: status

**This is a REVIEW BRANCH: `review/vn-fixes-20261012` (local name `review/vn-fixes-20261010`; commits 44f8131, 4f9e029 and the status commit on top). It is not `main` and not a release. Nothing on it has been printed, powered or measured.**
`main` is unchanged (9ced753). The earlier branch `review/vn-fixes-intermediate-20261011` (4d160f7) is the INTERMEDIATE snapshot of 2026-10-11 and is superseded by this branch. Merging into `main` is the user's decision (15).

## What happened

This branch reviews the vertical-Pi D2 candidate (9ced753, built on r7 d38468e) and fixes what the review found.

The 2026-10-10 review registered 84 issues: 0 blockers, 30 major, 47 minor, 7 info. The candidate's own numbers reproduced, but four things were wrong:
- Windows reproducibility was broken.
- Most r7 rule checks were never ported.
- The written build order was wrong in places.
- Several printed parts failed r7's print rules.

The fixes are in phase 1 (44f8131) and phase 2 with a verified fix-up (4f9e029).

## Result (computed geometry only)

| Status | Entries |
|---|---|
| closed in the repo, each with a check or test as proof | 48 |
| check ported, still failing | 7: VN-24, 26, 27, 28, 37, 47, 62 |
| open, repository work left | 2: VN-04 guide part, VN-21 (9 r7 categories) |
| needs a user decision | 9 |
| needs hardware or a bench test | 18 |

- **Main audit** (pass / fail / info): compact-Kowa 620 / 14 / 32, compact-Fujinon 615 / 14 / 32, original-Kowa 623 / 14 / 32. The failing rows are the inherited pi5/cooler overlap (79.902671 mm3) and 13 roll-catch rows for the bonded tab-catch stub (worst gap 0.055 mm, rule 0.10 mm).
- **Print:** every print check passes on all three variants.
- **Check scope:** fails only on the two hot plenum area rows (user decision 17).
- **Harness:** 27 / 15 / 20.
- **Evidence tools:** the reconciler fails 10 gates and the docs audit fails 11. The reasons are the rows above, plus the guide, renders and structural PDF still waiting for a rebuild.
- **Tests** (fresh clone, 2026-10-12): 32 of 36 candidate test files pass; the 4 red files map to the open items above. The r7 suite passes.
- **Nothing was relaxed.** The accepted print and harness failure sets are both empty.

## Read next

- [FINAL-STATUS.md](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/FINAL-STATUS.md): every VN entry with its proof, the final numbers, the open items, the user decisions and the bench order.
- [ISSUE-REGISTER.md](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/ISSUE-REGISTER.md): VN-01..VN-84 as found, and user decisions 1-17.
- [FIX-LOG.md](cad/gs8-d2-v1/candidate-vertical/review-2026-10-10/FIX-LOG.md): every fix lane, in order; later lines win.
