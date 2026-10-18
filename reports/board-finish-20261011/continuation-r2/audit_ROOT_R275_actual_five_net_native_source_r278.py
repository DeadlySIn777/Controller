"""Audit observed selected native fill against actual R157, never host fills."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,sys,time,collections,math
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as R
import guarded_power_projection_r44 as Z
K=N.K;L=N.L;sha=N.sha
OUT=H/'R275-actual-selected-native-five-net-source-body-reference-audit-r278'
NF=H/'U10003-HOST-R271-selected-actual-native-LG-FG-IO3-r275/selected-fill'
AP=H/'R275-exact-R155-parent-plus-only-ROOT-native-header-context-r276/context.pkl'
BP=H/'R275-actual-R157-fresh-five-net-BEFORE-cache-r277'
SP=H/'U10003-HOST-R157-exact-sparse-native-API-clone-r271/copy/board.kicad_pcb'
FG='/motherboard_motors/FIELD_GND';LG='/LOGIC_GND';IO='/IO_3V3'
HOST='/motherboard_do/DOA_SDI_HOST';FLT='/motherboard_do/DOA_FLT_N_FIELD'
CLK='/motherboard_do/DOA_SCLK_FIELD';NETS={FG,LG,IO,HOST,FLT}
def put(name,value):
 (OUT/name).write_text(json.dumps(value,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return R.shapeinfo(s)
def savegap(label,s):
 if not s.is_empty:(OUT/(label+'.wkb')).write_bytes(s.wkb)
def drilled(shape,ctx):
 return shape.difference(unary_union([ctx[0][int(i)]for i in ctx[1].query(shape,predicate='intersects')]))

def main():
 assert (NF/'receipt.json').exists(),'Native R275 still running; no substitute fill permitted'
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();R.OUT=OUT
 assert sha(AP)=='b1d133c5a7f91c791ae8aafa2e710404274f449989ce117e6378eac2f77b067e'
 assert sha(BP/'receipt.json')=='6182167ca6152e07941b7b66c138b40d5a0c13e68f4e541ff58b41d5b6257ed3'
 assert sha(SP)=='deee57788a5ba62ede98730231377069936d5474bb527e6dbed0b832ae6c8d38'
 br=json.loads((BP/'receipt.json').read_bytes());assert sha(BP/'actual-R157-five-net-model.pkl')==br['actual_model_SHA256'];assert sha(BP/'actual-R157-five-affected-net-groups.pkl')==br['groups_SHA256']
 before=pickle.loads((BP/'actual-R157-five-net-model.pkl').read_bytes());oldgroups=pickle.loads((BP/'actual-R157-five-affected-net-groups.pkl').read_bytes())
 g,h,b,q,c=pickle.loads(AP.read_bytes());nr=json.loads((NF/'receipt.json').read_bytes());assert nr['candidate_SHA256']==sha(SP);assert not nr['all_discrete_post_fill_errors'];assert sha(NF/'geometry.json')==nr['actual_geometry_SHA256'];assert sha(NF/'actual-via-flashes.json')==nr['actual_via_flashes_SHA256']
 api=H/'U10003-HOST-layer-aware-native-API-r274/native-joint-API.json';api_result=json.loads(api.read_bytes());assert api_result['candidate_SHA256']==sha(SP);assert not api_result['errors']
 ng=json.loads((NF/'geometry.json').read_bytes());flashes=json.loads((NF/'actual-via-flashes.json').read_bytes())['vias']
 after,ctx,padledger=N.convert_selected_actual(h,c,ng,flashes,NETS,source_pcb=SP)
 oldt={t['uuid']:t for t in before['tracks']};newt={t['uuid']:t for t in after['tracks']};oldv={v['uuid']:v for v in before['vias']};newv={v['uuid']:v for v in after['vias']}
 op=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/full-sparse-operation.pkl';d=pickle.loads(op.read_bytes());removed={t['uuid']for t in d['removed_original_tracks']};newids={t['uuid']for t in d['new_tracks']}
 assert len(removed)==6 and len(newids)==13 and set(newt)==set(oldt)-removed|newids
 nt=[newt[u]for u in sorted(newids)];restored=newt['06f5b2a7-dc39-4a5d-9309-5badd13a2347'];assert restored==oldt[restored['uuid']]
 assert set(newv)==set(oldv)|{v['uuid']for v in d['new_vias']}
 groups={};relationships=[];direct=[];source=[];roots={};sourcechanges=[]
 sourcepins={LG:('J11001','2'),FG:('J11003','2'),IO:('R18001','2')}
 for net in sorted(NETS):
  put('status.json',{'phase':'FRESH_ACTUAL_NATIVE_GROUPS','net':net,'completed':list(groups)})
  xs=K.physical(after,net,ctx)[1];groups[net]=xs;old=oldgroups[net];rows,bad=K.contact_losses(old,xs,removed)
  relationships.append({'net':net,'actual_before_groups':len(old),'actual_after_groups':len(xs),'old_relationships':rows,'losses':bad})
  for ly in K.LAYERS:
   oldfills=[r for gr in old for r in gr if r['kind']=='fill'and r['layer']==ly];newfills=[r for gr in xs for r in gr if r['kind']=='fill'and r['layer']==ly]
   ot=STRtree([r['shape']for r in oldfills]);at=STRtree([r['shape']for r in newfills]);metal=collections.defaultdict(list);now=collections.defaultdict(list)
   for gr in old:
    for r in gr:
     if r['kind']!='fill'and r['layer']==ly and r['uuid']not in removed and not(r['kind']=='pad'and r.get('ref')=='R10007'):metal[r['kind'],r['uuid'],ly].append(r['shape'])
   for gr in xs:
    for r in gr:
     if r['kind']!='fill'and r['layer']==ly:now[r['kind'],r['uuid'],ly].append(r['shape'])
   for key,shapes in metal.items():
    body=unary_union(shapes);hits=[oldfills[int(i)]for i in ot.query(body.buffer(.000002),predicate='intersects')if body.distance(oldfills[int(i)]['shape'])<=.000002]
    if not hits:continue
    nb=unary_union(now.get(key,[]));nh=[]if nb.is_empty else[newfills[int(i)]for i in at.query(nb.buffer(.000002),predicate='intersects')if nb.distance(newfills[int(i)]['shape'])<=.000002]
    direct.append({'net':net,'key':list(key),'old_touching_zone_UUIDs':sorted({r['uuid']for r in hits}),'after_touching_zone_UUIDs':sorted({r['uuid']for r in nh}),'ANY_same_net_actual_fill_touch_retained':bool(nh),'old_same_zone_touches_not_retained':sorted({r['uuid']for r in hits}-{r['uuid']for r in nh})})
  if net in sourcepins:
   ref,pin=sourcepins[net];ar=K.root(xs,ref,pin);orr=K.root(old,ref,pin);roots[net]=ar;lost=K.keys(orr)-K.keys(ar)-{('track',u,l)for u in removed for l in K.LAYERS}
   source.append({'net':net,'source':ref+'.'+pin,'before_named_pads':R.countpad(orr),'after_named_pads':R.countpad(ar),'prior_source_keys_lost':[list(k)for k in sorted(lost)]})
   for ly in K.LAYERS:
    ob=unary_union([r['shape']for r in orr if r['kind']=='fill'and r['layer']==ly]);ab=unary_union([r['shape']for r in ar if r['kind']=='fill'and r['layer']==ly]);loss=ob.difference(ab);gain=ab.difference(ob)
    sourcechanges.append({'net':net,'layer':ly,'old_source_Cu':ds(ob),'actual_new_source_Cu':ds(ab),'literal_source_Cu_not_retained':ds(loss),'explicit_actual_source_Cu_gained':ds(gain)})
    savegap(net.rsplit('/',1)[-1]+'-'+ly+'-actual-source-Cu-loss',loss)
  print('R278_ACTUAL',net,'groups',len(old),len(xs),'old_relationship_losses',len(bad),flush=True)
  put('checkpoint-old-relationships.json',relationships);put('checkpoint-source-keys.json',source)
 gp=OUT/'actual-five-net-all-drilled-after-groups.pkl';gp.write_bytes(pickle.dumps(groups,protocol=5));mp=OUT/'actual-five-net-after-model.pkl';mp.write_bytes(pickle.dumps(after,protocol=5));put('exact-native-pad-bindings.json',padledger)
 oldrefs=[]
 # Exact six declared retired FLT tracks are absent; every retained original
 # signal uses its original source support, including zero-area witnesses.
 reference_before={**before,'tracks':[t for t in before['tracks']if t['uuid']not in removed]}
 for ground in (LG,FG):
  ref,pin=sourcepins[ground];oldroot=K.root(oldgroups[ground],ref,pin);rows,proof=R.exact_reference_delta(reference_before,K.source_refs(oldroot),K.source_refs(roots[ground]),ground)
  oldrefs.append({'ground':ground,'strict_original_body_reference_losses':rows,'proof':proof})
 hp=H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';assert sha(hp)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402';hostpack=pickle.loads(hp.read_bytes())
 capspec={HOST:[(hostpack['vias'][0]['uuid'],hostpack['new_signal_exact_own_cap_mm']),(hostpack['source_terminal_UUID'],hostpack['source_terminal_exact_own_cap_mm'])],FLT:[('7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4',.525),('2938cbdd-1d38-4238-9455-504b30f06e5e',.575)],CLK:[('1f45e002-4f40-4087-bbed-3be260272d8f',.375)]}
 bodies=[]
 for t in nt+[restored]:
  net=L.norm(t['net']);ground=LG if net in (HOST,LG)else FG;rr=K.source_refs(roots[ground]);ly=K.MAP[t['layer']];body=drilled(K.A.shape({'kind':'segment',**t}),ctx);caps=unary_union([Z.bounded_disk(newv[u],rad)for u,rad in capspec.get(net,[])])
  gm=unary_union([r['shape']for r in roots[ground]if r['kind']=='via'and r['layer']==ly])if net==ground else unary_union([]);gap=body.difference(rr[t['layer']].union(caps).union(gm));bodies.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'source_reference_layer':ly,'actual_body':ds(body),'literal_gap_outside_ONLY_exact_own_caps_or_actual_source_ground_annuli':ds(gap),'exact_named_caps':capspec.get(net,[])})
  savegap(t['uuid']+'-actual-new-body-reference-gap',gap)
 shared=next(v['uuid']for v in d['new_vias']if L.norm(v['net'])==FG and v['uuid']!='73811c12-9f84-5491-bfee-0c5ee985a7a8')
 pairs=[('1f45e002-4f40-4087-bbed-3be260272d8f',shared,FG),('7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4',shared,FG),('2938cbdd-1d38-4238-9455-504b30f06e5e','73811c12-9f84-5491-bfee-0c5ee985a7a8',FG),(hostpack['vias'][0]['uuid'],hostpack['existing_ground_return_UUID'],LG)];returns=[]
 for su,ru,ground in pairs:
  sv,rv=newv[su],newv[ru];root=roots[ground];kk=K.keys(root);distance=math.hypot(sv['x']-rv['x'],sv['y']-rv['y']);annuli=[]
  for ly in ('In1.Cu','In4.Cu'):
   ann=unary_union([r['shape']for r in root if r['kind']=='via'and r['uuid']==ru and r['layer']==ly]);fill=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly]);hit=ann.intersection(fill)
   annuli.append({'layer':ly,'actual_flash_observed':ly in flashes[ru],'actual_source_key':('via',ru,ly)in kk,'finite_annulus_source_contact':ds(hit),'pass':ly in flashes[ru]and ('via',ru,ly)in kk and not hit.is_empty and hit.area>0})
  returns.append({'signal_UUID':su,'ground_UUID':ru,'source':ground,'distance_mm':distance,'ordinary_distance_pass':.9<=distance<=1,'actual_both_layer_annuli':annuli,'both_actual_source_contacts_pass':all(r['pass']for r in annuli)})
 smds=[]
 for p in after['pads']:
  if p['ref']!='R10007':continue
  assert p['smd']and set(p['layers'])=={'B.Cu'};body=drilled(unary_union(L.poly(p['layers']['B.Cu'])),ctx);rr=K.source_refs(roots[LG]);gap=body.difference(rr['B.Cu']);smds.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'actual_native_pose_mm':[p['x'],p['y']],'actual_B_body':ds(body),'whole_actual_J1_In4_support_gap':ds(gap)});savegap(p['uuid']+'-actual-SMD-In4-gap',gap)
 terminal=[]
 for net,requirements in ((HOST,[('R10007','1'),('U10003','3'),('U13004','31')]),(FG,[('U10003','9'),sourcepins[FG]]),(LG,[('R10007','2'),sourcepins[LG]])):
  ref,pin=requirements[-1];root=K.root(groups[net],ref,pin);present={(r.get('ref'),str(r.get('pin')))for r in root if r['kind']=='pad'};terminal.append({'net':net,'source_anchor':ref+'.'+pin,'required_actual_pad_terminals':[a+'.'+b for a,b in requirements],'missing_actual_pad_terminals':[a+'.'+b for a,b in requirements if (a,b)not in present]})
 put('all-actual-old-relationships.json',relationships);put('all-actual-old-direct-fill-contacts.json',direct);put('all-actual-source-bank-keys.json',source);put('all-six-layer-literal-source-Cu-deltas.json',sourcechanges);put('all-strict-old-routed-reference-deltas.json',oldrefs);put('all-new-plus-restored-clock-actual-body-references.json',bodies);put('ordinary-four-actual-source-return-pairs.json',returns);put('moved-R10007-native-SMD-source-body-support.json',smds);put('actual-source-terminal-obligations.json',terminal)
 counts={'old_relationship_losses':sum(len(r['losses'])for r in relationships),'old_direct_fill_contact_losses':sum(not r['ANY_same_net_actual_fill_touch_retained']for r in direct),'old_source_key_losses':sum(len(r['prior_source_keys_lost'])for r in source),'strict_old_routed_reference_losses':sum(len(r['strict_original_body_reference_losses'])for r in oldrefs),'new_body_reference_losses':sum(not r['literal_gap_outside_ONLY_exact_own_caps_or_actual_source_ground_annuli']['EMPTY']for r in bodies),'ordinary_return_failures':sum(not(r['ordinary_distance_pass']and r['both_actual_source_contacts_pass'])for r in returns),'moved_SMD_body_gaps':sum(not r['whole_actual_J1_In4_support_gap']['EMPTY']for r in smds),'actual_terminal_obligation_failures':sum(bool(r['missing_actual_pad_terminals'])for r in terminal),'prior_actual_selected_ground_mask_losses':len(nr['prior_R157_actual_selected_ground_flash_losses'])}
 files=[Path(__file__),AP,BP/'receipt.json',BP/'actual-R157-five-net-model.pkl',BP/'actual-R157-five-affected-net-groups.pkl',SP,NF/'receipt.json',NF/'geometry.json',NF/'actual-via-flashes.json',api,op,hp,Path(N.__file__),Path(R.__file__)]
 record={'status':'R275_ACTUAL_NATIVE_FIVE_NET_SOURCE_CONTACT_BODY_REFERENCE_SCOPED_PASS_OTHER_GATES_OPEN'if not any(counts.values())else'R275_ACTUAL_NATIVE_SOURCE_CONTACT_BODY_REFERENCE_REPAIR_REQUIRED','counts':counts,'fresh_actual_zone_fill_scope':[LG,FG,IO],'five_affected_physical_graphs':sorted(NETS),'HOST_FLT_no_claim_of_unselected_plane_refill':True,'exact_six_original_FLT_retirements':[u for u in sorted(removed)],'all_original_other_Cu_API_exact':True,'no_source_arrays_or_masks_forced':True,'literal_source_Cu_loss_layers':sum(not r['literal_source_Cu_not_retained']['EMPTY']for r in sourcechanges),'any_raw_source_Cu_loss_keeps_current_unqualified':True,'old_same_zone_touch_difference_count':sum(bool(r['old_same_zone_touches_not_retained'])for r in direct),'old_same_zone_differences_retained':True,'after_actual_model_SHA256':sha(mp),'after_actual_groups_SHA256':sha(gp),'source_header_from_exact_R155_plus_only_ROOT':True,'full_CPP_full_board_DRC':'OPEN','actual_native_source_GAIN_against_full_R157_foreign_filled_Cu_guards':'OPEN_SEPARATE_GATE','original_HOST575_finite_same_In4_source_path':'OPEN_RECHECK_ON_THIS_ACTUAL_NATIVE','native_SI_current_thermal_plating_all_other_nets':'OPEN_OR_FAIL_RETAINED','raw_R255_R257_witness_not_automatically_waived_for_new_native':True,'input_SHA256':{str(f.resolve()):sha(f)for f in files},'native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
 put('receipt.json',record);put('status.json',{'phase':'COMPLETE','counts':counts});print('R278_COMPLETE',sha(OUT/'receipt.json'),record['status'],counts,flush=True)
if __name__=='__main__':main()
