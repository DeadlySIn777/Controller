"""Host controls for actual-live continuity; no native or bundle jobs."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import qualify_continuity as q

PINS = json.loads(q.PINS.read_bytes())
BEFORE = json.loads(Path(PINS['paths']['partitions']['path']).read_bytes())
MEASURE = q.v1.WORK / 'measure/c05-shared'
AFTER = json.loads((MEASURE / 'partitions.json').read_bytes())


def branch_fixture():
    comparison = q.v1.compare(BEFORE, AFTER)
    live = q.continuity_scope(comparison, q.lost_basis(BEFORE, AFTER))
    return {'adopted': False, 'manufacturing_ready': False, 'live_transition': live,
            'open_matrix': {'live_transition': deepcopy(live)}}


class Tests(unittest.TestCase):
    def test_actual_native_comparison_and_witnesses(self):
        guard = q.v1.compare(BEFORE, AFTER)
        self.assertEqual((guard['completed'], guard['lost']), (21, 13))
        self.assertEqual(guard['verdict'], 'FAIL')
        witnesses = q.lost_basis(BEFORE, AFTER)
        self.assertEqual(len(witnesses), 13)
        self.assertEqual({w['net'] for w in witnesses}, {net for net, info in guard['per_net'].items() if info['lost']})
        for witness in witnesses:
            with self.subTest(net=witness['net']):
                net, a, b = witness['net'], witness['pad_a'], witness['pad_b']
                self.assertTrue(any(a in group and b in group for group in BEFORE['nets'][net]))
                self.assertFalse(any(a in group and b in group for group in AFTER['nets'][net]))
        result = branch_fixture()
        q.assert_scope(result)
        self.assertFalse(result['live_transition']['direct_live_adoption_allowed'])

    def test_pins_reject_wrong_identity_or_role(self):
        q.validate_pins(PINS)
        for field in ('schema', 'live_sha256', 'qualifier_v1_sha256', 'saved_native_refilled'):
            with self.subTest(field=field):
                broken = deepcopy(PINS)
                broken[field] = 'wrong'
                with self.assertRaises(ValueError):
                    q.validate_pins(broken)
        for role in q.BOARD_ROLES:
            with self.subTest(role=role):
                broken = deepcopy(PINS)
                broken['paths'][role]['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    q.validate_pins(broken)
        broken = deepcopy(PINS)
        broken['paths'].pop('manifest')
        with self.assertRaises(ValueError):
            q.validate_pins(broken)

    def test_actual_hash_change_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'host-input.txt'
            path.write_text('original host sentinel')
            expected = q.v1.digest(path.read_bytes())
            reads = q.v1.ReadSet()
            q.v1.tracked(reads, path, expected)
            path.write_text('changed host sentinel')
            with self.assertRaises(ValueError):
                q.v1.tracked(q.v1.ReadSet(), path, expected)
            with self.assertRaises(ValueError):
                reads.verify()

    def test_stale_partition_headers_rejected_after_hash_boundary(self):
        original_json = q.v1.ReadSet.json
        path = Path(PINS['paths']['partitions']['path']).resolve()
        args = SimpleNamespace(measure=MEASURE)
        for field, wrong in [('sha256', '0' * 64), ('refilled', False), ('board', str(MEASURE / 'copy/board.kicad_pcb'))]:
            with self.subTest(field=field):
                result = {'adopted': False, 'manufacturing_ready': False, 'open_matrix': {},
                          'project_hashes': {name: PINS['native_manifest'][name] for name in q.v1.PROJECT_NAMES}}
                reads = q.v1.ReadSet()

                def corrupt_json(instance, source):
                    value = original_json(instance, source)
                    if Path(source).resolve() == path:
                        value[field] = wrong
                    return value

                with patch.object(q.v1, 'evaluate', return_value=(result, reads)), \
                     patch.object(q.v1.ReadSet, 'json', corrupt_json):
                    with self.assertRaises(ValueError):
                        q.evaluate(args)

    def test_loss_and_adoption_bypasses_rejected(self):
        mutations = [
            lambda r: r.update(adopted=True),
            lambda r: r.update(manufacturing_ready=True),
            lambda r: r['live_transition'].update(direct_live_adoption_allowed=True),
            lambda r: r['live_transition'].update(live_adoption_withheld=False),
            lambda r: r['live_transition']['comparison'].update(verdict='PASS'),
            lambda r: r['live_transition']['comparison'].update(lost=0),
            lambda r: r['live_transition'].update(lost_relationship_basis=[]),
            lambda r: r['open_matrix']['live_transition']['comparison'].update(lost=0),
        ]
        for number, mutation in enumerate(mutations):
            with self.subTest(case=number):
                result = branch_fixture()
                mutation(result)
                with self.assertRaises(ValueError):
                    q.assert_scope(result)

    def test_pending_archive_cannot_have_pass_receipt(self):
        result = branch_fixture()
        captured = {}

        def interrupted(args, staged, reads):
            captured.update(deepcopy(staged))
            raise RuntimeError('Host interruption control before any files are created')

        with patch.object(q.v1, 'create_bundle', side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                q.create_bundle(SimpleNamespace(), result, q.v1.ReadSet(), PINS)
        self.assertEqual(captured['verdict'], 'STAGING_EXPERIMENTAL_NATIVE_EVIDENCE')
        self.assertEqual(captured['continuity_archive_state'], 'PENDING')
        self.assertFalse(captured['live_transition']['direct_live_adoption_allowed'])


if __name__ == '__main__':
    unittest.main()
