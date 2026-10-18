"""Fault-injection review of the new twelve-channel KiCad netlist."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_tx_twelve import validate

ROOT = Path(__file__).resolve().parents[1]


class TwelveChannelTransmitterTests(unittest.TestCase):
    def setUp(self):
        self.tree = ET.parse(ROOT / "hardware/tx_twelve/netlist.xml")
        self.design = json.loads((ROOT / "hardware/tx_twelve/allocation.json").read_text(encoding="utf-8"))

    def net(self,name):
        return self.tree.find(f".//nets/net[@name='/{name}']")

    def new_errors(self,tree=None,design=None):
        """Errors introduced by a mutation, excluding anything the untouched baseline already reports."""
        baseline = set(validate(ET.parse(ROOT / "hardware/tx_twelve/netlist.xml"),self.design))
        errors = [e for e in validate(tree or self.tree,design or self.design) if e not in baseline]
        self.assertTrue(errors,"mutation produced no new validator error")
        return errors

    def assertReported(self,errors,*fragments):
        self.assertTrue(any(all(f in e for f in fragments) for e in errors),f"no error matching {fragments} in {errors}")

    def test_exported_twelve_channel_block_matches_new_allocation(self):
        self.assertEqual([],validate(self.tree,self.design))

    def test_output_polarity_swap_is_detected(self):
        positive = self.net("STEP11_P").find("node[@ref='JTX5']")
        negative = self.net("STEP11_N").find("node[@ref='JTX5']")
        p_pin,n_pin = positive.attrib["pin"],negative.attrib["pin"]
        positive.attrib["pin"],negative.attrib["pin"] = n_pin,p_pin
        errors = self.new_errors()
        self.assertReported(errors,"Net STEP11_P:",f"missing=[('JTX5', '{p_pin}')]",f"unexpected=[('JTX5', '{n_pin}')]")
        self.assertReported(errors,"Net STEP11_N:",f"missing=[('JTX5', '{n_pin}')]",f"unexpected=[('JTX5', '{p_pin}')]")

    def test_final_bank_enable_bypass_is_detected(self):
        node = self.net("TX_PERMIT").find("node[@ref='U6']")
        self.net("TX_PERMIT").remove(node)
        self.net("CORE_5V").append(node)
        errors = self.new_errors()
        self.assertReported(errors,"Net TX_PERMIT:","missing=[('U6', '4')]")
        self.assertReported(errors,"Net CORE_5V:","unexpected=[('U6', '4')]")

    def test_each_bank_data_default_and_bypass_cannot_disappear(self):
        for ref in ("R25","R29","R33","R37","R41","R45","C1","C3","C5","C7","C9","C11","R49","R50","R51","R52","R53","R54"):
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
                                       (".//components/comp[@ref='R54']/value","10M 1%",
                                        "Value/default provision changed: R54")):
            with self.subTest(path=path):
                changed = copy.deepcopy(self.tree)
                changed.find(path).text = newvalue
                self.assertEqual([expected],self.new_errors(tree=changed))

    def test_duplicated_pin_or_added_short_is_detected(self):
        duplicate = copy.deepcopy(self.net("STEP0_FPGA").find("node"))
        self.net("CORE_5V").append(duplicate)
        errors = self.new_errors()
        self.assertReported(errors,f"Pin appears twice: ('{duplicate.attrib['ref']}', '{duplicate.attrib['pin']}')")
        self.assertReported(errors,"Net CORE_5V:",f"unexpected=[('{duplicate.attrib['ref']}', '{duplicate.attrib['pin']}')]")

    def test_reference_return_cannot_be_omitted(self):
        reference = self.net("LOGIC_GND").find("node[@ref='JREF1'][@pin='3']")
        self.net("LOGIC_GND").remove(reference)
        self.assertReported(self.new_errors(),"Net LOGIC_GND:","missing=[('JREF1', '3')]")

    def test_changed_allocation_is_rejected(self):
        changed = copy.deepcopy(self.design)
        channel = next(c for c in changed["channels"] if c["id"] == "STEP11")
        channel["component"] = "TX6"
        self.assertReported(self.new_errors(design=changed),"Allocation bank/channel/logic mismatch: STEP11")
        changed = copy.deepcopy(self.design)
        changed["channels"].append({**channel,"id":"STEP12"})
        self.assertEqual(["Allocation does not match the distinct twelve-channel candidate scope"],self.new_errors(design=changed))

    def test_twelve_channel_metadata_cannot_claim_eight_or_shipping(self):
        for key,value in (("motor_channels",8),("minimum_product_channels",6),("manufacturing_ready",True)):
            changed=copy.deepcopy(self.design);changed[key]=value
            self.assertIn("Candidate scope metadata differs",validate(self.tree,changed))

    def test_unpopulated_extension_cannot_pass_full_twelve_review(self):
        comps=self.tree.find(".//components")
        comps.remove(comps.find("comp[@ref='U6']"))
        self.new_errors()

    def test_each_physical_channel_has_own_signal_pair(self):
        for joint in range(12):
            for kind in ("STEP","DIR"):
                self.assertIsNotNone(self.net(f"{kind}{joint}_FPGA"))
                for pol in ("P","N"):
                    self.assertEqual(2,len(self.net(f"{kind}{joint}_{pol}").findall("node")))


if __name__ == "__main__":
    unittest.main()
