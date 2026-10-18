"""Locate the exact existing fault barrels for a single dive/return repair."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
OUT=H/'U10003-ground-fault-literal-existing-barrels-r126'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());net='/motherboard_do/DOA_FLT_N_FIELD';point=Point(215.95,143.05)
    vias=sorted([q for q in h['vias'] if C.norm(q['net'])==net],key=lambda q:point.distance(Point(q['x'],q['y'])))[:8]
    pads=[{k:v for k,v in q.items() if k not in ('layers','hole')} for q in h['pads'] if C.norm(q['net'])==net]
    tracks=[q for q in h['tracks'] if C.norm(q['net'])==net and LineString([q['a'],q['b']]).distance(point)<5.]
    groups=F.graph(full,net);membership={q['uuid']:i for i,xs in enumerate(groups) for q in xs};rows={'via_rows':vias,'pads':pads,'local_tracks':tracks,'group_membership_for_nearby_vias':{v['uuid']:membership[v['uuid']] for v in vias},'ground_pad':{k:v for k,v in next(p for p in h['pads'] if (p['ref'],p['num'])==('U10003','9')).items() if k not in ('layers','hole')}}
    record={'verdict':'LITERAL_EXISTING_FAULT_BARREL_AND_GROUND_PAD_SCOPE','model_sha256':sha(mp),'rows':rows,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
