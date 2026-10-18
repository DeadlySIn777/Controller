"""Read-only local two-port eligibility around the real native IO3 split."""
import pickle,json,hashlib,sys,time,math,traceback,collections
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R353-local-IO3-split-two-new-ordinary-port-existing-LG-return-eligibility-r367'
D=H/'sbc-power/CM79-R353-fresh-IO3-split-source-and-existing-annulus-port-attribution-r355'
NET='/IO_3V3';LG='/LOGIC_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r353/model.pkl';assert sha(mp)=='de8e2af4143fe43491773e0e0339c39efb17cb1660072bf37ffc6a22c155255e';g,h,b,q,c=pickle.loads(mp.read_bytes());assert sha(D/'actual-IO3-before-after-groups.pkl')=='be399f407a053b8cfeb6f3eecb41082b43d2663f57b19b1d2c45fed5168bd41d';io=pickle.loads((D/'actual-IO3-before-after-groups.pkl').read_bytes())['after'];source=K.root(io,'R18001','2');detached=next(xs for xs in io if xs is not source and len(K.keys(xs))>1000);iofill={name:zero(unary_union([r['shape']for r in xs if r['kind']=='fill'and r['layer']=='In2.Cu']))for name,xs in [('source',source),('detached',detached)]};cache=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/actual-drilled-after-groups.pkl';assert sha(cache)=='339dbe2c2173388fa7384c697e6364dcf5b9c507e552e64836b08c55203ed4eb';lg=K.root(pickle.loads(cache.read_bytes())['/LOGIC_GND'],'J11001','2');refs={ly:zero(unary_union([r['shape']for r in lg if r['kind']=='fill'and r['layer']==ly]))for ly in ('In1.Cu','In4.Cu')};native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=A.C.inventory(native.read_bytes());region=box(116.3,165.8,127.1,176.4);returns=[]
 for v in h['vias']:
  if L.norm(v['net'])!=LG or v['uuid']not in iv[3]or not region.buffer(1).covers(Point(v['x'],v['y'])):continue
  ann={ly:zero(unary_union([r['shape']for r in lg if r['kind']=='via'and r['uuid']==v['uuid']and r['layer']==ly]))for ly in ('In1.Cu','In4.Cu')};overlap={ly:ann[ly].intersection(refs[ly]).area for ly in ann}
  if all(a>0 for a in overlap.values()):returns.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'actual_source_fill_annulus_overlap_mm2':overlap,'native_chunk_sha256':hashlib.sha256(iv[3][v['uuid']]).hexdigest(),'all_original_masks_and_flags_unchanged':True})
 put(O/'local-original-actual-two-plane-J1-return-port-census.json',returns);rec,trees=F.build(c);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);vxy=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vxy);reserve,exempt=A.reservations();courts=[(f['ref'],s)for f in h['footprints']for ps in f['courtyard'].values()for s in L.poly(ps)];ct=STRtree([s for ref,s in courts]);qtree={ly:STRtree([z['shape']for z in q if z['layer']==ly])for ly in K.LAYERS};qlayer={ly:[z for z in q if z['layer']==ly]for ly in K.LAYERS};masks={ly:[]for ly in refs}
 for layer,rlayer in [('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]:
  for rr in rec[layer]:
   if rr['kind']=='fill'or L.norm(rr['net'])==LG or dom.get(L.norm(rr['net']))!=dom.get(LG)or not rr['shape'].intersects(region.buffer(2)):continue
   supported=rr['shape'].intersection(refs[rlayer])
   if not supported.is_empty:masks[rlayer].append({'uuid':rr['uuid'],'kind':rr['kind'],'shape':supported})
 for ly in refs:
  for rr in lg:
   if rr['kind']=='via'and rr['layer']==ly and rr['shape'].intersects(region.buffer(2)):
    supported=rr['shape'].intersection(refs[ly])
    if not supported.is_empty:masks[ly].append({'uuid':rr['uuid'],'kind':'existing_source_GND_annulus','shape':supported})
 mt={ly:STRtree([r['shape']for r in masks[ly]])for ly in refs};rows=[];legal={'source':[],'detached':[]};seen=set()
 for ret in returns:
  for angle in range(0,360,5):
   ar=math.radians(angle);xy=(round(ret['xy'][0]+.95*math.cos(ar),6),round(ret['xy'][1]+.95*math.sin(ar),6))
   if xy in seen or not region.covers(Point(xy)):continue
   seen.add(xy);p=Point(xy);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));side=next((s for s in ('source','detached')if iofill[s].covers(p.buffer(.1,quad_segs=128))and ann.intersection(iofill[s]).area>.025),None)
   if not side:continue
   bad=[];localcutters={};nativeLGcuts=[]
   for ly in K.LAYERS:
    for j in trees[ly].query(p.buffer(1.25),predicate='intersects'):
     rr=rec[ly][int(j)]
     if L.norm(rr['net'])==NET:continue
     local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;req=max(local,gap(NET,rr['net']))+.025
     if rr['kind']=='fill'and L.norm(rr['net'])==LG:
      cut=Z.bounded_buffer(p,.25+req);nativeLGcuts.append({'layer':ly,'UUID':rr['uuid'],'guard_radius_mm':.25+req});localcutters[ly]=zero(unary_union([localcutters.get(ly,Point().buffer(0)),cut]));continue
     distance=p.distance(rr['shape'])-.25
     if distance<req:bad.append({'layer':ly,'UUID':rr['uuid'],'kind':rr['kind'],'net':rr['net'],'actual_gap_mm':distance,'planner_required_mm':req})
    for j in qtree[ly].query(p.buffer(1.25),predicate='intersects'):
     z=qlayer[ly][int(j)]
     if L.norm(z['net'])==NET:continue
     req=max(float(z['clearance_mm']),gap(NET,z['net']))+.025
     if L.norm(z['net'])==LG:
      cut=Z.bounded_buffer(p,.25+req);localcutters[ly]=zero(unary_union([localcutters.get(ly,Point().buffer(0)),cut]));continue
     distance=p.distance(z['shape'])-.25
     if distance<req:bad.append({'layer':ly,'UUID':z['uuid'],'kind':'owned_physical_zone','net':z['net'],'actual_gap_mm':distance,'planner_required_mm':req})
   for j in ht.query(p.buffer(.385),predicate='intersects'):
    uid,n,s=holes[int(j)]
    if p.distance(s)-.1<.28:bad.append({'UUID':uid,'kind':'every_real_hole_to_new_drill','actual_gap_mm':p.distance(s)-.1,'planner_required_mm':.28})
   for j in vt.query(p.buffer(.825),predicate='intersects'):
    if p.distance(vxy[int(j)])<.815:bad.append({'UUID':h['vias'][int(j)]['uuid'],'kind':'ordinary_all_via_pitch','distance_mm':p.distance(vxy[int(j)])})
   for j in ct.query(p.buffer(.25),predicate='intersects'):bad.append({'ref':courts[int(j)][0],'kind':'original_component_courtyard_no_POWER_D4'})
   for rules,ex in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
    for rr in rules:
     if not ex and not rr.get('no_vias'):continue
     if ex and NET in exempt.get(rr['name'],set()):continue
     if any(p.distance(s)<.275 for s in L.poly(rr['outline'])):bad.append({'kind':'native_or_reserved_via_rule','name':rr.get('name',rr.get('uuid'))})
   for ly,cut in localcutters.items():
    if ly not in refs:continue
    for j in mt[ly].query(cut,predicate='intersects'):
     rr=masks[ly][int(j)];hit=cut.intersection(rr['shape'])
     if not hit.is_empty:bad.append({'kind':'exact_supported_old_body_or_source_ground_annulus_reference_mask','layer':ly,'UUID':rr['uuid'],'native_kind':rr['kind'],'hit_type':hit.geom_type,'hit_area_mm2':hit.area})
   row={'new_IO3_xy':list(xy),'size_drill_mm':[.5,.2],'side':side,'In2_actual_source_fill_annulus_overlap_mm2':ann.intersection(iofill[side]).area,'existing_original_J1_two_plane_return':ret,'ordinary_return_distance_mm':math.dist(xy,ret['xy']),'explicit_native_LG_fill_hole_operations':nativeLGcuts,'deficits':bad,'PASS_local_source_geometry_mask_screen':not bad};rows.append(row)
   if not bad:legal[side].append(row)
 put(O/'local-source-port-existing-return-candidate-mask-geometry-ledger.json',rows);put(O/'only-local-eligible-source-and-detached-ports.json',legal);put(O/'receipt.json',{'verdict':'READ_ONLY_LOCAL_IO3_TWO_NEW_PORT_ELIGIBILITY_EXISTING_TRUE_LG_RETURNS','model_sha256':sha(mp),'original_actual_two_plane_LG_return_count':len(returns),'source_contact_eligible_candidates':len(rows),'mask_geometry_eligible_by_side':{k:len(v)for k,v in legal.items()},'all_original_native_and_owned_foreign_Cu_except_explicit_LG_hole_retreat_hard':True,'actual_IO3_bypass_new_body_reference_fresh_all3689_source_oldcontact_native_current':'OPEN','model_source_native_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R367',sha(O/'receipt.json'),{k:len(v)for k,v in legal.items()},len(returns),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
