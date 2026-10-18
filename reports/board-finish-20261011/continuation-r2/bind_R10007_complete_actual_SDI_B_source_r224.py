"""Bind the complete retained SDI source group, with no display-window clipping."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'R10007-complete-actual-SDI-B-source-r224'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5';g,h,b,q,full=pickle.loads(mp.read_bytes());ids={p['uuid']for p in h['pads']if p['ref']=='R10007'};scene={**full,'pads':[p for p in h['pads']if p['uuid']not in ids]};_,groups=K.physical(scene,'/motherboard_do/DOA_SDI_HOST',K.hole_context(scene));root=K.root(groups,'U13004','31');assert any(r['kind']=='pad'and(r['ref'],str(r['pin']))==('U10003','3')for r in root);source=unary_union([r['shape']for r in root if r['layer']=='B.Cu']);p=OUT/'complete-actual-SDI-B-Cu.wkb';p.write_bytes(source.wkb);r={'verdict':'COMPLETE_RETAINED_ACTUAL_DRILLED_SDI_B_SOURCE_BOUND','model_sha256':sha(mp),'actual_driver_pad':'U13004.31','retained_isolator_pad':'U10003.3','old_R10007_pad_UUIDs_absent':sorted(ids),'source_layer_keys':len(K.keys(root)),'source_WKB_sha256':sha(p),'complete_source_no_display_crop':True,'source_bounds_mm':list(source.bounds),'native_jobs':0,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R224_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
