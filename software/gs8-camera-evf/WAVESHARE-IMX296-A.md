# D2 software setup: Waveshare IMX296 Global Camera (A)

2026-10-12. **Separate commissioning variant; host-tested only. No hardware pass.**

2026-10-13 (fix pass): part of the blocked [Waveshare study](../../variants/waveshare-imx296-a/README.md),
a study delivered by the delivering agent (dot); not adopted. The package `README.md`, `D2-INTEGRATION.md` and
`MANIFEST.in` are left unchanged on this branch: they are byte-identical to the upstream r7 commit
and hash-bound in `validation/software-verification.json`. This file and the Waveshare examples are
therefore not in the source distribution; use them from the repository checkout.

This variant selects Waveshare **SKU 32501, IMX296 Global Camera (A)**, whose
[product specifications](https://www.waveshare.com/product/raspberry-pi/cameras/global-shutter-cameras/imx296-global-camera-a.htm)
list colour 1456 × 1088 RAW10. Do not substitute an IMX296 monochrome module.
The original D2 runtime, readiness gates, camera backend, and examples remain
unchanged. This is a setup profile, not a new camera driver or a completed
production image. Read [D2-INTEGRATION.md](D2-INTEGRATION.md) for its remaining
adapter, EVF shutdown-screen, storage, power and thermal qualification work.

## Pi 5 camera connection and boot configuration

With the Pi powered off, connect the camera to **CAM1** using the appropriate
15-to-22-pin CSI cable. Verify cable orientation against the board markings and
[vendor connection guide](https://www.waveshare.com/wiki/IMX296_Global_Camera_%28A%29).
Use a single attached camera: the existing backend opens Picamera2's default
camera, not a hard-coded CAM1 index. A connector label is not a libcamera index.
Do not connect another camera and assume it will select this one.

Review and merge [the camera-only config fragment](examples/waveshare-imx296-a.pi5-config.txt)
into the active Raspberry Pi OS boot configuration, usually
`/boot/firmware/config.txt` on Bookworm; older installations use `/boot/config.txt`.
It is not a replacement for that file. Keep the existing D2 HDMI/KMS and power
settings. Resolve duplicate/contradictory camera directives and place the two
camera settings in a section that applies to this Pi:

```ini
camera_auto_detect=0
dtoverlay=imx296
```

For **CAM0 instead**, replace the overlay line with
`dtoverlay=imx296,cam0`; do not enable both lines for one camera. The Waveshare
wiki recommends CAM1 for one camera and an explicit overlay for third-party
modules. The upstream [IMX296 overlay reference](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README)
also documents the `cam0` parameter. Use the stock IMX296 overlay for this
profile; this guide does not apply IMX290 clock/tuning-file instructions.
Reboot after an operator applies the boot change.

Neither the setup nor the backend depends on a camera identity EEPROM: module
selection is explicit, and the backend validates libcamera's reported model
and negotiated colour mode. This does not establish whether a particular
received board contains an EEPROM. There is no EEPROM programming step and no
boot/config modification performed by the application.

## Verify enumeration before capture commissioning

Use Raspberry Pi OS's matched Picamera2/libcamera/KMS packages, as described in
the [package README](README.md#run-on-a-raspberry-pi-5). Record the actual OS,
kernel, firmware, libcamera and Picamera2 versions; this profile does not pin an
unmeasured hardware stack. After reboot:

```sh
rpicam-hello --list-cameras
```

There must be one intended camera with model `imx296` and the full 1456 × 1088
10-bit colour Bayer mode. Stop if the device or mode differs; a vendor product
name, a preview image or the listed maximum mode rate does not qualify capture.
Inspect Picamera2's `camera_properties`, `sensor_modes` and `camera_controls`
on the actual Pi and retain that inventory with the build report. The backend
requires these controls: `AeEnable`, `AwbEnable`, `ExposureTime`, `AnalogueGain`,
`ColourGains`, `FrameDurationLimits`, and `NoiseReductionMode`.

The unchanged `PicameraEvfBackend` verifies:

- Exact `imx296` identity (case/whitespace normalised), 1456 × 1088, 10-bit,
  and a colour Bayer unpacked RAW format; no smaller/cropped or monochrome fallback.
- A mode advertising the requested source rate, then applied metadata and
  sequence/cadence during warmup and capture. The same strict tolerances apply.
- Manual AE/AWB-off controls, explicit calibrated WB, a fixed 90° shutter,
  728 × 544 XRGB8888 preview, four camera buffers and `queue=False`.
- Matching progressive 59–61 Hz HDMI mode through DRM/KMS, unchanged bounded
  RAW/DNG queues, source-loss failure and durable drain/commit behavior.

D2 requests **48 → 24 FPS** and **54 → 18 FPS**, with nominal exposures of
10,417 µs and 13,889 µs respectively. Those are software requirements, not
measured Waveshare performance. Do not lower the source rate, crop the sensor,
relax metadata checks or invent timestamps to make a failed qualification pass.

## Separate D2 configuration and evidence

Copy these two examples to a new deployment directory using the filenames below:

- `examples/d2.waveshare-imx296-a.config.example.json` → `d2.waveshare-imx296-a.config.json`
- `examples/d2.waveshare-imx296-a.commissioning.example.json` → `d2.waveshare-imx296-a.commissioning.json`

The runtime example uses the existing schema, a separate
`/media/gs8/takes-waveshare-imx296-a` output directory, `simulation_only: false`,
`shutdown_mode: "drain_only"`, and **null WB gains**. It intentionally rejects
until the actual camera/lens/lighting WB is measured and supplied. Set the
output path to the verified storage mount; directory writability alone is not
mount verification. The commissioning example is explicitly `not_run`, with
no report hashes, review date or measurements. It also intentionally rejects.

Identify the actual SKU, board revision/serial if available, cable/port, optics,
WB calibration, storage, pack, cooling and software revisions in the new build's
reports. Do not reuse the original module's qualification as evidence for this
variant. The unchanged manifest loader requires reviewed, hash-matched physical
reports for G-W10/G-W11/G-W12 plus measurements within its existing bounds;
the full D2 gate procedures remain mandatory. Hashes provide traceability,
not proof that a measurement is true.

Only after qualification and installation of a reviewed live adapter, launch:

```sh
python -m gs8_camera_evf d2-run \
  --config /path/to/d2.waveshare-imx296-a.config.json \
  --adapter your_d2_adapter:build
```

The adapter should use the existing `picamera_backend_factory()` and the D2
input/gauge/readiness/display/media interfaces. `your_d2_adapter` is a placeholder;
no default live adapter or service is supplied. No new `camera_model`, EEPROM,
port or vendor key is added to runtime JSON; unknown keys still reject.
Do not launch the historical `run` command as a substitute for D2's 1S controls
and readiness gate. `drain_only` does not halt the Pi or authorize battery removal.

## Required physical evidence, still open

Measure both source rates on the received camera, manual-control application
and stability, real colour/DNG decode, sustained DNG conversion/write throughput,
frame counts and source gaps, full-sensor framing/orientation, optical EVF latency,
thermal and power behavior, and drained shutdown/media safety under load.
Requalify G-W10/G-W11/G-W12 for the actual assembly; all other D2 gate obligations
remain. Neither vendor compatibility nor a passing host test closes a gate.

Host checks from this package directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_waveshare_profile.py' -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

The profile tests use fake camera inventory and no EEPROM property to protect
the same backend contract at both rates, reject incompatible modes/controls,
and verify that incomplete Waveshare examples fail before adapter import.
They do not acquire real frames, decode DNG, access GPIO/I2C/HDMI or measure FPS.

## Source record

Vendor product specifications and indexed vendor wiki text were reviewed on
2026-10-12. Direct wiki retrieval was blocked; the indexed vendor text supplied
the single-camera CAM1, manual-overlay and boot-file instructions. The upstream
overlay reference was also checked. No page's generic camera tutorial is treated
as proof of SKU 32501's measured 48/54 FPS or DNG behavior on this D2 build.
