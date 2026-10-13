# Reproduction and evidence boundaries

## Base and isolation

Repository: `AubergineShallow/digital8mm-vertical-nizo`.
Delivered 2026-10-12 as a patch for the local branch `review/waveshare-imx296-a-20261012`
against published commit `f9704ac03de8938dfafdb52e22e63d098287c3c6`. That patch also carried
an official-camera source overlay (its root `OFFICIAL-SOURCE-SNAPSHOT.json`, local commit
`80a8059`, overlay archive SHA-256
`c3570d9bed7e959af19485e8009a39cdc52a64ef03bfc627241ac4a60a793d48`). Commit `80a8059` is in
no published history and cannot be verified.

On 2026-10-13 the study was rebuilt as a **Waveshare-only delta on `a0bfed9`** (review R-20):
the overlay and its 81 official-camera files are not carried, so every official-camera file
on this branch is exactly `a0bfed9`'s. See [the fix-pass record](review/FIX-PASS-2026-10-13.md).

Generated official-camera exports/reports were intentionally excluded from that
overlay. Any inherited `candidate-vertical/out` content is historical, not current
Waveshare evidence. The variant does not overwrite the official working checkout,
its branch or its ongoing CAD/audit outputs. The study stays BLOCKED and is not applied to
the official design; publishing its branch does not adopt it.

## Fast host checks

From repository root, without CadQuery:

```sh
python -m unittest discover -s variants/waveshare-imx296-a/tests -v
python variants/waveshare-imx296-a/review_status.py
```

The second command writes `review/status.json` and returns **2 intentionally**.
This is the expected fail-closed release outcome, not a failed host unit test.
The vendor drawing is not in the repository (R-03). The tests pass without it and hold
WS-09 stays open; to verify a local copy, place it at `evidence/local/vendor-drawing.jpg`
(git-ignored) or set `GS8_WAVESHARE_DRAWING` to its path before running them.
Changing booleans in the profile cannot bypass the missing-evidence gate; a future
measured/approved integration needs a reviewed source revision and new tests.

Software, from `software/gs8-camera-evf`:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Delivered 2026-10-12 results in `review/software-tests.txt` (not rerun into that file;
the 2026-10-13 rerun is in the fix-pass record): 263 tests run, 255 passed and 8 skipped;
7 are new Waveshare profile tests, 256 are existing tests (248 passed, 8 skipped).
The skipped cases need the separate post planner, absent from this checkout.
These tests use host fakes, not a camera, GPIO, HDMI, CSI, real DNG or real FPS.

## Bounded CAD study

Use the candidate's locked CadQuery environment. All active D2 CAD in the shared
cloud workspace must use the **same absolute lock wrapper in the official checkout**,
not the clone's independent `.cad.lock`:

```sh
/path/to/official/.venv-cad/bin/python \
  /path/to/official/cad/gs8-d2-v1/run_locked.py --max-wait-min 720 -- \
  /path/to/waveshare/variants/waveshare-imx296-a/cad/export_study.py
```

On another isolated machine with no concurrent D2 CAD, use that environment's
normal `run_locked.py` path. The exporter requires a new empty output directory;
`--out /new/path` avoids mixing old or partial artifacts. It writes six individual
STEP proxies/studies, a separate unanchored study assembly and a receipt. It checks
solid validity and STEP read-back volume. **It does not run D2 assembly collision,
FPC bend/slack, printability, structural or physical tests.** No production STL is
exported. The receipt states omitted geometry, source hashes and blocked release.
The exporter needs the local vendor drawing with the pinned SHA-256 and writes STEP
headers with the repository's fixed FILE_NAME stamp. The delivered seven STEP files
were header-normalised on 2026-10-13 without re-export; old and new hashes are in the
receipt's `post_export_update_2026_10_13` block.

## Runtime and gate preservation

`review/baseline-constraints.json` pins the unchanged baseline CAD layout/model,
QT harness rules and runtime sources (all 23 hashes equal `a0bfed9`'s, checked
2026-10-13). `verify_baseline.py` checks that they were
not modified to make the new profile pass. Existing full CAD checkers are retained,
not replaced by this lightweight profile suite. They apply only after generating
the correct integrated assembly; the variant does not claim an old checker pass
for the new camera. Keep original geometric tolerances and all physical gates.

No sensor-plane measurement, mount datum, approved new hardware, real camera
capture, thermal run or successful physical assembly is included in this package.
