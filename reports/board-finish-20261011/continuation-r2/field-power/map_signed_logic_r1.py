"""Map conserved signed logical scenarios to every distinct native physical pad."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from collections import defaultdict
from inventory import sha
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'signed-logic-physical-allocation-r1'
def main():
    assert not OUT.exists();OUT.mkdir();sp=HERE.parent/'sbc-power/signed-return-scenarios-r1.json';assert sha(sp)=='e1b14aeafe8802907ae92cd5ceb8c0c9ad42bf7beaf343d6c3886cdc1da165af';s=json.loads(sp.read_text());base=HERE/'coupled-logic-base-r1';b=json.loads((base/'receipt.json').read_text());assert sha(base/'model.pkl')==b['model_sha256'];h=pickle.loads((base/'model.pkl').read_bytes())['projected'];assert sha(base/'groups.pkl')==b['groups_sha256'];groups=pickle.loads((base/'groups.pkl').read_bytes())['new_groups'];membership={q['uuid']:i for i,xs in enumerate(groups) for q in xs if q['kind']=='pad'};pads=defaultdict(list)
    for q in h['pads']:
        if C.norm(q['net'])=='/LOGIC_GND':pads[q['ref'],q['num']].append(q)
    rows=[];missing=[];stress=defaultdict(lambda:{'maximum_positive_injection_a':0.,'maximum_negative_extraction_a':0.,'applicable_signed_groups':[]})
    for j,gg in enumerate(s['groups']):
        endpoints=[];covered=set()
        for node in gg['ground_node_candidates']:
            qs=pads[node['ref'],node['pin']]
            if not qs:missing.append({'group':gg['label'],'logical_node':node})
            for q in qs:
                gi=membership[q['uuid']];covered.add(gi);endpoints.append({'ref':q['ref'],'pin':q['num'],'physical_pad_uuid':q['uuid'],'at_mm':[q['x'],q['y']],'net_raw':q['net'],'actual_native_or_bound_pad_flash_layers':sorted(q['layers']),'r7_ground_group':gi,'hole_present':bool(q.get('hole'))})
        for gi in covered:
            if gg['signed_total_a']>=0:stress[gi]['maximum_positive_injection_a']+=gg['signed_total_a']
            else:stress[gi]['maximum_negative_extraction_a']+=abs(gg['signed_total_a'])
            stress[gi]['applicable_signed_groups'].append({'label':gg['label'],'signed_total_a':gg['signed_total_a']})
        rows.append({'label':gg['label'],'signed_total_a':gg['signed_total_a'],'within_group_distribution':gg['within_group_distribution'],'distinct_physical_endpoints':endpoints,'covered_r7_ground_groups':sorted(covered),'simplex_allocation_not_equal_sharing':True})
    receipt={'verdict':'EXACT_PHYSICAL_ENDPOINT_MAPPING' if not missing else 'MISSING_PHYSICAL_ENDPOINTS','signed_receipt_sha256':sha(sp),'source_export_sha256':s['source_sha256'],'coupled_base_receipt_sha256':sha(base/'receipt.json'),'groups':rows,'partition_stress_envelopes':dict(stress),'missing_logical_endpoints':missing,'signed_group_sum_a':sum(q['signed_total_a'] for q in rows),'source_J11001_2_only':True,'J11002_shutdown_ground_current_a':0.,'envelope_explanation':'Each group independently assigns its full signed magnitude to any eligible physical endpoint. For a partition, its positive or negative extrema are sums of eligible groups, a conservative stress envelope; extrema across partitions are not simultaneous invented extra load. Internal within-pin physical-pad sharing and device-pin current limits remain physical qualification obligations.','all_ordinary_capacitor_DC_injections_zero':True,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'verdict':receipt['verdict'],'missing':len(missing),'stress':{k:{q:v for q,v in vv.items() if q!='applicable_signed_groups'} for k,vv in stress.items()},'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
