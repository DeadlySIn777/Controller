"""Freeze read-only DIC attempt and unchanged measured parent checkpoint."""
import datetime,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
STAGE=HERE.parent.parent
REPORT=STAGE.parent.parent.parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
destination=HERE/'checkpoint.json'
if destination.exists():raise ValueError('Immutable checkpoint already exists')
screen=json.loads((HERE/'stitch-screen.json').read_bytes())
if screen['proposal'] is not None or screen['verdict']!='NO_COMPLETE_PATH_IN_BOUNDED_MODEL':raise ValueError('Unexpected candidate/path')
ready=json.loads((STAGE/'ready-r1.json').read_bytes())
for pins in (ready['files'],screen['source_files_sha256']):
    for path,digest in pins.items():
        if sha(path)!=digest:raise ValueError('Frozen input changed:'+path)
paths=[HERE/'stitch-screen.json',HERE/'host-controls.json',HERE/'screen_dic_stitch.py',HERE/'derivation.json',HERE/'test_controls.py',Path(__file__),
       STAGE/'runtime-audit/strict-reference-r1.json',STAGE/'runtime-audit/final-consistency-r1.json',REPORT/'measure/r07-four-fag-shared/proof.json',REPORT/'measure/r07-four-fag-shared/status.json',REPORT/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb',
       HERE.parent/'bounded-closure-r1.json',HERE.parent/'closure-r1-controls.json']
checkpoint={'schema':'frozen-dic-ownstitch-bounded-checkpoint-v1','verdict':'PRESERVED_NO_NEW_BOARD','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_sha256':screen['candidate_sha256'],'measured_parent':'Originalr07 allitems plus287owned additions, unchanged','required_r06_relationship':['R13013.1#0','U13003.3#0'],'attempt_result':screen['verdict'],'grounded_return_options_per_window':[[r['complete_grounded_return_options'] for r in w['newreturn_component_diagnostics']] for w in screen['windows']],
            'strict_native_parent_result':{'actual_r07_completed':7,'actual_r07_lost':0,'r06_completed':33,'r06_lost':14,'ordinary_DRC_errors':0,'warnings':180,'adoption':'WITHHELD_FATAL_R06_LOSS'},
            'files_sha256':{str(p.resolve()):sha(p) for p in paths},'ready_source_files_currently_verified':len(ready['files']),'screen_read_set_currently_verified':len(screen['source_files_sha256']),
            'new_board_emitted':False,'tail_trim_applied':False,'new_runner_emitted':False,'native_jobs_started':0,'gpu_jobs_started':0,'adopted':False,'manufacturing_ready':False,
            'limits':['Two bounded continuous signal samples on component0 have no compliant sourceconnected new-ground stitch region; not universal infeasibility','One other-end grounded return option does not constitute a whole signal route','100s/window; only2of7other-end samples processed under budget, no broad continuation','Code/data source read hashes recorded; no new at-run transitive nonstdlib-library closure claimed for negative host screens','All native/electrical/physical gates remain open for any future changed source; old measured198b native result is not transferred']}
destination.write_text(json.dumps(checkpoint,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'checkpoint':str(destination),'sha256':sha(destination),'verdict':checkpoint['verdict']}))
