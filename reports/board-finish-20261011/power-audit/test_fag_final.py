"""Cheap host rejection tests; no native input or output changes."""
import unittest
from finish_fag_proof import decode_filename, native_manifest


class ManifestTests(unittest.TestCase):
    def fixture(self):
        names = ("board.kicad_pcb", "board.kicad_pro", "board.kicad_dru", "sch.net", "fp-lib-table")
        return "\n".join("\\" + "a" * 64 + " *C:\\\\Users\\\\A B\\\\" + name for name in names).encode()

    def test_gnu_windows_escaped_filenames(self):
        parsed = native_manifest(self.fixture())
        self.assertEqual(parsed["board.kicad_pcb"]["path"], "C:/Users/A B/board.kicad_pcb")

    def test_plain_git_paths(self):
        data = self.fixture().decode().replace("\\" + "a" * 64, "a" * 64).replace("C:\\\\Users\\\\A B\\\\", "/z/project/")
        self.assertEqual(native_manifest(data.encode())["sch.net"]["path"], "/z/project/sch.net")

    def test_unknown_escape_rejected(self):
        with self.assertRaises(ValueError):
            decode_filename("C:\\Users")

    def test_duplicate_role_even_with_other_path_rejected(self):
        with self.assertRaises(ValueError):
            native_manifest(self.fixture() + ("\n" + "a" * 64 + " */other/board.kicad_pcb").encode())

    def test_embedded_newline_rejected(self):
        with self.assertRaises(ValueError):
            native_manifest(self.fixture().replace(b"A B", b"A\\nB"))

    def test_extra_unknown_role_rejected(self):
        with self.assertRaises(ValueError):
            native_manifest(self.fixture() + ("\n" + "a" * 64 + " */other/extra.txt").encode())

    def test_missing_hash_prefix_rejected(self):
        with self.assertRaises(ValueError):
            native_manifest(self.fixture()[1:].replace(b"a" * 64, b"a" * 63, 1))

    def test_decode_gnu_escape_round_trip(self):
        self.assertEqual(decode_filename("a\\\\b\\nc\\rd"), "a\\b\nc\rd")


if __name__ == "__main__":
    unittest.main()
