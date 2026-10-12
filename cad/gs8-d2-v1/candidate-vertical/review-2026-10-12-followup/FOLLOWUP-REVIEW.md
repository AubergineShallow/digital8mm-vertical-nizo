# Followup to the 12 October corrective review

This is a new delivery-side followup record on local branch `review/vn-catch-qt-cloud-20261012`, starting at reviewed commit `f9704ac03de8938dfafdb52e22e63d098287c3c6`. The original [corrective review](../review-2026-10-12-corrective/CORRECTIVE-REVIEW.md) and [register](../review-2026-10-12-corrective/CORRECTIVE-REGISTER.md) retain their findings unchanged. This record does not attribute later changes or conclusions to the independent reviewers.

**Local evidence refresh complete; release remains blocked.** Final numerical reports, generated assembly/BOM/wiring and coverage checks, guide/structural artifact review and documentation audit are complete. Final regression coverage records passing results for 45 modules / 624 cases (including one skip and one expected failure): 41 unchanged module results from the terminal full run plus four reruns against the final sources. This is not a single complete-suite run against the final tree; both failed full runs are preserved below. Existing downstream evidence must not be represented as current merely because its source now contains a fix. No push or merge is authorized. No physical build, printing, energization or complete-service qualification is claimed. All 56 inherited physical gates, applicable candidate G-V-* gates and collar M1 remain open.

## Scope and preserved requirements

The followup addresses check integrity and internal catch geometry, plus local evidence regeneration and factual documentation. It preserves the external dimensions, purchased selections, baseline BOM mapping and engineering acceptance thresholds. The QT length gate retains the installed-family minimum plus longest branch and 25 mm allowance against 240 mm minimum stock. A failed length result must still carry its independently evaluated collision sweep; a released pose stays informational. Catch criteria remain 0.30 mm centred / 0.10 mm worst-offset windows and the existing first-contact rules. Full-clearance tilt, yaw and bounded coupled poses are to be evaluated without relaxing them.

The user confirmed the **official Raspberry Pi Active Cooler**, which is already the selected BOM part; there is no substitution or geometry change from that confirmation. The retained 79.902671 mm³ witness is a conflict between the detailed official Pi STEP and the approximate cooler perimeter/underside/push-pin proxy and its registration. It does not prove the official cooler is incompatible. Actual enclosure airflow, fan-lead and service clearances, fit and thermal qualification remain open.

The catch trial changes only an internal lower catch face and a host-side adhesive escape groove; the tenon remains unchanged. Its exact selected dimensions and outcomes must be taken from the final source-bound export and checks, not from a superseded trial file. Actual seating depth, adhesive dosing, fixture/cure, printed tolerances, warm creep and whole-tub torque remain physical holds.

The chosen 0.1 mm axial-underseat screen is an axial reference bound, not a maximum joint-face opening. In the final compact-Kowa `stub_feasibility` rows, feasible transformed poses reach approximately 0.23995 mm at the sampled joint-face points because of tilt. This is not a qualified bondline thickness or manufacturing tolerance. The [process plan](BOND-PROCESS.md) requires measured seating, face positions and uncertainty; the adhesive/process envelope remains unqualified.

## QT remedy remains open

The selected production route is unchanged. Its installed-family minimum, including the longest branch, is approximately 238.99 mm; with the unchanged 25 mm allowance it requires approximately 263.99 mm against 240 mm minimum stock. Restoring the independent collision sweep on this failing row corrects the checker; it does not resolve the length failure or qualify a flexible transition.

The [bounded two-family study](qt-route-study/README.md) rejected both alternatives while retaining the source/destination roots, R6.4, OD3.2, longest branch and stock/allowance constraints:

- The fixed upper crossing/lateral return family has an invalid short bound (13.324 mm leg versus 14.912 mm required by the bends) and a 2.20 mm negative-pigtail separation at the long bound versus 3.20 mm required. Its stock members were not subsequently screened.
- The raised crossing family has a 223.853696 mm minimum including the branch, exceeding the permitted 215 mm by 8.853696 mm, and 1.06 mm positive-pigtail separation versus 3.20 mm required across both bounds and the 240/250/260 mm members.

