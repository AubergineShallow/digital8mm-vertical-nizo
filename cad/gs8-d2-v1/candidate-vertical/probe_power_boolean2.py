import cadquery as cq,time,math
import power_geometry as P
print('full ball volume',P.ball((0,0,0),1).Volume(),4*math.pi/3,flush=True)
cuts=P.grip_cuts();print('cutters',len(cuts),[(i,c.isValid(),len(c.Solids())) for i,c in enumerate(cuts) if not c.isValid()],flush=True)
for tol in (1e-6,1e-5,1e-4):
 tool=cuts[0].copy().fuse(*[c.copy() for c in cuts[1:]],tol=tol)
 print('fuzzy tool',tol,tool.isValid(),len(tool.Solids()),tool.Volume(),flush=True)
 if tool.isValid():
  base=cq.importers.importStep('/tmp/oldvalid-base_grip.step').val();s=base.cut(tool)
  print('fuzzy cut',s.isValid(),len(s.Solids()),s.Volume(),flush=True)
  if s.isValid() and len(s.Solids())==1:cq.exporters.export(s,'/tmp/fuzzy-fixed-grip.step')
base=cq.importers.importStep('/tmp/oldvalid-base_grip.step').val();s=base
for i,c in enumerate(cuts):
 t=s.copy().cut(c.copy())
 if not t.isValid():
  print('sequential invalid',i,flush=True);t=s.copy().cut(c.copy(),tol=1e-5);print('retry',t.isValid(),flush=True)
 if not t.isValid():raise ValueError('cut failed')
 s=t
print('sequential final',s.isValid(),len(s.Solids()),s.Volume(),flush=True);cq.exporters.export(s,'/tmp/sequential-fixed-grip.step')
