# Innomaker D2 source and software evidence

**HOLD: the saved public-STEP camera omits the real rear trigger/strobe headers. No complete-product fit, optical, hardware-capture or fabrication release is claimed.**

This note separates source evidence from physical acceptance. The fork changes the camera geometry and review records only. It does not edit capture code, install drivers, change a Pi configuration or validate a physical camera.

## 1 Mechanical source identity

- Product: [Innomaker colour IMX296 camera](https://www.inno-maker.com/product/cam-imx296color/), CAM-IMX296Color-GS / CAM-MIPI296Color; user-selected Amazon ASIN B0CQ4DTQZ2.
- Manufacturer archive: [IMX296 With CS ZIP](https://www.inno-maker.com/wp-content/uploads/2021/06/IMX296-With-CS.zip).
- Local STEP (not committed; no stated redistribution licence): fetch into `fetch/IMX296 With CS.stp` (git-ignored). The tools stop with a fetch message when it is missing.
- STEP SHA-256: `3d53cc2b16f4c4bd91776e57548dcf191689a6d4f7ee4962411cfb3f1b496b51`.
- Geometry implementation: `../innomaker_geometry.py`, with source checksum enforcement and explicit reconstruction assumptions. The fresh export manifest binds the actual implementation hash.

The source's PCB shells are reconstructed as 39 × 39 × 1.6 mm material with R3.5 corners. Four corner holes are Ø2 mm on 34 × 34 mm pitch. The four additional reconstructed holes are at native XY (−10, 0), (+10, 0), (+10, −3.5) and (−10, +3.5) mm, with radii 1, 1, 0.755 and 0.755 mm respectively. These are source-derived model values, not a receipt inspection. The manual's R2 corner value conflicts with the STEP R3.5 value. Minor 0.08 mm source edge rounds are omitted from the material reconstruction.

The product page gives 38 × 38 mm, while the STEP gives 39 × 39 mm (an earlier claim that a manufacturer drawing also gives 39 × 39 mm cited no source and is withdrawn); this fork follows the STEP and keeps the outline an open measurement. The check `board_outline_agrees_with_product_page` stays FAIL until the received board is measured. The as-supplied STEP spans native Z = −1.6 to +17.2 mm (18.8 mm total). That envelope includes the unidentified closed-disk upper part and excludes the separate received converter and photographed rear headers. It is not an installed working CS-mount depth or optical registration datum.

The source has 29 solids. Solid index 4 is excluded under an unverified protective-cap interpretation; its identity must be confirmed before treating the remaining shape as an operating camera. Native holder mouth Z = 13.2 mm is an unverified CS reference. A nominal 5 mm converter register difference preserves the original C flange at global X = +0.6 mm. No measured sensor plane, filter stack, back focus, converter thread/seating, rear-cell clearance or final camera clocking is established. The camera mass of 15 g and converter annular dimensions remain placeholders.

### Rear headers and source revision

The manufacturer documentation names two 2-pin rear headers opposite CSI (trigger and strobe connections), and a photograph supplied with the delivery (not committed, so not checkable here) shows them. Their true XY, housing geometry, solder features, projection and tolerances are unknown. The public STEP omits them. No removal, pin bending or alternative board revision is adopted.

The 3/6/9/12/15/18 mm rear prisms are sensitivity assumptions. A full-PCB-area prism covers XY only if the real headers remain within the PCB outline. A collision can reject that assumed envelope against its selected obstacles; a non-collision cannot qualify the actual, unmeasured headers. Use the exact fresh sensitivity report for scope and results, without carrying over lost or pin-free pass counts.

## 2 Pinned software evidence

The following exact upstream files were retrieved on 2026-10-13 without executing them. They are not committed (the manufacturer README states no licence; the driver is GPL-2.0 and the licence text is not shipped here). Fetch them into `fetch/`; `make_innomaker_records.py` verifies their SHA-256 identities and stops with a fetch message when one is missing. They are evidence snapshots, not installers or a qualified software stack.

### Manufacturer Raspberry Pi quick start

- [README at commit 46d6d217f0d754921503ef64a3d801aa935563d6](https://github.com/INNO-MAKER/cam-imx296raw-trigger/blob/46d6d217f0d754921503ef64a3d801aa935563d6/README.md).
- Local snapshot (not committed): `fetch/manufacturer-README-46d6d217.md`.
- SHA-256: `48c939936fc59d5865c9445b29baef24b2d91ad1796538429e7f77b34f1cfdc3`.

The manufacturer identifies a colour version, lists Raspberry Pi 5 with Bookworm/Trixie, and describes native kernel-driver use. Its Pi quick start connects CSI, enables the IMX296 overlay, reboots and tests with rpicam-apps. It does not prescribe a proprietary SDK installation for that Pi path. The separate Jetson binary package and optional trigger/I2C utilities are not the D2 Pi commissioning path.

The quick start uses CSI without additional trigger/strobe wiring; optional external-trigger and strobe functions are documented separately. Accordingly, the proposed ordinary free-running CSI use needs no extra header wires. This is an interpretation of the documented workflow, not a statement that the physical pins can be ignored. [Manufacturer hardware and quick-start documentation](https://docs.inno-maker.com/home/mipi-cameras/imx296-mipi-cameras)

The live documentation page was inspected through the web tool; a separate direct byte download returned HTTP 403, so no locally checksummed copy of that page is claimed. The immutable README snapshot supplies the local software evidence. Its published maximum frame rate is not a measured D2 throughput result.

### Raspberry Pi IMX296 kernel driver

- [Driver at commit f1c327d2ae5c1ffdb7a17660bf87b4a22d2ae313](https://github.com/raspberrypi/linux/blob/f1c327d2ae5c1ffdb7a17660bf87b4a22d2ae313/drivers/media/i2c/imx296.c).
- Local snapshot (not committed): `fetch/raspberrypi-imx296-f1c327d2.c`.
- SHA-256: `2af91529cefa4510602ad6b28355207fde7ef89e105d3d54a786b853b17e50b8`.
- The upstream file carries a GPL-2.0 SPDX identifier and its copyright notice; it is cited by URL, commit and hash rather than redistributed.
- Commissioning expectation (review B-14, not yet tested): `camera_auto_detect=0` and `dtoverlay=imx296` for the CAM/DISP1 port used by D2; the vendor's `,cam1` suffix is not an override listed in the Raspberry Pi `imx296` overlay, so do not copy it. The overlay defaults (54 MHz clock, rotation 180) and the libcamera `imx296` tuning files are for the official camera: record the board oscillator and set `clock-frequency` only if it is not 54 MHz, set rotation from the first frame, and calibrate colour (the Innomaker CS holder has its own IR filter). Open item: colour tuning/DNG matrices.

The driver enumerates 10-bit Bayer bus formats for all four flip-dependent colour layouts and a distinct monochrome Y10 path. This supports the plausibility of using the existing colour IMX296 stack. A kernel source file does not establish the installed Pi kernel, overlay, camera identity, userspace raw layout, tuning, buffer ownership or sustained capture behavior.

The manufacturer examples distinguish CAM0 and CAM1. Verify the actual installed overlay's supported parameters and the selected physical CAM/DISP 1 port during commissioning; do not apply configuration text blindly or treat this note as a configuration change. Record the actual OS image, kernel/firmware, overlay, libcamera, rpicam-apps, Picamera2 and camera revision. No vendor EEPROM or trigger-register writing is required or authorized here.

## 3 Cable and cooler software boundaries

The official Pi documentation recommends connecting the camera cable before installing the Pi 5 Active Cooler because the cooler can obstruct access. D2 retains that Pi-end bench order. Only later camera-end access with the panel off is proposed. The existing D2-20 200 mm Standard-Mini 22-to-15-pin cable provision remains; the Innomaker kit's included cable has not been established as equivalent. [Official Raspberry Pi camera installation](https://www.raspberrypi.com/documentation/accessories/camera.html#install-a-raspberry-pi-camera)

The normal CSI proposal does not use either rear header or reserve extra wires for them. It still requires their physical model and clearance, plus the full ribbon route, contact orientation, stiffeners, latches, bends and service motion. Electrical streaming evidence cannot close those mechanical holds.

## 4 Unchanged D2 capture contract

The existing software remains the commissioning foundation documented in [D2-INTEGRATION.md](../../../../software/gs8-camera-evf/D2-INTEGRATION.md). Earlier host-test statements are historical/unqualified for this camera fork; no new host-test count is asserted here. The old `run` path's 3S battery instructions are historical and must not be applied to D2's 1S X1203/toggle-run architecture.

- 24 fps recording requests 48 fresh sensor frames per second and records every second source frame.
- 18 fps recording requests 54 fresh sensor frames per second and records every third source frame.
- The retained default is a 90-degree shutter: approximately 10,417 µs at 24 fps and 13,889 µs at 18 fps. Actual applied exposure, gain, white balance and frame duration must be checked. A selected exposure must never be silently shortened to achieve a requested rate.
- Measured sensor timestamps and source sequence numbers remain distinct from recording sample indices and nominal postproduction time. Preview exposures deliberately not recorded are not missing frames. Sensor gaps or failure to sustain the requested cadence fail the take.
- The bounded ownership design remains: four camera buffers, at most one worker-retained camera request, up to two copied RAW frames, four DNG output slots and four disk-writer slots. Overload must fail/drain explicitly; it cannot be hidden by unbounded queues or retained camera buffers.
- An accepted RAW frame must be an owned copy after the original request is released. No compressed, packed or stride-padded data may be reinterpreted as the expected unpacked image solely because the sensor's bus format is RAW10.
- Accepted data must drain before durable close. Journal/hash/commit, low-power stop, removable-media, display-retention and shutdown contracts remain unchanged and unqualified on hardware.

## 5 Required bench acceptance

No item below has been performed on this Innomaker hardware by this reconstruction.

1. **Identity and modes:** enumerate the actual camera and colour sensor modes on the target Pi 5; confirm the correct board/revision, Bayer mode and resolution. Check compatibility with the existing camera-identity validation without weakening it to accept unknown devices.
2. **Negotiated RAW contract:** record requested and effective raw format, bit depth, Bayer order after flips, dimensions, stride, byte count and any packing/compression. Verify the adapter handles that exact layout and makes a valid owned copy. Check black/white levels, crop and metadata against the real stream. A preview or JPEG alone is insufficient.
3. **48 and 54 fps source cadence:** run both target modes at the accepted exposure/gain/WB settings. Save sequence numbers, measured timestamps, applied frame durations and observed rate. Check gaps, jitter, correct every-second/every-third selection and take-start/stop behavior. Do not use duplicated frames or nominal timestamps to conceal sensor loss.
4. **Buffer ownership and backpressure:** exercise preview plus RAW copy, conversion and disk writing together, including overload/failure. Verify bounded retention, prompt release, explicit failed-take reporting and complete drain behavior.
5. **Real DNG acceptance:** decode actual produced DNGs with an independent reader. Inspect image content, dimensions, CFA/Bayer order, orientation, black/white levels, exposure/gain/WB metadata, continuity and file integrity. Synthetic descriptors and fake DNG test bytes are not evidence of a working camera.
6. **Sustained load:** repeat both modes on the selected storage while warm, including capture/conversion/fsync, EVF preview, power and thermal logging. Measure useful sustained storage margin and optical source-to-eyepiece behavior rather than inferring them from driver support or callback timing.
7. **Integrated D2 behavior:** retain physical GPIO/selector/encoder, 1S power, media handling, shutdown-display, readiness and electrical/thermal acceptance. A software-ready label does not mean physical safety or PMIC-off.

Documentary native-driver compatibility is therefore useful evidence for proceeding to a controlled bench investigation. It is not a complete-product fit claim, a drop-in software guarantee or closure of the existing 48/54 fps RAW/DNG hardware gates.
