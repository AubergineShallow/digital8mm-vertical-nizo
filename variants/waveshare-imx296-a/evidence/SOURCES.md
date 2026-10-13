# Primary-source register

Reviewed 2026-10-12. These sources describe products; none is an actual-parts
measurement or completed D2 qualification report.

- [Waveshare SKU 32501 product page](https://www.waveshare.com/product/raspberry-pi/cameras/global-shutter-cameras/imx296-global-camera-a.htm): identity, sensor/output and package contents.
- [Waveshare dimension drawing](https://www.waveshare.com/img/devkit/accBoard/IMX296-Global-Camera-A/IMX296-Global-Camera-A-details-size.jpg): Waveshare's copyrighted artwork. It is **not stored in this repository** (fix pass 2026-10-13, review R-03): the drawing stays local. SHA-256 of the copy used for the study: `ac60b95fc60e9219b5362616dcf4742af9dc43a6b8c4be4bd1f8714405029146` (69,783 bytes), pinned as `drawing_sha256` in camera-profile.json. A reviewer keeps a downloaded copy at the git-ignored `evidence/local/vendor-drawing.jpg` (or names it in `GS8_WAVESHARE_DRAWING`); the profile then verifies it byte-exactly. Only dimensions read from it are used here, as facts with this citation; see the Waveshare entry in the root THIRD-PARTY-NOTICES.md.
- [Waveshare setup wiki](https://www.waveshare.com/wiki/IMX296_Global_Camera_%28A%29): manual overlay and Pi 5 connection procedure. Direct retrieval returned a block; indexed vendor text was used. No bypass or logged-in access was attempted.
- [Raspberry Pi overlay reference](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README): IMX296 `cam0` option, as checked for software setup.
- [Bolt Depot screw 6365](https://boltdepot.com/Product-Details?product=6365), [nut 7362](https://boltdepot.com/Product-Details?product=7362), [washer 7364](https://boltdepot.com/Product-Details?product=7364): dimensions and parts-only USD prices for the unselected proposal. Nothing was added to a cart or ordered.

All new project Python code follows the repository MIT license. Other inherited
material remains subject to its existing notices and licenses; the root
THIRD-PARTY-NOTICES.md still applies.
