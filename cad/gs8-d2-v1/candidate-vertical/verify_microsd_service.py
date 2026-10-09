"""Expose the rejected closed-panel microSD path; OS-card service requires panel removal or bench access."""
from pathlib import Path
import json,hashlib,time
import cadquery as cq
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';mf=D/'manifest.json';mh=hashlib.sha256(mf.read_bytes()).hexdigest();m=json.loads(mf.read_text())
sh={}
for name in ['microsd','power_button']:
 f=D/'step'/(name+'.step');assert hashlib.sha256(f.read_bytes()).hexdigest()==m['files']['step/'+f.name];sh[name]=cq.importers.importStep(str(f)).val()
hits=[]
for x in range(46):
 q=sh['microsd'].translate(cq.Vector(x,0,0)).intersect(sh['power_button']);v=q.Volume()
 if v>.02:hits.append({'translation_x_mm':x,'overlap_mm3':v})
assert hashlib.sha256(mf.read_bytes()).hexdigest()==mh
r={'manifest_sha256':mh,'verification_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'closed_panel_case':'REJECTED' if hits else 'No modeled switch contact in this limited pair test','sample_step_mm':1,'hits':hits,'selected_procedure':'Install OS microSD on bench before carrier insertion and retain it with the module. Any in-body +X extraction requires the panel and its power switch removed first; the main microsd_out check has only panel-removed scope. Real tool reach remains unqualified.','scope':'This diagnostic tests card versus conservative panel-switch body only, not a complete insertion or socket-mating qualification.','physical_qualified':False}
(D/'microsd-service-dependency.json').write_text(json.dumps(r,indent=2));print(json.dumps({'closed_case':r['closed_panel_case'],'hit_samples':len(hits),'max_overlap_mm3':max((q['overlap_mm3'] for q in hits),default=0),'manifest_sha256':mh}),flush=True)
