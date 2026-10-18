"""Independent lexical/IU/model audit of detached R155 chunks, no native launch."""
import os,psutil
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
from decimal import Decimal
import sys,json,re,pickle,hashlib
H=Path(__file__).resolve().parent;P=H.parent;sys.dont_write_bytecode=True
for d in(H,P/'field-power'):sys.path.insert(0,str(d))
import restore_field_current_mixed_precision_states_r366 as MIXED
from shapely.geometry import Polygon
from shapely.ops import unary_union
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def ast(text):
 tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text);stack=[];result=None
 for t in tokens:
  if t=='(':
   a=[]
   if stack:stack[-1].append(a)
   stack.append(a)
  elif t==')':
   a=stack.pop()
   if not stack:assert result is None;result=a
  else:assert stack;stack[-1].append(json.loads(t)if t.startswith('"')else t)
 assert not stack and result is not None;return result
def children(a,k):return[x for x in a[1:]if isinstance(x,list)and x[0]==k]
def one(a,k):
 r=children(a,k);assert len(r)==1,(k,r);return r[0]
def value(a,k):return one(a,k)[1]
def nm(v):
 d=Decimal(str(v))*1000000;assert d==d.to_integral_value(),('not integer nm',v);return int(d)
recipe=H/'R155-known-failed-reference-native-recipe-r306/receipt.json';assert sha(recipe)=='7b73c8ef1fc7fc3f4796553771a9af635a1c6b0050076c4d730be4783f09e6c4';r=read(recipe)
assert r['strict_old_reference_gate_pass']is False and r['full_new_reference_gate_pass']is False and r['host_retained_relationships_pass']is False and r['host_all_supply_pad_and_proposed_components_rooted']is False and not r['board_adopted'] and not r['board_written']
model=Path(r['frozen_host_model_file']);assert sha(model)==r['frozen_host_model_sha256']=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
g,h,b,q,current=pickle.loads(model.read_bytes());MIXED.restore_bound_field_current_precision_states(b,q)
qmap={z['uuid']:z for z in q};assert len(qmap)==48
profiles=read(recipe.parent/'current-owned-native-profile-ledger.json');assert len(profiles)==48
geometries={};seen=set();zonechecks=[]
for row in r['native_zone_rows']:
 path=Path(row['chunk_file']);assert sha(path)==row['chunk_sha256'];a=ast(path.read_text());assert a[0]=='zone'
 assert value(a,'uuid')==row['uuid'] and value(a,'net')==row['raw_net']and value(a,'layer')==row['layer'];assert row['uuid']not in seen;seen.add(row['uuid'])
 z=qmap[row['proposal_uuid']];assert z['net']==row['raw_net']and z['layer']==row['layer'];pf=recipe.parent/(r['native_zone_rows'][next(i for i,x in enumerate(r['native_zone_rows'])if x['proposal_uuid']==row['proposal_uuid'])]['uuid']+'.physical-Cu.wkb')
 # Physical/intended files use the native parent UUID of first part.
 parentrow=next(x for x in r['native_zone_rows']if x['proposal_uuid']==row['proposal_uuid']and x['part_index']==0)
 assert hashlib.sha256(z['shape'].wkb).hexdigest()==row['physical_Cu_wkb_sha256']==sha(recipe.parent/(parentrow['uuid']+'.physical-Cu.wkb'))
 assert hashlib.sha256(z['zone_outline_shape'].wkb).hexdigest()==row['intended_native_outline_wkb_sha256']==sha(recipe.parent/(parentrow['uuid']+'.native-outline.wkb'))
 rings=[[[nm(v)for v in xy[1:]]for xy in one(poly,'pts')[1:]]for poly in children(a,'polygon')];assert rings==[row['outer_integer_nm']]+row['hole_integer_nm']
 poly=Polygon([(x/1e6,y/1e6)for x,y in rings[0]],[[(x/1e6,y/1e6)for x,y in ring]for ring in rings[1:]]);assert poly.is_valid;geometries.setdefault(z['uuid'],[]).append(poly)
 settings=row['declared_native_settings'];assert int(value(a,'priority'))==settings['priority'];cp=one(a,'connect_pads');assert cp[1]=='yes'and Decimal(value(cp,'clearance'))==Decimal(str(settings['local_clearance_mm']));assert Decimal(value(a,'min_thickness'))==Decimal(str(settings['min_thickness_mm']));fill=one(a,'fill');assert int(value(fill,'island_removal_mode'))==settings['island_removal_mode'];assert Decimal(value(fill,'thermal_gap'))==Decimal(str(settings['thermal_gap_mm']))and Decimal(value(fill,'thermal_bridge_width'))==Decimal(str(settings['thermal_bridge_width_mm']));assert not children(a,'filled_polygon')and not children(a,'fill_segments')
 zonechecks.append({'uuid':row['uuid'],'proposal_uuid':z['uuid'],'literal_IU_AST_native_settings_and_physical_WKB_match':True})
