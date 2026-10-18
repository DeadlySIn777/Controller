"""Bind the adopted routed candidate and exact published bytes, without release."""
from pathlib import Path
import json, hashlib, sys, copy
root=Path.cwd();sys.path.insert(0,str(root/'tools'))
from check_release import check_release
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
out=root/'reports/motherboard-cad-publication-20261001/ROOT103-CAD29-release-binding-r01'
out.mkdir(exist_ok=False)
ad=root/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/adoption.json'
a=read(ad);assert a['adopted'] and a['working_revision']=='ROOT103' and not a['manufacturing_ready']
folder=root/'hardware/board_review/revisions/20261001-29';publication=folder/'publication.json';p=read(publication)
assert p['published'] and p['native_pcb_sha256']==a['board_sha256']==sha(Path(a['board']))
viewer=read(root/'hardware/board_review/board-view.json');assert viewer['current_revision']==p['revision']
assert sha(folder/'motherboard-native-candidate.kicad_pcb')==a['board_sha256']
rel=lambda p:Path(p).resolve().relative_to(root).as_posix()
manifest=root/'manufacturing/release-manifest.json';m=read(manifest);before=sha(manifest)
(out/'prior-manifest.json').write_bytes(manifest.read_bytes())
c=m['partial_candidate'];c.update(scope='Actual Source26 and adopted ROOT103; CAD29 contains the exact board bytes',
    published_native_revision=p['revision'],working_native_revision='ROOT103',working_board_sha256=a['board_sha256'],
    uncapped_physical_missing_joins=a['missing_joins'],working_board_file=rel(a['board']),
    working_adoption_path=rel(ad),working_adoption_sha256=sha(ad),native_regular_DRC_clean=True,
    preexisting_positive_SMD_drill_overlaps=277,preexisting_unique_SMD_overlapping_vias=274,
    SMD_drill_audit_is_lower_bound=True,SMD_assembly_qualification_complete=False)
stats=viewer['boards'][0]['stats'];v=c['published_viewer'];v.update(revision=p['revision'],
    board_file=rel(folder/'motherboard-native-candidate.kicad_pcb'),board_sha256=a['board_sha256'],
    track_via_items=a['track_via_count'],uncapped_missing_joins=a['missing_joins'],
    publication_path=rel(publication),publication_sha256=sha(publication),
    copper_zone_definitions=stats['copper_zones'],ruleareas=stats['native_rule_areas'],
    positive_filled_zone_definitions=stats['filled_copper_zones'])
bom=dict(path=rel(folder/'source-inputs/bom.csv'),sha256=sha(folder/'source-inputs/bom.csv'),
    source_design_path=rel(folder/'source-inputs/design.json'),source_design_sha256=sha(folder/'source-inputs/design.json'),
    published_revision=p['revision'],source_adoption_path=rel(folder/'electrical-source-adoption.json'),
    source_adoption_sha256=sha(folder/'electrical-source-adoption.json'),physical_footprints=a['physical_footprints'],
    scope='Exact Source26 designator BOM bound to CAD29; procurement/cost/assembly qualification incomplete')
v['bom']=copy.deepcopy(bom)
c['evidence']=[dict(path=rel(f),sha256=sha(f)) for f in [
    root/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json',ad,
    ad.parent/'final-independent-inventory-r01/review.json',publication,Path(a['full_validation_report']),
    root/'reports/motherboard-pcb-integration-20261001/health-r31-full-drill-SMD-audit-r01/receipt.json']]
items={x['id']:x for x in m['artifacts']}
items['pcb_layout'].update(status='partial-source26-root103-routing-incomplete',
    note='ROOT103 and CAD29 have identical PCB bytes:2688 footprints,11759 track/via items,1544 zones/ruleareas;3521 required joins remain. Native regular DRC0errors/0warnings/noignored,zeroorphans.274 inherited vias overlap277 same-net paste SMD lands; assembly disposition remains open. No manufacturing readiness.')
items['bom'].update(bom)
items['bom']['note']='Published CAD29/Source26 designator BOM. Dated partial v11 known consumed inventory at1/10/100:USD1091.51/877.37/796.51;105MPNs priced,185MPNs/720pieces unpriced. Complete manufactured board/modules/screens/kit costs remain null.'
items['placement'].update(status='partial-published-cad29-placement-not-production-CPL',
    note='CAD29 exactly matches ROOT103; routing, mechanical, assembly, electrical and physical qualification incomplete. No production CPL.')
items['drc'].update(status='partial-root103-native-clean-connectivity-incomplete',
    note='Native regular DRC0errors/0warnings/noignored;uncapped native=independent3521missingjoins,zeroorphans.110ownedbypassloops/225receivingreturns/188Source-anchoredfilledresources are scoped geometry proofs. SMD-drill assembly disposition, complete routing/power/return/fit and physical qualification remain open.')
items['software_validation'].update(status='partial-disconnected-bench-pass-complete-runtime-blocked',
    note='Full exact-ROOT103 pre-hardware r07:22PASS/9BLOCKED/1NOT_RUN/0FAIL,3765 unchanged scoped inputs.1887 host and235 native cases pass;5 Windows symlink cases skipped. Actual bounded stateful CNC3/SPI/mechanics and family mapping remain distinct from unfinished CAP3/HAL/full providers/vendor fit. Public18case/IOL1 extensions are separately verified after this full run.')
manifest.write_text(json.dumps(m,indent=2)+'\n',encoding='utf8',newline='\n')
for stage in ['prototype','production']:
    f=root/f'reports/{stage}-release-check.json';(out/f'prior-{stage}-release-check.json').write_bytes(f.read_bytes())
    result=check_release(m,root,stage);assert not result['ready']
    f.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
(out/'receipt.json').write_text(json.dumps(dict(passed=True,before_manifest_sha256=before,
    after_manifest_sha256=sha(manifest),board_sha256=a['board_sha256'],published_revision=p['revision'],
    adoption_sha256=sha(ad),exact_published_working_and_BOM_binding=True,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,working='ROOT103',published='20261001-29',missing_joins=a['missing_joins'])))
