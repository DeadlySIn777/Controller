"""Read-only native pad/net and layout-distance review for exact cap owners."""
from pathlib import Path
import argparse,hashlib,json,math
import pcbnew
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 before=hashlib.sha256(a.board.read_bytes()).hexdigest();board=pcbnew.LoadBoard(str(a.board.resolve()));fps={f.GetReference():f for f in board.GetFootprints()}
 pads={r:{} for r in fps}
 for r,f in fps.items():
  for p in f.Pads():pads[r].setdefault(p.GetNumber(),[]).append(p)
 manifest=json.loads(a.manifest.read_text());errors=[];rows=[]
 for c in manifest['capacitors']:
  result=dict(ref=c['ref'],owner_ref=c['owner_ref'],category=c['category'],endpoints=[])
  for cp,eps in c['actual_owner_endpoints'].items():
   for ep in eps:
    cap=pads.get(c['ref'],{}).get(cp,[]);own=pads.get(ep['ref'],{}).get(ep['pin'],[])
    if not cap or not own:errors.append('missing '+c['ref']+'.'+cp+' or '+ep['ref']+'.'+ep['pin']);continue
    if {p.GetNetname() for p in cap}!={p.GetNetname() for p in own}:errors.append('net '+c['ref']+'.'+cp+' vs '+ep['ref']+'.'+ep['pin'])
    dist=min(math.hypot(pcbnew.ToMM(x.GetPosition().x-y.GetPosition().x),pcbnew.ToMM(x.GetPosition().y-y.GetPosition().y))for x in cap for y in own)
    result['endpoints'].append(dict(cap_pin=cp,owner_ref=ep['ref'],owner_pin=ep['pin'],native_net=cap[0].GetNetname(),pad_anchor_distance_mm=dist))
  target=c['engineering_pad_to_owner_target_mm'];result['engineering_target_mm']=target
  result['within_engineering_target']=None if target is None else all(any(p['pad_anchor_distance_mm']<=target for p in result['endpoints']if p['cap_pin']==pin)for pin in ['1','2'])
  rows.append(result)
 after=hashlib.sha256(a.board.read_bytes()).hexdigest();assert before==after
 output=dict(native_board=str(a.board),board_sha256=before,board_unchanged=True,source_connectivity_ok=not errors,errors=errors,
   cap_count=len(rows),distance_is_pad_anchor_not_copper_edge=True,numeric_targets_are_engineering_not_manufacturer_limits=True,
   layout_qualified=False,capacitors=rows,
   over_engineering_target=[r['ref']for r in rows if r['within_engineering_target']is False])
 a.output.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:output[k]for k in ['source_connectivity_ok','cap_count','errors','over_engineering_target']},indent=2))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
