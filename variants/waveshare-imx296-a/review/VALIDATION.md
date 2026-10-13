# Verification summary

2026-10-12. **All results below are host/source/study checks, not hardware qualification.**

This table is the delivered 2026-10-12 summary. The 2026-10-13 fix pass reran the checks on
the Waveshare-only branch on `a0bfed9`; its results, and the STEP hash changes from header
normalisation, are in [FIX-PASS-2026-10-13.md](FIX-PASS-2026-10-13.md).

| Check | Result | Scope |
|---|---|---|
| New mechanical/profile tests | 15 passed | Unknown datums and physical flags stay blocked; camera identity/source and preserved constraints |
| Full software suite | 263 run: 255 passed, 8 skipped | 7 new profile tests passed; 256 existing tests yielded 248 passes and 8 existing missing-post-planner skips |
| Unchanged-source hash guard | Passed | Four baseline CAD/QT source files and all runtime Python modules |
| Individual STEP exports | 6 valid, single-solid read-backs | PCB pattern, nominal/max envelopes, broad connector reserve and unapproved frame |
| Standalone assembly STEP | Valid, 3-solid read-back | Local PCB/housing/frame only; volume matches constituent sum |
| Source/artifact review labelled "independent" by the delivering agent (reviewer not named; unverifiable, R-05) | No unresolved must-fix in bounded study scope after WS-R1 fix | Source, hashes, STEP text, analytic volumes, proposal arithmetic and labelling; no physical test |
| Release gate | BLOCKED, expected exit 2 | No installed D2 assembly or production mesh |
| Full D2 integrated CAD/route/structural checks | Not run for Waveshare | Requires actual mount datum, retention/anchor and cable definition first |
| Physical optics, capture, power, thermal, print and load tests | Not run | All still-applicable original gates plus WS holds remain open |

The independent review found and closed one source validator defect: an unsupported
backfocus-measured flag had not been checked. It did not bypass the physical-release
block. See INDEPENDENT-REVIEW.md for method, hashes and limitations.

The STEP receipt binds all seven files and four source/evidence files (the drawing is now
kept local, R-03). Its validity
and read-back values are produced by the exporter. The independent reviewer checked
those hashes, STEP entities/dimensions and separate analytic volumes without claiming
a second OpenCascade execution. No camera fit or load path is inferred from that.

The focused delivery archive adds a CRC/SHA-256 check and exact Git-tree patch
reconstruction receipt outside the repository; those results do not supersede any
engineering hold. Historical official-camera exports are not in the focused archive.
