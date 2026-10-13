# Mechanical review and retention decision

## Datum discipline

Study coordinates: X points toward the lens, PCB front is X=0, board centre is
Y=Z=0, CSI is at the lower edge in the source front view. This drawing-implied
centring/orientation is not a measured concentricity specification. Board rear
is X=-1.6, the connector reserve extends to X=-4.1, and the nominal housing front
is X=+12.5. The sensor plane and C-mount seating shoulder remain unknown.

The original D2 lens's C shoulder is X=+0.6. If the measured installed shoulder to
PCB-front distance is d, PCB-front X would be 0.6-d, and local Z would shift by
+60 to the original optical axis. `camera_profile.exploratory_pose(d)` performs
that sensitivity arithmetic only, clearly labelled unmeasured. It does not place
an assembly, certify optical alignment or let any release gate pass. The 12.5 mm
housing depth must not be substituted for d. The supplied adapter's shoulder and
spigot geometry must be measured separately in the configuration used.

## Why the old catches do not transfer

The old camera hangs from the clamped lens. Its BFAR ring provides the intended
axial catch surface, its tab provides anti-roll contact, and its rear cover has
a secondary catch. This module has neither the ring nor tab and has a different
rear stack. A smaller diameter passing a lip is not positive retention. Reusing
the original catch acceptance JSON would falsely certify absent contact surfaces.

The original catch geometry has NOT been silently removed from the D2 tub or
panel and relabelled as a Waveshare assembly. Those modifications need a known
camera pose and replacement load path. The integrated geometry is intentionally
blocked rather than exporting a visually plausible but unretained camera.

## Retention options

### A. Printed edge cradle using existing enclosure closure — not selected; incompatible with J7-R float as described

A saddle could locate board edges and be captured by the removable panel without
new fasteners. The board drawing does not give component/copper keepouts, edge
connector/latch access, allowed contact load or assembly order. Elastic clips
would add sustained strain, print-direction and hot-creep risks. Shell closure
could preload/warp the PCB and overconstrain the lens thread. This route is kept
as an unevaluated alternative, **not CAD-certified or recommended solely to avoid
extra hardware**. No fictitious clear PCB edge lands are assumed.

### B. Four-hole carrier interface — REJECTED as drawn under J7-R float (fix pass 2026-10-13)

The supplied four Ø2.5 board holes give a clearer potential load path than
unknown board edges. The standalone study uses a printed U-frame behind the
board with four integral 3 mm stand-offs, nominal 2.2 mm clearance holes, a
2.4 mm rear web and 7.2 mm diameter corner bosses. The lower middle stays open
for CSI access. Overall nominal frame span is 37.2×37.2 mm in Y/Z, depth 5.4 mm
behind the PCB rear. These are **design proposal dimensions**, not vendor data.

Proposed clamp stack: screw head → front washer → approved PCB annulus → printed
stand-off → rear web → nut. Candidate hardware is detailed in [BOM-DELTA](BOM-DELTA.md).
Metal washers may contact copper/components; no electrical clearance or safe
clamp torque is assumed. A 6 mm diameter support annulus on each rear corner also
needs actual component and trace inspection. Insulating washers/spacers, if needed,
would be a new proposal rather than an unrecorded substitution.

Intended complete load path, still unresolved: camera housing attachment → PCB
mount holes → carrier → positive enclosure anchor → tub, while the existing lens
collar supports the lens. The PCB/housing joint strength, lens-thread preload,
thermal movement and allowance for datum mismatch require review. The supplied
study stops at the carrier: **no enclosure anchor is modelled, and the frame must
not be mistaken for an installed mount**. Capturing its two sides in tub/panel
seats is a future design option after d and keepouts are measured; existing panel
screws would not alone prove adequate camera restraint.

## J7-R float and straight-driver holds (fix pass 2026-10-13, review R-21)

**J7-R float** is a project design rule: in the final pose the camera touches no
printed part, and lens torque never passes through the camera housing, cover or
PCB. The official D2 meets it by hanging the camera from the lens, which the lens
collar holds; its catches keep a clearance and touch only if the camera moves.

Option B as drawn fixes the camera in two places at once: the lens through the
collar, and the PCB through the printed carrier anchored to the enclosure. That is
a double constraint with a printed part in permanent contact with the PCB. Datum
mismatch, thread preload and thermal movement would then load the PCB/housing
joint and the lens thread. **Option B as drawn is rejected under J7-R float.**
Tighter tolerances do not make it acceptable. Option A, a printed saddle captured
by the panel against the board edges, touches the PCB in the final pose too and is
equally incompatible as described.

A retention concept can be reconsidered only when all of the following are shown
with measured parts and the integrated checks (hold WS-07):

1. The camera, with anything fastened to it, hangs from the lens held by the
   collar and has a recorded clearance to every printed part in the final pose.
   Any catch or carrier engages only when the camera moves (drop or shock),
   never at rest. A compliant carrier in permanent contact would still break the
   rule as written; it would need an explicit user decision first.
2. Lens focusing and rotation torque react through the collar, never through the
   camera housing, the PCB or a carrier.
3. The clearances come from the measured shoulder datum d (WS-01) and measured
   board keepouts, not from the 12.5 mm housing depth.

**Straight-driver rule** (hold WS-08): every screw must be drivable with a
straight driver along a clear axis in the assembled state; long bits and plugged
access holes are allowed. The proposed M2 clamp stack and any future anchor screw
have no driver axis shown with the camera installed and the lens in the collar.
This is open, not passed.

## Constraints and checks before adoption

- Keep the existing exterior envelope, optical axis, lens collar and official Active Cooler.
- J7-R float (WS-07): no printed part touches the camera in the final pose; lens torque
  goes through the collar only. Never clamp both the lens (collar) and the PCB (carrier).
- Straight-driver rule (WS-08): show a straight driver axis for every screw in the
  assembled state.
- Do not add screws/nuts/washers to the approved BOM without user approval.
- Check the board at maximum 38.2 mm side and housing depth at 12.7 mm; do not invent
  unspecified tolerance on hole location, thickness or diameter.
- Measure the actual cable/connector region; the broad rear reserve overlaps any
  corner stand-off until those local clear regions are established.
- Test insertion/removal from the open side and driver access without bending the
  PCB, twisting a loaded lens or unclipping a powered CSI cable.
- Resolve lens focus and final adjustment before locking the mount; do not turn
  the camera against a fixed lens with the cable trapped.
- Re-run camera, collar, tub/panel, cable/tool, cooling and full rigid/service
  collision checks on the actual integrated design. A standalone valid solid
  and STEP round-trip do not establish those results.
- Print coupon/fit checks, measured contact pressure, warm torque/creep and drop
  or service load qualification remain open. Do not infer material strength from
  a visually continuous frame.
