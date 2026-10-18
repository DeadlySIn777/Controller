"""Actual-annulus checker with exact sequential nonempty native fill collection.

The frozen geometric/annulus guards are inherited unchanged. Only empty native
fill lists are skipped; native BooleanAdd order and final Simplify stay exact.
No Append/Simplify union approximation or outline-only reference is accepted.
"""
from pathlib import Path
import hashlib
import pcbnew
import hardware_check_return_corridors_r02 as strict
import hardware_collect_native_reference_fills as collector
FROZEN_STRICT_SHA='3496b5598390833c3cf71fd8dade26817a28ca1a7b208bba6af80fd1a0e00682'
COLLECTOR_SHA='4cf2044f88d0d0f443260fcbcb87fc1184fe0f73d89adc581c34c2413ed112bd'
def dependencies():
 for p,h in [(Path(strict.__file__),FROZEN_STRICT_SHA),(Path(collector.__file__),COLLECTOR_SHA)]:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('Frozen native return dependency changed:'+str(p))
 return dict(strict_actual_annulus_checker_sha256=FROZEN_STRICT_SHA,native_nonempty_fill_collector_sha256=COLLECTOR_SHA)
class NativeCollectedAnnulusCheck(strict.ActualAnnulusReturnCheck):
 def reference(self,net,layer):
  key=net,layer
  if key not in self.fills:
   union=collector.collect_native_reference_fills(self.board,{net},{layer}).get(key,pcbnew.SHAPE_POLY_SET())
   union.Simplify();self.fills[key]=union
   # Preserve old maximum-clearance semantics, including empty native lists.
   clearances=[z.GetLocalClearance()for z in self.board.Zones()if not z.GetIsRuleArea()and z.GetNetname()==net and z.HasFilledPolysForLayer(layer)]
   self.zone_clearance[key]=max(clearances,default=0)
  if not self.fills[key].OutlineCount():
   raise ValueError('Actual filled own-reference plane is absent:'+net+' '+self.board.GetLayerName(layer))
  return self.fills[key]
def return_corridor_check(board,added,rows):
 dependencies();checker=NativeCollectedAnnulusCheck(board,rows)
 exact={strict.prior.uid(t):t for t in board.GetTracks()};items=[]
 if not set(added)<=set(exact):raise ValueError('Declared added copper UUID absent')
 for ident in sorted(added):
  t=exact[ident]
  if t.GetNetname()not in rows:raise ValueError('Actual new signal lacks exact source/return manifest')
  row=rows[t.GetNetname()]
  items.append(checker.via(t,row)if isinstance(t,pcbnew.PCB_VIA)else checker.segment(t,row))
 return dict(passed=True,new_copper_items_checked=len(items),items=items,
  actual_signal_via_reference_audits=list(checker.audits.values()),
  exact_same_net_antipad_exceptions_only=True,real_numbered_source_pad_anchor_required=True,
  actual_flashed_and_native_connected_reference_annuli_required=True,
  exact_sequential_native_nonempty_BooleanAdd_and_final_Simplify=True,
  physical_signal_integrity_qualified=False,measured_return_impedance=False,no_source_or_PCB_mutation=True)
