"""Exact raw-native six-delete/15-add U11015 recipe; no board output."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib
from pathlib import Path
from inventory import sha
from verify_source import parse,atom
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'u11015-native-recipe-r48'

def write(path,x):path.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();rp=HERE/'u11015-reverse-companion-repair-r44';r=json.loads((rp/'receipt.json').read_text());assert sha(rp/'receipt.json')=='590b1d52ff80afbccc311a5e157cade34a917dc59eb646643c9b45185a5e992d';assert sha(rp/'proposed-discrete.pkl')==r['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());assert len(d['vias'])==3 and len(d['tracks'])==12
 board=HERE.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';b=board.read_bytes();_,chunks,_=C.O.C.pcbtext.split(b);byid={C.O.C.pcbtext.chunk_uuid(x):x for x in chunks if C.O.C.pcbtext.chunk_uuid(x)}
 removed=[];adds=[]
 for t in r['owned_original_track_removals']:
  uid=t['uuid'];ch=byid[uid];assert C.O.C.pcbtext.chunk_kind(ch)=='segment';a=parse(ch.decode('utf-8'));assert atom(a,'net')==t['net'] and atom(a,'layer')==t['layer'];path=OUT/(uid+'.delete-original-segment-chunk');path.write_bytes(ch);removed.append({'kind':'segment','uuid':uid,'raw_net':t['net'],'chunk_path':str(path.resolve()),'exact_original_chunk_sha256':sha(path),'expected_geometry':t})
 tokens={}
 for kind,items in [('via',d['vias']),('segment',d['tracks'])]:
  for q in items:
   uid=q['uuid'];assert uid not in byid;tokens.setdefault(C.norm(q['net']),set()).add(q['net'])
   if kind=='via':text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],uid)
   else:
    assert q['w']>=.20;text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],q['layer'],q['net'],uid)
   assert C.O.C.pcbtext.chunk_kind(text.encode())==kind and C.O.C.pcbtext.chunk_uuid(text.encode())==uid;assert atom(parse(text),'net')==q['net'];path=OUT/(uid+'.'+kind+'-chunk');path.write_text(text,encoding='utf-8',newline='');adds.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 assert all(len(x)==1 for x in tokens.values());source=HERE/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 flash=[{'uuid':v['uuid'],'raw_net':v['net'],'required_native_postfill_flash':['B.Cu','In3.Cu'] if v['net']=='/motherboard_power_entry/AUX24_A_ILIM' else ['B.Cu','In1.Cu'],'planning_all6_annuli_are_not_native_flash_evidence':True} for v in d['vias']]
 write(OUT/'native-flash-obligations.json',flash);write(OUT/'exact-outside-contact-ledger.json',r['exact_outside_contact_ledger']);(OUT/'proposed-discrete.pkl').write_bytes((rp/'proposed-discrete.pkl').read_bytes())
 proof=HERE/'u11015-r44-joint-contact-audit-r46/receipt.json';joint=json.loads(proof.read_text());assert joint['input_R44_receipt_SHA256']==sha(rp/'receipt.json')
 write(OUT/'receipt.json',{'verdict':'FROZEN_SCOPED_U11015_NATIVE_RECIPE_CONTACT_CURRENT_FILL_PENDING','native_base_board':str(board.resolve()),'native_base_board_sha256':sha(board),'fresh_native_source_export_sha256':sha(source),'constructive_R44_receipt_sha256':sha(rp/'receipt.json'),'independent_R45_discrete_receipt_sha256':sha(HERE/'u11015-r44-independent-discrete-audit-r45/receipt.json'),'independent_R46_joint_contact_receipt_sha256':sha(proof),'R46_verdict':joint['verdict'],'new_vias':3,'new_segments':12,'new_zones':0,'exact_removed_original_segments':6,'delete_rows':removed,'add_rows':adds,'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'outside_contact_ledger_sha256':sha(OUT/'exact-outside-contact-ledger.json'),'native_flash_obligations_sha256':sha(OUT/'native-flash-obligations.json'),'RTN3_11_not_merged_with_GND6':True,'ILIM_R11056_and_DVDT_C11068_BOM_pose_pinroles_limits_unchanged':True,'all_unowned_original_chunks_unchanged_by_recipe':True,'raw_aliases_introduced':False,'scope':'only U11015 GND6 ground feed and explicit ILIM/DVDT companion restoration; other bare grounds remain open','new_foreign_zone_cut_and_reference_current_native_gates':'OPEN','native_jobs':0,'board_written':False,'board_adopted':False});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
