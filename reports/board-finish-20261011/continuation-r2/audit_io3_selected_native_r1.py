"""Independent exact-raw IO3 source graph on actual selected native fill."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H))
import contact_layout as C
import fast_contacts as F
import ordinary_routes as O
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    d=H/'io3-native-diagnostic-r2';out=d/'independent-selected-IO3.json';assert not out.exists()
    fill=d/'scoped-native-fill';r=json.loads((fill/'receipt.json').read_bytes())
    gp=fill/'geometry.json';fp=fill/'actual-via-flashes.json'
    assert sha(gp)==r['geometry_sha256']=='6f5447d29114cb527f13b44ab7f001bbcb18e581bb9484025919323e78e5b2f3'
    assert sha(fp)==r['actual_via_flashes_sha256']=='de2d00a03e24a2799d3cabffb2a01f58ea2a0385f526926d019a81325376695a'
    assert not r['all_discrete_post_fill_errors'] and r['selected_raw_net']=='/IO_3V3'
    mp=H/'sbc-power/owned-io3-layer-escape-repair-r42/model.pkl';mr=json.loads(mp.with_name('receipt.json').read_bytes());assert sha(mp)==mr['model_sha256']=='dc06d1688f700a4c0232ee948ebbdfba6d4af931a9918f5521b1914de194ce68'
    old,h,b,z,projected=pickle.loads(mp.read_bytes());ng=json.loads(gp.read_bytes());flashes=json.loads(fp.read_bytes())['vias'];raw='/IO_3V3'
    nativepads=[p for p in ng['pads'] if p['net']==raw];hpads=[p for p in h['pads'] if p['net']==raw]
    pads=[];seen=set()
    for p in nativepads:
        matches=[q for q in hpads if (q['ref'],q['num'])==(p['ref'],p['num']) and [q['x'],q['y']]==p['at']]
        assert len(matches)==1,('Ambiguous physical pad requires native UUID export',p['ref'],p['num'],p['at'])
        q=matches[0];assert q['uuid'] not in seen;seen.add(q['uuid'])
        pads.append({**q,'layers':{l:O.polys(p['poly']) for l in p['layers']}})
    assert seen=={q['uuid'] for q in hpads}
    tracks=[{'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'a':q['s'],'b':q['e'],'w':q['w'],'locked':q['locked']} for q in ng['tracks'] if q['net']==raw]
    vias=[{'uuid':q['uuid'],'net':q['net'],'x':q['at'][0],'y':q['at'][1],'d':q['w'],'drill':q['drill'],'flashed':flashes[q['uuid']]} for q in ng['vias'] if q['net']==raw]
    ht={q['uuid']:q for q in h['tracks'] if q['net']==raw};hv={q['uuid']:q for q in h['vias'] if q['net']==raw}
    assert set(ht)=={q['uuid'] for q in tracks} and set(hv)=={q['uuid'] for q in vias}
    for q in tracks:assert all(q[k]==ht[q['uuid']][k] for k in ('net','layer','a','b','w'))
    for q in vias:assert all(q[k]==hv[q['uuid']][k] for k in ('net','x','y','d','drill'))
    zones=[{**q,'fills':{l:O.polys(rs) for l,rs in q['fills'].items()}} for q in ng['zones'] if q['net']==raw]
    assert {q['uuid'] for q in zones}==set(r['selected_zone_UUIDs'])
    g={**h,'pads':pads,'tracks':tracks,'vias':vias,'zones':zones,'shapes':[q for q in h['shapes'] if q['net']==raw]}
    groups=F.graph(g,raw);index={q['uuid']:i for i,xs in enumerate(groups) for q in xs};source=next(q for q in pads if (q['ref'],q['num'])==('R18001','2'));target=next(q for q in pads if (q['ref'],q['num'])==('R11049','1'));root=index[source['uuid']]
    via='4df659b6-03b2-580c-b6b8-1cc10e70c2c8';need={'F.Cu','In1.Cu'};actual=set(flashes[via]);annular=[]
    from shapely.geometry import Point
    from shapely.ops import unary_union
    v=next(q for q in vias if q['uuid']==via);ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
    rec,trees=F.build(g,nets={raw})
    for layer in sorted(need):
        physical=unary_union([q['shape'] for q in groups[root] if q['layer']==layer and q['kind']!='via']);annular.append({'layer':layer,'actual_flashed':layer in actual,'source_rooted_other_Cu_annular_overlap_mm2':ann.intersection(physical).area})
    okay=index[target['uuid']]==root and index[via]==root and need<=actual and all(q['source_rooted_other_Cu_annular_overlap_mm2']>1e-8 for q in annular)
    report={'verdict':'PASS_SELECTED_NATIVE_IO3_SOURCE_PAIR_BARREL_AND_ANNULUS' if okay else 'FAIL_SELECTED_NATIVE_IO3_SOURCE_OR_ANNULUS','candidate_sha256':r['candidate_sha256'],'actual_source':'R18001.2','target':'R11049.1','actual_source_pad_UUID':source['uuid'],'target_physical_pad_UUID':target['uuid'],'target_same_actual_source_group':index[target['uuid']]==root,'new_barrel_same_actual_source_group':index[via]==root,'required_actual_F_In1_annuli':annular,'native_IO3_pad_count':len(pads),'actual_IO3_groups':len(groups),'actual_source_rooted_named_pads':len({q['uuid'] for q in groups[root] if q['kind']=='pad' and q['pin']}),'pad_binding':'Exact unique ref/pin/native centre plus preserved native footprint UUID chunks and source/API ledger; duplicate physical identities rejected','scope':'Only31 exact IO3 zones freshly filled; no other R38 power proposals or other-zone refill credit','whole_board_retained_contacts_DRC_current_and_final_power_composition':'OPEN','input_sha256':{str(p.resolve()):sha(p) for p in (Path(__file__),gp,fp,fill/'receipt.json',mp,mp.with_name('receipt.json'),d/'native-parity.json',d/'construction.json')},'native_jobs':0,'board_written':False,'adopted':False}
    out.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':report['verdict'],'groups':len(groups),'rooted_named_pads':report['actual_source_rooted_named_pads'],'annular':annular}),flush=True)
    return 0 if okay else 1
if __name__=='__main__':raise SystemExit(main())
