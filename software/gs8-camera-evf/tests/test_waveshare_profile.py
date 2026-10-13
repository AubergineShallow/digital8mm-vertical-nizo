# SPDX-License-Identifier: MIT
"""Waveshare setup regression tests: fake inventory, never physical evidence."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json
import unittest

from gs8_camera_evf.d2_app import D2Config, run_configured
from gs8_camera_evf.d2_readiness import load_commissioning
from gs8_camera_evf.d2_runtime import picamera_backend_factory
from gs8_camera_evf.evf import EvfPolicy, PicameraEvfBackend
from test_evf import FakeCamera, preview, settings


EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'
CONFIG = EXAMPLES / 'd2.waveshare-imx296-a.config.example.json'
COMMISSIONING = EXAMPLES / 'd2.waveshare-imx296-a.commissioning.example.json'


class WaveshareProfileTests(unittest.TestCase):
    def test_variant_preserves_existing_runtime_schema_and_safe_defaults(self):
        original = json.loads((EXAMPLES / 'd2.config.example.json').read_text())
        variant = json.loads(CONFIG.read_text())
        self.assertEqual(variant.keys(), original.keys())
        self.assertNotEqual(variant['output'], original['output'])
        self.assertNotEqual(variant['commissioning_manifest'], original['commissioning_manifest'])
        for key in set(original) - {'output', 'commissioning_manifest'}:
            self.assertEqual(variant[key], original[key], key)
        self.assertIsNone(variant['wb_gains'])
        self.assertIs(variant['simulation_only'], False)
        self.assertEqual(variant['shutdown_mode'], 'drain_only')
        with self.assertRaises(ValueError):
            D2Config.load(CONFIG)

    def test_variant_evidence_has_no_fabricated_hardware_pass(self):
        value = json.loads(COMMISSIONING.read_text())
        self.assertEqual(value['evidence_type'], 'not_run')
        self.assertIn('SKU 32501', value['build_id'])
        self.assertIsNone(value['recorded_at'])
        self.assertTrue(all(v is None for v in value['measurements'].values()))
        self.assertEqual(set(value['gates']), {'G-W10', 'G-W11', 'G-W12'})
        for gate in value['gates'].values():
            self.assertEqual(gate, {'status': 'not_run', 'report': None, 'sha256': None})
        with self.assertRaisesRegex(ValueError, 'measured-hardware evidence'):
            load_commissioning(COMMISSIONING)

    def test_calibration_alone_cannot_bypass_commissioning_or_open_adapter(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            value = json.loads(CONFIG.read_text())
            value['output'] = 'takes'
            value['wb_gains'] = [1.5, 1.25]  # Test input only, not calibration.
            (root / value['commissioning_manifest']).write_text(COMMISSIONING.read_text())
            path = root / 'config.json'
            path.write_text(json.dumps(value))
            parsed = D2Config.load(path)
            self.assertEqual(parsed.output, root.resolve() / 'takes')
            self.assertEqual(parsed.commissioning_manifest, root.resolve() / value['commissioning_manifest'])
            with patch('gs8_camera_evf.d2_app.importlib.import_module') as importer:
                with self.assertRaisesRegex(ValueError, 'measured-hardware evidence'):
                    run_configured(SimpleNamespace(config=path, adapter='unopened_test_adapter:build'))
                importer.assert_not_called()
            self.assertFalse(parsed.output.exists())

    def test_boot_fragment_defaults_to_one_explicit_cam1_overlay(self):
        fragment = (EXAMPLES / 'waveshare-imx296-a.pi5-config.txt').read_text()
        active = [line.strip() for line in fragment.splitlines() if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(active, ['camera_auto_detect=0', 'dtoverlay=imx296'])
        self.assertIn('# dtoverlay=imx296,cam0', fragment)

    def test_existing_factory_and_colour_raw10_contract_need_no_eeprom(self):
        for fps, source_fps, exposure_us in ((18, 54, 13889), (24, 48, 10417)):
            with self.subTest(fps=fps):
                factory_backend = picamera_backend_factory()(settings(fps))
                self.assertIsInstance(factory_backend, PicameraEvfBackend)
                self.assertEqual(factory_backend.policy.source_fps, source_fps)
                camera = FakeCamera()
                # Only libcamera's model is supplied: no serial/vendor/EEPROM identity.
                self.assertEqual(camera.camera_properties, {'Model': 'imx296'})
                backend = PicameraEvfBackend(factory_backend.policy, camera_factory=lambda: camera,
                                            preview_factory=preview)
                try:
                    descriptor = backend.preflight(settings(fps))
                    self.assertEqual((descriptor['model'], descriptor['width'], descriptor['height'],
                                      descriptor['bit_depth']), ('imx296', 1456, 1088, 10))
                    self.assertEqual(camera.config['raw']['format'], 'SBGGR10')
                    self.assertEqual(camera.config['controls']['ExposureTime'], exposure_us)
                    self.assertIs(camera.config['controls']['AeEnable'], False)
                    self.assertIs(camera.config['controls']['AwbEnable'], False)
                    self.assertEqual(camera.config['main'], {'size': (728, 544), 'format': 'XRGB8888'})
                    self.assertEqual(camera.config['buffer_count'], 4)
                    self.assertIs(camera.config['queue'], False)
                    self.assertFalse(backend.warmed_up)
                    for _ in range(source_fps):
                        camera.frame()
                    self.assertTrue(backend.warmed_up)
                finally:
                    backend.close()
                    factory_backend.close()
                self.assertTrue(camera.closed)

    def test_incompatible_raw_modes_do_not_gain_a_vendor_bypass(self):
        for fps in (18, 24):
            changes = ({'size': (1440, 1080)}, {'bit_depth': 12}, {'unpacked': 'R10'},
                       {'fps': EvfPolicy(fps).source_fps - 1})
            for change in changes:
                with self.subTest(fps=fps, change=change):
                    camera = FakeCamera()
                    camera.sensor_modes[0].update(deepcopy(change))
                    backend = PicameraEvfBackend(EvfPolicy(fps), camera_factory=lambda: camera, preview_factory=preview)
                    with self.assertRaisesRegex(ValueError, 'full-resolution colour RAW10'):
                        backend.preflight(settings(fps))
                    self.assertTrue(camera.closed)
                    self.assertFalse(camera.started)

    def test_model_aliases_and_missing_manual_controls_remain_rejected(self):
        for field, value in (('Model', 'Waveshare IMX296'), ('Model', 'imx296_mono'),
                             ('control', 'ExposureTime'), ('control', 'ColourGains'),
                             ('control', 'FrameDurationLimits')):
            with self.subTest(field=field, value=value):
                camera = FakeCamera()
                if field == 'Model':
                    camera.camera_properties['Model'] = value
                else:
                    del camera.camera_controls[value]
                backend = PicameraEvfBackend(EvfPolicy(24), camera_factory=lambda: camera, preview_factory=preview)
                with self.assertRaises(ValueError):
                    backend.preflight(settings())
                self.assertTrue(camera.closed)
                self.assertFalse(camera.started)
