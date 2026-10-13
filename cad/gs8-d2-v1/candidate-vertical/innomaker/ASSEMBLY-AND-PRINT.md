# Innomaker D2 assembly and print review

**STOP: source/header clearance and physical qualification are HOLD. The following is a candidate sequence for engineering review, not permission to fabricate, assemble or energize the camera.**

**2026-10-13 fix pass: blockers found by review (each stays open until measured or decided by the user).**

- **J7-R lens torque (user decision).** The delivered fork removed the official lens-torque catches and adds nothing in their place, so the first roll contact is the PCB corner on the printed guides (about 1.82 deg). The official rule needs a holder or metal reaction first, with a 1.0 deg margin. Choose a lens-hold design (for example a printed fixture on the metal CS holder or converter, or thread the lens and converter off-camera before the camera is hung). Check `lens_torque_reaction_before_PCB_contact` FAILs until then.
- **Focus (measurement).** The holder mouth is used as the CS flange. Under that convention the sensor die (review reading of the STEP) sits about 14.9 mm behind the C flange instead of 17.526 mm, which no Kowa focus travel can absorb. Measure the received holder and ring before any re-placement. Check `C_flange_to_sensor_plane_verified` FAILs.
- **Image orientation (measurement, then CAD).** As modelled, the sensor long axis is vertical (portrait frame); the imx296 overlay rotates only 0/180 deg. Re-clock the camera 90 deg after one bench capture confirms it. Check `sensor_long_axis_horizontal` FAILs.
- **Float to the panel (geometry or measurement).** The camera-to-panel gap is 0.500 mm; the official centring rule needs 0.30 stack + 0.25 panel location + 0.1 running = 0.65 mm. Check `J7_float_centring_camera_vs_panel` FAILs.
- **C-CS converter (user decision).** It is not in the manufacturer packing list. Confirm on receipt or buy one; its OD/ID/length are assumptions.
- **Bench procedure missing.** The "supported optical-bench procedure" cited below does not exist yet; write it after the measurements above.

This plan covers the compact Innomaker colour-camera substitution and its revised safety guides. It supersedes the official-camera BFAR, camera-PCB tripod-block, catch and bonded-stub instructions for this fork only. **The functional D2 tripod mount in the grip is retained.** Its D2-31 1/4-20 UNC steel nut remains one installed part in the existing base-grip hex pocket. Removed I-05B was a zero-installed, zero-purchase detail for the old camera's separate tripod block and two screws. All unrelated baseline constraints and failure gates remain applicable and unqualified.

## 1 Before any physical trial

1. Confirm the received colour SKU and board revision against CAM-IMX296Color-GS / CAM-MIPI296Color and the photograph supplied with the delivery (not committed) and the manufacturer documentation. Record all four rear pins and both header housings. Measure their XY bounds, solder-side features, rearward projection from the PCB and tolerances. Do not trim, bend, desolder or remove them.
2. Update the source model with the actual headers and rerun installed-clearance, full insertion and service checks against the exact saved geometry. Full-board 3/6/9/12/15/18 mm prisms are sensitivity studies, not substitute measurements. A no-contact result for a study prism does not close this gate.
3. Resolve the protective-cap interpretation and the public STEP/manual dimensional conflicts. Confirm the PCB edges and component keepouts before allowing a guide near them. A nominal 0.5 mm gap is not a measured tolerance allowance or safe contact surface.
4. Measure the received converter, actual CS seating face, thread engagement, holder material, rear-cell clearance, optical datum and final clocking. Demonstrate a safe way to support the holder directly during lens threading. **Do not react lens torque through the PCB, guide edges, CSI connector or unqualified holder grip.** No new tool, holder or purchased support is adopted by this plan.
5. Qualify the complete existing collar/load path and lens support band, including the inherited M1 requirement. The camera hangs from the lens/converter connection; passive guides do not normally carry its weight and do not provide qualified roll restraint.
6. Keep all power absent during assembly and service. Disconnect the battery physically and remove external power. The retained 1S X1203 architecture and all electrical safety gates are unchanged.

## 2 Printed parts and inventory

The compact production set is expected to comprise tub, panel, carrier, base grip, cap, eyecup, exposure knob, FPS knob and lens collar. The authoritative count and exact STL identities are generated from the fresh manifest in [PRINT-INVENTORY.csv](PRINT-INVENTORY.csv): **nine assembly rows and nine physical production pieces**. One file represents one piece. The centring gauge and local coupons are excluded from that total.

The tub includes its passive PCB-edge guides as integral material. There is no separate tab-catch insert, tenon bond or V-68 epoxy operation. V-68 was specified solely for that +Y tab-catch bond; the unrelated D2-45 adhesive foam, D2-46 adhesive-lined heat-shrink, D2-46R neutral-cure RTV, D2-48 tape and D2-49 bed-release supplies remain. Do not print the historical `tab_catch_insert.stl` or follow the historical V-68 adhesive step. The original-storage stick sleeve is outside this compact selection.

Use each manifest-bound bed orientation, rather than an assembly STEP orientation, for slicer review. The current material classes are inherited: ASA satin silver for tub/panel, ASA black for carrier/grip/cap/knobs/collar, and TPU 95A black for eyecup. These are unqualified classes, not a selected filament or machine profile. Collar heat performance remains open.

