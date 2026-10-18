"""Native-format exact local field copper recipe after R19 host gates."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid
from pathlib import Path
from shapely.geometry import Polygon
from shapely import set_precision
from shapely.strtree import STRtree
from inventory import sha
from verify_source import parse,children,child,atom
from emit_logic_zones_r1 import render,PRIMARY
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'corrected-local-native-recipe-r22'
def main():
 assert not OUT.exists();OUT.mkdir();ap=HERE/'repaired-local-return-audit-r19';ar=json.loads((ap/'receipt.json').read_text());assert ar['verdict']=='PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING';assert sha(ap/'local-owned-discrete.pkl')==ar['local_owned_discrete_sha256'];ds=pickle.loads((ap/'local-owned-discrete.pkl').read_bytes());h=pickle.loads((ap/'discrete.pkl').read_bytes());gg=pickle.loads((ap/'groups.pkl').read_bytes());assert len(ds['vias'])==19 and len(ds['tracks'])==98;zones=[];proofs=[]
 for label,key in[('source-rooted-local-field-returns-r6','proposal_sha256'),('bridged-field-ground-dogbones-r8','proposed_zones_sha256'),('logic-island-repair-r18','proposal_sha256')]:
  bp=HERE/label;r=json.loads((bp/'receipt.json').read_text());assert sha(bp/'proposed-zones.pkl')==r[key];zones+=pickle.loads((bp/'proposed-zones.pkl').read_bytes());proofs.append({'receipt':str((bp/'receipt.json').resolve()),'sha256':sha(bp/'receipt.json')})
 assert len(zones)==52;rawtokens={q['net'] for q in h['pads']};assert all(q['net'] in rawtokens for q in zones+ds['vias']+ds['tracks']);tokens={}
 for q in zones+ds['vias']+ds['tracks']:tokens.setdefault(C.norm(q['net']),set()).add(q['net'])
 assert all(len(v)==1 for v in tokens.values());rows=[];contacts=[];curows=[]
 for q in zones:
  sh=q['shape'];assert set_precision(sh,1e-6).equals(sh);parts=[sh] if sh.geom_type=='Polygon' else list(sh.geoms);parts=sorted(parts,key=lambda p:(-p.area,p.bounds));(OUT/(q['uuid']+'.wkb')).write_bytes(sh.wkb);physical=[r for xs in gg[C.norm(q['net'])] for r in xs if r['kind']!='fill' and r['layer']==q['layer']];tree=STRtree([r['shape'] for r in physical])
  for i,part in enumerate(parts):
   uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'separate-native-outer-'+str(i)));text=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Corrected local field return');path=OUT/(uid+'.zone-chunk');path.write_text(text,encoding='utf-8',newline='\n');ast=parse(text);assert atom(ast,'net')==q['net'] and atom(ast,'uuid')==uid and atom(ast,'layer')==q['layer'] and atom(ast,'priority')=='124';rings=[[(float(v[1]),float(v[2])) for v in child(poly,'pts')[1:]] for poly in children(ast,'polygon')];rt=Polygon(rings[0],rings[1:]);assert rt.is_valid and rt.symmetric_difference(part).area<1e-10;assert C.O.C.pcbtext.chunk_kind(text.encode())=='zone' and C.O.C.pcbtext.chunk_uuid(text.encode())==uid;hits=[]
   for j in tree.query(part,predicate='intersects'):
    r=physical[int(j)];hits.append({k:r[k] for k in('kind','uuid','net','ref','pin','layer') if k in r}|{'Cu_intersection_mm2':r['shape'].intersection(part).area})
   contacts.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_contacts':hits});rows.append({'uuid':uid,'proposal_uuid':q['uuid'],'part_index':i,'raw_net':q['net'],'layer':q['layer'],'area_mm2':part.area,'hole_rings':len(rings)-1,'survives_015mm_detached_interior':not part.buffer(-.075).is_empty,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path),'native_refilled_shape_and_contacts_attested':False})
 for kind,items in[('via',ds['vias']),('segment',ds['tracks'])]:
  for q in items:
   uid=q['uuid'];path=OUT/(uid+'.'+kind+'-chunk')
   if kind=='via':text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],uid)
   else:
    assert q['w']>=.20;text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],q['layer'],q['net'],uid)
   path.write_text(text,encoding='utf-8',newline='');assert C.O.C.pcbtext.chunk_kind(text.encode())==kind and C.O.C.pcbtext.chunk_uuid(text.encode())==uid;ast=parse(text);assert atom(ast,'net')==q['net'];curows.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(zones,protocol=5));(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(ds,protocol=5));(OUT/'physical-contact-ledger.json').write_text(json.dumps(contacts,indent=1)+'\n',encoding='utf-8');source=HERE/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';receipt={'verdict':'FROZEN_CORRECTED_LOCAL_NATIVE_FORMAT_RECIPE_CURRENT_REFILL_PENDING' if all(q['survives_015mm_detached_interior'] for q in rows) else 'NATIVE_MIN_THICKNESS_FRAGMENT_REVIEW_REQUIRED','zone_rows':rows,'discrete_rows':curows,'new_zone_chunks':len(rows),'owned_proposal_shapes':len(zones),'new_vias':19,'new_segments':98,'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'physical_contact_ledger_sha256':sha(OUT/'physical-contact-ledger.json'),'host_full_mutual_aperture_contact_audit_sha256':sha(ap/'receipt.json'),'shape_proofs':proofs,'native_discrete_base_sha256':ar['native_discrete_base_sha256'],'fresh_source_netlist_sha256':sha(source),'priority':124,'local_clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'all_existing_native_discrete_and_old_zone_outline_config_priority_bytes_preserved':True,'supersedes_original_r8_32via_32stub_plus_r9_r11_local_discrete_overlay':True,'existing_via_prospective_flash_obligation':ar['existing_LOGIC_via_extra_flash_required'],'ordinary_all_SMD_and_all_drill_guard_mm':.275,'raw_aliases_introduced':False,'field_remaining_bare_load_ground_groups':8,'new_root_positive24_B5_and_CORE_feeds_still_need_mutual_composition':True,'complete_mesh_current_barrel_thermal_native_refill_gates':'OPEN','native_jobs':0,'board_written':False,'board_adopted':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps({'zones':len(rows),'vias':19,'segments':98,'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
