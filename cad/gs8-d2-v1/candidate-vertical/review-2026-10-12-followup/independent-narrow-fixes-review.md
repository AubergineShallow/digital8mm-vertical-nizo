# Independent narrow-fix review

Approved within scope, subject to the pending UTF-8 correction and terminal-run condition. This is not a final full-suite pass.

Exact reviewed file hashes and proposed patch hash are in `independent-narrow-fixes-review.json`.

- Nominal catch web expectation changes from 3.0 to 2.85 mm after the approved recess; minimum requirement remains 2.4 mm.
- Fixture explicitly copies all three oversized required verification reports and compares copied/source hashes.
- AST assertion verifies the unchanged hot-bottom Z-plane numeric range, eliminating formatting dependence.
- Study STEP export uses the existing equivalent export-plus-normalization wrapper; historical execution records are preserved.
- Historical exclusion index preserves old entries and identifies its current manifest field as latest revalidation, not original move provenance.
- Only the named post-guide execution receipt receives field-level absolute-path classification; command/cwd consistency and recursive key/value checks retain four negative controls.
- Proposed scalar FPS input binding requires the current verifier source hash and exact fixed-input content hash; stale input and unknown producer tests remain.

## Required before completion

- Wait for running full suite to reach terminal before modifying checked sources. Preserve the complete run and its source snapshot.
- Add explicit encoding=utf-8 to the new test_repo_hygiene receipt fixture read; current snapshot contains this known cross-platform test failure.
- Apply the separately reviewed scalar-FPS packager patch after terminal.
- Run hygiene and cross-platform tests against corrected final sources, and packager tests against patched final sources.
- Bind unchanged modules to exact source hashes and distinguish prior full-suite execution from final targeted reruns; do not claim a blanket full final-tree suite pass.

- No repository tests or CAD were executed by this reviewer.
- No geometry or acceptance-threshold changes approved by this receipt.
- This receipt does not replace package, guide, physical qualification or final test evidence.
