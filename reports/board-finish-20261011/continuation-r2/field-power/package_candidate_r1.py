"""Pin independent field-owned native chunks and prospective return polygons."""
import hashlib,json,re
from inventory import HERE,BOARD,PARSER,sha
from contact_layout import O,norm
from stage_board_chunks import load_parser
from verify_source import parse,atom,children

OUT=HERE/'candidate-recipe-r1'
SOURCE=HERE/'combined-power-source-r2'

def main():
 if (OUT/'receipt.json').exists(): raise ValueError('Frozen candidate recipe exists')
 OUT.mkdir(exist_ok=True)
 original=BOARD.read_bytes();native=O.C.inventory(original)[3]
 private=json.loads((HERE/'private-DO-copper-r1.json').read_text(encoding='utf-8'))
 board=json.loads((HERE/'board-delta-r3/receipt.json').read_text(encoding='utf-8'))
 cut=json.loads((HERE/'owned-pad-cuts-r1/receipt.json').read_text(encoding='utf-8'))
 returns=json.loads((HERE/'variable-return-r2/receipt.json').read_text(encoding='utf-8'))
 export=json.loads((SOURCE/'source-export/receipt.json').read_text(encoding='utf-8'))
 assert private['native_partition_replay_exact'] and cut['graph_gate']=='PASS' and export['verdict']=='PASS'
 rawmap={}
 for raw in set(re.findall(rb'\(net "([^"\r\n]+)"\)',original)):
  raw=raw.decode('utf-8');n=norm(raw)
  assert n not in rawmap or rawmap[n]==raw
  rawmap[n]=raw
 rawmap['DOB_DO_FIELD_3V3']='DOB_DO_FIELD_3V3'
 retags=[]
 for group in private['private_moved_pad_components']:
  assert not group['retained_old_rail_pads']
  for item in group['copper_items']:
   uid=item['uuid'];before=native[uid];assert hashlib.sha256(before).hexdigest()==item['old_sha256']
   oldraw=rawmap[private['old_net']];newraw=rawmap[private['new_net']]
   after,n=re.subn(rb'\(net "'+re.escape(oldraw.encode('utf-8'))+rb'"\)',b'(net "'+newraw.encode('utf-8')+b'")',before)
   assert n==1 and after.replace(b'(net "'+newraw.encode()+b'")',b'(net "'+oldraw.encode()+b'")')==before
   root=parse(after.decode('utf-8'));assert atom(root,'uuid')==uid
   p=OUT/(uid+'.'+item['kind']+'-chunk');p.write_bytes(after)
   retags.append({'uuid':uid,'kind':item['kind'],'before_sha256':item['old_sha256'],'after_sha256':sha(p),'path':str(p.resolve()),'old_raw_net':oldraw,'new_raw_net':newraw,'geometry_UUID_and_all_other_bytes_preserved':True,'private_moved_pads':group['moved_pads']})
 assert len(retags)==51 and len({r['uuid'] for r in retags})==51
 assert not ({r['uuid'] for r in retags}&{r['uuid'] for r in cut['cuts']})
 parser=load_parser(PARSER);fresh=parser['read_netlist'](SOURCE/'source-export/fresh.net')
 checks=[]
 for row in board['existing_footprint_chunks']+board['new_footprint_chunks']:
  p=HERE/'board-delta-r3'/(row['ref']+'.footprint-chunk');assert sha(p)==row['chunk_sha256']
  ast=parse(p.read_text(encoding='utf-8'));ref=row['ref'];props={q[1]:q[2] for q in children(ast,'property')}
  path=atom(ast,'path');expected=parser['expected_path'](fresh['components'][ref]);assert path in expected
  mechanical=[q for q in children(ast,'pad') if not q[1]]
  assert all(not atom(q,'net') for q in mechanical)
  pads={q[1]:norm(atom(q,'net')) for q in children(ast,'pad') if q[1]}
  for pin,net in pads.items():assert net==fresh['node_net'][(ref,pin)],(ref,pin,net,fresh['node_net'].get((ref,pin)))
  assert props['Value']==fresh['components'][ref]['value']
  if row in board['new_footprint_chunks']:
   source=json.loads((SOURCE/'receipt.json').read_text(encoding='utf-8'))['new_components'][ref]
   assert props['MPN']==source['mpn']
  checks.append({'ref':ref,'path':path,'all_native_pad_assignments_match_combined_source':True,'value_matches_combined_source':True,'native_pads':len(pads),'unassigned_mechanical_pads':len(mechanical)})
 for row in board['local_tracks']:assert sha(row['path'])==row['sha256']
 for row in cut['cuts']:
  assert hashlib.sha256(native[row['uuid']]).hexdigest()==row['old_chunk_sha256']
  for replacement in row['replacement_segments']:assert sha(replacement['path'])==replacement['sha256']
 for row in returns['rows']:
  if 'copper_file' in row:assert sha(row['copper_file'])==row['copper_sha256']
 def binding(p):return {'path':str(p.resolve()),'sha256':sha(p)}
 recipe={
  'schema':'field-owned-host-candidate-recipe-r1',
  'verdict':'PASS_EXACT_SOURCE_AND_CHANGED_ITEM_SCOPE; POWER_SPINES_ELECTRICAL_AND_REFILL_GATES_OPEN',
  'original_board':binding(BOARD),
  'authoritative_six_part_combined_source':{'fresh_netlist':binding(SOURCE/'source-export/fresh.net'),'native_receipt':binding(SOURCE/'source-export/receipt.json'),'source_receipt':binding(SOURCE/'receipt.json'),'native_counts':export['counts'],'semantic_delta':'exact14 existing pad moves +6 new components +L11001/C11061 Value/MPN only'},
  'field_only_intermediate_source':{'fresh_source_export_sha256':board['fresh_source_export_sha256'],'scope':'Historical AB14+4 netlist used for the four initial cloned field footprints; inherited board-delta-r3 field retained this trace. It is not the authoritative integration netlist. All18 field footprint chunks independently checked here against combined six-part native export.'},
  'combined_source_owner_separation':{'field':'exact14 pad moves; U11038/C11092/C11093/R11088/C11095 additions','SBC':'C11094 addition and L11001 Value/MPN only','root':'C11061 Value/MPN only'},
  'existing_footprint_replacements':board['existing_footprint_chunks'],
  'new_field_footprint_additions':board['new_footprint_chunks'],
  'exact_existing_pad_net_moves':14,
  'combined_source_native_footprint_precheck':checks,
  'private_net_only_replacements':retags,
  'owned_pad_separation':{'receipt':binding(HERE/'owned-pad-cuts-r1/receipt.json'),'affected_existing_segments':35,'whole_segment_removals':24,'remaining_trimmed_replacements':11,'rows':cut['cuts'],'retained_pad_graph_replay':cut['unaffected_named_pad_graph_replay']},
  'new_local_segment_additions':board['local_tracks'],
  '11_local_fanout_paths_emitted_as37_segments':True,
  'project_proposal':binding(HERE/'board-delta-r3/project-proposal.kicad_pro'),
  'old_changed_pad_and_shared_contact_obligations':binding(HERE/'changed-pad-contact-r1.json'),
  'private_and_shared_DOB_contract':binding(HERE/'private-DO-copper-r1.json'),
  'source_rooted_return_polygon_proposals':{'receipt':binding(HERE/'variable-return-r2/receipt.json'),'binding':binding(HERE/'variable-return-r2/binding.json'),'rows':returns['rows'],'native_representation':'Create one copper zone per bank/layer with the exact WKB outer rings and holes. Preserve all original zone definitions. Raw net token from each row is mandatory. Native refill, contacts and retained foreign-net continuity remain explicit gates. WKB is a concrete host polygon proposal, not a saved native fill or an approved capacity.'},
  'open_obligations':['Full sheet/barrel current sharing with exact signed port loads, drop and temperature evidence; no6.5A qualification by summed widths.','Connect every retained/local ground group to real source and compose proposed bridges into subsequent reference geometry.','A5/B5 source feeds, relocated regulator input and DOB_DO/PG/output spines incomplete.','New global DO rail requires explicit scoped existing reserved-corridor rule treatment before any route relying on its exception.','Native refill must preserve every unchanged named-pad component; collision/contact and isolation DRC gates remain.','B5 and LDO startup/fault/backpower/rearm timing and effective capacitor/assembly qualification remain conditional.'],
  'counts':{'existing_footprint_replacements':13,'new_field_footprints':5,'private_net_only_items':51,'pad_cut_affected_items':35,'pad_cut_replacement_segments':11,'new_local_segments':37,'prospective_return_polygons':sum('copper_file' in r for r in returns['rows'])},
  'raw_native_net_collision_count':0,
  'whole_board_written':False,'native_board_jobs':0,'ready_for_adoption':False,
 }
 (OUT/'receipt.json').write_text(json.dumps(recipe,indent=1)+'\n',encoding='utf-8')
 assert sha(BOARD)==recipe['original_board']['sha256']
 print(json.dumps({'counts':recipe['counts'],'combined_native_source_sha256':recipe['authoritative_six_part_combined_source']['fresh_netlist']['sha256'],'owned_footprints_combined_parity':len(checks),'recipe_sha256':sha(OUT/'receipt.json')}))

if __name__=='__main__':main()
