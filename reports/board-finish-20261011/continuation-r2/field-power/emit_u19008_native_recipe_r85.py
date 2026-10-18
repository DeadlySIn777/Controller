"""Exact one-delete/two-via/seven-segment scoped native recipe; no board."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from inventory import sha
from verify_source import parse,atom
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'u19008-native-owned-recipe-r85'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();rp=HERE/'u19008-coupled-power-wall-nomination-r82';assert sha(rp/'receipt.json')=='e2d5a98972b6ec856e41362f47374f6f47b5b57d01d114d65aa3cff01e842963';r=json.loads((rp/'receipt.json').read_text());assert not r['failures'];assert sha(rp/'proposed-discrete.pkl')==r['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());assert len(d['vias'])==2 and len(d['tracks'])==7
 board=HERE.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';_,chunks,_=C.O.C.pcbtext.split(board.read_bytes());byid={C.O.C.pcbtext.chunk_uuid(x):x for x in chunks if C.O.C.pcbtext.chunk_uuid(x)}
 old=r['owned_old_power_track'];ch=byid[old['uuid']];assert C.O.C.pcbtext.chunk_kind(ch)=='segment';a=parse(ch.decode('utf-8'));assert atom(a,'net')==old['net'] and float(atom(a,'width'))==.8 and atom(a,'locked')=='yes';delete=OUT/(old['uuid']+'.delete-original-segment-chunk');delete.write_bytes(ch)
 adds=[];tokens={}
 for kind,items in [('via',d['vias']),('segment',d['tracks'])]:
  for q in items:
   uid=q['uuid'];assert uid not in byid;tokens.setdefault(C.norm(q['net']),set()).add(q['net'])
   if kind=='via':text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],uid)
   else:
    assert q['w']>=.20;lock='\t\t(locked yes)\n' if q['w']==.8 else '';q={**q,'locked':True} if q['w']==.8 else q;text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n%s\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],lock,q['layer'],q['net'],uid)
   assert C.O.C.pcbtext.chunk_kind(text.encode())==kind and C.O.C.pcbtext.chunk_uuid(text.encode())==uid;assert atom(parse(text),'net')==q['net'];path=OUT/(uid+'.'+kind+'-chunk');path.write_text(text,encoding='utf-8',newline='');adds.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 assert all(len(x)==1 for x in tokens.values());write(OUT/'outside-contact-ledger.json',r['answers'][0]['outside_contacts_preserved']);flash=[{'uuid':v['uuid'],'raw_net':v['net'],'required_outer_flash':['B.Cu'],'required_source_inner_flash':'BOUND_BY_FINAL_ACTUAL_SOURCE_FEED_AND_RETURN_PLANE_AUDIT','planning_all6_annuli_not_native_flash_proof':True} for v in d['vias']];write(OUT/'native-flash-obligations.json',flash)
 write(OUT/'receipt.json',{'verdict':'FROZEN_SCOPED_U19008_NATIVE_RECIPE_INDEPENDENT_SOURCE_REFERENCE_CURRENT_GATES_OPEN','native_base_board_sha256':sha(board),'native_base_board':str(board.resolve()),'nomination_receipt_sha256':sha(rp/'receipt.json'),'exact_original_deletes':[{'kind':'segment','uuid':old['uuid'],'raw_net':old['net'],'geometry':old,'chunk_path':str(delete.resolve()),'chunk_sha256':sha(delete)}],'add_rows':adds,'new_vias':2,'new_segments':7,'new_zones':0,'old_protected_power_width_mm':.8,'replacement_protected_power_width_mm':.8,'replacement_protected_power_lock_preserved':True,'outside_contact_ledger_sha256':sha(OUT/'outside-contact-ledger.json'),'flash_obligations_sha256':sha(OUT/'native-flash-obligations.json'),'source_export_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','source_BOM_poses_limits_and_rate_changes':0,'all_unowned_original_chunks_untouched_by_recipe':True,'raw_aliases':0,'native_jobs':0,'board_written':False,'adopted':False,'whole_joint_source_retained_relations_reference_allCu_drill_thermal_drop_fault_and_native_gates':'OPEN'})
 print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
