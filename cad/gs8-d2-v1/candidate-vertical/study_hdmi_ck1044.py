"""Freeze a new full-300 mm HDMI hypothesis for the corrected CK1044.

Does not modify a selected route, mechanical source, or previous evidence.
Run with the pinned CAD interpreter. This generator itself does not import CAD.
"""
from cv_io import read_text, rel_posix, write_text
from pathlib import Path
import hashlib, importlib.util, json, math, shutil
import routes as R

P = Path(__file__).resolve().parent
DEST = P / 'routing-snapshots/hdmi-ck1044-clear-20261009-0524'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value): write_text(DEST/name,json.dumps(value, indent=2))

def main():
    DEST.mkdir(exist_ok=False)
    source = read_text(P/'hdmi_routes.py')
    source = source.replace('max(3.0, 5.0-lift/2)', 'max(3.0, 5.5-lift/2)')
    source = source.replace('R5 installed, R3 both-unplugged', 'R5.5 installed, R3 both-unplugged')
    source = source.replace('Full intact300mm compact HDMI material geometry', 'CK1044 pin-clearance study; full intact300mm compact HDMI material geometry')
    write_text(DEST/'hdmi300.py',source)
    spec = importlib.util.spec_from_file_location('hdmi_ck1044', DEST/'hdmi300.py')
    hd = importlib.util.module_from_spec(spec); spec.loader.exec_module(hd)
    r = R.build()
    write('context.json', r)
    obs = [o for o in r['obstacles'] if o['id'] != 'switch_1824']
    def cyl(name, x, z, radius, y0, y1):
        obs.append(dict(id=name, box=R.B(x-radius,x+radius,y0,y1,z-radius,z+radius),
                        primitive=dict(type='cylinder_y',center_xz=[x,z],radius=radius)))
    cyl('corrected_ck1044_body',-111,80,13.75,11.1,25.2)
    for pin in range(1,13):
        angle=math.radians(255-30*(pin-1))
        cyl('corrected_ck1044_pin_'+str(pin),-111+11.1*math.cos(angle),80+11.1*math.sin(angle),.85,7.1,11.1)
    for mirror in (-1,1):
        cyl('corrected_ck1044_A_mirror_'+str(mirror),-111+mirror*3.85*math.cos(math.radians(225)),80+3.85*math.sin(math.radians(225)),.85,7.1,11.1)
    data=json.loads(read_text(P/'routing-snapshots/hdmi-300-exact-input/input.json'))
    for key,lift,drop in [('hdmi_installed',0,0),('hdmi_premate',0,6),('hdmi_both_unplugged',6,6)]:
        data[key]=hd.compact_300_service(lift,drop,obs)
    data['revision']='hdmi-ck1044-clear-20261009-0524'
    data['provenance']=dict(status='Separate unadopted hypothesis; all physical gates open',
        change='Natural U radius 5.5 mm installed, decreasing to 3 mm; two top rows rise 1 mm while R3 miter and R5 post bends remain. Left turn position solves exact 300 mm material length.',
        previous_input_sha256=digest(P/'routing-snapshots/hdmi-300-exact-input/input.json'),
        mechanical_manifest_sha256=digest(P/'out/compact-kowa_lm6hc/manifest.json'),
        corrected_switch_source='https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf',
        switch_gate='PCB terminal hole-derived radius 0.85 mm remains conservative hypothesis; actual section, common A mirror/clocking and electrical selection unmeasured',
        service_sequence='Remove panel and CK1044 body first; release/stage other crossing looms. EVF drop 0..6, then Pi lift 0..6. Full-width material and both hard heads retained.',
        selected=False,physical_qualified=False)
    write('input.json',data)
    samples=[]
    for stage in ['evf_drop','pi_lift']:
        for j in range(25):
            lift,drop=(0,j/4) if stage=='evf_drop' else (j/4,6)
            shape=hd.compact_300_service(lift,drop,obs)
            samples.append(dict(stage=stage,lift_mm=lift,drop_mm=drop,
                length_mm=shape['routed_length_mm'],remaining_mm=shape['remaining_length_mm'],
                width_mm=shape['width_mm'],fold_radius_mm=shape['fold_radius_mm'],
                loop=shape['explicit_slack_loops'][0],wall_hits=shape['wall_overrun_axes'],
                source_hits=shape['obstacle_overlaps'],segment_count=len(shape['segments'])))
    write('sampled-50-poses.json',samples)
    sources={}
    for name in ['routes.py','hdmi_routes.py','power_routes.py','signal_routes.py','fps_service_routes.py','verify_hdmi.py','verify_fps_access.py','power_geometry.py','study_hdmi_ck1044.py']:
        src=P/name;shutil.copyfile(src,DEST/('source-'+name));sources[rel_posix(src,P.parent)]=digest(src)
    for name in ['layout.py','run_locked.py']:
        src=P.parent/name;shutil.copyfile(src,DEST/('source-'+name));sources[name]=digest(src)
    write('manifest.json',dict(status='Unadopted geometry hypothesis; no release or physical gate closure',
        source_sha256=sources,mechanical_manifest_sha256=data['provenance']['mechanical_manifest_sha256'],
        files={f.name:dict(sha256=digest(f),bytes=f.stat().st_size) for f in DEST.iterdir() if f.is_file()},
        length_error_max_mm=max(abs(s['length_mm']-300) for s in samples),
        wall_failures=sum(bool(s['wall_hits']) for s in samples),source_proxy_failures=sum(bool(s['source_hits']) for s in samples),
        previous_input_preserved=True,physical_qualified=False))
    print(DEST)
    print(json.dumps(dict(samples=len(samples),length_error_max_mm=max(abs(s['length_mm']-300) for s in samples),
        wall_failures=sum(bool(s['wall_hits']) for s in samples),source_proxy_failures=sum(bool(s['source_hits']) for s in samples))))

if __name__=='__main__': main()
