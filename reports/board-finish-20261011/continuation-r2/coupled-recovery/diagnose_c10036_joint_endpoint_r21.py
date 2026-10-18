"""Exact endpoint foreign Cu and enforced reservation predicates."""
import sys,pickle,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
sys.path.insert(0,str(HERE));import audit_aux_exact_raw as A
from shapely.geometry import Point
GROUND='/motherboard_do/FIELD_B_0V'
def main():
 out=HERE/'c10036-joint-endpoint-diagnostic-r21.json';assert not out.exists();d=pickle.loads(A.read(HERE/'c10036-joint-reference-bridge-diagnostic-r19.pkl'));g=d['g'];r41=pickle.loads(A.read(FP/'regulated-field-source-feeds-r41/proposed-discrete.pkl'));m={**g,**r41,'pads':[],'zones':[],'shapes':[]};rec,_=F.build(g,layers={'In4.Cu'});rr,_=F.build(m,layers={'In4.Cu'});p=Point(d['old']['b']);rows=[]
 for q in rec['In4.Cu']+rr['In4.Cu']:
  if L.norm(q['net'])==GROUND or q['shape'].distance(p)>1.2:continue
  req=max(.25,.15 if g['domains_normalized'].get(L.norm(q['net']))==g['domains_normalized'][GROUND] else .6)+.025+.005;rows.append({'uuid':q['uuid'],'net':q['net'],'kind':q['kind'],'distance_mm':q['shape'].distance(p),'bridge_radius_max_mm':q['shape'].distance(p)-req,'bounds':q['shape'].bounds})
 res,exc=A.reservations();reserved=[{'name':r['name'],'outline_dist_mm':min(sh.distance(p) for sh in L.poly(r['outline'])),'exempt_nets':sorted(exc.get(r['name'],set())),'raw_record':r} for r in res['keepouts'] if 'In4.Cu' in r['layers'] and any(sh.distance(p)<.8 for sh in L.poly(r['outline']))];report={'endpoint_mm':d['old']['b'],'near_discrete':rows,'near_reservations':reserved,'glegal_point_distance_mm':p.distance(d['glegal']),'glegal_boundary_distance_mm':p.distance(d['glegal'].boundary),'read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
