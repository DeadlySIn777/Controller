"""Audit frozen interim return planes against true copper radii and exact peer planes."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 src=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
 assert src.is_relative_to(H) and out.is_relative_to(H) and not out.exists()
 r=json.loads((src/'receipt.json').read_bytes());p=src/'proposed-zones.pkl';c=src/'checkpoint.json'
 assert sha(p)==r['proposed_zones_sha256'] and sha(c)==r['checkpoint_sha256']
 parent=H/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl';assert sha(parent)==r['parent_model_sha256']
 old,h,b,parentzones,current=pickle.loads(parent.read_bytes());zones=pickle.loads(p.read_bytes());out.mkdir()
 records,trees=F.build({**h,'zones':[]});errors=[];pairs=[];checks=0
 def need(raw,other,local=.15):return max(.15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(other)] else .6,local)+.025
 for z in zones:
  for i in trees[z['layer']].query(z['shape'].buffer(1.5),predicate='intersects'):
   q=records[z['layer']][int(i)]
   if q['net']==z['net']:continue
   checks+=1
   if q['kind']=='via':
    v=q['source'];d=z['shape'].distance(Point(v['x'],v['y']))-v['d']/2
   elif q['kind']=='track':
    t=q['source'];d=z['shape'].distance(LineString([t['a'],t['b']]))-t['w']/2
   else:d=z['shape'].distance(q['shape'])
   required=need(z['net'],q['net'],float(z.get('clearance_mm',.15)))
   if d<required-1e-9:errors.append({'zone':z['uuid'],'other_uuid':q['uuid'],'kind':q['kind'],'layer':z['layer'],'analytic_gap_mm':d,'required_mm':required})
  for q in parentzones+zones:
   if z['layer']!=q['layer']or z['net']==q['net']:continue
   required=need(z['net'],q['net'],max(float(z.get('clearance_mm',.15)),float(q.get('clearance_mm',.15))))
   d=z['shape'].distance(q['shape'])
   if d<required-1e-9:pairs.append({'zone':z['uuid'],'other_zone':q['uuid'],'layer':z['layer'],'gap_mm':d,'required_mm':required})
 report={'verdict':'PASS_INTERIM_RETURN_ANALYTIC_COPPER_AND_PEER_PLANES'if not errors and not pairs else'FAIL_INTERIM_RETURN_ANALYTIC_GEOMETRY','zones':len(zones),'foreign_discrete_checks':checks,'physical_errors':errors,'foreign_peer_plane_errors':pairs,'inputs':{str(i.resolve()):sha(i)for i in(Path(__file__),parent,p,c,src/'receipt.json',Path(F.__file__),Path(C.__file__))},'bank_whole_projection_other_net_retained_current_native_refill_DRC':'OPEN','native_jobs':0,'board_written':False,'adopted':False}
 (out/'receipt.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'verdict':report['verdict'],'zones':len(zones),'foreign_discrete_checks':checks,'physical_errors':len(errors),'foreign_peer_plane_errors':len(pairs)}),flush=True)
if __name__=='__main__':main()
