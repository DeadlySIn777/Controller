import copy
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_terminals import validate


class TerminalContractTests(unittest.TestCase):
    def setUp(self):
        self.model=json.loads((ROOT/'hardware/motherboard_terminals/design.json').read_text())
        self.tree=ET.parse(ROOT/'hardware/motherboard_terminals/netlist.xml')

    def move(self, ref, pin, destination):
        root=self.tree.getroot()
        old=next(n for n in root.findall('.//nets/net') if any(p.attrib['ref']==ref and p.attrib['pin']==pin for p in n.findall('node')))
        node=next(p for p in old.findall('node') if p.attrib['ref']==ref and p.attrib['pin']==pin)
        old.remove(node)
        new=next(n for n in root.findall('.//nets/net') if n.attrib['name']==destination)
        new.append(node)

    def test_native_source_and_manufacturer_lands(self):
        self.assertEqual(validate(self.tree,self.model),[])

    def test_consistent_motor_enable_swap_is_rejected(self):
        row=next(r for r in self.model['terminal_ledger'] if r['source_id']=='XM0.8')
        self.move(row['reference'],row['pin'],'/EN0_NC')
        self.model['components'][row['reference']]['pins'][row['pin']]='EN0_NC'
        row['source_net']='EN0_NC'
        self.assertTrue(any('frozen function XM0.8' in e for e in validate(self.tree,self.model,False)))

    def test_motor_gap_cannot_be_reused(self):
        row=next(r for r in self.model['terminal_ledger'] if r['source_id']=='XM0.7')
        self.move(row['reference'],row['pin'],'/FIELD_GND')
        self.model['components'][row['reference']]['pins'][row['pin']]='FIELD_GND'
        self.assertTrue(any('motor isolation NC' in e for e in validate(self.tree,self.model,False)))

    def test_wrong_common_on_second_analog_output_is_rejected(self):
        row=next(r for r in self.model['terminal_ledger'] if r['source_id']=='XAO.5')
        self.move(row['reference'],row['pin'],'/AO0_COM')
        self.model['components'][row['reference']]['pins'][row['pin']]='AO0_COM'
        row['source_net']='AO0_COM'
        self.assertTrue(any('frozen function XAO.5' in e for e in validate(self.tree,self.model,False)))

    def test_power_entry_is_not_duplicated(self):
        row=next(r for r in self.model['terminal_ledger'] if r['source_id']=='XP2.1')
        row['reference']='J19501';row['pin']='1';row['reused_existing_power_entry']=False
        self.assertTrue(any('power header must be reused XP2.1' in e for e in validate(self.tree,self.model,False)))

    def test_motor_mating_plug_must_match_header(self):
        self.model['components']['J19501']['mating_plug_mpn']='1840463'
        self.assertTrue(any('mating pair mismatch J19501' in e for e in validate(self.tree,self.model)))

    def test_couplings_do_not_replace_isolated_common_with_chassis(self):
        self.model['components']['C19505']['pins']['1']='CHASSIS'
        self.assertTrue(any('AC-only chassis couplings' in e for e in validate(self.tree,self.model,False)))


if __name__=='__main__':unittest.main()
