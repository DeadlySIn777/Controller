"""Preserve first field failure and collect every native text/field discrepancy."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE/'sbc-native-contract-r1';OUT=HERE/'sbc-native-contract-r2-field-diagnostic'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh diagnostic required')
    source=HERE/'native_sbc_contract_r1.py';text=source.read_text(encoding='utf-8')
    text=text.replace('cu=list(board.GetEnabledLayers().CuStack()); rows=[]','cu=list(board.GetEnabledLayers().CuStack()); rows=[]; field_errors=[]')
    old="                if mm(text.GetPosition())!=exp['absolute_position_mm'] or str(text.GetLayerName())!=exp['native_layer'] or not angle_ok(text.GetTextAngleDegrees(),exp['native_angle_deg']):raise ValueError('Native field/text pose differs:'+row['ref']+'/'+exp['identity'])"
    new="                if mm(text.GetPosition())!=exp['absolute_position_mm'] or str(text.GetLayerName())!=exp['native_layer'] or not angle_ok(text.GetTextAngleDegrees(),exp['native_angle_deg']):field_errors.append({'ref':row['ref'],'expected':exp,'actual_position_mm':mm(text.GetPosition()),'actual_layer':str(text.GetLayerName()),'actual_angle_deg':text.GetTextAngleDegrees()})"
    if text.count(old)!=1:raise ValueError('Exact diagnostic edit anchor differs')
    text=text.replace(old,new)
    text=text.replace("        output.write_text(json.dumps(report,indent=1)+'\\n',encoding='utf-8')", "        report['native_field_pose_diagnostic']={'verdict':'FAIL' if field_errors else 'PASS','errors':field_errors,'board_unchanged':True}\n        if field_errors:report['SBC_exact_native_pad_masks_shapes_angles_and_field_poses']['verdict']='FAIL_FIELD_POSES'\n        output.write_text(json.dumps(report,indent=1)+'\\n',encoding='utf-8')")
    text=text.replace('        return 0','        return 1 if field_errors else 0')
    OUT.mkdir();helper=OUT/'native_field_diagnostic.py';helper.write_text(text,encoding='utf-8')
    command=json.loads((OLD/'invocation.json').read_bytes())['command'];command[4]=str(helper.resolve());command[-1]=str((OUT/'native-parity.json').resolve())
    pins=json.loads((OLD/'inputs.json').read_bytes())
    for p in [Path(__file__),source,helper,OLD/'receipt.json']:pins[str(p.resolve())]=sha(p)
    write(OUT/'derivation.json',{'source_sha256':sha(source),'derived_sha256':sha(helper),'changes':'Collect all field pose errors instead of stopping on first; retain all original pose/pad/via/source gates; any mismatch returns failure','board_changed':False})
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','no_refill_save_DRC':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen diagnostic input changed')
    report=json.loads((OUT/'native-parity.json').read_bytes());diagnostic=report.get('native_field_pose_diagnostic',{})
    write(OUT/'receipt.json',{'native_exit_code':run.returncode,'candidate_sha256':report.get('added_via_annuli',{}).get('board_sha256'),'diagnostic':diagnostic,'adopted':False})
    print(json.dumps(diagnostic),flush=True);return run.returncode
if __name__=='__main__':raise SystemExit(main())