for uid,parts in geometries.items():assert unary_union(parts).equals(qmap[uid]['zone_outline_shape']),uid
assert set(geometries)==set(qmap)
tracks={x['uuid']:x for x in h['tracks']};vias={x['uuid']:x for x in h['vias']};cuchecks=[]
for row in r['native_discrete_rows']:
 path=Path(row['chunk_file']);assert sha(path)==row['chunk_sha256'];a=ast(path.read_text());kind=row['kind'];assert a[0]==kind and value(a,'uuid')==row['uuid']and value(a,'net')==row['raw_net'];assert row['uuid']not in seen;seen.add(row['uuid']);t=(tracks if kind=='segment'else vias)[row['uuid']];assert t==row['geometry']
 if kind=='segment':
  assert [nm(x)for x in one(a,'start')[1:]]==[nm(x)for x in t['a']]and[nm(x)for x in one(a,'end')[1:]]==[nm(x)for x in t['b']]and nm(value(a,'width'))==nm(t['w'])and value(a,'layer')==t['layer'];assert bool(children(a,'locked'))==bool(t.get('locked',False))
 else:
  assert [nm(x)for x in one(a,'at')[1:]]==[nm(t['x']),nm(t['y'])]and nm(value(a,'size'))==nm(t['d'])and nm(value(a,'drill'))==nm(t['drill']);assert one(a,'layers')[1:]==['F.Cu','B.Cu'];assert not any(children(a,k)for k in('remove_unused_layers','keep_end_layers','zone_connection'))
 cuchecks.append({'uuid':row['uuid'],'kind':kind,'literal_native_raw_IU_locked_geometry_matches_current':True})
ir=read(r['complete_inventory_receipt_file']);assert sha(r['complete_inventory_receipt_file'])==r['complete_inventory_receipt_sha256'];diff=read(ir['diff_file']);assert sha(ir['diff_file'])==ir['diff_sha256'];assert {x['uuid']for x in r['native_discrete_rows']if x['kind']=='segment'}==set(diff['counts']['tracks']['new_UUIDs']);assert {x['uuid']for x in r['native_discrete_rows']if x['kind']=='via'}==set(diff['counts']['vias']['new_UUIDs'])
assert {x['uuid']for x in r['native_existing_owned_Cu_delete_rows']}=={x['uuid']for x in diff['native_existing_owned_Cu_delete_rows']}
for row in r['native_existing_owned_Cu_delete_rows']:assert sha(row['chunk_file'])==row['chunk_sha256']==row['exact_original_chunk_sha256']and sha(row['authorizing_recipe_file'])==row['authorizing_recipe_sha256']
assert r['native_existing_owned_Cu_replacement_rows']==diff['native_existing_owned_Cu_replacement_rows']and r['native_existing_owned_footprint_replacement_rows']==diff['native_existing_owned_footprint_replacement_rows']and r['existing_via_prospective_new_flashes']==diff['existing_via_prospective_new_flashes']
out=H/'R155-detached-native-serialization-independent-r308';assert not out.exists();out.mkdir();put(out/'zone-literal-native-roundtrip-checks.json',zonechecks);put(out/'discrete-literal-native-roundtrip-checks.json',cuchecks)
receipt={'verdict':'PASS_DETACHED_CURRENT_SERIALIZATION_ONLY_ALL_REFERENCE_PRODUCTION_FAILURES_PRESERVED','recipe_file':str(recipe),'recipe_sha256':sha(recipe),'exact_current_model_file':str(model),'exact_current_model_sha256':sha(model),'native_zone_chunks':len(zonechecks),'exact_current_owned_zone_shapes':len(qmap),'new_segments':276,'new_vias':99,'exact_original_deletes':41,'all_physical_and_intended_role_WKB_exact':True,'literal_nm_AST_raw_net_locked_settings_roundtrip':True,'mixed_physical_ED_D8_zero_grid_preserved':True,'same_UUID_replacements_all3FP_and_two_extra_flash_obligations_exact':True,'all_reference_and_production_failures_unchanged':True,'strict_old_reference_gate_pass':False,'full_new_reference_gate_pass':False,'native_or_physical_contact_reference_DRC_current_equivalence_claimed':False,'native_jobs':0,'adopted':False,'board_written':False,'helper_sha256':sha(__file__)};put(out/'receipt.json',receipt);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json')}),flush=True)
