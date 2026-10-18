"""Reject unsafe or misleading fabrication-contract changes."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hardware_apply_motherboard_stackup import spec,validate

class StackupContractTests(unittest.TestCase):
    def rejects(self,change):
        s=copy.deepcopy(spec());change(s)
        with self.assertRaises(ValueError):validate(s)
    def test_reviewed_thickness_reconciles(self):self.assertTrue(validate(spec()))
    def test_asymmetric_pressed_dielectric_rejected(self):self.rejects(lambda s:s['dielectric_thickness_mm'].__setitem__(0,.35))
    def test_weaker_finished_power_copper_rejected(self):self.rejects(lambda s:s['copper_layers'][0].__setitem__('thickness_mm',.035))
    def test_thickness_sums_not_hidden(self):self.rejects(lambda s:s.__setitem__('nominal_board_thickness_mm',1.2))
    def test_distant_reference_layer_rejected(self):self.rejects(lambda s:s['reference_layers'].__setitem__('F.Cu','In4.Cu'))
    def test_request_cannot_claim_factory_approval(self):self.rejects(lambda s:s.__setitem__('factory_stackup_approval',True))
    def test_request_cannot_claim_measured_impedance(self):self.rejects(lambda s:s.__setitem__('physical_impedance_verified',True))
    def test_wrong_usb_impedance_rejected(self):self.rejects(lambda s:s['controlled_impedance'][0].__setitem__('target_ohm',120))
    def test_control_via_exception_cannot_become_global(self):self.rejects(lambda s:s['exact_low_current_control_via_exceptions'].append(copy.deepcopy(s['exact_low_current_control_via_exceptions'][0])))
    def test_control_via_exception_cannot_move_to_unreviewed_escape(self):self.rejects(lambda s:s['exact_low_current_control_via_exceptions'][0]['position_mm'].__setitem__(0,0.))
    def test_advanced_annulus_cannot_claim_factory_approval(self):self.rejects(lambda s:s['exact_low_current_control_via_exceptions'][0].__setitem__('factory_DFM_and_quote_approved',True))

if __name__=='__main__':unittest.main()
