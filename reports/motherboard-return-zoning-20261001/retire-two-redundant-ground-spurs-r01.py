"""Retire only two native-reported open-ended ground stubs.

Their owning C11076.2 and D17053.1 keep the existing complete actual ground
routes. No source, land, pose, other copper, zone or NC disposition changes.
"""
import sys,json,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_route_logic_return import identity
from hardware_populate_motherboard_pcb import sha,write
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path('reports/motherboard-return-zoning-20261001/source26-r81-two-redundant-ground-spurs-r01');OUT.mkdir(parents=True,exist_ok=False)
IDS={'70dd1c72-0fd9-4558-a66d-4e8ccc7a422e','7b44c836-5f95-44e0-9b0a-12f7fcbc6cd7'}
NODES=[('C11076','2','14848da6-5f91-4c7b-9c7a-63325bde1b26'),('D17053','1','c114bdc6-886d-471e-92b7-1824b9916585')]
frozen={str(p):sha(p)for p in(BASE,BASE.parent/'drc.json',Path(__file__))}
native=json.loads((BASE.parent/'drc.json').read_text());actual={item['uuid']for row in native['violations']if row['type']=='track_dangling'for item in row['items']}
assert actual==IDS
tree=e.parse(BASE.read_text());tracks={e.value(e.child(t,'uuid')[1]):t for t in e.children(tree,'segment')}
for uid in IDS:tree.remove(tracks[uid])
dest=OUT/'motherboard-retired-ground-spurs-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n',encoding='utf8')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for p in BASE.parent.iterdir():
 if p.is_dir()and p.suffix=='.pretty':shutil.copytree(p,OUT/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,OUT/p.name)
cmd=['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(OUT/'native.json'),str(dest)]
r=subprocess.run(cmd,capture_output=True,text=True);(OUT/'native-command.txt').write_text(r.stdout+r.stderr);assert r.returncode==0
d=json.loads((OUT/'native.json').read_text());assert not d['ignored_checks']and all(v['severity']=='warning'and v['type']=='isolated_copper'for v in d['violations'])
b=pcbnew.LoadBoard(str(BASE));fresh=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();fresh.BuildConnectivity()
old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};new={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
assert set(old)-set(new)==IDS and not(set(new)-set(old))and all(new[k]==v for k,v in old.items()if k not in IDS)
clusters=clusters_preserved(source_clusters(b),fresh);co=fresh.GetConnectivity();ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in fresh.GetPads()};cu={t.m_Uuid.AsString():t for t in fresh.GetTracks()};checks=[]
for ref,pin,via_uid in NODES:
 p=ps[ref,pin];v=cu[via_uid];assert p.GetNetname()==v.GetNetname()=='/motherboard_do/FIELD_B_0V'
 assert p.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(v)}
 layers=[fresh.GetLayerName(l)for l in(pcbnew.In1_Cu,pcbnew.In4_Cu)if physical_reference_contact(v,l,co)]
 assert 'In1.Cu'in layers
 checks.append(dict(ref=ref,pin=pin,actual_retained_via=via_uid,actual_flashed_native_reference_contacts=layers,actual_source_pad_joined=True))
assert all(sha(Path(p))==h for p,h in frozen.items())
write(OUT/'receipt.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),removed_exact_obsolete_Cu=sorted(IDS),retained_actual_ground_routes=checks,all_prior_SOURCE_clusters=clusters,native_errors=0,native_warnings=d['violations'],ignored_checks=[],uncapped_native_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),source_or_other_copper_or_zone_mutation=False,manufacturing_ready=False))
write(OUT/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(IDS),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Retire exactly two native-reported redundant open-ended ground stubs. C11076.2 and D17053.1 retain actual own-domain Source return vias and In1 contacts; all previous SOURCE clusters and every other Cu/pose/land/zone remain. No suppression or NC waiver.',review_evidence_sha256={str(q):sha(q)for q in(OUT/'receipt.json',OUT/'native.json',Path(__file__))}))
print(json.dumps(dict(passed=True,removed=2,native_errors=0,native_warnings=len(d['violations']),missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False))))
