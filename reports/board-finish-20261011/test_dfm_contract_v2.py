"""Host rejection tests for the hardened DFM source guard; no native jobs."""
import unittest

from dfm_contract_v2 import validate


def fp(ref, uid, position, pads, silk="0.1", nested=False):
    extra = '(metadata (layer "F.SilkS"))' if nested else ""
    layer = "F.Cu" if nested else "F.SilkS"
    pad_text = "".join(f'\t\t(pad "{number}" smd rect (at {x} {y}) (size 1 1) '
                       f'(layers "F.Cu" "F.Paste" "F.Mask") (net {net} "N") (uuid "{uid}-pad-{number}"))\n'
                       for number, x, y, net in pads)
    return (f'\t(footprint "R"\n\t\t(at {position})\n\t\t(uuid "{uid}")\n'
            f'\t\t(property "Reference" "{ref}" (layer "F.Fab"))\n'
            f'\t\t(fp_line (start 0 0) (end 1 0) (stroke (width {silk}) (type default)) '
            f'(layer "{layer}") {extra} (uuid "{uid}-line"))\n{pad_text}\t)\n')


def tie(uid, start, end, net, layer="F.Cu", width="0.448", extra=""):
    return (f'\t(segment\n\t\t(start {start[0]} {start[1]})\n\t\t(end {end[0]} {end[1]})\n'
            f'\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net {net})\n'
            f'\t\t(uuid "{uid}")\n{extra}\t)\n')


def fixture(moved=False, segments=None, silk="0.1", nested=False):
    capacitor = fp("C14814", "cap", "0.7 1" if moved else "1 1",
                   [("1", -0.5, 0, 1), ("2", 0.5, 0, 2)], silk, nested)
    target = fp("U1", "target", "1.6 1", [("1", 0, 0, 1), ("2", 0, 0.5, 2)])
    if segments is None:
        segments = [tie("tie1", (0.2, 1), (1.6, 1), 1),
                    tie("tie2", (1.2, 1), (1.6, 1.5), 2)] if moved else []
    return ('(kicad_pcb\n\t(version 20260101)\n' + capacitor + target + "".join(segments) + ')\n').encode()


class ContractV2(unittest.TestCase):
    def test_silk_only_accepted(self):
        validate(fixture(), fixture(silk="0.15"))

    def test_owned_complete_ties_accepted(self):
        result = validate(fixture(), fixture(True))
        self.assertEqual(len(result["capacitor_ties"]), 2)

    def test_arbitrary_new_route_rejected(self):
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(segments=[tie("unrelated", (100, 100), (101, 101), 1)]))

    def test_missing_tie_rejected(self):
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments=[tie("tie1", (0.2, 1), (1.6, 1), 1)]))

    def test_duplicate_pad_tie_rejected(self):
        segments = [tie("tie1", (0.2, 1), (1.6, 1), 1), tie("tie2", (1.2, 1), (1.6, 1.5), 2),
                    tie("tie3", (0.2, 1), (1.6, 1), 1)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_non_pad_target_rejected(self):
        segments = [tie("tie1", (0.2, 1), (1.7, 1), 1), tie("tie2", (1.2, 1), (1.6, 1.5), 2)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_wrong_net_rejected(self):
        segments = [tie("tie1", (0.2, 1), (1.6, 1), 2), tie("tie2", (1.2, 1), (1.6, 1.5), 2)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_layer_change_rejected(self):
        segments = [tie("tie1", (0.2, 1), (1.6, 1), 1, layer="In3.Cu"), tie("tie2", (1.2, 1), (1.6, 1.5), 2)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_width_change_rejected(self):
        for width in ("0.3", "2.0", "NaN"):
            with self.subTest(width=width), self.assertRaises(ValueError):
                validate(fixture(), fixture(True, [tie("tie1", (0.2, 1), (1.6, 1), 1, width=width),
                                                   tie("tie2", (1.2, 1), (1.6, 1.5), 2)]))

    def test_extra_segment_fields_rejected(self):
        segments = [tie("tie1", (0.2, 1), (1.6, 1), 1, extra='\t\t(metadata "unreviewed")\n'),
                    tie("tie2", (1.2, 1), (1.6, 1.5), 2)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_old_pad_is_not_new_pad_owner(self):
        segments = [tie("tie1", (0.5, 1), (1.6, 1), 1), tie("tie2", (1.2, 1), (1.6, 1.5), 2)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_moved_old_pad_is_not_retained_target(self):
        segments = [tie("tie1", (0.2, 1), (0.5, 1), 1), tie("tie2", (1.2, 1), (1.6, 1.5), 2)]
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True, segments))

    def test_wrong_capacitor_delta_rejected(self):
        with self.assertRaises(ValueError):
            validate(fixture(), fixture(True).replace(b'(at 0.7 1)', b'(at 0.8 1)'))

    def test_nested_layer_cannot_exempt_copper_graphic(self):
        with self.assertRaises(ValueError):
            validate(fixture(nested=True), fixture(silk="0.9", nested=True))

    def test_duplicate_direct_layer_rejected(self):
        first = fixture().replace(b'(layer "F.SilkS")  (uuid "cap-line")',
                                  b'(layer "F.Cu") (layer "F.SilkS") (uuid "cap-line")')
        with self.assertRaises(ValueError):
            validate(first, first.replace(b'(stroke (width 0.1)', b'(stroke (width 0.9)', 1))

    def test_pad_net_change_rejected(self):
        with self.assertRaises(ValueError):
            validate(fixture(), fixture().replace(b'(net 1 "N")', b'(net 3 "N")', 1))


if __name__ == "__main__":
    unittest.main()