Those screens preserve the generated HDMI/FPS keepouts and modeled cable neighbors, but do not establish exact printed-solid, Pi or cooler clearance, self-clearance or continuous deformation. Their recorded inputs belong to the pre-refresh `294220bc` manifest; they are separately identified research, not rebound final acceptance evidence. Failure of two candidate families is not a proof that every route is infeasible. No purchased lead, selected route, bend radius, allowance or accepted failure was changed.

## Documentation and BOM corrections

| Original finding | Followup implementation | Remaining evidence or decision |
|---|---|---|
| CHE-9 / CR-20 | `make_bom_vertical.py` derives the print hold from the selected manifest's `ventilation.support` aperture arrays and support dimensions. Trial4 has open heights 15.4, 26.8 and 8.4 mm, with the outer aperture at Z49.6..58. The obsolete Z5..40 / approximately 35 mm bridge assertion is removed. Aperture height is not treated as a qualified bridge span. | The final manifest-derived BOM is regenerated and checked; the source-bound guide is rebuilt and visually reviewed. Actual slicer direction, bridge quality, beam/pillar bonds and cleanout remain unqualified. |
| ELE-6 / CR-26 | V-28 distinguishes its retained conditional 28–24 AWG / two-colour class from the unselected exact-parts proposal. The proposed contacts support 20–24 AWG and maximum insulation OD 1.85 mm. Path A is 24 AWG with one colour per half; path B is 22 AWG, all black. The note applies to V-28S as well. | Decision 13 still governs exact parts, gauge, OD, circuit marking, roots, latch, placement, storage and finished cuts. Neither path is adopted. |
| ELE-7 / CR-27 | `I-tub-stub` names `tab_catch_insert` as one physical printed constituent included in `P-tub`, purchase quantity zero. It exposes the existing second tub print without adding an assembly row, production piece or purchase. Separate insert material is explicitly unresolved because the manifest does not specify it. | Print/bond qualification and exact material remain open. Production counts stay compact 9 CAD rows / 10 prints and original storage 10 / 11. |
| CHE-7 | The superseded `guide/README.md` keeps its own SUPERSEDED / STALE warning and links to the selected guide instructions. A dedicated `StaleGuideBanner` regression covers that warning separately from the selected guide receipt. | The selected concealed-vent banner continues to follow its own source receipt; rebuilding it cannot make the older guide current. |
| REP-1 / CR-06 | `REPRODUCE.md` explicitly nominates Linux x86_64 as the selected reference and distinguishes Windows geometry comparison from byte-bound Linux cache reconstruction. | STEP formatting, STL/mesh triangulation and vertex/face ordering can differ across platforms. Exact cache mismatches remain failures. No full cross-platform byte-identity claim is made. |

The unchanged selection fields are variant, installed quantity/unit, purchase quantity/unit, included parent, SKU/class and supplier for every pre-existing row. Item, note and status edits are editorial. The new included row must be excluded from purchasing and from a second count of its parent assembly. The generated buy view must remain unchanged from the starting checkpoint.

## Final scoped reports and harness

All three variants have current full scope, print, mesh, exterior-mouth, envelope and core-void reports. Full check-scope is 36/0/14 for each. Geometric print totals are 168/0/7 for each compact variant and 172/0/7 for original storage. The two compact plenum reports are 49/0/21. Original storage remains 48/1/21: its 8893.7845 mm³ undeclared-cavity diagnostic compares the extended 185 mm body with a 158 mm compact historical tub. That unsupported reference does not independently establish physical interference. No variant-matched baseline, waiver or geometry repair is selected. The [fresh wall context probe](current-wall-probe-context.json) has four passing rows, including the deliberately empty CSI ray and three adjacent 2.5 mm wall samples; it is not a global minimum-wall proof. The selected-folder historical wall-probe file is preserved byte-for-byte, documented by [its preservation receipt](wall-probe-history-preservation.json).

