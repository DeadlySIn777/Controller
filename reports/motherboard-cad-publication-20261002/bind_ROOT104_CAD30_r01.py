"""Bind exact adopted/published work-in-progress bytes; release gates remain closed."""
from pathlib import Path
import copy,json,hashlib,sys
root=Path.cwd();sys.path.insert(0,str(root/'tools'))
from check_release import check_release
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
rel=lambda p:Path(p).resolve().relative_to(root).as_posix()
out=root/'reports/motherboard-cad-publication-20261002/ROOT104-CAD30-release-binding-r01';out.mkdir(exist_ok=False)
ad=root/'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/adoption.json';a=read(ad)
folder=root/'hardware/board_review/revisions/20261002-30';publication=folder/'publication.json';p=read(publication)
viewer=read(root/'hardware/board_review/board-view.json')
assert a['adopted'] and a['working_revision']=='ROOT104' and not a['manufacturing_ready']
assert p['published'] and viewer['current_revision']==p['revision']=='20261002-30'
assert p['native_pcb_sha256']==a['board_sha256']==sha(Path(a['board']))==sha(folder/'motherboard-native-candidate.kicad_pcb')
manifest=root/'manufacturing/release-manifest.json';m=read(manifest);before=sha(manifest)
(out/'prior-manifest.json').write_bytes(manifest.read_bytes())
c=m['partial_candidate'];c.update(scope='Actual Source26 and adopted ROOT104; CAD30 contains exact board bytes',published_native_revision=p['revision'],working_native_revision='ROOT104',working_board_sha256=a['board_sha256'],uncapped_physical_missing_joins=3508,working_board_file=rel(a['board']),working_adoption_path=rel(ad),working_adoption_sha256=sha(ad),native_regular_DRC_clean=True,preexisting_positive_SMD_drill_overlaps=277,preexisting_unique_SMD_overlapping_vias=274,SMD_drill_audit_is_lower_bound=True,SMD_assembly_qualification_complete=False)
stats=viewer['boards'][0]['stats'];v=c['published_viewer'];v.update(revision=p['revision'],board_file=rel(folder/'motherboard-native-candidate.kicad_pcb'),board_sha256=a['board_sha256'],track_via_items=11807,uncapped_missing_joins=3508,publication_path=rel(publication),publication_sha256=sha(publication),copper_zone_definitions=stats['copper_zones'],ruleareas=stats['native_rule_areas'],positive_filled_zone_definitions=stats['filled_copper_zones'])
bom=dict(path=rel(folder/'source-inputs/bom.csv'),sha256=sha(folder/'source-inputs/bom.csv'),source_design_path=rel(folder/'source-inputs/design.json'),source_design_sha256=sha(folder/'source-inputs/design.json'),published_revision=p['revision'],source_adoption_path=rel(folder/'electrical-source-adoption.json'),source_adoption_sha256=sha(folder/'electrical-source-adoption.json'),physical_footprints=2688,scope='Exact Source26 designator BOM bound to CAD30; procurement/cost/assembly qualification incomplete')
v['bom']=copy.deepcopy(bom)
drill=root/'reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json'
c['evidence']=[dict(path=rel(f),sha256=sha(f))for f in [root/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json',ad,ad.parent/'independent-inventory-r01/review.json',publication,Path(a['full_validation_report']),drill]]
items={x['id']:x for x in m['artifacts']}
items['pcb_layout'].update(status='partial-source26-root104-routing-incomplete',note='ROOT104/CAD30 exact PCB: 2688 footprints, 11807 track/via items, 1544 zones/rule areas; 3508 required joins. Native regular DRC has zero errors/warnings/ignored checks; zero orphan copper. 274 inherited vias overlap 277 same-net paste SMD lands. Not manufacturing-ready.')
items['bom'].update(bom)
items['bom']['note']='CAD30/Source26 designator BOM. Partial v11 consumed parts at quantities 1/10/100: USD1091.51/877.37/796.51;105 MPNs priced,185 MPNs/720 pieces unpriced. Complete board/module/screen/kit costs remain null.'
items['placement'].update(status='partial-published-cad30-placement-not-production-CPL',note='CAD30 exactly matches ROOT104. Routing, mechanical, assembly, electrical and physical qualification incomplete. No production CPL.')
items['drc'].update(status='partial-root104-native-clean-connectivity-incomplete',note='Native regular DRC 0 errors/0 warnings/no ignored checks; native and independent 3508 missing joins, zero orphans. Scoped proofs:120 bypass loops,245 receiving returns,188 Source-anchored filled resources. Complete power/routing/return and assembly qualification remain open.')
items['software_validation'].update(status='partial-disconnected-bench-pass-complete-runtime-blocked',note='Fresh ROOT104 full r08:25 PASS/9 BLOCKED/1 physical NOT_RUN/0 FAIL;4041 unchanged inputs.1895 host and238 native cases pass;5 Windows symlink skips. Includes2048 actual SPI seeded cases,18 reset/fault plant scenarios,diagnostic IOL1 and read-only IS2 CAP3 profile. Full HAL/providers/machines/vendor fit and physical qualification incomplete.')
manifest.write_text(json.dumps(m,indent=2)+'\n',encoding='utf8')
for stage in ['prototype','production']:
 f=root/f'reports/{stage}-release-check.json';(out/f'prior-{stage}-release-check.json').write_bytes(f.read_bytes())
 result=check_release(m,root,stage);assert not result['ready'];f.write_text(json.dumps(result,indent=2)+'\n')
(out/'receipt.json').write_text(json.dumps(dict(passed=True,before_manifest_sha256=before,after_manifest_sha256=sha(manifest),board_sha256=a['board_sha256'],published_revision=p['revision'],adoption_sha256=sha(ad),exact_published_working_and_BOM_binding=True,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,working='ROOT104',published='20261002-30',missing_joins=3508)))
