"""Compare exact owned primitives after R177; no geometry edits or area waiver."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import restore_SAFE_generated_precision_states_r168 as PS
import core_inner_feed_r18 as I
P=I.p
O=H/'sbc-power/IO3-incremental-primitive-diagnosis-r182'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 oldp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';newp=H/'sbc-power/original-IO3-full-owned-zone-normalization-r177/model.pkl'
 a,ah,ab,az,ac=pickle.loads(oldp.read_bytes());n,nh,nb,nz,nc=pickle.loads(newp.read_bytes());assert a==n and ah==nh
 PS.restore_bound_generated_precision_states(ab,az);PS.restore_bound_generated_precision_states(nb,nz)
 om={q['uuid']:q for q in az};rows=[]
 for q in nz:
  if q['uuid'] not in om:continue
  before=om[q['uuid']];rr={'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'roles':{}}
  for role in ('shape','zone_outline_shape'):
   x,y=before[role],q[role];lost=x.difference(y);gain=y.difference(x)
   rr['roles'][role]={'old_sha256':digest(x),'new_sha256':digest(y),'equals':x.equals(y),'removed_mm2':lost.area,'added_mm2':gain.area,'removed_bounds':None if lost.is_empty else list(lost.bounds),'added_bounds':None if gain.is_empty else list(gain.bounds)}
  rows.append(rr)
 oldzones={q['uuid']:q for q in ac['zones']};fillrows=[]
 for q in nc['zones']:
  if q['uuid'] not in oldzones:continue
  before=oldzones[q['uuid']]
  for layer in set(q['fills'])|set(before['fills']):
   x=unary_union(P.base.polygons(before['fills'].get(layer,[])));y=unary_union(P.base.polygons(q['fills'].get(layer,[])));lost=x.difference(y);gain=y.difference(x)
   if lost.is_empty and gain.is_empty:continue
   for role,s in [('lost',lost),('gain',gain)]:
    f=O/(q['uuid']+'.'+layer+'.'+role+'.wkb');f.write_bytes(s.wkb)
   fillrows.append({'uuid':q['uuid'],'raw_net':q['net'],'layer':layer,'prospective':bool(q.get('prospective_not_native')),'removed_mm2':lost.area,'added_mm2':gain.area,'removed_bounds':None if lost.is_empty else list(lost.bounds),'added_bounds':None if gain.is_empty else list(gain.bounds),'old_sha256':digest(x),'new_sha256':digest(y)})
 r={'verdict':'EXACT_PRIMITIVE_AND_FILL_DELTA_DIAGNOSIS_ONLY','parent_sha256':sha(oldp),'model_sha256':sha(newp),'same_uuid_owned_rows':rows,'same_uuid_fill_delta_rows':fillrows,'no_geometry_edits':True,'no_area_waiver':True,'script_sha256':sha(__file__)}
 (O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n')
 print('R182_COMPLETE',sha(O/'receipt.json'),'owned_changes',sum(any(not v['equals'] for v in r['roles'].values()) for r in rows),'fill_changes',len(fillrows),flush=True)
 for r in rows:
  if any(not v['equals'] for v in r['roles'].values()):print('OWNED_DELTA',r['uuid'],r['raw_net'],r['layer'],r['roles']['shape']['removed_mm2'],r['roles']['shape']['added_mm2'],flush=True)
if __name__=='__main__':main()
