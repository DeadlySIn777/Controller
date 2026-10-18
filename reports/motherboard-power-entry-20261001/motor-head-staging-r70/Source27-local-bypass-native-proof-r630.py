import sys,json,hashlib,shutil,subprocess,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
B=Path('reports/motherboard-power-entry-20261001/Source27-power-repair-native-proof-r616/motherboard-Source27-private-power-repair-candidate.kicad_pcb');A=Path('reports/motherboard-power-entry-20261001/Source27-two-RAW-bypass-barrel-repair-r628/motherboard-Source27-two-RAW-bypass-repair-candidate.kicad_pcb');ADD=Path('reports/motherboard-power-entry-20261001/Source27-C87-local-return-support-r626/actual-Cu.json');MOD=Path('reports/motherboard-power-entry-20261001/Source27-two-RAW-bypass-barrel-repair-r628/actual-Cu.json');OLD=Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r596/receipt.json');S=Path('reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/candidate/motherboard/design.json');H=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');BASE=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-local-bypass-native-proof-r630');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,A,ADD,MOD,OLD,S,H,BASE,Path(__file__)]};dest=O/'motherboard-Source27-local-bypass-candidate.kicad_pcb';shutil.copyfile(A,dest)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(A.with_suffix(e),dest.with_suffix(e))
for p in A.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
b0=pcbnew.LoadBoard(str(B));b0.BuildConnectivity();oldgroups=source_clusters(b0);b=pcbnew.LoadBoard(str(dest));print('FILL_START',flush=True);pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(dest),b);print('FILL_DONE',flush=True);b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity()
add=json.loads(ADD.read_text());mod=json.loads(MOD.read_text());oldcu={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert set(oldcu)<=set(newcu);assert set(newcu)-set(oldcu)=={x['uuid']for x in add['new_Cu']};assert{u for u in oldcu if oldcu[u]!=newcu[u]}=={x['uuid']for x in mod['exact_modified_Cu']};assert{p.m_Uuid.AsString():pad_identity(p)for p in b0.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
source_error=None
try:prior=clusters_preserved(oldgroups,b)
except Exception as e:prior=None;source_error=repr(e)
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};endpoints=[]
for row in json.loads(OLD.read_text())['actual_thirty_connected_new_endpoints']:
 a,c=ps[tuple(row['actual_endpoint'])],ps[tuple(row['target'])];ok=c.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(a)}|{a.m_Uuid.AsString()};endpoints.append(dict(**{k:v for k,v in row.items()if k!='passed'},passed=ok))
run=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;(O/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr);viol=json.loads((O/'drc.json').read_text())['violations']
spec=importlib.util.spec_from_file_location('frozen_power_guard',H);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.SOURCE=S.resolve()
try:power=m.review(pcbnew.LoadBoard(str(BASE)),b)
except Exception as e:power=dict(passed=False,rejection=repr(e))
assert all(sha(Path(p))==h for p,h in inputs.items());result=dict(passed=not source_error and not viol and all(q['passed']for q in endpoints),input_hashes=inputs,board_sha256=sha(dest),exact_new_Cu=add['new_Cu'],exact_modified_Cu=mod['exact_modified_Cu'],all_old_pads_identical=True,old_Source_clusters_preserved=prior,Source_error=source_error,thirty_endpoint_checks=endpoints,native_violations=viol,frozen_r07_power=power,Source27_promoted=False,manufacturing_ready=False);(O/'receipt.json').write_text(json.dumps(result,indent=2));print('NATIVE_LOCAL',result['passed'],len(viol),source_error,power.get('passed'),power.get('rejection'),flush=True)
