"""Source-bound single-footprint clone and exact BOM-property chunk edits."""
import json,re,hashlib,uuid
import local_copper_r3 as T
L=T.L;p=T.p
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    g,h,tail=T.model();native=tail[1];feet={p.base.ref_of(ch):(uid,ch) for uid,ch in native.items() if p.base.pcbtext.chunk_kind(ch)=='footprint'};dest=L.OUT/'source-native-frozen-r2';dest.mkdir(exist_ok=True)
    source_uuid='d6b66fa8-82f0-599c-95d9-3923ccf17ca7';path='/383e4f6a-2216-5d67-a14d-d839c5a852c2/'+source_uuid
    oldid,old=feet['C11088'];new=old.replace(b'(property "Reference" "C11088"',b'(property "Reference" "C11094"');new=re.sub(rb'\(at [^\)]+\)',b'(at 249.5 102 180)',new,count=1)
    new,count=re.subn(rb'\(path "[^"]+"\)',('(path "'+path+'")').encode(),new);assert count==1
    ledger={}
    for u in re.findall(rb'\(uuid "([^"]+)"\)',old):ledger[u.decode()]=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-sbc-r2-C11094/'+source_uuid+'/'+u.decode()))
    for a,b in ledger.items():new=new.replace(('(uuid "'+a+'")').encode(),('(uuid "'+b+'")').encode())
    assert b'"C11088"' not in new and b'"C11094"' in new and source_uuid.encode() in new
    (dest/'C11094.footprint-chunk').write_bytes(new);rows=[]
    changes={'L11001':{'Value':'6.8uH 20%','MPN':'XAL1010-682MED'},'C11061':{'Value':'4.7uF 25V X7R','MPN':'C2012X7R1E475K125AB'}}
    for ref,props in changes.items():
        uid,ch=feet[ref];replacement=ch;updates=[]
        for name,value in props.items():
            pat=rb'(\(property "'+name.encode()+rb'" ")([^"\n]*)(")';matches=list(re.finditer(pat,replacement));assert len(matches)==1,(ref,name,len(matches));oldvalue=matches[0].group(2).decode();replacement=re.sub(pat,lambda m:m.group(1)+value.encode()+m.group(3),replacement,count=1);updates.append({'property':name,'old':oldvalue,'new':value})
        f=dest/(ref+'.BOM-only.footprint-chunk');f.write_bytes(replacement);rows.append({'ref':ref,'uuid':uid,'original_native_chunk_sha256':digest(ch),'new_chunk_path':str(f.resolve()),'new_chunk_sha256':digest(replacement),'property_updates':updates,'pose_pads_nets_and_geometry_unchanged':True})
    result={'exact_board':L.live.SHA,'source_native_netlist_sha256':'02e4e4cbbe0272b3f45f9368fb2a3ca2766f9e6a1fdeb1bf87d5f8e5c689e1b5','new_C11094':{'ref':'C11094','new_native_chunk_path':str((dest/'C11094.footprint-chunk').resolve()),'new_native_chunk_sha256':digest(new),'cloned_from_ref':'C11088','original_native_chunk_sha256':digest(old),'new_footprint_uuid':ledger[oldid],'private_uuid_ledger':ledger,'schematic_path':path,'schematic_symbol_uuid':source_uuid,'target_native_pose':[249.5,102,180],'layer':'F.Cu','pad1_CORE_at':[252.3,102],'pad2_GND_at':[246.7,102],'pad_raw_nets':{'1':'/mc_local_power{slash}CORE_5V','2':'/LOGIC_GND'},'host_full_courtyard_and_pad_geometry_clear':True,'physical_capacitor_path_parasitics_and_loop_qualification_open':True},'two_BOM_property_chunk_edits':rows,'C11061_pose_composition':'Apply this exact Value/MPN-only chunk edit and then the six-part local recipe whole-footprint pose; do not overwrite either operation.','all_other_chunks_preserved':'source-only snippets; no board constructed','no_net_normalization_aliases':True,'native_body_mask_DRC_sourceparity_and_fullcontact_gate_open':True,'native_jobs':0}
    (dest/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('SOURCE_NATIVE_FROZEN',digest(new),rows,flush=True)
if __name__=='__main__':main()