The final [harness refresh](harness-refresh.json), completed at 18:07:57 UTC, binds report SHA-256 `38ae8d78c1f4eda3d24610fc03cfb8f0f2472f019e8bd892a3c567926d3e9885` with **29 pass / 13 fail / 20 info**. Its process exits 1 and the failures remain visible. The preceding primary-batch harness result and its execution receipt are preserved separately because they predate full installed-scene coverage for the minimum member.

The exact failed rows are:

- `cable_routes`: `fan`, `fpc`, `oled_flex`, `pigtail_negative`, `pigtail_positive`, `power_button`, `qt`
- `cable_stow`: `power_button_j2_pair`
- `lead_access`: `pigtail_drop`, `pigtail_ties_on_route`, `pigtail_xt30_mouth`
- `mate_reach`: `j2_btn`, `xt30_pack`

The QT minimum member now sets `installed_targets=true`, tests 6934 targets at the unchanged 0.01 mm³ hit threshold, and reports empty `hits` and `cable_overlaps`. Its independently calculated length slack remains −23.99 mm, so the row fails. The released static pose is separately swept and informational only; it cannot substitute for the installed-family length rule or prove continuous deformation. No alternative variant inherits this selected compact-Kowa harness result.

## Reporting and numerical comparison

`run_shadow_checks.py` now returns a nonzero process status when any child check fails, while retaining all per-child results. The aggregate wrapper already rejected such failures; the standalone runner no longer masks them behind exit zero. Historical execution receipts remain unchanged.

The structural JSON serialization canonicalizes values with absolute magnitude below 1e-12 to zero, addressing REP-2's platform-dependent near-zero coordinate without rounding other useful nonzero values or changing engineering tolerances. Structural wording distinguishes the 10 mm nominal tenon height from certified bonded engagement, records the recess/vent and sampled-pose limits, and does not credit an unqualified dry joint plane as adhesive load-bearing area. Final structural evidence and physical joint qualification remain separate requirements.

## Verification and selected evidence

The serial [export receipt](export-run.json) records successful exports with these exact identities:

| Variant | Manifest SHA-256 |
|---|---|
| Compact Kowa | `d2b93a43ed74e2a0c777c10d5d0907d99af5e8623699dfa919a814e0f6efa754` |
| Compact Fujinon | `e61d3064a471ed3e2d1ea665a4fbbe2e34b89ddfaec242a8eed4f6e8cd8db93c` |
| Original-storage Kowa | `902aa8658965acd513d3166fcba91f723f86a7a35fd4b561430be2a2fea0fd9c` |

The three full main audits are now complete. Each report's manifest, verifier and assembly-state hashes match the corresponding current inputs:

| Variant | Main audit pass / fail / info | Roll-catch pass / fail / info |
|---|---|---|
| [Compact Kowa](../out/compact-kowa_lm6hc/verification.json) | 1874 / 1 / 32 | 1429 / 0 / 1 |
| [Compact Fujinon](../out/compact-fujinon_hf6xa/verification.json) | 1869 / 1 / 32 | 1429 / 0 / 1 |
| [Original-storage Kowa](../out/original-kowa_lm6hc/verification.json) | 1877 / 1 / 32 | 1429 / 0 / 1 |

Each main failure is `interference/pi5/cooler`, with the proxy/registration limitation described above. Each catch audit assesses 69 hypotheses / 49 feasible nominal-host poses. At thirteen BFAR positions per feasible pose, all 637 feasible windows and 637 first-contact rows pass; minima are 0.129 mm worst-offset and 0.400 mm centred against unchanged 0.100/0.300 mm criteria. Another thirteen window and thirteen first-contact rows preserve one explicitly non-feasible legacy diagnostic. Category totals include these diagnostics, feasibility/coverage and baseline rows and must not be described as functional pose counts alone. These are finite numerical samples, not tolerance, adhesive, printed-joint or full-body torque qualification.

