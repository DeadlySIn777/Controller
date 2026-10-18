"""Independent sparse-byte rebuild and actual drilled ALL77 joint audit.

Unchanged nets reuse an independently built physical BEFORE graph only after
exact metadata/fill equality and disjointness from every new hole are proved.
No inherited power/current/native failure is converted to acceptance.
"""
import sys,json,pickle,copy,time,math,re,collections
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
import audit_c10036_r24_full_independent_r30 as Q
import physical_reference_losses_r3_zero_r208 as RF
import DIC_source_supported_own_apertures_r200 as OS
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C;LAYERS=Q.LAYERS;GND='/LOGIC_GND';NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER'
O=H/'DIC-C1022-actual-R214-independent-full77-r218'
ROOTS=[('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17'),('/IO_3V3','R18001','2'),('/CORE_1V2','L2001','2')]
MAP={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'}
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def keys(xs):return {(q['kind'],q['uuid'],q['layer']) for q in xs if q['kind']!='fill'}
def root(groups,ref,pin):return next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],str(q['pin']))==(ref,pin) for q in xs))
def hole_context(g):
 holes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128) for v in g['vias']]+[sh for p in g['pads'] for sh in L.poly(p.get('hole')or[])];return holes,STRtree(holes)
def physical(g,net,context):
 rec,_=F.build(g,nets={net});holes,ht=context;uf=A.S.UF();rows=[]
 for layer,xs in rec.items():
  rr=[]
  for row in xs:
   body=row['shape'].difference(unary_union([holes[int(i)] for i in ht.query(row['shape'],predicate='intersects')]))
   for piece in RF.parts(body):
    key=(row['kind'],row['uuid']) if row['kind'] in('pad','via') else(row['kind'],row['uuid'],layer,C.sha(piece.wkb));rr.append({**row,'key':key,'shape':piece})
  tree=STRtree([r['shape']for r in rr])
  for i,row in enumerate(rr):
   uf.find(row['key']);rows.append(row)
   for j in tree.query(row['shape'].buffer(.000002),predicate='intersects'):
    if i<int(j)and row['shape'].distance(rr[int(j)]['shape'])<=.000002:uf.join(row['key'],rr[int(j)]['key'])
 groups=collections.defaultdict(list)
 for row in rows:groups[uf.find(row['key'])].append(row)
 return uf,list(groups.values())
def contact_losses(old,new,removed=()):
 removed=set(removed);mapping=collections.defaultdict(set)
 for i,xs in enumerate(new):
  for key in keys(xs):mapping[key].add(i)
 rows=[];bad=[]
 for i,xs in enumerate(old):
  kk={k for k in keys(xs)if not(k[0]=='track'and k[1]in removed)};groups=set().union(*(mapping.get(k,{'MISSING'})for k in kk))if kk else set();row={'old_group':i,'retained_layer_key_count':len(kk),'candidate_groups':[str(x)for x in sorted(groups,key=str)]};rows.append(row)
  if len(groups)>1 or'MISSING'in groups:bad.append({**row,'all_exact_retained_layer_keys':[list(k)for k in sorted(kk)]})
 return rows,bad
