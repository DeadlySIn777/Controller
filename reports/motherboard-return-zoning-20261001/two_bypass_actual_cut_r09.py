"""Actual persisted conductor cuts for the two same-side Source bypass loops."""
from pathlib import Path
import sys,json,math,argparse,shutil
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
ap=argparse.ArgumentParser();ap.add_argument('--ref',choices=['C13006','C13007']);ap.add_argument('--case',choices=['VCC_branch','cap_return_branch','Ground_barrel']);ap.add_argument('--reload',type=Path);a=ap.parse_args()
p=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06')
baseline=p/'motherboard-two-same-side-bypass-candidate.kicad_pcb'
assert sha(baseline)=='769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5'
receipt=json.loads((p/'current108-bypass-manifest.json').read_text())
owners=json.loads(Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json').read_text())
if a.reload:
 dest=a.reload;meta=json.loads(dest.with_suffix('.mutation.json').read_text());ref=meta['ref'];case=meta['case'];uid=meta['removed_UUID'];assert sha(dest)==meta['board_sha256']
else:
 ref=a.ref;case=a.case;dest=p/f'actual-cut-{ref}-{case}.kicad_pcb';assert not dest.exists()
row=next(r for r in owners['capacitors']if r['ref']==ref)
group=next(g for g in receipt['owned_loops']if g['ref']==ref)
b=pcbnew.LoadBoard(str(dest if a.reload else baseline));b.BuildConnectivity()
pads={(f.GetReference(),q.GetNumber()):q for f in b.GetFootprints()for q in f.Pads()if q.GetNumber()}
cp=pads[ref,row['cap_power']];cr=pads[ref,row['cap_return']]
power=[pads[r['ref'],r['pin']]for r in row['power_nodes']];returns=[pads[r['ref'],r['pin']]for r in row['return_nodes']]
def connected(x,y):return y.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(x)}
cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
if not a.reload:
 assert all(connected(cp,q)for q in power)and all(connected(cr,q)for q in returns)
 candidates=[cu[u]for u in group['new_UUIDs']]
 if case=='VCC_branch':target=next(t for t in candidates if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname()==cp.GetNetname())
 elif case=='cap_return_branch':target=next(t for t in candidates if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname()==cr.GetNetname())
 else:target=next(t for t in candidates if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()==cr.GetNetname())
 uid=target.m_Uuid.AsString();b.Remove(target);b.BuildConnectivity()
 # Regenerate physical pours after each actual deletion before persisting.
 filler=pcbnew.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity()
 for ext in('.kicad_pro','.kicad_dru'):shutil.copyfile(baseline.with_suffix(ext),dest.with_suffix(ext))
 pcbnew.SaveBoard(str(dest),b)
 write(dest.with_suffix('.mutation.json'),dict(ref=ref,case=case,removed_UUID=uid,board_sha256=sha(dest),before_sha256=sha(baseline),native_zones_refilled=True))
assert uid not in{t.m_Uuid.AsString()for t in b.GetTracks()}
assert set(group['new_UUIDs'])-{t.m_Uuid.AsString()for t in b.GetTracks()}=={uid}
if case=='VCC_branch':assert all(not connected(cp,q)for q in power),'Actual supply cut failed to disconnect Source pads'
else:assert all(not connected(cr,q)for q in returns),'Actual return cut failed to disconnect Source pads'
write(dest.with_suffix('.fresh-review.json'if a.reload else'.review.json'),dict(passed=True,ref=ref,case=case,board_sha256=sha(dest),removed_actual_UUID=uid,fresh_native_reload=a.reload is not None,all_actual_owner_Source_endpoints_disconnected=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,ref=ref,case=case,fresh_reload=a.reload is not None)),flush=True)
