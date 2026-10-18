"""Conserved planning-current cut bounds on an exact completed power model.

Removing a barrel is only a graph diagnostic. It does not predict sharing,
resistance, thermal rise, transients or the current in a non-dominating barrel.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,math,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
    assert len(sys.argv)==3,'completed_model.pkl fresh_output_directory'
    mp,out=map(lambda x:Path(x).resolve(),sys.argv[1:]);assert mp.is_relative_to(H) and out.is_relative_to(H) and not out.exists()
    mr=json.loads(mp.with_name('receipt.json').read_bytes());assert sha(mp)==mr['model_sha256']
    ap=H/'protected24-port-allocation-r1/receipt.json';a=json.loads(ap.read_bytes())
    assert a['verdict']=='PASS_PROTECTED24_PLANNING_KCL_EXACT_NATIVE_ENDPOINTS_CURRENT_MESH_OPEN'
    assert all(abs(x)<1e-12 for x in a['KCL_residual_a'].values())
    rp=H/'protected24-dogbones-r7';r=json.loads((rp/'receipt.json').read_bytes())
    assert sha(rp/'proposed-discrete.pkl')==r['proposed_discrete_sha256']
    new=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());old,h,b,z,current=pickle.loads(mp.read_bytes())
    allpads={p['uuid']:p for p in current['pads']};vias={v['uuid']:v for v in h['vias']}
    for t in a['terms']:
        for e in t['eligible_physical_endpoints']:
            p=allpads[e['physical_pad_uuid']];assert p['net']==e['raw_net'] and (p['ref'],p['num'])==(e['ref'],e['pin'])
    out.mkdir();rows=[]
    for domain,ref in [('FA','U11004'),('FB','U11006')]:
        net='/motherboard_power_entry/FIELD_'+domain[-1]+'_24V_PROTECTED'
        groups=F.graph(current,net);root=next(xs for xs in groups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'17') for q in xs))
        rootpads={q['uuid'] for q in root if q['kind']=='pad'}
        for v in [v for v in new['vias'] if C.norm(v['net'])==net]:
            assert v==vias[v['uuid']] and any(q['kind']=='via' and q['uuid']==v['uuid'] for q in root),'Feed barrel is not actual-source-rooted'
            cut={**current,'vias':[w for w in current['vias'] if w['uuid']!=v['uuid']]}
            cutgroups=F.graph(cut,net);sr=next(xs for xs in cutgroups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'17') for q in xs))
            remaining={q['uuid'] for q in sr if q['kind']=='pad'};detached=rootpads-remaining
            impacts=[]
            for t in [t for t in a['terms'] if t['domain']==domain]:
                ports={e['physical_pad_uuid'] for e in t['eligible_physical_endpoints']};hit=ports&detached
                if not hit:continue
                value=t['signed_supply_current_a'];lo=hi=value if hit==ports else 0.
                if hit!=ports:lo,hi=min(value,0.),max(value,0.)
                impacts.append({'term':t['name'],'conserved_signed_total_a':value,'signed_detached_injection_interval_a':[lo,hi],'detached_exact_physical_ports':sorted(hit),'all_term_ports_detached':hit==ports})
            lo=math.fsum(t['signed_detached_injection_interval_a'][0] for t in impacts);hi=math.fsum(t['signed_detached_injection_interval_a'][1] for t in impacts)
            row={'domain':domain,'barrel_uuid':v['uuid'],'barrel_diameter_drill_mm':[v['d'],v['drill']],'actual_source':ref+'.17','detached_originally_source_rooted_pad_UUIDs':sorted(detached),'single_barrel_graph_cut':bool(detached),'signed_detached_injection_interval_a':[lo,hi],'conditional_single_cut_current_magnitude_bound_a':max(abs(lo),abs(hi)) if detached else None,'non_dominating_barrel_current':'UNSOLVED; no zero-current inference' if not detached else None,'term_impacts':impacts}
            rows.append(row);write(out/'checkpoint.json',rows);print(json.dumps({'domain':domain,'barrel_uuid':v['uuid'],'detached_pads':len(detached),'bound_A':row['conditional_single_cut_current_magnitude_bound_a']}),flush=True)
    write(out/'receipt.json',{'verdict':'PLANNING_EXACT_SOURCE_PORT_SINGLE_BARREL_CUT_BOUNDS_MESH_NATIVE_CURRENT_OPEN','rows':rows,'model_sha256':sha(mp),'input_sha256':{str(p.resolve()):sha(p) for p in (Path(__file__),mp,mp.with_name('receipt.json'),ap,rp/'receipt.json',rp/'proposed-discrete.pkl',Path(F.__file__),Path(C.__file__))},'full_fitted_normal_current_and_KCL_preserved':True,'sharing':'Coupled simplex endpoint weights; no equal division and no sum of independent maxima as one operating case','barrel_sheet_package_neck_drop_thermal_ripple_startup_fault_current':'OPEN','native_jobs':0,'source_or_board_written':False,'adopted':False})
if __name__=='__main__':main()
