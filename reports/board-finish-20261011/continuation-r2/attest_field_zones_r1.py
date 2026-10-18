"""Compose exact field-only zones on immutable eedf and inspect native settings."""
import hashlib,json,os,re,shutil,subprocess,sys
from decimal import Decimal
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import native_pose_signal_contract as N
C=N.C;OUT=H/'field-zone-native-contract-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh native field-zone attestation required')
    recipe=H/'field-power/full-field-zone-recipe-r2/receipt.json';spec=json.loads(recipe.read_bytes())
    if sha(recipe)!='0ae126294c01a85b4cd2c874d274adb437106ad5ee8bdc6e06a16fadf7f76264':raise ValueError('Exact field zone recipe changed')
    parent=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';raw=parent.read_bytes();inv=C.inventory(raw)
    if digest(raw)!=spec['existing_native_discrete_sha256']:raise ValueError('Exact discrete parent changed')
    pins={str(p.resolve()):sha(p) for p in (parent,recipe,Path(__file__),H/'native_field_zone_shape_r1.py')};new={};expected=[]
    for row in spec['rows']:
        path=Path(row['chunk_file']);ch=path.read_bytes()
        if digest(ch)!=row['chunk_sha256'] or C.pcbtext.chunk_uuid(ch)!=row['uuid']:raise ValueError('Owned zone chunk differs')
        pins[str(path.resolve())]=sha(path)
        if row['uuid'] in inv[3]:raise ValueError('Existing UUID collision')
        rings=[]
        for body in re.findall(rb'\(polygon\s*\(pts\s*([\s\S]*?)\n\s*\)\s*\)',ch):
            ring=[]
            for a,b in re.findall(rb'\(xy\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)',body):
                ring.append([int(Decimal(a.decode())*1000000),int(Decimal(b.decode())*1000000)])
            rings.append(ring)
        if len(rings)!=row['holes']+1 or len(rings[0])!=row['outline_corners']:raise ValueError('Expected exact outer/hole extraction differs')
        new[row['uuid']]=ch;expected.append({'uuid':row['uuid'],'raw_net':row['net_raw'],'layer':row['layer'],'rings_IU':rings})
    data=inv[0]+b''.join(inv[1])+b''.join(new.values())+inv[2];after=C.inventory(data)
    if any(after[3].get(u)!=ch for u,ch in inv[3].items()) or after[4]!=inv[4] or after[0]!=inv[0] or after[2]!=inv[2]:raise ValueError('Unowned board entity changed')
    OUT.mkdir();copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';board.write_bytes(data)
    for suffix in ('.kicad_pro','.kicad_dru'):
        original=H/'sbc-native-contract-r1/copy'/('board'+suffix);shutil.copy2(original,board.with_suffix(suffix));pins[str(original.resolve())]=sha(original);pins[str(board.with_suffix(suffix).resolve())]=sha(board.with_suffix(suffix))
    expected_path=OUT/'expected.json';write(expected_path,{'candidate_sha256':digest(data),'zones':expected})
    pins[str(board.resolve())]=sha(board);pins[str(expected_path.resolve())]=sha(expected_path)
    write(OUT/'construction.json',{'parent_sha256':digest(raw),'candidate_sha256':digest(data),'owned_new_zones':len(new),'original_all_entities_Cu_FPs_zone_outlines_settings_exact':True,'source_rule_project_unchanged':True,'native_fill_caches_added':False,'production_board_changed':False,'adopted':False})
    command=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str((H/'native_field_zone_shape_r1.py').resolve()),str(expected_path.resolve()),str(board.resolve()),str((OUT/'native-zones.json').resolve())]
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','no_native_save_refill_DRC':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen field-zone native input changed: '+p)
    result=json.loads((OUT/'native-zones.json').read_bytes()) if (OUT/'native-zones.json').exists() else {'verdict':'NATIVE_HELPER_FAILED_BEFORE_RECEIPT','errors':[]}
    receipt={'verdict':result['verdict'],'native_exit_code':run.returncode,'candidate_sha256':digest(data),'parent_sha256':digest(raw),'zone_count':len(new),'native_holes_checked':result.get('native_holes_checked'),'errors':result.get('errors'),'full_source_API_and_68_actual_vias':'PENDING_SEPARATE_GATE','combined_SBC_native_refill_contact_current_DRC':'OPEN','adopted':False}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
    return 0 if run.returncode==0 and result['verdict'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
