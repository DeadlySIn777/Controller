"""Independent R44 added Cu versus final prospective old/new zone fills."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.geometry import Point
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'u11015-r44-independent-plane-audit-r47'

def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'u11015-r44-joint-contact-audit-r46';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];h=pickle.loads((bp/'geometry.pkl').read_bytes());assert sha(bp/'groups.pkl')==br['groups_sha256'];groups=pickle.loads((bp/'groups.pkl').read_bytes());rp=HERE/'u11015-reverse-companion-repair-r44';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());rows=[];fails=[]
 zones={l:[] for l in ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']}
 for z in h['zones']:
  for l,rs in z['fills'].items():
   for sh in C.poly(rs):zones[l].append({'uuid':z['uuid'],'raw_net':z['net'],'shape':sh,'domain':h['domains_normalized'][C.norm(z['net'])],'local_clearance_mm':z.get('clearance_mm',.15),'prospective_not_native':z.get('prospective_not_native',False)})
 trees={l:STRtree([z['shape'] for z in zs]) for l,zs in zones.items()}
 for kind,objects in [('via',d['vias']),('segment',d['tracks'])]:
  for q in objects:
   own=[];dom=h['domains_normalized'][C.norm(q['net'])];sh=Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=32) if kind=='via' else C.body(q)
   for l in q['flashed'] if kind=='via' else [q['layer']]:
    for j in trees[l].query(sh.buffer(.626),predicate='intersects'):
     z=zones[l][int(j)]
     if z['raw_net']==q['net']:continue
     required=max(.15 if z['domain']==dom else .6,float(z['local_clearance_mm']))+.025;distance=sh.distance(z['shape'])
     if distance<required-2e-6:own.append({'zone_UUID':z['uuid'],'zone_raw_net':z['raw_net'],'layer':l,'prospective_new_zone':z['prospective_not_native'],'distance_mm':distance,'required_mm':required})
   row={'kind':kind,'uuid':q['uuid'],'raw_net':q['net'],'verdict':'PASS' if not own else 'REJECT','violations':own};rows.append(row);fails+=own
 annrows=[]
 for v in d['vias']:
  pp=Point(v['x'],v['y']);ann=pp.buffer(v['d']/2,quad_segs=32).difference(pp.buffer(v['drill']/2,quad_segs=64));needed=['B.Cu','In3.Cu'] if v['net']=='/motherboard_power_entry/AUX24_A_ILIM' else ['B.Cu','In1.Cu'];net=C.norm(v['net']);rootpin=('U11015','7') if 'ILIM' in v['net'] else ('J11003','2');ri=next(i for i,xs in enumerate(groups[net]) if any(q['kind']=='pad' and(q['ref'],q['pin'])==rootpin for q in xs));root=groups[net][ri]
  contacts=[]
  for l in needed:
   hits=[{'kind':q['kind'],'uuid':q['uuid'],'overlap_mm2':q['shape'].intersection(ann).area} for q in root if q['uuid']!=v['uuid'] and q['layer']==l and q['shape'].intersection(ann).area>.001]
   contacts.append({'layer':l,'source_rooted_other_Cu_contacts':hits,'verdict':'PASS' if hits else 'REJECT'})
  annrows.append({'via_UUID':v['uuid'],'raw_net':v['net'],'required_native_flash':needed,'physical_annular_source_contacts':contacts,'verdict':'PASS' if all(x['verdict']=='PASS' for x in contacts) else 'REJECT'})
 receipt={'verdict':'PASS_PROSPECTIVE_FOREIGN_PLANE_CLEARANCE_AND_REQUIRED_ANNULAR_CONTACTS_NATIVE_PENDING' if not fails and all(x['verdict']=='PASS' for x in annrows) else 'PLANE_OR_ANNULAR_REPAIR_REQUIRED','Cu_rows':rows,'annular_rows':annrows,'input_R46_receipt_sha256':sha(bp/'receipt.json'),'input_R44_receipt_sha256':sha(rp/'receipt.json'),'comparison_uses_all_exact_R32_plus_R44_original_and_proposed_fill_shapes':True,'physical_annulus_excludes_drill':True,'source_layer_contacts_not_inferred_from_barrel_or_equal_sharing':True,'native_jobs':0,'board_written':False,'native_refill_flash_min_thickness_mesh_drop_fault_thermal_gates':'OPEN'};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(receipt['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
