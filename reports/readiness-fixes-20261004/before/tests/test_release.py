import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.check_release import (PROTOTYPE, PRODUCTION, QUOTE_PACKAGE, QUOTE_PREREQUISITES,
                                 check_release)

PROJECT = Path(__file__).resolve().parents[1]


def _write_evidence(root, key):
    """Distinct, clearly labelled test-only bytes inside the temporary directory only."""
    path = root / f'{key}.txt'
    path.write_bytes(f'test-only {key} evidence, not a real board artifact'.encode())
    return {'id': key, 'status': 'complete', 'board_revision': 'test',
            'reviewed_by': 'test fixture', 'reviewed_at': '2026-09-28',
            'path': f'{key}.txt', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        artifacts = [_write_evidence(self.root, key) for key in sorted(PROTOTYPE)]
        self.path = self.root / artifacts[0]['path']
        self.manifest = {
            'schema_version': 1, 'product_revision': 'test', 'board_revision': 'test',
            'manufacturer': 'PCBWay', 'artifacts': artifacts}
        by_id = self.items()
        by_id['pcbway_quote'].update(
            requires=sorted(QUOTE_PREREQUISITES), quantities=[1, 10],
            submission={
                'quote_id': 'test-only-quote', 'quoted_at': '2026-09-28',
                'submitted_by': 'test fixture', 'board_revision': 'test',
                'quantities': [1, 10],
                'package_sha256': {k: by_id[k]['sha256'] for k in QUOTE_PACKAGE},
                # Test-only numbers for the checker's structure rules; not a PCBWay quote.
                'figures': [
                    {'quantity': 1, 'currency': 'USD', 'unit_price': 1.0, 'setup_cost': 0,
                     'lead_time_days': 1},
                    {'quantity': 10, 'currency': 'USD', 'unit_price': 0.5, 'setup_cost': 0,
                     'lead_time_days': 1}]})

    def items(self, manifest=None):
        return {a['id']: a for a in (manifest or self.manifest)['artifacts']}

    def blockers(self, stage='prototype'):
        result = check_release(self.manifest, self.root, stage)
        self.assertFalse(result['ready'])
        return result['blockers']

    def add_production_evidence(self):
        for key in sorted(PRODUCTION - PROTOTYPE):
            self.manifest['artifacts'].append(_write_evidence(self.root, key))

    def test_complete_manifest_is_consistent(self):
        result = check_release(self.manifest, self.root)
        self.assertTrue(result['ready'], result['blockers'])
        self.assertEqual(set(result), {'stage', 'ready', 'blockers', 'meaning'})

    def test_production_requires_additional_evidence(self):
        result = check_release(self.manifest, self.root, 'production')
        self.assertEqual(len(result['blockers']), len(PRODUCTION-PROTOTYPE))

    def test_complete_production_manifest_is_consistent(self):
        self.add_production_evidence()
        result = check_release(self.manifest, self.root, 'production')
        self.assertTrue(result['ready'], result['blockers'])

    def test_deleted_required_entry_cannot_bypass(self):
        self.manifest['artifacts'].pop()
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_modified_evidence_rejected(self):
        self.path.write_bytes(b'changed after review')
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_empty_file_even_with_matching_hash_rejected(self):
        self.path.write_bytes(b'')
        self.manifest['artifacts'][0]['sha256'] = hashlib.sha256(b'').hexdigest()
        blockers = self.blockers()
        self.assertIn(f"{self.manifest['artifacts'][0]['id']}: empty evidence file", blockers)
        self.assertFalse(any('identical' in b or 'shares' in b for b in blockers))

    def test_shared_evidence_file_rejected(self):
        first, second = self.manifest['artifacts'][:2]
        second.update(path=first['path'], sha256=first['sha256'])
        self.assertIn(f"{second['id']}: shares evidence file with {first['id']}", self.blockers())

    def test_identical_evidence_bytes_rejected(self):
        # A copied placeholder saved under another name has a new path but the same bytes.
        first, second = self.manifest['artifacts'][:2]
        copy = self.root / 'renamed-copy.bin'
        copy.write_bytes((self.root / first['path']).read_bytes())
        second.update(path='renamed-copy.bin', sha256=first['sha256'])
        blockers = self.blockers()
        self.assertIn(f"{second['id']}: evidence bytes identical to {first['id']} (same SHA-256)",
                      blockers)
        self.assertFalse(any('shares evidence file' in b for b in blockers))

    def test_one_placeholder_for_every_artifact_rejected(self):
        placeholder = self.root / 'evidence.txt'
        placeholder.write_bytes(b'test-only evidence, not a real board')
        digest = hashlib.sha256(placeholder.read_bytes()).hexdigest()
        for entry in self.manifest['artifacts']:
            entry.update(path='evidence.txt', sha256=digest)
        blockers = self.blockers()
        self.assertEqual(sum('shares evidence file' in b for b in blockers), len(PROTOTYPE) - 1)

    def test_missing_or_escaping_path_rejected(self):
        for path in ['missing.txt', '../evidence.txt', '/tmp/evidence.txt', 'C:/file', 'a\\b']:
            with self.subTest(path=path):
                self.manifest['artifacts'][0]['path'] = path
                self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_wrong_revision_rejected(self):
        self.manifest['artifacts'][0]['board_revision'] = 'older'
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_unreviewed_rejected(self):
        self.manifest['artifacts'][0]['reviewed_by'] = ''
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_duplicate_rejected(self):
        self.manifest['artifacts'].append(dict(self.manifest['artifacts'][0]))
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_status_draft_rejected(self):
        self.manifest['artifacts'][0]['status'] = 'draft'
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_bad_hash_rejected(self):
        self.manifest['artifacts'][0]['sha256'] = '123'
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_malformed_manifest(self):
        for data in [None, [], {}, {'schema_version': True}]:
            self.assertFalse(check_release(data, self.root)['ready'])

    def test_prototype_requires_programming_fabrication_and_link_evidence(self):
        for key in ('programming_bundle', 'fabrication_spec', 'programming_test_scope',
                    'link_prototype_measurement'):
            with self.subTest(key=key):
                self.assertIn(key, PROTOTYPE)
                manifest = dict(self.manifest)
                manifest['artifacts'] = [dict(a) for a in self.manifest['artifacts']]
                for entry in manifest['artifacts']:
                    if entry['id'] == key:
                        entry['status'] = 'blocked-by-layout'
                result = check_release(manifest, self.root)
                self.assertFalse(result['ready'])
                self.assertIn(f'{key}: blocked-by-layout', result['blockers'])

    def test_removing_programming_bundle_blocks_release(self):
        self.manifest['artifacts'] = [a for a in self.manifest['artifacts']
                                      if a['id'] != 'programming_bundle']
        self.assertIn('programming_bundle: required evidence missing', self.blockers())

    def test_prototype_does_not_require_prior_production_test(self):
        self.manifest['artifacts'].append({'id':'hardware_test','status':'requires-prototype'})
        self.assertTrue(check_release(self.manifest, self.root)['ready'])

    def test_quote_record_must_be_structured(self):
        cases = {
            'requires': ('pcbway_quote: structured quote record needs a requires list', None),
            'quantities': ('pcbway_quote: quantities must list positive whole-unit quote '
                           'quantities', [0]),
        }
        for field, (message, value) in cases.items():
            with self.subTest(field=field):
                self.setUp()
                self.items()['pcbway_quote'][field] = value
                self.assertIn(message, self.blockers())
        self.setUp()
        del self.items()['pcbway_quote']['submission']
        self.assertIn('pcbway_quote: submission must be recorded (null until a real quote exists)',
                      self.blockers())

    def test_quote_prerequisite_list_cannot_be_shortened(self):
        quote = self.items()['pcbway_quote']
        quote['requires'] = [k for k in quote['requires'] if k not in ('drc', 'programming_bundle')]
        self.assertIn('pcbway_quote: requires omits drc, programming_bundle', self.blockers())

    def test_quote_complete_without_submission_rejected(self):
        self.items()['pcbway_quote']['submission'] = None
        self.assertIn('pcbway_quote: complete without a recorded supplier submission',
                      self.blockers())

    def test_quote_complete_before_layout_rejected(self):
        self.items()['pcb_layout']['status'] = 'not-created'
        blockers = self.blockers()
        self.assertIn('pcbway_quote: complete while prerequisite pcb_layout is not-created', blockers)

    def test_quote_for_other_board_revision_rejected(self):
        # The eight-motor candidate must be quoted as its own revision, never as the baseline.
        self.items()['pcbway_quote']['submission']['board_revision'] = 'expanded-8j-4enc-r0'
        self.assertIn('pcbway_quote: submission is for a different board revision',
                      self.blockers())

    def test_quote_package_hash_must_match_released_files(self):
        self.items()['pcbway_quote']['submission']['package_sha256']['placement'] = '0' * 64
        self.assertIn('pcbway_quote: submission package hash for placement does not match '
                      'released evidence', self.blockers())

    def test_quote_submission_fields_required(self):
        self.items()['pcbway_quote']['submission']['quote_id'] = ''
        self.assertIn('pcbway_quote: submission quote_id missing', self.blockers())

    def test_quote_identity_fields_must_be_non_blank_strings(self):
        # Same rule as reviewed_by/reviewed_at: whitespace or a non-string is not a record.
        cases = {'quote_id': '   ', 'submitted_by': 0, 'quoted_at': ' 	',
                 'board_revision': 7}
        for field, value in cases.items():
            with self.subTest(field=field, value=value):
                self.setUp()
                self.items()['pcbway_quote']['submission'][field] = value
                self.assertIn(f'pcbway_quote: submission {field} missing', self.blockers())

    def test_quote_date_must_be_iso(self):
        for value in ('not-a-date', '28/09/2026', '2026-13-01'):
            with self.subTest(value=value):
                self.items()['pcbway_quote']['submission']['quoted_at'] = value
                self.assertIn('pcbway_quote: submission quoted_at must be an ISO 8601 date',
                              self.blockers())
        self.items()['pcbway_quote']['submission']['quoted_at'] = '2026-09-28T10:15:00+00:00'
        self.assertTrue(check_release(self.manifest, self.root)['ready'])

    def test_quote_figures_required(self):
        submission = self.items()['pcbway_quote']['submission']
        for value in (None, []):
            with self.subTest(value=value):
                submission['figures'] = value
                self.assertIn('pcbway_quote: submission figures missing', self.blockers())
        del submission['figures']
        self.assertIn('pcbway_quote: submission figures missing', self.blockers())
        submission['figures'] = {'quantity': 1}
        self.assertIn('pcbway_quote: submission figures must be a list', self.blockers())

    def test_quote_figures_must_cover_quoted_quantities(self):
        submission = self.items()['pcbway_quote']['submission']
        submission['figures'] = submission['figures'][:1]
        self.assertIn('pcbway_quote: submission figures must cover exactly the quoted quantities',
                      self.blockers())
        submission['figures'] = [dict(submission['figures'][0]) for _ in range(2)]
        self.assertIn('pcbway_quote: submission figures repeat a quantity', self.blockers())

    def test_quote_figure_values_validated(self):
        cases = {
            'quantity': (0, 'quantity must be a positive whole number'),
            'currency': ('usd', 'currency must be an ISO 4217 code'),
            'unit_price': (-1, 'unit_price must be a non-negative number'),
            'setup_cost': (float('nan'), 'setup_cost must be a non-negative number'),
            'lead_time_days': (2.5, 'lead_time_days must be a positive whole number'),
        }
        for field, (value, message) in cases.items():
            with self.subTest(field=field):
                self.setUp()
                self.items()['pcbway_quote']['submission']['figures'][1][field] = value
                self.assertIn(f'pcbway_quote: submission figures[1] {message}', self.blockers())
        self.setUp()
        del self.items()['pcbway_quote']['submission']['figures'][0]['lead_time_days']
        self.assertIn('pcbway_quote: submission figures[0] missing lead_time_days', self.blockers())
        self.setUp()
        self.items()['pcbway_quote']['submission']['figures'][0]['unit_price'] = True
        self.assertIn('pcbway_quote: submission figures[0] unit_price must be a non-negative number',
                      self.blockers())

    def test_final_cost_requires_completed_quote(self):
        self.add_production_evidence()
        self.items()['pcbway_quote']['status'] = 'not-requested-design-incomplete'
        self.assertIn('final_cost: complete while pcbway_quote is not-requested-design-incomplete',
                      self.blockers('production'))


class LiveManifestTests(unittest.TestCase):
    """The canonical manifest records every gate and matches its regenerated reports."""

    def setUp(self):
        self.manifest = json.loads(
            (PROJECT / 'manufacturing/release-manifest.json').read_text(encoding='utf-8'))
        self.items = {a['id']: a for a in self.manifest['artifacts']}

    def test_every_gate_is_recorded(self):
        for stage in ('prototype', 'production'):
            result = check_release(self.manifest, PROJECT, stage)
            self.assertFalse(any('required evidence missing' in b or 'duplicate' in b
                                 for b in result['blockers']), result['blockers'])

    def test_quote_record_is_structured_and_empty(self):
        quote = self.items['pcbway_quote']
        self.assertLessEqual(QUOTE_PREREQUISITES, set(quote['requires']))
        self.assertIsNone(quote['submission'])
        result = check_release(self.manifest, PROJECT)
        self.assertEqual([b for b in result['blockers'] if b.startswith('pcbway_quote:')],
                         [f"pcbway_quote: {quote['status']}"])

    def test_partial_designator_bom_does_not_claim_complete_controller(self):
        self.assertNotEqual('complete', self.items['bom']['status'])
        self.assertFalse(self.manifest['manufacturing_ready'])
        folder=PROJECT/'hardware/motherboard'
        source=json.loads((folder/'design.json').read_text(encoding='utf-8'))
        with (folder/'bom.csv').open(encoding='utf-8-sig',newline='') as handle:
            rows=list(csv.DictReader(handle))
        self.assertEqual(set(source['components']),{r['Reference'] for r in rows})
        self.assertEqual(len(rows),len(source['components']))
        self.assertEqual(len(rows),self.manifest['partial_candidate']['electrical_source_footprints'])

    def test_viewer_bom_is_bound_to_its_actual_frozen_published_revision(self):
        viewer=json.loads((PROJECT/'hardware/board_review/board-view.json').read_text())
        revision=viewer['current_revision'];board=viewer['boards'][0];binding=self.items['bom']
        self.assertEqual(revision,binding['published_revision'])
        path=PROJECT/'hardware/board_review'/board['bom_file']
        self.assertEqual(path.resolve(),(PROJECT/binding['path']).resolve())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),binding['sha256'])
        self.assertEqual(binding['sha256'],board['bom_sha256'])
        frozen=json.loads((PROJECT/binding['source_design_path']).read_text())
        self.assertEqual(hashlib.sha256((PROJECT/binding['source_design_path']).read_bytes()).hexdigest(),binding['source_design_sha256'])
        with path.open(encoding='utf-8-sig',newline='')as handle:rows=list(csv.DictReader(handle))
        self.assertEqual(set(frozen['components']),{r['Reference']for r in rows})
        self.assertEqual(binding['physical_footprints'],len(rows))
        published=self.manifest['partial_candidate']['published_viewer']
        self.assertEqual(revision,published['revision'])
        self.assertEqual(hashlib.sha256((PROJECT/published['board_file']).read_bytes()).hexdigest(),published['board_sha256'])
        publication_path=PROJECT/published['publication_path']
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
        self.assertFalse(adoption['manufacturing_ready'])
        self.assertFalse(self.manifest['manufacturing_ready'])

    def test_reports_match_checker(self):
        for stage in ('prototype', 'production'):
            with self.subTest(stage=stage):
                recorded = (PROJECT / f'reports/{stage}-release-check.json').read_bytes()
                expected = json.dumps(check_release(self.manifest, PROJECT, stage),
                                      indent=2) + '\n'
                self.assertEqual(recorded, expected.encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
