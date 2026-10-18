"""Exact local power-blocker contacts; no design mutations."""
import sys,pickle,json,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
from shapely.geometry import Point,box
from shapely.ops import unary_union
NET='/motherboard_do/DOB_FIELD_3V3';U='75409711-7adb-4e55-b9ea-c36978361c51'
def main():
 out=HERE/'c10036-supply-blocker-diagnostic-r10.json';assert not out.exists();r=FP/'local-and-b5-return-audit-r25';g=pickle.loads(A.read(r/'geometry.pkl'));t=next(t for t in g['tracks'] if t['uuid']==U);body=L.body(t);rec,trees=F.build(g,nets={NET});contact=[];local=[]
 for q in rec['B.Cu']:
  if q['uuid']==U:continue
  if body.distance(q['shape'])<.000002:contact.append({k:q[k] for k in q if k not in('shape','key')}|{'distance_mm':body.distance(q['shape']),'intersection_area_mm2':body.intersection(q['shape']).area,'bounds':q['shape'].bounds})
 for q in g['tracks']:
  if q['layer']=='B.Cu' and L.body(q).intersects(box(63,92,69,97)):local.append(q)
 pads=[{k:p[k] for k in p if k not in('layers','hole')} for p in g['pads'] if L.norm(p['net'])==NET and any(s.distance(body)<.000002 for s in L.poly(p['layers'].get('B.Cu',[])))]
 rootgroups=F.graph(g,NET);group=next(xs for xs in rootgroups if any(q['uuid']==U for q in xs));group_pads=sorted({(q['ref'],q['pin']) for q in group if q['kind']=='pad'})
 raw= {'exact_blocking_track':t,'B_same_net_contacts':contact,'same_net_contact_pads':pads,'source_group_pad_ids':group_pads,'local_B_tracks':local,'read_files_sha256':A.READS};out.write_text(json.dumps(raw,indent=1)+'\n');print(json.dumps(raw),flush=True)
if __name__=='__main__':main()


