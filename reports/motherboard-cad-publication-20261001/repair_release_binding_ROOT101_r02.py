"""Bind release bookkeeping to the actual published CAD26 and adopted ROOT101.

Run only after the active frozen-input validation run ends. No fabrication
artifact or source board is generated, modified or declared complete.
"""
from pathlib import Path
import json,hashlib,sys,csv,copy
root=Path.cwd();sys.path.insert(0,str(root))
from tools.check_release import check_release
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
assert (root/'reports/pre-hardware-validation-20261001/full-r01/report.json').is_file(),'Do not modify frozen inputs during full-r01'
out=root/'reports/motherboard-cad-publication-20261001/ROOT101-release-binding-repair-r02';out.mkdir(exist_ok=False);before={}
path=root/'manufacturing/release-manifest.json';manifest=read(path);items={x['id']:x for x in manifest['artifacts']}
viewer=read(root/'hardware/board_review/board-view.json');revision=viewer['current_revision'];assert revision=='20261001-26'
pubroot=root/'hardware/board_review/revisions'/revision;publication=read(pubroot/'publication.json')
adoptpath=root/'reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/adoption.json';adoption=read(adoptpath)
workboard=adoptpath.parent/'motherboard-bounded-merged-candidate.kicad_pcb'
pubboard=pubroot/'motherboard-native-candidate.kicad_pcb';bom=pubroot/'source-inputs/bom.csv';design=pubroot/'source-inputs/design.json';source_adopt=pubroot/'electrical-source-adoption.json'
assert adoption['adopted']and not adoption['manufacturing_ready']
assert publication['published']and not publication['manufacturing_ready']
assert sha(pubboard)==sha(workboard)==adoption['board_sha256']==publication['native_pcb_sha256']
assert sha(design)==adoption['exact_source_design_sha256']
assert sha(source_adopt)==publication['source_adoption_sha256']
with bom.open(encoding='utf-8-sig',newline='')as f:rows=list(csv.DictReader(f))
assert {r['Reference']for r in rows}==set(read(design)['components'])and len(rows)==2688
# The prior publisher retained the exact BOM bytes and source hash but omitted
# its public download fields. Restore metadata only from that frozen evidence.
for index,meta in enumerate((pubroot/'board-view.json',root/'hardware/board_review/board-view.json')):
 d=read(meta);assert d['current_revision']==revision
 v=d['boards'][0];assert v['source_hashes']['bom.csv']==sha(bom)
 original=copy.deepcopy(d);before[meta.relative_to(root).as_posix()]=sha(meta)
 (out/f'viewer-before-{index}.json').write_bytes(meta.read_bytes())
 v['bom_file']=f'revisions/{revision}/source-inputs/bom.csv';v['bom_sha256']=sha(bom)
 for field in('components','tracks','native_edge_cuts','stats','evidence','source_hashes'):
  assert v[field]==original['boards'][0][field]
 write(meta,d)
