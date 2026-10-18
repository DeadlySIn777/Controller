"""Load/save/reload only an isolated tiny fixture; never fill or save a source board."""
import sys,os,ctypes
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];handle=k.GetCurrentProcess();assert k.SetProcessAffinityMask(handle,sum(1<<i for i in range(16,28)));assert k.SetPriorityClass(handle,0x4000)
from pathlib import Path
import pcbnew,json,hashlib,time
H=Path(__file__).resolve().parent;OUT=H/'CORE60-single-outer-native-roundtrip-r2';INPUT=OUT/'input.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ring(c):return[[c.CPoint(i).x,c.CPoint(i).y]for i in range(c.PointCount())]
def rings(p):return[{'outer_IU':ring(p.COutline(i)),'holes_IU':[ring(p.CHole(i,j))for j in range(p.HoleCount(i))]}for i in range(p.OutlineCount())]
def canonical(q):
    if q[0]==q[-1]:q=q[:-1]
    def one(p):
        t=tuple(map(tuple,p));m=min(t);return min(t[i:]+t[:i]for i,v in enumerate(t)if v==m)
    return min(one(q),one(list(reversed(q))))
def inspect(b,data):
    zs={z.m_Uuid.AsString():z for z in b.Zones()};assert set(zs)=={r['UUID']for r in data['zones']};result=[]
    for row in data['zones']:
        z=zs[row['UUID']];ps=z.Outline();rr=rings(ps);assert len(rr)==1 and not rr[0]['holes_IU']
        assert canonical(rr[0]['outer_IU'])==canonical(row['native_integer_outer_IU'])
        result.append({'UUID':row['UUID'],'exact_native_integer_outer_and_hole_ownership_preserved':True,'native_outlines':rr,'raw_net':z.GetNetname(),'name':z.GetZoneName(),'layer':b.GetLayerName(z.GetLayer()),'priority':z.GetAssignedPriority(),'minimum_thickness_IU':z.GetMinThickness(),'local_clearance_IU':z.GetLocalClearance(),'all6_cached_fills_empty':all(not z.HasFilledPolysForLayer(l)or z.GetFilledPolysList(l).OutlineCount()==0 for l in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu))})
    return result
def main():
    t=time.monotonic();d=json.loads(INPUT.read_bytes());pins={str(f):sha(f)for f in(Path(__file__),INPUT,Path(d['native_input']),Path(d['held_legacy_fixture']),Path(d['source']))}
    assert sha(d['native_input'])==d['native_input_SHA256']and sha(d['held_legacy_fixture'])==d['held_legacy_fixture_SHA256']
    legacy=pcbnew.LoadBoard(d['held_legacy_fixture']);lz=next(z for z in legacy.Zones()if z.m_Uuid.AsString()==d['original_zone_UUID']);observation={'native_outer_count':lz.Outline().OutlineCount(),'native_hole_counts':[lz.Outline().HoleCount(i)for i in range(lz.Outline().OutlineCount())],'outlines':rings(lz.Outline()),'source':d['held_legacy_fixture'],'source_SHA256':sha(d['held_legacy_fixture']),'failed_two_outer_intent_is_not_legal_native_equivalence':True}
    (OUT/'held-legacy-multiple-polygon-native-parser-observation.json').write_text(json.dumps(observation,indent=1)+'\n',encoding='utf-8')
    b=pcbnew.LoadBoard(d['native_input']);before=inspect(b,d)
    for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
    output=Path(d['native_saved_output']);assert not output.exists();assert pcbnew.SaveBoard(str(output),b)
    after=inspect(pcbnew.LoadBoard(str(output)),d);assert before==after
    assert all(sha(f)==v for f,v in pins.items())and sha(d['source'])==d['source_SHA256']
    rec={'status':'ALL_TWO_SINGLE_OUTER_CORE60_NATIVE_INTEGER_CONTOURS_HOLE_OWNERSHIP_LOAD_SAVE_RELOAD_PASS_NO_FILL','native_version':pcbnew.GetBuildVersion(),'isolated_mini_fixture_only_no_source_save':True,'native_before_after_observations_equal':True,'both_real_fragments_kept_under_original_and_deterministic_child_UUID':True,'held_legacy_multiple_polygon_observation':observation,'rows':after,'native_saved_output':str(output),'native_saved_output_SHA256':sha(output),'all_Cu_cache_empty_before_after':all(r['all6_cached_fills_empty']for r in after),'native_CPP_after_reference_source_contact_current_IR_minwidth_thermal_barrel_gates':'OPEN_REQUIRED','Fill_calls':0,'SaveBoard_calls_isolated_mini_fixture_only':1,'SaveProject_calls':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-t}
    (OUT/'native-roundtrip-receipt.json').write_text(json.dumps(rec,indent=1)+'\n',encoding='utf-8');print('CORE60_SINGLE_OUTER_NATIVE_ROUNDTRIP_PASS',sha(OUT/'native-roundtrip-receipt.json'),flush=True)
if __name__=='__main__':main()
