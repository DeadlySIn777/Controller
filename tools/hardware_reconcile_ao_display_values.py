"""Correct only the two stale AO rail-divider display fields.

The fitted source has already been corrected to TNPW0603267KBEEA. No
electrical/component/land/pin/pose/copper change is permitted here; original
baseline footprints displaying their exact source MPN remain unchanged.
"""
import argparse,collections,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,children,value,q,dump,child
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills,zone_definition
from hardware_populate_motherboard_pcb import sha,native_parts_and_nets,footprint_name,write
from hardware_route_logic_return import identity
from hardware_reconcile_motherboard_peripheral_pcb import piece

REFS={'R14602','R14626'}
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def ref(f):return next(value(p[2])for p in children(f,'property')if value(p[1])=='Reference')
def check_values(components,values):
 for r in REFS:
  c=components[r]
  if (c['mpn'],c['value'],c['footprint'])!=('TNPW0603267KBEEA','267000R0.1%','Resistor_SMD:R_0603_1608Metric')or values[r]!='274000R0.1%':raise ValueError('Exact old descriptor/current corrected source required '+r)
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('board','source','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 model=json.loads((a.source/'design.json').read_text());parts=model['components']
 frozen={str(p.resolve()):sha(p)for p in (a.board,a.source/'design.json',a.source/'netlist.xml',Path(__file__))}
 b=pcbnew.LoadBoard(str(a.board.resolve()));fps={f.GetReference():f for f in b.GetFootprints()};old_values={r:f.GetValue()for r,f in fps.items()};check_values(parts,old_values)
 _,nodes=native_parts_and_nets(a.source/'netlist.xml',parts)
 if set(parts)!=set(fps):raise ValueError('Full source population mismatch')
 oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={p.m_Uuid.AsString():piece(p)for p in b.GetPads()}
 tree=parse(without_generated_fills(a.board.read_text()));oldraw={ref(f):dump(f)for f in children(tree,'footprint')};zones={value(child(z,'uuid')[1]):zone_definition(z)for z in children(tree,'zone')}
 for f in children(tree,'footprint'):
  if ref(f)in REFS:
   for p in children(f,'property'):
    if value(p[1])=='Value':p[2]=q(parts[ref(f)]['value'])
 if {ref(f)for f in children(tree,'footprint')if dump(f)!=oldraw[ref(f)]}!=REFS:raise ValueError('Unrelated raw footprint delta')
 a.out.mkdir(parents=True);dest=a.out/'motherboard-ao-display-reconciled-candidate.kicad_pcb'
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
 for p in a.board.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
  elif p.name=='fp-lib-table':shutil.copyfile(p,a.out/p.name)
 dest.write_text(dump_board(tree))
 run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True)
 (a.out/'drc.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native DRC did not execute')
 drc=json.loads((a.out/'drc.json').read_text())
 if drc.get('ignored_checks')or any(v['severity']=='error'for v in drc['violations']):raise ValueError('New native error/ignored check')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();nf={f.GetReference():f for f in fresh.GetFootprints()}
 if {t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}!=oldcu or {p.m_Uuid.AsString():piece(p)for p in fresh.GetPads()}!=pads:raise ValueError('Actual copper/land/pin/pose changed')
 for r,f in nf.items():
  if footprint_name(f)!=parts[r]['footprint']or f.GetValue()!=(parts[r]['value']if r in REFS else old_values[r]):raise ValueError('Actual current exact footprint or display delta differs '+r)
  for p in f.Pads():
   if p.GetNumber()and p.IsOnCopperLayer()and p.GetNetname()!=nodes[r,p.GetNumber()]:raise ValueError('Exact source/native pin-net mismatch')
 final=parse(without_generated_fills(dest.read_text()));raw={ref(f):f for f in children(final,'footprint')}
 if any(dump(raw[r])!=v for r,v in oldraw.items()if r not in REFS):raise ValueError('Unrelated raw footprint changed')
 for r in REFS:
  reverse=parse(dump(raw[r]));next(p for p in children(reverse,'property')if value(p[1])=='Value')[2]=q(old_values[r])
  if dump(reverse)!=oldraw[r]:raise ValueError('Other property of corrected footprint changed')
 if {value(child(z,'uuid')[1]):zone_definition(z)for z in children(final,'zone')}!=zones:raise ValueError('Zone rule/outline changed')
 if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen input changed')
 result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),source_parts=len(nf),exact_display_changes=[dict(reference=r,old_display=old_values[r],current_display=parts[r]['value'],unchanged_fitted_MPN=parts[r]['mpn'])for r in sorted(REFS)],electrical_source_unchanged=True,all_actual_pads_poses_and_copper_unchanged=True,all_other_raw_footprints_and_zone_definitions_unchanged=True,native_DRC_types=dict(collections.Counter(v['type']for v in drc['violations'])),native_errors=0,ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
 write(a.out/'receipt.json',result);print({k:result[k]for k in('passed','exact_display_changes','board_sha256','uncapped_missing_joins')})
if __name__=='__main__':main()
