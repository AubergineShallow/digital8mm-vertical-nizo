# SPDX-License-Identifier: MIT
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from camera_profile import (ROOT, DRAWING_LOCAL, load_profile, validate_profile, drawing_verified,
                            nominal_local_bounds, exploratory_pose, release_status)


class ProfileContract(unittest.TestCase):
    def setUp(self):
        self.p = load_profile()

    def test_vendor_datum_is_pcb_not_sensor(self):
        bounds=nominal_local_bounds(self.p)
        self.assertEqual(bounds['pcb'],[-1.6,0.,-19.,19.,-19.,19.])
        self.assertAlmostEqual(bounds['unlocated_rear_connector_reserve'][0],-4.1)
        self.assertIsNone(self.p['optics']['pcb_front_to_sensor_mm'])
        self.assertIsNone(self.p['optics']['pcb_front_to_c_mount_shoulder_mm'])

    def test_drawing_bound(self):
        # The vendor drawing stays local (R-03). The pin is unchanged and a supplied copy is
        # verified byte-exactly; a stand-in file exercises both outcomes without the artwork.
        self.assertEqual(self.p['drawing_sha256'],'ac60b95fc60e9219b5362616dcf4742af9dc43a6b8c4be4bd1f8714405029146')
        with tempfile.TemporaryDirectory() as d:
            stand_in=Path(d)/'stand-in.jpg'; stand_in.write_bytes(b'not the vendor drawing')
            q=copy.deepcopy(self.p); q['drawing_sha256']=hashlib.sha256(stand_in.read_bytes()).hexdigest()
            self.assertTrue(drawing_verified(validate_profile(q,stand_in),stand_in))
            q['drawing_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'hash mismatch'):validate_profile(q,stand_in)
            with self.assertRaisesRegex(ValueError,'hash mismatch'):validate_profile(self.p,stand_in)
            with self.assertRaisesRegex(ValueError,'not found'):validate_profile(self.p,Path(d)/'missing.jpg')
        local=ROOT/DRAWING_LOCAL
        if local.is_file():
            self.assertTrue(drawing_verified(self.p,local))

    def test_drawing_pin_format_and_locality(self):
        for key,value in [('drawing_sha256','AC60'+'0'*60),('drawing_sha256','0'*63),('drawing_sha256',None),
                          ('drawing_redistributed',True),('drawing_redistributed',None),
                          ('drawing_local_path','evidence/vendor-drawing.jpg')]:
            q=copy.deepcopy(self.p);q[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate_profile(q)
        q=copy.deepcopy(self.p);q['sources']['drawing']=''
        with self.assertRaises(ValueError):validate_profile(q)

    def test_no_vendor_artwork_in_variant(self):
        # R-03: vendor drawings/datasheet images are never part of the public study.
        artwork={'.jpg','.jpeg','.png','.gif','.webp','.bmp','.tif','.tiff','.pdf'}
        local=(ROOT/DRAWING_LOCAL).parent
        found=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
               if p.is_file() and p.suffix.lower() in artwork and local not in p.parents]
        self.assertEqual(found,[])
        ignore=ROOT.parents[1]/'.gitignore'
        if ignore.is_file():
            self.assertIn('variants/waveshare-imx296-a/evidence/local/',ignore.read_text(encoding='utf-8').splitlines())

    def test_wrong_profile_rejected(self):
        for key,value in [('sku','SC0926'),('profile_id','official-pi-gs')]:
            q=copy.deepcopy(self.p);q[key]=value
            with self.assertRaises(ValueError):validate_profile(q)

    def test_no_bfar_or_tripod_inheritance(self):
        for key in ('bfar_ring','official_lock_tab','tripod_block_removal_required'):
            q=copy.deepcopy(self.p);q['features'][key]=True
            with self.assertRaises(ValueError):validate_profile(q)

    def test_no_pass_or_gate_relaxation(self):
        for key in ('production_release','physical_gate_inheritance','official_bfar_test_inheritance',
                    'qt_clearance_gate_relaxed','fps_48_54_measured','manual_controls_measured','dng_roundtrip_measured'):
            q=copy.deepcopy(self.p);q['qualification'][key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(q)

    def test_cooler_stays_official(self):
        q=copy.deepcopy(self.p);q['qualification']['official_pi5_active_cooler_retained']=False
        with self.assertRaises(ValueError):validate_profile(q)

    def test_no_unapproved_hardware_or_fake_dimensions(self):
        for key in ('hardware_fit_validated','fastener_addition_approved','exterior_change_approved','board_component_keepouts_measured'):
            q=copy.deepcopy(self.p);q['mechanical'][key]=True
            with self.assertRaises(ValueError):validate_profile(q)
        for key in ('pcb_front_to_sensor_mm','pcb_front_to_c_mount_shoulder_mm','adapter_diameter_mm','adapter_face_to_face_mm','lens_thread_engagement_mm'):
            q=copy.deepcopy(self.p);q['optics'][key]=12.5
            with self.assertRaises(ValueError):validate_profile(q)
        q=copy.deepcopy(self.p);q['mechanical']['installed_pcb_front_x_mm']=-16.9
        with self.assertRaises(ValueError):validate_profile(q)

    def test_tolerance_not_invented(self):
        q=copy.deepcopy(self.p);q['vendor_dimensions_mm']['mount_hole_tolerance']=.1
        with self.assertRaises(ValueError):validate_profile(q)

    def test_exploratory_pose_cannot_release(self):
        result=exploratory_pose(17.5)
        self.assertAlmostEqual(result['pcb_front_x_mm'],-16.9)
        self.assertFalse(result['physical_release'])
        self.assertFalse(result['installed_pose_approved'])
        for invalid in (None,True,float('nan'),float('inf'),0,-1,'17.5'):
            with self.assertRaises(ValueError):exploratory_pose(invalid)

    def test_setup_and_sensor_contract(self):
        for section,key,value in [('optics','sensor','imx477'),('optics','width',1440),
                                  ('optics','colour',False),('optics','raw_bit_depth',12),
                                  ('electrical','pi5_port','CAM0'),('electrical','dtoverlay','imx290'),
                                  ('electrical','eeprom_dependency',True),('electrical','cable_length_mm',200),
                                  ('electrical','cable_contact_orientation_confirmed',True)]:
            q=copy.deepcopy(self.p);q[section][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(q)

    def test_no_unmeasured_backfocus_claim(self):
        for value in (True, 0, None, 'false'):
            q=copy.deepcopy(self.p);q['optics']['optical_backfocus_measured']=value
            with self.subTest(value=value),self.assertRaises(ValueError):validate_profile(q)

    def test_schema_boolean_rejected(self):
        q=copy.deepcopy(self.p);q['schema_version']=True
        with self.assertRaises(ValueError):validate_profile(q)

    def test_baseline_hashes_and_tampering(self):
        from verify_baseline import verify
        self.assertTrue(verify()['baseline_constraints_unchanged'])
        with tempfile.TemporaryDirectory() as d:
            result=verify(d)
            self.assertFalse(result['baseline_constraints_unchanged'])
            self.assertFalse(result['physical_release'])
            self.assertTrue(result['mismatches'])

    def test_release_stays_blocked(self):
        result=release_status(self.p)
        self.assertFalse(result['physical_release'])
        self.assertFalse(result['integrated_assembly_generated'])
        self.assertFalse(result['adopted_in_official_design'])
        self.assertFalse(result['vendor_drawing_in_repository'])
        self.assertTrue(result['retention_option_b_as_drawn'].startswith('REJECTED'))
        # Fix pass 2026-10-13 added WS-07 (J7-R float), WS-08 (straight driver), WS-09 (drawing local).
        self.assertEqual(sorted(result['holds']),['WS-%02d'%i for i in range(1,10)])
        self.assertIn('J7-R float',result['holds']['WS-07'])
        self.assertIn('straight driver',result['holds']['WS-08'])

    def test_command_fails_closed_and_writes_hold_record(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'status.json'
            result=subprocess.run([sys.executable,str(ROOT/'review_status.py'),'--out',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertFalse(json.loads(out.read_text(encoding='utf-8'))['physical_release'])
            self.assertNotIn(b'\r',out.read_bytes())
        self.assertNotIn(b'\r',(ROOT/'review/status.json').read_bytes())
        saved=json.loads((ROOT/'review/status.json').read_text(encoding='utf-8'))
        self.assertEqual(saved,release_status(self.p),'review/status.json is stale; rerun review_status.py')


if __name__=='__main__':unittest.main()
