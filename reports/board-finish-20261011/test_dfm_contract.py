import unittest
from reconcile_dfm import validate, children


def board(ref="C14814", pose="1 1", net="1", silk="0.1", copper="", uid="pad-one"):
    return (f'(kicad_pcb\n\t(version 20260101)\n\t(footprint "R"\n'
            f'\t\t(at {pose})\n\t\t(uuid "fp-one")\n'
            f'\t\t(property "Reference" "{ref}" (layer "F.Fab"))\n'
            f'\t\t(fp_line (start 0 0) (end 1 0) (stroke (width {silk}) (type default)) '
            f'(layer "F.SilkS") (uuid "line-one"))\n'
            f'\t\t(pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu" "F.Paste" "F.Mask") '
            f'(net {net} "N") (uuid "{uid}"))\n\t)\n{copper})\n').encode()


class Contract(unittest.TestCase):
    def test_qualified_silk_and_bounded_owned_cap_movement(self):
        r = validate(board(), board(pose="1.3 1", silk="0.15"))
        self.assertEqual(len(r["moved_footprints"]), 1)
        self.assertTrue(r["all_pad_local_geometry_uuid_and_net_assignments_retained_exact"])

    def test_pad_net_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "protected"):
            validate(board(), board(net="2"))

    def test_pad_identity_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "protected"):
            validate(board(), board(uid="pad-two"))

    def test_unapproved_motion_rejected(self):
        with self.assertRaisesRegex(ValueError, "unapproved"):
            validate(board(ref="U1"), board(ref="U1", pose="1.3 1"))

    def test_rotation_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "unapproved"):
            validate(board(), board(pose="1 1 90"))

    def test_reference_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "reference changed"):
            validate(board(), board(ref="C2"))

    def test_original_copper_removal_rejected(self):
        old = board(copper='\t(segment\n\t\t(start 0 0)\n\t\t(end 1 0)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net 1)\n\t\t(uuid "seg-one")\n\t)\n')
        with self.assertRaisesRegex(ValueError, "old copper"):
            validate(old, board())

    def test_copper_layer_graphic_change_rejected(self):
        before = board().replace(b'"F.SilkS"', b'"F.Cu"')
        after = board(silk="0.15").replace(b'"F.SilkS"', b'"F.Cu"')
        with self.assertRaisesRegex(ValueError, "protected"):
            validate(before, after)

    def test_parser_handles_parentheses_and_escaped_quotes_in_text(self):
        prefix, nodes = children(b'(fp_text "A(\\\"B)" (layer "F.SilkS") (effects (font (size 1 1))))')
        self.assertEqual(len(nodes), 2)
        self.assertTrue(prefix.startswith(b'(fp_text "A'))


if __name__ == "__main__":
    unittest.main()
