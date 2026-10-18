"""Read-only exact power wall and retained sense barrel obligations."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'freeze_Q0_exact_gate_sense_PG_scope_r342.py'
code=base.read_text(encoding='utf-8').replace("prefixes=['9963e84b','ff87aa4e','6faa01ce','7b8f7e31','fe8ccdb0']", "prefixes=['7bb3c794','5d069f59','cfc5281b','5a4b7757']").replace('Q0-actual-gate-sense-PG-contact-obligations-r342','Q0-adjacent-power-SENSE-barrel-contact-obligations-r402').replace("'exact_selected_wall_count':5", "'exact_selected_wall_count':4")
exec(compile(code,str(base),'exec'))
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
maskfile=H.parent/'R155-known-reference-native-diagnostic-r157/measure/original-parent-retained-via-actual-flash-masks.json'
masks=json.loads(maskfile.read_text())['retained_original_via_masks']
v=next(x for x in h['vias']if x['uuid']=='5a4b7757-ae7c-470d-81fe-abcec92e0f06')
assert masks[v['uuid']]==['F.Cu','B.Cu']
rec,trees=K.F.build({**h,'zones':[]});pt=Point(v['x'],v['y']);errors=[];checks=[];dom=h['domains_normalized'];net=K.L.norm(v['net'])
for layer in K.LAYERS:
 for j in trees[layer].query(pt.buffer(1.1),predicate='intersects'):
  r=rec[layer][int(j)]
  if r['uuid']==v['uuid']or K.L.norm(r['net'])==net:continue
  req=.15 if dom.get(K.L.norm(r['net']))==dom.get(net)else .6
  if r['kind']=='track'and not r['source'].get('m'):gap=pt.distance(LineString([r['source']['a'],r['source']['b']]))-v['d']/2-r['source']['w']/2
  elif r['kind']=='via':gap=pt.distance(Point(r['source']['x'],r['source']['y']))-v['d']/2-r['source']['d']/2
  else:gap=pt.distance(r['shape'])-v['d']/2
  row={'layer':layer,'other_UUID':r['uuid'],'kind':r['kind'],'raw_net':r['net'],'gap_mm':gap,'native_required_mm':req,'planner_required_mm':req+.025,'actual_original_annulus_present':layer in masks[v['uuid']]};checks.append(row)
  if gap<req+.025:errors.append(row)
put(out/'retained-SENSE-barrel-actual-mask-and-prospective-all6-checks.json',{'original_native_actual_mask_file':str(maskfile),'original_native_actual_mask_sha256':sha(maskfile),'uuid':v['uuid'],'native_actual_layers':masks[v['uuid']],'existing_flags_native_chunk_file':str(out/(v['uuid']+'.original-native-chunk')),'prospective_NEW_In3_or_In2_layer_requires_natural_actual_flash_and_exact_layer_delta':True,'flags_or_original_required_masks_changed':False,'all6_conservative_checks':checks,'all6_conservative_errors':errors,'new_In3_layer_errors':[x for x in errors if x['layer']=='In3.Cu'],'new_In2_layer_errors':[x for x in errors if x['layer']=='In2.Cu'],'native_or_board_jobs':0})
put(out/'supplemental-receipt.json',{'verdict':'READ_ONLY_EXACT_SOURCE_CONTACT_SCOPE_AND_PROSPECTIVE_LAYER_SCREEN','primary_receipt_file':str(out/'receipt.json'),'primary_receipt_sha256':sha(out/'receipt.json'),'mask_screen_file':str(out/'retained-SENSE-barrel-actual-mask-and-prospective-all6-checks.json'),'mask_screen_sha256':sha(out/'retained-SENSE-barrel-actual-mask-and-prospective-all6-checks.json'),'new_In3_layer_error_count':sum(x['layer']=='In3.Cu'for x in errors),'new_In2_layer_error_count':sum(x['layer']=='In2.Cu'for x in errors),'adopted':False})
print(json.dumps({'supplemental_receipt_sha256':sha(out/'supplemental-receipt.json'),'new_In3_layer_errors':[x for x in errors if x['layer']=='In3.Cu'],'new_In2_layer_errors':[x for x in errors if x['layer']=='In2.Cu']}),flush=True)
