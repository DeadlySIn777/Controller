"""Verify a complete same-side bypass on exact fresh native copper/map.

Separate adjacent-plane proof supplements, never relaxes, the old 101 loops.
The negative control physically removes its one new supply trace in memory.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity
from check_same_side_bypass_r02 import check_group
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--map',type=Path,required=True);ap.add_argument('--drc',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
donor_dir=Path(__file__).parent/'source26-r79-adjacent-same-side-r01';donor=donor_dir/'owned-bypass-loop-candidate.kicad_pcb';receipt=donor_dir/'receipt.json'
owners=ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
read=lambda p:json.loads(p.read_text())
paths=[a.board,a.map,a.drc,donor,receipt,owners,Path(__file__),Path(__file__).parent/'check_same_side_bypass_r01.py',Path(__file__).parent/'check_same_side_bypass_r02.py']
frozen={str(p.resolve()):sha(p)for p in paths};m=read(a.map);r=read(receipt);drc=read(a.drc)
assert m['input_sha256'][str(a.board.resolve())]==sha(a.board)
assert r['board_sha256']==sha(donor) and not r['new_route_DRC_defects']
assert not drc['ignored_checks'] and all(v['severity']=='warning'for v in drc['violations'])
groups=[g for g in r['owned_loops']if g['retained']];assert len(groups)==1 and groups[0]['ref']=='C14804';g=groups[0]
assert g['new_UUIDs']==['55913ac8-56df-4d99-9550-f80788fa193d']
row=next(x for x in read(owners)['capacitors']if x['ref']=='C14804')
b=pcbnew.LoadBoard(str(a.board));db=pcbnew.LoadBoard(str(donor))
actual={t.m_Uuid.AsString():t for t in b.GetTracks()};original={t.m_Uuid.AsString():t for t in db.GetTracks()}
assert all(identity(actual[u])==identity(original[u])for u in g['new_UUIDs'])
positive=check_group(b,g,row,m)
cut=pcbnew.LoadBoard(str(a.board));alive=list(cut.GetTracks());cu={t.m_Uuid.AsString():t for t in alive}
for u in g['new_UUIDs']:cut.Remove(cu[u])
cut.BuildConnectivity();rejected=False
try:check_group(cut,g,row,m)
except (ValueError,AssertionError,KeyError) as ex:rejected=True;reason=str(ex)
assert rejected,'Real missing supply copper was accepted'
assert all(sha(Path(p))==v for p,v in frozen.items())
write(a.out,dict(passed=True,input_sha256=frozen,board_sha256=sha(a.board),map_sha256=sha(a.map),exact_actual_C14804_adjacent_only_proof=positive,negative_actual_supply_copper_cut_rejected=rejected,negative_reason=reason,old_101_checks_unchanged_and_separately_required=True,physical_power_or_impedance_qualification=False,manufacturing_ready=False))
print('Actual C14804 same-side SOURCE/native proof and physical cut passed')
