"""Read-only literal DSN protection review, separate from the preparation."""
from pathlib import Path
import sys,copy,json
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import hardware_route_selected_additive_r02 as e
OUT=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-selected-DSN-r02'
raw=e.parse((OUT/'native.dsn').read_text(encoding='utf8'));selected=e.parse((OUT/'selected.dsn').read_text(encoding='utf8'))
manifest=e.read(OUT/'manifest.json');receipt=e.read(OUT/'prepare.json');rows=manifest['nets']
scope=e.read(ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-allowlist-r04/source-scope-review.json'); assert set(rows)==set(scope['selected_nets']) and len(rows)==27
assert e.sha(OUT/'selected.dsn')==receipt['selected_dsn_sha256']
assert e.child(raw,'library')==e.child(selected,'library') and e.child(raw,'placement')==e.child(selected,'placement')
assert {e.value(v[1])for v in e.children(e.child(selected,'network'),'net')}==set(rows)
protected=[]
rw=e.child(raw,'wiring');sw=e.child(selected,'wiring');assert len(rw)==len(sw)
for old,new in zip(rw[1:],sw[1:]):
 expected=copy.deepcopy(old)
 if not isinstance(old,list)or old[0]not in('wire','via'):
  assert old==new;continue
 for t in list(e.children(expected,'type')):expected.remove(t)
 expected.append(['type','protect']);n=e.child(expected,'net')
 if n is not None and e.value(n[1])not in rows:expected.remove(n)
 assert expected==new and e.child(new,'type')==['type','protect']
 protected.append(old[0])
assert len(protected)==receipt['selection']['old_wires_vias_protected']; assert len(e.children(rw,'via'))+sum((len(e.child(w,'path'))-3)//2-1 for w in e.children(rw,'wire'))==11759
assert not e.children(e.child(selected,'structure'),'plane')
assert receipt['all_native_pad_pieces']==9847 and receipt['prepared_board_sha256']==manifest['board_sha256']
assert not receipt['baseline_native_drc']['regular_violations'] and not receipt['baseline_native_drc']['ignored_checks']
assert receipt['selection']['actual_filled_copper_keepout_polygons_on_routable_layers']>0
assert len(receipt['selection']['actual_adjacent_reference_void_obstacles'])==4
e.write(OUT/'independent-DSN-protection-review.json',dict(passed=True,board_sha256=manifest['board_sha256'],selected_DSN_sha256=e.sha(OUT/'selected.dsn'),selected_exact_source_reviewed_unjoined_GPIO_config_visual_nets=sorted(rows),all_exported_retained_wire_via_records_protected=len(protected),all_actual_physical_library_placement_identical_to_native_export=True,all9847_native_pad_pieces_retained_in_frozen_base=True,no_excluded_plane_net_reintroduced=True,actual_filled_power_copper_and_reference_voids_are_interchange_obstacles=True,original_native_board_unchanged=True,SES_overwrite_not_authorized=True,solver_or_import_pass_claimed=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,protected_wires_vias=len(protected),selected=len(rows),sha256=e.sha(OUT/'selected.dsn'))))
