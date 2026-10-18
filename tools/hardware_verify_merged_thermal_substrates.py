"""Independently recheck all44 actual ISO1212 floating islands after a merge."""
import argparse,hashlib,json
from pathlib import Path
import pcbnew
from hardware_add_iso1212_substrates import check_substrates
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('board','out'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();rowsfile=ROOT/'reports/motherboard-return-zoning-20261001/floating-substrates-r03/substrate-rows.json'
 frozen={str(f.resolve()):sha(f)for f in (a.board,rowsfile,Path(__file__))}
 if a.out.exists():raise ValueError('Fresh review file required')
 b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();rows=json.loads(rowsfile.read_text())
 if len(rows)!=44 or len({r['net']for r in rows})!=44:raise ValueError('Actual44 separate thermal networks required')
 pads={p.m_Uuid.AsString():p for f in b.GetFootprints()for p in f.Pads()};zones={z.m_Uuid.AsString():z for z in b.Zones()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
 errors=[]
 for r in rows:
  pad=pads[r['pad_uuid']];zone=zones[r['zone_uuid']];via=cu[r['via_uuid']]
  if pad.GetParentFootprint().GetReference()!=r['reference']or pad.GetNumber()!=r['pin']or pad.GetNetname()!=r['net']or zone.GetNetname()!=r['net']or via.GetNetname()!=r['net']:errors.append('Exact thermal source/zone/via identity differs '+r['reference']+'.'+r['pin'])
  cluster=[i for i in b.GetConnectivity().GetConnectedItems(pad)if i.Type()==pcbnew.PCB_PAD_T and i.GetNumber()]
  if {i.m_Uuid.AsString()for i in cluster}!={r['pad_uuid']}:errors.append('Floating substrate physically joins another numbered source pin '+r['reference']+'.'+r['pin'])
 result=check_substrates(b,rows);result.update(exact_44_source_pad_clusters_and_zone_via_nets_checked=True,source_cluster_errors=errors,input_sha256=frozen,manufacturing_ready=False,physical_qualification=False)
 result['passed']=result['passed']and not errors
 if any(sha(Path(p))!=s for p,s in frozen.items()):raise ValueError('Review input changed')
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],islands=len(result['rows']),source_cluster_errors=errors)));raise SystemExit(not result['passed'])
if __name__=='__main__':main()
