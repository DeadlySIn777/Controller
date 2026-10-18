import hashlib
from pathlib import Path
import tempfile
import unittest
from tools.check_release import PROTOTYPE, PRODUCTION, check_release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        artifacts = []
        for key in sorted(PROTOTYPE):
            path = self.root / f'{key}.txt'
            path.write_bytes(f'test-only {key} evidence, not a real board'.encode())
            artifacts.append({
                'id': key, 'status': 'complete', 'board_revision': 'test',
                'reviewed_by': 'test fixture', 'reviewed_at': '2026-09-28',
                'path': f'{key}.txt', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        self.path = self.root / artifacts[0]['path']
        self.manifest = {
            'schema_version': 1, 'product_revision': 'test', 'board_revision': 'test',
            'manufacturer': 'PCBWay', 'artifacts': artifacts}

    def test_complete_manifest_is_consistent(self):
        self.assertTrue(check_release(self.manifest, self.root)['ready'])

    def test_production_requires_additional_evidence(self):
        result = check_release(self.manifest, self.root, 'production')
        self.assertEqual(len(result['blockers']), len(PRODUCTION-PROTOTYPE))

    def test_deleted_required_entry_cannot_bypass(self):
        self.manifest['artifacts'].pop()
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_modified_evidence_rejected(self):
        self.path.write_bytes(b'changed after review')
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_empty_file_even_with_matching_hash_rejected(self):
        self.path.write_bytes(b'')
        self.manifest['artifacts'][0]['sha256'] = hashlib.sha256(b'').hexdigest()
        self.assertFalse(check_release(self.manifest, self.root)['ready'])

    def test_shared_evidence_file_rejected(self):
        first = self.manifest['artifacts'][0]
        self.manifest['artifacts'][1].update(path=first['path'], sha256=first['sha256'])
        result = check_release(self.manifest, self.root)
        self.assertFalse(result['ready'])
        self.assertTrue(any('shares evidence file' in b for b in result['blockers']))

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

    def test_prototype_requires_programming_and_fabrication_package(self):
        for key in ('programming_bundle', 'fabrication_spec', 'programming_test_scope'):
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

    def test_prototype_does_not_require_prior_production_test(self):
        self.manifest['artifacts'].append({'id':'hardware_test','status':'requires-prototype'})
        self.assertTrue(check_release(self.manifest, self.root)['ready'])

if __name__ == '__main__':
    unittest.main()