Separately executed companion catch checks also pass for [compact Kowa](../review-2026-10-12-corrective/catch-extended/catch-acceptance-compact-kowa_lm6hc.json), [compact Fujinon](../review-2026-10-12-corrective/catch-extended/catch-acceptance-compact-fujinon_hf6xa.json) and [original-storage Kowa](../review-2026-10-12-corrective/catch-extended/catch-acceptance-original-kowa_lm6hc.json). Each compares 1370 catch/feasibility/coverage rows with its full main audit, with exact row matches, no missing/mismatched rows and no freshness errors. Inputs and sources remained stable during each run. This is repeatability of the shared numerical checks, not an independent physical or alternative-model validation.

The [prelude receipt](validation-run-prelude.json) records exit zero for selected plenum, exterior-mouth context, three plenum crops, the two-piece bonded-catch coupon, structural update and structural `--check`. These are bounded preparatory results; the full main/first-contact audits, final report chain and artifact review remain separate requirements. Export success alone does not establish any variant's harness or service qualification.

Completed before final export, through `run_locked.py`:

- CAD-free BOM schema/selection comparison: all 135 rows in the starting `f9704ac` BOM remain, with no changes in any preserved selection field. The new `I-tub-stub` included row brings the explicit-row count to 136. All 70 unchanged upstream generator source rows remain mapped. CAD was not imported. No generated BOM file was overwritten during this check.
- The manifest-derived print hold reports Z5..20.4, Z21.6..48.4 and Z49.6..58, with heights 15.4, 26.8 and 8.4 mm. It contains neither the stale Z5..40 assertion nor the approximately 35 mm bridge claim.
- `tests/test_build_order_docs.py StaleGuideBanner`: 2 tests passed, including the new superseded-guide regression. This is a focused test result, not the complete candidate suite.
- `tests/test_corrective_aggregate.py`: the main followup session reports 6 passing regressions, including execution of the standalone batch runner with mocked child commands in isolated temporary output for both all-pass and failing-child cases. Final source-bound suite evidence will supersede this preliminary report.
- Whitespace check of the edited documentation, BOM generator and banner test: passed.

After the three-export batch, the locked preparation refresh regenerated ASSEMBLY (the B1 block), BOM and WIRING; all three generator `--check` commands passed. A direct comparison of the generated CSV against `f9704ac` again found all 135 previous rows preserved with zero selection-field changes and the single included `I-tub-stub` addition. `BUY-VERTICAL.csv` is byte-identical to the starting checkpoint (SHA-256 `1827971204cc4d9f2e4e05c97a9bc7d5e16be5a07f7de04380bba7a5906c04b9`). The selected guide's assembly stale marker is governed by its final source-bound rebuild.

After the final strengthened harness completed, ASSEMBLY, BOM and WIRING were regenerated again and each generator freshness check passed. `tests/test_wiring_bom.py` passed all 20 regressions. Coverage `--write` and `--check` passed with no problems or stale outputs after the current product-render receipts and blocked reconciler were refreshed. The [final BOM/documentation comparison](bom-documentation-check.json) confirms all 135 starting selection mappings, the single included row, unchanged buy-view bytes and unchanged original reviewer records.

The reconciler reports verified source/export identities and evidence bindings, with no identity failures; its sole retained reconciliation gate is the failing harness. This does not erase the separately recorded rigid cooler proxy and original-storage plenum failures. All twelve variant product renders were visually reviewed by the main session. Both complete runs and the final targeted reruns are preserved below; their combined source coverage does not change the retained engineering failures or physical holds.

Use [REPRODUCE.md](../REPRODUCE.md) and the shared serial CAD lock. Source/export identity, report freshness, calculated acceptance and physical qualification are separate conclusions. A current blocked receipt retains its failing gates and is not a release.

## Final artifacts and status bindings

