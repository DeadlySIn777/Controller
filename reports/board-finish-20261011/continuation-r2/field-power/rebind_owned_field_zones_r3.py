"""Explicit native-discrete antipad update, preserving every old proposal and cut receipt."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
from shapely import set_precision
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import complete_geometry_r2 as G
from inventory import sha
import contact_layout as C
OUT=HERE/'owned-field-zones-native-r3'

def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'native-bound-field-base-r5';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')==br['model_sha256'];m=pickle.loads((bp/'model.pkl').read_bytes());old=pickle.loads((HERE/'coupled-logic-base-r1/model.pkl').read_bytes())['discrete'];h=m['discrete'];changed=set()
    for kind in ('tracks','vias','pads'):
        prior={q['uuid']:q for q in old[kind]};changed|={q['uuid'] for q in h[kind] if q['uuid'] not in prior or q!=prior[q['uuid']]}
    zones=[q for q in m['new_zones'] if C.norm(q['net']) in {'/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'}];assert len(zones)==9
    for label in ('logic-return-repair-r2','field-contact-repair-r2-raw','b5-contact-repair-r3-frozen'):
        b=HERE/label;r=json.loads((b/'receipt.json').read_text());assert sha(b/'proposed-zones.pkl')==r['proposal_sha256'];zones+=pickle.loads((b/'proposed-zones.pkl').read_bytes())
    assert len(zones)==38;cache={};rows=[];result=[]
    for q in zones:
        key=(q['net'],q['layer'])
        if key not in cache:cache[key]=G.foreign_discrete(h,q['net'],q['layer'],changed)
        cutters=cache[key];cut=unary_union([s for _,s in cutters]);shape=set_precision(q['shape'].difference(cut),1e-6);delta=q['shape'].difference(shape);assert shape.difference(q['shape']).area<1e-7
        file=OUT/(q['uuid']+'.wkb');file.write_bytes(shape.wkb);result.append({**q,'shape':shape,'geometry_file':str(file.resolve()),'sha256':sha(file),'net_raw':q['net'],'native_discrete_sha256':br['native_discrete_sha256']});rows.append({'uuid':q['uuid'],'net_raw':q['net'],'layer':q['layer'],'prior_area_mm2':q['shape'].area,'final_area_mm2':shape.area,'explicit_native_changed_Cu_antipad_removed_area_mm2':delta.area,'cutters':[uid for uid,s in cutters if s.intersects(q['shape'])],'geometry_file':str(file.resolve()),'sha256':sha(file),'empty':shape.is_empty})
    assert not any(q['empty'] for q in rows);(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(result,protocol=5));r={'verdict':'EXPLICIT_NATIVE_BOUND_38_SHAPE_ANTIPAD_REBIND_MUTUAL_CONTACT_PENDING','native_discrete_sha256':br['native_discrete_sha256'],'base_receipt_sha256':sha(bp/'receipt.json'),'old_proposal_discrete_sha256':sha(HERE/'coupled-logic-base-r1/model.pkl'),'changed_native_discrete_UUIDs':sorted(changed),'rows':rows,'proposal_sha256':sha(OUT/'proposed-zones.pkl'),'original_frozen_shapes_and_receipts_preserved':True,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print(json.dumps({'native_changed_items':len(changed),'changed_shapes':sum(q['explicit_native_changed_Cu_antipad_removed_area_mm2']>1e-7 for q in rows),'removed_area_mm2':sum(q['explicit_native_changed_Cu_antipad_removed_area_mm2'] for q in rows),'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
