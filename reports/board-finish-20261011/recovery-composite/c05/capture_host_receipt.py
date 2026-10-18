"""Record completed host controls without changing any frozen construction input."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def record(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


log = (HERE / 'host-tests-r1.log').read_text(encoding='utf-8-sig')
if 'Ran 18 tests in 120.748s' not in log or not log.rstrip().endswith('OK'):
    raise ValueError('Completed host control log differs')
frozen = {name: record(HERE / name) for name in ['compose_c05.py', 'measure_c05.py',
          'construction.json', 'c05-fag-e1-rollback-dfm.kicad_pcb', 'construction-check.json']}
expected = {'compose_c05.py': '00854648eab57280fc2987911f012c72ece1ab9b5083847f6cd5d4870fab92c4',
            'measure_c05.py': 'ce1dc397f7231632fef112238d1acdbdc1a66fb68c8ca02d1ac369bc4a3f19ca',
            'construction.json': '9670ccaf5e62c6736c8ee8030afdeedb0f0e973025afe05e2a0f8ac4d18354f7',
            'c05-fag-e1-rollback-dfm.kicad_pcb': '95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d',
            'construction-check.json': 'afdcb9e656beac70eaa339eda4aa2f10416a1522aebe932e633f0ff03f7c1241'}
if {name: item['sha256'] for name, item in frozen.items()} != expected:
    raise ValueError('Frozen c05 source identity changed during host controls')
receipt = {'schema': 'c05-host-controls-v1', 'evidence_class': 'Source reconstruction and host/model controls',
           'verdict': 'PASS', 'test_methods': 18, 'controls_including_binary_subtests': 21,
           'skips': 0, 'elapsed_seconds': 120.748, 'frozen_source_files': frozen,
           'host_files': {name: record(HERE / name) for name in ['test_c05.py', 'host-tests-r1.log']},
           'independent_evidence': {'c04_raw_error_attribution': record(ROOT / 'c04-error-attribution.json'),
                                    'exact_rollback_audit': record(ROOT / 'power-audit/c05-rollback-audit.json')},
           'controls': ['Authentic frozen c04 reconstruction and exact c05 candidate bytes',
                        'All462 new group items removed; all remaining chunks/header/tail byte exact',
                        'Incomplete and duplicate FAG/E1 ownership refused',
                        'Unapproved/swapped E1 net and changed native copper digest refused',
                        'Original r06 and retained recovery native UUID relabelling refused',
                        'Altered source/candidate bytes and constructor/source identities refused',
                        'Saved inputs.json exact-byte seal and all four native binary identities refused on mutation'],
           'earlier_test_attempt': {'log': record(HERE / 'host-tests.log'), 'tests': 18,
                                  'outcome': '17passed; one positive fixture failed on a bound parser method in test harness only',
                                  'repair': 'Changed only test_c05.py parser cache to staticmethod, then reran all18'},
           'native_job_launched_by_this_script': False, 'native_result': 'PENDING_ROOT_OWNED_MEASURE_C05_SHARED',
           'adopted': False, 'manufacturing_ready': False,
           'limits': ['Host evidence does not establish native clearance or connectivity',
                      'Final refilled uncapped strict lost=0 and raw native DRC0 remain mandatory',
                      'Same-SHA netlist parity and remaining board qualification are separate gates']}
(HERE / 'host-receipt.json').write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
print(json.dumps({'verdict': receipt['verdict'], 'test_methods': 18, 'controls': 21,
                  'candidate_sha256': expected['c05-fag-e1-rollback-dfm.kicad_pcb']}))
