from pathlib import Path
import json,hashlib
import pcbnew as p
R=Path(__file__).resolve().parent;SRC=R.parent/'r0_3'
parts=json.loads((SRC/'parts.json').read_text(encoding='utf-8'))['parts'];geo={}
def box(b):return [p.ToMM(b.GetLeft()),p.ToMM(b.GetTop()),p.ToMM(b.GetRight()),p.ToMM(b.GetBottom())]
for ref,part in parts.items():
 lib,name=part['footprint'].split(':');folder=SRC/(lib+'.pretty')
 if not folder.exists():folder=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')
 fp=p.FootprintLoad(str(folder),name);assert fp,ref
 bb=[box(g.GetBoundingBox()) for g in fp.GraphicalItems() if g.GetLayer()==p.F_CrtYd]
 assert bb,ref
 b=[min(v[0] for v in bb),min(v[1] for v in bb),max(v[2] for v in bb),max(v[3] for v in bb)]
 geo[ref]={'courtyard':b,'area_mm2':(b[2]-b[0])*(b[3]-b[1]),'footprint':part['footprint'],'source_sha256':hashlib.sha256((folder/(name+'.kicad_mod')).read_bytes()).hexdigest(),
 'pads':[{'pin':v.GetNumber(),'box':box(v.GetBoundingBox()),'drill':p.ToMM(v.GetDrillSizeX()),'xy':[p.ToMM(v.GetPosition().x),p.ToMM(v.GetPosition().y)]} for v in fp.Pads()]}
(R/'placement-geometry.json').write_text(json.dumps(geo,indent=2)+'\n',encoding='utf-8')
print('courtyard area by ref:')
for ref in sorted(geo,key=lambda n:-geo[n]['area_mm2']):
 b=geo[ref]['courtyard'];print(ref,round(b[2]-b[0],3),round(b[3]-b[1],3),round(geo[ref]['area_mm2'],3))
print('Total top courtyard area',sum(v['area_mm2'] for n,v in geo.items() if n not in ('J1','J2')))
