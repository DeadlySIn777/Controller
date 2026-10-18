"""Independent sparse actual-fill audit; no q/native/current qualification."""
from pathlib import Path
import sys,pickle,json,hashlib,copy,time,math
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as ROOT
from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
start=time.monotonic();out=H/'Q0-R436-independent-physical-source-reference-r438';assert not out.exists();out.mkdir();candidate=H/'Q0-exact-R428-current-filled-only-r436';crp=candidate/'receipt.json';assert sha(crp)=='0f4c4442ad12c21844ebb34f38176547601eb99a79a18abd179dfdc8f76c96b6';cr=json.loads(crp.read_bytes());cm=Path(cr['model_file']);assert sha(cm)==cr['model_sha256']=='b80087827ba1f1d6e7f21948faa9b960eaf20e6c07c6443e5a31219b0ba956ae';bm=Path(cr['base_model_file']);assert sha(bm)==cr['base_model_sha256'];g0,h0,b0,q0,before=pickle.loads(bm.read_bytes());g,h,b,q,after=pickle.loads(cm.read_bytes());assert g==g0 and b==b0 and len(q)==len(q0)
for a,z in zip(q0,q):
 assert set(a)==set(z)
 for key in a:assert a[key].wkb==z[key].wkb if hasattr(a[key],'wkb')else a[key]==z[key]
