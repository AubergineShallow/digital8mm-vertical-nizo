# Signal routing corrective study, 2026-10-12

Scope: compact Kowa, unchanged purchased parts and external envelope. The studies use the pinned CAD interpreter and the unchanged exact capsule implementation from `verify_harness_checks.py`, with every opened STEP checked against the nominated mechanical manifest. They do not certify fabrication or flexible service.

## Confirmed correction

The propped QT lead rises from its unchanged fan-in to Z69 before crossing the Pi. The original route crossed the Pi solid at Z56–65. The strict sweep gives zero exact intersections for the corrected route, and reproduces 7.27 mm³ of Pi overlap when the old knots are restored. The corrected minimum-reach curve uses 147.47 mm plus a 43.07 mm longest branch. At the 240 mm minimum purchased length, the unchanged 24 mm service margin leaves 25.45 mm additional reserve.

`qt-free-lead-check.json` is the scoped result, with manifest and source hashes. Reproduce through `run_locked.py -- candidate-vertical/corrective-study-2026-10-12/check_signal_routes.py`, using paths relative to the repository root as in `REPRODUCE.md`.

The free route is a minimum-reach shape plus a reserved allowance. The entire remaining lead is not laid out in that propped pose, and no continuous full-material deployment or closure path is demonstrated. Four real OD1.6 cores still do not fit the OD3.2 main proxy; actual core packing, the donor splices and sleeves remain measurement/modeling gates.

## Installed QT storage study

The unchanged R5.5 HDMI U-turn conflicts with the previous QT top-run storage for 250 and 260 mm leads. A candidate keeps the QT transverse run above the U-turn at Z90.5, uses a variable lower-return height to store the intact 240–260 mm length, and raises its +Y crossing from Z65 to Z68 so both R6.4 corner trims fit. Source roots, branches, diameters, bend radius and purchased lengths are retained. The separate released minimum retains the previously checked top56/low38/cross65 geometry for the unchanged route allowance. Static poses do not demonstrate a safe continuous motion between them.

The exploratory exact sweep and J2 housing-home screen are reproduced by `study_stored_qt_j2.py`; its output is `stored-qt-j2-study.json`. All three 240/250/260 mm QT stored shapes have zero exact saved-part hits and zero cable-envelope overlaps on the bound baseline. The candidate is selected in `signal_routes.py`; `harness_rules.py` now uses a separate released minimum for reach and applies strict installed-target sweeps to that minimum. The stored family’s 44–55.2 mm lower-return bounds preserve 238.99–261.39 mm total nominal range. The old QT/HDMI conflict remains a negative-control fixture in `tests/test_fxh_harness.py`. Integrated-export verification is still required after other geometry changes.

## J2 identity and placement hold

V-28 identifies a Micro-Fit 3.0 class, not an exact purchased SKU. The 7.5 × 11 × 20 mm legacy estimated housing box (1,650 mm³) is clear of saved parts at X[-25.25,-17.75], Y[-19.5,-8.5], Z[15,35]. A larger gross box X[-33,-9], Y[-24,-7], Z[15,39.5] is also statically clear of saved parts and would provide 1,999.2 mm³ at the unchanged 20% fill factor. Neither candidate was selected as a real housing placement or a new reserve.

The old capacity calculation charged only one of two OD1.6 cores and used an unverified 150 mm finished allocation. `routes.py` now charges both cores and reports:

- Legacy 150 mm allocation: 294.54 mm³ loop + 1,650 mm³ legacy estimated pair = 1,944.54 mm³
- Inherited 387 mm combined-half comparison: 1,247.58 + 1,650 = 2,897.58 mm³
- Current selected stock minimum (two >=231 mm halves per circuit): 1,549.17 + 1,650 = at least 3,199.17 mm³

The selected part has no finite maximum length or maximum insulation diameter yet. These volume cases even credit the entire hypothetical 76.75 mm route spine as flexible-wire consumption; the rigid connector and exposed-wire roots are not placed, so the quantities are optimistic lower bounds. The larger candidate box therefore does not justify a pass. The original 777.6 mm³-capacity reserve and failed row remain selected, with the two-core accounting corrected.

The BOM permits trimming the purchased leads; intact stock need not all be stored. A defensible finished cut requires corrected Pi and switch roots, actual housing/terminal part numbers, wire exits and solder allowances, installed stow and service reach. The legacy 150 mm allocation is not that cut plan. Latch travel, finger/tool access, insertion/withdrawal stroke and full-material service deformation remain open. No smaller connector, shorter bought wire, bend-radius relaxation or fill-factor relaxation was used.

The later exact-parts proposal identifies a 24.77 mm mated Molex pair and recommended 12.7 mm unbiased lead exits. The earlier 20 mm estimate is not an upper bound. See ../corrective-2026-10-12/j2-parts-proposal/README.md; no exact SKU or new routing is selected.
