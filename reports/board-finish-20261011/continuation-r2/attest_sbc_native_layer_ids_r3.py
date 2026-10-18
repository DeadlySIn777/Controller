"""Compare serialized/native silkscreen layers by their exact KiCad enum IDs."""
import hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE/'sbc-native-contract-r2-field-diagnostic';OUT=HERE/'sbc-native-contract-r3-layer-ids'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh native layer-ID attestation required')
    source=OLD/'native_field_diagnostic.py';text=source.read_text(encoding='utf-8')
    anchor="        mm=lambda p:[pcbnew.ToMM(p.x),pcbnew.ToMM(p.y)]"
    replacement=anchor+"\n        def native_layer_id(name):\n            return {'F.SilkS':pcbnew.F_SilkS,'B.SilkS':pcbnew.B_SilkS}.get(name,board.GetLayerID(name))"
    if text.count(anchor)!=1:raise ValueError('Exact layer-ID helper anchor differs')
    text=text.replace(anchor,replacement)
    old="str(text.GetLayerName())!=exp['native_layer']";new="int(text.GetLayer())!=int(native_layer_id(exp['native_layer']))"
    if text.count(old)!=1:raise ValueError('Exact native field layer comparison differs')
    text=text.replace(old,new)
    OUT.mkdir();helper=OUT/'native_layer_id_attestation.py';helper.write_text(text,encoding='utf-8')
    command=json.loads((OLD/'invocation.json').read_bytes())['command'];command[4]=str(helper.resolve());command[-1]=str((OUT/'native-parity.json').resolve())
    pins=json.loads((OLD/'inputs.json').read_bytes())
    for p in [Path(__file__),source,helper,OLD/'receipt.json']:pins[str(p.resolve())]=sha(p)
    write(OUT/'derivation.json',{'source_sha256':sha(source),'derived_sha256':sha(helper),'only_change':'Compare F.SilkS/B.SilkS serialization names using pcbnew.F_SilkS/B_SilkS enum IDs; all coordinate/angle/raw-net/pad-mask/shape/via and source checks unchanged','board_changed':False,'all15_prior_errors_only_display_name_aliases':True})
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','no_refill_save_DRC':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen native attestation input changed')
    report=json.loads((OUT/'native-parity.json').read_bytes())
    passed=run.returncode==0 and report.get('native_field_pose_diagnostic',{}).get('verdict')=='PASS' and report.get('summary',{}).get('parity_defects')==0
    receipt={'verdict':'PASS_SOURCE_API_26_POSES_68_VIAS_23_EXACT_SMD_PAD_MASKS_AND_ALL_FIELD_POSES' if passed else 'FAIL_NATIVE_LAYER_ID_CONTRACT','candidate_sha256':report.get('added_via_annuli',{}).get('board_sha256'),'native_exit_code':run.returncode,'native_summary':report.get('summary'),'power_zones_all_contacts_current_reference_and_full_refill_DRC':'OPEN','adopted':False}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True);return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
