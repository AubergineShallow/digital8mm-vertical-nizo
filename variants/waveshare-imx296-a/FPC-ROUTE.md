# CSI/FPC route: endpoints and holds

**No fitted cable route or slack result is exported for this camera.**

The existing D2 route terminates at the official camera's connector model and
assumes an official 200 mm cable. Waveshare includes 15-to-22-pin and 15-pin cables,
but the referenced product specification does not establish the received length,
contact-side orientation, stiffener length or minimum bend radius. The included
15-to-22 cable is the candidate Pi 5 lead; an additional cable is not approved.

## Retained and changed endpoints

- Pi end: retain selected CAM1 and the official Pi 5 Active Cooler. Existing
  source-model connector/latch/tool and cooler conflicts remain holds.
- Camera end: 15-pin CSI is drawn at the PCB lower rear edge. Only its 2.5 mm
  rear projection is dimensioned; exact socket location, width, latch sweep,
  contact orientation and exit tangent are not sufficient to create a real route.
- Module datum: camera PCB front X remains unplaced pending the installed C-mount
  shoulder measurement. Moving a route endpoint to an arbitrary old camera X
  would hide this missing datum.

## Proposed routing and assembly sequence, not an approved geometry

After measuring the endpoints, try the existing Pi-side service corridor and
camera lower opening first. Keep the ribbon clear of fan inlet/exhaust, cooler
surfaces, lens threads, fastener heads, shutter/control mechanism and removable
panel joint. Preserve the original QT route and its strict clearance criteria.
The U-frame study has an open lower middle, but that opening is not clearance
proof for the actual latch, fingers, tool or folded cable.

With all power disconnected: orient/seat the measured camera lead, set the optics
on the bench, install/anchor the module without loading the cable, mate CAM1 using
the documented service access, store measured slack in a supported curve, then
close the panel only after inspecting every fold and pinch plane. Reverse the
procedure for removal; do not use the ribbon to pull the module out. The final
sequence must be demonstrated on the integrated design and received parts.

## Release evidence required

Record cable end-to-end usable length, contact sides and continuity/pin mapping,
width/thickness/stiffeners, vendor or tested bend limit, both connector/latch
poses, required finger/tool volumes and strain-relief sites. Build the actual
ribbon surface and cable-length/bend budget, then check closed state, install,
unplug, lens focus/rotation, panel removal and service motions against every
part. Include source-camera connector geometry in checks; do not exempt it by
reusing an official-camera own-end rule. A cable that electrically enumerates
still needs mechanical, noise/dropout, warm recording and repeated-service tests.
