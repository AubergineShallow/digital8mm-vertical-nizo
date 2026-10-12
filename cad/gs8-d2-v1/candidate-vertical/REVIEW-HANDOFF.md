# D2 corrective package: independent review handoff

The user requested this saved package for independent Claude review and will handle any later push. Publication work is stopped. No message is being sent to Claude. The local branch is `review/vn-corrective-local-20261012`; the preserved published starting checkpoint is `review/vn-fixes-20261012` at `bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f`.

**This is a blocked review candidate. No fabrication, printing, energizing, complete-service or physical qualification release is granted.** Applicable r7 physical gates, candidate G-V-* gates and M1 remain open. Read [REVIEW.md](REVIEW.md), [assembly STOPs](ASSEMBLY-VERTICAL.md), [measurement plan](MEASUREMENTS-TO-CLOSE.md) and [publication status](PUBLISHING.md).

## Selected evidence

| Variant | Manifest prefix | Full main audit: pass/fail/info | Full check-scope |
|---|---|---:|---:|
| Compact Kowa | `294220bc` | 633 / 1 / 32 | 36 / 0 / 14 |
| Compact Fujinon | `e3a652e7` | 628 / 1 / 32 | 36 / 0 / 14 |
| Original-storage Kowa | `0b467d10` | 636 / 1 / 32 | 36 / 0 / 14 |

Exact identities and raw checks are in each `out/<variant>/manifest.json`, `verification.json`, `print-checks.json` and `check-scope-checks.json`. All three main audits retain the Pi/cooler source/proxy overlap of 79.902671 mm³ as a failure. Geometry-print and mesh screens pass. [Assembly bounds](out/comparison/assembled-comparison.json) and core-void intervals are proxy-model measurements, not weighed or measured product volumes.

The selected [harness report](out/compact-kowa_lm6hc/harness-checks.json) is 30 pass / 12 fail / 20 info. QT routing improved within the existing parts, but power-button, fan-root, camera/OLED flex, pigtail length/retention/service/drop and J2 stow/source gaps remain. Alternative variants have no solved harness/service routes. Rigid `camera_in` and `carrier_in` omit the complete linked 200 mm CSI ribbon; their passes do not prove flexible assembly. Seat the Pi CSI end before its cooler and support both modules for camera-end mating; the full flexible motion remains unproved.

## Review priorities and limits

1. **Bonded catch margin.** Each full main audit has 130/130 passing bonded-stub checks within the 189-row roll-catch category. The minimum reported tilted window is 0.106 mm against 0.100 mm, only about 0.006 mm nominal headroom. Check the unchanged tilt/BFAR cases and the production geometry; do not treat this as tolerance-robust manufacturing or adhesive/torque qualification. Earlier isolated catch probes are not the final evidence.
2. **Concealed ventilation.** Trial4 has a supported stepped front mouth. The saved geometric capacity screens give hot 509.999996/510 mm², cold 420/420 mm² and hot branch-series 575.2/510 mm² under the unchanged 0.002 mm² tolerance. The front minimum sampled neck is 274.2 mm²; if the hot underside is blocked, the 591.0 mm² parallel-mouth sum cannot be credited. Fan operating point, pressure loss, cleanout and closed-body thermal performance remain unknown.
3. **Original-storage reference mismatch.** Its [plenum report](out/original-kowa_lm6hc/shadow-plenum-checks.json) is 48/1/21, while both compact reports are 49/0/21. The failed original cavity-difference row compares a 185 mm tub with the 158 mm compact pre-plenum export18 reference and reports 8893.785 mm³ undeclared difference. This is a mismatched-reference diagnostic, not proof of an assembly collision. No variant-matched pre-plenum original tub was established; 9ced753 original already has trial1 plenums and bdfd44fc has trial3. The failed row stays visible and unwaived. No further CAD repair is included in this handoff.
4. **Structural/material scope.** The [three-page structural PDF](structural-review/output/pdf/D2-shadow-plenum-structural-supplement.pdf), [editable calculation](structural-review/CONCEALED-VENT-STRUCTURAL.md) and [QA receipt](structural-review/output/pdf/structural-supplement-pdf-receipt.json) bind the selected inputs. The proposed equal-share J4 screens are 0.95 N m compact and 1.00 N m all variants; 70% sharing is separate and unqualified. Polymaker 1.13 versus inherited 1.07 g/cm³ means +5.6% of the ASA contribution at fixed volume, not camera mass or a silently adopted grade. Material allowables, exact epoxy/cure and actual ribbon minimum bend radii remain unknown. See [research applicability](corrective-2026-10-12/RESEARCH-INTEGRATION.md).
5. **Production and coupon counts.** Compact has 10 physical production prints across 9 assembly rows; original has 11 across 10. The tub body and catch stub print separately. The gauge, [three plenum crops](vent-study/shadow-plenum-coupon/README.md), [nine retained structural pieces](structural-review/coupons/README.md) and [new two-piece local catch study](structural-review/bonded-catch-coupon/README.md) are additional. No coupon has been sliced, printed, bonded or mechanically tested. The cropped catch study preserves both print orientations but cannot qualify whole-tub 0.5 N m torque.

## Unselected studies

- [Power-options assessment](corrective-2026-10-12/power-options/README.md) and [factory-lead study](corrective-2026-10-12/power-options/FACTORY-LEAD-STUDY.md): exploratory 14 AWG/termination/routing proposals. The selected 270 mm 16 AWG upper case is 0.16254 V against 0.150 V. Its electrical length ceiling is about 225.43 mm, while the current positive route family needs about 279.82 mm with the unchanged allowance. The isolated factory-lead remedy remains blocked by loaded-neck and clearance failures. No wire/BOM substitution or complete passing power loom is selected.
- [J2 exact-parts proposal](corrective-2026-10-12/j2-parts-proposal/README.md): the proposed Molex pair is 24.77 mm mated, so the legacy 20 mm proxy is not an upper bound. Manufacturer free-wire guidance is 12.7 mm per housing before bend/tie/twist; actual latch/finger/mating accommodation remains unproved. The source-backed proposal does not change selected geometry or authorize procurement.

## Reproduce and report findings

Use [REPRODUCE.md](REPRODUCE.md) and the pinned Python 3.12.14 / CadQuery 2.6.1 environment; the candidate overlay pins pypdf 6.1.1. Inspect existing report/source hashes before rebuilding. Keep geometry fixed during checks and use the standard serial CAD wrapper. The actual corrective run additionally used a guarded separate output/lock lane for alternative rigid audits; its execution receipt does not weaken the standard reproduction procedure.

Follow the documented dependency order: export variants, saved plenum/context checks, local catch study, plenum crops, structural write/check, full scope/main evidence, then final documents. A new source hash requires the affected reports and artifacts to be rebound. Do not regenerate baseline numbers just to clear a failure.

The inherited batch runner can exit zero despite failed child checks. Inspect its child receipt, the corrective aggregate status and `current-review-evidence.json`; distinguish source/export identity, report freshness, acceptance failures and physical gates. `reconcile_review_evidence.py --record-blocked` can write the current blocked receipt while intentionally returning nonzero. `--check` still reports acceptance failures. Current coverage and document audit are generated separately.

For each finding, identify the exact file/report row and manifest, show a reproducible witness, state whether it is a geometry defect, proxy/source uncertainty, evidence mismatch or physical qualification gap, and preserve existing failed diagnostics. Proposed changes should name their affected evidence chain and whether they alter selected hardware, dimensions or numeric requirements. The user will decide what to implement or publish after the independent review.
