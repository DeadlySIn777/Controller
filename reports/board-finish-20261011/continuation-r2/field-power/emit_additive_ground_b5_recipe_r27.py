"""Freeze native-format R23/R4 additive Cu, preserving intended PTH outlines."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely import set_precision
from shapely.strtree import STRtree
from inventory import sha
from verify_source import parse,children,child,atom
from emit_logic_zones_r1 import render
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'additive-ground-b5-native-recipe-r27'

def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def polys(sh):return[sh] if sh.geom_type=='Polygon' else list(sh.geoms)
def main():
 assert not OUT.exists();OUT.mkdir();ap=HERE/'local-and-b5-return-audit-r25';ar=json.loads((ap/'receipt.json').read_text());assert ar['verdict']=='PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING';assert sha(ap/'discrete.pkl')==ar['discrete_sha256'];h=pickle.loads((ap/'discrete.pkl').read_bytes());assert sha(ap/'groups.pkl')==ar['groups_sha256'];gg=pickle.loads((ap/'groups.pkl').read_bytes());ds={'vias':[],'tracks':[]};zones=[];inputs={}
 for name in('remaining-field-ground-feeds-r23','b5-source-rooted-feeds-r4'):
  bp=HERE/name;r=json.loads((bp/'receipt.json').read_text());assert sha(bp/'proposed-discrete.pkl')==r['proposed_discrete_sha256'];d=pickle.loads((bp/'proposed-discrete.pkl').read_bytes());assert sha(bp/'proposed-zones.pkl')==r['proposed_zones_sha256'];ds['vias']+=d['vias'];ds['tracks']+=d['tracks'];zones+=pickle.loads((bp/'proposed-zones.pkl').read_bytes());inputs[name]=sha(bp/'receipt.json')
 assert len(zones)==5 and len(ds['vias'])==6 and len(ds['tracks'])==10;rawtokens={q['net'] for q in h['pads']};assert all(q['net'] in rawtokens for q in zones+ds['vias']+ds['tracks']);tokens={}
 for q in zones+ds['vias']+ds['tracks']:tokens.setdefault(C.norm(q['net']),set()).add(q['net'])
 assert all(len(v)==1 for v in tokens.values());rows=[];contacts=[];curows=[]
 for q in zones:
  physical=q['shape'];outline=q['zone_outline_shape'];assert set_precision(physical,1e-6).equals(physical) and set_precision(outline,1e-6).equals(outline);assert outline.buffer(.000002).covers(physical);(OUT/(q['uuid']+'.physical.wkb')).write_bytes(physical.wkb);(OUT/(q['uuid']+'.intended.wkb')).write_bytes(outline.wkb)
  physicalcontacts=[r for xs in gg[C.norm(q['net'])] for r in xs if r['kind']!='fill' and r['layer']==q['layer']];tree=STRtree([r['shape'] for r in physicalcontacts])
  for i,part in enumerate(sorted(polys(outline),key=lambda x:(-x.area,x.bounds))):
   uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'separate-native-outer-'+str(i)));text=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Additive field ground and B5 feed');path=OUT/(uid+'.zone-chunk');path.write_text(text,encoding='utf-8',newline='\n');ast=parse(text);assert atom(ast,'net')==q['net'] and atom(ast,'uuid')==uid and atom(ast,'layer')==q['layer'] and atom(ast,'priority')=='124';rings=[[(float(v[1]),float(v[2])) for v in child(poly,'pts')[1:]] for poly in children(ast,'polygon')];rt=Polygon(rings[0],rings[1:]);assert rt.is_valid and rt.symmetric_difference(part).area<1e-10;assert C.O.C.pcbtext.chunk_kind(text.encode())=='zone' and C.O.C.pcbtext.chunk_uuid(text.encode())==uid
   ep=physical.intersection(part);hits=[]
   for j in tree.query(ep,predicate='intersects'):
    r=physicalcontacts[int(j)];overlap=r['shape'].intersection(ep).area
    if overlap>1e-10:hits.append({k:r[k] for k in('kind','uuid','net','ref','pin','layer') if k in r}|{'physical_Cu_intersection_mm2':overlap})
   contacts.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_contacts':hits});rows.append({'uuid':uid,'proposal_uuid':q['uuid'],'part_index':i,'raw_net':q['net'],'layer':q['layer'],'intended_outline_area_mm2':part.area,'effective_physical_Cu_area_mm2':ep.area,'drill_subtracted_area_mm2':part.area-ep.area,'hole_rings':len(rings)-1,'survives_015mm_detached_interior':not part.buffer(-.075).is_empty,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path),'effective_physical_WKB_sha256':sha(OUT/(q['uuid']+'.physical.wkb')),'intended_outline_WKB_sha256':sha(OUT/(q['uuid']+'.intended.wkb')),'native_refilled_shape_and_contacts_attested':False})
 required=[]
 for v in ds['vias']:
  ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64));zl={q['layer'] for q in zones if q['net']==v['net'] and q['shape'].intersection(ann).area>.001};tl={t['layer'] for t in ds['tracks'] if t['net']==v['net'] and C.body(t).intersection(ann).area>.001};assert zl and tl;required.append({'uuid':v['uuid'],'net_raw':v['net'],'outer_stub_layers':sorted(tl),'source_bridge_layers':sorted(zl),'required_native_postfill_flash':sorted(tl|zl),'planning_all_layer_annuli_are_not_native_flash_proof':True})
 for kind,items in[('via',ds['vias']),('segment',ds['tracks'])]:
  for q in items:
   uid=q['uuid'];path=OUT/(uid+'.'+kind+'-chunk')
   if kind=='via':text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],uid)
   else:
    assert q['w']>=.20;text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],q['layer'],q['net'],uid)
   path.write_text(text,encoding='utf-8',newline='');assert C.O.C.pcbtext.chunk_kind(text.encode())==kind and C.O.C.pcbtext.chunk_uuid(text.encode())==uid;assert atom(parse(text),'net')==q['net'];curows.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(zones,protocol=5));(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(ds,protocol=5));write(OUT/'physical-contact-ledger.json',contacts);write(OUT/'native-flash-obligations.json',required);source=HERE/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 write(OUT/'receipt.json',{'verdict':'FROZEN_ADDITIVE_GROUND_B5_NATIVE_FORMAT_RECIPE_CURRENT_REFILL_PENDING' if all(q['survives_015mm_detached_interior'] for q in rows) else 'NATIVE_MIN_THICKNESS_FRAGMENT_REVIEW_REQUIRED','zone_rows':rows,'discrete_rows':curows,'new_zone_chunks':len(rows),'owned_proposal_shapes':len(zones),'new_vias':6,'new_segments':10,'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'physical_contact_ledger_sha256':sha(OUT/'physical-contact-ledger.json'),'flash_obligations_sha256':sha(OUT/'native-flash-obligations.json'),'host_full_mutual_aperture_contact_audit_sha256':sha(ap/'receipt.json'),'constructive_input_receipt_SHA256s':inputs,'native_discrete_base_sha256':ar['native_discrete_base_sha256'],'fresh_source_netlist_sha256':sha(source),'priority':124,'local_clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'intended_outline_spans_own_PTH_holes_physical_current_model_subtracts_drills':True,'B5_r4_source_escape_In3_seed_label_superseded_by_actual_F_In4_flash_requirement':True,'all_existing_native_discrete_and_old_zone_outline_config_priority_bytes_preserved':True,'supersedes_no_previous_native_accepted_discrete':True,'ordinary_all_SMD_and_all_drill_guard_mm':.275,'raw_aliases_introduced':False,'field_remaining_bare_load_ground_groups':6,'complete_mesh_current_barrel_thermal_native_refill_gates':'OPEN','native_jobs':0,'board_written':False,'board_adopted':False});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
