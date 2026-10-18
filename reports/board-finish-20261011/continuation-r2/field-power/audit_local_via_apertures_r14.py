"""Independent root ordinary-via gate: .275mm hole-to-all-SMD Cu, same-net too."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
import contact_layout as C
from inventory import sha
HERE=Path(__file__).resolve().parent;OUT=HERE/'local-via-aperture-audit-r14'
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'complete-local-field-return-contact-audit-r10';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());rp=HERE/'bridged-field-ground-dogbones-r8';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];ds=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());pads=[{'uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'raw_net':q['net'],'layer':l,'shape':unary_union(C.poly(ps))} for q in g['pads'] if q['smd'] for l,ps in q['layers'].items() if l in ('F.Cu','B.Cu')];tree=STRtree([q['shape'] for q in pads]);rows=[]
    for v in ds['vias']:
        point=Point(v['x'],v['y']);hits=[]
        for i in tree.query(point.buffer(v['drill']/2+.30),predicate='intersects'):
            p=pads[int(i)];distance=point.distance(p['shape'])-v['drill']/2
            if distance<.275-1e-7:hits.append({k:w for k,w in p.items() if k!='shape'}|{'actual_circular_drilled_hole_to_SMD_Cu_mm':distance})
        rows.append({'via_uuid':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'verdict':'PASS' if not hits else 'REJECT_ORDINARY_APERTURE','violations':hits})
    receipt={'verdict':'PASS' if all(q['verdict']=='PASS' for q in rows) else 'REJECT_NEW_VIAS_UNTIL_CORRECTED','rows':rows,'required_hole_to_SMD_Cu_mm':.275,'same_net_exception':False,'radius_exact_point_to_polygon_minus_drill_radius':True,'source_r8_receipt_sha256':sha(rp/'receipt.json'),'exact_native_base_contact_receipt_sha256':sha(bp/'receipt.json'),'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'failed_sites':sum(q['verdict']!='PASS' for q in rows),'sites':len(rows),'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
