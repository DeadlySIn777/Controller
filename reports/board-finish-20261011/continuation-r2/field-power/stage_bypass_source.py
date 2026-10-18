"""Freeze separate14+5 AB local-bypass source; prior14+4 remains immutable."""
import json,copy,re
from inventory import HERE,BASE,BOARD,NET,PARSER,load,sha
from stage_source import clone_group,replace_owned_label,owned_groups
from verify_source import verify_variant
from source_precheck import precheck
OUT=HERE/'ab-local-bypass-source'
def main():
 if OUT.exists():raise ValueError('Refuse immutable source variant')
 old=HERE/'ab-prereg-split-source';ledger=json.loads((old/'receipt-r3.json').read_text(encoding='utf-8'));saved={str(p):sha(p) for p in (old/'source').iterdir()};saved[str(old/'source-export/fresh.net')]=sha(old/'source-export/fresh.net');saved[str(BOARD)]=sha(BOARD)
 local=json.loads((HERE/'new-local-bypass-r1.json').read_text(encoding='utf-8'));chosen=next(c for c in local['candidates'] if c['local_all_paths_found']);part=local['new_component'];assert part['ref']=='C11095'
 source_parts,_,_=load();SBC=BASE/'continuation-r2/sbc-power/source-proposal-r2/integrated-power-source.json';sr=json.loads(SBC.read_text(encoding='utf-8'));sbcnew=set(sr['power_entry_components'])-set(source_parts);assert sbcnew=={'C11094'},sbcnew
 refs=set(source_parts)|set(ledger['new_components'])|sbcnew;assert len(refs)==2722 and 'C11095' not in refs
 OUT.mkdir();dest=OUT/'source';dest.mkdir()
 for p in (old/'source').iterdir():(dest/p.name).write_bytes(p.read_bytes())
 p=dest/'motherboard_power_entry.kicad_sch';s=p.read_text(encoding='utf-8');t=clone_group(s,'C11053','C11095',1150,3310);tmp='(kicad_sch '+t+')';tmp=replace_owned_label(tmp,'C11095','FIELD_FIELD_VCC','FIELD_B_5V_PRE');tmp=replace_owned_label(tmp,'C11095','FIELD_GND','FIELD_B_0V');t=tmp[len('(kicad_sch '):-1];s=s[:s.rfind(')')]+t+s[s.rfind(')'):];p.write_text(s,encoding='utf-8',newline='')
 receipt=copy.deepcopy(ledger);receipt.update(schema='root106-field-AB-local-bypass-exact14plus5-r1',variant=OUT.name,original_AB_source_receipt_sha256=sha(old/'receipt-r3.json'),original_AB_native_export_sha256=sha(old/'source-export/fresh.net'),native_export='PENDING_FRESH_NATIVE_EXPORT; no reused14plus4 export asserted current',frozen_14plus4_unchanged=True,C11076_original_pose_preserved=True,census={'original_components':2717,'AB_new':4,'SBC_new':['C11094'],'combined_prior_unique':len(refs),'proposed_local_C11095_is_unused':True,'combined_prior_SBC_receipt_sha256':sha(SBC)},expected_native_counts={'components':2722,'nodes':9607,'nets':2388,'existing_pin_net_moves':14,'new_parts':5},local_bypass_layout=chosen)
 receipt['new_components']['C11095']={k:part[k] for k in ['clone','mpn','value','footprint','pins']};receipt['files']={str(p.relative_to(OUT)):sha(p) for p in sorted(dest.iterdir())};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 object_gate=precheck(OUT);pin_gate=verify_variant(OUT);assert object_gate['verdict']==pin_gate['verdict']=='PASS'
 checks={'exact_object_delta':object_gate,'independent_pin_wire_label_graph':pin_gate,'all_prior_original_AB_files_before':saved,'all_prior_original_AB_files_after':{p:sha(p) for p in saved},'source_stage_only':True,'native_jobs':0};assert checks['all_prior_original_AB_files_before']==checks['all_prior_original_AB_files_after'];(OUT/'host-precheck.json').write_text(json.dumps(checks,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'old_pin_moves':14,'new_parts':5,'combined_previous_unique_refs':len(refs),'C11095_pose':chosen['pose_mm'],'cap_loop_mm':chosen['paths'][0]['length_mm']+chosen['paths'][2]['length_mm'],'object_gate':object_gate['verdict'],'pin_gate':pin_gate['verdict'],'native_export':'PENDING_FRESH','source_receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
