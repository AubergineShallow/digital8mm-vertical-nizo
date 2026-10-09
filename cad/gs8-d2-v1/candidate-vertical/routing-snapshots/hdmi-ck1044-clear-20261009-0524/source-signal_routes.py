# SPDX-License-Identifier: MIT
"""Source-only signal reconciliation for the 56 mm vertical D2 candidate.

NO CAD imports. This is a blocked geometric proposal, not a manufacturing route.
Use build(the_loaded_routes_module). Does not change routes.py or model.py.
All nominal stock lengths, diameters, source roots, and bend radii stay explicit.
"""
import math

REVISION = 'signal-reconciliation-2026-10-09-v2-rigid-fps-angled-csi'


def _solve_top(make_curve, target, low=35., high=95.):
    for _ in range(64):
        mid=(low+high)/2
        c=make_curve(mid)
        if c['errors']:
            raise ValueError(c['errors'])
        if c['rounded_length_mm']>target:high=mid
        else:low=mid
    return make_curve((low+high)/2)


def _station(points, distance):
    """Polyline station; explicitly approximate, for a proposed junction only."""
    total=0.
    for a,b in zip(points,points[1:]):
        d=math.dist(a,b)
        if total+d>=distance:
            t=(distance-total)/d
            return dict(point=[a[i]+t*(b[i]-a[i]) for i in range(3)],
                        tangent=[(b[i]-a[i])/d for i in range(3)],
                        sampled_station_mm=distance)
        total+=d
    return dict(point=points[-1],sampled_station_mm=total)