The [40-page catch/QT followup guide](../guide/out-concealed-vents/D2-vertical-catch-QT-followup-f9704ac.pdf) has PDF SHA-256 `e3ddbee5bddcda0fa74fcca74715ab9865d79af5b4dce633f7b95f21792b355a`. Its [source receipt](../guide/out-concealed-vents/guide-receipt.json) is `3320c47d680343f8e4acf2abb5938a7aca5a28622ea14aaba31d6f1e896610a0`; the [visual-review record](../guide/out-concealed-vents/visual-review-followup.json) binds all forty inspected pages to that PDF and receipt. The separate [post-guide build-order check](../guide/out-concealed-vents/post-guide-build-order-check.json) passes 24/24 with unchanged bound inputs. The [source/pages ZIP](../guide/out-concealed-vents/D2-vertical-catch-QT-followup-f9704ac-source-and-pages.zip) contains 694 members / 92,427,315 bytes, SHA-256 `2a2861a59d1f956a3609d389ae8b138e44d175ecf6cab4708db579fd45d36f97`. These document checks do not close engineering or physical gates.

The [four-page structural supplement](../structural-review/output/pdf/D2-shadow-plenum-structural-supplement.pdf) has PDF SHA-256 `dcc4e24f9adfa90670d4be00be187bb4b976b3dc1e989d7bb48ea99dd836503e`. Its [receipt](../structural-review/output/pdf/structural-supplement-pdf-receipt.json) records current source bindings, passing text checks and visual review of all four final pages. No FEA, adhesive/process, printed-joint or whole-tub strength qualification follows from this document review.

[CHECKPOINT-STATUS.json](../CHECKPOINT-STATUS.json) was refreshed from actual artifacts at 18:35:45 UTC. It records all three current manifests, the current guide PDF/receipt/QA/post-guide identities, current trial4 and catch/harness holds, and the reviewed `f9704ac` followup base. The upstream and export18 historical references remain intact. Every variant source/export file and guide source/page hash was verified before updating the status. Coverage `--check` and the [documentation audit](../out/review-docs-audit.json) `--write` / `--check` then passed with zero failures, missing links, stale outputs or missing bound caches. Release remains blocked, with all 56 inherited physical gates and M1 open.

## Complete-suite execution history

The [first full-suite receipt](full-suite-first-failed/receipt.json) preserves all 45 executed modules, 617 reported test cases, 40 passing modules and five failing modules, with stable test sources. The failures were in `test_critical_features_cf.py`, `test_deterministic_export.py`, `test_evidence_tooling.py`, `test_fx_fixup.py` and `test_repo_hygiene.py`. Failed logs remain in that directory, alongside [the exact executed-source mapping](full-suite-first-failed/ARCHIVED-SOURCES.json). This failed run is not overwritten by later maintenance or a passing rerun.

After independently reviewed regression maintenance, the [second full run](full-suite/receipt.json) executed 45 modules / 623 cases: 44 modules passed and one failed because newly added test code omitted explicit UTF-8 in a text read. That terminal receipt and its logs remain unchanged. The explicit encoding correction and an independently approved FPS packaging-binding fix were then followed by [four targeted final-source reruns](final-targeted/receipt.json): packager (22 cases), repository hygiene (21), cross-platform I/O (12) and deterministic export (21), all passing.

The [final regression-coverage receipt](final-regression-coverage.json), SHA-256 `9ab25553654c8986b130b255e354c76caeec0263df54bb6e4547fd34a4da31e1`, accounts for **45 modules / 624 cases, including one skip and one expected failure**, using **41 unchanged module results from the terminal full run plus four final-source reruns**. Current dependency hashes and both source run receipt hashes were verified. This is explicitly **not a single final-tree full-suite run**. The first and second failed full runs remain historical evidence; no failed result is relabelled or overwritten. The maintenance does not alter frozen geometry, engineering acceptance thresholds, selected part choices or guide-bound documents. Regression success does not make the camera a passing engineering or physical release.
