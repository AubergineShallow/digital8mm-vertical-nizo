"""Read vendor STEP files only; no D2 geometry imports or modifications."""
import hashlib
import json
import math
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
results = {}
for name in ('430200201', '430250200'):
    path = HERE / 'sources' / (name + '.stp')
    shape = cq.importers.importStep(str(path)).val()
    b = shape.BoundingBox()
    results[name] = {
        'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'valid': shape.isValid(),
        'solids': len(shape.Solids()),
        'vendor_axes_bbox_mm': [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],
        'vendor_axes_size_mm': [b.xlen,b.ylen,b.zlen],
        'nominal_solid_volume_mm3': shape.Volume(),
        'scope': 'Nominal manufacturer housing STEP only, no tolerance, contact, wire, latch actuation, or device fit qualification',
    }
out = HERE / 'vendor-model-bounds.json'
out.write_text(json.dumps(results, indent=2) + '\n')
print(out)
print(json.dumps(results, indent=2))

# Bounded arithmetic only. This does not load the D2 assembly or form a mated
# connector; actual polarization/registration, tolerances and obstacles stay open.
reserve = [[-33.,-9.],[-24.,-7.],[15.,39.5]]
center = [(a+b)/2 for a,b in reserve]
length = 24.77  # Manufacturer housing drawing, nominal mated rear-to-rear length.
width = max(v['vendor_axes_size_mm'][0] for v in results.values())
# Deliberately cover either sign of the vendor transverse Z extents rather than
# pretend the unmated models have already been registered into a physical pair.
cross_height = 2*max(abs(v['vendor_axes_bbox_mm'][i])
                     for v in results.values() for i in (4,5))
projection = (length+width)/math.sqrt(2)
housing_box = [[center[0]-projection/2,center[0]+projection/2],
               [center[1]-cross_height/2,center[1]+cross_height/2],
               [center[2]-projection/2,center[2]+projection/2]]
axis = [1/math.sqrt(2),0.,1/math.sqrt(2)]
root_ends = [[center[i]+sign*(length/2+12.7)*axis[i] for i in range(3)]
             for sign in (-1,1)]
assessment = {
    'scope':'ARITHMETIC ONLY, NO D2 FIT PASS; no actual mated registration, tolerance, latch, wire sweep or obstacle check',
    'prior_clear_reserve_mm':reserve,
    'reserve_size_mm':[b-a for a,b in reserve],
    'axis_aligned_nominal_mated_length_fits':False,
    'nominal_study_box_local_mm':{'width':width,'cross_height':cross_height,'length':length},
    'cross_height_basis':'2 x largest absolute vendor Z extent; covers either sign before actual cross-datum registration',
    'nominal_study_center_mm':center,
    'nominal_study_mating_axis':axis,
    'rotation_description':'45 degrees in world XZ; local transverse width in XZ, transverse height along Y',
    'nominal_projected_housing_box_mm':housing_box,
    'per_side_arithmetic_reserve_margin_mm':[(b-a-(d-c))/2 for (a,b),(c,d) in zip(reserve,housing_box)],
    'free_root_length_each_mm':12.7,
    'free_root_centerline_outer_ends_mm':root_ends,
    'root_outer_ends_inside_prior_clear_reserve':False,
    'root_scope':'Each root represents two separated cores; listed positions are pair-axis stations only. Wire radius and individual 3 mm centerline offsets are not included.',
}
(HERE/'reserve-arithmetic.json').write_text(json.dumps(assessment,indent=2)+'\n')
print(json.dumps(assessment,indent=2))
