"""Hash the frozen, natively tested and visually inspected r03 candidate."""
import datetime
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parent
OUT=P/'populated-r03'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
report=json.loads((OUT/'report.json').read_text(encoding='utf8'))
snapshots=json.loads((P/'frozen-source-r02/snapshot-sha256.json').read_text(encoding='utf8'))
assert all(sha(P/'frozen-source-r02'/n)==h for n,h in snapshots.items())
assert 'Ran 20 tests' in(P/'test-output-r03.txt').read_text(encoding='utf8')
assert (P/'test-output-r03.txt').read_text(encoding='utf8').rstrip().endswith('OK')
report['date']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['population'].update(source_inputs_unchanged=True,retained_zone_native_definitions_unchanged=True,
                            all_added_pad_and_stencil_templates_match_exact_source_library=True)
report['tests']=dict(native_mutation_tests=20,passed=20,report='../test-output-r03.txt')
report['native_visual_review']=dict(inspected=True,pdf='board-review.pdf',png='board-review.png',
                                   scope='Motor regions, 12 DI pairs and empty reservations visible; this is a partial board review.')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
names=['README.md','report.json','motherboard-populated-candidate.kicad_pcb','motherboard-populated-candidate.kicad_pro',
       'motherboard-populated-candidate.kicad_dru','drc.json','drc-command.txt','placement-ledger.json',
       'bounded-placement-changes.json','exact-source-pad-templates.json','board-review.pdf','board-review.png']
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),revision='populated-r03',
             source_scope='Corrected copied 880-part source; later live 980-part source is not claimed on this PCB.',
             frozen_source_file_count=len(snapshots),frozen_source_hashes_unchanged=True,
             source_board_sha256=report['source_board_sha256'],
             candidate_board_sha256=report['candidate_board_sha256'],physical_footprints=880,fitted_footprints=878,
             retained_footprints=327,retained_tracks_vias=1907,retained_filled_zones=5,
             uncapped_missing_joins=report['uncapped_native_missing_joins'],native_drc=report['native_drc'],
             native_tests=20,native_tests_passed=20,native_visual_review=report['native_visual_review'],
             bounded_actual_changed_references=report['actual_native_changed_footprints'],
             frozen_inputs=snapshots,file_sha256={n:sha(OUT/n)for n in names},
             script_sha256={n:sha(P/n)for n in ['refine-bypass-r03.py','tests-pcb-population-r03.py','test-output-r03.txt','close-r03-receipt.py']},
             manufacturing_ready=False,physical_validation=False,new_routing=False)
(P/'receipt-r03.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print({k:receipt[k]for k in ['candidate_board_sha256','uncapped_missing_joins','native_tests_passed']})
