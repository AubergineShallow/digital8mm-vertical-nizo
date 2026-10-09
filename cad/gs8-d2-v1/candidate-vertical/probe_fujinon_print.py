import model as M,math,cadquery as cq
L=M.L;L.LENS='fujinon_hf6xa';M.collar_setup();sh=M.printed_collar.build_part(L).val();C=L.COLLAR;t=C['bridge_membrane_t'];seat=C['flange_x'][1]
disks=[M.cyl('x',C['hole_d']/2+.1,seat-t,seat,*C['feet'][k]) for k in C['bolted']]
for clean in (False,True):
 p=sh.fuse(*disks)
 if clean:p=p.clean()
 lost=sh.cut(p);added=p.cut(sh)
 print(clean,'valid',p.isValid(),'solids',len(p.Solids()),'delta',p.Volume()-sh.Volume(),'lost',lost.Volume(),'added',added.Volume(),flush=True)
 for q in lost.Solids():print('LOST',q.Volume(),M.bounds(q),flush=True)
