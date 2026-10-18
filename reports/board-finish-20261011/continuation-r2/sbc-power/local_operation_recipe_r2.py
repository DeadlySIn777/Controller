"""Exact owned local operation recipe; partial until joint plane/control completion."""
import json,hashlib,re
import local_copper_r3 as T
import raw_net_tokens_r2 as N
L=T.L;p=T.p
def main():
    g,h,tail=T.model();scope,native,prior,omit=tail
    old=json.loads((L.OUT/'local-copper-r2.json').read_text());new=json.loads((L.OUT/'local-copper-r3.json').read_text());dropv=set(new['superseded_r2_local_via_uuids']);dropt=set(new['superseded_r2_local_track_uuids'])
    via=[x for x in old['new_vias'] if x['uuid'] not in dropv]+new['new_vias'];tracks=[x for x in old['new_tracks'] if x['uuid'] not in dropt]+new['new_tracks']
    poses={'U11012':[116,161.4,-90],'C11061':[119.5,160.4,90],'C11062':[116.775,161.65,0],'C11063':[115.75,165.325,-90],'C15001':[115.752,164.575,90],'C15002':[118.427,163.775,0]}
    foot={p.base.ref_of(ch):(uid,ch) for uid,ch in native.items() if p.base.pcbtext.chunk_kind(ch)=='footprint'}
    moved=[]
    for ref,pose in poses.items():
        uid,ch=foot[ref];moved.append({'ref':ref,'uuid':uid,'original_native_chunk_sha256':hashlib.sha256(ch).hexdigest(),'target_native_at_mm_deg':pose,'native_layer_unchanged':re.search(rb'\(layer "([^"]+)"\)',ch).group(1).decode(),'every_pad_net_unchanged':True,'target_pad_positions':[{'uuid':q['uuid'],'num':q['num'],'x':q['x'],'y':q['y'],'net_raw':N.raw(q['net'])} for q in h['pads'] if q['ref']==ref]})
    result={'status':'COMPLETED_LOCAL_PIECES_ONLY_JOINT_PLANES_AND_CONTROLS_OPEN','exact_input_board_sha256':L.live.SHA,'move_native_footprints':moved,'remove_existing_item_uuids':sorted(omit),'remove_existing_item_chunks':[{'uuid':u,'sha256':hashlib.sha256(native[u]).hexdigest(),'kind':p.base.pcbtext.chunk_kind(native[u])} for u in sorted(omit)],'removal_contact_ledger_sources':['power-audit/sbc-198b-source-proposal/bounded-five-part-fanout-proposal.json','continuation-r2/sbc-power/cap-pair-r1.json'],'new_vias':via,'new_tracks':tracks,'required_additional_CORE_via_at_mm':[114.2,161.4],'original_retained_ground_via_uuids':['45617979-cdc6-42db-9b78-94c762d1aff4','7cb8b8f4-41dd-4467-b9bf-968886ddbdc6'],'source_changes_owned_by_field_combined_clone_only':{'L11001':'6.8uH XAL1010-682MED','C11094':'330uF16V bulk CORE_5V/LOGIC_GND','C11061':'root v2 25V same0805 correction'},'no_all_board_reserialization':'Copy exact 198b bytes; replace only listed footprint chunks by native-aware whole-footprint pose transforms, remove only listed old owned copper UUID chunks, append new exact raw-net copper and explicitly bound zone chunks. Preserve original chunks outside exact ledger. Native refill only after composition and freeze.','emission_raw_net_registry':'raw-net-token-binding-r2.json','remaining_obligations':['joint EN/PG copper and CORE/SBC pours','full CORE/SBC branch and return IR/current sharing','all original pad groups plus old track/via barrel and plane contacts, including displaced F LOGIC_GND and IO3','r3 C63 ordinary aperture/body/courtyard verification','native full board DRC and dual connectivity guard','selective six CM power contacts qualification'],'native_jobs':0,'board_written':False}
    (L.OUT/'completed-local-operation-recipe-r2.json').write_text(json.dumps(result,indent=2)+'\n');print('LOCAL_RECIPE',len(moved),len(omit),len(via),len(tracks),flush=True)
if __name__=='__main__':main()
