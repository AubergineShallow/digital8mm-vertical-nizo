# SPDX-License-Identifier: MIT
"""Vendor-datum review contract. No inherited camera fit or physical passes."""
from pathlib import Path
import hashlib
import json
import math
import os
import re

ROOT = Path(__file__).resolve().parent
PROFILE_ID = 'waveshare-imx296-global-camera-a-sku32501'
# The vendor drawing is Waveshare's copyrighted artwork. It is NOT stored in the public
# repository (fix pass 2026-10-13, review R-03): only its source URL and SHA-256 are.
# A reviewer who downloads it keeps it at this git-ignored path, or names it in the
# environment variable below; the hash is then verified exactly as before.
DRAWING_LOCAL = 'evidence/local/vendor-drawing.jpg'
DRAWING_ENV = 'GS8_WAVESHARE_DRAWING'
_HEX64 = re.compile(r'[0-9a-f]{64}')


def drawing_path(drawing=None):
    """Return the local drawing path to verify, or None when no local copy is available."""
    if drawing is not None:
        return Path(drawing)
    env = os.environ.get(DRAWING_ENV)
    if env:
        return Path(env)
    local = ROOT / DRAWING_LOCAL
    return local if local.is_file() else None


def drawing_verified(p, drawing=None):
    """True when a local drawing copy exists and its SHA-256 equals the profile pin.

    A copy that is present but differs raises; an absent copy returns False and keeps
    hold WS-09 open. Absence never passes as verification."""
    path = drawing_path(drawing)
    if path is None:
        return False
    if not path.is_file():
        raise ValueError(f'vendor drawing not found at the named path: {path.name}')
    if hashlib.sha256(path.read_bytes()).hexdigest() != p['drawing_sha256']:
        raise ValueError('vendor drawing hash mismatch')
    return True


def load_profile(path=None, drawing=None):
    value = json.loads(Path(path or ROOT / 'camera-profile.json').read_text(encoding='utf-8'))
    validate_profile(value, drawing)
    return value


def validate_profile(p, drawing=None):
    if type(p.get('schema_version')) is not int or p.get('schema_version') != 1 or p.get('profile_id') != PROFILE_ID or p.get('sku') != '32501':
        raise ValueError('wrong camera profile; official-camera evidence is not interchangeable')
    dims = p.get('vendor_dimensions_mm', {})
    expected = {'pcb_side': 38.0, 'pcb_side_tolerance': .2, 'pcb_thickness': 1.6,
                'mount_hole_spacing': 30.0, 'mount_hole_diameter': 2.5,
                'housing_outer_diameter': 28.5, 'front_opening_diameter': 25.0,
                'pcb_front_to_housing_front': 12.5,
                'pcb_front_to_housing_front_tolerance': .2,
                'rear_connector_projection': 2.5, 'rear_housing_attachment_spacing': 20.0}
    if dims != expected:
        raise ValueError('vendor-dimension contract changed; re-review drawing before changing CAD')
    for k in ('bfar_ring', 'official_lock_tab', 'tripod_block_removal_required'):
        if p['features'].get(k) is not False:
            raise ValueError(f'official-camera feature cannot be inherited: {k}')
    if {k: p['optics'].get(k) for k in ('sensor', 'colour', 'width', 'height', 'raw_bit_depth')} != {
            'sensor': 'imx296', 'colour': True, 'width': 1456, 'height': 1088, 'raw_bit_depth': 10}:
        raise ValueError('software sensor mode contract must remain full-colour IMX296 RAW10')
    if p['electrical'].get('pi5_port') != 'CAM1' or p['electrical'].get('dtoverlay') != 'imx296':
        raise ValueError('selected setup profile is CAM1 imx296; CAM0 requires explicit profile revision')
    if p['electrical'].get('camera_auto_detect') != 0 or p['electrical'].get('eeprom_dependency') is not False:
        raise ValueError('manual overlay setup has no EEPROM dependency')
    for key in ('cable_length_mm', 'connector_latch_sweep_mm', 'minimum_bend_radius_mm'):
        if p['electrical'].get(key) is not None:
            raise ValueError(f'{key} needs measured cable/connector evidence')
    if p['electrical'].get('cable_contact_orientation_confirmed') is not False:
        raise ValueError('contact orientation has not been measured')
    q = p['qualification']
    for k in ('production_release', 'physical_gate_inheritance', 'official_bfar_test_inheritance',
              'qt_clearance_gate_relaxed', 'fps_48_54_measured', 'manual_controls_measured', 'dng_roundtrip_measured'):
        if q.get(k) is not False:
            raise ValueError(f'no measured evidence supports qualification flag: {k}')
    if q.get('official_pi5_active_cooler_retained') is not True:
        raise ValueError('official Pi5 Active Cooler must be retained')
    for k in ('hardware_fit_validated', 'fastener_addition_approved', 'exterior_change_approved',
              'board_component_keepouts_measured'):
        if p['mechanical'].get(k) is not False:
            raise ValueError(f'unapproved/unmeasured mechanical claim: {k}')
    if p['optics'].get('optical_backfocus_measured') is not False:
        raise ValueError('optical backfocus has no measured evidence')
    for k in ('pcb_front_to_sensor_mm', 'pcb_front_to_c_mount_shoulder_mm',
              'adapter_diameter_mm', 'adapter_face_to_face_mm', 'lens_thread_engagement_mm'):
        if p['optics'].get(k) is not None:
            raise ValueError(f'{k} needs a separately reviewed measured-parts revision')
    if p['mechanical'].get('installed_pcb_front_x_mm') is not None:
        raise ValueError('installed pose is blocked by unknown shoulder datum')
    if type(p.get('drawing_sha256')) is not str or not _HEX64.fullmatch(p['drawing_sha256']):
        raise ValueError('drawing_sha256 must be a lowercase 64-hex SHA-256 pin')
    if p.get('drawing_redistributed') is not False or p.get('drawing_local_path') != DRAWING_LOCAL:
        raise ValueError('vendor drawing must stay local (R-03): drawing_redistributed false, git-ignored local path')
    if not str(p.get('sources', {}).get('drawing', '')).startswith('https://www.waveshare.com/'):
        raise ValueError('vendor drawing source URL must be recorded')
    drawing_verified(p, drawing)
    return p


