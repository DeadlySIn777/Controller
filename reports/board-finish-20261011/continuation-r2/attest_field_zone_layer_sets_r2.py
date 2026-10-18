"""Use the zone's actual layer set rather than inherited single-layer accessor."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;OLD=H/'field-zone-native-contract-r1';OUT=H/'field-zone-native-contract-r2-layer-sets'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh actual-zone-layer attestation required')
    prior=json.loads((OLD/'native-zones.json').read_bytes())
    if not prior['errors'] or any(r.get('field')!='layer' for r in prior['errors']):raise ValueError('Prior errors are not exclusively inherited zone layer access')
    source=H/'native_field_zone_shape_r1.py';code=source.read_text(encoding='utf-8')
    a="'layer':str(z.GetLayerName())";b="'layers':sorted(str(board.GetLayerName(int(layer))) for layer in z.GetLayerSet().Seq())"
    if code.count(a)!=1:raise ValueError('Exact native layer accessor anchor differs')
    code=code.replace(a,b);a="'layer':exp['layer']";b="'layers':[exp['layer']]"
    if code.count(a)!=1:raise ValueError('Exact expected layer anchor differs')
    code=code.replace(a,b)
    OUT.mkdir();helper=OUT/'native_field_zone_layer_sets_r2.py';helper.write_text(code,encoding='utf-8')
    command=json.loads((OLD/'invocation.json').read_bytes())['command'];command[4]=str(helper.resolve());command[-1]=str((OUT/'native-zones.json').resolve())
    pins=json.loads((OLD/'inputs.json').read_bytes())
    for p in (source,helper,Path(__file__),OLD/'native-zones.json',OLD/'receipt.json'):pins[str(p.resolve())]=sha(p)
    write(OUT/'inputs.json',pins);write(OUT/'derivation.json',{'only_change':'Compare exact singleton GetLayerSet().Seq() against declared layer; inherited ZONE.GetLayerName returns single-item default F.Cu. All integer ring/raw-net/settings checks unchanged.','prior_error_count':len(prior['errors']),'board_changed':False,'prior_all41_outer_and315_holes_exact':all(r['outer_and_all_hole_integer_coordinates_exact'] for r in prior['rows'])})
    write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','no_save_refill_DRC':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen native layer-set input changed')
    report=json.loads((OUT/'native-zones.json').read_bytes())
    receipt={k:v for k,v in report.items() if k!='rows'};receipt['native_exit_code']=run.returncode
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
    return 0 if run.returncode==0 and report['verdict'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
