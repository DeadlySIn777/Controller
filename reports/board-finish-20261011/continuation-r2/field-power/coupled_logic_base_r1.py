"""Bound final r7 projected planes and actual/proposed physical Cu contact graph."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'sbc-power'))
import complete_geometry_r2 as G
import contact_layout as C
import power_groups as P
from shapely.geometry import Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
from inventory import sha
OUT=HERE/'coupled-logic-base-r1'
def build(g,nets=None,layers=None):
    records=defaultdict(list);domain=g['domains_normalized'];actual=json.loads((C.BASE/'continuation-r2/native-198b-geometry/actual-via-flashes.json').read_text(encoding='utf-8'))['vias']
    def add(layer,shape,**r):
        if layers is not None and layer not in layers:return
        if nets is not None and C.norm(r.get('net','')) not in nets:return
        records[layer].append(dict(r,layer=layer,shape=shape,domain=domain.get(C.norm(r.get('net','')))))
    for q in g['pads']:
        for layer,polys in q['layers'].items():
            for sh in C.poly(polys):add(layer,sh,kind='pad',net=q['net'],ref=q['ref'],pin=q['num'],uuid=q['uuid'])
    for t in g['tracks']:add(t['layer'],C.body(t),kind='track',net=t['net'],uuid=t['uuid'],source=t)
    for v in g['vias']:
        # Existing via masks come from the combined native API if supplied;
        # newly proposed vias use explicit expected masks, never an all-layer default.
        mask=v.get('flashed',actual.get(v['uuid']))
        assert mask is not None,('missing explicit via flash mask',v['uuid'])
        provenance='EXISTING_NATIVE_OR_BOUND_NATIVE_MASK' if v['uuid'] in actual else 'EXPLICIT_PROSPECTIVE_MASK_REQUIRES_NATIVE_CHECK'
        for layer in mask:add(layer,Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32),kind='via',net=v['net'],uuid=v['uuid'],source=v,flash_evidence=provenance)
    for z in g['zones']:
        for layer,polys in z['fills'].items():
            for i,sh in enumerate(C.poly(polys)):add(layer,sh,kind='fill',net=z['net'],uuid=z['uuid'],contour=i)
    for q in g['shapes']:
        for sh in C.poly(q['poly']):add(q['layer'],sh,kind='graphic',net=q['net'],uuid=q['uuid'])
    return records,{l:STRtree([r['shape'] for r in rs]) for l,rs in records.items()}
def graph(g,net):
    # The exact original UF logic is retained; only the explicit flash source changes.
    prior=P.build;P.build=build
    try:return P.graph(g,net)
    finally:P.build=prior
def physical_pads(xs):return {(x['ref'],x['pin'],x['uuid']) for x in xs if x['kind']=='pad' and x['pin']}
def pad_summary(xs):
    pp=[x for x in xs if x['kind']=='pad' and x['pin']];sh=unary_union([x['shape'] for x in pp])
    return {'pads':[list(p) for p in sorted(physical_pads(xs))],'pad_count':len(physical_pads(xs)),'pad_bounds_mm':sh.bounds if pp else None,'layers':sorted({x['layer'] for x in xs}),'Cu_item_count':len({P.key(x) for x in xs})}
def main():
    assert not OUT.exists();OUT.mkdir();g,h,tail,binding,z=G.model(final_frozen=True,with_field=True,coupled_revision='r7');hh,retreats=G.projected(g,h,z)
    print('projected',len(hh['pads']),len(hh['vias']),len(hh['tracks']),len(hh['zones']),flush=True)
    raw=pickle.dumps({'old':g,'discrete':h,'projected':hh,'new_zones':z},protocol=5);(OUT/'model.pkl').write_bytes(raw)
    oldgroups=graph(g,'/LOGIC_GND');newgroups=graph(hh,'/LOGIC_GND');membership={p:i for i,xs in enumerate(newgroups) for p in physical_pads(xs)};losses=[]
    for i,xs in enumerate(oldgroups):
        pads=physical_pads(xs)
        if len(pads)<2:continue
        partitions=defaultdict(list)
        for pad in pads:partitions[str(membership.get(pad,'MISSING'))].append(list(pad))
        if len(partitions)>1 or 'MISSING' in partitions:losses.append({'old_group':i,'old_retained_pad_count':len(pads),'new_partitions':{k:sorted(v) for k,v in partitions.items()}})
    rr=[pad_summary(xs)|{'group':i,'contains_external_source':any(x['kind']=='pad' and (x['ref'],x['pin']) in {('J11001','2'),('J11002','2')} for x in xs)} for i,xs in enumerate(newgroups)]
    gg=pickle.dumps({'old_groups':oldgroups,'new_groups':newgroups},protocol=5);(OUT/'groups.pkl').write_bytes(gg)
    receipt={'verdict':'BASE_CONTACT_AUDIT_REPAIR_REQUIRED' if losses else 'PASS','model_file':str((OUT/'model.pkl').resolve()),'model_sha256':sha(OUT/'model.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'coupled_r7_receipt_sha256':sha(HERE.parent/'sbc-power/coupled-power-geometry-frozen-r7/receipt.json'),'combined_parent_binding':binding,'original_logic_pad_groups':sum(bool(physical_pads(x)) for x in oldgroups),'projected_logic_pad_groups':sum(bool(physical_pads(x)) for x in newgroups),'lost_retained_relationships':losses,'new_groups':rr,'old_fill_retreats':retreats,'native_filled_evidence':False,'new_via_flash_status':'EXPLICIT_PROSPECTIVE_MASKS_ONLY; native validation required','root_latest_candidate_metadata':{'path':'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb','sha256':'1beb9a2296ae451daed4b905383ccc5bd3ee083b3400cf5ef2e3ab2e7b7dae6b','not_yet_overlaid':True},'native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':receipt['verdict'],'loss_groups':len(losses),'source_group':[q['group'] for q in rr if q['contains_external_source']],'partitions':[{k:len(v) for k,v in q['new_partitions'].items()} for q in losses],'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
