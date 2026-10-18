"""Save an honest resumable engineering checkpoint; preserve prior source bytes."""
import datetime,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();evidence={}
    names=['native-198b-geometry/receipt.json','remaining-net-census-r2.json','field-power/normal-model-r2.json','field-power/ab-prereg-split-source/source-export/receipt-r2.json','coupled-recovery/aux-exact-audit-r3.json','coupled-recovery/aux-cap-recipe-audit-r2.json','cap-native-r3/native-attestation.json','new-via-escape-r2/result.json','outer-ground-channel-r1/result.json','resource-monitor-r7/previous-monitor-receipt.json','aux-native-r1/measure/native-parity-r4.json','aux-native-r1/measure/status.json']
    for name in names:
        p=HERE/name
        if p.is_file():evidence[name]={'path':str(p.resolve()),'sha256':sha(p)}
    checkpoint={'updated_utc':now,'scope':'ROOT106 experimental native board; continue Claude work, preserve adopted Source26/ROOT104/CAD30','current_measured_board_sha256':'198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab','current_missing_pad_joins':1348,'current_r06_losses':14,'current_ordinary_drc_errors':0,'live_r07_r08_unchanged':True,'adopted':False,'manufacturing_ready':False,'evidence':evidence,'active_work':['Exact-name AUX capacitor layout native board construction and measurement','Coupled XF and remaining original r06 relationship recovery','Source-rooted full-current field supply/return plane bridges and regulator bypass/fanout','CORE variable-width power lane, IO3 restoration, complete fanouts and return','Independent ordinary two-via escape audit; future native refill mandatory'],'failures_preserved':['Old AUX 0fb4ae9b source/native parity rejects normalization collision on AUX_24V_A; no adoption','Sensor zero-via path has 0.385107 mm2 full-copper-body reference gap and was withheld','153 retained-via and154 fixed-outer-ground-channel searches yielded no accepted route; finite bounds only','Owned short native API GetWidth assertion stopped; explicit-layer derivative finishes and catches real net collision','C68 PAD.GetLayer nominal0 is inappropriate; native actual IsOnLayer(B.Cu)/!IsOnLayer(F.Cu) attestation passes'],'resource':['r6 completed358 samples maxCPU63.6percent/GPU52C82.38W zero breaches','r7 active; existing4heavy KiCad slots retained; no global WSL hard-thread-cap claim'],'open':['All1348required joins and14r06 loss preservation; neither has been waived','Actual current/IR/thermal/return/SI/controlled/analog/safety/DFM/mechanical qualification','Combined exact source/export/native/ERC proof for electrical corrections','Final PCBWay stackup and selective compute connector current qualification','Final manufacture audit and actual fabrication artifacts after completion']}
    p=HERE/'checkpoint-r1.json'
    if p.exists():raise ValueError('Fresh checkpoint revision required')
    p.write_text(json.dumps(checkpoint,indent=1)+'\n',encoding='utf-8')
    note=("**Board continuation checkpoint - 11 October 2026, 20:42 UTC:** [resumable evidence]("+('reports/board-finish-20261011/continuation-r2/checkpoint-r1.json' if False else 'board-finish-20261011/continuation-r2/checkpoint-r1.json')+") records continued work on measured `198bba53...`; live r07/r08 and adopted hardware remain untouched. The board still has 1,348 required pad joins and 14 original r06 losses. Fresh exact native fills/annuli passed with all inputs unchanged. A full signed field planning model retains all simultaneous loads (A input about4.584A, B about4.769A), and an isolated field source export passes its14intentional pin moves plus4new parts. Coupled AUX and compute plane changes are staged with retained-contact obligations. KiCad confirms C11068's exact underside pad pose. The first AUX candidate fails native net parity because a normalized slash spelling creates a second physical net; corrected exact-name constructors and separate receipts are retained. A new ordinary two-via signal path is under independent audit; none is adopted. The resource watch completed358samples without breach and a successor is active. Routing, electrical, physical and manufacturing completion remain open.\n\n")
    docs=[ROOT/'PROJECT_MEMORY.md',ROOT/'reports/ENGINEERING_STATUS.md',BASE/'README.md'];backups=HERE/'checkpoint-source-backups-r1';backups.mkdir()
    identities={}
    for doc in docs:
        raw=doc.read_bytes();(backups/(doc.name+'.before')).write_bytes(raw)
        link_note=note
        if doc.name=='PROJECT_MEMORY.md':link_note=link_note.replace('](board-finish-20261011/','](reports/board-finish-20261011/')
        elif doc==BASE/'README.md':link_note=link_note.replace('](board-finish-20261011/continuation-r2/','](continuation-r2/')
        # Insert following the initial heading line while preserving every
        # pre-existing byte, including its historical encoding and line endings.
        end=raw.find(b'\n')+1
        if end<=0:end=0
        new=raw[:end]+b'\n'+link_note.encode('utf-8')+raw[end:];doc.write_bytes(new)
        if doc.read_bytes()!=new:raise ValueError('Checkpoint write mismatch')
        identities[str(doc)]={'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':sha(doc),'old_bytes_retained_exactly':True}
    (HERE/'checkpoint-document-receipt-r1.json').write_text(json.dumps({'updated_utc':now,'checkpoint_sha256':sha(p),'documents':identities,'native_board_or_source_changed':False,'adopted':False},indent=1)+'\n',encoding='utf-8')
    status=BASE/'CURRENT_STATUS.json';old=status.read_bytes();(backups/'CURRENT_STATUS.json.before').write_bytes(old);data=json.loads(old);data['updated_utc']=now;data['continuation_r2']=checkpoint;status.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checkpoint':str(p),'live_or_adopted_changed':False,'manufacturing_ready':False}),flush=True)
if __name__=='__main__':main()