viewer=read(root/'hardware/board_review/board-view.json')
assert viewer['boards'][0]['bom_sha256']==sha(bom)
relative=lambda p:p.relative_to(root).as_posix()
binding=dict(path=relative(bom),sha256=sha(bom),source_design_path=relative(design),source_design_sha256=sha(design),published_revision=revision,source_adoption_path=relative(source_adopt),source_adoption_sha256=sha(source_adopt),physical_footprints=2688,scope='Exact frozen Source26 designator BOM belonging to actual CAD26 publication; procurement/cost/assembly qualification remains incomplete')
before[relative(path)]=sha(path);(out/path.name).write_bytes(path.read_bytes())
items['bom'].update(binding)
items['bom']['note']='The downloadable designator BOM is frozen to actual published CAD26/Source26. Current v11 prices105 exact MPNs and leaves185 MPNs/720 fitted pieces unpriced. Known consumed inventory per board at1/10/100 is USD1091.51/877.37/796.51; complete board/PCBWay/kit totals remain null. No complete procurement or manufacturing BOM claim.'
items['pcb_layout'].update(status='partial-source26-root101-routing-incomplete',note='Adopted ROOT101 and published CAD26 are exact matching native PCB bytes:2688 footprints,11635 track/via items,1521 native zones/ruleareas and3528 independently counted required joins. Native regular DRC zeroerrors/zerowarnings/noignoredchecks, zero orphan copper. Full connectivity and manufacturing readiness remain incomplete.')
items['placement'].update(status='partial-published-cad26-placement-not-production-CPL',note='Actual published CAD26 matches adopted ROOT101. Native component placement is review evidence; routing, mechanical/thermal/electrical qualification and final assembly/programming/test are unfinished. No production CPL released.')
c=manifest['partial_candidate'];c.update(scope='Actual Source26 and adopted working ROOT101; native CAD26 is the exact published board snapshot',published_native_revision=revision,drc_regular_violations=0,drc_unresolved_warnings=0,native_regular_DRC_clean=True,drc_pass=False,drc_reported_unconnected_items=publication['reported_unconnected_items'],uncapped_physical_missing_joins=adoption['missing_joins'],working_native_revision='ROOT101',working_board_file=relative(workboard),working_board_sha256=sha(workboard),working_adoption_path=relative(adoptpath),working_adoption_sha256=sha(adoptpath))
c['published_viewer']=dict(revision=revision,board_file=relative(pubboard),board_sha256=sha(pubboard),physical_footprints=2688,track_via_items=adoption['track_via_count'],native_zone_or_rulearea_count=1521,copper_zone_definitions=1433,ruleareas=88,positive_filled_zone_definitions=388,source_anchored_reference_components=188,uncapped_missing_joins=publication['uncapped_missing_joins'],publication_path=relative(pubroot/'publication.json'),publication_sha256=sha(pubroot/'publication.json'),bom=copy.deepcopy(binding))
evidence=[root/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json',adoptpath,adoptpath.parent/'independent-connectivity/review.json',pubroot/'publication.json']
c['evidence']=[dict(path=relative(p),sha256=sha(p))for p in evidence]
assert not manifest['manufacturing_ready']and c['fabrication_outputs']==[]
write(path,manifest)
test=root/'tests/test_release.py';old=test.read_text();before[relative(test)]=sha(test);(out/test.name).write_bytes(test.read_bytes())
start="        self.assertNotEqual(published['board_sha256'],self.manifest['partial_candidate']['working_board_sha256'])\n        self.assertEqual(4753,published['uncapped_missing_joins'])"
replacement="""        publication_path=PROJECT/published['publication_path']
        self.assertEqual(hashlib.sha256(publication_path.read_bytes()).hexdigest(),published['publication_sha256'])
        publication=json.loads(publication_path.read_text())
        self.assertEqual(revision,publication['revision'])
        self.assertTrue(publication['published'])
        self.assertEqual(published['board_sha256'],publication['native_pcb_sha256'])
        self.assertEqual(publication['uncapped_missing_joins'],published['uncapped_missing_joins'])
        candidate=self.manifest['partial_candidate']
        working=PROJECT/candidate['working_board_file']
        adoption_path=PROJECT/candidate['working_adoption_path']
        self.assertEqual(hashlib.sha256(adoption_path.read_bytes()).hexdigest(),candidate['working_adoption_sha256'])
        adoption=json.loads(adoption_path.read_text())
        self.assertTrue(adoption['adopted'])
        self.assertEqual(hashlib.sha256(working.read_bytes()).hexdigest(),candidate['working_board_sha256'])
        self.assertEqual(adoption['board_sha256'],candidate['working_board_sha256'])
        self.assertEqual(adoption['missing_joins'],candidate['uncapped_physical_missing_joins'])
        self.assertFalse(adoption['manufacturing_ready'])"""
assert old.count(start)==1
test.write_text(old.replace(start,replacement))
for stage in('prototype','production'):
 p=root/f'reports/{stage}-release-check.json';before[relative(p)]=sha(p);(out/p.name).write_bytes(p.read_bytes());result=check_release(manifest,root,stage)
 assert not result.get('ready',False)and result['blockers']
 write(p,result)
write(out/'receipt.json',dict(passed=True,changes=[dict(path=n,before_sha256=h,after_sha256=sha(root/n))for n,h in before.items()],actual_published_and_working_board_bytes_equal=True,publication_geometry_or_source_or_PCB_changed=False,viewer_BOM_metadata_restored=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,published_revision=revision,working_revision='ROOT101',missing_joins=3528,manufacturing_ready=False)))
