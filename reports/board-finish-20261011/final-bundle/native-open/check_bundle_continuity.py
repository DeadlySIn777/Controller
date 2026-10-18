"""Read-only full manifest and explicit live-loss envelope around native alias open."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'continuity-v2'))
import qualify_continuity as q


def envelope(bundle):
    qualification = bundle / 'qualification.json'
    result = json.loads(qualification.read_bytes())
    q.v1.require(result['schema'] == 'experimental-native-bundle-v2'
                 and result['verdict'] == 'PASS_EXPERIMENTAL_NATIVE_EVIDENCE'
                 and result['continuity_archive_state'] == 'COMPLETE', 'V2 bundle is not complete/qualified')
    q.assert_scope(result)
    comparison = result['live_transition']['comparison']
    q.v1.require((comparison['completed'], comparison['lost']) == (21, 13)
                 and comparison['before_sha256'] == q.LIVE_SHA, 'Expected actual-live loss scope differs')
    actual = {}
    for relative, entry in result['bundle']['manifest'].items():
        path = (bundle / relative).resolve()
        q.v1.require(path.is_relative_to(bundle) and path != bundle and not path.is_symlink(), 'Unsafe manifest source')
        actual[relative] = q.v1.digest(path.read_bytes())
        q.v1.require(actual[relative] == entry['sha256'], 'Changed bundle manifest member: ' + relative)
    return {'bundle': str(bundle), 'qualification_sha256': q.v1.digest(qualification.read_bytes()),
            'manifest_file_hashes': actual, 'live_transition': result['live_transition'],
            'direct_live_adoption_allowed': False, 'native_jobs': 0, 'source_or_bundle_mutations': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--before', type=Path)
    args = parser.parse_args()
    bundle, out = args.bundle.resolve(), args.out.resolve()
    q.v1.require(bundle.is_relative_to(HERE.parent) and out.is_relative_to(HERE)
                 and not out.exists() and out != HERE, 'New isolated check receipt required')
    result = envelope(bundle)
    if args.before is not None:
        before = json.loads(args.before.read_bytes())
        q.v1.require(result == before, 'Bundle manifest or live-loss scope changed during alias open')
        result = {'verdict': 'PASS', 'before_receipt_sha256': q.v1.digest(args.before.read_bytes()),
                  'entire_manifest_unchanged': True, 'live_loss_scope_unchanged': True, 'envelope': result}
    out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(out), 'sha256': q.v1.digest(out.read_bytes()),
                      'manifest_files': len(result.get('envelope', result)['manifest_file_hashes']),
                      'live_completed': 21, 'live_lost': 13, 'direct_live_adoption_allowed': False}))


if __name__ == '__main__':
    main()
