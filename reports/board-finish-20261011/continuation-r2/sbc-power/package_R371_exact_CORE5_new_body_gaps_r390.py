"""Bind already completed R354 CORE5 bodies to the unchanged frozen R371 head."""
import sys,json,pickle,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354'
O=H/'sbc-power/CM79-R371-exact-CORE5-new-body-gap-parallel-handoff-r390'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b'
 g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());rows=[r for r in json.loads((R/'all-six-new-body-fill-only-reference-gaps.json').read_text())if L.norm(r['net'])=='/mc_local_power/CORE_5V'];tm={t['uuid']:t for t in h['tracks']}
 packet=[]
 for r in rows:
  f=R/(r['UUID']+'-new-actual-body-fill-only-source-reference-gap.wkb');assert sha(f)==r['gap_sha256'];packet.append({'exact_current_track':tm[r['UUID']],'raw_completed_body_reference':r,'exact_raw_gap_wkb_path':str(f.resolve()),'WKB_sha256':sha(f),'required_actual_reference_plane':'In1.Cu'if r['layer']in ('F.Cu','In2.Cu')else'In4.Cu'})
 pins=[p for p in h['pads']if L.norm(p['net'])=='/mc_local_power/CORE_5V'];put(O/'exact-CORE5-new-tracks-and-raw-body-reference-gaps.json',packet);(O/'exact-CORE5-source-pads-native-pins.pkl').write_bytes(pickle.dumps(pins,protocol=5));put(O/'exact-CORE5-source-pad-pin-summary.json',[{k:p.get(k)for k in ('uuid','ref','num','net','x','y','layers','hole')}for p in pins])
 fail=[r for r in rows if not r['full_source_fill_reference_gap_empty']];put(O/'receipt.json',{'verdict':'SAVED_CORE5_RAW_BODY_REFERENCE_GAP_HANDOFF_NO_NEW_SEARCH','current_model_sha256':sha(D/'model.pkl'),'R354_receipt_sha256':sha(R/'receipt.json'),'exact_new_CORE5_track_count':len(rows),'raw_nonempty_gap_count':len(fail),'raw_nonempty_gap_area_sum_mm2':sum(r['gap_area_mm2']for r in fail),'actual_CORE5_source_pad_count':len(pins),'all_geometry_unchanged_from_R354_to_R371':'CORE5 and J1 In1 exact; only IO3 and new LG In4 support added','blocker_attribution':'No completed CORE5 positive shadow blocker screen in this stream; raw per-UUID WKB retained','source_reference':'actual J11001.2 source-connected fill only','adoption':False,'script_sha256':sha(__file__)})
 print('R390',sha(O/'receipt.json'),len(rows),len(fail),sum(r['gap_area_mm2']for r in fail),flush=True)
if __name__=='__main__':main()
