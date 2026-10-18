"""Wrap the frozen v1 qualifier with an explicit actual-live continuity gate.

Only a root-invoked bundle run creates files. --check-only saves host revalidation
without creating an editable bundle. No live board, shared tool, native job,
refill, DRC, save, fabrication export or adoption is performed here.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import qualify_bundle as v1
from finish_bridge_proof import manifest

V1_SHA = 'eda72ec6559194a403dad2fed5fc78ae2d82520cebf2bb3fa88096e872344bc1'
LIVE_PINS_SHA = '09478c4c62663d3647a6652cc1b38c0971bee2ac507a1feb7e07181299a06f21'
LIVE_SHA = '0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
PINS = HERE / 'live-inputs.json'
BOARD_ROLES = {'revision_board', 'r08_board', 'live_board', 'applied_board', 'copy_board'}
ROLES = BOARD_ROLES | {'partitions', 'manifest', 'summary', 'raw_drc', 'drc_log', 'report'} | v1.PROJECT_NAMES


def validate_pins(pins):
    v1.require(pins.get('schema') == 'live-r07-continuity-inputs-v1'
               and pins.get('live_sha256') == LIVE_SHA
               and pins.get('qualifier_v1_sha256') == V1_SHA
               and pins.get('saved_native_refilled') is True,
               'Actual live native continuity pins are invalid')
    v1.require(set(pins['paths']) == ROLES, 'Live continuity role inventory is incomplete')
    v1.require(all(pins['paths'][role]['sha256'] == LIVE_SHA for role in BOARD_ROLES),
               'Live/revision/r08/native board SHA identity differs')


def lost_basis(before, after):
    """Minimal actual pad relationships present before but absent afterwards."""
    witnesses = []
    for net in sorted(before['nets']):
        groups = after['nets'][net]
        index = {pad: number for number, group in enumerate(groups) for pad in group}
        parent = list(range(len(groups)))

        def find(number):
            while parent[number] != number:
                parent[number] = parent[parent[number]]
                number = parent[number]
            return number

        for group in before['nets'][net]:
            first = group[0]
            for pad in group[1:]:
                left, right = find(index[first]), find(index[pad])
                if left != right:
                    witnesses.append({'net': net, 'pad_a': first, 'pad_b': pad,
                                      'meaning': 'Connected in saved refilled live r07; separate candidate islands'})
                    parent[right] = left
    return witnesses


def continuity_scope(comparison, witnesses):
    v1.require(comparison.get('partition_identity_check') is True,
               'Direct-live partition identity cannot be verified')
    v1.require(type(comparison.get('lost')) is int and comparison['lost'] >= 0
               and len(witnesses) == comparison['lost'], 'Direct-live loss accounting differs')
    if comparison['lost']:
        v1.require(comparison.get('verdict') == 'FAIL', 'Lost live relationships bypassed strict guard')
    return {'status': 'FAIL_LOST_RELATIONSHIPS' if comparison['lost'] else comparison['verdict'],
            'comparison': comparison, 'lost_relationship_basis': witnesses,
            'actual_live_and_saved_r08_sha256': LIVE_SHA,
            'direct_live_adoption_allowed': False, 'live_adoption_withheld': True,
            'direct_live_connectivity_gate_passed': comparison['verdict'] == 'PASS' and comparison['lost'] == 0,
            'scope': 'Experimental branch may pass its r06 baseline gate while failing direct transition from current r07/r08. No live adoption is performed or authorized by this qualifier.'}


def assert_scope(result):
    live = result['live_transition']
    v1.require(result.get('adopted') is False and result.get('manufacturing_ready') is False,
               'Experimental scope changed')
    v1.require(live.get('direct_live_adoption_allowed') is False and live.get('live_adoption_withheld') is True,
               'Live adoption cannot be claimed by experimental bundle')
    expected = continuity_scope(live['comparison'], live['lost_relationship_basis'])
    v1.require(live == expected, 'Live-loss limitation or count was bypassed')
    v1.require(result['open_matrix']['live_transition'] == live,
               'Open matrix hides or changes live-transition loss')


def evaluate(args):
    # Frozen v1 retains every exact-candidate native/DRC/API/export/project gate.
    result, reads = v1.evaluate(args)
    v1.tracked(reads, HERE.parent / 'qualify_bundle.py', V1_SHA)
    pins = json.loads(v1.tracked(reads, PINS, LIVE_PINS_SHA))
    validate_pins(pins)
    for entry in pins['paths'].values():
        v1.tracked(reads, entry['path'], entry['sha256'])
    paths = {role: Path(entry['path']) for role, entry in pins['paths'].items()}
    before = reads.json(paths['partitions'])
    after = reads.json(args.measure.resolve() / 'partitions.json')
    v1.require(before['sha256'] == LIVE_SHA and before['refilled'] is True,
               'Live native partition receipt is stale or unrefilled')
    v1.require(Path(before['board']).resolve() == paths['copy_board'].resolve(),
               'Native live partitions do not describe pinned exact native copy')
    members = manifest(reads.read(paths['manifest']))
    v1.require(members == pins['native_manifest'] and members['board.kicad_pcb'] == LIVE_SHA,
               'Native live manifest differs')
    for name in v1.PROJECT_NAMES:
        v1.require(v1.digest(reads.read(paths[name])) == members[name] == result['project_hashes'][name],
                   'Live/candidate measured project/rules/netlist/table differ: ' + name)
    drc = v1.check_summary(reads.json(paths['raw_drc']), before, reads.json(paths['summary']), LIVE_SHA)
    v1.require(drc == pins['native_drc'] and drc['errors'] == 0, 'Native live DRC receipt is stale')
    comparison = v1.compare(before, after)
    result['schema'] = 'experimental-native-bundle-v2'
    result['live_transition'] = continuity_scope(comparison, lost_basis(before, after))
    result['open_matrix']['live_transition'] = deepcopy(result['live_transition'])
    result['continuity_inputs'] = {'path': str(PINS), 'sha256': LIVE_PINS_SHA,
                                   'preserved_v1_checker_sha256': V1_SHA,
                                   'native_live_manifest': members, 'native_live_drc': drc}
    result['continuity_checker_sha256'] = v1.digest(reads.read(__file__))
    assert_scope(result)
    reads.verify()
    result['observed_file_hashes'] = dict(reads.hashes)
    return result, reads, pins


def create_bundle(args, result, reads, pins):
    assert_scope(result)
    # An interruption during copying leaves a visibly unqualified staging receipt.
    staged = deepcopy(result)
    staged['verdict'] = 'STAGING_EXPERIMENTAL_NATIVE_EVIDENCE'
    staged['continuity_archive_state'] = 'PENDING'
    out = v1.create_bundle(args, staged, reads)
    archive = out / 'evidence/live-transition'
    sources = {'r07-board.kicad_pcb': pins['paths']['revision_board']['path'],
               'r07-live-inputs.json': str(PINS), 'qualify_continuity.py': str(Path(__file__).resolve())}
    archive_names = {'partitions': 'partitions.json', 'manifest': 'sha256.txt', 'summary': 'summary.json',
                     'raw_drc': 'drc.json', 'drc_log': 'drc.log', 'report': 'report.json'}
    sources.update({name: pins['paths'][role]['path'] for role, name in archive_names.items()})
    sources.update({'project/' + name: pins['paths'][name]['path'] for name in v1.PROJECT_NAMES})
    for relative, source in sources.items():
        target = archive / relative
        v1.require(not target.exists() and target.resolve().is_relative_to(out), 'Continuity archive collision')
        data = reads.read(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        v1.require(v1.digest(target.read_bytes()) == v1.digest(data), 'Continuity archive differs')
        target.chmod(stat.S_IREAD)
        staged['bundle']['manifest'][target.relative_to(out).as_posix()] = {
            'source': str(Path(source).resolve()), 'sha256': v1.digest(data)}
    # The final receipt takes the completed v1 archive paths plus all v2 limitations.
    result['bundle'] = staged['bundle']
    result['continuity_archive_state'] = 'COMPLETE'
    result['observed_file_hashes'] = dict(reads.hashes)
    assert_scope(result)
    reads.verify()
    for relative, entry in result['bundle']['manifest'].items():
        v1.require(v1.digest((out / relative).read_bytes()) == entry['sha256'], 'Bundle starting bytes changed')
    readme = out / 'README.txt'
    text = readme.read_text(encoding='utf-8')
    live = result['live_transition']['comparison']
    prefix = (f"DIRECT LIVE TRANSITION: {live['completed']} completed; {live['lost']} lost versus current r07/r08.\n"
              "LIVE ADOPTION WITHHELD. This is a separately qualified experimental branch; CAD30 and the live ROOT106 board remain separate.\n\n")
    readme.chmod(stat.S_IREAD | stat.S_IWRITE)
    readme.write_text(prefix + text, encoding='utf-8')
    readme.chmod(stat.S_IREAD)
    qualification = out / 'qualification.json'
    temporary = out / 'qualification-v2.part'
    temporary.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    qualification.chmod(stat.S_IREAD | stat.S_IWRITE)
    temporary.replace(qualification)
    qualification.chmod(stat.S_IREAD)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('board', 'measure', 'parity', 'source-export', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--binding-audit', type=Path, default=v1.WORK / 'power-audit/project-binding-audit.json')
    parser.add_argument('--symbol-library-root', type=Path, default=Path('Z:/pcb-runs/claude-finish/review/schematic/erc_full'))
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    result, reads, pins = evaluate(args)
    if args.check_only:
        v1.require(args.receipt is not None, '--check-only requires a separate receipt path')
        target = args.receipt.resolve()
        v1.require(target.is_relative_to(HERE) and not target.exists() and target != HERE,
                   'Host evaluation receipt must be a new continuity-v2 file')
        v1.require(not args.out.exists(), 'Prospective bundle destination already exists')
        reads.verify()
        result['final_bundle_produced'] = False
        target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    else:
        v1.require(args.receipt is None, '--receipt is only for --check-only')
        create_bundle(args, result, reads, pins)
    print(json.dumps({'verdict': result['verdict'], 'board_sha256': args.sha256,
                      'r06_completed': result['connectivity']['completed'], 'r06_lost': result['connectivity']['lost'],
                      'live_completed': result['live_transition']['comparison']['completed'],
                      'live_lost': result['live_transition']['comparison']['lost'],
                      'direct_live_adoption_allowed': False, 'final_bundle_produced': not args.check_only}))


if __name__ == '__main__':
    main()
