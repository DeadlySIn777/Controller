"""Freeze the conservative visual-only subset for a protected router copy."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
import hardware_route_ordinary_wip_r05 as issued
import hardware_bind_ordinary_route_manifest_r03 as binder
import hardware_scope_anchored_reference_pieces as pieces
import hardware_merge_bounded_pcb_delta as delta
e=issued.engine
BASE=ROOT/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb'
MAP=BASE.parent/'final-source26-map-r01/domain-map.json'
FULL=BASE.parent/'final-literal-resources-r01.json'
OUT=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-visual-allowlist-r01'
assert not OUT.exists();OUT.mkdir(parents=True)
assert e.sha(BASE)=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
review=ROOT/issued.SOURCE;r=e.read(review);status=e.read(ROOT/'hardware/motherboard_status/design.json')
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();conn=b.GetConnectivity()
pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()}
rows=[];selected=[]
for index in range(24):
 name='/motherboard_status/OBS'+str(index)+'_INVERTED';row=r['nets'][name]
 assert row['signal_class']=='status_logic' and len(row['source_pins'])==2
 producer=row['declared_producer'][0]
 assert status['components'][producer]['role']=='TTL receive buffer, no motion/DI authority'
 pp,qq=[pads[tuple(v)]for v in row['source_pins']]
 connected=qq.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in conn.GetConnectedItems(pp)}
 item=dict(net=name,source_pins=row['source_pins'],source_pad_UUIDs=[pp.m_Uuid.AsString(),qq.m_Uuid.AsString()],actual_connected_before=connected,required_joins_before=int(not connected),producer_role=status['components'][producer]['role'],classification='Independent buffered general-DI visual indication only; no acquisition, motor alarm, watchdog or actuator authority.')
 rows.append(item)
 if not connected:selected.append(name)
assert selected,'No actual unjoined visual opportunity'
proof=pieces.qualify(FULL,MAP,BASE,{'/LOGIC_GND'},{'In1.Cu','In4.Cu'})
e.write(OUT/'literal-plane-eligibility.json',proof)
e.write(OUT/'selected-nets.json',selected)
manifest=binder.bind(BASE,OUT/'literal-plane-eligibility.json',OUT/'manifest.json',set(selected))
assert all(manifest['nets'][n]==r['nets'][n]for n in selected)
e.write(OUT/'baseline-disposition.json',dict(board_sha256=e.sha(BASE),routing_incomplete=True,known_unresolved_native_warnings=[],manufacturing_ready=False,scope='Native zero regular/ignored baseline. Missing connections remain explicit; zero regular DRC is not routing completion.'))
excluded=[]
for name,row in sorted(r['nets'].items()):
 if name in selected:continue
 reason='Already physically joined visual branch; old copper is protected.'if name in{v['net']for v in rows}else 'Outside conservative visual-only subset: acquisition, motor/alarm, watchdog/fault, identity/strap, permission/enable or safety-qualified status are protected.'
 excluded.append(dict(net=name,signal_class=row['signal_class'],reason=reason))
sourcehash={str(p):e.sha(p)for p in(BASE,MAP,FULL,review,ROOT/'hardware/motherboard_status/design.json',Path(__file__))}
tree=e.parse(delta.without_generated_fills(BASE.read_text(encoding='utf8')))
hashtext=lambda s:hashlib.sha256(s.encode('utf8')).hexdigest()
cu={};zones={};fps={};padpieces={}
for kind in('segment','via','arc'):
 for item in e.children(tree,kind):
  u=e.value(e.child(item,'uuid')[1]);cu[u]=dict(kind=kind,definition_sha256=hashtext(e.dump(item)),net=e.value(e.child(item,'net')[1]))
for z in e.children(tree,'zone'):
 u=e.value(e.child(z,'uuid')[1]);zones[u]=dict(definition_sha256=hashtext(e.dump(z)),is_rule_area=e.child(z,'keepout')is not None)
for fp in e.children(tree,'footprint'):
 ref=next(e.value(p[2])for p in e.children(fp,'property')if e.value(p[1])=='Reference')
 fps[ref]=dict(footprint_UUID=e.value(e.child(fp,'uuid')[1]),complete_definition_sha256=hashtext(e.dump(fp)))
 for p in e.children(fp,'pad'):
  u=e.value(e.child(p,'uuid')[1]);assert u not in padpieces
  padpieces[u]=dict(reference=ref,pin=e.value(p[1]),exact_definition_sha256=hashtext(e.dump(p)))
assert len(cu)==11759 and len(fps)==2688 and len(padpieces)==9847 and len(zones)==1544
e.write(OUT/'protected-native-manifest.json',dict(passed=True,board_path=str(BASE),board_sha256=e.sha(BASE),source_revision=26,design_sha256=manifest['design_sha256'],netlist_sha256=manifest['netlist_sha256'],all_retained_copper_protected=cu,all_footprints_and_poses_protected=fps,all_actual_pad_pieces_protected=padpieces,all_zone_and_rule_definitions_protected=zones,all_other_native_objects_sha256=hashtext(str(e.immutable_objects(tree))),project_sha256=e.sha(BASE.with_suffix('.kicad_pro')),rules_sha256=e.sha(BASE.with_suffix('.kicad_dru')),route_layers=['F.Cu','In2.Cu','In3.Cu','B.Cu'],reserved_reference_layers=['In1.Cu','In4.Cu'],excluded_physical_nets=sorted(str(n.GetNetname())for n in b.GetNetsByName().values()if str(n.GetNetname())not in selected),interchange_only_excluded_netless_obstacles=True,SES_direct_overwrite_forbidden=True,only_literal_reviewed_new_segments_and_vias_may_be_appended=True,manufacturing_ready=False))
e.write(OUT/'source-scope-review.json',dict(passed=True,input_sha256=sourcehash,board_sha256=e.sha(BASE),reviewed_visual_rows=rows,selected_nets=selected,selected_unjoined_nets=len(selected),required_joins_before=sum(v['required_joins_before']for v in rows),already_physically_joined_visual_nets=24-len(selected),prior112_rows_unchanged=True,excluded_prior_review_rows=excluded,no_new_category_promoted=True,scope='Conservative first Freerouting evaluation: only actual open OBS0..23 visual indicator branches. All old copper/pads/poses/zones remain protected, including selected-net copper.',prior_failure_lessons=['Raw SES may replace old copper; use donor-only import and additive immutable native merge.','Same-named nominal planes cannot establish actual Source reference.','Signal-via handoffs require actual own Source stitch <=1mm and flashed/connected adjacent annuli.','Native fixed power fills and reference voids must remain obstacles; post-refill power topology/source/feed proofs are separate mandatory gates.'],manufacturing_ready=False))
assert all(e.sha(p)==h for p,h in sourcehash.items())
print(json.dumps(dict(passed=True,selected_nets=len(selected),required_joins_before=len(selected),old_copper=len(cu),pads=len(padpieces),out=str(OUT))))
