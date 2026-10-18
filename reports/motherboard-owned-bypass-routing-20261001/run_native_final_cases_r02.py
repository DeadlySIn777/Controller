"""Rerun receiving-loop fixtures plus actual ADC no-via generic-route guard."""
from pathlib import Path
import subprocess,json,hashlib,sys,shutil
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_logic_return import identity
from hardware_populate_motherboard_pcb import pad_template
tool=ROOT/'tools/hardware_route_owned_bypass_loops.py'
fixture=Path(__file__).parent/'native-fixture-r08'
out=Path(__file__).parent/'native-final-proof-r02';out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];frozen={str(p):sha(p)for p in(tool,ROOT/'tools/hardware_check_return_corridors.py',ROOT/'tools/hardware_route_local_signals.py',Path(__file__))}
adc=out/'adc_guard_input';adc.mkdir()
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(fixture/'top'/('fixture'+suffix),adc/('fixture'+suffix))
b=pcbnew.LoadBoard(str(fixture/'top/fixture.kicad_pcb'))
next(f for f in b.GetFootprints()if f.GetReference()=='C1').SetReference('C14744')
pcbnew.SaveBoard(str(adc/'fixture.kicad_pcb'),b)
d=json.loads((fixture/'top/owners.json').read_text());d['capacitors'][0]['ref']='C14744';d['capacitors'][0]['category']='HF_supply_bypass'
(adc/'owners.json').write_text(json.dumps(d,indent=2)+'\n')
for case in('top','bottom','missing_reference','wrong_owner','reference_slot','adc_no_via_guard'):
 origin=adc if case=='adc_no_via_guard'else fixture/case
 source=origin/'fixture.kicad_pcb';owners=origin/'owners.json';dest=out/case
 frozen.update({str(p):sha(p)for p in(source,owners)})
 r=subprocess.run([sys.executable,str(tool),'--board',str(source),'--owners',str(owners),'--out',str(dest)],capture_output=True,text=True)
 (out/(case+'-log.txt')).write_text(r.stdout+r.stderr)
 if case=='wrong_owner':
  assert r.returncode!=0 and 'Exact owner physical nets differ C1' in r.stderr
  checks.append(dict(case=case,wrong_native_owner_pin_rejected=True));continue
 assert r.returncode==0,r.stdout+r.stderr
 receipt=json.loads((dest/'receipt.json').read_text());before=pcbnew.LoadBoard(str(source));after=pcbnew.LoadBoard(str(dest/'owned-bypass-loop-candidate.kicad_pcb'))
 old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};new={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
 assert all(new[u]==v for u,v in old.items())
 lands=lambda board:{p.m_Uuid.AsString():(p.GetNetname(),pad_template(p),tuple(p.GetPosition()))for p in board.GetPads()}
 assert lands(before)==lands(after)
 if case in('top','bottom'):
  assert sum(v['retained']for v in receipt['owned_loops'])==1 and not receipt['required_remaining']
  assert receipt['uncapped_missing_joins']==0 and receipt['native_DRC_regular']==0
  assert len(receipt['actual_filled_supply_branch_return_reviews'])==1
  if case=='bottom':
   vias=[v for v in receipt['actual_filled_supply_branch_return_reviews'][0]['items']if 'return_stitches' in v]
   assert len(vias)==1 and set(vias[0]['intended_reference_layers'])=={'In1.Cu','In4.Cu'}
   assert vias[0]['return_stitches']and all(v['distance_mm']<=1 and v['source_pad_anchors']for v in vias[0]['return_stitches'])
 else:
  assert not any(v['retained']for v in receipt['owned_loops'])and len(receipt['required_remaining'])==1
  assert receipt['uncapped_missing_joins']==2 and new==old
  if case=='reference_slot':assert 'unqualified reference boundary, slot or hole' in receipt['actual_return_corridor_rejections'][0]['reason']
  if case=='adc_no_via_guard':
   assert receipt['required_remaining'][0]['ref']=='C14744'
   assert 'dedicated same-side direct no-via' in receipt['required_remaining'][0]['reason']
   assert not receipt['owned_loops'] and receipt['native_DRC_regular']==0
 checks.append(dict(case=case,native_DRC_regular=receipt['native_DRC_regular'],actual_uncapped_missing_joins=receipt['uncapped_missing_joins'],all_retained_native_lands_pins_and_copper_verified=True,receipt_sha256=sha(dest/'receipt.json')))
assert all(sha(Path(p))==v for p,v in frozen.items())
(out/'review.json').write_text(json.dumps(dict(passed=True,native_cases=checks,checks_count=len(checks),frozen_inputs=frozen,test_only_fixtures=True,whole_controller_routing_or_physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(dict(passed=True,actual_native_cases=len(checks),top_bottom_own_loops_and_physical_stitches_pass=True,wrong_owner_missing_reference_reference_slot_rejected=True,ADC_mandatory_no_via_generic_exclusion_proven=True))
