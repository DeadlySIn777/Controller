from pathlib import Path
import sys,json,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import hardware_review_motherboard_di_capacitors as h


class Owners(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=h.ROOT/'reports/motherboard-integration-20260930/r23-2688-reset-bypass-staged'
        cls.parts=json.loads((source/'design.json').read_text(encoding='utf-8'))['components']
        cls.nodes,cls.nc,_=h.native(source/'netlist.xml')

    def test_all_actual_36_caps_and_separate_domains(self):
        rows=h.owners(self.parts,self.nodes,self.nc)
        self.assertEqual(len(rows),36)
        self.assertEqual(sum(r['category']=='field_filter' for r in rows),24)
        self.assertEqual(sum(r['category']=='local_bypass' for r in rows),12)
        even=next(r for r in rows if r['ref']=='C8001');odd=next(r for r in rows if r['ref']=='C8002')
        self.assertEqual(even['actual_owner_endpoints']['1'][0]['pin'],'16')
        self.assertEqual(odd['actual_owner_endpoints']['1'][0]['pin'],'11')

    def test_upstream_input_is_not_filter_owner(self):
        nodes=dict(self.nodes);nodes['C8001','1']=nodes['U8001','15']
        with self.assertRaisesRegex(ValueError,'SENSE'):h.owners(self.parts,nodes,self.nc)

    def test_field_filter_return_cannot_be_logic(self):
        nodes=dict(self.nodes);nodes['C8001','2']=nodes['U8001','1']
        with self.assertRaisesRegex(ValueError,'field return'):h.owners(self.parts,nodes,self.nc)

    def test_logic_bypass_must_use_actual_supply(self):
        nodes=dict(self.nodes);nodes['C8101','1']=nodes['U8001','4']
        with self.assertRaisesRegex(ValueError,'VCC'):h.owners(self.parts,nodes,self.nc)

    def test_logic_nc7_is_not_invented_ground(self):
        with self.assertRaisesRegex(ValueError,'GND/NC'):h.owners(self.parts,self.nodes,self.nc-{('U8001','7')})


if __name__=='__main__':unittest.main()
