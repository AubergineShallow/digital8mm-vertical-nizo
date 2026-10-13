# Cloud follow-up to the independent corrective review

Baseline: `f9704ac03de8938dfafdb52e22e63d098287c3c6`, preserved on the existing review history. Delivered by the delivering agent (`dot`) as commit `a0bfed9` (local branch `review/vn-catch-qt-cloud-20261012`); it is published on the GitHub branch `review/vn-catch-qt-20261013` with the 2026-10-13 review-and-fix commit on top; `main` is untouched.

The evidence was regenerated and bound after this note was first written; the current record is [FOLLOWUP-REVIEW.md](FOLLOWUP-REVIEW.md) and the 2026-10-13 corrections are in [FIX-PASS-2026-10-13.md](FIX-PASS-2026-10-13.md). Physical qualification remains open.

The original installed-family QT minimum plus longest branch and 25 mm allowance against 240 mm minimum stock remains the acceptance rule. A failed length row must still report its independent collision sweep. A released pose remains informational and is not a replacement rule.

The original 0.30 mm centred / 0.10 mm worst-offset catch window and first-contact criteria remain unchanged. Full pocket-clearance tilt, yaw and bounded coupled poses enter main acceptance. Current trial recesses only the internal lower catch face and adds a host-side adhesive escape groove; no purchased part or external-size change is selected. The previous catch-extended report is retained as a baseline failure witness.

Initial standalone tub attempts omitted the normal collar_setup context and failed validity before power passage cuts; they are not evidence about the catch trial. The corrected isolated builder uses the same collar and J4 contexts as model.build. Full final exports, not isolated trial files, will govern the review handoff.

## Notes on records in this folder (fix pass 2026-10-13)

- `independent-*.json` and `independent-*.md` name no reviewer: they are unattributed static audits made within the delivering agent's session, with no tests or CAD run (R-05). `independent-kowa-review.json` cites an earlier Kowa review that is not in the repo; `independent-narrow-fixes-review.json` cites a patch (`5fcf76f9`) and evidence (`5db068d6`) that are not in the repo. Their bytes are kept.
- `bom-documentation-check.json` asserts `original_reviewer_records_unchanged: true` with no producer and no file list; the claim is unsupported (R-02) and has no generator through which it could be corrected, so the file is kept as delivered and must not be cited for that flag.
- `guide-library-verification.json` claims a Library item and an exact byte match for the source-and-pages ZIP; the ZIP was not delivered (it is git-ignored), so that entry is unverifiable (R-19). The file is kept as delivered.
- `full-suite-first-failed/receipt.json` records its 45 log paths under `full-suite/`; the logs were later moved into `full-suite-first-failed/`, where all 45 hashes match (R-11). The receipt is kept as written.
- `catch-firstcontact-probe.json` is identical to `catch-firstcontact-before-vent-fix.json`: a pre-vent-fix diagnostic bound to the rejected trial inputs (R-11; see `rejected-vent-overshoot/README.md`).
- `check_catch_trial.py` now writes to a separate `--out` directory so it cannot overwrite the archived trial files (R-11).
- `export-run.json` and `final-targeted/receipt.json` record no timestamps, runtime, platform or log hashes; the reruns were on Linux (R-30). Archived `.txt`/`.log` evidence and executed copies contain cloud-sandbox absolute paths (a workspace scratch folder and an agent home folder; no personal data); they are generated evidence and are not rewritten (R-09). The JSON-only path guard of VN-10 does not scan them.
