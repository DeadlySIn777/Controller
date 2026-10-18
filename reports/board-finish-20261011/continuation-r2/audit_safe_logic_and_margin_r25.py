"""Independent strict round-cap/pad/foreign-plane check of the six R22 changes."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'safe-logic-five-and-fag-margin-r22/model.pkl';out=H/'safe-logic-margin-independent-r25.json';assert sha(mp)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'and not out.exists();g,h,b,z,current=pickle.loads(mp.read_bytes());adds=pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes());adds.append(pickle.loads(mp.with_name('owned-margin-replacement.pkl').read_bytes()));assert len(adds)==6
rec,trees=F.build({**h,'zones':[]});physical=[];foreign=[];checks=0
def need(q,r,local):return max(.15 if h['domains_normalized'][C.norm(q)]==h['domains_normalized'][C.norm(r)]else .6,local)+.025
def gap(sh,q):
 if q['kind']=='via':v=q['source'];return sh.distance(Point(v['x'],v['y']))-v['d']/2
 if q['kind']=='track':t=q['source'];return sh.distance(LineString([t['a'],t['b']]))-t['w']/2
 return sh.distance(q['shape'])
for q in adds:
 for i in trees[q['layer']].query(q['shape'].buffer(1.5),predicate='intersects'):
  r=rec[q['layer']][int(i)]
  if q['net']==r['net']:continue
  checks+=1;d=gap(q['shape'],r);n=need(q['net'],r['net'],float(q.get('clearance_mm',.15)))
  if d<n:physical.append({'new_zone_uuid':q['uuid'],'other_uuid':r['uuid'],'other_kind':r['kind'],'layer':q['layer'],'actual_mm':d,'required_mm':n})
 for r in z:
  if q['layer']!=r['layer']or q['net']==r['net']:continue
  checks+=1;d=q['shape'].distance(r['shape']);n=need(q['net'],r['net'],max(float(q.get('clearance_mm',.15)),float(r.get('clearance_mm',.15))))
  if d<n:foreign.append({'new_zone_uuid':q['uuid'],'other_zone_uuid':r['uuid'],'layer':q['layer'],'actual_mm':d,'required_mm':n})
report={'verdict':'PASS_SIX_CHANGED_OWNED_SHAPES_STRICT_ANALYTIC_CAP_PAD_VIA_FOREIGN_NEW_PLANE_GEOMETRY'if not physical and not foreign else'FAIL_SIX_CHANGED_OWNED_SHAPES_GEOMETRY','model_sha256':sha(mp),'scope_changed_UUIDs':[q['uuid']for q in adds],'physical_errors':physical,'foreign_new_zone_errors':foreign,'checks':checks,'required':'Full0.15mm same-domain or0.6mm foreign-domain plus0.025mm planning guard; no deficit waiver','all_board_native_current_mechanics_gates':'OPEN','script_sha256':sha(__file__),'native_jobs':0,'board_written':False,'adopted':False};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