def nominal_local_bounds(p):
    d = p['vendor_dimensions_mm']
    h = d['pcb_side'] / 2
    return {'pcb': [-d['pcb_thickness'], 0., -h, h, -h, h],
            'housing_envelope': [0., d['pcb_front_to_housing_front'], -14.25, 14.25, -14.25, 14.25],
            'unlocated_rear_connector_reserve': [-d['pcb_thickness']-d['rear_connector_projection'],
                                                -d['pcb_thickness'], -h, h, -h, h]}


def exploratory_pose(shoulder_to_pcb_front_mm, *, c_shoulder_x_mm=.6):
    """Sensitivity input only; never invent an installed pose or close a gate.

    Caller-provided shoulder distance is not a measured value merely because it
    is numeric. Origin is PCB FRONT, not sensor. Lens/C shoulder stays at the
    baseline design's +0.6 mm; actual optics and lens engagement remain open.
    """
    for v in (shoulder_to_pcb_front_mm, c_shoulder_x_mm):
        if type(v) not in (int, float) or not math.isfinite(v):
            raise ValueError('finite numerical exploratory datum required')
    if shoulder_to_pcb_front_mm <= 0:
        raise ValueError('shoulder-to-PCB distance must be positive')
    x = c_shoulder_x_mm - shoulder_to_pcb_front_mm
    return {'pcb_front_x_mm': x, 'axis_yz_mm': [0., 60.],
            'basis': 'USER-SUPPLIED SENSITIVITY DATUM, NOT MEASUREMENT',
            'installed_pose_approved': False, 'physical_release': False}


def release_status(p, drawing=None):
    validate_profile(p, drawing)
    return {'schema_version': 1, 'profile_id': PROFILE_ID, 'state': 'BLOCKED_REVIEW_STUDY',
            'physical_release': False, 'integrated_assembly_generated': False,
            'official_camera_receipts_applicable': False,
            'adopted_in_official_design': False,
            'retention_option_b_as_drawn': 'REJECTED under J7-R float (see MECHANICAL-REVIEW.md)',
            'vendor_drawing_in_repository': False,
            'holds': {
                'WS-01': 'Measure PCB-front to installed C-mount shoulder and sensor/backfocus; identify adapter seating/thread engagement.',
                'WS-02': 'Approve and validate retention load path, board contact keepouts, enclosure anchor, insertion/removal and warm creep.',
                'WS-03': 'Confirm cable length/pin orientation, camera socket datum/latch/tool sweep, bend radius and complete closed-state/service route.',
                'WS-04': 'Rebuild and independently check actual placed camera, cradle and enclosure; preserve exterior and official Active Cooler.',
                'WS-05': 'Bench qualify both lenses, full colour RAW10, manual controls, 48/54 fps, timing, DNG and sustained recording.',
                'WS-06': 'Every still-applicable original physical gate remains open; strict QT and unrelated known failures remain applicable.',
                'WS-07': 'J7-R float: in the final pose the camera (PCB, housing and anything fastened to it) touches no printed part, and lens torque never passes through the camera housing or PCB. Option B as drawn (PCB carrier anchored to the enclosure while the collar holds the lens) is rejected; any retention must be shown floating/compliant by measured clearance.',
                'WS-08': 'Straight-driver access: every screw of any adopted retention (including the proposed M2 stack) must be drivable with a straight driver along a clear axis in the assembled state (long bits and plugged holes allowed); not yet shown.',
                'WS-09': 'Vendor drawing kept local (R-03): verify a local copy against drawing_sha256 before relying on the profile dimensions; the public repository holds only the URL and hash.',
            }}
