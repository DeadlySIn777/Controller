"""Independent exact-raw CORE1V2 source graph on actual selected native fill."""
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
    d=H/'core1v2-native-diagnostic-r132';out=d/'independent-selected-CORE1V2-r133.json';assert not out.exists()
    fill=d/'scoped-native-fill';r=json.loads((fill/'receipt.json').read_bytes())
    gp=fill/'geometry.json';fp=fill/'actual-via-flashes.json'
    assert sha(gp)==r['geometry_sha256']=='65e55826c5b925fdcfb98114b1f6d04f0ca49e67b3025db21157436cee71f6eb'
    assert sha(fp)==r['actual_via_flashes_sha256']=='13571e6204e78f9aab1f2858ff123b6ef72f3aab766edb2587bc8155954f8ec7'
    assert not r['all_discrete_post_fill_errors'] and r['selected_raw_net']=='/CORE_1V2'
    mp=H/'sbc-power/frozen-regional-source-exit-replay-r129/model.pkl';mr=json.loads(mp.with_name('receipt.json').read_bytes());assert sha(mp)==mr['model_sha256']=='8f4db80497693186388d622a45508cdf39eb5e0f51a9ee359061bb7d6428ad93'
    old,h,b,z,projected=pickle.loads(mp.read_bytes());ng=json.loads(gp.read_bytes());flashes=json.loads(fp.read_bytes())['vias'];raw='/CORE_1V2'
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
    groups=F.graph(g,raw);index={q['uuid']:i for i,xs in enumerate(groups) for q in xs};source=next(q for q in pads if (q['ref'],q['num'])==('L2001','2'));target=next(q for q in pads if (q['ref'],q['num'])==('U1001','J7'));root=index[source['uuid']]
    via='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92';need={'F.Cu','In3.Cu','In4.Cu'};actual=set(flashes[via]);annular=[]
    from shapely.geometry import Point
    from shapely.ops import unary_union
    v=next(q for q in vias if q['uuid']==via);ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
    rec,trees=F.build(g,nets={raw})
    for layer in sorted(need):
        physical=unary_union([q['shape'] for q in groups[root] if q['layer']==layer and q['kind']!='via']);annular.append({'layer':layer,'actual_flashed':layer in actual,'source_rooted_other_Cu_annular_overlap_mm2':ann.intersection(physical).area})
    # Repeat pad/track/via source membership with the independent integer
    # contact implementation, rather than credit the fast graph's 2 nm glue.
    sys.path.insert(0,str(H/'sbc-power'));import io3_contact_restore_r2 as Q
    Q.NET=raw;exact_groups,exact_parts,exact_assign=Q.groups(g,return_details=True)
    exact_root=next(i for i,xs in enumerate(exact_groups) if any((p['ref'],p['pad'])==('L2001','2') for p in xs))
    exact_source_keys={p['uuid'] for p in exact_groups[exact_root]}
    expected=json.loads((H/'sbc-power/frozen-regional-source-exit-replay-r129/source-scope-checkpoint.json').read_bytes())['joined_pad_keys']
    missing_expected=set(expected)-exact_source_keys
    landing='13ace114-2da3-479c-9c70-bee7d15da004';lv=next(q for q in vias if q['uuid']==landing)
    la=Point(lv['x'],lv['y']).buffer(lv['d']/2,quad_segs=64).difference(Point(lv['x'],lv['y']).buffer(lv['drill']/2,quad_segs=64))
    lphysical=unary_union([q['shape'] for q in groups[root] if q['layer']=='In4.Cu' and q['kind']!='via'])
    landing_overlap=la.intersection(lphysical).area
    okay=index[target['uuid']]==root and index[via]==root and need<=actual and all(q['source_rooted_other_Cu_annular_overlap_mm2']>1e-8 for q in annular) and not missing_expected and landing_overlap>1e-8 and 'In4.Cu' in flashes[landing]
    report={'verdict':'PASS_SELECTED_NATIVE_CORE1V2_SOURCE_PAIR_BARREL_AND_ANNULUS' if okay else 'FAIL_SELECTED_NATIVE_CORE1V2_SOURCE_OR_ANNULUS','candidate_sha256':r['candidate_sha256'],'actual_source':'L2001.2','target':'U1001.J7','actual_source_pad_UUID':source['uuid'],'target_physical_pad_UUID':target['uuid'],'target_same_actual_source_group':index[target['uuid']]==root,'new_barrel_same_actual_source_group':index[via]==root,'required_actual_F_In3_In4_annuli':annular,'native_CORE1V2_pad_count':len(pads),'actual_CORE1V2_groups':len(groups),'actual_source_rooted_named_pads':len({q['uuid'] for q in groups[root] if q['kind']=='pad' and q['pin']}),'pad_binding':'Exact unique ref/pin/native centre plus preserved native footprint UUID chunks and source/API ledger; duplicate physical identities rejected','scope':'Only3 exact CORE1V2 zones freshly filled; complete owned CORE notch and other power proposals excluded. This proves selected source/barrel geometry, not wholeboard or PDN qualification.','whole_board_retained_contacts_DRC_current_and_final_power_composition':'OPEN','input_sha256':{str(p.resolve()):sha(p) for p in (Path(__file__),gp,fp,fill/'receipt.json',mp,mp.with_name('receipt.json'),d/'native-parity.json',d/'construction.json')},'native_jobs':0,'board_written':False,'adopted':False}
    report.update({'independent_exact_integer_source_group':exact_root,'exact_integer_expected25_pad_keys_source_retained':not missing_expected,'missing_expected_exact_pad_keys':sorted(missing_expected),'target_landing_In4_annular_overlap_mm2':landing_overlap,'original_f6_F_In3_actual_masks_retained':{'F.Cu','In3.Cu'}<=actual,'additional_f6_In4_actual_native_flash':('In4.Cu' in actual),'landing_via_actual_In4_flash':('In4.Cu' in flashes[landing]),'exact_no_host_contact_tolerance':True,'complete_current_or_thermal_capability_granted':False})
    out.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':report['verdict'],'groups':len(groups),'rooted_named_pads':report['actual_source_rooted_named_pads'],'annular':annular}),flush=True)
    return 0 if okay else 1
if __name__=='__main__':raise SystemExit(main())
