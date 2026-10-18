"""Independent literal coupled candidate contacts, source and true Cu checks."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
A,L,F,GE,Z,PS,Q,RF,OS,C=(getattr(K,n)for n in('A','L','F','GE','Z','PS','Q','RF','OS','C'))
LAYERS=K.LAYERS
OUT=H/'U10003-compliant-clock-fault-ground-independent-drilled-source-geometry-r193'
FG='/motherboard_motors/FIELD_GND';FLT='/motherboard_do/DOA_FLT_N_FIELD';CLK='/motherboard_do/DOA_SCLK_FIELD'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir();base=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r192/model.pkl'
 assert sha(base)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='d1efefc5d13afa5c7fc2e55a9e476c74bee0febf8df373ab63701023e6b58fa8'
 g,h0,b0,q0,before=pickle.loads(base.read_bytes());ng,h,b,q,after=pickle.loads(mp.read_bytes());assert ng==g
 receipt=json.loads(mp.with_name('receipt.json').read_bytes());removed=set(receipt['seven_exact_original_track_replacements']);oldtracks={t['uuid']for t in h0['tracks']};oldvias={v['uuid']for v in h0['vias']};nt=[t for t in h['tracks']if t['uuid']not in oldtracks];nv=[v for v in h['vias']if v['uuid']not in oldvias];assert len(nt)==9 and len(nv)==3
 assert all(next(v for v in h['vias']if v['uuid']==s['uuid'])==s for s in h0['vias'])
 dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom[L.norm(a)]==dom[L.norm(bb)]else.6
 # Run the existing literal analytic cap/annulus guard implementation against
 # this freshly loaded candidate; no constructor-generated checks are trusted.
 source=Path(K.__file__).read_text();start=source.index(' # True circular caps/annuli are measured');end=source.index(' # Separate any native-cache guard deficit',start);block=source[start:end]
 ns={**globals(),**locals(),'O':OUT,'STRtree':K.STRtree};exec(compile(block,'independent_K_R220_true_geometry_block','exec'),ns,ns);geometry_errors=ns['errors'];checks=ns['checks']
 contexts=[K.hole_context(x)for x in(before,after)];groups={};rows=[]
 for net in(FG,FLT,CLK):
  print('R193_DRILLED_BEGIN',net,flush=True);_,old=K.physical(before,net,contexts[0]);_,new=K.physical(after,net,contexts[1]);checked,loss=K.contact_losses(old,new,removed);groups[net]=(old,new);rows.append({'net':net,'old_groups':len(old),'new_groups':len(new),'retained_old_layer_contact_checks':checked,'retained_old_contact_losses':loss});print('R193_DRILLED_END',net,len(loss),flush=True)
 put(OUT/'three-net-retained-drilled-contact-proof.json',rows)
 oldroot=K.root(groups[FG][0],'J11003','2');newroot=K.root(groups[FG][1],'J11003','2');oldkeys=K.keys(oldroot);newkeys=K.keys(newroot);lost=sorted(oldkeys-newkeys-{('track',u,l)for u in removed for l in LAYERS});refs={l:unary_union([r['shape']for r in newroot if r['kind']=='fill'and r['layer']==l])for l in('In1.Cu','In4.Cu')}
 pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U10003','9'));groundvias=[v for v in nv if L.norm(v['net'])==FG];source_rows=[]
 for v in groundvias:
  pt=Point(v['x'],v['y']);ann=pt.buffer(v['d']/2,quad_segs=256).difference(pt.buffer(v['drill']/2,quad_segs=128));source_rows.append({'UUID':v['uuid'],'all_host_layer_keys_source_rooted':all(('via',v['uuid'],l)in newkeys for l in LAYERS),'actual_source_fill_annuli_mm2':{l:ann.intersection(sh).area for l,sh in refs.items()},'actual_native_flashes_and_post_fill_annuli':'OPEN'})
 source_proof={'original_J11003_layer_key_losses':[list(k)for k in lost],'U10003_9_source_rooted':any(k[0]=='pad'and k[1]==pad['uuid']for k in newkeys),'new_ordinary_ground_rows':source_rows}
 put(OUT/'actual-drilled-ground-source-proof.json',source_proof)
 bodyrows=[];holes,ht=contexts[1]
 for net in(FG,FLT,CLK):
  parts=[K.A.shape({'kind':'segment',**t})for t in nt if L.norm(t['net'])==net];body=unary_union(parts);drilled=body.difference(unary_union([holes[int(i)]for i in ht.query(body,predicate='intersects')]))
  for layer,ref in refs.items():
   raw=body.difference(ref);physical=drilled.difference(ref);(OUT/(net.split('/')[-1]+'-'+layer+'-raw-gap.wkb')).write_bytes(raw.wkb);(OUT/(net.split('/')[-1]+'-'+layer+'-actual-drilled-gap.wkb')).write_bytes(physical.wkb)
   bodyrows.append({'net':net,'plane':layer,'full_track_body_raw_gap_mm2':raw.area,'raw_gap_empty':raw.is_empty,'actual_drilled_track_body_gap_mm2':physical.area,'actual_drilled_gap_empty':physical.is_empty,'own_signal_aperture_no_automatic_credit':True})
 put(OUT/'all-new-track-body-raw-and-actual-drilled-reference.json',bodyrows)
 ok=not geometry_errors and not any(r['retained_old_contact_losses']for r in rows)and not lost and source_proof['U10003_9_source_rooted']and all(x['all_host_layer_keys_source_rooted']for x in source_rows)
 result={'verdict':'SCOPED_TRUE_CU_DRILLED_CONTACT_AND_GROUND_SOURCE_PASS_OTHER_GATES_OPEN'if ok else'FAIL_SCOPED_COUPLED_GEOMETRY_SOURCE_OR_OLD_CONTACT','model_sha256':sha(mp),'base_sha256':sha(base),'true_geometry_check_count':len(checks),'true_geometry_error_count':len(geometry_errors),'geometry_source_contact_scope_pass':ok,'new_reference_rows':bodyrows,'source':source_proof,'retained_all_other_net_physics_strict_old_reference_fullcurrent_and_native_qualification':'OPEN','saved_return_distances_mm':receipt['both_saved_return_distances_mm'],'all_R191_raw_reference_failures_and_inherited_outside_intention_failures_retained':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False}
 put(OUT/'receipt.json',result);print('R193_COMPLETE',ok,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
