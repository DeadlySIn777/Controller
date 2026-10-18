"""Independent dimensions and hostile geometry cases; no machine interfaces."""
from pathlib import Path
import unittest

from tools.hardware_build_assembly import parse, children, child, value, dump
from tools.hardware_mc_footprint_envelopes import add_courtyard, geometry

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'TPS62901_RPJ9': 'hardware/mc_local_power/CNC_MC_Power.pretty/TPS62901_RPJ9.kicad_mod',
    'XGL4020': 'hardware/mc_local_power/CNC_MC_Power.pretty/XGL4020.kicad_mod',
    'LTC2962_UD16': 'hardware/mc_local_power/CNC_MC_Power.pretty/LTC2962_UD16.kicad_mod',
    'TPS3851_DRB8': 'hardware/is1_watchdogs/startup_conditioning_r0_2/CNC_IS1.pretty/TPS3851_DRB8.kicad_mod',
}


class MCFootprintEnvelopesTests(unittest.TestCase):
    def source(self, name):
        return (ROOT/FILES[name]).read_text(encoding='utf-8')

    def test_primary_maximum_body_and_copper_include_quarter_mm_each_side(self):
        # Independent fixture read from TI RPJ0009A / DRB0008A, ADI UD16,
        # Coilcraft 1529-3; TPS RPJ bottom/top copper is asymmetric.
        expected = {'TPS62901_RPJ9': [-1.2, -1.45, 1.2, 1.3],
                    'XGL4020': [-2.4, -2.4, 2.4, 2.4],
                    'LTC2962_UD16': [-2.0, -2.0, 2.0, 2.0],
                    'TPS3851_DRB8': [-1.95, -1.8, 1.95, 1.8]}
        for name, bounds in expected.items():
            with self.subTest(name=name):
                self.assertEqual(bounds, geometry(self.source(name))['courtyard_bounds_mm'])

    def test_no_existing_pad_or_nominal_body_is_changed(self):
        for name in FILES:
            with self.subTest(name=name):
                old = parse(self.source(name)); new = parse(add_courtyard(self.source(name)))
                self.assertEqual(children(old, 'pad'), children(new, 'pad'))
                self.assertEqual(children(old, 'fp_rect'), children(new, 'fp_rect')[:-1])
                self.assertEqual(old, new[:-1])

    def test_idempotence_does_not_duplicate_courtyard(self):
        for name in FILES:
            once = add_courtyard(self.source(name))
            self.assertEqual(once, add_courtyard(once))

    def test_wrong_existing_courtyard_is_rejected(self):
        changed = add_courtyard(self.source('XGL4020')).replace('(start -2.4 -2.4)', '(start -2.3 -2.3)')
        with self.assertRaisesRegex(ValueError, 'differs'):
            add_courtyard(changed)

    def test_rotated_pad_is_rejected_instead_of_underbounded(self):
        tree = parse(self.source('TPS62901_RPJ9'))
        child(children(tree, 'pad')[0], 'at').append('45')
        with self.assertRaisesRegex(ValueError, 'rotation'):
            add_courtyard(dump(tree))

    def test_larger_pad_is_not_hidden_by_body_envelope(self):
        tree = parse(self.source('LTC2962_UD16'))
        child(children(tree, 'pad')[0], 'size')[1] = '3.0'
        self.assertEqual(-3.15, geometry(dump(tree))['courtyard_bounds_mm'][0])

    def test_nonfinite_or_nonpositive_pad_size_is_rejected(self):
        for number in ('nan', '0', '-1'):
            tree = parse(self.source('XGL4020'))
            child(children(tree, 'pad')[0], 'size')[1] = number
            with self.assertRaises(ValueError):
                add_courtyard(dump(tree))

    def test_unknown_footprint_remains_byte_equal(self):
        text = self.source('TPS62901_RPJ9').replace('TPS62901_RPJ9', 'OTHER_PACKAGE')
        self.assertEqual(text, add_courtyard(text))


if __name__ == '__main__':
    unittest.main()
