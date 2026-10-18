"""Complete the native DRC diagnostic after the preserved R9 flash failure.

Never repeat the completed Python fill, alter its failure, save native copper,
or imply acceptance from a lower unconnected count. Use the existing main slot.
"""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
STAGE=H/'SAFE-exploratory-native-trial-r9';MEASURE=STAGE/'measure'
OUT=H/'R9-failed-flash-native-DRC-diagnostic-r113'
EXPECTED='3b579aa7ea4cf4c070c22e36df8dca2fbfcdefccd0e3c2a874ebf337acda3919'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists();board=MEASURE/'copy/board.kicad_pcb'
    assert sha(board)==EXPECTED
    contract=read(MEASURE/'actual-full-refill-contract.json')
    assert contract['candidate_sha256']==EXPECTED and contract['full_native_filler_ok']
    assert contract['verdict']=='FAIL_ACTUAL_FULL_NATIVE_FILL_CU_OR_FLASH_CONTRACT'
    assert contract['postfill_Cu_or_flash_errors']==[{'uuid':'18701851-0390-4dc4-b03d-f8e1cd66c395','missing_required_old_native_flashes':['In3.Cu'],'actual_flashes':['F.Cu','In1.Cu','In4.Cu','B.Cu']}]
    proof=read(MEASURE/'matching-stem-source-proof.json');assert proof['verdict']=='PASS'
    parts=read(MEASURE/'partitions.json');assert parts['sha256']==EXPECTED and parts['refilled']
    wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavym.sh')
    cli=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
    files=[Path(__file__),wrapper,cli,STAGE/'receipt.json',STAGE/'inputs.json',STAGE/'native-postfill-via-obligations.json',MEASURE/'actual-full-refill-contract.json',MEASURE/'partitions.json',MEASURE/'matching-stem-source-proof.json',MEASURE/'matching-stem-fresh.net']
    files.extend(p for p in (MEASURE/'copy').rglob('*') if p.is_file())
    pins={str(p.resolve()):sha(p) for p in files}
    def check():
        for p,s in pins.items():assert sha(p)==s,p
    OUT.mkdir()
    command=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str((OUT/'drc.json').resolve()),'board.kicad_pcb']
    record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'NATIVE_DRC_RUNNING_AFTER_PRESERVED_FLASH_FAILURE','candidate_sha256':EXPECTED,'actual_python_refill_already_complete':True,'api_unconnected_count':parts['api_unconnected_count'],'uncapped_pad_island_joins':parts['pad_island_joins'],'failed_flash_contract_sha256':sha(MEASURE/'actual-full-refill-contract.json'),'pins':pins,'command':command,'cwd':str((MEASURE/'copy').resolve()),'existing_reserved_main_KiCad_slots':1,'new_heavy_slots':0,'adopted':False,'manufacturing_ready':False}
    write(OUT/'inputs.json',record);write(OUT/'status.json',record);print(record['phase'],flush=True)
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    check()
    with (OUT/'drc.log').open('w',encoding='utf-8') as log:r=subprocess.run(command,cwd=MEASURE/'copy',env=env,stdout=log,stderr=subprocess.STDOUT)
    check();report=OUT/'drc.json'
    assert report.exists() and report.stat().st_size,'Native CLI produced no report'
    drc=read(report);counts={}
    for kind in ('violations','unconnected_items','schematic_parity'):
        rows=drc.get(kind,[]);counts[kind]=len(rows)
        counts[kind+'_types']={}
        for q in rows:
            key=q.get('type','UNKNOWN');counts[kind+'_types'][key]=counts[kind+'_types'].get(key,0)+1
    log=(OUT/'drc.log').read_text(errors='replace')
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'NATIVE_DRC_DIAGNOSTIC_COMPLETE_FLASH_CONTRACT_REMAINS_FAILED','candidate_sha256':EXPECTED,'cli_exit_code':r.returncode,'drc_sha256':sha(report),'counts':counts,'schematic_parity_execution_blocked':'Failed to fetch schematic netlist' in log or 'Schematic parity tests require' in log,'inputs_sha256':sha(OUT/'inputs.json'),'python_refill_repeated':False,'native_copper_saved':False,'adopted':False,'manufacturing_ready':False}
    write(OUT/'receipt.json',result);write(OUT/'status.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
