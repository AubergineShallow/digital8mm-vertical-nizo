"""Compose unretouched CAD renders into a labeled engineering comparison."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';out=P/'vent-study';font=P.parent/'fonts/DejaVuSans.ttf';bold=P.parent/'fonts/DejaVuSans-Bold.ttf'
cols=[('Reviewed vertical checkpoint','56 mm body / 831 g estimate',out/'reviewed-export18-renders'),('Visible angled trial / not selected','59 mm body / 871 g estimate',out/'angled-channel-trial/renders'),('Selected exterior plenum','63.6 mm body / 864 g estimate',D/'renders')]
w=2400;canvas=Image.new('RGB',(w,1490),'#f4f3ef');draw=ImageDraw.Draw(canvas)
def txt(x,y,s,size=24,heavy=False,color='#243437'):draw.text((x,y),s,font=ImageFont.truetype(str(bold if heavy else font),size),fill=color)
txt(34,22,'Concealed ventilation / actual CAD comparison',38,True)
txt(34,72,'Nine production printed parts. Geometry only; cooling, printing and full service remain unqualified.',24)
receipts=[]
for col,(title,sub,folder) in enumerate(cols):
 x=col*800;txt(x+24,122,title,25,True);txt(x+24,157,sub,22)
 for row,view in enumerate(['vent_side','vent_front']):
  f=folder/(view+'.png');im=Image.open(f).convert('RGB');im.thumbnail((780,607),Image.Resampling.LANCZOS);canvas.paste(im,(x+(800-im.width)//2,195+row*610));receipts.append(dict(file=str(f.relative_to(P)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
txt(34,1428,'Broad-side grille concealed. Front/rear edge openings remain visible; the central side aperture is CSI service access.',23)
f=out/'D2-concealed-vent-comparison.png';canvas.save(f)
(out/'render-comparison-receipt.json').write_text(json.dumps(dict(output=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),sources=receipts,mechanical_manifest_sha256=hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),physical_qualified=False),indent=2))
print(f)
