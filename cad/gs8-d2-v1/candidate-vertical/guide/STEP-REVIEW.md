# Assembly step evidence and limitations

All entries are review status, not permission to build. Use only the verification report bound to the same geometry snapshot. No physical gate is closed.

| Step | Evidence reviewed | Explicit missing evidence / stop |
|---|---|---|
| 00 Isolation | Candidate written safety sequence | Whole pack / XT30 extraction with final retention and both leads; closed-body access |
| 01 Printed set | Exported nine compact production meshes and candidate BOM | Slicer, material, supports, tolerances and physical print |
| 01b Purchased set | Exported COTS envelopes plus BOM identities | Real purchased revisions and connector measurements |
| 02 Hardware | Candidate BOM and assembly counts | Revised coupons, actual standoff bottoming, nut/tool fit |
| 03 Optics / inserts | Candidate optical datum and inherited optical process | Measured lens support band, back focus, M1, insert coupons |
| 04 Stack | Carrier solid, kit spacing and nominal engagement | Actual kit thread depth and polymer compression; hands / solder access |
| 05 J2 | Official Raspberry Pi J2 documentation and candidate circuit | Pad metrology, exact removable connector, insulation/strain relief and switch nut |
| 06 Controls | Baseline WIRING / candidate BOM; independent pin-map review | Real pin-one identification, wire-tail and splice positions, I2C bench qualification |
| 06d OS microSD | Bench insertion before carrier fit; card included in carried stack. In-body withdrawal requires panel removal | Closed-panel +X extraction intersects the panel-mounted J2 power switch; the front slit does not establish service access |
| 07 Grip | Candidate base and lock geometry | Keyhole assembly sweep, run lead, actual strap and driver access |
| 07b Strap | Complete exported 12 mm routing proxy through both revised upper and heel slots | Actual threading, textile bend radius, closure/overlap/tail retention, hand clearance and load qualification |
| 08 Camera | camera_in discrete rigid-body path | Carried FPC, real fingers/tools, tolerance and optical load |
| 09 EVF | evf_in discrete rigid-body path | Native flex, foam compression, temporary support and exact connector access |
| 10 HDMI bench | Selected 300 mm installed / EVF-unplugged poses; Pi stays mated. Both-unplugged service is rejected due power-wire conflict; prior 200 mm study rejected | Real material minimum bend radius, clocking, thickness, shielding and strain relief |
| 11 Carrier insertion | Bare-module sweep plus separate full-carried study; 300 mm exact full-material and carried-head checks are separately source-bound | Complete carried ribbon, free head, Pi head and other attached leads; headers carried because closed-wall sockets cannot be reached in situ |
| 12 HDMI mate | Source EVF-head direction and catalog envelope | Constant-length full ribbon motion, upward head stroke and hands / tools |
| 13 Other leads | Official-source CSI geometry and declared straight-tool reservations | Full-width FPC/complete purchased length, physical contact faces, simultaneous connector access |
| 14 Power | Inherited electrical path and polarity rules | All electrical gates, actual pads/BMS, feed choice, fuse temperature and drop |
| 15 Slack | Revised floor/grip passage; separate 201-pose rigid connector/fuse/pack report, usable only with current manifest binding | Real complete-length retention, ties/heads and isolation reach |
| 16 Panel closure | Supported stationary FPS switch; axial shaft-tip support during initial 8.5 mm panel movement; FPS pair stays mated | Whole harness motion, junction hand access, stable prop, seam pinch and tool corridor |
| 17 Recording drive / lens | storage_out discrete sweep; collar geometry. OS card already fitted on bench; its extraction study is panel-off only | Real Princeton cap-off envelope, connector orientation, warm write rate; revised collar load |
| 18 Qualification | Existing gate list | 56 inherited physical gates, M1 and all new candidate gates remain open |
| 19 Service | Candidate dependency order; independent wording review | Hands/tools, retained harness, repeated-cycle tests and connector lifetime |

The inherited CSI orientation and its former passing side-port tool test are superseded by official-source connector geometry. The new long-connector-end cylindrical reserve test always retains operational HOLD for real jaws, latch travel, cooler and full FPC occupancy. The guide enables computed-pass captions only when the report matches the relevant snapshot, mechanical-manifest and current verifier/helper source hashes.

Source-only review by the independent packaging reviewer confirmed the J2 normally-open circuit and physical J8 map, and required more explicit FPC/stack disconnection wording. The builder subsequently identified inaccessible wall-facing GPIO housings, so the service order now carries header plugs during a bounded staging move, subject to full lead reach and sweep qualification. This is not a completed independent physical assembly audit.

The guide also binds the static power-wire report and exact input by hash. Known printed-part overlaps are called out explicitly; a static capsule pass would not qualify omitted pad roots or full flexible deployment. Selected FPS service keeps the genuine pair and full harness mated while the switch and carrier move together. The unsupported PH identity and in-body connector-grasp schemes are rejected. Bench separation, hand support and actual roots remain physical gates.
