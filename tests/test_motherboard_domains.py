"""Mutation tests for actual galvanic cuts and grounded-return identity."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import hardware_map_motherboard_domains as h


class Domains(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT/'reports/motherboard-integration-20260930/r20b-2663-electrical-corrections-staged'
        cls.parts = json.loads((source/'design.json').read_text(encoding='utf-8'))['components']
        cls.nodes, cls.nc, cls.functions = h.native(source/'netlist.xml')

    def test_actual_complete_partition(self):
        domains, barriers, floating, coupling = h.classify(self.parts, self.nodes, self.nc)
        self.assertEqual(len(barriers), 91)
        self.assertEqual(sum(r['kind']=='independent_substrate' for r in floating), 44)
        self.assertEqual(sum(r['kind']=='floating_contact' for r in floating), 15)
        self.assertEqual(len(coupling), 9)
        for domain, name in h.SEEDS.items(): self.assertEqual(domains[name], domain)
        self.assertNotEqual(domains[self.nodes['U10003','9']], domains[self.nodes['U10016','9']])

    def test_field_to_logic_ground_mutation_rejected(self):
        nodes = dict(self.nodes); nodes['U10003','9'] = h.SEEDS['LOGIC']
        with self.assertRaisesRegex(ValueError, 'Distinct seeded'): h.classify(self.parts,nodes,self.nc)

    def test_a_b_bridge_mutation_rejected(self):
        parts = copy.deepcopy(self.parts); parts['Rbad'] = dict(mpn='RC0603',pins={'1':'A','2':'B'})
        nodes = dict(self.nodes); nodes['Rbad','1']=h.SEEDS['FIELD_A']; nodes['Rbad','2']=h.SEEDS['FIELD_B']
        with self.assertRaisesRegex(ValueError, 'Distinct seeded'): h.classify(parts,nodes,self.nc)

    def test_analog_secondary_to_logic_mutation_rejected(self):
        nodes = dict(self.nodes); nodes['U14701','7'] = h.SEEDS['LOGIC']
        with self.assertRaisesRegex(ValueError, 'Distinct seeded'): h.classify(self.parts,nodes,self.nc)

    def test_chassis_coupling_never_dc_union(self):
        domains,_,_,coupling=h.classify(self.parts,self.nodes,self.nc)
        self.assertEqual(domains['/CHASSIS'],'CHASSIS')
        self.assertEqual(domains['/LOGIC_GND'],'LOGIC')
        self.assertTrue(all('no copper' in c['role'] for c in coupling))

    def test_chassis_capacitor_changed_endpoint_rejected(self):
        nodes=dict(self.nodes); nodes['C19501','2']=h.SEEDS['LOGIC']
        with self.assertRaisesRegex(ValueError,'Changed explicit chassis'):h.classify(self.parts,nodes,self.nc)

    def test_raw_filtered_return_not_aliased(self):
        domains,_,_,_=h.classify(self.parts,self.nodes,self.nc)
        for net,(domain,ref) in h.RAW_RETURNS.items():
            self.assertEqual(domains[net],domain)
            self.assertNotEqual(net,h.SEEDS[domain])
            self.assertEqual({self.nodes[ref,p] for p in ['1','2']},{net,h.SEEDS[domain]})

    def test_filtered_return_bypass_mutation_rejected(self):
        nodes=dict(self.nodes);nodes['U14818','1']=h.SEEDS['CAN']
        with self.assertRaisesRegex(ValueError,'Ferrite return endpoints'):h.classify(self.parts,nodes,self.nc)

    def test_unknown_isolation_family_is_not_silently_conductive(self):
        parts=copy.deepcopy(self.parts);parts['U8001']['mpn']='ISO9999-unknown'
        with self.assertRaisesRegex(ValueError,'Unreviewed isolation'):h.classify(parts,self.nodes,self.nc)

    def test_floating_substrate_join_mutation_rejected(self):
        nodes=dict(self.nodes);nodes['U8001','12']=h.SEEDS['FIELD_B']
        with self.assertRaisesRegex(ValueError,'SUB must remain'):h.classify(self.parts,nodes,self.nc)

    def test_parallel_pad_rows_do_not_invent_insulation_rating(self):
        def pad(x,y):return {'position_mm':[x,y],'copper_aabb_mm':[x-.8,y-.205,x+.8,y+.205]}
        shape=h.barrier_geometry([[pad(-2.7,-2.2225),pad(-2.7,2.2225)],
                                  [pad(2.7,-2.2225),pad(2.7,2.2225)]])
        self.assertEqual(shape['pad_edge_projection_gap_mm'],3.8)
        self.assertIn('certification is not established',shape['meaning'])

    def test_mechanical_hole_is_not_stencil_or_electrical_pin(self):
        self.assertEqual(h.auxiliary_pad_kind('',False,'NPTH',['F.Cu','B.Cu','F.Mask']),'npth')
        with self.assertRaisesRegex(ValueError,'electrical pin number'):
            h.auxiliary_pad_kind('1',False,'NPTH',['F.Cu','B.Cu'])

    def test_stencil_and_mask_only_apertures_remain_distinct(self):
        self.assertEqual(h.auxiliary_pad_kind('',False,'other',['F.Paste']),'stencil_only')
        self.assertEqual(h.auxiliary_pad_kind('',False,'other',['F.Mask']),'mask_only')
        self.assertIsNone(h.auxiliary_pad_kind('1',True,'other',['F.Cu','F.Mask']))

    def test_unknown_unnumbered_copper_cannot_hide_as_aperture(self):
        with self.assertRaisesRegex(ValueError,'Undeclared copper'):
            h.auxiliary_pad_kind('',True,'other',['F.Cu'])
        with self.assertRaisesRegex(ValueError,'Undeclared copper'):
            h.auxiliary_pad_kind('1',False,'other',['F.Paste'])


if __name__=='__main__':unittest.main()
