"""Bind the completed native trial to the continuing board-finish status."""
import datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
import measure_cap_signal_r1 as M
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):
    if p.exists():raise ValueError('Fresh receipt required '+str(p))
    p.write_text(json.dumps(o,indent=1)+'\n',encoding='utf-8')
def main():
    out=HERE/'cap-signal-native-r1/measure';inputs=json.loads((out/'inputs.json').read_bytes());summary=json.loads((out/'summary.json').read_bytes());proof=json.loads((out/'proof.json').read_bytes());source=json.loads((out/'source-proof.json').read_bytes())
    M.verify_inputs(out,inputs,sha(out/'inputs.json'),M.ReadSet())
    candidate=Path(inputs['after_board']);M.validate_construction(HERE/'cap-signal-native-r1/construction.json',candidate)
    if source['verdict']!='PASS' or summary['board_sha256']!=sha(candidate) or proof['verdict']!='FAIL' or proof['connectivity']['lost'] or proof['connectivity_r06']['lost']!=13 or summary['drc_errors']:raise ValueError('Unexpected completed measurement')
    if sha(inputs['live_board'])!=inputs['before_sha256']:raise ValueError('Live board changed')
    checked=[out/n for n in ['inputs.json','source-proof.json','native-parity.json','partitions.json','drc.json','summary.json','proof.json','status.json']]
    receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':str(candidate.resolve()),'candidate_sha256':sha(candidate),'verdict':'REJECTED_FOR_ADOPTION_R06_CONTINUITY_LOSSES','native_summary':summary,'r07_connectivity':proof['connectivity'],'r06_connectivity':proof['connectivity_r06'],'fresh_source_and_native_api':'PASS;2717 components,2384 distinct raw nets,9590 source nodes,9609 matched pads,0 normalization collisions/defects','actual_added_annuli':'9 new-from-r07 vias,each flashed on all6 copper layers','cli_schematic_parity':'Copied-stem CLI check not independently executed; separate fresh-hierarchy source/native proof passed','live_board_sha256':sha(inputs['live_board']),'frozen_outputs':{str(p.resolve()):sha(p) for p in checked},'adopted':False,'manufacturing_ready':False}
    save(HERE/'cap-signal-native-r1/completed-measurement-r1.json',receipt)
    checkpoint={'utc':receipt['utc'],'task':'Finish the motherboard by continuing saved Claude revisions','latest_completed_trial':receipt,'ongoing_work':{'field_power':'Fresh combined power-source export PASS2723components/9609nodes/2388nets; exact14pad moves,6addedparts and2BOM pairs. Fieldownedcopper/returns under completion.','sbc_power':'Full-load CORE/SBC source and host-plane/cap/control routing; source/return/all-contact/native gates open.','r06_recovery':'CM widened controlled clock plus exact limited terminal-neck profile; coupled MOSI and XF repairs under construction.','ordinary_signals':'26 outer-only current-source DI/fault attempts completed without a path. New paired-return ordinary FPGAreset route failed independent mutual-copper clearance and is being repaired; no emitted board or adoption. RetainedVIPPO and paired-return current-source searches running.'},'resource_watch':'Existing r7 CPU/GPU watcher to21:39UTC;existing4KiCad slot design unchanged','adopted':False,'manufacturing_ready':False}
    save(HERE/'checkpoint-r3.json',checkpoint)
    paths=[BASE/'CURRENT_STATUS.json',BASE/'CURRENT_STATUS.txt',BASE/'README.md']
    backups={}
    for p in paths:
        backup=HERE/('checkpoint-r3-before-'+p.name);backup.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(backup.resolve()),'sha256':sha(backup)}
    record=json.loads(paths[0].read_bytes());record['continuation_r3']=checkpoint;record['updated_utc']=receipt['utc'];paths[0].write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    paths[1].write_text('Board finish continuation: '+receipt['utc']+'\nLive r07/r08 remains unchanged. Latest completed staged candidatec9a461fb:1346 missing pad joins,1355 uncapped API unconnected,0 ordinary DRC errors,181 warnings. r07+9/-0; r06+34/-13. Fresh source/native parity PASS. Adoption FAIL for13 r06 losses.\nCombined field/compute power source freshnative export PASS2723/9609/2388. Exact owned copper and source-rooted supply/return work continue at full fitted loads.\nFPGAreset paired-return proposal caught by independent mutualclearance audit; repositioning onlynewground companions. No fabricated output or manufacturing qualification.\nSee continuation-r2/checkpoint-r3.json.\n',encoding='utf-8')
    prior=paths[2].read_bytes();i=prior.find(b'\n')+1;note=('\nContinuation checkpoint '+receipt['utc']+'\n\nThe completed c9a461fb native trial reports1346 missing pad joins,0 ordinary DRC errors and181 warnings, r07+9/-0 and r06+34/-13. Clean fresh source/native API parity does not override those13 r06 losses: adoption remains rejected. Combined power-source export now passes2723components/9609nodes/2388nets; source-rooted supply/return copper and coupled signal repair continue at full fitted loads. See [checkpoint-r3](continuation-r2/checkpoint-r3.json).\n\n').encode();paths[2].write_bytes(prior[:i]+note+prior[i:])
    save(HERE/'checkpoint-document-receipt-r3.json',{'backups':backups,'after':{str(p.resolve()):sha(p) for p in paths},'all_prior_readme_bytes_preserved':paths[2].read_bytes().replace(note,b'',1)==prior,'live_unchanged':True,'adopted':False})
    print(json.dumps({'checkpoint':str(HERE/'checkpoint-r3.json'),'native_joins':summary['missing_pad_joins'],'drc_errors':summary['drc_errors'],'r06_losses':proof['connectivity_r06']['lost'],'live_unchanged':True}),flush=True)
if __name__=='__main__':main()