def build(R, step=.2):
    hs=R.header_housings(); branches=[]
    # Source-derived housing and root coordinates are unchanged. Pin 6 turns
    # rearward before rising: the old pin-5 and pin-6 upward paths overlap.
    for h in hs:
        if h['cable']=='run_lead':continue  # complete per-core routes below
        root=h['wire_exit'];lane=-23.4
        knots=[root,[root[0],lane,root[2]]]
        knots+=([[-54,lane,root[2]],[-54,lane,25]] if h['id']=='hdr_qt_6' else [[root[0],lane,25]])
        c=R.rounded_path(knots,3.2,3,0,step)
        branches.append(dict(id=h['id'],cable=h['cable'],pins=h['pins'],housing_box=h['box'],
            source_wire_exit=root,od_mm=1.6,curve=c,
            change='Pin 6 turns toward X=-54 before rising to avoid the pin-5 branch' if h['id']=='hdr_qt_6' else 'source root and original branch retained',
            status='ROOT CONTACT AND ACTUAL CORE SECTION UNQUALIFIED; screen against the current dogleg power revision'))
    qt_branches=[b for b in branches if b['cable']=='qt']
    qt_longest=max(b['curve']['rounded_length_mm'] for b in qt_branches)
    qt_x=sum(h['wire_exit'][0] for h in hs if h['cable']=='qt')/4
    def qt_curve(low):
        top=87.5
        return R.rounded_path([[qt_x,-23.4,25],[qt_x,-23.4,top],[-72.5,-23.4,top],
            [-72.5,-23.4,low],[-93.2,-23.4,low],[-93.2,-23.4,65],
            [-93.2,14.8,65],[-85,14.8,77],[-72,14.8,77]],6.4,3,4,step)
    lo,hi=34.,50.
    for _ in range(64):
        mid=(lo+hi)/2;c=qt_curve(mid)
        if c['errors']:raise ValueError(c['errors'])
        if c['rounded_length_mm']>250-qt_longest:lo=mid
        else:hi=mid
    qc=qt_curve((lo+hi)/2)
    qt=dict(id='qt',stock_length_mm=250,od_mm=3.2,minimum_centerline_radius_mm=6.4,
        curve=qc,nominal_longest_breakout_plus_main_mm=qt_longest+qc['rounded_length_mm'],
        nominal_other_branch_remainders_mm={b['id']:250-qc['rounded_length_mm']-b['curve']['rounded_length_mm'] for b in qt_branches},
        status='UPPER ROUTE RECONCILED ONLY; individual branch-to-bundle fan-in and actual QT construction are unmodeled',
        fan_in_gate='Source branches end at their own X/Y coordinates, not the averaged main start. Do not join them by invisible straight jumps. Reserve and measure a real fan-in; re-solve the top-loop height after its exact length is known.',
        section_gate='The main OD3.2 envelope and branch OD1.6 proxies are retained. Four real OD1.6 circular cores cannot fit inside a round OD3.2 bundle (minimum enclosing OD3.863 for a square pack). Measure the actual breakout/core OD and bundle construction; do not shrink the proxy cores or claim a passed merge.',
        final_root_gate='The modeled endpoint is on the socket rear face. Only the local terminal approach may enter that source envelope; connector/root measurement remains required.')
    fps_branch=next(b for b in branches if b['cable']=='fps_lead')
    fps_bl=fps_branch['curve']['rounded_length_mm']
    # A real 12 mm rigid PH-pair housing is ADDITIONAL to 200 + 50 mm
    # of modeled exposed wire. Both wire curves meet its end faces tangentially.
    # Cross-section is the unchanged 6 x 8 mm proxy, oriented 8 in X / 6 in Y.
    def fps_pigtail(far_z):
        return R.rounded_path([[-113,-22,far_z],[-113,-22,70],[-111,-22,78],
            [-111,12.2,78]],5.2,3,3,step)
    lo,hi=55.,65.
    for _ in range(64):
        mid=(lo+hi)/2;c=fps_pigtail(mid)
        if c['errors']:raise ValueError(c['errors'])
        if c['rounded_length_mm']>50:lo=mid
        else:hi=mid
    far_z=(lo+hi)/2;near_z=far_z-12
    fp=fps_pigtail(far_z)
    def fps_curve(top):
        return R.rounded_path([[-82.91,-23.4,25],[-82.91,-23.4,33.5],[-119,-23.4,33.5],
            [-119,-23.4,top],[-102,-23.4,top],[-102,-23.4,38.5],
            [-113,-22,38.5],[-113,-22,near_z]],5.2,3,3,step)
    fc=_solve_top(fps_curve,200-fps_bl,80,95)
    lead_points=fps_branch['curve']['sampled_centerline']+fc['sampled_centerline'][1:]
    axis_points=[[-113.,-22.,near_z+12*j/max(1,math.ceil(12/step))]
                 for j in range(max(1,math.ceil(12/step))+1)]
    assembly_points=lead_points+axis_points[1:]+fp['sampled_centerline'][1:]
    # Compatibility key is an assembly reference spine, NOT a flexible wire
    # through the housing. Consumers must render the full box and two wire parts.
    assembly_curve=dict(sampled_centerline=assembly_points,
        rounded_length_mm=262.,wire_length_mm=250.,rigid_housing_length_mm=12.,
        knots=None,errors=fc['errors']+fp['errors'],centerline_radius_mm=5.2,
        status='ASSEMBLY REFERENCE SPINE: 200 mm wire + 12 mm rigid housing + 50 mm wire; render separate wire_parts and junction.box',
        first_straight_min_mm=3,last_straight_min_mm=3)
    fps=dict(id='fps_lead',stock_length_mm=250,source_lengths_mm=[200,50],od_mm=2.6,
        minimum_centerline_radius_mm=5.2,curve=assembly_curve,breakout=fps_branch,
        lead_200=dict(curve=fc,breakout=fps_branch,complete_sampled_centerline=lead_points,
            modeled_wire_length_mm=fps_bl+fc['rounded_length_mm']),
        pigtail_50=dict(curve=fp,modeled_wire_length_mm=fp['rounded_length_mm']),
        wire_parts=[dict(id='fps_header_branch',curve=fps_branch['curve'],od_mm=1.6),
                    dict(id='fps_200_main',curve=fc,od_mm=2.6),
                    dict(id='fps_50_pigtail',curve=fp,od_mm=2.6)],
        complete_nominal_centerline=assembly_points,nominal_total_mm=262.,
        modeled_flexible_wire_total_mm=fps_bl+fc['rounded_length_mm']+fp['rounded_length_mm'],
        junction=dict(source_proxy_dimensions_mm=[6,8,12],world_dimensions_mm=[8,6,12],
            source_proxy_volume_mm3=576,box=R.B(-117,-109,-25,-19,near_z,far_z),
            near_wire_face=[-113,-22,near_z],far_wire_face=[-113,-22,far_z],
            wire_axis=[0,0,1],rigid_axis_centerline=axis_points,
            lead_straight_before_near_face_mm=near_z-38.5-5.2,
            pigtail_straight_after_far_face_mm=70-far_z-fp['corner_trim_mm'][1],
            wall_clearance_mm=.5,
            status='FULL RIGID SOURCE PROXY PLACED; nominal static source fit only. Actual keyed orientation, latch access, crimp/strain-relief datums, printed guide clearance, and removable mating motion remain unmeasured.',
            length_gate='Exactly 200 and 50 mm are modeled as exposed wire from source roots to the housing end faces. The full 12 mm housing is additional, so the assembly reference path is 262 mm. Verify the purchased length convention and terminal-root measurements before fabrication; no housing length is credited as free wire.'),
        status='NOMINAL STATIC GEOMETRY RECONCILED; exact actual terminal/core section, printed solids, and service access remain open',
        source_root_gate='Source housing/root positions remain unchanged. The original low positive-power return is incompatible; use only the current revised dogleg power geometry and repeat the complete check after any power change.')
    runs=[]
    for name,rx,lane,front,down in [('run_pin37',-87.99,-21.6,-12,-30),('run_pin39',-90.53,-24.3,-14,-32)]:
        h=next(h for h in hs if h['pins']==([37] if name=='run_pin37' else [39]))
        def make(top):
            p=[list(h['wire_exit']),[rx,lane,11.77]]
            # The forward shelf keeps pin37 above the negative return until X=-75.
            p+=([[rx,lane,18.5],[-75,lane,18.5],[-75,lane,4.9]] if name=='run_pin37' else [[rx,lane,4.9]])
            p += [[front,lane,4.9],[front,lane,top],[down,lane,top],[down,lane,12],
                  [down,5.25,12],[down,5.25,-14.2]]
            return R.rounded_path(p,3.2,3,3,step)
        c=_solve_top(make,250,35,80)
        runs.append(dict(id=name,cable='run_lead',pins=h['pins'],stock_length_mm=250,
            od_mm=1.6,minimum_centerline_radius_mm=3.2,source_housing_box=h['box'],curve=c,
            complete_modeled_length_mm=c['rounded_length_mm'],
            status='NOMINAL 250 mm ROUTE; source roots, printed passage, and service deformation remain unqualified. Requires the revised positive-power dogleg.',
            endpoint_gate='RUN roots X=-30 and -32, Y=5.25, Z=-14.2 are a proposed 2 mm spacing about the original center X=-31, not measured pin positions or clocking. Confirm the existing passage and terminal orientation before use.'))
    fpc=R.rounded_path([[-83,-.8,61],[-83,-.8,82],[-33.5,-.8,82],[-33.5,0,43.75],[-28.09,0,43.75]],1,5,4,step)
    j2=R.rounded_path([[-37,4.5,48],[-37,4.5,55],[-30.5,4.5,55],[-30.5,-12,55],
        [-33.8,-12,51],[-33.8,-12,33],[-20,-12,33],[-20,-12,25.5],[-20,-1.4,25.5]],3.2,3,3,step)
    return dict(revision=REVISION,status='BLOCKED SOURCE GEOMETRY; DO NOT FREEZE, CUT, OR CLAIM ASSEMBLY PASS',
        body_inner_y_mm=[-25.5,25.2],body_inner_z_mm=[2.5,97.5],source_headers=hs,
        branches=branches,qt=qt,fps=fps,run_cores=runs,
        fpc=dict(id='fpc',stock_length_mm=200,full_width_mm=16,thickness_allowance_mm=.3,
            curve=fpc,unmodeled_stock_mm=200-fpc['rounded_length_mm'],
            status='PROVISIONAL CENTERLINE ONLY; 16 mm developable shape, stock stow, endpoint clocking, and 4 mm final tail remain unresolved'),
        power_button=dict(id='power_button',stock_length_mm=150,od_mm=1.6,minimum_centerline_radius_mm=3.2,
            curve=j2,unmodeled_stock_mm=150-j2['rounded_length_mm'],
            status='PROVISIONAL CENTERLINE ONLY; actual J2 pads, both wire roots, 2-pin connector, full stock stow, and zero-clearance PCB start are unresolved'),
        required_accommodations=[
            'Requires the revised positive-power dogleg and current 270 mm power storage. The original low positive return crosses FPS/RUN header tails and must not be restored. This module does not modify power geometry.',
            'QT pin 6 turns toward X=-54 before rising instead of overlapping the pin-5 vertical centerline.',
            'QT uses explicit wall-plane storage but its actual fan-in remains open. FPS separately stores exactly 200 and 50 mm of wire with an additional full 12 mm rigid junction. Recompute from measured purchased root datums before fabrication.',
            'QT transverse lane X=-93.2 and wall return X=-72.5 accommodate the specified two-radius angled CSI tool; this does not qualify the wider slot or unmodeled FPC.',
            'RUN uses two separate 250 mm paths with distinct Y lanes and terminal hypotheses; no shared round-wire proxy or hidden common endpoint is used.',
            'Printed open/releasable guides for the new wall routes and low RUN shelf require exact parent-solid checks. No housing or guide redesign is claimed here.'
        ],
        service_staging=[
            'Isolate the battery using a validated grip extraction sequence before body opening. The current power flexible-service motion is not yet validated.',
            'Release QT/FPS panel connections and their open loom guides before any +Y HDMI-head service translation. Record actual release/reconnect access and do not drag a retained signal loom through the HDMI swept volume.',
            'Release the camera FPC at a measured accessible ZIF and release its guides before HDMI service if its full-width/service shape overlaps that volume.',
            'Mate and retain the HDMI assembly first, then reinstall the released signal paths in their listed lanes and close the panel. This is a required proposed staging order, not a passed continuous-motion proof.'
        ],
        csi_tool_access=dict(tips_mm=[[-87,-4,61.5],[-79,-4,61.5]],
            backward_unit_direction=[0,-.9950371902099892,.09950371902099892],
            segments=[dict(start_mm=0,length_mm=15,radius_mm=2),dict(start_mm=15,length_mm=75,radius_mm=4)],
            qt_surface_clearances_mm=[.60001,.90006],
            qualification='Conservative finite-axis capsule screening at dense cable samples; full prescribed tool radii are subtracted. These are nominal static QT-only clearances, not an exact printed-solid, full-width FPC, or latch-motion qualification. Any additional obstruction requires explicit release/parking before access.'),
        check_limits='Source COTS/connector boxes, full installed 300 mm HDMI segments, and complete 270 mm power core samples can be tested against these curves. Endpoint contacts must be reported locally. Printed solids, physical terminations, 16 mm FPC, rigid PH junctions, and service motion are not certified by centerlines.')
