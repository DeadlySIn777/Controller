"""Independent native nine-Y2 AC-only endpoint and shield/bond verification."""
import argparse,json,math
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy
from hardware_isow_layout_recipe import lands,vec
from hardware_validate_isow_cells import evaluate as isow_evaluate

EXPECTED={
 'C19501':('J15004',['17'],['SH1','SH2','SH3','SH4']),
 'C19502':('J19513',['2','9'],['10']),
 'C19503':('J19501',['13'],['6']),
 'C19504':('J19534',['9'],['12']),
 'C19505':('J19529',['2'],['3']),
 'C19506':('J19530',['2'],['3']),
 'C19507':('J19531',['11'],['12']),
 'C19508':('J19532',['3','6'],['5']),
 'C19509':('J19533',['3','6'],['5'])}

def evaluate(b,old,poses):
    b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};before={f.GetReference():f for f in old.GetFootprints()};errors=[];rows=[]
    def pad(r,pin):return next(z for z in fs[r].Pads()if z.GetNumber()==pin)
    for ref,(owner,pp,gg)in EXPECTED.items():
        f=fs[ref];row=dict(ref=ref,owner=owner,ends=[])
        if f.GetValue()!=before[ref].GetValue():errors.append(ref+' exact value changed')
        if lands(f)!=lands(before[ref]):errors.append(ref+' native manufacturer lands/source pin net changed')
        actual=[*xy(f.GetPosition()),f.GetOrientationDegrees()%360]
        expected=[*poses[ref][:2],poses[ref][2]%360]
        if any(abs(x-y)>1e-5 for x,y in zip(actual,expected)):errors.append(ref+' approved physical pose changed')
        for cp,targets in[('1',pp),('2',gg)]:
            q=pad(ref,cp);cluster={z.m_Uuid.AsString()for z in b.GetConnectivity().GetConnectedItems(q)if z.Type()==p.PCB_PAD_T};nodes=[pad(owner,z)for z in targets];actual_join=any(z.m_Uuid.AsString()in cluster for z in nodes)
            if not all(z.GetNetCode()==q.GetNetCode()for z in nodes):errors.append(ref+'.'+cp+' is not its own declared physical return/shield net')
            if not actual_join:errors.append(ref+'.'+cp+' missing actual own-port Cu join')
            if (cp=='2')!=q.GetNetname().endswith('/CHASSIS'):errors.append(ref+' functional ground DC bond or incorrect chassis pin')
            row['ends'].append(dict(pin=cp,actual_native_net=q.GetNetname(),owner_pins=targets,actual_owner_pin_joined=actual_join,owner_nearest_pin_distance_mm=min(math.dist(xy(q.GetPosition()),xy(z.GetPosition()))for z in nodes)))
        rows.append(row)
    chassis=[z for z in b.GetPads()if z.GetNetname().endswith('/CHASSIS')];bond=pad('H19501','1');connected={z.m_Uuid.AsString()for z in b.GetConnectivity().GetConnectedItems(bond)if z.Type()==p.PCB_PAD_T}
    missing=[z.GetParentFootprint().GetReference()+'.'+z.GetNumber()for z in chassis if z.m_Uuid.AsString()not in connected]
    if len(chassis)!=51 or missing:errors.append('Actual51 shield/coupling/bond population not fully joined: '+repr(missing))
    for ref,f in fs.items():
        if ref in EXPECTED:continue
        if lands(f)!=lands(before[ref])or xy(f.GetPosition())!=xy(before[ref].GetPosition())or f.GetOrientationDegrees()!=before[ref].GetOrientationDegrees()or f.GetLayer()!=before[ref].GetLayer():errors.append(ref+' unowned native source/pose change')
    return errors,rows,missing

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--board',required=True,type=Path);ap.add_argument('--proposal',required=True,type=Path);a=ap.parse_args();out=a.out.resolve();assert not out.exists();out.mkdir(parents=True)
    rp=a.board.with_name('receipt.json');r=json.loads(rp.read_text());pr=json.loads(a.proposal.read_text());base=Path(next(q for q in pr['input_hashes']if q.endswith('motherboard-bounded-merged-candidate.kicad_pcb')));poses={z['ref']:z['new_pose']for z in pr['proposal']}
    primary=ROOT/'reports/motherboard-chassis-20261001/y2-primary-r01/receipt.json';isowrp=ROOT/'reports/motherboard-chassis-20261001/isow-full-cells-r03/receipt.json';cs=ROOT/'hardware/motherboard_comms/design.json'
    inputs={str(q.resolve()):sha(q)for q in[a.board,rp,a.proposal,base,primary,isowrp,cs,ROOT/'tools/hardware_isow_layout_recipe.py',Path(__file__)]};old=p.LoadBoard(str(base));b=p.LoadBoard(str(a.board));errors,rows,missing=evaluate(b,old,poses)
    isow_errors,_=isow_evaluate(b,json.loads(cs.read_text()),json.loads(isowrp.read_text()));errors.extend(isow_errors)
    negative=[]
    def test(name,fn):
        q=p.LoadBoard(str(a.board));fs={f.GetReference():f for f in q.GetFootprints()};fn(q,fs);e,_,_=evaluate(q,old,poses);negative.append(dict(name=name,rejected=bool(e),errors=e[:5]));assert e,name
    test('Functional return shorted by assigning Y2 pin1 CHASSIS',lambda q,fs:next(z for z in fs['C19503'].Pads()if z.GetNumber()=='1').SetNet(next(z for z in fs['H19501'].Pads()).GetNet()))
    test('Cap coupling assigned to another isolated return',lambda q,fs:next(z for z in fs['C19505'].Pads()if z.GetNumber()=='1').SetNet(next(z for z in fs['C19506'].Pads()if z.GetNumber()=='1').GetNet()))
    test('Coupling moved away from its approved mate-clear port pose',lambda q,fs:fs['C19508'].SetPosition(fs['C19508'].GetPosition()+vec((20,0))))
    test('Stock Y2 lead geometry changed',lambda q,fs:next(z for z in fs['C19507'].Pads()if z.GetNumber()=='2').SetSize(vec((4,4))))
    def cutbond(q,fs):
        bp=next(z for z in fs['H19501'].Pads());doomed=[t for t in q.GetTracks()if t.GetNetCode()==bp.GetNetCode()and(bp.HitTest(t.GetStart())or bp.HitTest(t.GetEnd()))];assert doomed
        for t in doomed:
            if bp.HitTest(t.GetStart()):t.SetStart(t.GetStart()+vec((20,20)))
            if bp.HitTest(t.GetEnd()):t.SetEnd(t.GetEnd()+vec((20,20)))
    test('Actual M4 bond Cu cut while logical net name remains',cutbond)
    assert inputs=={q:sha(Path(q))for q in inputs}
    d=dict(input_hashes=inputs,baseline_pass=not errors,errors=errors,native_Y2=rows,native_CHASSIS_pads=51,actual_all51_bonded=not missing,ISOW_source_RAW_corridor_and_same_side_HF_preserved=not isow_errors,negative_controls=negative,all_negative_controls_rejected=all(z['rejected']for z in negative),native_DRC_new_exact_violations=r['native_DRC_new_exact_violations'],retained_prior_native_DRC=r['native_DRC_regular'],ignored_checks=r['native_DRC_ignored'],source_modified=False,physical_qualification=False,protective_earth_fault_capacity_qualified=False,manufacturing_ready=False)
    (out/'review.json').write_text(json.dumps(d,indent=2)+'\n');(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in d.items()if k not in['input_hashes','native_Y2','negative_controls']}));assert not errors and not d['native_DRC_new_exact_violations']and not d['ignored_checks']
if __name__=='__main__':main()
