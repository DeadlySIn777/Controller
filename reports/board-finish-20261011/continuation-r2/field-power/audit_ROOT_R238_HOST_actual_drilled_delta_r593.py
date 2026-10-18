"""Independent HOST/pad delta: actual drilled groups, direct touches and return."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,collections,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import guarded_power_projection_r44 as Z
OUT=H/'ROOT-R238-HOST-independent-actual-drilled-old-contact-return-reference-r593'
BEFORE=ROOT/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl'
AFTER=ROOT/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl'
PACK=ROOT/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl'
GND='/LOGIC_GND';IO3='/IO_3V3';HOST='/motherboard_do/DOA_SDI_HOST'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def named(xs):return len({x['uuid']for x in xs if x['kind']=='pad'and str(x['pin'])})
def rootvia(xs,uid):return next(g for g in xs if any(x['kind']=='via'and x['uuid']==uid for x in g))
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(BEFORE)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5';assert sha(AFTER)=='8bc676155f72e590cc8dd77f6315f0990d60b421f54a3c7928dc8e66ba48f91d';assert sha(PACK)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402'
 a=pickle.loads(BEFORE.read_bytes());v=pickle.loads(AFTER.read_bytes());g0,h0,b0,q0,c0=a;g,h,b,q,c=v;d=pickle.loads(PACK.read_bytes());nt=d['tracks'];nv=d['vias'];assert len(nt)==6 and len(nv)==1 and not d['original_native_Cu_deletes']
 beforeq={x['uuid']:x for x in q0};assert {x['uuid']for x in q}==set(beforeq)
 for z in q:
  old=beforeq[z['uuid']];assert z.keys()==old.keys()
  for k,x in z.items():assert x.wkb==old[k].wkb if k in('shape','zone_outline_shape')else x==old[k],(z['uuid'],k)
 for kind,new in [('tracks',nt),('vias',nv)]:
  old={x['uuid']:x for x in h0[kind]};current={x['uuid']:x for x in h[kind]};assert current.keys()==old.keys()|{x['uuid']for x in new};assert all(current[u]==x for u,x in old.items());assert all(current[x['uuid']]==x for x in new)
 for kind in('pads','footprints'):
  key='uuid'if kind=='pads'else'ref';old={x[key]:x for x in h0[kind]};current={x[key]:x for x in h[kind]};assert current.keys()==old.keys();assert all(current[u]==x for u,x in old.items()if x['ref']!='R10007')
 changedfills=[];z0={z['uuid']:z for z in c0['zones']};assert set(z0)=={z['uuid']for z in c['zones']}
 for z in c['zones']:
  old=z0[z['uuid']];assert {k:v for k,v in z.items()if k!='fills'}=={k:v for k,v in old.items()if k!='fills'}
  assert z['fills'].keys()==old['fills'].keys()
  for ly,rs in z['fills'].items():
   if rs!=old['fills'][ly]:changedfills.append({'UUID':z['uuid'],'raw_net':z['net'],'layer':ly})
 assert {(x['UUID'],x['layer'])for x in changedfills}=={('58c55cd5-98e6-4467-88e3-146ceeee361a','In1.Cu'),('c1d27fa1-452b-4e27-985d-5ad23644d800','In4.Cu'),('54921f4b-0308-4821-9549-ff9360bf05ca','In2.Cu')}
 put(OUT/'exact-current-model-changed-fill-scopes.json',changedfills);put(OUT/'status.json',{'phase':'RECOMPUTING_BEFORE_AND_AFTER_ACTUAL_DRILLED_THREE_NETS','q_roles_ALL_exact':True,'after_source_contact_reference':'OPEN'});print('R591_EXACT_DELTA_BOUND',flush=True)
 ctx0=K.hole_context(c0);ctx=K.hole_context(c);before={};after={};contacts=[];sources=[];direct=[]
 # An optional frozen cache can be rebound only to the exact R196 before hash.
 cachefile=OUT/'optional-exact-R196-cache-binding.json'
 cachebinding=json.loads(cachefile.read_bytes())if cachefile.exists()else None
 cache={}
 if cachebinding:
  assert cachebinding['model_sha256']==sha(BEFORE);cp=Path(cachebinding['cache_file']);assert sha(cp)==cachebinding['cache_sha256'];cache=pickle.loads(cp.read_bytes())
 for net in (GND,IO3,HOST):
  if net in cache:before[net]=cache[net]
  else:_,before[net]=K.physical(c0,net,ctx0)
  print('R591_BEFORE',net,len(before[net]),flush=True)
  _,after[net]=K.physical(c,net,ctx);print('R591_AFTER',net,len(after[net]),flush=True)
  (OUT/('groups-'+net.rsplit('/',1)[-1]+'.pkl')).write_bytes(pickle.dumps({'before':before[net],'after':after[net]},protocol=5))
  rows,bad=K.contact_losses(before[net],after[net]);contacts.append({'net':net,'old_group_count':len(before[net]),'after_group_count':len(after[net]),'old_relationships':rows,'losses':bad})
  oldroot=K.root(before[net],'J11001','2')if net==GND else K.root(before[net],'R18001','2')if net==IO3 else rootvia(before[net],d['source_terminal_UUID'])
  newroot=K.root(after[net],'J11001','2')if net==GND else K.root(after[net],'R18001','2')if net==IO3 else rootvia(after[net],d['source_terminal_UUID'])
  sources.append({'net':net,'root':'J11001.2'if net==GND else'R18001.2'if net==IO3 else'EXACT_RETAINED_HOST_TERMINAL_'+d['source_terminal_UUID'],'before_named_pads':named(oldroot),'after_named_pads':named(newroot),'prior_source_keys_lost':[list(k)for k in sorted(K.keys(oldroot)-K.keys(newroot))],'new_HOST_via_keys_rooted':all(('via',nv[0]['uuid'],l)in K.keys(newroot)for l in K.LAYERS)if net==HOST else None})
  for ly in K.LAYERS:
   oldfill=unary_union([x['shape']for xs in before[net]for x in xs if x['kind']=='fill'and x['layer']==ly]);newfill=unary_union([x['shape']for xs in after[net]for x in xs if x['kind']=='fill'and x['layer']==ly]);oldmetal={};newmetal=collections.defaultdict(list)
   if oldfill.is_empty:continue
   for xs in before[net]:
    for x in xs:
     if x['kind']!='fill'and x['layer']==ly:oldmetal[x['kind'],x['uuid'],ly]=x
   for xs in after[net]:
    for x in xs:
     if x['kind']!='fill'and x['layer']==ly:newmetal[x['kind'],x['uuid'],ly].append(x['shape'])
   for key,x in oldmetal.items():
    if x['shape'].distance(oldfill)>.000002:continue
    body=unary_union(newmetal.get(key,[]));gap=None if body.is_empty or newfill.is_empty else body.distance(newfill)
    direct.append({'net':net,'physical_key':list(key),'before_actual_any_fill_touch':True,'after_retained_direct_actual_any_fill_touch':gap is not None and gap<=.000002,'after_gap_mm':gap,'same_2nm_host_operator_not_native_DRC_tolerance':True})
 lg=K.root(after[GND],'J11001','2');lgkeys=K.keys(lg);returnuid=d['existing_ground_return_UUID'];rv=next(x for x in c['vias']if x['uuid']==returnuid);oldrv=next(x for x in c0['vias']if x['uuid']==returnuid);assert rv==oldrv
 distance=math.hypot(nv[0]['x']-rv['x'],nv[0]['y']-rv['y']);annuli=[]
 for ly in ('In1.Cu','In4.Cu'):
  ann=unary_union([x['shape']for x in lg if x['kind']=='via'and x['uuid']==returnuid and x['layer']==ly]);fill=unary_union([x['shape']for x in lg if x['kind']=='fill'and x['layer']==ly]);annuli.append({'via_UUID':returnuid,'layer':ly,'actual_source_root_layer_key':('via',returnuid,ly)in lgkeys,'finite_drill_subtracted_annulus':ds(ann),'finite_actual_J1_source_fill_overlap':ds(ann.intersection(fill))})
 refs=K.source_refs(lg);ntids={x['uuid']for x in nt};trackphysical={}
 for xs in after[HOST]+after[GND]:
  for x in xs:
   if x['kind']=='track'and x['uuid']in ntids:trackphysical.setdefault(x['uuid'],[]).append(x['shape'])
 terminal=next(x for x in c['vias']if x['uuid']==d['source_terminal_UUID']);caps=unary_union([Z.bounded_disk(nv[0],d['new_signal_exact_own_cap_mm']),Z.bounded_disk(terminal,d['source_terminal_exact_own_cap_mm'])]);bodyrows=[]
 for t in nt:
  body=unary_union(trackphysical.get(t['uuid'],[]));rawgap=body.difference(refs[t['layer']]);outside=rawgap.difference(caps)if t['net']!=GND else rawgap
  bodyrows.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'actual_full_native_drill_subtracted_physical_body':ds(body),'raw_actual_source_LG_fill_reference_gap':ds(rawgap),'explicit_terminal_cap_only_gap':ds(outside),'source_existing_terminal_cap_radius_mm':d['source_terminal_exact_own_cap_mm'],'new_own_cap_radius_mm':d['new_signal_exact_own_cap_mm'],'source_terminal_575_scope_authority':'OPEN; original terminal neighbor shadow does not qualify it','caps_operator_does_not_fabricate_ground':True})
 put(OUT/'all-old-three-net-relationships.json',contacts);put(OUT/'actual-three-source-root-deltas.json',sources);put(OUT/'all-old-direct-fill-contact-obligations.json',direct);put(OUT/'actual442fd-source-finite-annuli-and-new-pair-window.json',{'existing_return_UUID':returnuid,'existing_geometry_flashes_exact':True,'new_signal_return_distance_mm':distance,'saved_ordinary_return_window_mm':[.9,1.0],'window_pass':.9<=distance<=1,'annuli':annuli});put(OUT/'six-actual-body-LG-source-reference-raw-and-explicit-caps.json',bodyrows)
 actualgroup=OUT/'fresh-actual-drilled-groups.pkl';actualgroup.write_bytes(pickle.dumps(after,protocol=5));badcontact=sum(len(x['losses'])for x in contacts);badsource=sum(len(x['prior_source_keys_lost'])for x in sources);baddirect=[x for x in direct if not x['after_retained_direct_actual_any_fill_touch']];badrefs=[x for x in bodyrows if not x['explicit_terminal_cap_only_gap']['empty']];returnpass=all(x['actual_source_root_layer_key']and not x['finite_actual_J1_source_fill_overlap']['empty']for x in annuli)and .9<=distance<=1
 put(OUT/'receipt.json',{'status':'ROOT_R238_HOST_SCOPED_ACTUAL_SOURCE_CONTACT_RETURN_REPAIR_REQUIRED'if badcontact or badsource or baddirect or badrefs or not returnpass else'sROOT_R238_HOST_SCOPED_ACTUAL_SOURCE_CONTACT_RETURN_PASS_NATIVE_AND_CAP_AUTHORITY_OPEN','before_model_SHA256':sha(BEFORE),'after_model_SHA256':sha(AFTER),'exact_packet_SHA256':sha(PACK),'q_roles_ALL_unchanged':True,'original_discrete_Cu_all_geometry_and_masks_exact':True,'source_net_profile_rules_ALL_unchanged':True,'changed_actual_fill_scopes':changedfills,'old_relationship_loss_count':badcontact,'prior_source_key_loss_count':badsource,'old_direct_fill_contact_count':len(direct),'old_direct_contact_loss_count':len(baddirect),'actual442fd_finite_both_plane_source_and_saved_window_pass':returnpass,'new_body_reference_outside_explicit_two_cap_failure_count':len(badrefs),'raw_new_body_reference_failures_remain_visible':[x['UUID']for x in bodyrows if not x['raw_actual_source_LG_fill_reference_gap']['empty']],'full_original_575_terminal_aperture_authority_and_current_reference_policy':'OPEN; not neighbor credit','fresh_group_SHA256':sha(actualgroup),'sources':sources,'native_actual_NEW_HOST_all6_annuli_fullDRC_and_full_reference':'OPEN','inherited_R196_FG_CLK_FLT_nine_body_nomination_only_failures_retained':True,'original5492_TMR_closed_boundary_FAIL_retained':True,'all_field_supply_return_full_signed_mesh_current_thermal':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st})
 print('R591',sha(OUT/'receipt.json'),'oldgroups',badcontact,'source',badsource,'direct',len(baddirect),'bodyrefs',len(badrefs),'return',returnpass,flush=True)
if __name__=='__main__':main()
