# Shadow-plenum open-edge inspection tests

**UNQUALIFIED TEST GEOMETRY. No fabrication or physical release is granted.**

These two inspection coupons are cropped from the selected saved tub. They are
separate from the nine production prints and the earlier structural coupon set.
No supports or reinforcement have been added to make a crop work. The production
enclosure geometry is unchanged.

| Test | Source crop, mm | Bed dimensions, mm | Files |
|---|---|---|---|
| Preliminary regular grid | X −152..−104, Y −35.6..−25.5, Z 8..40 | 48 × 32 × 10.1 | `plenum-bridge-open-edge-coupon.step`, `.stl`; `receipt.json` |
| Ports, service opening and edge regions | X −110..0, Y −35.6..−25.5, Z 0..100 | 110 × 100 × 10.1 | `plenum-port-service-open-edge-coupon.step`, `.stl`; `port-service-receipt.json` |

The STL files already have the original **−Y face on the bed**. The STEP files
retain assembly coordinates. `coupon-index.json` and the individual receipts bind
the files to the source manifest and record the one-solid and STEP-reimport checks.

The larger crop retains the inlet and hot ports, CSI sleeve, post-avoidance regions,
front mouth, lower support row, and top/front frame regions. It includes spans
that are larger or less directly supported than the nominal 8 mm post grid. It is
not a proof that every full-body unsupported span has been captured.

Review the actual first roof layers and bridge directions in the slicer. Discrete
post tops do not guarantee two-ended support for every extrusion line. In the
front-mouth band, the mouth removes the frame beneath the first roof layer; do not
treat that region as an ordinary grid bridge. Automatic support trapped inside
the full plenum is unacceptable.

Both tests have cut-open edges. Those edges provide access and inspection that
the complete enclosure does not. Even a successful coupon cannot establish
closed-body debris removal, channel cleanliness, hand/garment occlusion, assembly
fit, strength, airflow, pressure loss, or cooling. Those physical gates remain open.

Reproduce through the existing CAD lock:

```text
.venv-cad/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/make_shadow_plenum_coupon.py
```

The exporter requires a matching successful `shadow-plenum-checks.json` and stops
if either crop is invalid or disconnected. It does not invent replacement supports.
