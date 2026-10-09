# SPDX-License-Identifier: MIT
"""Provisional full-wire FPS access study; no CAD and no physical access approval."""
import math


def build(R, panel_shift=0., junction_shift=0., step=.2):
    if not (0<=panel_shift<=10 and 0<=junction_shift<=5):
        raise ValueError('Study covers only panel+Y0..10 and junction+Y0..5')
    # Conservatively reorient the SAME 6 x 8 x 12 inline pair, with axis -Y.
    # Actual connector polarity, latch side and separating stroke remain gates.
    near=[-133.5,15.1+junction_shift,79.7]
    far=[-133.5,3.1+junction_shift,79.7]
    h=next(h for h in R.header_housings() if h['cable']=='fps_lead')
    root=h['wire_exit']
    branch=R.rounded_path([root,[root[0],-23.4,root[2]],[root[0],-23.4,25]],3.2,3,0,step)
    def lead(top):
        return R.rounded_path([[-82.91,-23.4,25],[-82.91,-23.4,33.5],[-103.5,-23.4,33.5],
            [-103.5,-23.4,top],[-114.5,-23.4,top],[-114.5,-23.4,62.2],[-125,-23.4,62.2],
            [-125,23.3+junction_shift,62.2],[-133.5,23.3+junction_shift,79.7],near],5.2,3,3,step)
    low,high=72.6,96
    for _ in range(64):
        mid=(low+high)/2;c=lead(mid)
        if c['errors']:raise ValueError(c['errors'])
        if c['rounded_length_mm']+branch['rounded_length_mm']>200:high=mid
        else:low=mid
    lc=lead((low+high)/2)
    def short(y):
        return R.rounded_path([far,[-133.5,y,79.7],[-111,y,79.7],[-111,12.2+panel_shift,78]],5.2,3,3,step)
    low,high=-20,far[1]-8.2
    # At minimum outgoing straight and bend, stock must still reach the panel.
    minimum=short(high)
    if minimum['errors'] or minimum['rounded_length_mm']>50+1e-8:
        return dict(status='BLOCKED: short pigtail cannot reach with required tails/radii',panel_shift=panel_shift,junction_shift=junction_shift,minimum_curve=minimum)
    for _ in range(64):
        mid=(low+high)/2;c=short(mid)
        if c['errors']:raise ValueError(c['errors'])
        if c['rounded_length_mm']>50:low=mid
        else:high=mid
    sc=short((low+high)/2)
    box=R.B(-137.5,-129.5,3.1+junction_shift,15.1+junction_shift,76.7,82.7)
    return dict(status='PROVISIONAL SOURCE ACCESS SHAPE; actual connector, printed solids, latch/tool and separation stroke remain gates',
        panel_shift_y_mm=panel_shift,junction_shift_y_mm=junction_shift,
        lead_200=dict(curve=lc,branch=branch,modeled_wire_length_mm=lc['rounded_length_mm']+branch['rounded_length_mm']),
        pigtail_50=dict(curve=sc,modeled_wire_length_mm=sc['rounded_length_mm']),
        wire_parts=[dict(id='fps_header_branch',curve=branch,od_mm=1.6),dict(id='fps_200_main',curve=lc,od_mm=2.6),dict(id='fps_50_pigtail',curve=sc,od_mm=2.6)],
        junction=dict(box=box,source_dimensions_mm=[6,8,12],world_dimensions_mm=[8,12,6],wire_axis=[0,-1,0],near_wire_face=near,far_wire_face=far),
        required_fpc_spare_reservation=R.B(-116.8,-102.1,-21.6,-4.5,64.7,75),
        fpc_note='This relocated volume clears proposed FPS access. It is only a reservation, with width16 oriented mainlyY; actual full developable FPC and guide routing remain unmodeled.',
        proposed_sequence='After independently proven battery isolation, remove panel fasteners. Coordinate panel+Y10mm with inline FPS pair+Y5mm and deploy the explicitly modeled wall loop. Do not pull solely on crimp wires. At this pose the pair is in the upper rear opening; actual tool and unplugging-stroke envelopes still require validation.',
        unproved_steps=['How to support/move the initially enclosed pair without loading wires','PH latch orientation and grip/tool access','Separate male/female full swept bodies and full-wire shapes after electrical disconnect','Final panel removal after disconnection','Printed guide release and complete full-width FPC conflicts'])
