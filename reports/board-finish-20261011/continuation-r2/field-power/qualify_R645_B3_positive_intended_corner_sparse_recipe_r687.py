"""Preserve prior readers; serialize distinct native outer parts with frozen UUID scheme."""
import json,hashlib,uuid
from pathlib import Path
H=Path(__file__).resolve().parent
P=H/'qualify_R645_B3_positive_intended_corner_sparse_recipe_r683.py'
O=H/'R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r685'
F=O/'failure.json';assert not F.exists()
F.write_text(json.dumps({'status':'SERIALIZER_SCHEMA_FAILURE_BEFORE_MODEL_OR_NATIVE_EMISSION','helper_SHA256':hashlib.sha256((H/'qualify_R645_B3_positive_intended_corner_sparse_recipe_r685.py').read_bytes()).hexdigest(),'exact_error':'emit_logic_zones_r1.render accepts a Polygon; B3 intended union has distinct MultiPolygon outers. Prior guards, witnesses, role packet and unchanged identity files remain frozen; no model/native emitted.','explicit_successor_serializer':'Same frozen emit_complete_power_recipe_r114/emit_known_failed_reference_native_recipe_r298 distinct-outer scheme: sort by (-area,bounds); primary proposal UUID then UUID5 separate-native-outer-i. Native profiles exact, no topology normalization.'},indent=1)+'\n',encoding='utf-8')
s=P.read_text(encoding='utf-8');s=s.replace("ly not in v['layers']","ly not in v['flashed']").replace('r683','r687').replace('R683','R687')
start=s.index(' text=render(uid,net,ly,new[\'zone_outline_shape\'])')
end=s.index('\n failures=errors+nozone+overlaps;',start)
replacement=''' parts=sorted(list(new['zone_outline_shape'].geoms)if new['zone_outline_shape'].geom_type=='MultiPolygon'else[new['zone_outline_shape']],key=lambda x:(-x.area,x.bounds));oldparts=sorted(list(old['zone_outline_shape'].geoms)if old['zone_outline_shape'].geom_type=='MultiPolygon'else[old['zone_outline_shape']],key=lambda x:(-x.area,x.bounds));assert len(parts)==len(oldparts);chunkrows=[];changedparts=[]
 for i,(part,oldpart)in enumerate(zip(parts,oldparts)):
  nid=uid if i==0 else str(uuid.uuid5(uuid.UUID(uid),'separate-native-outer-'+str(i)))
  text=render(nid,net,ly,part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Exact current B3 union native intended')
  oldtext=render(nid,net,ly,oldpart).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Exact current B3 union native intended')
  ast=parse(text);assert atom(ast,'net')==net and atom(ast,'uuid')==nid
  rings=[[[int(round(float(x[1])*1e6)),int(round(float(x[2])*1e6))]for x in child(pp,'pts')[1:]]for pp in children(ast,'polygon')];expected=[[[int(round(x*1e6)),int(round(y*1e6))]for x,y in r.coords[:-1]]for r in(part.exterior,*part.interiors)];assert rings==expected
  reconstructed=Polygon([(x/1e6,y/1e6)for x,y in rings[0]],[[(x/1e6,y/1e6)for x,y in rr]for rr in rings[1:]]);assert reconstructed.is_valid and reconstructed.wkb==part.wkb
  assert int(atom(ast,'priority'))==124 and float(atom(child(ast,'connect_pads'),'clearance'))==.15 and child(ast,'connect_pads')[1]=='yes' and float(atom(ast,'min_thickness'))==.15
  fill=child(ast,'fill');assert int(atom(fill,'island_removal_mode'))==1 and float(atom(fill,'thermal_gap'))==.15 and float(atom(fill,'thermal_bridge_width'))==.3
  chunkfile=OUT/(nid+'.zone-chunk');chunkfile.write_text(text,encoding='utf-8',newline='');beforefile=OUT/(nid+'.exact-before-zone-chunk');beforefile.write_text(oldtext,encoding='utf-8',newline='')
  changed=part.wkb!=oldpart.wkb
  if changed:changedparts.append(i)
  else:assert text==oldtext
  chunkrows.append({'UUID':nid,'proposal_UUID':uid,'part_index':i,'raw_net':net,'layer':ly,'all_current_declared_native_profile_fields':{k:new[k]for k in KEYS},'chunk_file':str(chunkfile.resolve()),'chunk_SHA256':sha(chunkfile),'exact_before_chunk_file':str(beforefile.resolve()),'exact_before_chunk_SHA256':sha(beforefile),'before_part_WKB_SHA256':hs(oldpart),'after_part_WKB_SHA256':hs(part),'changed_only_declared_intended_corner':changed,'exact_ring_coordinate_arrays_IU':rings,'native_API_and_refill':'OPEN_NO_NATIVE_LAUNCH'})
 assert len(changedparts)==1
 chunk=OUT/'native-owner-profile-and-exact-IU-distinct-outer-chunk-rows.json';put(chunk,{'rows':chunkrows,'one_changed_native_outer_part_index':changedparts[0],'all_other_native_outer_chunks_byte_identical':True,'frozen_R114_R298_distinct_outer_UUID_scheme':True})'''
s=s[:start]+replacement+s[end:]
s=s.replace("'one_new_native_intended_chunk_SHA256':sha(chunk)","'native_distinct_outer_chunk_manifest_SHA256':sha(chunk),'one_native_outer_part_changed_all_other_chunk_bytes_exact':True")
exec(compile(s,str(Path(__file__)),'exec'))
