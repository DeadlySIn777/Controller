"""Read-only native parsing of both retained CORE60 intent fragments."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
from pathlib import Path
import pcbnew,json,hashlib,time
H=Path(__file__).resolve().parent
PACKET=H/'coupled-CORE60-preserved-fragments-stage3-candidate-r1'
SOURCE=H.parents[3]/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb'
CANDIDATE=PACKET/'candidate/board.kicad_pcb';OUT=H/'CORE60-preserved-fragments-read-only-native-probe-r1'
UID='60c95fa7-e6df-530f-a3d3-00d3f96e46bc';LG='c1d27fa1-452b-4e27-985d-5ad23644d800'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ring(c):return[[c.CPoint(i).x,c.CPoint(i).y]for i in range(c.PointCount())]
def rings(p):return[{'outer_IU':ring(p.COutline(i)),'holes_IU':[ring(p.CHole(i,j))for j in range(p.HoleCount(i))]}for i in range(p.OutlineCount())]
def canonical(q):
    def one(p):
        if p[0]==p[-1]:p=p[:-1]
        m=min(p);return min(tuple(tuple(v)for v in p[i:]+p[:i])for i,v in enumerate(p)if v==m)
    return min(one(q),one(list(reversed(q))))
def zone(z,b):
    return{'UUID':z.m_Uuid.AsString(),'name':z.GetZoneName(),'raw_net':z.GetNetname(),'layers':[b.GetLayerName(l)for l in b.GetEnabledLayers().CuStack()if z.GetLayerSet().Contains(l)],'outline_count':z.Outline().OutlineCount(),'native_outlines':rings(z.Outline()),'priority':z.GetAssignedPriority(),'minimum_fill_width_IU':z.GetMinThickness(),'cached_IsFilled':bool(z.IsFilled())}
def main():
    t=time.monotonic();assert not OUT.exists();OUT.mkdir()
    inputs=[Path(__file__),SOURCE,CANDIDATE,PACKET/'receipt.json',PACKET/'per-component-per-edge-exact-native-IU-subset-proof.json'];pins={str(f):sha(f)for f in inputs}
    assert pins[str(SOURCE)]=='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca'
    assert pins[str(CANDIDATE)]=='447bf8e80de868c02ed7b36aa336a1b8248b4ad5c0c87f227d44f413f6a4287b'
    boards=[];counts=[]
    for f in(SOURCE,CANDIDATE):
        b=pcbnew.LoadBoard(str(f));zs={z.m_Uuid.AsString():z for z in b.Zones()};counts.append(len(zs));boards.append({'file':str(f),'zones':{u:zone(zs[u],b)for u in(UID,LG)}})
    before,after=boards;assert counts==[850,850]
    assert before['zones'][UID]['outline_count']==1 and after['zones'][UID]['outline_count']==2
    assert before['zones'][LG]==after['zones'][LG]
    rawproof=json.loads((PACKET/'per-component-per-edge-exact-native-IU-subset-proof.json').read_bytes())
    expected=[]
    for component in rawproof['components']:expected.append(canonical([row['a_IU']for row in component['edges']]))
    actual=[canonical(p['outer_IU'])for p in after['zones'][UID]['native_outlines']]
    assert sorted(expected)==sorted(actual)and all(not p['holes_IU']for p in after['zones'][UID]['native_outlines'])
    for k in('UUID','name','raw_net','layers','priority','minimum_fill_width_IU','cached_IsFilled'):assert before['zones'][UID][k]==after['zones'][UID][k]
    assert all(sha(f)==v for f,v in pins.items())
    rec={'status':'READ_ONLY_NATIVE_PARSER_CONFIRMS_BOTH_REAL_FRAGMENTS_EXACT_SAME_UUID_NO_FILL_SAVE','native_version':pcbnew.GetBuildVersion(),'zone_counts':counts,'native_outline_count_before_after':[1,2],'native_integer_rings_exact_to_per_edge_host_proof':True,'native_both_fragments_retained_no_holes_no_fragment_discarded':True,'literal_retained_LG_native_API_observations_identical':True,'observations':boards,'native_CPP_refill_all_physical_reference_current_IR_minwidth_thermal_gates':'OPEN_REQUIRED','Fill_calls':0,'SaveBoard_calls':0,'SaveProject_calls':0,'source_and_candidate_hashes_unchanged':True,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-t}
    (OUT/'receipt.json').write_text(json.dumps(rec,indent=1)+'\n',encoding='utf-8');print('NATIVE_CORE60_TWO_OUTLINES_CONFIRMED',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
