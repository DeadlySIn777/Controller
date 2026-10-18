"""Exact indexed broad phase; preserve deliberate own-host R560 stop."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;src=H/'audit_DIC_policy_coupled_actual_current_r560.py';out=H/'DIC-policy-coupled-actual-current-independent-r560';fp=out/'failure.json';assert not fp.exists();fp.write_text(json.dumps({'status':'OWN_CONFINED_HOST_INTENTIONALLY_STOPPED_FOR_EXACT_CONTACT_INDEX_SUCCESSOR','helper_SHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'completed_scopes':'3 exact source-fill replay families; six raw scope FAILs;165 true geometry checks0errors; IO3 old relationships0loss','full_source_contact_reference_receipt_NOT_completed':True,'successor_change':'Layer/group STRtree dwithin broad phase preserves the exact2nm finite contact predicate and every actual source primitive; complete-dimension source-reference delta supplement includes lines/points','no_model_source_geometry_mask_threshold_or_native_change':True},indent=1)+'\n')
s=src.read_text().replace('DIC-policy-coupled-actual-current-independent-r560','DIC-policy-coupled-actual-current-independent-r562').replace('R560_','R562_')
old="""   for gr in oldg:
    for r in gr:
     if r['kind']=='fill'or r['uuid']in removed:continue
     oldtouch=[f for f in gr if f['kind']=='fill'and f['layer']==r['layer']and r['shape'].distance(f['shape'])<=.000002]
     if not oldtouch:continue
     nb=unary_union(nby[r['kind'],r['uuid'],r['layer']]);touch=[f for f in fillby[r['layer']]if nb.distance(f['shape'])<=.000002];row="""
new="""   newft={ly:STRtree([f['shape']for f in fs])for ly,fs in fillby.items()}
   for gr in oldg:
    oldfb=collections.defaultdict(list)
    for f in gr:
     if f['kind']=='fill':oldfb[f['layer']].append(f)
    oldft={ly:STRtree([f['shape']for f in fs])for ly,fs in oldfb.items()}
    for r in gr:
     if r['kind']=='fill'or r['uuid']in removed or r['layer']not in oldft:continue
     oldtouch=[oldfb[r['layer']][int(i)]for i in oldft[r['layer']].query(r['shape'],predicate='dwithin',distance=.000002)if r['shape'].distance(oldfb[r['layer']][int(i)]['shape'])<=.000002]
     if not oldtouch:continue
     nb=unary_union(nby[r['kind'],r['uuid'],r['layer']]);touch=[fillby[r['layer']][int(i)]for i in newft[r['layer']].query(nb,predicate='dwithin',distance=.000002)if nb.distance(fillby[r['layer']][int(i)]['shape'])<=.000002]if r['layer']in newft else[];row="""
assert s.count(old)==1;s=s.replace(old,new)
old="""  rr,proof=RF.audit(before,K.source_refs(banks0[net]),K.source_refs(banks[net]),net,removed=removed);refs.append({'net':net,'strict_literal_old_reference_losses':rr,'proof':proof});refbad.extend({'ground':net,**r}for r in rr)"""
new="""  oldref=K.source_refs(banks0[net]);newref=K.source_refs(banks[net]);rr,proof=RF.audit(before,oldref,newref,net,removed=removed)
  def all_dimension_parts(sh):
   if sh.is_empty:return[]
   if sh.geom_type in('Polygon','LineString','Point'):return[sh]
   return[p for x in getattr(sh,'geoms',[])for p in all_dimension_parts(x)]
  deltas={ly:oldref[ly].difference(newref[ly])for ly in newref};ps={ly:all_dimension_parts(sh)for ly,sh in deltas.items()};dtrees={ly:STRtree(xs)for ly,xs in ps.items()};complete=[]
  for t in before['tracks']:
   ly=t['layer'];tn=K.L.norm(t['net'])
   if t['uuid']in removed or ly not in dtrees or tn==net or before['domains_normalized'].get(tn)!=before['domains_normalized'][net]or not ps[ly]:continue
   body=K.A.shape({'kind':'segment',**t})if t.get('m')is None else K.L.body(t);idx=dtrees[ly].query(body,predicate='intersects')
   if not len(idx):continue
   raw=body.intersection(unary_union([ps[ly][int(i)]for i in idx]))
   if raw.is_empty:continue
   f=out/(net.rsplit('/',1)[-1]+'-'+t['uuid']+'-'+ly+'-complete-dimension-raw-old-reference-loss.wkb');f.write_bytes(raw.wkb);complete.append({'uuid':t['uuid'],'net':t['net'],'layer':ly,'prior_source_reference_lost_mm2':raw.area,'exact_raw_loss':info(raw),'file':str(f.resolve()),'all_dimension_zero_area_line_and_point_witnesses_NOT_waived':True})
  refs.append({'net':net,'preserved_polygon_delta_helper_raw_rows':rr,'proof':proof,'strict_complete_dimension_old_reference_losses':complete});refbad.extend({'ground':net,**r}for r in complete)"""
assert s.count(old)==1;s=s.replace(old,new)
old="""put(out/'all-current-old-contact-obligations.json',contacts);put(out/'all-old-direct-layer-fill-contact-obligations.json',direct);put(out/'actual-ten-prior-source-key-obligations.json',sources);put(out/'all-three-strict-literal-old-reference-results.json',refs);"""
new="""put(out/'all-current-old-contact-obligations.json',contacts);put(out/'all-old-direct-layer-fill-contact-obligations.json',direct);put(out/'actual-ten-prior-source-key-obligations.json',sources);put(out/'all-three-strict-literal-old-reference-results.json',refs);bankfile=out/'actual-before-and-after-ten-source-bank-primitives.pkl';bankfile.write_bytes(pickle.dumps({'before':banks0,'after':banks},protocol=5));"""
assert s.count(old)==1;s=s.replace(old,new)
newfile=H/'audit_DIC_policy_coupled_actual_current_r562.py';assert not newfile.exists();newfile.write_text(s);print(str(newfile),hashlib.sha256(newfile.read_bytes()).hexdigest())
