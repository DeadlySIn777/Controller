"""Reconcile exactly two reference identities and three manufacturer fuse lands.

All native source pin numbers/nets/UUIDs, original copper, poses, zone rules,
and other footprint objects remain invariant. This is a bounded necessary
source/PCB reconciliation before separate fuse service movement/global routing.
"""
import argparse,collections,copy,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value,q
from hardware_populate_motherboard_pcb import sha,write,pad_template,footprint_name,native_parts_and_nets,load_exact_footprint
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills,zone_definition
from hardware_apply_fuse_geometry_upgrade import patch_native_tree,REFS as FUSES,OLD,NEW
from hardware_anchor_owned_cmos_returns import source_clusters
from hardware_route_logic_return import identity

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
CAPS={'C14741','C14743'};ALL=CAPS|FUSES
def ref(f):return value(next(p[2]for p in children(f,'property')if value(p[1])=='Reference'))
def pad_data(board):
 return {p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),pad_template(p),tuple(p.GetPosition()))for p in board.GetPads()}
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('board','adoption','source','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable source/PCB transaction required')
 adoption=json.loads(a.adoption.read_text());model=json.loads((a.source/'design.json').read_text());parts=model['components']
 rows={r['reference']:r for r in adoption['exact_component_changes']}
 if not adoption['passed']or not adoption['adopted']or set(rows)!=ALL or not adoption['all_native_pin_nets_preserved']:raise ValueError('Exact adopted five-part qualification source required')
 for name,h in adoption['source_hashes'].items():
  if sha(a.source/name)!=h:raise ValueError('Current adopted parent changed '+name)
 frozen={str(p.resolve()):sha(p)for p in(a.board,a.adoption,a.source/'design.json',a.source/'netlist.xml',Path(__file__),Path(__file__).parent/'hardware_apply_fuse_geometry_upgrade.py')}
 native,nodes=native_parts_and_nets(a.source/'netlist.xml',parts)
 b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
 old_values={r:f.GetValue()for r,f in fps.items()}
 # Original baseline footprints use the exact fitted MPN as their display
 # value. This bounded five-part transaction must retain all other literal
 # values; unrelated stale descriptors are reported for separate correction.
 prior_value_discrepancies=[dict(reference=r,actual_display_value=f.GetValue(),source_display_value=parts[r]['value'],source_mpn=parts[r]['mpn'],classification='exact_source_MPN_display'if f.GetValue()==parts[r]['mpn']else'stale_display_requires_separate_reconciliation')for r,f in fps.items()if r not in ALL and f.GetValue()!=parts[r]['value']]
 if set(fps)!=set(parts):raise ValueError('Actual complete source population differs')
 for r,f in fps.items():
  for p in f.Pads():
   if p.GetNumber()and p.IsOnCopperLayer()and p.GetNetname()!=nodes[r,p.GetNumber()]:raise ValueError('Exact source/native pin-net differs')
  wanted=rows[r]['before']['footprint']if r in ALL else parts[r]['footprint']
  if footprint_name(f)!=wanted:raise ValueError('Actual old source footprint differs '+r)
 oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads=pad_data(b);clusters=source_clusters(b)
 poses={r:(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())for r,f in fps.items()}
 tree=parse(without_generated_fills(a.board.read_text()));raw={ref(f):f for f in children(tree,'footprint')};oldraw={r:dump(f)for r,f in raw.items()}
 zone_before={value(child(z,'uuid')[1]):zone_definition(z)for z in children(tree,'zone')}
 for r in ALL:
  if fps[r].GetValue()!=rows[r]['before']['value']:raise ValueError('Old exact fitted value differs '+r)
  if parts[r]!=rows[r]['after']:raise ValueError('Actual adopted component differs '+r)
 tree=patch_native_tree(tree);newraw={ref(f):f for f in children(tree,'footprint')}
 for r in CAPS:
  before=rows[r]['before'];after=rows[r]['after']
  if (before['mpn'],after['mpn'],after['footprint'])!=('GRM188R71H105KA12D','GRM188R71E105KA12D','Capacitor_SMD:C_0603_1608Metric'):raise ValueError('Unexpected reference identity/land delta')
  for p in children(newraw[r],'property'):
   if value(p[1])=='Value':p[2]=q(after['value'])
   elif value(p[1])=='MPN':p[2]=q(after['mpn'])
 if {r for r in raw if oldraw[r]!=dump(newraw[r])}!=ALL:raise ValueError('Other raw footprint changed')
 a.out.mkdir(parents=True);dest=a.out/'motherboard-source26-reconciled-candidate.kicad_pcb'
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
 for p in a.board.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
  elif p.name=='fp-lib-table':shutil.copyfile(p,a.out/p.name)
 source_lib=a.source/'CNC_MB_Fuse.pretty';new_lib=a.out/source_lib.name
 if new_lib.exists():raise ValueError('Unexpected pre-existing fuse library')
 shutil.copytree(source_lib,new_lib)
 lookup=parse((a.out/'fp-lib-table').read_text());actual_table=parse((a.source/'fp-lib-table').read_text())
 own=next(lib for lib in children(actual_table,'lib')if value(child(lib,'name')[1])=='CNC_MB_Fuse')
 if any(value(child(lib,'name')[1])=='CNC_MB_Fuse'for lib in children(lookup,'lib')):raise ValueError('Unreviewed existing project fuse lookup')
 lookup.append(copy.deepcopy(own));(a.out/'fp-lib-table').write_text(dump(lookup)+'\n');dest.write_text(dump_board(tree))
 run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True)
 (a.out/'drc.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native DRC failed to execute')
 report=json.loads((a.out/'drc.json').read_text())
 if report.get('ignored_checks')or any(v['severity']=='error'for v in report['violations']):raise ValueError('Native source reconciliation has errors or ignored checks')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();nf={f.GetReference():f for f in fresh.GetFootprints()};np=pad_data(fresh);cu={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
 if oldcu!=cu:raise ValueError('Any original copper changed/reassigned')
 if set(np)!=set(oldpads)or any(np[u][:3]!=v[:3]for u,v in oldpads.items()):raise ValueError('Source pad UUID/number/net inventory changed')
 if any(np[u]!=v for u,v in oldpads.items()if v[0]not in FUSES):raise ValueError('Unrelated manufacturer land/pose changed')
 for r,f in nf.items():
  wanted_value=parts[r]['value']if r in ALL else old_values[r]
  if poses[r]!=(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())or footprint_name(f)!=parts[r]['footprint']or f.GetValue()!=wanted_value:raise ValueError('Actual current source pose/foot/bounded-value differs '+r)
 for r in FUSES:
  master,file=load_exact_footprint(NEW,a.source,dest);master.SetOrientationDegrees(nf[r].GetOrientationDegrees())
  if nf[r].GetLayer()!=master.GetLayer():master.Flip(master.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
  if collections.Counter(pad_template(p)for p in master.Pads())!=collections.Counter(pad_template(p)for p in nf[r].Pads()):raise ValueError('Actual fuse manufacturer copper/drill/land template differs')
 raw_final={ref(f):f for f in children(parse(without_generated_fills(dest.read_text())),'footprint')}
 if any(dump(raw_final[r])!=v for r,v in oldraw.items()if r not in ALL):raise ValueError('Other actual raw footprint changed')
 final_tree=parse(without_generated_fills(dest.read_text()));zone_after={value(child(z,'uuid')[1]):zone_definition(z)for z in children(final_tree,'zone')}
 if zone_before!=zone_after:raise ValueError('Actual zone definition changed')
 byu={p.m_Uuid.AsString():p for p in fresh.GetPads()}
 for group in clusters:
  p=byu[next(iter(group))];actual={v.m_Uuid.AsString()for v in fresh.GetConnectivity().GetConnectedItems(p)if isinstance(v,pcbnew.PAD)}|{p.m_Uuid.AsString()}
  if not group<=actual:raise ValueError('Prior source-pad cluster fragmented')
 if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Source/PCB input changed during bounded reconciliation')
 result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_changed_references=sorted(ALL),source_parts=len(nf),all_other_literal_display_values_preserved=True,preexisting_display_value_discrepancies=prior_value_discrepancies,all_old_copper_preserved=True,all_prior_source_pad_clusters_preserved=True,all_native_pad_UUIDs_numbers_nets_preserved=True,all_original_poses_preserved=True,manufacturer_fuse_lands_exact=True,all_zone_definitions_preserved=True,native_DRC_types=dict(collections.Counter(v['type']for v in report['violations'])),native_errors=0,ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,physical_qualification=False)
 write(a.out/'receipt.json',result);print({k:result[k]for k in('passed','exact_changed_references','board_sha256','native_DRC_types','uncapped_missing_joins')})

if __name__=='__main__':main()
