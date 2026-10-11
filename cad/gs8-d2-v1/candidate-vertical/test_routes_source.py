"""Fast source-only regression tests. These are NOT physical release tests."""
from cv_io import read_text
import hashlib
import json
import math
from pathlib import Path
import unittest
import routes


LANDMARKS=Path(routes.__file__).resolve().parent/'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/port-landmarks.json'
TOL_MM=1e-12  # FP-15: platform libm last-bit differences (observed <= 1.42e-14); evidence tolerance elsewhere is 1e-6 mm


def assert_usb_plug_on_landmark(tc,plug,landmarks):
    """p_usb_pi box: mating face exactly on the official GPIO-side USB2 receptacle face, centred on it in z, centre inside it in y."""
    b,u=plug['box'],landmarks['usb2']['bbox_candidate_mm']
    tc.assertEqual(b['x'][1],u[0])
    tc.assertAlmostEqual((b['z'][0]+b['z'][1])/2,(u[4]+u[5])/2,places=9)
    tc.assertTrue(u[2]<=(b['y'][0]+b['y'][1])/2<=u[3])
    tc.assertAlmostEqual(b['x'][1]-b['x'][0],31.0,places=9)
    tc.assertAlmostEqual(b['y'][1]-b['y'][0],9.8,places=9)
    tc.assertAlmostEqual(b['z'][1]-b['z'][0],15.5,places=9)


def float_differences(a,b,where=''):
    """[{where, a, b, ulps}] for floats that differ; raises AssertionError on any other difference."""
    if isinstance(a,dict):
        if not isinstance(b,dict) or a.keys()!=b.keys():raise AssertionError('keys differ at %s'%where)
        return [d for k in a for d in float_differences(a[k],b[k],where+'.'+str(k))]
    if isinstance(a,list):
        if not isinstance(b,list) or len(a)!=len(b):raise AssertionError('length differs at %s'%where)
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in float_differences(x,y,'%s[%d]'%(where,i))]
    if isinstance(a,float) and isinstance(b,float):
        if a==b:return []
        return [dict(where=where,a=a,b=b,abs=abs(a-b),ulps=abs(a-b)/math.ulp(max(abs(a),abs(b))))]
    if type(a)!=type(b) or a!=b:raise AssertionError('value differs at %s: %r != %r'%(where,a,b))
    return []


def assert_same_within_tol(tc,a,b,tol=TOL_MM):
    bad=[d for d in float_differences(a,b) if not d['abs']<=tol]
    tc.assertEqual(bad,[])


class RoutesStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=routes.build()
        cls.alt=routes.build(185)

    def test_original_harnesses_and_new_power_button(self):
        r=self.r
        self.assertEqual(r['route_count'],11)
        self.assertEqual(r['plug_end_count'],22)
        self.assertEqual({c['id'] for c in r['routes']},{c['id'] for c in routes.L.CABLES}|{'power_button'})
        self.assertEqual(routes.build(power_button=False)['route_count'],10)
        json.dumps(r,allow_nan=False)

    def test_full_rigid_connectors_retained(self):
        p={p['id']:p for p in self.r['plugs']}
        # FP-15 correction (FIX-LOG 'D2 FP-15 test_routes_source'; proof: tests/test_routes_source_fix.py): the old
        # constants x [-153,-122], z [44.75,60.25] were the rejected Ethernet-row placement. The plug is bound to the
        # official Pi 5 GPIO-side USB2 landmark, exactly, with the full 31 x 9.8 x 15.5 allowance.
        assert_usb_plug_on_landmark(self,p['p_usb_pi'],json.loads(read_text(LANDMARKS))['objects'])
        self.assertAlmostEqual(p['p_hdmi_pi']['box']['z'][1]-p['p_hdmi_pi']['box']['z'][0],14.5)
        self.assertAlmostEqual(p['p_hdmi_evf']['box']['z'][1]-p['p_hdmi_evf']['box']['z'][0],26.5)
        self.assertFalse(self.r['checks']['rigid_connector_collisions'])
        self.assertFalse(self.r['checks']['rigid_connector_wall_overruns'])
        self.assertFalse(self.alt['checks']['rigid_connector_collisions'])

    def test_header_tails_and_unshrunk_housing_gate(self):
        self.assertEqual(len(self.r['header_housings']),7)
        for h in self.r['header_housings']:self.assertAlmostEqual(h['wire_exit'][1],-15.4)
        for b in self.r['header_wire_branches']:self.assertFalse(b['curve']['errors'])
        self.assertTrue(self.r['checks']['header_housing_tolerance_overlaps'])
        self.assertIn('fan-in',self.r['signal_geometry']['qt']['fan_in_gate'])

    def test_full_300mm_hdmi_material(self):
        for key in ['hdmi_ribbon','hdmi_ribbon_premate','hdmi_ribbon_unplugged']:
            h=self.r[key]
            self.assertAlmostEqual(h['routed_length_mm'],300,places=7)
            self.assertTrue(h['segments'])
            self.assertFalse(h['wall_overrun_axes'])
            self.assertIn('physical',h['material_warning'])
        self.assertAlmostEqual(self.alt['hdmi_ribbon']['routed_length_mm'],300,places=7)
        self.assertFalse(self.r['hdmi_200_rejected']['selected'])
        self.assertIn('0.011286',self.r['hdmi_200_rejected']['reason'])

    def test_fps_has_two_wires_and_full_extra_housing(self):
        fps=self.r['signal_geometry']['fps']
        self.assertAlmostEqual(fps['lead_200']['modeled_wire_length_mm'],200,places=7)
        self.assertAlmostEqual(fps['pigtail_50']['modeled_wire_length_mm'],50,places=7)
        self.assertAlmostEqual(fps['modeled_flexible_wire_total_mm'],250,places=7)
        self.assertEqual(fps['curve']['rigid_housing_length_mm'],12)
        self.assertEqual(fps['junction']['world_dimensions_mm'],[8,6,12])
        for key in ['lead_straight_before_near_face_mm','pigtail_straight_after_far_face_mm']:
            self.assertGreaterEqual(fps['junction'][key],3)
        self.assertEqual(len(next(x for x in self.r['routes'] if x['id']=='fps_lead')['wire_parts']),3)

    def test_two_run_cores_are_not_one_averaged_wire(self):
        cores=self.r['signal_geometry']['run_cores']
        self.assertEqual(len(cores),2)
        for c in cores:
            self.assertAlmostEqual(c['complete_modeled_length_mm'],250,places=7)
            self.assertFalse(c['curve']['errors'])
        self.assertNotEqual(cores[0]['curve']['sampled_centerline'],cores[1]['curve']['sampled_centerline'])

    def test_power_budget_and_root_fuse_semantics(self):
        p=self.r['power_geometry']
        for c in p['cores']:
            self.assertAlmostEqual(c['modeled_length_mm'],270,places=7)
            self.assertGreater(c['unmodeled_root_joint_allowance_mm'],0)
            self.assertIn('NOT a passed',c['root_warning'])
            self.assertFalse(c['wall_overrun_points'])
            self.assertEqual(c['minimum_round_bend_radius_mm'],8)
        self.assertEqual(p['cores'][0]['rigid_inline_zone_mm'],20)
        self.assertEqual(p['cores'][1]['rigid_inline_zone_mm'],0)
        self.assertEqual(len(p['cores'][0]['flexible_wire_parts']),2)
        self.assertEqual(p['fuse']['far_lead_station_mm'],24)
        self.assertLessEqual(p['fuse']['far_lead_station_mm'],p['fuse']['proximity_limit_mm'])
        self.assertAlmostEqual(97.5-p['cores'][0]['xz_loop_top_z']-1.6,.9502590069,places=7)
        self.assertLess(p['electrical']['estimated_60c_copper_drop_v'],.15)
        self.assertIn('hard hot-load',p['electrical']['gate'])

    def test_frozen_mechanical_geometry_unchanged(self):
        p=self.r['power_geometry'];ref=p['mechanical_snapshot']
        path=Path(routes.__file__).parent/ref['path']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),ref['sha256'])
        old=json.loads(read_text(path))
        for key in ['junction_center','junction_yaw_deg','junction_pitch_deg','fuse']:
            self.assertEqual(p[key],old[key])
        # FP-15 correction (FIX-LOG 'D2 FP-15 test_routes_source'; proof: tests/test_routes_source_fix.py): the poses are
        # recomputed with sin/cos; the frozen JSON holds correctly rounded values and some platforms' libm returns the
        # neighbouring double, and the difference propagates. Same structure, strings and ints; every float within TOL_MM.
        assert_same_within_tol(self,p['rigid_service_poses'],old['rigid_service_poses'])
        assert_same_within_tol(self,p['cores'][1]['local_points'],old['cores'][1]['local_points'])
        self.assertEqual(len(p['cores']),len(old['cores']))
        for c,oc in zip(p['cores'],old['cores']):
            # same selection rule as before (z < 5) on both sides; the selected points then compared within TOL_MM
            assert_same_within_tol(self,[x for x in c['local_points'] if x[2]<5],[x for x in oc['local_points'] if x[2]<5])

    def test_service_is_not_waived(self):
        self.assertIn('BLOCKED',self.r['status'])
        service={x['id']:x for x in self.r['service_envelopes']}
        self.assertIn('before any body opening',service['carrier_out']['mandatory_first_precondition'])
        self.assertIn('STOP',service['panel_mate']['status'])
        self.assertIn('Stack blocks',service['panel_mate']['status'])
        self.assertIn('STOP',service['xt30_service']['status'])
        self.assertIn('Flexible',self.r['power_geometry']['rigid_service_poses'][-1]['note'])
        self.assertTrue(self.r['source_sha256'])

    def test_radius_never_reduced_to_fit(self):
        bad=routes.rounded_path([[0,0,0],[2,0,0],[2,2,0]],3)
        self.assertEqual(bad['status'],'blocked')
        self.assertEqual(bad['centerline_radius_mm'],3)
        self.assertIsNone(bad['rounded_length_mm'])
        good=routes.rounded_path([[0,0,0],[10,0,0],[10,10,0]],3)
        self.assertAlmostEqual(good['rounded_length_mm'],14+1.5*math.pi)


if __name__=='__main__':unittest.main()
