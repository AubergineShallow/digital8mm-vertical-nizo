"""Integral concealed-channel ventilation candidate. Nominal CAD only, no thermal pass.
All added side-wall material lies outside the preserved Y=-25.5 internal datum.
"""
import math
import cadquery as cq
V=cq.Vector
OUTER_Y=-31.0
INNER_Y=-25.5
SIDE_H=4.4
SIDE_Z=(13.5,20.5,27.5,34.5)
FRONT_H=4.8
FRONT_Z=(11.0,18.5,26.0,33.5)
FRONT_BANKS=((-25.5,2.0),(8.0,11.5))

def side_channel(x0,x1,z):
    # 45-degree downward/outward passage. True normal aperture is H/sqrt(2).
    a,b=OUTER_Y-.1,INNER_Y+.1
    p=[(a,z+a-INNER_Y),(b,z+b-INNER_Y),(b,z+b-INNER_Y+SIDE_H),(a,z+a-INNER_Y+SIDE_H)]
    w=cq.Wire.makePolygon([V(x0,y,zz) for y,zz in p]+[V(x0,*p[0])])
    return cq.Solid.extrudeLinear(w,[],V(x1-x0,0,0))

def front_channel(y0,y1,z):
    # Existing5.2mm front wall retained; no projection toward lens/collar tools.
    a,b=-5.3,.1
    p=[(a,z-(a+5.2)),(b,z-(b+5.2)),(b,z-(b+5.2)+FRONT_H),(a,z-(a+5.2)+FRONT_H)]
    w=cq.Wire.makePolygon([V(x,y0,zz) for x,zz in p]+[V(p[0][0],y0,p[0][1])])
    return cq.Solid.extrudeLinear(w,[],V(0,y1-y0,0))

def inlet_cuts():return [side_channel(-103,-68,z) for z in SIDE_Z]
def side_exhaust_cuts():return [side_channel(-40,-32,z) for z in SIDE_Z]
def front_exhaust_cuts():return [front_channel(a,b,z) for z in FRONT_Z for a,b in FRONT_BANKS]
def metadata():
    return dict(revision='concealed-channel trial1',outer_side_y_mm=OUTER_Y,inner_side_y_mm=INNER_Y,
        side_wall_mm=INNER_Y-OUTER_Y,side_projected_height_mm=SIDE_H,side_pitch_mm=7,
        intake_normal_throat_mm2=4*35*SIDE_H/math.sqrt(2),side_exhaust_normal_throat_mm2=4*8*SIDE_H/math.sqrt(2),
        front_normal_throat_mm2=4*sum(b-a for a,b in FRONT_BANKS)*FRONT_H/math.sqrt(2),
        side_normal_web_mm=(7-SIDE_H)/math.sqrt(2),front_normal_web_mm=(7.5-FRONT_H)/math.sqrt(2),
        side_normal_sight_overlap_mm=INNER_Y-OUTER_Y-SIDE_H,front_normal_sight_overlap_mm=5.2-FRONT_H,
        side_path_length_mm=(INNER_Y-OUTER_Y)*math.sqrt(2),front_path_length_mm=5.2*math.sqrt(2),
        csi_access_open_area_mm2=12*27-(4-math.pi),csi_unchanged_straight_access=True,
        panel_previous_relief='Four blind grooves with0.2mm retained floors, not through-vents; removed for plain2.8mm panel',
        airflow='Wall passages and existing separating baffle only. CSI remains an unsealed bypass. Equal gross throat is not equal flow or cooling.',
        physical_qualified=False,remaining=['Actual cooler profile/registration','Fan operating point and duct pressure loss','Hand occlusion','Printed channel and bridge coupons','Real CSI latch/jaw access','All56 inherited gates andM1'])
