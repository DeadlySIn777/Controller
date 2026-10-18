import unittest

from compose_additions import compose


def board(copper=b"", net=b"G", fill=b"(xy 1 1) (xy 2 1) (xy 2 2)"):
    return (b'(kicad_pcb\n\t(version 20260101)\n\t(zone\n\t\t(net "' + net +
            b'")\n\t\t(uuid "z")\n\t\t(polygon\n\t\t\t(pts (xy 0 0) (xy 3 0) (xy 3 3))\n\t\t)\n' +
            b'\t\t(filled_polygon\n\t\t\t(layer "F.Cu")\n\t\t\t(pts ' + fill + b')\n\t\t)\n\t)\n' + copper + b')\n')


def seg(uuid, end=b"1 1"):
    return b'\t(segment\n\t\t(start 0 0)\n\t\t(end ' + end + b')\n\t\t(uuid "' + uuid + b'")\n\t)\n'


class CompositionTests(unittest.TestCase):
    def test_additive_merge_retains_actual_target_bytes(self):
        base = board(seg(b"old"))
        target = board(seg(b"old") + seg(b"target"), fill=b"(xy 1 1) (xy 3 1) (xy 3 2)")
        donor = board(seg(b"old") + seg(b"new"))
        output, added = compose(target, base, donor)
        self.assertEqual(output, target[:-2] + seg(b"new") + b')\n')
        self.assertEqual([a["uuid"] for a in added], ["new"])

    def test_changed_zone_net_rejected(self):
        with self.assertRaisesRegex(ValueError, "definitions"):
            compose(board(seg(b"old"), net=b"WRONG"), board(seg(b"old")), board(seg(b"old") + seg(b"new")))

    def test_changed_old_copper_rejected(self):
        with self.assertRaisesRegex(ValueError, "original copper"):
            compose(board(seg(b"old")), board(seg(b"old")), board(seg(b"old", end=b"2 2")))

    def test_removed_original_copper_rejected(self):
        with self.assertRaisesRegex(ValueError, "original copper"):
            compose(board(seg(b"old")), board(seg(b"old")), board())

    def test_uuid_collision_rejected(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            compose(board(seg(b"old") + seg(b"new")), board(seg(b"old")), board(seg(b"old") + seg(b"new")))


if __name__ == "__main__":
    unittest.main()
