"""Fault-injection review of the actual six-joint KiCad netlist."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_tx_six import validate

ROOT = Path(__file__).resolve().parents[1]


class SixJointTransmitterTests(unittest.TestCase):
    def setUp(self):
        self.tree = ET.parse(ROOT / "hardware/tx_six/netlist.xml")
        self.design = json.loads((ROOT / "hardware/electrical-design.json").read_text(encoding="utf-8"))

    def net(self,name):
        return self.tree.find(f".//nets/net[@name='/{name}']")

    def new_errors(self,tree=None,design=None):
        """Errors introduced by a mutation, excluding anything the untouched baseline already reports."""
        baseline = set(validate(ET.parse(ROOT / "hardware/tx_six/netlist.xml"),self.design))
        errors = [e for e in validate(tree or self.tree,design or self.design) if e not in baseline]
        self.assertTrue(errors,"mutation produced no new validator error")
        return errors

    def assertReported(self,errors,*fragments):
        self.assertTrue(any(all(f in e for f in fragments) for e in errors),f"no error matching {fragments} in {errors}")

    def test_exported_six_joint_block_matches_actual_ledger(self):
        self.assertEqual([],validate(self.tree,self.design))

    def test_output_polarity_swap_is_detected(self):
        positive = self.net("STEP5_P").find("node[@ref='JTX2']")
        negative = self.net("STEP5_N").find("node[@ref='JTX2']")
        p_pin,n_pin = positive.attrib["pin"],negative.attrib["pin"]
        positive.attrib["pin"],negative.attrib["pin"] = n_pin,p_pin
        errors = self.new_errors()
        self.assertReported(errors,"Net STEP5_P:",f"missing=[('JTX2', '{p_pin}')]",f"unexpected=[('JTX2', '{n_pin}')]")
        self.assertReported(errors,"Net STEP5_N:",f"missing=[('JTX2', '{n_pin}')]",f"unexpected=[('JTX2', '{p_pin}')]")

    def test_final_bank_enable_bypass_is_detected(self):
        node = self.net("TX_PERMIT").find("node[@ref='U3']")
        self.net("TX_PERMIT").remove(node)
        self.net("SIGNAL_5V").append(node)
        errors = self.new_errors()
        self.assertReported(errors,"Net TX_PERMIT:","missing=[('U3', '4')]")
        self.assertReported(errors,"Net SIGNAL_5V:","unexpected=[('U3', '4')]")

    def test_each_bank_data_default_and_bypass_cannot_disappear(self):
        for ref in ("R13","R17","R21","C1","C3","C5","R25","R26","R27"):
            with self.subTest(ref=ref):
                changed = copy.deepcopy(self.tree)
                for net in changed.findall(".//nets/net"):
                    for node in list(net.findall("node")):
                        if node.attrib["ref"] == ref:
                            net.remove(node)
                errors = self.new_errors(tree=changed)
                self.assertReported(errors,"missing=",f"('{ref}', ")
                self.assertEqual(2,sum(1 for e in errors if e.startswith("Net ") and f"('{ref}', " in e),errors)

    def test_driver_package_or_default_value_change_is_detected(self):
        for path,newvalue,expected in ((".//components/comp[@ref='U2']/footprint","WrongPackage",
                                        "Driver package/MPN differs from reviewed PW16 contract: U2"),
                                       (".//components/comp[@ref='R27']/value","10M 1%",
                                        "Value/default provision changed: R27")):
            with self.subTest(path=path):
                changed = copy.deepcopy(self.tree)
                changed.find(path).text = newvalue
                self.assertEqual([expected],self.new_errors(tree=changed))

    def test_duplicated_pin_or_added_short_is_detected(self):
        duplicate = copy.deepcopy(self.net("STEP0_FPGA").find("node"))
        self.net("SIGNAL_5V").append(duplicate)
        errors = self.new_errors()
        self.assertReported(errors,f"Pin appears twice: ('{duplicate.attrib['ref']}', '{duplicate.attrib['pin']}')")
        self.assertReported(errors,"Net SIGNAL_5V:",f"unexpected=[('{duplicate.attrib['ref']}', '{duplicate.attrib['pin']}')]")

    def test_reference_return_cannot_be_omitted(self):
        reference = self.net("LOGIC_GND").find("node[@ref='JREF1'][@pin='3']")
        self.net("LOGIC_GND").remove(reference)
        self.assertReported(self.new_errors(),"Net LOGIC_GND:","missing=[('JREF1', '3')]")

    def test_expanded_or_changed_ledger_does_not_inherit_baseline_evidence(self):
        changed = copy.deepcopy(self.design)
        channel = next(c for c in changed["channels"] if c["id"] == "STEP5")
        channel["component"] = "TX3"
        self.assertReported(self.new_errors(design=changed),"Ledger bank/channel/logic mismatch: STEP5")
        changed = copy.deepcopy(self.design)
        changed["channels"].append({**channel,"id":"STEP6"})
        self.assertEqual(["Ledger does not match the distinct baseline six-joint scope"],self.new_errors(design=changed))


if __name__ == "__main__":
    unittest.main()
