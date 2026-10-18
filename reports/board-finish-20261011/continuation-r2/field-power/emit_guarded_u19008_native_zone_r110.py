"""Derive current U19008 native zone rings; preserve every R102 Cu operation."""
import pickle,json,uuid
from pathlib import Path
from shapely.geometry import Polygon
from inventory import sha
from verify_source import parse,atom,children,child
from emit_logic_zones_r1 import render
import contact_layout as C
H=Path(__file__).resolve().parent;O=H/'u19008-guarded-native-owned-recipe-r110'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();oldp=H/'u19008-corrected-native-owned-recipe-r102';assert sha(oldp/'receipt.json')=='1d012f2eb0b92b3dac83bab686c1506f1783251a19ff3536f361915f39e29003';r=json.loads((oldp/'receipt.json').read_text());bp=H/'corrected-regulated-joint-search-base-r106';assert sha(bp/'model.pkl')=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39';z=pickle.loads((bp/'model.pkl').read_bytes())[3];q0=pickle.loads((H/'u19008-source-return-reference-r99/proposed-zones.pkl').read_bytes())[0];q=next(x for x in z if x['uuid']==q0['uuid']);(O/'proposed-zones.pkl').write_bytes(pickle.dumps([q],protocol=5));outline=q['zone_outline_shape'];parts=[outline] if outline.geom_type=='Polygon' else sorted([x for x in outline.geoms if x.geom_type=='Polygon'],key=lambda x:(-x.area,x.bounds));rows=[]
 for i,part in enumerate(parts):
  uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'native-outer-'+str(i)));txt=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','U19008 protected-power source return');a=parse(txt);rings=[[(float(v[1]),float(v[2])) for v in child(x,'pts')[1:]] for x in children(a,'polygon')];assert Polygon(rings[0],rings[1:]).symmetric_difference(part).area<1e-10;assert atom(a,'net')==q['net'] and atom(a,'priority')=='124';assert C.O.C.pcbtext.chunk_uuid(txt.encode())==uid;f=O/(uid+'.zone-chunk');f.write_text(txt,encoding='utf-8',newline='');rows.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'part_index':i,'chunk_path':str(f.resolve()),'chunk_sha256':sha(f),'intended_polygon_area_mm2':part.area,'holes':len(rings)-1,'survives_min_015_interior_screen':not part.buffer(-.075).is_empty})
 for k in ('exact_original_deletes','exact_original_replacements','add_rows'):
  for x in r[k]:
   for key,value in x.items():
    if key.endswith('chunk_path'):assert sha(value)==x[key.replace('path','sha256')]
 oldshape=q0['shape'];newshape=q['shape'];r.update({'verdict':'FROZEN_GUARDED_SCOPED_NATIVE_RECIPE_FULL_JOINT_GATES_OPEN','zone_rows':rows,'new_zone_chunks':len(rows),'superseded_R102_recipe_sha256':sha(oldp/'receipt.json'),'exact_R102_original_delete_same_UUID_replacements_and_9_new_Cu_chunks_unchanged':True,'source_R106_host_model_sha256':sha(bp/'model.pkl'),'scoped_independent_R109_receipt_sha256':sha(H/'u19008-corrected-independent-audit-r109/receipt.json'),'current_reference_proposal_sha256':sha(O/'proposed-zones.pkl'),'R99_to_R106_physical_removed_area_mm2':oldshape.difference(newshape).area,'R99_to_R106_physical_added_area_mm2':newshape.difference(oldshape).area,'R99_to_R106_intended_removed_area_mm2':q0['zone_outline_shape'].difference(outline).area,'source_reference_body_full_coverage_scoped_R109':True});write(O/'receipt.json',r);print('R110 frozen',sha(O/'receipt.json'),sha(O/'proposed-zones.pkl'),flush=True)
if __name__=='__main__':main()
