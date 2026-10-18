"""Independent preservation of all76 accepted root42 zone-bearing net groups."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
import physical_reference_losses_r1 as REF
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 assert len(sys.argv)==4,'model.pkl expected_sha256 fresh_directory'
 mp=Path(sys.argv[1]).resolve();expected=sys.argv[2];out=Path(sys.argv[3]).resolve();assert mp.is_relative_to(H)and out.is_relative_to(H)and not out.exists()and sha(mp)==expected
 base=H/'logic-two-reference-safe-return-restoration-r42/model.pkl';audit=H/'logic-two-independent-full-r43/receipt.json';assert sha(base)=='a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba'and sha(audit)=='c0688d943d936947bb21ce60b7afc57574e5c4220db00ff7349b6b4821a0f0b3'
 raw=H/'sbc-power/IO3-notch-ROOT42-SAFE-unprojected-r165/unprojected-model.pkl';assert sha(raw)=='b469400ca259d0085d1d0564a14f0ccab90f28c3e4a3389081110173ad4845cb'
 bg,bh,bb,bz,before=pickle.loads(base.read_bytes());g,h,b,z,after=pickle.loads(mp.read_bytes());rg,rh,rb,rz,unprojected=pickle.loads(raw.read_bytes());assert g==rg and h==rh,'normalizer must preserve exact frozen original and current discrete inventories'
 inventory=H/'safe-root42-discrete-inventory-r49.json';ir=json.loads(inventory.read_bytes());assert ir['safe_unprojected_model_sha256']==sha(raw)and ir['root42_model_sha256']==sha(base)
 assert all(not ir['rows'][k]['removed']for k in ir['rows'])and all(not ir['rows'][k]['changed']for k in ('tracks','pads','footprints','zones'))and all(not ir['rows'][k]['added']for k in ('vias','pads','footprints','zones'))
 assert len(ir['rows']['tracks']['added'])==1 and len(ir['rows']['vias']['changed'])==1
 beforetracks={t['uuid']:t for t in bh['tracks']};aftertracks={t['uuid']:t for t in h['tracks']};assert all(aftertracks[uid]==t for uid,t in beforetracks.items())
 beforevias={v['uuid']:v for v in bh['vias']};aftervias={v['uuid']:v for v in h['vias']};changed=[uid for uid,v in beforevias.items()if aftervias[uid]!=v];assert changed==['f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92'];assert ir['rows']['vias']['changed'][0]['changed_fields']==['prospective_new_flash_requires_native_refill','flashed'] or set(ir['rows']['vias']['changed'][0]['changed_fields'])=={'prospective_new_flash_requires_native_refill','flashed'}
 extra=H/'sbc-power/core1v2-source-barrel-extra-In4-proposal-r111/extra-flash-obligation.json';assert sha(extra)=='33c16b1ed6c7d3af6e8c16b146c342b6eb54d9b08c333ad3adbd3862c7024f2e';er=json.loads(extra.read_bytes());assert beforevias[changed[0]]==er['expected_original_host_geometry']and aftervias[changed[0]]==er['expected_prospective_host_geometry']
 assert {k:v for k,v in beforevias[changed[0]].items()if k not in ('flashed','prospective_new_flash_requires_native_refill')}=={k:v for k,v in aftervias[changed[0]].items()if k not in ('flashed','prospective_new_flash_requires_native_refill')}
 assert set(beforevias[changed[0]]['flashed'])<=set(aftervias[changed[0]]['flashed'])and set(aftervias[changed[0]]['flashed'])-set(beforevias[changed[0]]['flashed'])=={'In4.Cu'}
 out.mkdir();nets={C.norm(q['net'])for q in before['zones']};assert len(nets)==76;groups={};oldgroups={};rows=[]
 for net in sorted(nets):
  prior=F.graph(before,net);new=F.graph(after,net);bad=losses(prior,new);rows.append({'net':net,'before_groups':len(prior),'after_groups':len(new),'old_discrete_contact_losses':bad});groups[net]=new;oldgroups[net]=prior;put(out/'contact-checkpoint.json',rows);print('R50_CONTACT',net,len(prior),len(new),'losses',len(bad),flush=True)
 sources=[];refs=[]
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  prior=oldgroups[net];new=groups[net];br=next(xs for xs in prior if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs));nr=next(xs for xs in new if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs));lost=F.discrete_keys(br)-F.discrete_keys(nr)
  sources.append({'net':net,'source':ref+'.2','before_named_pads':len({q['uuid']for q in br if q['kind']=='pad'and q['pin']}),'after_named_pads':len({q['uuid']for q in nr if q['kind']=='pad'and q['pin']}),'lost_prior_source_keys':[list(k)for k in sorted(lost)]})
  bf={o:unary_union([q['shape']for q in br if q['kind']=='fill'and q['layer']==l])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};nf={o:unary_union([q['shape']for q in nr if q['kind']=='fill'and q['layer']==l])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,proof=REF.audit(before,bf,nf,net);refs.append({'net':net,'retained_outer_reference_losses':bad,'proof':proof});put(out/'reference-checkpoint.json',refs);print('R50_SOURCE_REFERENCE',net,'source_losses',len(lost),'reference_losses',len(bad),flush=True)
 ok=not any(row['old_discrete_contact_losses']for row in rows)and not any(row['lost_prior_source_keys']for row in sources)and not any(row['retained_outer_reference_losses']for row in refs)
 (out/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 put(out/'receipt.json',{'verdict':'PASS_SAFE_FULL76_ROOT42_OLD_CONTACT_SOURCE_REFERENCE_NATIVE_CURRENT_OPEN'if ok else'FAIL_SAFE_FULL76_ROOT42_RETENTION','model_sha256':sha(mp),'model_file':str(mp),'parent_root42_model_sha256':sha(base),'root43_audit_sha256':sha(audit),'inventory_delta_ledger_sha256':sha(inventory),'all76_zone_bearing_nets':rows,'sources':sources,'retained_reference_sha256':sha(out/'reference-checkpoint.json'),'all_original_tracks_pads_footprint_poses_native_zone_outlines_preserved_to_root42':True,'one_existing_barrel_extra_In4_native_obligation':'OPEN_actual_full_native_fill','native_jobs':0,'board_written':False,'adopted':False,'whole_board_native_DRC_current_thermal':'OPEN','script_sha256':sha(__file__)})
 print('R50_COMPLETE',ok,sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
