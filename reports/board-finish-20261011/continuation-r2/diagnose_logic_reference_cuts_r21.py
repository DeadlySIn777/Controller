"""Attribute R18 reference failure to exact owned planes before replacing them."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import physical_reference_losses_r1 as REF
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bp=H/'corrected-joint-ground-base-r11/model.pkl';mp=H/'logic-source-union-reuse-return-restoration-r18/model.pkl';qp=mp.with_name('proposed-zones.pkl');out=H/'logic-seven-reference-diagnosis-r21'
assert sha(bp)=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8' and sha(mp)=='20ae7a0558877ba76300f2163b920c77fe96c5861a930fb7b22570f665ad37b8' and not out.exists()
g,h,b,z,after=pickle.loads(mp.read_bytes());_,_,_,_,before=pickle.loads(bp.read_bytes());adds=pickle.loads(qp.read_bytes());gs=pickle.loads((H/'logic-seven-independent-incremental-r20/groups.pkl').read_bytes());net='/motherboard_do/FIELD_B_0V';oldgs=F.graph(before,net)
root=lambda xs:next(q for q in xs if any(a['kind']=='pad'and(a['ref'],a['pin'])==('J11005','2')for a in q))
oldroot=root(oldgs);newroot=root(gs[net]);oldrefs={l:unary_union([q['shape']for q in oldroot if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')};newrefs={l:unary_union([q['shape']for q in newroot if q['kind']=='fill'and q['layer']==l])for l in oldrefs}
out.mkdir();rows=[]
for q in adds:
 d=oldrefs.get(q['layer']);cut=N.bounded_buffer(q.get('zone_outline_shape',q['shape']),max(.6,float(q.get('clearance_mm',.15)))+.025)
 direct=0 if d is None else cut.intersection(d).area
 rows.append({'zone_uuid':q['uuid'],'layer':q['layer'],'direct_old_source_reference_fill_cut_mm2':direct,'shape_bounds_mm':list(q['shape'].bounds)})
 masks={};deltas={}
for layer,outer in [('In1.Cu','F.Cu'),('In4.Cu','B.Cu')]:
 bodies=[]
 for t in before['tracks']:
  if t['layer']==outer and C.norm(t['net'])!=net and before['domains_normalized'].get(C.norm(t['net']))==before['domains_normalized'][net]:
   body=REF.A.shape({'kind':'segment',**t});sh=body.intersection(oldrefs[layer])
   if not sh.is_empty:bodies.append(sh)
 masks[layer]=unary_union(bodies);deltas[layer]=oldrefs[layer].difference(newrefs[layer]);(out/(layer+'-old-required-reference-mask.wkb')).write_bytes(masks[layer].wkb);(out/(layer+'-lost-source-reference-fill.wkb')).write_bytes(deltas[layer].wkb)
 for q in rows:
  if q['layer']==layer:
   source=next(x for x in adds if x['uuid']==q['zone_uuid']);cut=N.bounded_buffer(source.get('zone_outline_shape',source['shape']),.625)
   q['direct_old_required_track_reference_cut_mm2']=cut.intersection(masks[layer]).area
(out/'masks.pkl').write_bytes(pickle.dumps(masks,protocol=5));report={'verdict':'EXACT_NEW_LOGIC_SHAPE_REFERENCE_CAUSE_DIAGNOSIS','rows':rows,'reference_masks_sha256':sha(out/'masks.pkl'),'lost_source_fill_area_mm2':{l:s.area for l,s in deltas.items()},'old_source_fill_preservation_requirement':'All actual source-rooted foreign ground fill may be conserved as a stronger routing mask; root connectivity and old outer bodies must be rechecked after replacement.','script_sha256':sha(__file__),'model_sha256':sha(mp),'parent_sha256':sha(bp),'adopted':False,'native_jobs':0};(out/'receipt.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
