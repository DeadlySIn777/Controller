"""Adopt four reviewed, exact source26 routing transactions; never waive DRC."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_merge_bounded_pcb_delta import objects,without_generated_fills
from hardware_build_assembly import parse,dump
from hardware_route_owned_bypass_loops_wip_r03 import new_route_defects,warning_key

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def prepare_scope(before,donor,ids,out,reason):
    trees=[parse(without_generated_fills(p.read_text())) for p in (before,donor)]
    actual=set()
    for kind in ('segment','via','arc'):
        old,new=[objects(t,kind) for t in trees]
        if any(uid not in new or dump(new[uid])!=dump(v) for uid,v in old.items()):
            raise ValueError('Additive adoption changed prior copper')
        actual.update(set(new)-set(old))
    if actual!=set(ids):raise ValueError('Reviewed additive UUID scope differs')
    data=dict(electrical_source_unchanged=True,reviewed_scope_reason=reason,
      reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(actual),reviewed_added_zone_UUIDs=[])
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+'\n')
    return out

before=ROOT/'reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb'
ao=ROOT/'reports/motherboard-critical-routing-20261001/actual-AO0-source26-root56-r01'
freeze=json.loads((ao/'freeze-r05.json').read_text()); donor=ao/'imported-authoritative-r05/additive-route-candidate.kicad_pcb'
if not freeze['passed'] or digest(donor)!=freeze['board_sha256']:raise ValueError('AO0 freeze differs')
ao_scope=prepare_scope(before,donor,freeze['added_signal_copper_UUIDs'],ROOT/'reports/motherboard-pcb-integration-20261001/source26-AO0-scope-r57.json','Two reviewed actual AO0 PG-field signal traces; original source, lands, poses and all prior copper retained. Own native filled reference corridors checked independently.')
hf=ROOT/'reports/motherboard-owned-bypass-routing-20261001/source26-r56-first-batch-r04'
receipt=json.loads((hf/'receipt.json').read_text());hf_donor=hf/'owned-bypass-loop-candidate.kicad_pcb'
if digest(hf_donor)!=receipt['board_sha256'] or receipt['new_route_DRC_defects'] or not receipt['all_prior_native_source_pad_clusters_preserved']:raise ValueError('HF receipt not qualified')
ids=[u for row in receipt['owned_loops'] if row['retained'] for u in row['new_UUIDs']]
hf_scope=prepare_scope(before,hf_donor,ids,ROOT/'reports/motherboard-pcb-integration-20261001/source26-HF-scope-r60.json','94 retained actual capacitor-owner loops. Exact source pin pairs, receiving reference annuli, filled own supply-return corridors and all prior source-pad clusters checked. 221 rejected/remaining groups are not included; no current capacity or measured inductance claim.')
transactions=[
 ('source26-critical-AO0-r57',donor,ao_scope),
 ('source26-secondary-AO1-r58',ROOT/'reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r04/motherboard-AO1-secondary-return-candidate.kicad_pcb',ROOT/'reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r04/bounded-scope.json'),
 ('source26-return-bridges-r59',ROOT/'reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/motherboard-source26-return-bridges-candidate.kicad_pcb',ROOT/'reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/bounded-scope.json'),
 ('source26-owned-bypass-r60',hf_donor,hf_scope)]
target=before
baseline=ROOT/'reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/baseline-disposition.json'
known=set(map(warning_key,json.loads(baseline.read_text())['known_unresolved_native_warnings']))
for name,donor,scope in transactions:
    out=ROOT/'reports/motherboard-pcb-integration-20261001'/name
    if out.exists():
        previous=json.loads((out/'receipt.json').read_text())
        expected={str(p.resolve()):digest(p) for p in (before,donor,target,scope)}
        if previous['input_sha256']!=expected or digest(out/'motherboard-bounded-merged-candidate.kicad_pcb')!=previous['board_sha256']:raise ValueError('Existing exact merge receipt differs')
    else:
        result=subprocess.run([sys.executable,str(ROOT/'tools/hardware_merge_bounded_pcb_delta.py'),'--before',str(before),'--donor',str(donor),'--target',str(target),'--scope',str(scope),'--out',str(out)],cwd=ROOT,capture_output=True,text=True)
        (out/'merge-command.txt').write_text(result.stdout+result.stderr)
        if result.returncode:raise ValueError(name+' merge failed: '+result.stderr[-1600:])
    report=json.loads((out/'drc.json').read_text())
    defects=new_route_defects(report,known)
    if defects:
        (out/'new-defects.json').write_text(json.dumps(defects,indent=2)+'\n')
        raise ValueError(name+' introduced '+str(len(defects))+' native defects; unadopted')
    target=out/'motherboard-bounded-merged-candidate.kicad_pcb'
    disposition=dict(board_sha256=digest(target),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=report['violations'],ignored_checks=[])
    (out/'baseline-disposition.json').write_text(json.dumps(disposition,indent=2)+'\n')
    known=set(map(warning_key,report['violations']))
    print(name,json.loads((out/'receipt.json').read_text())['uncapped_missing_joins'],len(known),flush=True)
print('current',target,flush=True)