def source_refs(group):return {out:unary_union([q['shape']for q in group if q['kind']=='fill'and q['layer']==inner])for out,inner in MAP.items()}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();A.read(__file__)
 for m in(A,L,F,GE,Z,PS,Q,RF,OS):A.read(m.__file__)
 rp=H/'DIC-C1022-exact-R214-current-construction-r216/receipt.json';receipt=json.loads(A.read(rp));assert C.sha(A.read(rp))=='ad67b39a25d83cf9b0c348e859f2990ce34d2239e41755a841fc3a4bdb0bb11c';basefile=Path(receipt['base_model_file']);raw=A.read(basefile);assert C.sha(raw)==receipt['base_model_sha256']=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h0,b0,q0,before=pickle.loads(raw);q=copy.deepcopy(q0);precision=PS.restore_bound_generated_precision_states(b0,q)
 source=A.read(receipt['source_parent_file']);assert C.sha(source)==receipt['source_parent_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(source);iv=C.inventory(source);op=json.loads(A.read(receipt['exact_operation_file']));assert C.sha(A.read(receipt['exact_operation_file']))==receipt['exact_operation_sha256'];deleted={};added={}
 for row in op:
  ch=A.read(row['exact_chunk_path']);assert C.sha(ch)==row['exact_chunk_sha256'];packet=A.read(row['packet_file']);assert C.sha(packet)==row['packet_sha256'];uid=row['uuid']
  if row['action']=='remove':assert iv[3][uid]==ch and source.count(ch)==1;deleted[uid]=ch
  else:assert row['action']=='add'and uid not in iv[3];added[uid]=ch
 assert len(deleted)==4 and len(added)==26;identity.assert_chunks(added);nt=[];nv=[];oldtracks={t['uuid']:t for t in h0['tracks']}
 for uid,ch in deleted.items():
  p=A.G.parse(uid,ch,{});t=oldtracks[uid];assert(p['net'],p['layer'],p['w'],p['a'],p['b'])==(L.norm(t['net']),t['layer'],t['w'],t['a'],t['b'])
 for uid,ch in added.items():
  p=A.G.parse(uid,ch,{})
  if p['kind']=='segment':nt.append({'uuid':uid,'net':identity.raw(p['net']),'layer':p['layer'],'w':p['w'],'a':p['a'],'b':p['b']})
  else:assert p['kind']=='via'and(p['d'],p['drill'])==(.5,.2);nv.append({'uuid':uid,'net':identity.raw(p['net']),'x':p['at'][0],'y':p['at'][1],'d':p['d'],'drill':p['drill'],'flashed':list(LAYERS)})
 assert len(nt)==21 and len(nv)==5;h=copy.deepcopy(h0);h['tracks']=[t for t in h['tracks']if t['uuid']not in deleted]+nt;h['vias']+=nv;modelraw=A.read(receipt['model_file']);assert C.sha(modelraw)==receipt['model_sha256']=='de159ff0d9abb17eeb787dc7a078e74ea4a2482d6d9cece29a303d8e9f04cf8a';sg,sh,sb,sq,saved=pickle.loads(modelraw);assert h==sh and b0==sb;assert g==sg
 assert len(q)==len(sq)and all(a['uuid']==b['uuid']and all(a[r].wkb==b[r].wkb for r in('shape','zone_outline_shape'))for a,b in zip(q,sq));assert all({k:v for k,v in a.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in b.items()if k not in('shape','zone_outline_shape')}for a,b in zip(q,sq))
 dom=h['domains_normalized'];gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6;zones=[];cutledger=[];affected={L.norm(t['net'])for t in nt+nv}
 for old in before['zones']:
  assert'clearance_mm'in old;local=float(old['clearance_mm']);z={**old,'fills':{}}
  if old['uuid']in iv[3]:
   match=re.search(rb'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',iv[3][old['uuid']]);assert match and float(match.group(1))==local
  for layer,rs in old['fills'].items():
   original=unary_union(L.poly(rs));cuts=[];rows=[]
   for item in nt+nv:
    via='d'in item;same=L.norm(item['net'])==L.norm(z['net'])
    if not via and(item['layer']!=layer or same):continue
    req=max(local,gap(item['net'],z['net']))+.025;radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;cut=Z.bounded_disk(item,radius)if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
    if cut.intersects(original):cuts.append(cut);rows.append({'new_UUID':item['uuid'],'kind':'via'if via else'track','raw_net':item['net'],'same_net_physical_drill_only':bool(same),'analytic_radius_mm':radius,'exact_cutter_WKB_sha256':C.sha(cut.wkb)})
   if cuts:
    final=original.difference(unary_union(cuts));z['fills'][layer]=GE.records(final);affected.add(L.norm(z['net']));cutledger.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'exact_native_or_owned_local_mm':local,'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(final.wkb),'removed_mm2':original.difference(final).area,'actual_split_piece_count':len(GE.records(final)),'cuts':rows})
   else:z['fills'][layer]=rs
  zones.append(z)
 after={**h,'zones':zones};assert after==saved;put(O/'independently-rebuilt-original-fill-cut-ledger.json',cutledger);put(O/'exact-unchanged-generated-role-precision.json',precision);print('R218_EXACT_SPARSE_BYTES_AND_INCREMENTAL_PROJECTION_BOUND',flush=True)
 # True circular caps/annuli are measured analytically against straight old
 # caps, real flashed circles and exact exported pad/graphic polygons.
 records,trees=F.build({**h,'zones':[]});checks=[];errors=[];inherited=[];aperture=[];holelist=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],L.norm(p['net']),s)for p in h['pads']for s in L.poly(p.get('hole')or[])];holes=STRtree([x[2]for x in holelist]);smd=[(p['uuid'],p['ref'],p['num'],s)for p in h['pads']if p['smd']for l,rr in p['layers'].items()if l in('F.Cu','B.Cu')for s in L.poly(rr)];st=STRtree([x[3]for x in smd]);outline=unary_union(L.poly(h['outline'])).buffer(-.525);reserve,exempt=A.reservations();fill_records=[]
 for z in after['zones']:
  for layer,rs in z['fills'].items():
   fill_records.extend({'UUID':z['uuid'],'net':z['net'],'layer':layer,'local':float(z['clearance_mm']),'shape':s,'prospective':z.get('prospective_not_native',False)}for s in L.poly(rs))
 fill_by={layer:[r for r in fill_records if r['layer']==layer]for layer in LAYERS};fill_trees={l:STRtree([r['shape']for r in rr])for l,rr in fill_by.items()}
 def record(kind,item,other,layer,d,req):
  row={'kind':kind,'new_UUID':item['uuid'],'other_UUID':other,'layer':layer,'actual_analytic_gap_mm':d,'guarded_required_mm':req};checks.append(row)
  if d<req:errors.append(row)
 for item in nt+nv:
  via='d'in item;net=L.norm(item['net']);axis=Point(item['x'],item['y'])if via else LineString([item['a'],item['b']]);radius=item['d']/2 if via else item['w']/2;body=Z.bounded_buffer(axis,radius);layers=LAYERS if via else[item['layer']]
  for layer in layers:
   for j in trees[layer].query(body.buffer(.8),predicate='intersects'):
    r=records[layer][int(j)]
    if L.norm(r['net'])==net:continue
    if r['kind']=='via':other=r['source'];distance=axis.distance(Point(other['x'],other['y']))-radius-other['d']/2
    elif r['kind']=='track'and not r['source'].get('m'):other=r['source'];distance=axis.distance(LineString([other['a'],other['b']]))-radius-other['w']/2
    else:distance=axis.distance(r['shape'])-radius
    record('true_new_cap_to_actual_discrete_'+r['kind'],item,r['uuid'],layer,distance,gap(net,r['net'])+.025)
   for j in fill_trees[layer].query(body.buffer(.8),predicate='intersects'):
    r=fill_by[layer][int(j)]
    if L.norm(r['net'])==net:continue
    record('true_new_cap_to_incrementally_projected_actual_fill',item,r['UUID'],layer,axis.distance(r['shape'])-radius,max(r['local'],gap(net,r['net']))+.025)
  if not outline.covers(body):errors.append({'kind':'exact_outline','new_UUID':item['uuid']})
  for rule in h['rule_areas']:
   if set(layers)&set(rule['layers'])and rule.get('no_vias'if via else'no_tracks')and any(body.distance(s)<.025 for s in L.poly(rule['outline'])):errors.append({'kind':'native_rule_area','new_UUID':item['uuid'],'rule_UUID':rule['uuid']})
  for rule in reserve['keepouts']:
   if net not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(body.distance(s)<.025 for s in L.poly(rule['outline'])):errors.append({'kind':'frozen_reserved_area','new_UUID':item['uuid'],'rule':rule['name']})
  if via:
   near=smd[int(st.nearest(axis))];sm=axis.distance(near[3])-item['drill']/2-.005;dr=min((axis.distance(s)-item['drill']/2-.005,uid)for uid,n,s in holelist if uid!=item['uuid']);pitch=min((axis.distance(Point(v['x'],v['y'])),v['uuid'])for v in h['vias']if v['uuid']!=item['uuid']);row={'new_UUID':item['uuid'],'guarded_nearest_SMD_edge_mm':sm,'nearest_SMD':[near[0],near[1],near[2]],'guarded_nearest_every_drill_edge':dr,'nearest_via_pitch':pitch,'required_SMD_drill_mm':.275,'required_pitch_mm':.815};aperture.append(row)
   if sm<.275 or dr[0]<.275 or pitch[0]<.815:errors.append({'kind':'ordinary_SMD_every_hole_pitch',**row})
  else:
   for j in holes.query(body.buffer(.285),predicate='intersects'):
    uid,other,sh=holelist[int(j)]
    if other!=net:record('true_new_track_to_foreign_every_drill',item,uid,item['layer'],axis.distance(sh)-radius-.005,.275)
 put(O/'true-copper-new-incremental-analytic-checks.json',checks);put(O/'true-copper-new-incremental-analytic-errors.json',errors);put(O/'ordinary-aperture-checks.json',aperture);print('R218_NEW_TRUE_CU_AND_EVERY_HOLE',len(checks),len(errors),flush=True)
 # Separate any native-cache guard deficit on unchanged original copper.
 # These are inherited BEFORE facts and cannot be transformed into a pass.
 cutkeys={(r['zone_UUID'],r['layer'])for r in cutledger};old_byid={z['uuid']:z for z in before['zones']};newids=set(added)
 for zid,layer in sorted(cutkeys):
  z=old_byid[zid];oldfill=unary_union(L.poly(z['fills'][layer]));local=float(z['clearance_mm'])
  for j in trees[layer].query(oldfill.buffer(.7),predicate='intersects'):
   r=records[layer][int(j)]
   if r['uuid']in newids or r['uuid']in deleted or L.norm(r['net'])==L.norm(z['net']):continue
   if r['kind']=='via':v=r['source'];d=Point(v['x'],v['y']).distance(oldfill)-v['d']/2
   elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=LineString([t['a'],t['b']]).distance(oldfill)-t['w']/2
   else:d=r['shape'].distance(oldfill)
   req=max(local,gap(z['net'],r['net']))+.025
   if d<req:inherited.append({'kind':'UNCHANGED_BEFORE_PROJECTED_FILL_GUARD_DEFICIT_SEPARATE_NOT_WAIVED','zone_UUID':zid,'layer':layer,'actual_old_Cu_UUID':r['uuid'],'raw_net':r['net'],'before_gap_mm':d,'declared_native_requirement_mm':max(local,gap(z['net'],r['net'])),'new_constructor_guard_requirement_mm':req,'original_native_or_existing_host_projection':not z.get('prospective_not_native',False),'fill_only_retreats_original_Cu_unchanged':True})
 put(O/'inherited-before-native-or-projected-fill-guard-deficits.json',inherited)
 # All77 old physical graphs use drill-subtracted copper and distinct actual
 # split-piece keys. The hole tree is shared only to avoid identical rebuilds.
 oldctx=hole_context(before);newctx=hole_context(after);nets=sorted({L.norm(z['net'])for z in before['zones']}|{'/motherboard_motors/AUX_5V_B'});assert len(nets)==77;assert affected<=set(nets);oldgroups={};newgroups={};ufs={};contacts=[];contactbad=[];direct=[];directbad=[];unchangedproof=[];newholes=[Z.bounded_disk(v,v['drill']/2)for v in nv]
 for net in nets:
  _,a=physical(before,net,oldctx);oldgroups[net]=a
  if net in affected:uf,n=physical(after,net,newctx)
  else:
   for kind in('tracks','vias','pads','shapes'):assert [r for r in before[kind]if L.norm(r['net'])==net]==[r for r in after[kind]if L.norm(r['net'])==net]
   assert [z for z in before['zones']if L.norm(z['net'])==net]==[z for z in after['zones']if L.norm(z['net'])==net]
   assert all(not sh.intersects(r['shape'])for xs in a for r in xs for sh in newholes),'Unchanged-net reuse requires every actual new hole disjoint';uf=None;n=a;unchangedproof.append({'net':net,'all_native_discrete_and_fill_records_exact':True,'every_new_actual_drill_disjoint':True,'physical_BEFORE_graph_reused_without_electrical_assumption':True})
  newgroups[net]=n;ufs[net]=uf;rows,bad=contact_losses(a,n,deleted);contactbad.extend({'net':net,**r}for r in bad);contacts.append({'net':net,'actual_old_drilled_group_count':len(a),'actual_new_drilled_group_count':len(n),'all_old_surviving_layer_relationships':rows,'lost_surviving_layer_relationships':bad})
  if net in affected:
   finalfill=collections.defaultdict(list)
   for xs in n:
    for r in xs:
     if r['kind']=='fill':finalfill[r['uuid'],r['layer']].append(r['shape'])
   for layer in LAYERS:
    metal=[r for xs in a for r in xs if r['layer']==layer and r['kind']!='fill'and r['uuid']not in deleted];tree=STRtree([r['shape']for r in metal])
    for fill in(r for xs in a for r in xs if r['kind']=='fill'and r['layer']==layer and(r['uuid'],layer)in cutkeys):
     for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
      r=metal[int(j)]
      if r['shape'].distance(fill['shape'])>.000002:continue
      hits=[C.sha(s.wkb)for s in finalfill[fill['uuid'],layer]if s.distance(r['shape'])<=.000002];row={'net':net,'old_zone_UUID':fill['uuid'],'layer':layer,'old_actual_drilled_piece_WKB_sha256':C.sha(fill['shape'].wkb),'old_discrete_contact_key':[r['kind'],r['uuid'],layer],'candidate_same_zone_actual_piece_contacts':hits,'direct_contact_retained':bool(hits)};direct.append(row)
      if not hits:directbad.append(row)
  put(O/'all77-contact-checkpoint.json',contacts);print('R218_ALL77_ACTUAL_DRILLED_CONTACT',net,len(bad),'REBUILT'if net in affected else'EXACT_UNCHANGED',flush=True)
 (O/'actual-physical-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));put(O/'all77-contact-rows.json',contacts);put(O/'all77-unchanged-net-reuse-proof.json',unchangedproof);put(O/'complete-direct-layer-fill-contact-ledger.json',direct);put(O/'direct-layer-fill-contact-losses.json',directbad)
 source_rows=[];refs=[];priorcached=pickle.loads(A.read(basefile.parent/'groups.pkl'));inherited_source=[]
 for net,ref,pin in ROOTS:
  a=root(oldgroups[net],ref,pin);n=root(newgroups[net],ref,pin);lost=sorted(keys(a)-keys(n));source_rows.append({'net':net,'actual_source':ref+'.'+pin,'all_prior_source_layer_keys_lost':[list(k)for k in lost],'actual_old_rooted_named_pad_UUID_count':len({r['uuid']for r in a if r['kind']=='pad'and r['pin']}),'actual_new_rooted_named_pad_UUID_count':len({r['uuid']for r in n if r['kind']=='pad'and r['pin']}),'current_native_fault_thermal_A_load_qualification':'OPEN'})
  cached=root(priorcached[net],ref,pin);lk=sorted(keys(cached)-keys(a));inherited_source.append({'net':net,'source':ref+'.'+pin,'cached_undrilled_before_keys_absent_actual_drilled_before':[list(k)for k in lk],'inherited_BEFORE_only_never_waived':True})
  if ref in('J11001','J11003','J11005'):
   bad,proof=RF.audit(before,source_refs(a),source_refs(n),net,removed=deleted);refs.append({'net':net,'strict_zero_old_full_body_reference_losses':bad,'zero_threshold_delta_proof':proof})
 put(O/'seven-actual-source-rows.json',source_rows);put(O/'inherited-before-cached-versus-actual-drilled-source-failures.json',inherited_source);put(O/'three-bank-zero-old-full-body-reference-rows.json',refs);print('R218_SEVEN_SOURCE_AND_THREE_BANK_ZERO_REFERENCE_DONE',flush=True)
 lg_old=root(oldgroups[GND],'J11001','2');lg_new=root(newgroups[GND],'J11001','2');oldrefs=source_refs(lg_old);newrefs=source_refs(lg_new);dpacket=json.loads(A.read(H/'DIC-native-owned-ledger-r212/receipt.json'));vby={v['uuid']:v for v in h['vias']};own=[];pairs=[];sourcekeys=keys(lg_new)
 for row in dpacket['actual_source_paired_returns']:
  sig=vby[row['signal_UUID']];ret=vby[row['return_UUID']];radius=.575 if L.norm(sig['net'])==CMD else.525;assert radius==row['unchanged_exact_own_radius_mm'];dist=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);ann=Point(ret['x'],ret['y']).buffer(.25,quad_segs=128).difference(Point(ret['x'],ret['y']).buffer(.1,quad_segs=128));areas={plane:ann.intersection(newrefs[layer].buffer(-.075,quad_segs=128)).area for layer,plane in(('F.Cu','In1.Cu'),('B.Cu','In4.Cu'))};joined=all(('via',ret['uuid'],plane)in sourcekeys for plane in('In1.Cu','In4.Cu'));p={'signal_UUID':sig['uuid'],'return_UUID':ret['uuid'],'actual_signal_at_mm':[sig['x'],sig['y']],'actual_return_at_mm':[ret['x'],ret['y']],'actual_J1_rooted_In1_In4_annuli':joined,'finite_interior_annular_area_mm2':areas,'actual_distance_mm':dist,'own_radius_mm':radius,'radius_expansion_mm':0,'native_actual_flash_fill':'OPEN'};pairs.append(p)
  if joined and .815<=dist<=1 and all(a>.004 for a in areas.values()):own.append((sig['uuid'],L.norm(sig['net']),Z.bounded_disk(sig,radius)))
 supported,ownproof=OS.scopes(before,h,lg_old,oldrefs,own,iv);newrefs_rows=[];newrefs_errors=list(ownproof['errors'])
 for t in nt:
  layer=t['layer'];body=A.shape({'kind':'segment',**t});allow=newrefs[layer].union(supported.get((L.norm(t['net']),layer),Point()));missing=body.difference(allow);row={'new_UUID':t['uuid'],'raw_net':t['net'],'used_layer':layer,'actual_J1_reference_layer':MAP[layer],'full_body_gap_mm2':missing.area,'gap_empty':missing.is_empty,'full_body_WKB_sha256':C.sha(body.wkb),'source_supported_own_scope_only':True};newrefs_rows.append(row)
  if not missing.is_empty:(O/(t['uuid']+'-new-body-reference-gap.wkb')).write_bytes(missing.wkb);newrefs_errors.append(row)
 actual_targets=[]
 for net,wanted in((NET,{'c9bab2fa-e6cb-45f7-b879-a934865b0e12','73d7d605-feb4-47ae-b36a-40896fba4ee9'}),('/IO_3V3',set())):
  if wanted:joined=any(wanted<={r['uuid']for r in xs if r['kind']=='pad'}for xs in newgroups[net]);actual_targets.append({'net':net,'native_r06_actual_pad_UUIDs':sorted(wanted),'joined_actual_drilled_host':joined})
 io=root(newgroups['/IO_3V3'],'R18001','2');actual_targets.append({'net':'/IO_3V3','actual_source':'R18001.2','target':'C1022.1','joined_actual_drilled_host':any(r['kind']=='pad'and(r['ref'],str(r['pin']))==('C1022','1')for r in io)})
 put(O/'three-real-paired-returns-after-combined-holes.json',pairs);put(O/'combined-source-supported-own-aperture-ledger.json',ownproof);put(O/'all21-new-body-source-reference-rows.json',newrefs_rows);put(O/'all21-new-body-source-reference-errors.json',newrefs_errors);put(O/'actual-recovered-target-source-rows.json',actual_targets)
 # Current/r06/r07 selected signal guards remain actual native pad identities.
 padmap={};counts=collections.Counter()
 for p in before['pads']:
  label=p['ref']+'.'+str(p['num']);i=counts[label];counts[label]+=1;padmap[label+'#'+str(i)]=p['uuid']
 nativeguards=[];padloss=[]
 for label,path in(('current198b',A.G.REPORT/'measure/r07-four-fag-shared/partitions.json'),('r06',A.P.R.R06_PART),('r07',A.P.R.R07_PART)):
  native={L.norm(net):groups for net,groups in json.loads(A.read(path))['nets'].items()}
  for net in sorted({L.norm(t['net'])for t in nt if L.norm(t['net'])!='/IO_3V3'}):
   for relation in native[net]:
    wanted={padmap[x]for x in relation};joined=any(wanted<={r['uuid']for r in xs if r['kind']=='pad'}for xs in newgroups[net]);row={'baseline':label,'net':net,'exact_native_pad_labels':relation,'actual_pad_UUIDs':sorted(wanted),'joined_actual_drilled_host':joined};nativeguards.append(row)
    if not joined:padloss.append(row)
 put(O/'current-r06-r07-signal-native-pad-guards.json',nativeguards);newfail=errors or contactbad or directbad or any(r['all_prior_source_layer_keys_lost']for r in source_rows)or any(r['strict_zero_old_full_body_reference_losses']for r in refs)or newrefs_errors or padloss or len(own)!=3 or not all(r['joined_actual_drilled_host']for r in actual_targets);result={'verdict':'EXACT_R214_C1022_DIC_INCREMENTAL_ALL77_SEVEN_SOURCE_ZERO_REFERENCE_NEW_BODY_PASS_FULL_PRODUCTION_OPEN'if not newfail else'EXACT_R214_C1022_DIC_INCREMENTAL_ALL77_SEVEN_SOURCE_ZERO_REFERENCE_OR_NEW_BODY_FAIL','constructor_receipt_file':str(rp),'constructor_receipt_sha256':C.sha(A.read(rp)),'base_R214_model_sha256':C.sha(raw),'new_current_model_file':receipt['model_file'],'new_current_model_sha256':C.sha(modelraw),'all26_add_four_delete_exact_source_bytes_rebuilt':True,'all_untouched_R214_Cu_FP_pad_native_design_zone_rule_project_and_generated_roles_exact':True,'independent_incremental_projection_matches_every_saved_fill_record':True,'all77_actual_drilled_old_contact_losses':contactbad,'direct_actual_old_layer_fill_contact_losses':directbad,'seven_source_layer_key_loss_count':sum(len(r['all_prior_source_layer_keys_lost'])for r in source_rows),'strict_ZERO_old_reference_loss_count':sum(len(r['strict_zero_old_full_body_reference_losses'])for r in refs),'new_full_body_reference_errors':newrefs_errors,'actual_native_signal_pad_losses':padloss,'new_true_Cu_geometry_errors':errors,'real_qualified_paired_returns':len(own),'actual_target_rows':actual_targets,'inherited_BEFORE_native_or_projected_fill_guard_deficit_count':len(inherited),'inherited_BEFORE_cached_source_keys_absent_actual_drilled_source_count':sum(len(r['cached_undrilled_before_keys_absent_actual_drilled_before'])for r in inherited_source),'original_ROOT42_raw_reference_power_and_current_failures':'OPEN/FAIL UNMODIFIED; incremental PASS is not blanket production/current/native qualification','all_signed_supply_loads_A_barrel_mesh_inductive_loop_fault_thermal_SI_and_native_full_board':'OPEN','native_exact_raw_net_IU_every_FP_and_actual_all6_new_via_flash_full_fill_DRC_allnets_r06_r07':'OPEN','host_retained_relationships_production_flags_modified':False,'read_files_sha256':A.READS,'output_files_sha256':{str(p):C.sha(p.read_bytes())for p in O.iterdir()if p.is_file()and p.name!='receipt.json'},'native_jobs':0,'board_written':False,'source_or_project_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',result);print(json.dumps({'receipt_sha256':C.sha((O/'receipt.json').read_bytes()),'verdict':result['verdict'],'all77_contact_losses':len(contactbad),'direct_fill_losses':len(directbad),'seven_source_losses':result['seven_source_layer_key_loss_count'],'zero_old_ref_losses':result['strict_ZERO_old_reference_loss_count'],'new_ref_errors':len(newrefs_errors),'geometry_errors':len(errors),'inherited_before_guard_deficits':len(inherited)}),flush=True)
if __name__=='__main__':main()
