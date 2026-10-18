"""Retire one duplicate drill object, retaining its identical physical barrel."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
base=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-supply-merged-trial-r91/motherboard-bounded-merged-candidate.kicad_pcb')
assert sha(base)=='c05bacd720a1c008f5195e40211415a2053d51a9abc36af9ff4005186001ec72'
out=base.parent.parent/'source26-BankA-health-duplicate-via-repair-r92';out.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();clusters=source_clusters(b)
cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
old={u:identity(t)for u,t in cu.items()};pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
remove='00ab4e38-02eb-4059-9a89-1b617985437c';keep='864617ea-0ed9-4c88-b0bb-1017d6e7da65'
v,w=cu[remove],cu[keep]
assert v.Type()==w.Type()==pcbnew.PCB_VIA_T
assert identity(v)[1:]==identity(w)[1:]
assert v.GetNetname()=='/motherboard_power_entry/FIELD_5V'
assert v.GetLayerSet().FmtBin()==w.GetLayerSet().FmtBin()
assert v.GetViaType()==w.GetViaType()
contacts=[b.GetLayerName(l)for l in b.GetEnabledLayers().CuStack()if physical_reference_contact(w,l,b.GetConnectivity())]
b.Remove(v)
assert {t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}=={u:d for u,d in old.items()if u!=remove}
assert pads=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
dest=out/base.name;pcbnew.SaveBoard(str(dest),b)
for ext in('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(ext),dest.with_suffix(ext))
for f in base.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
write(out/'proposed-exact-delta.json',dict(before_sha256=sha(base),removed_UUID=remove,retained_UUID=keep,identical_native_barrel_geometry=old[keep][1:],actual_old_filled_contacts=contacts,scope='Duplicate drill identity retirement; no physical barrel removed. Current Source paths and health receiving-loop proof still required.',manufacturing_ready=False))
with(out/'drc-command.txt').open('w')as log:
 r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--all-track-errors','--severity-all','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity()
current={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
assert current=={u:d for u,d in old.items()if u!=remove}
assert pads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
retained=next(t for t in after.GetTracks()if t.m_Uuid.AsString()==keep)
assert all(physical_reference_contact(retained,after.GetLayerID(l),after.GetConnectivity())for l in contacts)
prior=clusters_preserved(clusters,after)
drc=json.loads((out/'drc.json').read_text());assert not drc['violations']and not drc['ignored_checks']
write(out/'receipt.json',dict(passed=True,board_sha256=sha(dest),before_sha256=sha(base),removed_exact_duplicate_UUID=remove,identical_retained_barrel_UUID=keep,retained_geometry=identity(retained),actual_contacts_preserved=contacts,prior_SOURCE_clusters=prior,all_other_Cu_pads_and_poses_preserved=True,native_errors=0,native_warnings=0,ignored_checks=[],track_via_count=len(after.GetTracks()),manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(dest),native_violations=0)))
