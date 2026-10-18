"""Independent actual-annulus/layer proof and persisted ADC ground negatives."""
import argparse,copy,json
from pathlib import Path
import pcbnew
from hardware_route_adc_quiet_anchors import anchor_checks,NET
from hardware_populate_motherboard_pcb import sha,write
from hardware_build_assembly import parse,dump,children,child,value

def actual_anchor_layer_checks(path,groups):
 rows=anchor_checks(path,groups);b=pcbnew.LoadBoard(str(path));b.BuildConnectivity();exact={t.m_Uuid.AsString():t for t in b.GetTracks()}
 for row in rows:
  v=exact[row['via_uuid']]
  if not v.FlashLayer(pcbnew.In1_Cu)or not b.GetConnectivity().IsConnectedOnLayer(v,pcbnew.In1_Cu):
   raise ValueError('Drilled span is not a flashed/native-connected In1 annulus')
  row.update(actual_In1_annulus_flashed=True,native_IsConnectedOnLayer_In1=True)
 return rows

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('board','receipt','out'):ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.out=a.out.resolve();assert not a.out.exists();a.out.mkdir(parents=True)
 r=json.loads(a.receipt.read_text());assert r['passed']and r['board_sha256']==sha(a.board)
 frozen={str(p.resolve()):sha(p)for p in [a.board,a.receipt,Path(__file__),Path(__file__).with_name('hardware_route_adc_quiet_anchors.py')]}
 groups=r['exact_four_ground_branches'];healthy=actual_anchor_layer_checks(a.board,groups);tests=[]
 def rejected(name,path):
  try:actual_anchor_layer_checks(path,groups)
  except ValueError as e:tests.append(dict(name=name,persisted_native_fixture_sha256=sha(path),rejected=True,reason=str(e)))
  else:raise ValueError('Actual negative ADC fixture accepted '+name)
 # A real removed stitch cannot be replaced by a span-only metadata claim.
 via=healthy[0]['via_uuid'];b=pcbnew.LoadBoard(str(a.board))
 item=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==via);b.Remove(item)
 p=a.out/'missing-real-ground-stitch.kicad_pcb';pcbnew.SaveBoard(str(p),b);rejected('missing-real-ground-stitch',p)
 # Preserve zone outlines while removing the actual filled own copper. An
 # unfilled polygon must never be accepted as a connected annulus.
 b=pcbnew.LoadBoard(str(a.board));
 for z in b.Zones():
  if z.GetNetname()==NET:z.UnFill()
 p=a.out/'own-reference-unfilled.kicad_pcb';pcbnew.SaveBoard(str(p),b);rejected('own-reference-unfilled',p)
 b=pcbnew.LoadBoard(str(a.board));ident=groups[1]['added_UUIDs'][0];next(t for t in b.GetTracks()if t.m_Uuid.AsString()==ident).SetLayer(pcbnew.B_Cu)
 p=a.out/'quiet-ground-branch-on-B.kicad_pcb';pcbnew.SaveBoard(str(p),b);rejected('quiet-ground-branch-on-B',p)
 b=pcbnew.LoadBoard(str(a.board));f=next(f for f in b.GetFootprints()if f.GetReference()=='U14734');next(p for p in f.Pads()if p.GetNumber()=='6').SetNet(b.FindNet('/LOGIC_GND'))
 p=a.out/'quiet-owner-wrong-domain.kicad_pcb';pcbnew.SaveBoard(str(p),b);rejected('quiet-owner-wrong-domain',p)
 assert all(sha(p)==h for p,h in frozen.items())
 write(a.out/'review.json',dict(passed=True,input_sha256=frozen,actual_native_own_In1_annulus_proofs=healthy,
  actual_persisted_negative_controls=tests,actual_fourteen_F_only_pairs_retained_receipt_sha256=sha(a.receipt),
  In4_reference_claimed=False,global_planes_qualified=False,physical_reference_noise_qualified=False,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_annuli=4,persisted_negative_controls=len(tests))))

if __name__=='__main__':main()
