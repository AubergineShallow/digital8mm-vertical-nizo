# Bounded QT route study: two rejected families

Neither candidate provides an acceptable replacement. Keep the selected route and its QT length failure: **238.99 + 25 > 240 mm**. This study changes no production route, branch, purchased lead, radius, allowance or accepted failure.

[study.json](study.json) preserves the completed probe's numerical stdout, exact knots, endpoint and radius constraints, input SHA-256 values and limitations. The input hashes were captured when saving the completed result, before evidence regeneration; the selected manifest was still `294220bc7e1babc507e00d41542d108bfbf172250e45f20ba828e83437634ae4`. Saving this record did not rerun the probe or optimize either family.

Both families retain the source root `(-45.445, -23.4, 37)`, destination `(-72, 14.8, 77)`, initial +Z and final +X directions, R6.4 centreline, OD3.2 envelope, 3/4 mm terminal straights and the unchanged 43.071861818216426 mm longest branch. The permitted family minimum including that branch is **215 mm**, retaining the 25 mm allowance against 240 mm minimum stock.

| Candidate | Checked result | Rejection |
|---|---|---|
| Fixed upper crossing Z75; lower return Y−19.7; low bound 27.5..55.2 | Long bound 263.063886 mm; no HDMI/FPS keepout hit | Negative-pigtail separation 2.20 mm versus 3.20 mm required at the long bound. Short bound invalid: leg 4 has 13.324 mm versus 14.912 mm required by R6.4 bends. Stock members were not subsequently tested. |
| +Y crossing Z80; upper crossing Z90.5; low bound 44..67.2 | Minimum 223.853696 mm; modeled 240/250/260 mm members fit the length range; no HDMI/FPS keepout hit | Minimum exceeds 215 mm by 8.853696 mm. Both bounds and all three stock members overlap the positive pigtail: 1.06 mm versus 3.20 mm required. |

The probe keeps the generated installed/premate/unplugged HDMI cells, FPS pair keepout and modeled neighboring cable paths, including the FPC round reserve. It checks those keepout boxes and cable separation. It does **not** establish exact printed-solid, Pi or cooler clearance; no such pass is claimed. Continuous deformation, self-clearance, guides and hardware qualification remain outside scope. Failure of these two families is not proof that every possible route is infeasible.

To reproduce the numerical measurements, first compare the recorded input hashes, then run from the repository root through the shared CAD lock:

```sh
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/review-2026-10-12-followup/qt-route-study/probe_qt_families.py
```

Its JSON stdout corresponds to `study.json` → `measurements`. The saved source differs from the executed source only by its license and explanatory header; both source hashes are recorded. Later source or manifest changes require a new, separately identified study rather than rebinding this historical result.
