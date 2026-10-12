# SPDX-License-Identifier: MIT
"""Review views from the bound coupon STL triangles; no CAD changes or deformation model."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

P = Path(__file__).resolve().parent/'bonded-catch-coupon'
rp = P/'receipt.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads(rp.read_text(encoding='utf-8'))
start = {'receipt.json': sha(rp), **r['files']}
for name, expected in start.items():
    assert sha(P/name) == expected, 'Unbound input: ' + name


def triangles(name):
    data = (P/name).read_bytes()
    n = int(np.frombuffer(data, '<u4', 1, 80)[0])
    rec = np.frombuffer(data, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)
    return rec['v'].astype(float)


def source_frame(tris, pose):
    ax = np.array(pose['rotation_axis'], float)
    ax /= np.linalg.norm(ax)
    angle = np.deg2rad(pose['angle_deg'])
    c, s = np.cos(angle), np.sin(angle)
    x, y, z = ax
    K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    R = c*np.eye(3) + (1-c)*np.outer(ax, ax) + s*K
    return (tris-np.array(pose['translation_mm'])) @ R


host_p, insert_p = triangles('catch-host-coupon.stl'), triangles('catch-insert.stl')
host_r, insert_r = r['parts']
host = source_frame(host_p, host_r)
insert = source_frame(insert_p, insert_r['production_print_pose'])
fig = plt.figure(figsize=(12, 9), facecolor='white')
fig.suptitle('Bonded catch local joint study', fontsize=18, x=.055, y=.975, ha='left', fontweight='bold')
fig.text(.055, .939, 'Source-bound geometry only. No print, adhesive or whole-tub torque qualification.', fontsize=11, color='#444444')
views = [
    ('Nominal source assembly', host, insert, (-23, -53)),
    ('Opposite view of the local joint', host, insert, (12, 137)),
    ('Exploded for inspection only', host, insert+[-8, 23, -10], (-17, -58)),
    ('Production layer directions preserved', host_p, insert_p+[29, 5, 0], (24, -57)),
]
for i, (title, h, ins, camera) in enumerate(views, 1):
    ax = fig.add_subplot(2, 2, i, projection='3d')
    for tris, color in ((h, '#8297a5'), (ins, '#d78538')):
        ax.add_collection3d(Poly3DCollection(tris, facecolors=color, edgecolors='#344653', linewidths=.07, alpha=1))
    points = np.concatenate([h.reshape(-1, 3), ins.reshape(-1, 3)])
    lo, hi = points.min(0), points.max(0)
    pad = max(hi-lo)*.05
    ax.set_xlim(lo[0]-pad, hi[0]+pad)
    ax.set_ylim(lo[1]-pad, hi[1]+pad)
    ax.set_zlim(lo[2]-pad, hi[2]+pad)
    ax.set_box_aspect(hi-lo+2*pad)
    ax.view_init(elev=camera[0], azim=camera[1])
    ax.set_title(title, fontsize=11, pad=3, loc='left')
    ax.set_axis_off()
dims = lambda part: ' x '.join(f'{v:.1f}' for v in part['mesh']['print_dimensions_mm'])
fig.text(.055, .045, f'Blue-gray: cropped host, {dims(host_r)} mm as printed. Orange: exact production insert, {dims(insert_r)} mm.', fontsize=10)
fig.text(.055, .021, 'Cropped boundaries and the fixture change stiffness. Exploded placement is illustrative; no deformation is shown.', fontsize=9, color='#444444')
fig.subplots_adjust(left=.025, right=.985, bottom=.075, top=.90, wspace=.02, hspace=.11)
output = P/'coupon-review.png'
fig.savefig(output, dpi=160, facecolor='white')
plt.close(fig)
assert all(sha(P/name) == expected for name, expected in start.items()), 'Input changed during rendering'
receipt = {'manifest_sha256': r['manifest_sha256'], 'geometry_receipt_sha256': start['receipt.json'],
           'input_sha256': start, 'renderer_sha256': sha(Path(__file__)), 'output': output.name,
           'output_sha256': sha(output), 'visual_review': 'pending image inspection', 'physical_qualified': False}
(P/'review-render-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8', newline='\n')
print(output)
