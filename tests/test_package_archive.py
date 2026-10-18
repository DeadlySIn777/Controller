"""Real codec and hostile archive tests; temporary stores, never extract or execute."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from controller_config import package_archive as archive


def manifest_for(entries):
    return {"schema_version": 1, "format": "controller-package-tar-zstd", "kind": "support",
            "metadata": {"fixture": "host-test-only"}, "payload_bytes": sum(map(len, entries.values())),
            "entries": [{"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                        for name, data in entries.items()]}


def tar_bytes(members, format=tarfile.USTAR_FORMAT):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w", format=format) as output:
        for name, data, type_, link in members:
            info = tarfile.TarInfo(name)
            info.type, info.linkname, info.size = type_, link, len(data)
            output.addfile(info, io.BytesIO(data))
    return result.getvalue()


class BackendAvailabilityTests(unittest.TestCase):
    def test_optional_backend_is_explicit_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(archive, '_zstd', None):
            self.assertFalse(archive.capabilities()['available'])
            for function, args in ((archive.compress_bytes, (b'x',)),
                                   (archive.decompress_bytes, (b'x', 10)),
                                   (archive.create_archive, (Path(directory) / 'x.zst', {'x': b'x'}, 'support')),
                                   (archive.read_archive, (Path(directory) / 'missing.zst',))):
                with self.subTest(function=function.__name__), self.assertRaises(archive.ArchiveError) as error:
                    function(*args)
                self.assertEqual(error.exception.code, 'ARCHIVE_UNAVAILABLE')
            self.assertEqual(list(Path(directory).iterdir()), [])


@unittest.skipUnless(archive.capabilities()['available'], 'Optional compression.zstd backend unavailable')
class PackageArchiveTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.path = self.folder / 'package.tar.zst'
        self.entries = {'report.json': b'{"simulation_only":true}', 'logs/one.txt': b'fixture\n' * 100}

    def forged(self, *, entries=None, manifest=None, extra=(), raw=None):
        entries = self.entries if entries is None else entries
        manifest = manifest_for(entries) if manifest is None else manifest
        if raw is None:
            manifest_bytes = manifest if type(manifest) is bytes else json.dumps(manifest).encode()
            raw = tar_bytes([('manifest.json', manifest_bytes, tarfile.REGTYPE, ''),
                             *[(name, data, tarfile.REGTYPE, '') for name, data in entries.items()], *extra])
        self.path.write_bytes(archive.compress_bytes(raw))
        return self.path

    def reject(self, *, codes=None, **kwargs):
        self.forged(**kwargs)
        before = self.path.read_bytes()
        with self.assertRaises(archive.ArchiveError) as error:
            archive.read_archive(self.path)
        if codes:
            self.assertIn(error.exception.code, codes)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(set(p.name for p in self.folder.iterdir()), {self.path.name})

    def test_all_kinds_roundtrip_bytes_metadata_and_checksums_without_extraction(self):
        self.entries['empty.bin'] = b''
        for kind in archive.KINDS:
            with self.subTest(kind=kind):
                destination = self.folder / (kind + '.tar.zst')
                receipt = archive.create_archive(destination, self.entries, kind,
                                                 {'fixture': True, 'unicode': '\u03b1', 'nested': [1, None, 1.5]})
                result = archive.read_archive(destination, expected_kind=kind)
                self.assertEqual(result['entries'], self.entries)
                self.assertEqual(result['manifest'], receipt['manifest'])
                self.assertEqual(result['sha256'], hashlib.sha256(destination.read_bytes()).hexdigest())
                self.assertFalse(result['executed'])
                self.assertFalse(result['configuration_applied'])
        self.assertEqual(len(list(self.folder.iterdir())), 3)

    def test_deterministic_package_bytes_and_source_entries_unchanged(self):
        before = deepcopy(self.entries)
        one = self.folder / 'one.zst'
        two = self.folder / 'two.zst'
        archive.create_archive(one, self.entries, 'job')
        archive.create_archive(two, dict(reversed(list(self.entries.items()))), 'job')
        self.assertEqual(one.read_bytes(), two.read_bytes())
        self.assertEqual(self.entries, before)

    def test_existing_destination_is_never_overwritten(self):
        self.path.write_bytes(b'user-owned')
        with self.assertRaises(archive.ArchiveError) as error:
            archive.create_archive(self.path, self.entries, 'support')
        self.assertEqual(error.exception.code, 'ARCHIVE_EXISTS')
        self.assertEqual(self.path.read_bytes(), b'user-owned')
        self.assertEqual(list(self.folder.iterdir()), [self.path])

    def test_publication_race_keeps_winner_and_removes_temporary(self):
        def competitor(source, destination, **kwargs):
            Path(destination).write_bytes(b'concurrent-owner')
            raise FileExistsError('fixture concurrent publication')
        with patch.object(archive.os, 'link', side_effect=competitor), self.assertRaises(archive.ArchiveError) as error:
            archive.create_archive(self.path, self.entries, 'config')
        self.assertEqual(error.exception.code, 'ARCHIVE_EXISTS')
        self.assertEqual(self.path.read_bytes(), b'concurrent-owner')
        self.assertEqual(list(self.folder.iterdir()), [self.path])

    def test_failed_fsync_or_unsupported_atomic_link_publishes_nothing(self):
        for operation in ('fsync', 'link'):
            with self.subTest(operation=operation), patch.object(archive.os, operation, side_effect=OSError('fixture failure')):
                with self.assertRaises(archive.ArchiveError) as error:
                    archive.create_archive(self.path, self.entries, 'support')
                self.assertEqual(error.exception.code, 'ARCHIVE_IO')
                self.assertEqual(list(self.folder.iterdir()), [])

    def test_directory_flush_failure_preserves_published_archive_and_reports_uncertain_ack(self):
        with patch.object(archive, '_sync_directory', side_effect=OSError('fixture directory flush failure')):
            with self.assertRaises(archive.ArchiveError) as error:
                archive.create_archive(self.path, self.entries, 'support')
        self.assertEqual(error.exception.code, 'ARCHIVE_PUBLICATION_UNCERTAIN')
        self.assertIn(str(self.path), str(error.exception))
        self.assertEqual(archive.read_archive(self.path)['entries'], self.entries)
        self.assertEqual(list(self.folder.iterdir()), [self.path])
        before = self.path.read_bytes()
        with self.assertRaises(archive.ArchiveError) as retry:
            archive.create_archive(self.path, self.entries, 'support')
        self.assertEqual(retry.exception.code, 'ARCHIVE_EXISTS')
        self.assertEqual(self.path.read_bytes(), before)

    def test_lost_link_acknowledgment_never_deletes_a_complete_published_package(self):
        original = archive.os.link
        def link_then_lose_ack(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError('fixture lost publication acknowledgment')
        with patch.object(archive.os, 'link', side_effect=link_then_lose_ack):
            with self.assertRaises(archive.ArchiveError) as error:
                archive.create_archive(self.path, self.entries, 'support')
        self.assertEqual(error.exception.code, 'ARCHIVE_PUBLICATION_UNCERTAIN')
        self.assertEqual(archive.read_archive(self.path)['entries'], self.entries)
        self.assertEqual(list(self.folder.iterdir()), [self.path])

    def test_host_receipt_and_import_do_not_authenticate_sender_or_qualify_power_loss(self):
        receipt = archive.create_archive(self.path, self.entries, 'support', {'authenticates_sender': True})
        imported = archive.read_archive(self.path)
        self.assertFalse(receipt['authenticates_sender'])
        self.assertFalse(imported['authenticates_sender'])
        self.assertTrue(imported['integrity_verified'])
        self.assertTrue(receipt['publication_acknowledged'])
        self.assertIn('target_power_loss_not_qualified', receipt['durability_scope'])

    def test_no_parent_directory_is_implicitly_created(self):
        with self.assertRaises(archive.ArchiveError):
            archive.create_archive(self.folder / 'missing' / 'archive.zst', self.entries, 'support')
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_invalid_names_and_collisions_rejected_at_create(self):
        names = ('../outside', '/rooted', 'a/../b', 'a//b', './x', 'a\\b', 'C:/file',
                 'x:y', 'CON', 'nul.txt', 'COM1.txt', 'trail.', 'a\x00b', 'a\nb', 'manifest.json',
                 'MANIFEST.JSON', '\u03b1.json', 'a' * 101)
        for name in names:
            with self.subTest(name=name), self.assertRaises(archive.ArchiveError):
                archive.create_archive(self.path, {name: b'x'}, 'support')
        for entries in ({'x': b'x', 'X': b'x'}, {'x': b'x', 'x/y': b'y'}):
            with self.assertRaises(archive.ArchiveError):
                archive.create_archive(self.path, entries, 'support')
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_archive_types_schema_and_expected_kind_are_strict(self):
        self.forged()
        with self.assertRaises(archive.ArchiveError) as error:
            archive.read_archive(self.path, expected_kind='job')
        self.assertEqual(error.exception.code, 'ARCHIVE_KIND')
        for key, value in (('schema_version', 2), ('schema_version', True), ('format', 'foreign'),
                            ('kind', 'firmware'), ('unknown', 1)):
            with self.subTest(key=key, value=value):
                manifest = manifest_for(self.entries)
                manifest[key] = value
                self.reject(manifest=manifest)

    def test_rejects_traversal_absolute_windows_names_and_parent_conflicts_on_read(self):
        for name in ('../evil', '/evil', 'C:/evil', 'a\\evil', 'nul.txt', 'trailing.', 'a//b'):
            with self.subTest(name=name):
                self.reject(entries={name: b'x'}, codes={'ARCHIVE_PATH'})
        self.reject(entries={'a': b'x', 'a/b': b'y'}, codes={'ARCHIVE_PATH'})

    def test_rejects_tar_links_devices_directories_and_extensions(self):
        for type_ in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE, tarfile.CHRTYPE,
                      tarfile.BLKTYPE, tarfile.FIFOTYPE, tarfile.XHDTYPE, tarfile.GNUTYPE_SPARSE):
            with self.subTest(type=type_):
                self.reject(extra=[('unsafe', b'', type_, '../outside')], codes={'ARCHIVE_TAR'})

    def test_duplicate_case_colliding_and_unlisted_tar_members_rejected(self):
        for name in ('report.json', 'REPORT.JSON', 'manifest.json', 'surprise.bin'):
            with self.subTest(name=name):
                self.reject(extra=[(name, b'x', tarfile.REGTYPE, '')])

    def test_missing_changed_hash_or_size_and_manifest_duplicates_rejected(self):
        base = manifest_for(self.entries)
        for field, value in (('sha256', '0' * 64), ('sha256', 'invalid'), ('size', 1), ('size', True)):
            manifest = deepcopy(base)
            manifest['entries'][0][field] = value
            self.reject(manifest=manifest)
        self.reject(entries={'logs/one.txt': self.entries['logs/one.txt']}, manifest=base)
        manifest = deepcopy(base)
        manifest['entries'].append(deepcopy(manifest['entries'][0]))
        self.reject(manifest=manifest, codes={'ARCHIVE_DUPLICATE'})
        manifest = deepcopy(base)
        manifest['payload_bytes'] += 1
        self.reject(manifest=manifest, codes={'ARCHIVE_INTEGRITY'})

    def test_malformed_duplicate_nonfinite_or_deep_manifest_rejected(self):
        for payload in (b'not-json', b'[]', b'{"schema_version":1,"schema_version":1}',
                        b'{"x":NaN}', b'\xff'):
            self.reject(manifest=payload)
        for value in (float('nan'), float('inf'), {'x': float('inf')}):
            manifest = manifest_for(self.entries)
            manifest['metadata'] = {'bad': value}
            self.reject(manifest=manifest)
        nested = {}
        for _ in range(10):
            nested = {'x': nested}
        self.reject(manifest={**manifest_for(self.entries), 'metadata': nested})

    def test_entry_total_count_and_metadata_limits_before_publication(self):
        for entries in ({}, {'x': bytearray(b'x')}, {str(i): b'x' for i in range(archive.MAX_ENTRIES + 1)},
                         {'large': bytes(archive.MAX_FILE_BYTES + 1)}):
            with self.assertRaises(archive.ArchiveError):
                archive.create_archive(self.path, entries, 'support')
        with patch.object(archive, 'MAX_PAYLOAD_BYTES', 10), self.assertRaises(archive.ArchiveError):
            archive.create_archive(self.path, {'a': b'123456', 'b': b'123456'}, 'support')
        for metadata in ([], {1: 'key'}, {'bad': float('nan')}, {'huge': 'x' * archive.MAX_METADATA_BYTES}):
            with self.assertRaises(archive.ArchiveError):
                archive.create_archive(self.path, self.entries, 'support', metadata)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_declared_huge_member_rejected_before_data_read(self):
        member = tarfile.TarInfo('oversize.bin')
        member.size = archive.MAX_FILE_BYTES + 1
        raw = member.tobuf(format=tarfile.USTAR_FORMAT) + bytes(1024)
        self.reject(raw=raw, codes={'ARCHIVE_SIZE'})

    def test_manifest_and_total_limits_on_read(self):
        self.reject(manifest=b' ' * (archive.MAX_MANIFEST_BYTES + 1), codes={'ARCHIVE_SIZE'})
        self.forged()
        with patch.object(archive, 'MAX_PAYLOAD_BYTES', 10), self.assertRaises(archive.ArchiveError):
            archive.read_archive(self.path)

    def test_member_count_and_compressed_file_size_are_bounded_on_read(self):
        self.reject(entries={str(i): b'x' for i in range(archive.MAX_ENTRIES + 1)}, codes={'ARCHIVE_TAR'})
        with self.path.open('wb') as handle:
            handle.truncate(archive.MAX_COMPRESSED_BYTES + 1)
        with self.assertRaises(archive.ArchiveError) as error:
            archive.read_archive(self.path)
        self.assertEqual(error.exception.code, 'ARCHIVE_SIZE')

    def test_large_frame_uses_bounded_window_and_roundtrips(self):
        raw = b'host-fixture-only' * 600000
        self.assertGreater(len(raw), archive.MAX_WINDOW_BYTES)
        frame = archive.compress_bytes(raw)
        self.assertFalse(frame[4] & 0x20)  # Not a single-segment full-input window.
        self.assertEqual(archive.decompress_bytes(frame, len(raw)), raw)

    def test_tar_truncation_header_corruption_missing_end_and_hidden_trailer(self):
        raw = tar_bytes([('manifest.json', json.dumps(manifest_for(self.entries)).encode(), tarfile.REGTYPE, ''),
                         *[(name, data, tarfile.REGTYPE, '') for name, data in self.entries.items()]])
        for invalid in (raw[:-1], raw[:512], bytes([raw[0] ^ 1]) + raw[1:], raw + b'x' * 512,
                        raw + tar_bytes([('hidden', b'x', tarfile.REGTYPE, '')])):
            self.reject(raw=invalid, codes={'ARCHIVE_TAR'})
        self.reject(raw=bytes(10240), codes={'ARCHIVE_MANIFEST'})

    def test_nonzero_member_padding_is_rejected(self):
        raw = bytearray(tar_bytes([('tiny', b'x', tarfile.REGTYPE, '')]))
        raw[513] = 1
        self.reject(raw=bytes(raw), codes={'ARCHIVE_TAR'})

    def test_archive_input_is_not_a_directory_or_fifo(self):
        with self.assertRaises(archive.ArchiveError):
            archive.read_archive(self.folder)
        if hasattr(os, 'mkfifo'):
            os.mkfifo(self.path)
            with self.assertRaises(archive.ArchiveError):
                archive.read_archive(self.path)

    def test_symlink_archive_and_existing_symlink_destination_rejected(self):
        original = self.folder / 'original'
        original.write_bytes(b'preserve')
        try:
            self.path.symlink_to(original)
        except OSError:
            self.skipTest('Host does not grant symlink creation')
        with self.assertRaises(archive.ArchiveError):
            archive.read_archive(self.path)
        with self.assertRaises(archive.ArchiveError) as error:
            archive.create_archive(self.path, self.entries, 'support')
        self.assertEqual(error.exception.code, 'ARCHIVE_EXISTS')
        self.assertEqual(original.read_bytes(), b'preserve')

    def test_raw_codec_empty_and_binary_roundtrip_with_checksum(self):
        for raw in (b'', bytes(range(256)) * 100, b'fixture\n' * 10000, os.urandom(16384)):
            frame = archive.compress_bytes(raw)
            self.assertTrue(frame[4] & 4)
            self.assertEqual(archive.decompress_bytes(frame, len(raw)), raw)

    def test_raw_codec_rejects_trailing_concatenated_skippable_truncated_and_bad_checksum(self):
        valid = archive.compress_bytes(b'payload' * 1000)
        corrupted = valid[:-1] + bytes([valid[-1] ^ 1])
        for frame in (valid + b'x', valid + valid, b'\x50\x2a\x4d\x18\0\0\0\0' + valid,
                      valid[:-1], valid[:6], corrupted):
            with self.subTest(frame=frame[:12]), self.assertRaises(archive.ArchiveError):
                archive.decompress_bytes(frame, 10000)

    def test_unchecksummed_dictionary_flags_reserved_flags_and_huge_window_rejected(self):
        zstd = archive._zstd
        unchecksummed = zstd.compress(b'fixture')
        with self.assertRaises(archive.ArchiveError):
            archive.decompress_bytes(unchecksummed, 100)
        valid = bytearray(archive.compress_bytes(b'fixture'))
        for flag in (1, 2, 8, 16):
            changed = valid.copy()
            changed[4] |= flag
            with self.assertRaises(archive.ArchiveError):
                archive.decompress_bytes(bytes(changed), 100)
        # Unknown-size standard frame header with a 64 MiB window descriptor.
        with self.assertRaises(archive.ArchiveError) as error:
            archive.decompress_bytes(b'\x28\xb5\x2f\xfd\x04\x80\x01\x00\x00' + bytes(4), 100)
        self.assertEqual(error.exception.code, 'ARCHIVE_WINDOW')

    def test_unknown_size_bomb_stops_at_output_limit(self):
        zstd = archive._zstd
        compressor = zstd.ZstdCompressor(options={zstd.CompressionParameter.checksum_flag: 1,
                                                 zstd.CompressionParameter.window_log: 20})
        frame = compressor.compress(b'A' * 2_000_000) + compressor.flush()
        self.assertIsNone(zstd.get_frame_info(frame).decompressed_size)
        with self.assertRaises(archive.ArchiveError) as error:
            archive.decompress_bytes(frame, 1024)
        self.assertEqual(error.exception.code, 'ARCHIVE_SIZE')

    def test_invalid_codec_limits_and_levels_rejected(self):
        frame = archive.compress_bytes(b'payload')
        for bound in (-1, True, 1.5, archive.MAX_RAW_BYTES + 1, 3):
            with self.assertRaises(archive.ArchiveError):
                archive.decompress_bytes(frame, bound)
        for level in (0, 10, True, 3.0):
            with self.assertRaises(archive.ArchiveError):
                archive.compress_bytes(b'payload', level)
        with self.assertRaises(archive.ArchiveError):
            archive.compress_bytes('not bytes')


if __name__ == '__main__':
    unittest.main()
