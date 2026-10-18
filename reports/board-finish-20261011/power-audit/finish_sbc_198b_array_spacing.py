"""Final read-only whole source+load array spacing gate; no route/search/mutation."""
import copy,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'sbc-198b-source-proposal'
V2=OUT/'final-bounded-blocker-v2.json';RAW=OUT/'tapered-hub-prerequisites.json';DEST=OUT/'final-bounded-blocker-v3.json'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def whole_array_ok(arrays):
    if len(arrays)!=2 or any(len(ar)!=9 for ar in arrays):return False
    pts=[pt for ar in arrays for pt in ar]
    if any(len(pt)!=2 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in pt) for pt in pts):return False
    return all(math.dist(a,b)>=.8-1e-9 for i,a in enumerate(pts) for b in pts[i+1:])
def main():
    if DEST.exists():raise ValueError('new immutable receipt required')
    before={str(path.resolve()):sha(path) for path in (V2,RAW,Path(__file__))}
    v2=json.loads(V2.read_bytes());raw=json.loads(RAW.read_bytes())
    for path,expected in v2['source_sha256_before'].items():
        if sha(path)!=expected:raise ValueError('frozen v2 input changed')
        before[path]=expected
    if v2['source_sha256_before']!=v2['source_sha256_after'] or v2['board_sha256']!=raw['board_sha256']:raise ValueError('v2 read/source identity differs')
    a=[[x*.8,0.] for x in range(9)];b=[[x*.8,2.] for x in range(9)]
    rows=[]
    fixtures=[('valid eighteen distinct sites',[a,b],True),('cross-array.4mm collision',[a,[a[0][:1]+[.4]]+b[1:]],False),
        ('same via credited to both arrays',[a,[a[0]]+b[1:]],False),('one array undersized',[a,b[:-1]],False),
        ('nonfinite coordinate',[a,[[float('nan'),2.]]+b[1:]],False),('exact.8mm cross-array boundary',[a,[[0.,.8]]+b[1:]],True),
        ('below.8mm cross-array boundary',[a,[[0.,.7999]]+b[1:]],False)]
    for name,arrays,expected in fixtures:
        accepted=whole_array_ok(arrays)
        if accepted!=expected:raise ValueError('spacing control failed: '+name)
        rows.append({'name':name,'expected_accept':expected,'actual_accept':accepted})
    result=copy.deepcopy(v2)
    result['schema']='exact198b-final-one-bounded-SBC-source-proposal-blocker-v3'
    checks=[]
    for screen in raw['screens']:
        for i,lead in enumerate(screen['at_most_two_hub_choice_geometry_leads']):
            arrays=[[row['via'] for row in ar['branches']] for ar in lead['arrays']]
            cross=[{'source_at':a,'load_at':b,'distance_mm':math.dist(a,b)} for a in arrays[0] for b in arrays[1] if math.dist(a,b)<.8-1e-9]
            okay=whole_array_ok(arrays)
            checks.append({'net':screen['net'],'layer':screen['layer'],'raw_lead_index':i,'whole_eighteen_site_spacing_accept':okay,
                'cross_array_minimum_mm':min(math.dist(a,b) for a in arrays[0] for b in arrays[1]),'conflicts':cross})
            match=next(row for row in result['actual_trunk_branch_paths'] if row['net']==screen['net'] and row['layer']==screen['layer'] and row['raw_lead_index']==i)
            match['whole_source_plus_load_array_spacing_accept']=okay
            match['geometry_accept_only']=match['geometry_accept_only'] and okay
    if len(checks)!=2:raise ValueError('raw lead inventory differs')
    result['whole_source_load_array_spacing_checks']=checks
    result['whole_array_spacing_controls']=rows
    result['bounded_trunk_findings']['independent_geometry_accepted_output_leads']=sum(r['geometry_accept_only'] for r in result['actual_trunk_branch_paths'])
    result['superseded_v2_scope']='v2 checks each array internally; v3 additionally checks all eighteen prospective source+load via centers together. One second-lead cross-array pair.4mm apart is rejected; no repacking/research performed.'
    result['route_gate_and_spacing_control_count']=len(result['raw_route_gate_controls'])+len(rows)
    result['source_sha256_before']=before;result['source_sha256_after']={path:sha(path) for path in before}
    if before!=result['source_sha256_after']:raise ValueError('final read set changed')
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(DEST),'sha256':sha(DEST),'controls':result['route_gate_and_spacing_control_count'],
        'actual_paths_individually_checked':result['actual_checked_paths'],'whole_array_geometry_accepted_leads':result['bounded_trunk_findings']['independent_geometry_accepted_output_leads'],
        'cross_array_checks':checks,'verdict':result['verdict']}))
if __name__=='__main__':main()
