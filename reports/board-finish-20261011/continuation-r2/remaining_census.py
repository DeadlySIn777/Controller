"""Classify the current native missing joins without changing a design."""
import collections,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
PATHS={'partitions':BASE/'measure/r07-four-fag-shared/partitions.json','controlled':Path('Z:/pcb-runs/impedance/controlled-nets.json'),'historical_power_width_inventory':BASE/'power-audit/constraint-snapshot/1-power_widths.json','field_rail_role_inventory':BASE/'power-audit/constraint-snapshot/0-field_pdn_spec.json'}
def norm(n):return n.replace('{slash}','/')
def main():
    raw={k:p.read_bytes() for k,p in PATHS.items()};d={k:json.loads(v) for k,v in raw.items()}
    if d['partitions']['sha256']!='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab':raise ValueError('Wrong native candidate')
    ctrl={norm(n):r for n,r in d['controlled']['nets'].items()};power={norm(n) for n in d['historical_power_width_inventory']}
    power.update(norm(r['net']) for r in d['field_rail_role_inventory']['rails'])
    # Exact existing source rail names; classification only, no capacity inference.
    power.update(['/LOGIC_GND','/IO_3V3','/CORE_1V2','/motherboard_analog_output/AO0_COM','/motherboard_analog_output/AO1_COM','/motherboard_comms/CAN_GND','/motherboard_comms/RS485_COM','/motherboard_analog_input/AI_AGND','/motherboard_do/DOA_FIELD_3V3','/motherboard_do/DOB_FIELD_3V3','/motherboard_comms/CM_AUX_3V3'])
    rows=[];counts=collections.defaultdict(lambda:{'nets':0,'joins':0})
    for net,groups in d['partitions']['nets'].items():
        if len(groups)<2:continue
        n=norm(net);c=ctrl.get(n);active=bool(c and any(p.get('pintype') in ('input','output','bidirectional','open_collector','open_emitter','tri_state') for p in c.get('end_parts',[])))
        if n in power:kind='power_or_return_inventory'
        elif c and c.get('class')!='NONE':kind='controlled_impedance'
        elif 'motherboard_analog_' in n:kind='analog_review'
        elif c and active:kind='ordinary_digital_catalog'
        elif c:kind='passive_or_external_catalog'
        else:kind='unclassified_ROOT106'
        row={'net':net,'normalized_net':n,'category':kind,'groups':len(groups),'missing_joins':len(groups)-1,'pads':sum(map(len,groups)),'controlled_class':c.get('class') if c else None,'native_groups':groups}
        rows.append(row);counts[kind]['nets']+=1;counts[kind]['joins']+=len(groups)-1
    total=sum(r['missing_joins'] for r in rows)
    if total!=d['partitions']['pad_island_joins']:raise ValueError('Census total does not reproduce native')
    target=HERE/'remaining-net-census-r2.json'
    if target.exists():raise ValueError('Existing census')
    result={'board_sha256':d['partitions']['sha256'],'missing_pad_joins':total,'incomplete_nets':len(rows),'categories':dict(counts),'rows':sorted(rows,key=lambda r:(-r['missing_joins'],r['net'])),'inputs':{k:{'path':str(PATHS[k]),'sha256':hashlib.sha256(v).hexdigest()} for k,v in raw.items()},'historical_catalog_limit':'ROOT104 catalog is a classification aid; every proposed ROOT106 route needs current source/net-policy review. Historical power width values are not reused for current sizing.','native_jobs':0,'board_edits':0,'adopted':False,'manufacturing_ready':False}
    target.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'joins':total,'nets':len(rows),'categories':dict(counts),'top':[{k:v for k,v in r.items() if k!='native_groups'} for r in result['rows'][:8]]}))
if __name__=='__main__':main()
