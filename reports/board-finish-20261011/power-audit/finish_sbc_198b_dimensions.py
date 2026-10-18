"""Read-only final pooled18via dimension/pitch/hole/copper arithmetic gate."""
import copy,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'sbc-198b-source-proposal'
V3=OUT/'final-bounded-blocker-v3.json';RAW=OUT/'tapered-hub-prerequisites.json';PACK=OUT/'bounded-five-part-fanout-proposal.json'
PRO=HERE.parent/'measure/r07-four-fag-shared/copy/board.kicad_pro';DRU=PRO.with_suffix('.kicad_dru');DEST=OUT/'final-bounded-blocker-v4.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pooled_check(arrays,dimensions=(.6,.3)):
    diameter,drill=dimensions
    if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in dimensions) or diameter<.5 or drill<.3 or (diameter-drill)/2<.15-1e-9:return {'accept':False,'reason':'ordinary power via dimensions/annulus'}
    if len(arrays)!=2 or any(len(a)!=9 for a in arrays):return {'accept':False,'reason':'two exact nine-site arrays required'}
    pts=[{'role':role,'index':i,'at':pt,'diameter_mm':diameter,'drill_mm':drill} for role,a in zip(('source','load'),arrays) for i,pt in enumerate(a)]
    if any(len(p['at'])!=2 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in p['at']) for p in pts):return {'accept':False,'reason':'invalid site'}
    rows=[]
    for i,a in enumerate(pts):
        for b in pts[i+1:]:
            center=math.dist(a['at'],b['at']);copper=center-(a['diameter_mm']+b['diameter_mm'])/2;holes=center-(a['drill_mm']+b['drill_mm'])/2
            hc_ab=center-(a['drill_mm']+b['diameter_mm'])/2;hc_ba=center-(b['drill_mm']+a['diameter_mm'])/2
            okay=center>=.8-1e-9 and copper>=.15+.025-1e-9 and holes>=.25+.025-1e-9 and min(hc_ab,hc_ba)>=.25+.025-1e-9
            rows.append({'a':a,'b':b,'center_mm':center,'copper_edge_gap_mm':copper,'drill_edge_gap_mm':holes,
                'drill_a_to_copper_b_mm':hc_ab,'drill_b_to_copper_a_mm':hc_ba,'accept':okay})
    return {'accept':all(r['accept'] for r in rows),'distinct_sites':len(pts),'pairs_checked':len(rows),
        'minimum_center_pair_witness':min(rows,key=lambda r:r['center_mm']),'failed_pairs':[r for r in rows if not r['accept']]}
def main():
    if DEST.exists():raise ValueError('new immutable receipt required')
    files=(V3,RAW,PACK,PRO,DRU,Path(__file__));before={str(p.resolve()):sha(p) for p in files}
    prior=json.loads(V3.read_bytes());raw=json.loads(RAW.read_bytes());pack=json.loads(PACK.read_bytes())
    for path,expected in prior['source_sha256_before'].items():
        if sha(path)!=expected:raise ValueError('frozen previous input changed')
        before[path]=expected
    if not prior['board_sha256']==raw['board_sha256']==pack['board_sha256']:raise ValueError('native identity differs')
    if any(row['via_mm']!=[.6,.3] for row in pack['array_necessary_conditions_even_if_pose_withheld']):raise ValueError('actual prospective power via dimensions differ')
    rules=json.loads(PRO.read_bytes())['board']['design_settings']['rules'];dru=DRU.read_text()
    if rules['min_hole_to_hole']!=.25 or rules['min_hole_clearance']!=.25 or rules['min_via_diameter']!=.5 or '(constraint annular_width (min 0.15mm))' not in dru:raise ValueError('native minima differ')
    a=[[x*.8,0.] for x in range(9)];b=[[x*.8,2.] for x in range(9)]
    tests=[]
    for name,arrays,dims,expect in (('valid eighteen ordinary power sites',[a,b],(.6,.3),True),
        ('two internally legal arrays with cross pair.4',[a,[[0.,.4]]+b[1:]],(.6,.3),False),
        ('larger copper violates edge gap at legalpitch',[a,b],(.8,.3),False),
        ('larger drill violates hole gap at legalpitch',[a,b],(1.,.6),False),
        ('insufficient annulus',[a,b],(.5,.3),False),
        ('exact.8crossboundary',[a,[[0.,.8]]+b[1:]],(.6,.3),True)):
        check=pooled_check(arrays,dims)
        if check['accept']!=expect:raise ValueError('pooled dimension control failed: '+name)
        tests.append({'name':name,'expected_accept':expect,'actual_accept':check['accept']})
    result=copy.deepcopy(prior);result['schema']='exact198b-final-one-bounded-SBC-source-proposal-blocker-v4'
    checks=[]
    for screen in raw['screens']:
        for i,lead in enumerate(screen['at_most_two_hub_choice_geometry_leads']):
            arrays=[[row['via'] for row in ar['branches']] for ar in lead['arrays']];check=pooled_check(arrays)
            check.update(net=screen['net'],layer=screen['layer'],raw_lead_index=i);checks.append(check)
            match=next(r for r in result['actual_trunk_branch_paths'] if r['net']==screen['net'] and r['layer']==screen['layer'] and r['raw_lead_index']==i)
            match['pooled_dimensions_pitch_hole_copper_accept']=check['accept'];match['geometry_accept_only']=match['geometry_accept_only'] and check['accept']
    result['all_eighteen_prospective_vias_pooled_dimension_checks']=checks
    result['pooled_dimension_controls']=tests
    result['prospective_power_via_dimensions_mm']=[.6,.3]
    result['pooled_spacing_contract_mm']={'ordinary_center_pitch':.8,'copper_edge_conservative_planner_min':.15,'hole_to_hole_min':.25,'hole_to_other_copper_conservative_planner_min':.25,'margin':.025,
        'native_context':'sameSBCnet pooledarray; native minhole-to-hole/minhole-clearance.25 retained, customordinaryannulus.15 retained; conservativeCu.15planner spacing is stronger than relying on same-net electrical clearances; no dense/vippo exception'}
    result['bounded_trunk_findings']['independent_geometry_accepted_output_leads']=sum(r['geometry_accept_only'] for r in result['actual_trunk_branch_paths'])
    result['route_gate_and_spacing_and_dimension_control_count']=len(result['raw_route_gate_controls'])+len(result['whole_array_spacing_controls'])+len(tests)
    result['source_sha256_before']=before;result['source_sha256_after']={p:sha(p) for p in before}
    if before!=result['source_sha256_after']:raise ValueError('inputs changed')
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(DEST),'sha256':sha(DEST),'controls':result['route_gate_and_spacing_and_dimension_control_count'],
        'path_count':result['actual_checked_paths'],'pooled_checks':[{'lead':c['raw_lead_index'],'accept':c['accept'],'pairs':c['pairs_checked'],'minimum':c['minimum_center_pair_witness']} for c in checks],
        'qualified_power':False,'board_emitted':False}))
if __name__=='__main__':main()
