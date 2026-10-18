"""Test precise old fault wall removals against every remaining old contact."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import fast_contacts as F
import contact_layout as C
OUT=H/'U10003-three-exact-fault-wall-retention-test-r127'
IDS={'bd3e65f9-fe77-4a1f-88a1-c704d85af39f','ca9b0c5d-8d6f-44b2-8bec-780b6f1b3f3f','774ec021-d81e-471e-a8c8-0ea85fa50f67'}
NET='/motherboard_do/DOA_FLT_N_FIELD'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());old={t['uuid']:t for t in g['tracks']};removed=[t for t in h['tracks'] if t['uuid'] in IDS];assert len(removed)==3
    for t in removed:assert t==old[t['uuid']] and C.norm(t['net'])==NET and t['layer']=='B.Cu' and t['w']==.2 and t['locked']
    before=F.graph(full,NET);test={**full,'tracks':[t for t in full['tracks'] if t['uuid'] not in IDS]};after=F.graph(test,NET);membership={k:i for i,xs in enumerate(after) for k in F.discrete_keys(xs)};losses=[]
    for i,xs in enumerate(before):
        keys=F.discrete_keys(xs)-{('track',u) for u in IDS};missing=[list(k) for k in keys if k not in membership];groups={membership[k] for k in keys if k in membership}
        if missing or len(groups)>1:losses.append({'old_group':i,'missing':missing,'after_groups':sorted(groups),'retained_pad_rows':[{k:v for k,v in q.items() if k not in ['shape','source']} for q in xs if q['kind']=='pad' and q['pin']]})
    record={'verdict':'ALL_REMAINING_OLD_FAULT_DISCRETE_CONTACTS_RETAINED_THREE_PRECISE_WALL_REMOVALS_ONLY' if not losses else 'EXACT_FAULT_WALL_REMOVAL_BREAKS_OLD_CONTACTS_REPLACEMENT_REQUIRED','parent_model_sha256':sha(mp),'removed_exact_original_tracks':removed,'all_other_Cu_FP_source_vias_native_zone_definitions_and_actual_fill_records_unchanged':True,'before_groups':len(before),'after_groups':len(after),'losses':losses,'no_restore_or_contact_invention':True,'removed_old_Cu_requires_scoped_native_authority_and_full_all_original_no_loss':True,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
