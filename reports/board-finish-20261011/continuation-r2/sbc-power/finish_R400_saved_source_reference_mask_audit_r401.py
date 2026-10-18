"""Resume finished source graphs; index real holes for the remaining old-reference audit."""
import sys,json,pickle,hashlib,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
N=H/'sbc-power/CM79-R397-exact-five-tracks-three-ordinary-vias-R7035-real-pose-r398'
P=H/'sbc-power/CM79-R398-native-R7035-real-pose-three-via-mask-readonly-r399'
B=H/'sbc-power/CM79-R398-actual-native-pad-local-aperture-fresh-source-r400'
O=H/'sbc-power/CM79-R400-saved-source-graphs-indexed-oldrefs-port-audit-r401'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());gg,hh,bb,qq,cc=pickle.loads((B/'model.pkl').read_bytes());assert(g==gg and b==bb);pack=pickle.loads((N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl').read_bytes());own={p['uuid']for p in pack['R7035_source_scope']['pads']};nt=pack['tracks'];nv=pack['vias'];sourceRows=json.loads((B/'fresh-all-changed-source-oldgroups-and-pad-layer-keys.json').read_text());otherIdentity=json.loads((B/'other-source-bank-new-hole-disjoint-full-physics-identity.json').read_text());newBodyRows=json.loads((B/'all-five-new-body-and-two-native-full-SMD-source-reference-proof.json').read_text());fresh=pickle.loads((B/'fresh-actual-drilled-all-source-groups.pkl').read_bytes());before=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());oldRoot=K.root(before['/LOGIC_GND'],'J11001','2');newRoot=K.root(fresh['/LOGIC_GND'],'J11001','2');oldRefs=K.source_refs(oldRoot);newRefs=K.source_refs(newRoot);allBefore,allTrees=F.build(c);beforeCtx=K.hole_context(c);dom=h['domains_normalized'];tracks={t['uuid']:t for t in nt};vias={v['uuid']:v for v in nv};pads={p['uuid']:p for p in cc['pads']if p['uuid']in own};cutops=[];projection=json.loads((B/'explicit-local-original-native-plane-hole-pad-track-impact.json').read_text())
 for rr in projection:
  if L.norm(rr['raw_net'])!='/LOGIC_GND'or rr['layer']not in('In1.Cu','In4.Cu'):continue
  for op in rr['exact_declared_new_physical_Cu_and_hole_operations']:
   uid=op['new_UUID'];kind=op['kind'];candidate=[]
   if kind=='via':candidate=[Z.bounded_disk(vias[uid],op['physical_native_radius_mm'])]
   elif kind=='track':t=tracks[uid];candidate=[Z.bounded_buffer(LineString([t['a'],t['b']]),op['physical_native_radius_mm'])]
   else:candidate=[Z.bounded_buffer(sh,op['native_local_clearance_mm'])for sh in L.poly(pads[uid]['native_outside_layers'].get(rr['layer'],[]))]
   sh=next(x for x in candidate if hashlib.sha256(x.wkb).hexdigest()==op['cutter']['WKB_sha256']);cutops.append({'zone_UUID':rr['zone_UUID'],'layer':rr['layer'],'new_UUID':uid,'shape':sh})
 oldLoss=[];maskHits=[];count=0
 for layer,rlayer in K.MAP.items():
  ref=oldRefs[layer]
  for rr in allBefore[layer]:
   if rr['kind']=='fill'or rr['uuid']in own or dom.get(L.norm(rr['net']))!=dom.get('/LOGIC_GND'):continue
   body=rr['shape'].difference(unary_union([beforeCtx[0][int(j)]for j in beforeCtx[1].query(rr['shape'],predicate='intersects')]));supported=body.intersection(ref)
   if supported.is_empty:continue
   count+=1;lost=supported.difference(newRefs[layer])
   if not lost.is_empty:
    fn=O/(rr['uuid']+'-'+layer.replace('.','_')+'-'+str(len(oldLoss))+'-raw-old-reference-loss.wkb');fn.write_bytes(lost.wkb);oldLoss.append({'UUID':rr['uuid'],'kind':rr['kind'],'layer':layer,'actual_raw_before_supported_loss':ds(lost),'raw_loss_file':str(fn.resolve())})
   for op in cutops:
    if op['layer']!=rlayer:continue
    hit=supported.intersection(op['shape'])
    if not hit.is_empty:maskHits.append({'UUID':rr['uuid'],'layer':layer,'declared_cut_zone_UUID':op['zone_UUID'],'new_UUID':op['new_UUID'],'actual_before_supported_mask_hit':ds(hit)})
  print('R401_OLDREF_LAYER',layer,'checked',count,'raw',len(oldLoss),'literalcuts',len(maskHits),flush=True);put(O/'raw-all-existing-body-reference-losses-no-waiver.json',oldLoss);put(O/'literal-old-supported-body-mask-vs-every-declared-local-cut-hits.json',maskHits)
 portRows=[]
 for v in nv:
  if L.norm(v['net'])!='/LOGIC_GND':continue
  ov={}
  for ly in('In1.Cu','In4.Cu'):
   ann=unary_union([rr['shape']for rr in newRoot if rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==ly]);actualFill=unary_union([rr['shape']for rr in newRoot if rr['kind']=='fill'and rr['layer']==ly]);ov[ly]=ann.intersection(actualFill).area
  portRows.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'fresh_actual_source_connected_two_plane_annulus_overlap_mm2':ov,'both_positive':all(x>0 for x in ov.values())})
 put(O/'fresh-both-new-LG-return-actual-J1-source-annuli.json',portRows);put(O/'receipt.json',{'verdict':'SAVED_ACTUAL_NATIVE_PAD_SOURCE_GRAPHS_SCOPED_REFERENCE_PORT_AUDIT','R400_diagnostic_model_sha256':sha(B/'model.pkl'),'R398_exact_sparse_packet_sha256':sha(N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl'),'R399_actual_native_API_sha256':sha(P/'actual-native-API.json'),'source_key_loss_count':sum(len(x['all_old_source_keys_lost'])for x in sourceRows.values()),'old_source_group_relationship_loss_count':sum(len(x['old_group_relationship_losses'])for x in sourceRows.values()),'other_source_exact_newhole_disjoint_bank_count':len(otherIdentity),'new_five_body_and_two_native_OUTSIDE_SMD_reference_FAIL_count':sum(not x.get('exact_inner_guard_reference_gap',x.get('whole_actual_J1_In1_reference_gap'))['EMPTY']for x in newBodyRows),'old_supported_body_reference_count':count,'raw_old_body_reference_loss_count':len(oldLoss),'literal_old_body_mask_vs_all_declared_local_cut_hit_count':len(maskHits),'new_LG_actual_two_source_plane_annulus_FAIL_count':sum(not x['both_positive']for x in portRows),'completed_R400_source_graphs_and_body_proofs_reused_byte_exact':True,'raw_nonempty_reference_predicates_are_FAIL_and_never_waived':True,'one_combined_full_allnet_candidate_native_refill_allmasks_finite_terminal_loop_current_SI_thermal':'OPEN','all_inherited_CORE14_CORE93_other_FAIL_flags':'RETAINED','adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R401',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
