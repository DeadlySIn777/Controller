"""Selected native trial recipe; emits no board and grants no full-board gate."""
from pathlib import Path
from decimal import Decimal
import hashlib,pickle,json,sys,uuid
from shapely.geometry import Polygon
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
from emit_logic_zones_r1 import render
from verify_source import parse,children,child,atom
O=H/'sbc-power/selected-CORE1V2-native-recipe-r136'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def nm(v):
 x=Decimal(str(v))*1000000;assert x==x.to_integral_value(),v;return int(x)
def ring(r):return [[nm(x),nm(y)] for x,y in list(r.coords)[:-1]]
def main():
 assert not O.exists();O.mkdir()
 sf=H/'sbc-power/frozen-regional-source-exit-replay-r129/accepted-source-scope/receipt.json';assert sha(sf)=='03f79f5b1cad213c90af61747ccbbe6b6c35748d05c1cf04153846324e228513'
 sr=json.loads(sf.read_bytes());qf=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/new-feed-zones.pkl';assert sha(qf)=='0d7fea4cd6f0abf399a2f86ac614554b86bad127a46c51c8a0575ae87b5f7aa5';zs=pickle.loads(qf.read_bytes());assert len(zs)==1
 jf=H/'sbc-power/core1v2-local-outer-join-nominees-r106/proposed-tracks.pkl';assert sha(jf)=='ebce5be3f82d0c2de9bf6ee303d287efa78a9f85bc19358ee5249f01152b3073'
 js=pickle.loads(jf.read_bytes());assert len(js)==1
 flash=H/'sbc-power/core1v2-source-barrel-extra-In4-proposal-r111/extra-flash-obligation.json';assert sha(flash)=='33c16b1ed6c7d3af6e8c16b146c342b6eb54d9b08c333ad3adbd3862c7024f2e'
 fr=json.loads(flash.read_bytes());rows=[];drows=[];components=[]
 for q in zs:
  assert q['net']=='/CORE_1V2' and q['layer']=='In4.Cu'
  sh=q.get('zone_outline_shape',q['shape']);ps=[sh] if sh.geom_type=='Polygon' else list(sh.geoms)
  for i,p in enumerate(sorted(ps,key=lambda x:(-x.area,x.bounds))):
   assert p.geom_type=='Polygon';rings=[ring(p.exterior)]+[ring(r) for r in p.interiors]
   exact=Polygon([(x/1e6,y/1e6) for x,y in rings[0]],[[(x/1e6,y/1e6) for x,y in r] for r in rings[1:]]);assert exact.is_valid and exact.equals(p)
   uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'selected-in4-part-'+str(i)))
   text=render(uid,q['net'],q['layer'],exact).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Selected CORE1V2 regulator source bridge')
   f=O/(uid+'.zone-chunk');f.write_text(text,encoding='utf-8',newline='');a=parse(text)
   rt=[[[nm(float(v[1])),nm(float(v[2]))] for v in child(poly,'pts')[1:]] for poly in children(a,'polygon')];assert rt==rings
   assert atom(a,'net')==q['net'] and atom(a,'uuid')==uid and atom(a,'priority')=='124'
   assert not children(a,'filled_polygon') and not children(a,'fill_segments')
   settings={'priority':124,'local_clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'island_removal_mode':1}
   rows.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'chunk_file':str(f.resolve()),'chunk_sha256':sha(f),'outer_integer_nm':rings[0],'hole_integer_nm':rings[1:],'area_mm2':p.area,'declared_native_settings':settings,'declared_min_thickness_interior_nonempty':not p.buffer(-.075).is_empty})
   components.append({'uuid':uid,'area_mm2':p.area,'min_thickness_interior_survives':not p.buffer(-.075).is_empty,'native_fill_source_root_required':True})
 for q in js:
  assert q['net']=='/CORE_1V2' and q['layer']=='F.Cu' and q['w']==.20
  for pt in (q['a'],q['b']):
   for v in pt:nm(v)
  text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*q['a'],*q['b'],q['w'],json.dumps(q['layer']),json.dumps(q['net']),json.dumps(q['uuid']))
  f=O/(q['uuid']+'.segment-chunk');f.write_text(text,encoding='utf-8',newline='');a=parse(text);assert atom(a,'net')==q['net'] and atom(a,'uuid')==q['uuid']
  drows.append({'kind':'segment','uuid':q['uuid'],'raw_net':q['net'],'geometry':q,'chunk_file':str(f.resolve()),'chunk_sha256':sha(f)})
 receipt={'verdict':'EXACT_SELECTED_CORE1V2_NATIVE_TRIAL_RECIPE_FULL_MUTUAL_GATES_OPEN','parent_native_board_file':str((H/'sbc-native-contract-r1/copy/board.kicad_pcb').resolve()),'parent_native_board_sha256':'eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a','fresh_source_file':str((H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net').resolve()),'fresh_source_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','scoped_host_source_receipt_file':str(sf.resolve()),'scoped_host_source_receipt_sha256':sha(sf),'native_zone_rows':rows,'native_discrete_rows':drows,'native_existing_owned_Cu_delete_rows':[],'native_existing_owned_Cu_replacement_rows':[],'native_existing_owned_footprint_replacement_rows':[],'existing_via_prospective_new_flashes':[{'uuid':fr['via_uuid'],'original_native_flashes':fr['original_actual_native_flash_mask'],'required_after_refill':fr['required_native_postfill_flash_mask'],'same_existing_serialized_via':True,'explicit_ledger_file':str(flash.resolve()),'explicit_ledger_sha256':sha(flash)}],'source_marker':fr['actual_source_marker'],'landing_via_UUID':'13ace114-2da3-479c-9c70-bee7d15da004','new_zone_chunks':len(rows),'new_segments':len(drows),'new_vias':0,'exact_component_screen':components,'native_API_all_Cu_source_actual_source_F_In3_and_In4_flash_ordinary_DRC':'OPEN','scope':'Append only this selected In4 CORE1V2 feed and exact J7 F track to matching-stem frozen eedf clone. Other full-power proposal zones and the owned-new c7 CORE notch are excluded from this trial; it cannot validate complete CORE retention, foreign source/reference continuity or current. Full final candidate must use the complete R129 model and later peer rebases.','full_fitted_CORE1V2_A':.8,'original_native_zone_outlines_settings_and_discrete_bytes_untouched':True,'all_new_coordinates_integer_nm':True,'physical_drill_holes_intentionally_preserved_as_native_zone_holes':'Only source f6 drill void is restored in intended outline by exact R135; physical shape unchanged. Native own drill subtraction mandatory.','wholeboard_current_reference_no_loss_and_native_full_final':'OPEN','native_jobs':0,'board_written':False}
 receipt.update({'exact_source_outline_operation_file':str((H/'sbc-power/CORE1V2-source-native-outline-correction-r135/exact-outline-operation-ledger.json').resolve()),'exact_source_outline_operation_sha256':sha(H/'sbc-power/CORE1V2-source-native-outline-correction-r135/exact-outline-operation-ledger.json'),'corrected_host_model_file':str((H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl').resolve()),'corrected_host_model_sha256':'729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca'})
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('SELECTED_CORE1V2_NATIVE_R136',len(rows),len(drows),sha(O/'receipt.json'),components,flush=True)
if __name__=='__main__':main()
