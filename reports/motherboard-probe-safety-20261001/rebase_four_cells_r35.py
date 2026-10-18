"""Rebase the proved41 poses onto root's independently native-clean r35."""
from pathlib import Path
import collections,copy,hashlib,json,shutil,subprocess,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,dump,child,children,value
from hardware_route_logic_return import identity
from hardware_merge_bounded_pcb_delta import reference,objects,zone_definition,pad_nets
from hardware_retire_owned_capacitor_leaves import observer_clusters
from hardware_review_motherboard_probe_safety import check
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=ROOT/'reports/motherboard-pcb-integration-20261001/source24-probe-pins-r34/probe-source-reconciled-candidate.kicad_pcb'
donor=REPORT/'four-cell-placement-r04/motherboard-probe-safety-cells-candidate.kicad_pcb'
target=ROOT/'reports/motherboard-pcb-integration-20261001/source24-native-clean-r35/native-dangling-cleared-candidate.kicad_pcb'
scope_path=REPORT/'four-cell-placement-r04/merge-scope.json';scope=json.loads(scope_path.read_text())
allowed=set(scope['reviewed_footprint_references']);assert len(allowed)==41
out=REPORT/'four-cell-placement-native-clean-r05';assert not out.exists();out.mkdir()
trees={k:parse(p.read_text())for k,p in [('before',before),('donor',donor),('target',target)]}
fp={k:{reference(f):f for f in children(t,'footprint')}for k,t in trees.items()}
assert set(fp['before'])==set(fp['donor'])==set(fp['target'])
for ref in allowed:
    assert dump(fp['before'][ref])==dump(fp['target'][ref]),ref
    idx=trees['target'].index(fp['target'][ref]);trees['target'][idx]=copy.deepcopy(fp['donor'][ref])
retired=set(scope['reviewed_copper_delta_UUIDs']);already_retired=set();remaining=set()
for kind in ('segment','via','arc'):
    old=objects(trees['before'],kind);now=objects(trees['target'],kind)
    for uid,v in now.items():assert uid in old and dump(v)==dump(old[uid]),uid
    for uid in retired&set(old):
        if uid in now:trees['target'].remove(now[uid]);remaining.add(uid)
        else:already_retired.add(uid)
    for uid,v in old.items():
        if uid not in now and uid not in retired:already_retired.add(uid)
assert remaining|already_retired>=retired
# Root's17 prior retirements must be all that differs from the frozen donor
# base. They are not new board edits credited to this41-cell transaction.
root_removed={uid for kind in ('segment','via','arc')for uid in
    set(objects(trees['before'],kind))-set(objects(parse(target.read_text()),kind))}
assert len(root_removed)==17
for old in children(trees['before'],'zone'):
    uid=value(child(old,'uuid')[1]);now=next(z for z in children(trees['target'],'zone')if value(child(z,'uuid')[1])==uid)
    assert zone_definition(old)==zone_definition(now)
dest=out/'motherboard-probe-safety-cells-native-clean-candidate.kicad_pcb'
dest.write_text(dump(trees['target'])+'\n')
for p in target.parent.iterdir():
    if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
    elif p.name=='fp-lib-table':shutil.copyfile(p,out/p.name)
for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(target.with_suffix(suffix),dest.with_suffix(suffix))
initial=pcbnew.LoadBoard(str(target));initial.BuildConnectivity()
nets={str(p.GetNetname())for f in initial.GetFootprints()if f.GetReference()in allowed for p in f.Pads()if p.GetNumber()}
clusters=observer_clusters(initial,allowed,nets)
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)]
run=subprocess.run(cmd,capture_output=True,text=True);(out/'native-drc-command.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
drc=json.loads((out/'drc.json').read_text());assert not drc['ignored_checks']and not drc['violations'],drc['violations']
final=pcbnew.LoadBoard(str(dest));final.BuildConnectivity()
assert observer_clusters(final,allowed,nets)==clusters
old_tracks={t.m_Uuid.AsString():identity(t)for t in initial.GetTracks()};new_tracks={t.m_Uuid.AsString():identity(t)for t in final.GetTracks()}
assert set(old_tracks)-set(new_tracks)==remaining
assert all(new_tracks.get(uid)==v for uid,v in old_tracks.items()if uid not in remaining)
old_fp={f.GetReference():f for f in initial.GetFootprints()};new_fp={f.GetReference():f for f in final.GetFootprints()}
for ref,f in old_fp.items():
    new=new_fp[ref];assert pad_nets(f)==pad_nets(new),ref
    if ref not in allowed:
        assert tuple(f.GetPosition())==tuple(new.GetPosition())and f.GetLayer()==new.GetLayer()and f.GetOrientationDegrees()==new.GetOrientationDegrees(),ref
independent=check(final);assert independent['ok'],independent
(out/'independent-layout-review.json').write_text(json.dumps(independent,indent=2)+'\n')
newscope={**scope,'reviewed_removed_copper_UUIDs':sorted(remaining),'reviewed_copper_delta_UUIDs':sorted(remaining)}
(out/'merge-scope.json').write_text(json.dumps(newscope,indent=2)+'\n')
prior=json.loads((REPORT/'four-cell-placement-r04/receipt.json').read_text())
receipt={**prior,'input_board':str(target),'input_board_SHA256':sha(target),'board_SHA256':sha(dest),
    'track_via_items':len(new_tracks),'uncapped_missing_joins':final.GetConnectivity().GetUnconnectedCount(False),
    'baseline_native_DRC_regular':0,'candidate_native_DRC_regular':0,'new_native_DRC_regular':0,
    'source_23_probe_two_pad_reconciliation_pending':False,
    'exact_old_copper_removed':[dict(UUID=uid,before=old_tracks[uid])for uid in sorted(remaining)],
    'prior_donor_retirement_count':len(retired),'root_prior17_retirements_overlapping_donor':sorted(root_removed&retired),
    'root_prior17_total':len(root_removed),'all_target_r35_other_copper_and_unmoved_pad_clusters_preserved':True,
    'independent_topology_and_local_geometry_pass':True,
    'source_snapshot':'reports/motherboard-integration-20260930/r24-2688-probe-topology-staged',
    'input_hashes':{str(p.relative_to(ROOT)):sha(p)for p in [before,donor,target,scope_path,Path(__file__)]},
    'scope':'Exactly41 source24-correct probe/safety poses plus remaining proven local/causal leaf retirement rebased onto native-clean r35. NativeDRC0,independent source topology/local spacing pass. Local input/bypass routing and actual return-plane continuity remain unfinished; no physicalEMC/timing qualification.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k]for k in ['physical_parts','track_via_items','uncapped_missing_joins','candidate_native_DRC_regular']}))
