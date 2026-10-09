"""Bind isolated port correction to source shapes and all four inherited holes."""
from pathlib import Path
import hashlib,json,math,sys
import cadquery as cq
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path[:0]=[str(ROOT),str(ROOT.parent)]
import official_pi5_geometry as G
import official_pi5_csi as C
import layout as L
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def contains(outer,inner):return all(outer[i]<=inner[i]+1e-6 and outer[i+1]>=inner[i+1]-1e-6 for i in (0,2,4))
def bounds(b):return [v for a in 'xyz' for v in b[a]]
meta=json.loads((G.SOURCE/'connector-extraction.json').read_text());registered=[]
local_points=[[x-28,y+39.3] for x,y in L.PI['holes']]
for h in meta['main_hole_registration']:
 p=h['candidate_xz'];target=min(local_points,key=lambda q:math.dist(p,q));registered.append(dict(source_candidate_xz=p,inherited_candidate_xz=target,residual_mm=math.dist(p,target)))
assert max(h['residual_mm'] for h in registered)<1e-8
features={}
nom=G.feature_envelopes();bracket=G.feature_envelopes(True)
for name,row in nom.items():
 native=G.SOURCE/(name+'-native.step')
 if not native.exists():native=G.SOURCE/('port-edge-leaf-'+str(row['source_leaf_index'])+'.step')
 s=cq.importers.importStep(str(native)).val();placed=C.place(s)
 assert contains(bounds(row['box']),bb(placed)),name
 assert contains(bounds(bracket[name]['box']),bb(C.place(s,.03,18.5))),name
 assert contains(bounds(bracket[name]['box']),bb(C.place(s,1.306,20.1))),name
 features[name]={k:v for k,v in row.items() if k!='shape'}
 features[name]['bracket_box']=bracket[name]['box'];features[name]['exact_native_file_sha256']=digest(native)
head=G.usb2_upper_head_reservation();headb=G.usb2_upper_head_reservation(True)
assert math.isclose(head['box']['x'][1]-head['box']['x'][0],31,abs_tol=1e-9)
assert math.isclose(head['box']['z'][1]-head['box']['z'][0],15.5,abs_tol=1e-9)
assert math.isclose(head['box']['y'][1]-head['box']['y'][0],9.8,abs_tol=1e-9)
upper_source_window=[11.36600076793,16.48600076744];lower_source_window=[2.786000767444,7.906000766601]
assert abs(sum(upper_source_window)/2-G.USB2_UPPER_NATIVE_CENTRE[2])<1e-6
assert abs(sum(lower_source_window)/2-G.USB2_LOWER_NATIVE_CENTRE[2])<1e-6
pcb=G.candidate_pcb();expected_pcb_volume=85*56*1.6-math.pi*(4*1.35**2+2*1.55**2)*1.6
assert pcb.isValid() and len(pcb.Solids())==1
assert abs(pcb.Volume()-expected_pcb_volume)<1e-6
report=dict(status='pass',four_main_holes=registered,max_main_hole_residual_mm=max(h['residual_mm'] for h in registered),
 transform=G.provenance()['nominal_matrix'],features=features,csi_latches=G.csi_latch_bounds(),cooler_mount_axes=G.cooler_mount_axes(),
 usb2_upper_head=head,usb2_upper_head_with_registration_bracket=headb,
 usb2_axis_evidence=dict(section_file='official-fpc-sources/usb-opening-sections.json',upper_shell_window_native_z=upper_source_window,lower_shell_window_native_z=lower_source_window,scope='Geometric window centre, not a measured cable-head or engagement datum'),
 usb3_upper_window_candidate=C.native_to_candidate_point(G.USB3_UPPER_NATIVE_CENTRE),
 storage_translation_mm=[0,G.STORAGE_DY,G.STORAGE_DZ],
 pcb=dict(bbox_mm=bb(pcb),volume_mm3=pcb.Volume(),hole_count=6,kit_thickness_mm=1.6,source_datum='Inherited kit underside remains fixed; fourØ2.7 main holes plus two sourceØ3.1 cooler holes'),
 source_sha256={str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'official_pi5_geometry.py',ROOT/'official_pi5_csi.py',G.SOURCE/'connector-extraction.json',G.SOURCE/'port-landmarks.json',G.SOURCE/'usb-opening-sections.json']},
 provenance=G.provenance(),physical_qualified=False)
(P/'official-pi5-geometry-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(status='pass',max_main_hole_residual_mm=report['max_main_hole_residual_mm'],validated_features=list(features),usb2_upper_head=head['box'])),flush=True)
