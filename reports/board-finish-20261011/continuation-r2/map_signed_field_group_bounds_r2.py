"""Map signed planning ports onto the independently audited r15 physical groups.

Bounds are coupled simplex ranges, not a resistance solution or simultaneous
independent maxima. Distinct RTN nets keep their separate physical obligations.
"""
import collections,hashlib,json,math,pickle
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'field-signed-group-bounds-r2-r25'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return s.replace('{slash}','/')
def main():
    if OUT.exists():raise ValueError('Fresh physical current group map required')
    allocation=H/'field-signed-port-allocation-r4/receipt.json';a=json.loads(allocation.read_bytes())
    contact=H/'field-power/local-and-b5-return-audit-r25';cr=json.loads((contact/'receipt.json').read_bytes())
    if a['unresolved_endpoint_terms'] or not a['verdict'].startswith('PASS_SIGNED_') or not cr['verdict'].startswith('PASS_'):raise ValueError('Frozen endpoint/contact gate rejected')
    if sha(contact/'groups.pkl')!=cr['groups_sha256']:raise ValueError('Frozen exact physical groups changed')
    gs=pickle.loads((contact/'groups.pkl').read_bytes());rows=[];unmapped=[]
    for domain,net,root in [('FA','/motherboard_motors/FIELD_GND','J11003'),('FB','/motherboard_do/FIELD_B_0V','J11005')]:
        groups=gs[net];index={q['uuid']:i for i,xs in enumerate(groups) for q in xs if q['kind']=='pad'}
        rootids={i for i,xs in enumerate(groups) for q in xs if q['kind']=='pad' and (q['ref'],q['pin'])==(root,'2')}
        if len(rootids)!=1:raise ValueError('Actual physical source not unique')
        rootid=next(iter(rootids));terms=[t for t in a['terms'] if t['domain']==domain]
        for t in terms:
            for e in t['eligible_physical_endpoints']:
                if norm(e['raw_net'])==net and e['physical_pad_uuid'] not in index:raise ValueError('Exact ground port is absent from physical contact graph')
                if norm(e['raw_net'])!=net:unmapped.append({'term':t['name'],'domain':domain,'raw_net':e['raw_net'],'physical_pad_uuid':e['physical_pad_uuid'],'ref':e['ref'],'pin':e['pin'],'reason':'Distinct actual RTN net; internal/source support path qualification remains required, never collapsed onto GND'})
        group_rows=[]
        for i,xs in enumerate(groups):
            pads=sorted({(q['ref'],q['pin'],q['uuid']) for q in xs if q['kind']=='pad' and q['pin']})
            if not pads:continue
            impacts=[]
            for t in terms:
                ee=t['eligible_physical_endpoints'];hits=[e for e in ee if norm(e['raw_net'])==net and index.get(e['physical_pad_uuid'])==i]
                if not hits:continue
                all_here=len(hits)==len(ee);v=t['signed_current_a']
                lo=hi=v if all_here else 0
                if not all_here:lo=min(v,0);hi=max(v,0)
                impacts.append({'term':t['name'],'kind':t['kind'],'conserved_signed_total_a':v,'signed_injection_min_a':lo,'signed_injection_max_a':hi,'all_eligible_physical_ports_in_this_group':all_here,'eligible_ports_in_this_group':[{'ref':e['ref'],'pin':e['pin'],'physical_pad_uuid':e['physical_pad_uuid'],'raw_net':e['raw_net']} for e in hits],'eligible_ports_total':len(ee)})
            lower=math.fsum(t['signed_injection_min_a'] for t in impacts);upper=math.fsum(t['signed_injection_max_a'] for t in impacts)
            group_rows.append({'group':i,'actual_source_group':i==rootid,'physical_pad_identities':[list(p) for p in pads],'signed_nodal_injection_range_a':[lower,upper],'conservative_single_group_return_cut_magnitude_a':max(abs(lower),abs(upper)),'positive_load_injection_upper_a':math.fsum(max(t['signed_injection_max_a'],0) for t in impacts),'negative_port_injection_lower_a':math.fsum(min(t['signed_injection_min_a'],0) for t in impacts),'term_impacts':impacts,'DC_capacitors_without_explicit_leak_term':'No fictitious DC current; startup/ripple/fault loop current still open'})
        rows.append({'domain':domain,'actual_raw_ground_net':next(t['eligible_physical_endpoints'][0]['raw_net'] for t in terms if t['kind']=='source_sink'),'source':root+'.2','source_group':rootid,'named_pad_groups':len(group_rows),'groups':group_rows})
    OUT.mkdir();report={'verdict':'PASS_EXACT_PHYSICAL_GROUP_SIGNED_SIMPLEX_PLANNING_BOUNDS_MESH_OPEN','rows':rows,'distinct_RTN_physical_ports_with_path_qualification_open':unmapped,'endpoint_receipt_sha256':sha(allocation),'contact_receipt_sha256':sha(contact/'receipt.json'),'groups_sha256':sha(contact/'groups.pkl'),'native_discrete_sha256':cr['native_discrete_base_sha256'],'corrected_local_R25_and_B5_included':True,'later_CORE_protected_and_signal_wall_recipes_excluded':True,'individual_group_extrema_cannot_be_summed_as_simultaneous_independent_loads':True,'no_equal_pad_sharing':True,'source_KCL_for_all146_terms_preserved_in_endpoint_receipt':True,'actual_current_redistribution_and_mesh_barrel_drop_thermal':'OPEN','native_jobs':0,'board_or_source_written':False,'adopted':False,'read_files_sha256':{str(p.resolve()):sha(p) for p in (allocation,contact/'receipt.json',contact/'groups.pkl',Path(__file__))}}
    (OUT/'receipt.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    for row in rows:
        required=[g for g in row['groups'] if not g['actual_source_group']]
        print(json.dumps({'domain':row['domain'],'named_groups':row['named_pad_groups'],'unrooted_groups':len(required),'largest_unrooted_branch_bound_a':max(g['conservative_single_group_return_cut_magnitude_a'] for g in required),'distinct_RTN_ports_open':len([e for e in unmapped if e['domain']==row['domain']])}),flush=True)
if __name__=='__main__':main()
