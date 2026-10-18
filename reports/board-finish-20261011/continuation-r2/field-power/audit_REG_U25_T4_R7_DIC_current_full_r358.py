"""Independent actual-drilled graph/full caps/current-filled subset audit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy,time,collections
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import complete_geometry_r2 as G
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
R=H/'REG-U25-T4-R7-corrected-DIC262-sparse-current-composition-r356'
B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262'
O=H/'REG-U25-T4-R7-DIC-current-independent-full-audit-r358'
LAYERS=('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu');IDS={'ed7b6af5-93e5-5f20-8977-d10ca721564d','d8d8bdad-3845-5659-b172-4d0e231cdadc','f4863c44-a057-598a-aef7-adca7cfb15f1'}
def write(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();br=json.loads((R/'receipt.json').read_text());assert sha(R/'model.pkl')==br['model_SHA256'];assert sha(B/'model.pkl')=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144';g,h0,b0,q0,before=pickle.loads((B/'model.pkl').read_bytes());gg,h,b,q,after=pickle.loads((R/'model.pkl').read_bytes());d=pickle.loads((R/'new-owned-discrete.pkl').read_bytes());removed=set(d['removed']);nt=d['tracks'];nv=d['vias'];assert(len(nt),len(nv),len(removed))==(26,6,18);oldtracks={t['uuid']:t for t in h0['tracks']};oldvias={v['uuid']:v for v in h0['vias']};assert g==gg;assert {t['uuid']:t for t in h['tracks']}==({u:t for u,t in oldtracks.items()if u not in removed}|{t['uuid']:t for t in nt});assert {v['uuid']:v for v in h['vias']}==(oldvias|{v['uuid']:v for v in nv})
 for key in h0:
  if key not in ('tracks','vias'):assert h[key]==h0[key],key
 qm0={z['uuid']:z for z in q0};qm={z['uuid']:z for z in q};newq=[z for z in q if z['uuid']not in qm0];assert len(newq)==7;unchanged=[]
 for z in q0:
  n=qm[z['uuid']];assert {k:v for k,v in n.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}
  if z['uuid']not in IDS:assert all(n[r].wkb==z[r].wkb for r in('shape','zone_outline_shape'));unchanged.append(z['uuid'])
  assert set_precision(n['shape'],0).difference(set_precision(z['shape'],0)).is_empty,('owned physical gain',z['uuid'])
 fill0={z['uuid']:z for z in before['zones']};fill1={z['uuid']:z for z in after['zones']};subset=[];changed_fill=set();affected={L.norm(t['net'])for t in nt+nv}|{L.norm(z['net'])for z in newq}
 for uid,z in fill0.items():
  n=fill1[uid];assert set(z['fills'])==set(n['fills']);assert {k:v for k,v in z.items()if k!='fills'}=={k:v for k,v in n.items()if k!='fills'}
  for layer,rs in z['fills'].items():
   if rs==n['fills'][layer]:continue
   old=unary_union(L.poly(rs));now=unary_union(L.poly(n['fills'][layer]));gain=now.difference(old);assert gain.is_empty,('actual current filled gain',uid,layer,gain.area);changed_fill.add((uid,layer));affected.add(L.norm(z['net']));subset.append({'UUID':uid,'layer':layer,'before_SHA256':A.C.sha(old.wkb),'after_SHA256':A.C.sha(now.wkb),'removed_mm2':old.difference(now).area,'strict_subset_and_original_coordinates_not_snapped':True})
 write(O/'independent-all-current-filled-subset-ledger.json',subset);write(O/'unrelated-owned-role-WKB-exact.json',unchanged);print('R358 exact sparse identities and current subset',len(subset),flush=True)
 # Measure true round ends/radii, native flashed old pad apertures, and all
 # dynamic new/old drilled clearances. Planner-only R7 deficits are separate.
 rec,trees=F.build({**h,'zones':[]});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};checks=[];errors=[];planner=[];inherited=[]
 def check(row,prior=None):
  row['planner_PASS']=row['actual_mm']+1e-10>=row['required_mm'];row['native_PASS']=row['actual_mm']+1e-10>=row.get('native_required_mm',row['required_mm']-.025);checks.append(row)
  if not row['native_PASS']:errors.append(row)
  elif not row['planner_PASS']:
   if prior is not None and prior+1e-10<row['required_mm'] and row['actual_mm']+1e-10>=prior:inherited.append({**row,'actual_BEFORE_mm':prior,'unchanged_or_improved_inherited_planner_deficit':True})
   elif row.get('new_UUID')=='01b7f163-fae6-5367-b06f-31d290812677'and row.get('BGA_literal_native_exception'):planner.append(row)
   else:errors.append(row)
 fills={l:[] for l in LAYERS}
 for z in after['zones']:
  for layer,rs in z['fills'].items():fills[layer].extend({'UUID':z['uuid'],'net':z['net'],'local':z.get('clearance_mm',.15),'shape':s}for s in L.poly(rs))
 ftrees={l:STRtree([r['shape']for r in xs])for l,xs in fills.items()}
 for item in nt+nv:
  via='d'in item;axis=Point(item['x'],item['y'])if via else LineString([item['a'],item['b']]);radius=item['d']/2 if via else item['w']/2;ls=LAYERS if via else[item['layer']]
  for layer in ls:
   for j in trees[layer].query(axis.buffer(radius+.801),predicate='intersects'):
    a=rec[layer][int(j)]
    if L.norm(a['net'])==L.norm(item['net']):continue
    gap=axis.distance(a['shape'])-radius
    if a['kind']=='track'and not tm[a['uuid']].get('m'):t=tm[a['uuid']];gap=axis.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
    elif a['kind']=='via':v=vm[a['uuid']];gap=axis.distance(Point(v['x'],v['y']))-radius-v['d']/2
    bga=via and a['kind']=='pad'and a.get('ref')=='U1001';native=.125 if bga else G.gap(h,item['net'],a['net']);check({'kind':'full_cap_annulus_to_actual_'+a['kind'],'new_UUID':item['uuid'],'foreign_UUID':a['uuid'],'layer':layer,'actual_mm':gap,'required_mm':native+.025,'native_required_mm':native,'BGA_literal_native_exception':bga})
   for j in ftrees[layer].query(axis.buffer(radius+.801),predicate='intersects'):
    a=fills[layer][int(j)]
    if L.norm(a['net'])==L.norm(item['net']):continue
    native=max(a['local'],G.gap(h,item['net'],a['net']));check({'kind':'full_cap_annulus_to_actual_current_fill','new_UUID':item['uuid'],'foreign_UUID':a['UUID'],'layer':layer,'actual_mm':axis.distance(a['shape'])-radius,'required_mm':native+.025,'native_required_mm':native})
  for rule in h['rule_areas']:
   if set(ls)&set(rule['layers'])and rule.get('no_vias'if via else'no_tracks')and any(axis.distance(s)-radius<.025 for s in L.poly(rule['outline'])):errors.append({'kind':'actual_native_rule_area','new_UUID':item['uuid'],'rule_UUID':rule['uuid']})
  if via:
   for pad in h['pads']:
    if pad['smd']:
     for layer,rs in pad['layers'].items():
      if layer not in ('F.Cu','B.Cu'):continue
      for s in L.poly(rs):
       gap=axis.distance(s)-item['drill']/2
       if gap<.30:check({'kind':'every_SMD_including_same_raw_drill','new_UUID':item['uuid'],'foreign_UUID':pad['uuid'],'layer':layer,'actual_mm':gap,'required_mm':.275,'native_required_mm':.275})
    for s in L.poly(pad.get('hole')or[]):
     gap=axis.distance(s)-item['drill']/2
     if gap<.30:check({'kind':'every_native_pad_hole','new_UUID':item['uuid'],'foreign_UUID':pad['uuid'],'actual_mm':gap,'required_mm':.275,'native_required_mm':.275})
   for other in h['vias']:
    if other['uuid']==item['uuid']:continue
    gap=axis.distance(Point(other['x'],other['y']))-(item['drill']+other['drill'])/2
    if gap<.30:check({'kind':'dynamic_every_native_and_new_drill','new_UUID':item['uuid'],'foreign_UUID':other['uuid'],'actual_mm':gap,'required_mm':.275,'native_required_mm':.275})
 for z in newq+[qm[u]for u in IDS]:
  shape=set_precision(z['shape'],0);layer=z['layer'];prior=set_precision(qm0[z['uuid']]['shape'],0)if z['uuid']in qm0 else None
  for j in trees[layer].query(shape.buffer(.801),predicate='intersects'):
   a=rec[layer][int(j)]
   if L.norm(a['net'])==L.norm(z['net']):continue
   gap=shape.distance(a['shape']);oldgap=prior.distance(a['shape'])if prior is not None else None
   if a['kind']=='track'and not tm[a['uuid']].get('m'):t=tm[a['uuid']];axis=LineString([t['a'],t['b']]);gap=shape.distance(axis)-t['w']/2;oldgap=prior.distance(axis)-t['w']/2 if prior is not None else None
   elif a['kind']=='via':v=vm[a['uuid']];axis=Point(v['x'],v['y']);gap=shape.distance(axis)-v['d']/2;oldgap=prior.distance(axis)-v['d']/2 if prior is not None else None
   native=max(z.get('clearance_mm',.15),G.gap(h,z['net'],a['net']));check({'kind':'new_or_changed_owned_plane_to_true_'+a['kind'],'new_UUID':z['uuid'],'foreign_UUID':a['uuid'],'layer':layer,'actual_mm':gap,'required_mm':native+.025,'native_required_mm':native},oldgap)
  for peer in q:
   if peer['uuid']==z['uuid']or peer['layer']!=layer or L.norm(peer['net'])==L.norm(z['net']):continue
   native=max(z.get('clearance_mm',.15),peer.get('clearance_mm',.15),G.gap(h,z['net'],peer['net']));gap=shape.distance(set_precision(peer['shape'],0))
   if gap<native+.035:check({'kind':'all_peer_physical_owned_plane','new_UUID':z['uuid'],'foreign_UUID':peer['uuid'],'layer':layer,'actual_mm':gap,'required_mm':native+.025,'native_required_mm':native},prior.distance(set_precision(qm0[peer['uuid']]['shape'],0))if prior is not None and peer['uuid']in qm0 else None)
  for j in ftrees[layer].query(shape.buffer(.801),predicate='intersects'):
   a=fills[layer][int(j)]
   if L.norm(a['net'])==L.norm(z['net']):continue
   native=max(z.get('clearance_mm',.15),a['local'],G.gap(h,z['net'],a['net']));gap=shape.distance(a['shape']);oldz=fill0.get(a['UUID']);oldbody=unary_union(L.poly(oldz['fills'].get(layer,[])))if oldz else None;oldgap=prior.distance(oldbody)if prior is not None and oldbody is not None else None
   if gap<native+.035:check({'kind':'changed_owned_to_every_actual_native_or_owned_fill','new_UUID':z['uuid'],'foreign_UUID':a['UUID'],'layer':layer,'actual_mm':gap,'required_mm':native+.025,'native_required_mm':native},oldgap)
 write(O/'independent-all-true-copper-checks.json',checks);write(O/'independent-all-true-copper-errors.json',errors);write(O/'explicit-R7-extra-planner-failures.json',planner);write(O/'unchanged-inherited-margin-deficits.json',inherited);print('R358 true Cu',len(checks),'errors',len(errors),'R7 planner',len(planner),'inherited',len(inherited),flush=True)
 # Independently rebuild physical layer graphs with all actual drill voids.
 oldctx=K.hole_context(before);newctx=K.hole_context(after);nets={L.norm(z['net'])for z in before['zones']}|affected|{'/motherboard_motors/AUX_5V_B'};oldgroups={};groups={};contacts=[];direct=[];directbad=[];newholes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in nv]
 for net in sorted(nets):
  _,a=K.physical(before,net,oldctx);oldgroups[net]=a;reused=False
  if net not in affected and all(not hole.intersects(r['shape'])for xs in a for r in xs for hole in newholes):
   for kind in ('tracks','vias','pads','shapes','zones'):assert [r for r in before[kind]if L.norm(r['net'])==net]==[r for r in after[kind]if L.norm(r['net'])==net]
   n=a;reused=True
  else:_,n=K.physical(after,net,newctx)
  groups[net]=n;rows,bad=K.contact_losses(a,n,removed);contacts.append({'net':net,'old_layer_key_partition_losses':bad,'actual_BEFORE_graph_reused_only_after_exact_unchanged_geometry_and_all_new_holes_disjoint':reused});write(O/'all-net-drilled-contact-checkpoint.json',contacts);print('R358 contact',net,len(bad),'EXACT_REUSE'if reused else'PHYSICAL_REBUILD',flush=True)
  if net in affected:
   final=collections.defaultdict(list)
   for xs in n:
    for r in xs:
     if r['kind']=='fill':final[r['uuid'],r['layer']].append(r['shape'])
   for layer in LAYERS:
    metal=[r for xs in a for r in xs if r['kind']!='fill'and r['layer']==layer and r['uuid']not in removed];tree=STRtree([r['shape']for r in metal])
    for fill in (r for xs in a for r in xs if r['kind']=='fill'and r['layer']==layer and(r['uuid'],layer)in changed_fill):
     for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
      m=metal[int(j)]
      if m['shape'].distance(fill['shape'])>.000002:continue
      hits=[A.C.sha(s.wkb)for s in final[fill['uuid'],layer]if m['shape'].distance(s)<=.000002];row={'net':net,'UUID':fill['uuid'],'layer':layer,'physical_old_contact_key':[m['kind'],m['uuid'],layer],'retained_actual_same_zone_contact':bool(hits)};direct.append(row)
      if not hits:directbad.append(row)
 (O/'actual-drilled-before-groups.pkl').write_bytes(pickle.dumps(oldgroups,protocol=5));(O/'actual-drilled-current-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));write(O/'all-direct-native-owned-fill-contact-ledger.json',direct);sources=[];refs=[]
 for net,ref,pin in K.ROOTS:
  a=K.root(oldgroups[net],ref,pin);n=K.root(groups[net],ref,pin);missing=K.keys(a)-{('track',uid,layer)for uid in removed for layer in LAYERS}-K.keys(n);sources.append({'net':net,'source':ref+'.'+pin,'prior_source_physical_layer_keys_lost':[list(k)for k in sorted(missing)]})
  if ref in ('J11001','J11003','J11005'):
   bad,proof=RF.audit(before,K.source_refs(a),K.source_refs(n),net,removed);refs.append({'net':net,'strict_ZERO_retained_old_reference_losses':bad,'proof':proof})
 targets=[]
 for net,ref,pin,pairs in [('/motherboard_motors/FIELD_GND','J11003','2',[('U11025','2')]),('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')]),('/motherboard_do/DOB_FIELD_3V3','U11018','1',[('U19008','10')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')])]:
  n=K.root(groups[net],ref,pin);present={(r['ref'],str(r['pin']))for r in n if r['kind']=='pad'};targets.append({'net':net,'source':ref+'.'+pin,'required_targets':pairs,'not_actual_source_rooted':[p for p in pairs if p not in present]})
 fg=K.root(groups['/motherboard_motors/FIELD_GND'],'J11003','2');fr=K.source_refs(fg);health='/motherboard_power_entry/FIELD_HEALTH_B_N';newhealth=[]
 for t in nt:
  if t['net']!=health:continue
  body=A.shape({'kind':'segment',**t});gap=body.difference(fr[t['layer']]);newhealth.append({'UUID':t['uuid'],'new_full_health_body_reference_gap_mm2':gap.area,'gap_empty':gap.is_empty})
 write(O/'all-nine-source-key-rows.json',sources);write(O/'three-bank-strict-zero-reference-rows.json',refs);write(O/'REG-U25-actual-source-targets.json',targets);write(O/'all-four-new-health-body-reference-rows.json',newhealth)
 bad=errors or any(c['old_layer_key_partition_losses']for c in contacts)or directbad or any(s['prior_source_physical_layer_keys_lost']for s in sources)or any(r['strict_ZERO_retained_old_reference_losses']for r in refs)or any(t['not_actual_source_rooted']for t in targets)or any(not h['gap_empty']for h in newhealth)
 rec={'verdict':'SPARSE_COMBINED_INCREMENTAL_PHYSICAL_SOURCE_OLDREF_HOST_PASS_INHERITED_CURRENT_NATIVE_OPEN'if not bad else'SPARSE_COMBINED_INCREMENTAL_PHYSICAL_SOURCE_OLDREF_REPAIR_REQUIRED','current_constructor_receipt_SHA256':sha(R/'receipt.json'),'current_model_SHA256':sha(R/'model.pkl'),'baseline_corrected_DIC_R262_model_SHA256':sha(B/'model.pkl'),'all_net_count':len(nets),'old_relationship_loss_count':sum(len(c['old_layer_key_partition_losses'])for c in contacts),'direct_contact_losses':directbad,'all_nine_prior_source_loss_count':sum(len(s['prior_source_physical_layer_keys_lost'])for s in sources),'strict_ZERO_old_reference_losses':sum(len(r['strict_ZERO_retained_old_reference_losses'])for r in refs),'new_true_copper_checks':len(checks),'new_true_copper_errors':errors,'explicit_R7_extra_planner_failures':planner,'inherited_margin_deficits':inherited,'actual_source_target_rows':targets,'new_health_reference_rows':newhealth,'every_unchanged_original_source_node_native_definition_rule_component_and_pad_untouched':True,'inherited_CORE_reference_gap_mm2':93.04195929171794,'inherited_ROOT42_CORE_DC_current_native_FAIL_OPEN_preserved':True,'new_DIC_own_supported_body_and_REG_DC_current_mesh_full_native_rule_fill_flash_DRC':'OPEN_separate_no_aperture_expansion_or_source_waiver','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'verdict':rec['verdict'],'contact_losses':rec['old_relationship_loss_count'],'direct_losses':len(directbad),'source_losses':rec['all_nine_prior_source_loss_count'],'strict_zero_refs':rec['strict_ZERO_old_reference_losses'],'true_errors':len(errors)}),flush=True)
if __name__=='__main__':main()