Before release, inspect the actual slicer paths, supports, access for support removal, guide roots, overhangs, plenum manufacture and cleanout, wall/boss geometry, collar geometry, bed contact and dimensional change. Print appropriate dimensional and structural coupons only through the qualification process. Mesh validity, watertightness or sampled CAD clearance does not establish printability, strength, useful airflow or a physically safe guide. Record machine, filament, profile, orientation, measured dimensions, mass and test results. No production printing release is granted here.

## 3 Proposed assembly order after the gates close

### Bench preparation

Prepare the unpowered Pi/UPS/carrier assembly on its own support. Seat the **Pi end** of the retained D2-20 Standard-Mini 22-to-15-pin, 200 mm camera cable straight in CAM/DISP 1, with confirmed contact orientation and latch closure, **before installing the official Raspberry Pi Active Cooler**. Raspberry Pi warns that the cooler makes camera-connector access awkward. Keep the free camera end protected. Fit the official cooler and keep its native fan lead with the module. This preserves the official bench order; an enclosure opening is not proof of cooler-retained Pi latch access. [Official camera installation guidance](https://www.raspberrypi.com/documentation/accessories/camera.html#install-a-raspberry-pi-camera)

Retain the baseline module, FPS switch, EVF, power and other harness preparation constraints. Any older test/pass language in those records is historical/unqualified for this fork. Do not use the preserved software's historical 3S setup for the D2 1S system.

### Centre the collar in an empty optical bay

With the carrier and removable +Y panel absent, fit and centre the retained lens collar using the selected centring gauge **while both the camera and converter are out of the body**. Follow the inherited collar qualification and support requirements. Remove the gauge completely before bringing in either the camera or converter. The gauge and converter are not a coexisting assembly state; do not use a camera-installed or converter-installed centring sequence.

### Camera and converter insertion

Keep the carrier and removable +Y panel absent. The lens is absent during the proposed camera insertion. Seat and verify the actual converter only through the supported optical-bench procedure after its unresolved support/thread/optical gates are closed.

The conditional rigid insertion path starts with the camera and converter **6.2 mm rearward** of their final axial position. Bring the assembly in through the open +Y side, then move it **forward 6.2 mm along +X** to the candidate position. This replaces the old official-camera 11.1 mm / 2 mm-high BFAR path; do not combine the two instructions. Keep the camera supported throughout. The proposed path is based on the incomplete public source and remains HOLD for the actual headers, tolerance, fingers/tool support and any connected ribbon.

The current camera-approach screen conservatively retains module obstacles even though this proposed sequence removes the module. That screen is limited to the declared camera approach; it does not validate later carrier insertion, complete camera/module sequencing or linked-ribbon deployment. Those integrated assembly and service paths remain unverified.

Only after the camera's safe holder-supported assembly method is established may the lens-threading operation be considered. Support lens and holder independently, preserve verified thread seating and avoid transferring torque to the PCB or guides. Establish the existing lens/collar support before letting go of the camera. Removing the lens later requires independent camera/holder support first; the guides do not make a loose camera self-supporting.

### Carrier and camera cable

The Pi cable end remains installed from the pre-cooler bench step. Carry the module on its own support, never by the ribbon, and protect the free camera end throughout insertion. **Only the camera-end CSI mating is proposed later with the panel off.** Its nominal reserve does not prove actual finger access, latch travel, insertion force or cable withdrawal.

The complete 200 mm ribbon must be modeled and checked at full width, including both end stiffeners, correct contact faces, roots, minimum bend requirements, strain-free slack and all deployment/storage poses. Actual seated camera clocking must be used. Until that is done, neither the proposed order nor separate rigid-envelope results qualifies the linked camera/module assembly or service path. If the included Innomaker cable is considered instead, first establish its pin count, orientation, length, stiffeners and electrical equivalence; it has not replaced D2-20.

### Closure and commissioning

Retain the existing EVF, FPS and panel work order, with every harness independently supported and all unresolved mating/reach gates respected. **The QT −23.99 mm failure remains a STOP.** Do not stretch a cable or use a closed panel to force parts into place. Check passive-guide gaps without PCB preload and verify that closing the panel cannot push the camera, lens, headers, CSI latch or ribbon.

Install a battery or apply power only after the unchanged electrical, power, service and thermal acceptance gates are actually completed. No permission to energize follows from a completed CAD sequence.

## 4 Service boundaries

- Camera service requires support for the camera/holder before the lens or converter ceases to carry it. Safe support and actual thread release are HOLD.
- Panel-off camera-end access is a proposal only. Full cable deployment, controlled slack, header clearance and removal/reinsertion remain HOLD.
- Pi-end camera-cable release with the official cooler retained is unqualified. Repeated cooler removal/refit is not an adopted service workaround; that route would need its own reviewed procedure and qualification.
- The passive guides are safety/roll-stop geometry only. They cannot be used as a tool reaction surface, clamp, datum lock or normal weight support.
- Retain every inherited pack, power, hot-drop, fuse, EVF, QT, FPS, J2, structural, strap, fastener, print and flexible-harness hold. No unrelated gate is closed by the smaller camera board.

## 5 Required release evidence

Release requires a source-current manifest and reports, a measured source model matching the actual rear headers, actual optical/converter and holder-support evidence, complete ribbon and harness deployment/service evidence, verified physical print/strength/thermal results, and the unchanged electrical acceptance. The software must separately satisfy the colour sensor, 48/54 fps, RAW-buffer, measured-timestamp, DNG and sustained-load tests in [SOURCE-AND-SOFTWARE.md](SOURCE-AND-SOFTWARE.md). Until then this remains an engineering review candidate.