pd=H/'Q0-R426-exact-native-owned-operation-r428';pr=json.loads((pd/'receipt.json').read_bytes());assert sha(pd/'receipt.json')=='f0b31e152b7f13c0a00401149176fb5dff69c4743121654439ca39a82dfeb27c';pp=Path(pr['exact_packet_file']);assert sha(pp)==pr['exact_packet_sha256'];op=pickle.loads(pp.read_bytes());nt=op['tracks'];nv=op['vias'];removed=set(op['exact_deleted_track_UUIDs']);newids={x['uuid']for x in nt+nv};GND='/motherboard_motors/FIELD_GND';dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6;oldtracks={t['uuid']:t for t in h0['tracks']};assert {t['uuid']:t for t in h['tracks']}==({u:t for u,t in oldtracks.items()if u not in removed}|{t['uuid']:t for t in nt});assert all(t['a']!=t['b']for t in nt)
records,trees=K.F.build({**h,'zones':[]});holes=[(v['uuid'],K.L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],K.L.norm(p['net']),s)for p in h['pads']for s in K.L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);smd=[(p,s)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for s in K.L.poly(rs)];st=STRtree([s for p,s in smd]);reserve,exempt=K.A.reservations();checks=[];errors=[];apertures=[];fill={l:[]for l in K.LAYERS}
for z in after['zones']:
 for l,rs in z['fills'].items():fill[l]+=[{'uuid':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':s}for s in K.L.poly(rs)]
ft={l:STRtree([r['shape']for r in xs])for l,xs in fill.items()}
items=nt+nv+[{'uuid':op['original_SENSE_via_UUID'],'net':'/motherboard_do/DOA_Q0_ISNS','x':228.96,'y':160.412,'d':.5,'drill':.2,'added_layer_only':'In2.Cu'}]
for item in items:
 via='d'in item;net=K.L.norm(item['net']);axis=Point(item['x'],item['y'])if via else LineString([item['a'],item['b']]);rad=item['d']/2 if via else item['w']/2;body=K.Z.bounded_buffer(axis,rad);layers=[item['added_layer_only']]if'added_layer_only'in item else K.LAYERS if via else[item['layer']]
 for l in layers:
  for j in trees[l].query(body.buffer(.8),predicate='intersects'):
   r=records[l][int(j)]
   if r['uuid']==item['uuid']or K.L.norm(r['net'])==net:continue
   if r['kind']=='track'and not r['source'].get('m'):dist=axis.distance(LineString([r['source']['a'],r['source']['b']]))-rad-r['source']['w']/2
   elif r['kind']=='via':dist=axis.distance(Point(r['source']['x'],r['source']['y']))-rad-r['source']['d']/2
   else:dist=axis.distance(r['shape'])-rad
   row={'kind':'true_cap_to_'+r['kind'],'new_UUID':item['uuid'],'other_UUID':r['uuid'],'layer':l,'gap_mm':dist,'required_mm':gap(net,r['net'])+.025};checks.append(row)
   if dist<row['required_mm']:errors.append(row)
  for j in ft[l].query(body.buffer(.8),predicate='intersects'):
   r=fill[l][int(j)]
   if K.L.norm(r['net'])==net:continue
   row={'kind':'true_cap_to_actual_after_fill','new_UUID':item['uuid'],'other_UUID':r['uuid'],'layer':l,'gap_mm':axis.distance(r['shape'])-rad,'required_mm':max(r['local'],gap(net,r['net']))+.025};checks.append(row)
   if row['gap_mm']<row['required_mm']:errors.append(row)
 for rule in h['rule_areas']:
  if set(layers)&set(rule['layers'])and rule.get('no_vias'if via else'no_tracks')and any(body.distance(s)<.025 for s in K.L.poly(rule['outline'])):errors.append({'kind':'native_rule_area','UUID':item['uuid'],'rule_UUID':rule['uuid']})
 for rule in reserve['keepouts']:
  if net not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(body.distance(s)<.025 for s in K.L.poly(rule['outline'])):errors.append({'kind':'frozen_reserve','UUID':item['uuid'],'name':rule['name']})
 if via and item['uuid']in newids:
  p,sh=smd[int(st.nearest(axis))];sm=axis.distance(sh)-.105;dr=min((axis.distance(s)-.105,u)for u,n,s in holes if u!=item['uuid']);pitch=min((axis.distance(Point(v['x'],v['y'])),v['uuid'])for v in h['vias']if v['uuid']!=item['uuid']);row={'UUID':item['uuid'],'role':item.get('role'),'nearest_SMD':[p['ref'],p['num'],p['uuid']],'guarded_SMD_mm':sm,'guarded_every_hole':dr,'pitch':pitch};apertures.append(row)
  if sm<.275 or dr[0]<.275 or pitch[0]<.815:errors.append({'kind':'ordinary_hole_or_pitch',**row})
 elif not via:
  for j in ht.query(body.buffer(.285),predicate='intersects'):
   uid,other,sh=holes[int(j)]
   if other==net:continue
   d=axis.distance(sh)-rad-.005
   if d<.275:errors.append({'kind':'new_track_every_foreign_drill','UUID':item['uuid'],'other':uid,'gap_mm':d,'required_mm':.275})
put(out/'true-new-copper-analytic-ledger.json',checks);put(out/'true-new-copper-errors.json',errors);put(out/'all-seven-ordinary-apertures.json',apertures);print('Q0_R438_TRUE_GEOMETRY',len(checks),len(errors),flush=True)
oldgroupfile=P/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl';assert sha(oldgroupfile)=='ee233fd9010cf3c29d0c4b47503fd93bf754dddf9dd297f9f7c58117c7589742';oldgroups=pickle.loads(oldgroupfile.read_bytes());affected=set(json.loads((candidate/'affected-native-physical-net-list.json').read_bytes()));ctx=K.hole_context(after);oldctx=K.hole_context(before);groups={};contactrows=[];contactbad=[]
for net in sorted(affected):
 if net not in oldgroups:oldgroups[net]=K.physical(before,net,oldctx)[1]
 groups[net]=K.physical(after,net,ctx)[1];rows,bad=K.contact_losses(oldgroups[net],groups[net],removed);contactrows.append({'net':net,'rows':rows});contactbad.extend({'net':net,**row}for row in bad);print('Q0_R438_ACTUAL_GRAPH',net,'lost',len(bad),flush=True)
# Exhaustive unchanged-net identity plus exact physical new-drill exclusion is
# equivalent to recomputing unchanged graphs; no before cache is credited.
oldrec,oldtrees=K.F.build(before);excluded=[];unaffectedbad=[];newholes=[K.Z.bounded_disk(v,v['drill']/2+.005)for v in nv]
for layer in K.LAYERS:
 for i,hole in enumerate(newholes):
  for j in oldtrees[layer].query(hole,predicate='intersects'):
   r=oldrec[layer][int(j)];net=K.L.norm(r['net'])
   if net in affected:continue
   unaffectedbad.append({'net':net,'kind':r['kind'],'uuid':r['uuid'],'layer':layer,'new_drill_UUID':nv[i]['uuid'],'intersection_WKB_sha256':K.C.sha(hole.intersection(r['shape']).wkb)})
for net in sorted(set(oldgroups)-affected):
 groups[net]=oldgroups[net];excluded.append({'net':net,'every_native_discrete_and_filled_definition_exact':True,'every_new_drill_expanded5um_disjoint_from_all_old_raw_Cu':not any(x['net']==net for x in unaffectedbad),'actual_before_group_count':len(oldgroups[net]),'no_new_same_net_Cu_or_FP_or_zone_or_hole_change':True})
put(out/'all-native-net-actual-contact-ledger.json',contactrows);put(out/'unchanged-net-exhaustive-physical-identity-exclusion-ledger.json',excluded);put(out/'unchanged-net-new-drill-physical-overlap-errors.json',unaffectedbad)
roots=[];banks={};oldbanks={}
for net,ref,pin in ROOT.ROOTS+[('/motherboard_do/DOA_FIELD_3V3','U11017','1')]:
 a=K.root(oldgroups[net],ref,pin);n=K.root(groups[net],ref,pin);lost=K.keys(a)-{('track',uid,l)for uid in removed for l in K.LAYERS}-K.keys(n);roots.append({'net':net,'source':[ref,pin],'prior_source_layer_keys_lost':sorted(lost),'before_source_pads':len({r['uuid']for r in a if r['kind']=='pad'}),'after_source_pads':len({r['uuid']for r in n if r['kind']=='pad'})});
 if ref in('J11001','J11003','J11005'):banks[net]=n;oldbanks[net]=a
put(out/'all-ten-actual-source-bank-ledger.json',roots);oldrefs=K.source_refs(oldbanks[GND]);refs=K.source_refs(banks[GND]);beforeRefs={l:oldrefs[l]for l in('F.Cu','B.Cu','In2.Cu','In3.Cu')};afterRefs={l:refs[l]for l in beforeRefs};source=Path(pr['source_native_parent_file']);iv=K.C.inventory(source.read_bytes());hvia={v['uuid']:v for v in h['vias']};oldvia={v['uuid']:v for v in h0['vias']};pairs=json.loads((pd/'six-exact-paired-source-return-nominations.json').read_bytes());pairproof=[];support={};supportrows=[]
for row in pairs:
 sig=hvia[row['signal']];ret=hvia[row['return']];new=sig['uuid']in newids;spacing=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);ann=K.Z.bounded_disk(ret,ret['d']/2).difference(K.Z.bounded_disk(ret,ret['drill']/2));witness={p:ann.buffer(-.025,quad_segs=128).intersection(refs[o]).area for o,p in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};rooted=all(('via',ret['uuid'],l)in K.keys(banks[GND])for l in('In1.Cu','In4.Cu'));pairproof.append({'signal':sig['uuid'],'return':ret['uuid'],'spacing_mm':spacing,'actual_after_return_source_rooted':rooted,'actual_after_annular_interior_mm2':witness,'PASS':.90<=spacing<=1.0 and rooted and all(x>.002 for x in witness.values()),'native_actual_flashes':'OPEN'})
 for outer,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
  if new:
   sh=K.Z.bounded_disk(sig,.525).intersection(oldrefs[outer]);cuts=[K.Z.bounded_disk(v,.1 if K.L.norm(v['net'])==GND else .525)for v in nv if v['uuid']!=sig['uuid']];sh=sh.difference(unary_union(cuts));rad=.525
  elif sig['uuid']=='a01ff36f-ac32-4648-88fe-29a54c58570b':sh,sr=support_FLT(K,before,h,oldbanks[GND],iv,sig,GND,K.L.norm(sig['net']),plane);rad=.575;supportrows.append(sr)
  else:
   assert sig['uuid']=='5a4b7757-ae7c-470d-81fe-abcec92e0f06'and oldvia[sig['uuid']]['flashed']==['F.Cu','B.Cu'];code=(H/'Q0_retained_FLT_source_supported_aperture_r384.py').read_text().replace('support_FLT','support_SENSE').replace('a01ff36f-ac32-4648-88fe-29a54c58570b','5a4b7757-ae7c-470d-81fe-abcec92e0f06').replace('(228.25,157.65,.6,.3)','(228.96,160.412,.5,.2)').replace('.575','.375');ns={};exec(compile(code,str(H/'Q0_retained_FLT_source_supported_aperture_r384.py'),'exec'),ns);sh,sr=ns['support_SENSE'](K,before,h,oldbanks[GND],iv,sig,GND,K.L.norm(sig['net']),plane);sr['actual_reference_layer_old_flash']=False;sr['actual_old_reference_layer_via_width_mm']=.2;supportrows.append(sr);rad=.375
  support[(sig['uuid'],outer)]=sh;supportrows.append({'signal':sig['uuid'],'outer':outer,'actual_reference_plane':plane,'exact_radius_mm':rad,'own_WKB_sha256':K.C.sha(sh.wkb),'new_support_before_actual_root_clipped_only':new})
put(out/'actual-paired-return-and-strong-own-scope-ledger.json',{'pairs':pairproof,'support':supportrows});newref=[];oldloss=[];newpad=[]
for t in nt:
 l=t['layer'];outer='F.Cu'if l in('F.Cu','In2.Cu')else'B.Cu';net=K.L.norm(t['net']);own=unary_union([sh for(uid,o),sh in support.items()if o==outer and K.L.norm(hvia[uid]['net'])==net]);body=K.A.shape({'kind':'segment',**t});raw=body.difference(refs[l]);loss=raw.difference(own);newref.append({'UUID':t['uuid'],'net':t['net'],'layer':l,'raw_gap_mm2':raw.area,'strong_exact_supported_own_only_gap_mm2':loss.area,'strong_exact_supported_own_only_gap_empty':loss.is_empty});
 if not loss.is_empty:(out/(t['uuid']+'-new-reference-gap.wkb')).write_bytes(loss.wkb)
for t in before['tracks']:
 if t['uuid']in removed or t['layer']not in refs or K.L.norm(t['net'])==GND or dom.get(K.L.norm(t['net']))!=dom[GND]:continue
 l=t['layer'];body=K.A.shape({'kind':'segment',**t});delta=oldrefs[l].difference(refs[l]);raw=body.intersection(delta)
 if raw.is_empty:continue
 outer='F.Cu'if l in('F.Cu','In2.Cu')else'B.Cu';own=unary_union([sh for(uid,o),sh in support.items()if o==outer and K.L.norm(hvia[uid]['net'])==K.L.norm(t['net'])]);loss=raw.difference(own);oldloss.append({'UUID':t['uuid'],'net':t['net'],'layer':l,'raw_new_loss_mm2':raw.area,'raw_new_loss_empty':False,'own_bound_only_gap_mm2':loss.area,'own_bound_only_gap_empty':loss.is_empty,'raw_loss_file':str(out/(t['uuid']+'-raw-retained-reference-loss.wkb'))});(out/(t['uuid']+'-raw-retained-reference-loss.wkb')).write_bytes(raw.wkb)
for p in h['pads']:
 if p['ref']=='R10016':
  body=unary_union(K.L.poly(p['layers']['F.Cu']));loss=body.difference(refs['F.Cu']);newpad.append({'UUID':p['uuid'],'pin':p['num'],'net':p['net'],'new_whole_SMD_body_actual_source_reference_gap_mm2':loss.area,'new_whole_SMD_body_gap_empty':loss.is_empty,'new_pad_source_contact_current_DC_loop_SI':'OPEN; no SMD terminal disk waiver'})
put(out/'all-new-track-strong-reference-ledger.json',newref);put(out/'all-retained-FG-body-raw-and-own-bound-reference-ledger.json',oldloss);put(out/'new-translated-SMD-whole-reference-raw-ledger.json',newpad)
joined=any({'8a1e957c-f776-4b05-9e5a-1bcb50251dfd','7b5b05c6-a80d-4cf4-8c24-1674b932a42d'}<={r['uuid']for r in xs if r['kind']=='pad'}for xs in groups['/motherboard_do/DOA_Q0_READY_N']);bad=errors or contactbad or unaffectedbad or any(r['prior_source_layer_keys_lost']for r in roots)or not joined or any(not r['PASS']for r in pairproof)or any(not r['strong_exact_supported_own_only_gap_empty']for r in newref)or any(not r['own_bound_only_gap_empty']for r in oldloss)
result={'verdict':'INDEPENDENT_ACTUAL_FILL_GEOMETRY_SOURCE_CONTACT_STRONG_TRACK_REFERENCE_INCREMENTAL_PASS_Q_NATIVE_PAD_CURRENT_OPEN'if not bad else'INDEPENDENT_Q0_CURRENT_REPAIR_REQUIRED','constructor_receipt_sha256':sha(crp),'actual_filled_only_model_sha256':sha(cm),'source_packet_receipt_sha256':sha(pd/'receipt.json'),'all_actual_net_relationship_count':len(groups),'changed_net_physical_graph_count':len(affected),'new_true_geometry_checks':len(checks),'new_true_geometry_errors':len(errors),'actual_old_contact_group_losses':len(contactbad),'unchanged_net_new_drill_intersections':len(unaffectedbad),'ten_actual_prior_source_keys_lost':sum(len(r['prior_source_layer_keys_lost'])for r in roots),'actual_r06_Q0_pad_relationship_joined':joined,'actual_paired_return_failures':sum(not r['PASS']for r in pairproof),'new_strong_track_reference_failures':sum(not r['strong_exact_supported_own_only_gap_empty']for r in newref),'retained_track_raw_reference_loss_rows':len(oldloss),'retained_track_own_bound_unqualified_loss_rows':sum(not r['own_bound_only_gap_empty']for r in oldloss),'new_SMD_whole_body_reference_rows':newpad,'generated_q_new_antipad_role_replay_current_native_pose_all6_flash_source_parity_refill_all_baselines_DRC_and_SI':'OPEN','all_raw_R155_R368_28_R7_CORE_ROOT42_planner_native_designated_DICpair_failures_preserved':True,'no_reference_radius_expansion_old_SENSE_actual_unflashed_reference_width_bound':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
