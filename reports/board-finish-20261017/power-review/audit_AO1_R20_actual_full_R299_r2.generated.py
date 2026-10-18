"""Independent AO1 scoped rebuild from actual full native baseline.

Native normal antipads are prospective HOST geometry only. The exact current
R753 AO1 discrete identity is checked; other current domains/full AFTER native
fill, actual new masks, current/analog/SI remain separate open gates.
"""
from pathlib import Path
import os
for variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[variable]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
import sys,json,pickle,hashlib,time,math,copy
H=Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261011\\continuation-r2\\coupled-recovery');ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
OUT=Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261017\\power-review\\AO1-R20-actual-full-R299-requalification-r2')
COM='/motherboard_analog_output/AO1_COM';VREF='/motherboard_analog_output/AO1_VREF';MON='/motherboard_analog_output/AO1_MON_12V'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in pieces(g)]if hasattr(s,'geoms')else[]
def records(s):return[[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in pieces(s)]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def axis(t):return Point(t['x'],t['y'])if'd'in t else LineString([t['a'],t['b']])
def rad(t):return t['d']/2 if'd'in t else t['w']/2
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,w=None):
  p=Path(p);v=sha(p);assert w is None or v==w;pins[str(p.resolve())]=v;return p
 rr=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/receipt.json');r=json.loads(rr.read_bytes());assert r['controlled_power_path'];pf=pin(r['packet_file'],r['packet_SHA256']);p=pickle.loads(pf.read_bytes());bp=pin(Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261017\\actual-full-audit-repaired-r1\\r763\\actual-combined-full-after-model.pkl'),'c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806');before=pickle.loads(bp.read_bytes());bgf=pin(bp.parent/'actual-combined-full-after-all-net-groups.pkl','c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd');bg=pickle.loads(bgf.read_bytes());ep=pin(ROOT/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json','13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3');expected=json.loads(ep.read_bytes())['copper'];nt=p['tracks'];nv=p['vias'];removed=set(p['deleted_original_chunks']);assert len(removed)==4 and len(nt)==14 and len(nv)==2
 source=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');ident=K.A.N.SourceNets(source.read_bytes());iv=K.C.inventory(source.read_bytes())[3]
 assert {u:iv[u]for u in removed}==p['deleted_original_chunks'];ident.assert_chunks(p['exact_new_chunks']);assert set(p['exact_new_chunks']).isdisjoint(iv)
 for t in nt:
  item=K.A.G.parse(t['uuid'],p['exact_new_chunks'][t['uuid']],{});assert (item['net'],item['layer'],item['a'],item['b'],item['w'])==(K.L.norm(t['net']),t['layer'],t['a'],t['b'],t['w']);assert (b'(locked yes)'in p['exact_new_chunks'][t['uuid']])==bool(t.get('locked_yes',False))
 aobase=[t for t in before['tracks']if K.L.norm(t['net']).startswith('/motherboard_analog_output/AO1')]+[v for v in before['vias']if K.L.norm(v['net']).startswith('/motherboard_analog_output/AO1')]
 for t in aobase:
  e=expected[t['uuid']];assert e['raw_net']==t['net']
  if'd'in t:assert e['at_IU']==[round(t['x']*1e6),round(t['y']*1e6)]and e['drill_IU']==round(t['drill']*1e6)and set(e['diameters_IU'].values())=={round(t['d']*1e6)}
  else:assert e['start_IU']==[round(x*1e6)for x in t['a']]and e['end_IU']==[round(x*1e6)for x in t['b']]and e['width_IU']==round(t['w']*1e6)and e['layer']==t['layer']
 raw={'tracks':[t for t in before['tracks']if t['uuid']not in removed]+nt,'vias':before['vias']+nv};header={**before,**raw};dom=before['domains_normalized'];gap=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else .6;cutledger=[];zones=[];affected={COM,VREF,MON};allrawgain=[]
 for z in before['zones']:
  nz={**z,'fills':{}};local=float(z['clearance_mm'])
  for ly,rs in z['fills'].items():
   cut=[];cr=[]
   for t in nt+nv:
    same=K.L.norm(t['net'])==K.L.norm(z['net']);via='d'in t
    if not via and(t['layer']!=ly or same):continue
    radius=t['drill']/2 if via and same else rad(t)+max(local,gap(t['net'],z['net']))
    sh=K.Z.bounded_disk(t,radius)if via else K.Z.bounded_buffer(axis(t),radius)
    if any(not sh.envelope.disjoint(s.envelope)for s in K.L.poly(rs)):cut.append(sh);cr.append({'new_UUID':t['uuid'],'native_local_clearance_mm':local,'analytic_native_normal_cut_radius_mm':radius,'source_physical_drill_only':via and same,'planner_extra_applied_to_native_antipad':False,'outward_numerical_buffer_mm':K.Z.OUTWARD_MM})
   if not cut:nz['fills'][ly]=rs;continue
   mask=unary_union(cut);newrs=[];changed=False
   for index,(record,sh)in enumerate(zip(rs,K.L.poly(rs))):
    if not mask.intersects(sh):newrs.append(record);continue
    aft=sh.difference(mask);gain=aft.difference(sh);loss=sh.difference(aft);changed|=not loss.is_empty
    row={'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':ly,'record':index,'before_WKB_SHA256':hashlib.sha256(sh.wkb).hexdigest(),'after_WKB_SHA256':hashlib.sha256(aft.wkb).hexdigest(),'literal_positive_gain':info(gain),'removed':info(loss),'cutters':cr,'all_UNCHANGED_record_arrays_retained':True};cutledger.append(row)
    if not gain.is_empty:allrawgain.append(row)
    newrs.extend(records(aft))
   nz['fills'][ly]=newrs
   if changed:affected.add(K.L.norm(z['net']))
  zones.append(nz)
 after={**header,'zones':zones};put('normal-native-profile-prospective-antipad-per-record-ledger.json',cutledger);put('raw-per-record-positive-gain-FAIL-ledger.json',allrawgain);put('status.json',{'phase':'ALL_NEW_TRUE_GEOMETRY','affected_nets':len(affected)})
 context=K.hole_context(after);rec,trees=K.F.build({**after,'zones':[]});checks=[];errors=[];holes=[]
 for v in after['vias']:holes.append((v['uuid'],K.L.norm(v['net']),False,Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for pad in after['pads']:
  for sh in K.L.poly(pad.get('hole')or[]):holes.append((pad['uuid'],K.L.norm(pad['net']),pad['npth'],sh))
 ht=STRtree([q[3]for q in holes]);smd=[(q,s)for q in after['pads']if q['smd']for ly,rrs in q['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rrs)];smt=STRtree([q[1]for q in smd]);reserve,exempt=K.A.reservations();outline=unary_union(K.L.poly(after['outline']))
 def check(row,ok):
  checks.append(row)
  if not ok:errors.append(row)
 for t in nt+nv:
  ax=axis(t);radius=rad(t);net=K.L.norm(t['net']);lyrs=K.LAYERS if'd'in t else[t['layer']];body=K.Z.bounded_buffer(ax,radius)
  for ly in lyrs:
   for i in trees[ly].query(body.buffer(.8),predicate='intersects'):
    q=rec[ly][int(i)]
    if q['uuid']==t['uuid']or K.L.norm(q['net'])==net:continue
    if q['kind']in('track','via'):d=ax.distance(axis(q['source']))-radius-rad(q['source'])
    else:d=ax.distance(q['shape'])-radius
    req=gap(t['net'],q['net'])+.025;check({'kind':'true_discrete_Cu','UUID':t['uuid'],'other_UUID':q['uuid'],'layer':ly,'gap_mm':d,'required_mm':req},d>=req)
  for i in ht.query(body.buffer(.285),predicate='intersects'):
   uid,hnet,np,sh=holes[int(i)]
   if uid==t['uuid']or not np and hnet==net and'd'not in t:continue
   d=ax.distance(sh)- (t['drill']/2 if'd'in t else radius);check({'kind':'all-physical-drill','UUID':t['uuid'],'other_UUID':uid,'gap_mm':d,'required_mm':.275},d>=.275)
  if'd'in t:
   pt=Point(t['x'],t['y']);i=int(smt.nearest(pt));q,sh=smd[i];d=pt.distance(sh)-t['drill']/2-.005;check({'kind':'ordinary_all_SMD_drill_after_native_ERROR_INSIDE_bound_5um','UUID':t['uuid'],'nearest_pad_UUID':q['uuid'],'ref':q['ref'],'pin':q['num'],'gap_mm':d,'required_mm':.275},d>=.275)
   nearest=min((v for v in after['vias']if v['uuid']!=t['uuid']),key=lambda v:pt.distance(Point(v['x'],v['y'])));d=pt.distance(Point(nearest['x'],nearest['y']));check({'kind':'all_via_pitch','UUID':t['uuid'],'other_UUID':nearest['uuid'],'pitch_mm':d,'required_mm':.815},d>=.815)
  check({'kind':'outline','UUID':t['uuid']},outline.buffer(-.025).covers(body))
  for rule in after['rule_areas']:
   if set(lyrs)&set(rule['layers'])and rule.get('no_vias'if'd'in t else'no_tracks'):
    if any(body.distance(sh)<.025 for sh in K.L.poly(rule['outline'])):check({'kind':'native_rule','UUID':t['uuid'],'rule_UUID':rule['uuid']},False)
  for rule in reserve['keepouts']:
   if net not in exempt.get(rule['name'],set())and set(lyrs)&set(rule['layers']):
    if any(body.distance(sh)<.025 for sh in K.L.poly(rule['outline'])):check({'kind':'fixed_reserved_rule','UUID':t['uuid'],'rule':rule['name']},False)
 put('all-new-true-discrete-hole-SMD-pitch-rule-checks.json',checks);put('all-new-true-geometry-errors.json',errors);put('status.json',{'phase':'ACTUAL_ALL_DRILLED_AO1_OLD_GROUP_AND_SOURCE','geometry_errors':len(errors)})
 aonets={n for n in bg if n.startswith('/motherboard_analog_output/AO1')};nets=affected|aonets;ng={};groupbad=[];sourcebad=[];groupcounts=[]
 for n in sorted(nets):
  ng[n]=K.physical(after,n,context)[1];proof,bad=K.contact_losses(bg[n],ng[n],removed);groupbad.extend({'net':n,**q}for q in bad);groupcounts.append({'net':n,'native_full_before_groups':len(bg[n]),'prospective_after_groups':len(ng[n]),'retained_old_layer_key_losses':len(bad)});put('status.json',{'phase':'ACTUAL_ALL_DRILLED_AO1_OLD_GROUP_AND_SOURCE','net':n,'completed':len(ng),'net_count':len(nets)})
 oldroot=K.root(bg[COM],'U14619','7');newroot=K.root(ng[COM],'U14619','7');oldkeys=K.keys(oldroot);newkeys=K.keys(newroot);sourcebad=sorted(oldkeys-newkeys);oldref=K.source_refs(oldroot);newref=K.source_refs(newroot);direct=[]
 for oldgroup in bg[COM]:
  for q in oldgroup:
   if q['kind']=='fill':continue
   oldfills=[s for s in oldgroup if s['kind']=='fill'and s['layer']==q['layer']and q['shape'].distance(s['shape'])<=.000002]
   if not oldfills:continue
   choices=[g for g in ng[COM]if any(z['kind']==q['kind']and z['uuid']==q['uuid']and z['layer']==q['layer']for z in g)]
   if not choices or not any(any(s['kind']=='fill'and s['layer']==q['layer']and q['shape'].distance(s['shape'])<=.000002 for s in g)for g in choices):direct.append({'UUID':q['uuid'],'kind':q['kind'],'layer':q['layer']})
 refbad=[];eligible=[];deltas={l:oldref[l].difference(newref[l])for l in newref}
 for t in before['tracks']:
  if t['uuid']in removed or t['layer']not in newref or K.L.norm(t['net'])==COM or dom.get(K.L.norm(t['net']))!=dom[COM]:continue
  body=K.L.body(t);loss=body.intersection(deltas[t['layer']]);row={'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'literal_source_reference_loss':info(loss)};eligible.append(row)
  if not loss.is_empty:
   path=OUT/(t['uuid']+'-raw-retained-body-reference-loss.wkb');path.write_bytes(loss.wkb);refbad.append(row|{'file':str(path.resolve())})
 newbody=[];newbodybad=[];sg=next(v for v in nv if K.L.norm(v['net'])==VREF);ret=next(v for v in nv if K.L.norm(v['net'])==COM);owncap=Point(sg['x'],sg['y']).buffer(.525,quad_segs=256)
 for t in nt:
  ly=t['layer'];body=K.L.body(t);allowed=newref[ly]
  if K.L.norm(t['net'])==VREF:allowed=allowed.union(owncap)
  missing=body.difference(allowed);row={'UUID':t['uuid'],'raw_net':t['net'],'layer':ly,'SOURCE_reference_layer':K.MAP[ly],'owncap_ONLY_named_VREF_new_via_radius_mm':.525 if K.L.norm(t['net'])==VREF else None,'raw_full_body_gap':info(missing)};newbody.append(row)
  if not missing.is_empty:
   path=OUT/(t['uuid']+'-raw-new-body-reference-gap.wkb');path.write_bytes(missing.wkb);newbodybad.append(row|{'file':str(path.resolve())})
 ann=Point(ret['x'],ret['y']).buffer(.25,quad_segs=256).difference(Point(ret['x'],ret['y']).buffer(.1,quad_segs=256));pair={'signal_UUID':sg['uuid'],'return_UUID':ret['uuid'],'distance_mm':math.dist([sg['x'],sg['y']],[ret['x'],ret['y']]),'native_actual_masks_OPEN':True,'prospective_rooted_return_layers':{l:('via',ret['uuid'],l)in newkeys for l in('In1.Cu','In4.Cu')},'finite_source_annulus_interior_mm2':{l:ann.intersection(newref['F.Cu'if l=='In1.Cu'else'B.Cu'].buffer(-.005)).area for l in('In1.Cu','In4.Cu')}}
 target=['9e8539ce-5524-48bc-861a-3943b2d53017','391d8dff-9c1d-4299-9e76-310f724dc137'];targetgroup=[g for g in ng[VREF]if any(q['kind']=='pad'and q['uuid']==target[0]for q in g)];joined=bool(targetgroup)and all(any(q['kind']=='pad'and q['uuid']==u for q in targetgroup[0])for u in target)
 put('all-AO1-and-normal-antipad-affected-old-group-deltas.json',groupcounts);put('raw-old-AO1-contact-losses.json',groupbad);put('SOURCE-COM-old-rooted-layer-key-losses.json',[list(k)for k in sourcebad]);put('all-old-COM-direct-fill-contact-losses.json',direct);put('all-old-COM-domain-retained-body-reference-checks.json',eligible);put('raw-all-old-COM-domain-retained-body-reference-losses.json',refbad);put('all-new-full-body-actual-SOURCE-reference-checks.json',newbody);put('raw-new-full-body-reference-losses.json',newbodybad);put('new-ordinary-VREF-real-SOURCE-COM-return-pair.json',pair)
 power='/motherboard_analog_output/AO1_5V';oldpower=K.root(bg[power],'U14620','1');newpower=K.root(ng[power],'U14620','1');oldpowerkeys={k for k in K.keys(oldpower)if not(k[0]=='track'and k[1]in removed)};newpowerkeys=K.keys(newpower);powerkeysbad=sorted(oldpowerkeys-newpowerkeys);newpowertracks=[t for t in nt if K.L.norm(t['net'])==power];powertracksbad=[t['uuid']for t in newpowertracks if('track',t['uuid'],'F.Cu')not in newpowerkeys];positiveproof={'actual_5V_source_ref':'U14620','pin':'1','source_pinfunction':'OUT_1','all_retained_old_5V_SOURCE_layer_key_losses':[list(k)for k in powerkeysbad],'all_new_locked_native_width_power_tracks_rooted':not powertracksbad,'new_power_track_source_errors':powertracksbad,'old_source_group_layer_keys_retained':len(oldpowerkeys),'new_source_group_layer_keys':len(newpowerkeys),'current_voltage_load_derating_mesh_IR_qualification':'OPEN; no load or fitted channel reduction'}
 from verify_source import parse,children,child,atom
 nf=pin(ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2');doc=parse(nf.read_text());chain=[]
 for n in children(child(doc,'nets'),'net'):
  rawnet=atom(n,'name');normnet=K.L.norm(rawnet);nodes=[{q[0]:q[1]for q in node[1:]}for node in children(n,'node')];inputs=[q for q in nodes if q['ref']=='U14620'and q.get('pintype')=='power_in'and normnet!=COM];outputs=[q for q in nodes if q['ref']=='U14619'and q.get('pintype')=='power_out']
  for inp in inputs:
   for out in outputs:
    assert normnet in bg and normnet in ng;before_feed=K.root(bg[normnet],out['ref'],out['pin']);after_feed=K.root(ng[normnet],out['ref'],out['pin']);oldp=any(q['kind']=='pad'and q['ref']==inp['ref']and str(q['pin'])==inp['pin']for q in before_feed);newp=any(q['kind']=='pad'and q['ref']==inp['ref']and str(q['pin'])==inp['pin']for q in after_feed);chain.append({'raw_input_supply_net':rawnet,'genuine_converter_source':out,'regulator_input':inp,'actual_full_before_feed_joined':oldp,'prospective_after_feed_joined':newp,'input_supply_old_source_layer_key_losses':len(K.keys(before_feed)-K.keys(after_feed))})
 put('genuine_U14619_converter_to_U14620_5V_regulator_native_source_chain.json',chain);put('actual-5V-SOURCE-all-old-and-two-new-power-track-provenance.json',positiveproof)
 model=OUT/'AO1-only-sparse-prospective-normal-native-antipad-host-model.pkl';model.write_bytes(pickle.dumps(after,protocol=5));groups=OUT/'AO1-and-local-antipad-all-drilled-after-groups.pkl';groups.write_bytes(pickle.dumps(ng,protocol=5));passed=not(errors or allrawgain or groupbad or sourcebad or direct or refbad or newbodybad or powerkeysbad or powertracksbad)and bool(chain)and all(q['actual_full_before_feed_joined']and q['prospective_after_feed_joined']and q['input_supply_old_source_layer_key_losses']==0 for q in chain)and joined and .90<=pair['distance_mm']<=1 and all(pair['prospective_rooted_return_layers'].values())and all(v>0 for v in pair['finite_source_annulus_interior_mm2'].values())
 result={'verdict':'R20_ACTUAL_FULL_R299_HOST_SOURCE_CONTACT_REFERENCE_PASS_NATIVE_CURRENT_ANALOG_SI_OPEN'if passed else'R20_ACTUAL_FULL_R299_RAW_HOST_REPAIR_REQUIRED','current_R753_AO1_discrete_before_identity_count':len(aobase),'new_tracks':len(nt),'new_vias':len(nv),'only_controlled_original_MON3_and_exact_b177_5V_replaced':sorted(removed),'genuine_positive_5V_source_proof':positiveproof,'U14619_to_5V_regulator_supply_chain':chain,'geometry_errors':len(errors),'raw_positive_fill_gain_records':len(allrawgain),'all_AO1_and_affected_old_contact_losses':len(groupbad),'SOURCE_COM_old_layer_key_losses':len(sourcebad),'old_direct_COM_fill_losses':len(direct),'strict_literal_old_SOURCE_reference_losses':len(refbad),'new_full_body_reference_losses':len(newbodybad),'VREF_original_R07_target_joined':joined,'ordinary_pair':pair,'host_model_file':str(model.resolve()),'host_model_SHA256':sha(model),'groups_SHA256':sha(groups),'prospective_antipads_are_normal_native_profile_WITHOUT_planner_override':True,'exact_full_R753_AFTER_native_source_fills_and_all_new_actual_masks':'ACTUAL_FULL_R299_BEFORE; prospective R28 additions still require native AFTER','current_analog_noise_SI_current_thermal':'OPEN','native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','geometry_errors','raw_positive_fill_gain_records','all_AO1_and_affected_old_contact_losses','SOURCE_COM_old_layer_key_losses','old_direct_COM_fill_losses','strict_literal_old_SOURCE_reference_losses','new_full_body_reference_losses','VREF_original_R07_target_joined','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
