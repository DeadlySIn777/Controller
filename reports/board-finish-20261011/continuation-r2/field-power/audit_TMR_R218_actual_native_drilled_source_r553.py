"""Independent selected native FA/IO3 fill connectivity, without hollow ports.

Native actual pad polygons and via FlashLayer inventory replace the host
nominees. Every native hole is subtracted by K.physical; finite annuli must
meet real source-connected fill. The unrefilled nets receive no new credit.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,re,collections,copy
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MS
import ordinary_routes as O
from inventory import sha
N=H.parent/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl'
HG=H/'FA-IO3-TMR-current-R515-complete-delta-direct-contact-r517/actual-drilled-current-groups.pkl'
BG=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl'
OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r553'
RAWS={'/IO_3V3','/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED'}
ROOTS=[('/IO_3V3','R18001','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17')]
VIA='498e9bfd-bcf6-4711-864a-ddfe55479c3a'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pad_count(xs):return len({r['uuid']for r in xs if r['kind']=='pad'and str(r['pin'])})
def main():
 assert not OUT.exists();OUT.mkdir();start=time.monotonic()
 assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862'
 assert sha(N/'receipt.json')=='a8204097f1ee9862b5cc0f68faf7a5ab2b11005898fd821062e4b16351c3bbaf'
 r=json.loads((N/'scoped-fill/receipt.json').read_bytes());gp=N/'scoped-fill/geometry.json';vp=N/'scoped-fill/actual-via-flashes.json'
 assert sha(gp)==r['geometry_sha256']=='84bb0c848cc670a82c6dbdf2cca5353f9093855072cd127c6d6453c7020e6d7e'
 assert sha(vp)==r['actual_via_flashes_sha256']=='bdd51c56b5d6611aea20f78846cdff14765bd3b99a866249c26d952f9120d6f7'
 assert r['filler_ok']and not r['all_discrete_post_fill_errors']
 api=json.loads((N/'native-two-zone-API.json').read_bytes());exp=json.loads((N/'two-zone-native-expected.json').read_bytes())
 assert not api['errors']and api['candidate_sha256']==exp['candidate_sha256']==r['candidate_sha256']=='6befbca6dcac6bfe812dc8be04069701338f8ef95159faf9a5cb4a114395d55e'
 assert sha(N/'native-two-zone-API.json')=='2070d8576436a8c0e7db6211849cde54757ec03edc65bf9e45784c0104ed1a1b'
 ng=json.loads(gp.read_bytes());flashes=json.loads(vp.read_bytes())['vias'];g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 host=pickle.loads(HG.read_bytes());baseline=pickle.loads(BG.read_bytes())
 assert sha(HG)==json.loads(HG.with_name('receipt.json').read_bytes())['actual_final_group_sha256']
 htracks={x['uuid']:x for x in h['tracks']};hvias={x['uuid']:x for x in h['vias']}
 assert set(htracks)=={x['uuid']for x in ng['tracks']}and set(hvias)=={x['uuid']for x in ng['vias']}==set(flashes)
 for x in ng['tracks']:
  old=htracks[x['uuid']];assert (x['net'],x['layer'],x['s'],x['e'],x['w'])==(old['net'],old['layer'],list(old['a']),list(old['b']),old['w'])
 vias=[]
 for x in ng['vias']:
  old=hvias[x['uuid']];assert(x['net'],x['at'],x['w'],x['drill'])==(old['net'],[old['x'],old['y']],old['d'],old['drill'])
  vias.append({**old,'flashed':list(flashes[x['uuid']])})
 # Every actual physical pad on the selected raw nets has an exact unique
 # ref/pin/centre binding to the native-preserved footprint identity. No
 # rounding, coincident-pad merge, or pin-number-only binding is permitted.
 index=collections.defaultdict(list)
 for x in h['pads']:
  if x['net']in RAWS:index[x['ref'],str(x['num']),x['x'],x['y'],x['net']].append(x)
 replacements={};padrows=[]
 for x in ng['pads']:
  if x['net']not in RAWS:continue
  matches=index[x['ref'],str(x['num']),*x['at'],x['net']];assert len(matches)==1,(x['ref'],x['num'],x['at'],len(matches))
  old=matches[0];assert old['uuid']not in replacements
  native={**old,'layers':{ly:O.polys(x['poly'])for ly in x['layers']}}
  replacements[old['uuid']]=native
  padrows.append({'UUID':old['uuid'],'ref':x['ref'],'pin':str(x['num']),'raw_net':x['net'],'native_at_mm':x['at'],'native_layers':x['layers'],'binding':'Exact unique ref/pin/native centre/raw-net and preserved complete footprint AST; all ambiguous physical bindings rejected','native_poly_records_SHA256':hashlib.sha256(json.dumps(x['poly'],separators=(',',':')).encode()).hexdigest(),'original_exact_native_hole_geometry_retained':True})
 assert set(replacements)=={x['uuid']for xs in index.values()for x in xs}
 pads=[replacements.get(x['uuid'],x)for x in h['pads']]
 nativezones=[{**x,'fills':{ly:O.polys(rs)for ly,rs in x['fills'].items()}}for x in ng['zones']if x['net']in RAWS]
 assert {x['uuid']for x in nativezones}==set(r['selected_zone_UUIDs'])
 # Native export zones already carry their own real settings and per-piece
 # fill arrays. No union, grid snap or old-fill restoration is introduced.
 candidate={**c,'pads':pads,'vias':vias,'zones':[x for x in c['zones']if x['net']not in RAWS]+nativezones}
 put(OUT/'exact-native-physical-pad-bindings.json',padrows)
 ctx=K.hole_context(candidate);groups={};source=[];contact=[];direct=[];annular=[]
 for net,ref,pin in ROOTS:
  _,xs=K.physical(candidate,net,ctx);groups[net]=xs;actual=K.root(xs,ref,pin);actualkeys=K.keys(actual);hr=K.root(host[net],ref,pin);br=K.root(baseline[net],ref,pin)
  comparisons={}
  for label,prior in [('R515_host_final',host[net]),('R155_prior_host',baseline[net])]:
   rows,bad=K.contact_losses(prior,xs);comparisons[label]={'prior_groups':len(prior),'actual_native_groups':len(xs),'losses':bad};contact.append({'net':net,'baseline':label,'all_old_relationships':rows,'losses':bad})
  sr={'net':net,'source':ref+'.'+pin,'actual_native_groups':len(xs),'actual_native_source_named_pads':pad_count(actual),'host_R515_source_named_pads':pad_count(hr),'prior_R155_source_named_pads':pad_count(br),'R515_host_prior_source_keys_lost':[list(x)for x in sorted(K.keys(hr)-actualkeys)],'R155_prior_source_keys_lost':[list(x)for x in sorted(K.keys(br)-actualkeys)],'R515_host_actual_extra_source_keys':[list(x)for x in sorted(actualkeys-K.keys(hr))],'whole_board_other_nets_not_freshly_refilled':'NO_CREDIT','full_signed_sheet_barrel_fault_drop_thermal_current':'OPEN'}
  if net=='/IO_3V3':
   target={('pad','fd718e28-2f39-4c99-9c18-ba03fc86da8b','F.Cu'),('track','e34c9ec3-20ba-430a-902c-b5069a85c2f7','F.Cu')}|{('via',VIA,ly)for ly in K.LAYERS}
   sr['R14045_exact_eight_keys_rooted']=target<=actualkeys;sr['R14045_exact_eight_missing_keys']=[list(k)for k in sorted(target-actualkeys)]
   v=next(x for x in vias if x['uuid']==VIA)
   for layer in K.LAYERS:
    vr=[x['shape']for x in actual if x['kind']=='via'and x['uuid']==VIA and x['layer']==layer]
    ann=unary_union(vr);fill=unary_union([x['shape']for x in actual if x['kind']=='fill'and x['layer']==layer]);hit=ann.intersection(fill)
    ar={'via_UUID':VIA,'layer':layer,'native_actual_FlashLayer':layer in flashes[VIA],'actual_same_source_root_barrel_layer_key':('via',VIA,layer)in actualkeys,'finite_drill_subtracted_native_annulus_mm2':ann.area,'actual_source_rooted_fill_overlap_mm2':hit.area,'finite_overlap_nonempty':not hit.is_empty,'actual_min_overlap_threshold_is_not_capacity':True};annular.append(ar)
   sr['existing498_actual_In2_source_fill_annulus']=next(x for x in annular if x['layer']=='In2.Cu')
  source.append(sr)
  # Every host-before fill-to-native discrete layer contact is recorded. A
  # final source-root merge alone does not hide a lost retained local touch.
  bylayer=collections.defaultdict(list)
  for xx in xs:
   for x in xx:
    if x['kind']=='fill':bylayer[x['layer']].append(x['shape'])
  finalfill={ly:unary_union(sh)for ly,sh in bylayer.items()}
  for ly in K.LAYERS:
   metal={}
   for xx in host[net]:
    for x in xx:
     if x['layer']==ly and x['kind']!='fill':metal[(x['kind'],x['uuid'],ly)]=x
   alloldfill=unary_union([x['shape']for xx in host[net]for x in xx if x['kind']=='fill'and x['layer']==ly])
   for key,x in metal.items():
    if x['shape'].distance(alloldfill)>.000002:continue
    newmetal=[y for yy in xs for y in yy if(y['kind'],y['uuid'],y['layer'])==key];body=unary_union([y['shape']for y in newmetal]);gap=body.distance(finalfill.get(ly,Polygon()))if not body.is_empty else None
    direct.append({'net':net,'native_discrete_layer_key':list(key),'retained_direct_any_same_net_native_fill_touch':gap is not None and gap<=.000002,'actual_gap_mm':gap,'same_2nm_host_contact_operator_not_native_DRC_tolerance':True})
  print('R553 actual_native',net,'sourcepads',sr['actual_native_source_named_pads'],'groups',len(xs),'R515lost',len(sr['R515_host_prior_source_keys_lost']),flush=True)
 # Conditional native rule applies to BOTH fill and every intended outline,
 # even though the underlying AREA's no-fill flag is false.
 rulefile=N/'copy/board.kicad_dru';text=rulefile.read_text(encoding='utf-8');mm=re.search(r'\(rule "P1v2 TMR4WI U14619 keepout: no unrelated copper under converter"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow track via zone\)\)',text);assert mm
 allowed=re.findall(r"A.NetName != '([^']+)'",mm.group(1));area=next(x for x in ng['rule_areas']if x.get('name')=='TMR4WI_KEEPOUT_U14619');ha=next(x for x in h['rule_areas']if x.get('name')==area['name']);assert area['outline']==ha['outline']and area['layers']==ha['layers'];area_shape=unary_union(L.poly(area['outline']))
 nozone=[];nrings=[]
 for x in exp['zones']:
  assert x['raw_net']in RAWS and x['raw_net']not in allowed
  rr=[[(p[0]/1e6,p[1]/1e6)for p in ring]for ring in x['rings_IU']];body=Polygon(rr[0],rr[1:]);hit=body.intersection(area_shape);nrings.append({'UUID':x['uuid'],'layer':x['layer'],'raw_net':x['raw_net'],'native_all_outer_hole_integer_rings_and_all_nine_settings_API_exact':True,'actual_native_intended_outline_rule_intersection':ds(hit)})
  if not hit.is_empty:nozone.append({'role':'native_API_intended_outline','UUID':x['uuid'],**ds(hit)})
 for x in nativezones:
  for ly,rs in x['fills'].items():
   body=unary_union(L.poly(rs));hit=body.intersection(area_shape)
   if not hit.is_empty:nozone.append({'role':'native_actual_filled_physical_Cu','UUID':x['uuid'],'layer':ly,**ds(hit)})
 for x in q:
  if x['net']not in RAWS:continue
  for role in('shape','zone_outline_shape'):
   hit=x[role].intersection(area_shape)
   if not hit.is_empty:nozone.append({'role':'host_R515_'+role,'UUID':x['uuid'],'layer':x['layer'],**ds(hit)})
 directbad=[x for x in direct if not x['retained_direct_any_same_net_native_fill_touch']]
 failures=any(x['R515_host_prior_source_keys_lost']or x['R155_prior_source_keys_lost']for x in source)or any(x['losses']for x in contact)or directbad or nozone or not source[0].get('R14045_exact_eight_keys_rooted')or not source[0]['existing498_actual_In2_source_fill_annulus']['finite_overlap_nonempty']
 put(OUT/'actual-native-selected-source-and-host-delta.json',source);put(OUT/'all-selected-host-prior-native-physical-relationships.json',contact);put(OUT/'all-selected-host-before-direct-fill-contacts.json',direct);put(OUT/'native-direct-contact-disagreements.json',directbad);put(OUT/'existing498-real-all-layer-annular-contacts.json',annular);put(OUT/'native-intended-TMR-rule-ring-binding.json',nrings);put(OUT/'native-filled-and-intended-TMR-nozone-errors.json',nozone)
 (OUT/'fresh-native-selected-all-drilled-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 inputfiles=[Path(__file__),M,HG,BG,N/'receipt.json',N/'scoped-fill/receipt.json',gp,vp,N/'native-two-zone-API.json',N/'two-zone-native-expected.json',rulefile]
 receipt={'status':'SELECTED_NATIVE_FA_IO3_ACTUAL_SOURCE_OR_CONTACT_DISAGREEMENT_REPAIR_REQUIRED'if failures else'SELECTED_NATIVE_FA_IO3_ACTUAL_ALL_DRILL_SOURCE_CONTACT_AND_TMR_BOTH_ROLE_PASS_FULL_BOARD_CURRENT_DRC_OPEN','native_candidate_SHA256':r['candidate_sha256'],'R515_exact_host_model_SHA256':sha(M),'actual_selected_nets':[x[0]for x in ROOTS],'actual_selected_zone_count':len(nativezones),'all_native_tracks_exact':len(htracks),'all_native_vias_exact_actual_FlashLayer_inventory':len(vias),'actual_native_pad_bindings':len(padrows),'every_native_drill_subtracted_context_count':len(ctx[0]),'sources':source,'host_R515_relationship_loss_count':sum(len(x['losses'])for x in contact if x['baseline']=='R515_host_final'),'prior_R155_relationship_loss_count':sum(len(x['losses'])for x in contact if x['baseline']=='R155_prior_host'),'host_before_direct_native_fill_contact_count':len(direct),'host_before_direct_native_fill_contact_disagreement_count':len(directbad),'existing498_all_real_annular_contacts':annular,'actual_native_intended_API_all27_settings_rings_bound':True,'native_filled_and_intended_TMR_nozone_errors':nozone,'native_actual_group_pickle_SHA256':sha(OUT/'fresh-native-selected-all-drilled-groups.pkl'),'actual_new_native_physical_bodies_not_hollow_via_source_shortcuts':True,'full_host_vs_native_disagreements_explicit_without_tolerance_waiver':True,'all_other_nets_or_all_board_fills_references_DRC_current_capacity_fault_thermal':'OPEN_NO_SELECTED_FILL_CREDIT','inherited_R15528refs_CORE_ROOT42_planner_current_failures_retained':True,'inputs_SHA256':{str(x.resolve()):sha(x)for x in inputfiles},'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start}
 put(OUT/'receipt.json',receipt);print(json.dumps({'status':receipt['status'],'receipt_SHA256':sha(OUT/'receipt.json'),'sources':[{'net':x['net'],'actualpads':x['actual_native_source_named_pads'],'hostpads':x['host_R515_source_named_pads'],'lost':len(x['R515_host_prior_source_keys_lost'])}for x in source],'directlosses':len(directbad),'nozone':len(nozone)}),flush=True)
if __name__=='__main__':main()
