import model,json
m=model.build();r=m['rows']
for k,v in r.items():
 s=v['shape'];print(k,s.isValid(),len(s.Solids()),round(s.Volume(),1),[round(x,2) for x in model.bounds(s)],flush=True)
for a in ['tub','panel','carrier','lens_collar']:
 for b,v in r.items():
  if a==b or (b in ['tub','panel','carrier','lens_collar'] and b<a):continue
  vol=r[a]['shape'].intersect(v['shape']).Volume()
  if vol>.05:print('INTERSECT',a,b,round(vol,3),[round(x,3) for x in model.bounds(r[a]['shape'].intersect(v['shape']))],flush=True)

for a,b in [("tub","panel")]:
 for c in r[a]["shape"].intersect(r[b]["shape"]).Solids():print("DETAIL",a,b,c.Volume(),model.bounds(c),flush=True)
