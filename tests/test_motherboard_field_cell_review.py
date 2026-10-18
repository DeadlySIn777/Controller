"""Source admission negatives for the separate 30V field-filter recipe."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import hardware_review_field_input_cells as reviewed
SOURCE=ROOT/'hardware/motherboard'
ADOPTION=ROOT/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json'

class FieldCellSourceAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=reviewed.native(json.loads((SOURCE/'design.json').read_text()),SOURCE/'netlist.xml')

    def test_actual_source_retains_exact_30v_local_filters_and_no_external_wiring(self):
        result=reviewed.review(SOURCE,ADOPTION)
        self.assertEqual(48,len(result['nets']))
        self.assertTrue(all(r['maximum_voltage_v']==30 and r['normal_current_max_a']==.00275 and not r['allow_vias'] for r in result['nets'].values()))
        self.assertFalse(any(name.endswith('_FIELD') or '_SUB_ISLAND' in name for name in result['nets']))

    def test_filter_ground_cannot_be_borrowed_from_linux_domain(self):
        nodes,nets,functions=copy.deepcopy(self.native);nodes['C8001','2']='/LOGIC_GND'
        with patch.object(reviewed,'native',return_value=(nodes,nets,functions)):
            with self.assertRaisesRegex(ValueError,'FIELD_B return'):reviewed.review(SOURCE,ADOPTION)

    def test_an_added_physical_branch_cannot_be_omitted_from_routing_scope(self):
        nodes,nets,functions=copy.deepcopy(self.native);name=nodes['U8001','16'];nets[name].append(('R8201','1'));nets[name].sort()
        with patch.object(reviewed,'native',return_value=(nodes,nets,functions)):
            with self.assertRaisesRegex(ValueError,'full physical field RC endpoint'):reviewed.review(SOURCE,ADOPTION)

    def test_voltage_profile_cannot_expand_selected_electrical_limits(self):
        original=reviewed.load
        def altered(path):
            result=original(path)
            if Path(path)==ROOT/'hardware/motherboard_di/design.json':
                result=copy.deepcopy(result);result['interface']['operating_max_v']=48
            return result
        with patch.object(reviewed,'load',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'input limits changed'):reviewed.review(SOURCE,ADOPTION)

if __name__=='__main__':unittest.main()
