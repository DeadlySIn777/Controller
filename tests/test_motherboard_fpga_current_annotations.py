"""Current FPGA text cannot silently rewrite historical electrical allocation."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_apply_motherboard_fpga_allocation import (
    reconcile_current_allocation_annotations,parse,children,value)

class FPGAAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old=ROOT/'reports/motherboard-integration-20260930/r23-2688-reset-bypass-staged'
        cls.core=parse((old/'fpga_core.kicad_sch').read_text())
        cls.metadata=json.loads((old/'fpga-allocation-parent.json').read_text())
    def test_current_counts_preserve_all_pin_ports_and_ledgers(self):
        original=copy.deepcopy(self.core);metadata=copy.deepcopy(self.metadata)
        core,m=reconcile_current_allocation_annotations(self.core,self.metadata)
        self.assertEqual(original,self.core);self.assertEqual(metadata,self.metadata)
        self.assertEqual([n for n in core if not isinstance(n,list) or n[0]!='text'],
                         [n for n in original if not isinstance(n,list) or n[0]!='text'])
        self.assertEqual(self.metadata['exact_pin_rename_ledger'],m['exact_pin_rename_ledger'])
        self.assertEqual((135,48),(m['assigned_user_pins'],m['free_user_gpio']))
        texts=[value(t[1]) for t in children(core,'text')]
        self.assertEqual(4,sum(t.startswith('HISTORICAL TRANSACTION') for t in texts))
        self.assertEqual(1,sum(t.startswith('CURRENT IS2 FPGA ALLOCATION:135 assigned /48 free') for t in texts))
    def test_wrong_actual_resource_count_rejected(self):
        m=copy.deepcopy(self.metadata);m['assigned_user_pins']=142
        with self.assertRaisesRegex(ValueError,'exact reviewed135/48'):
            reconcile_current_allocation_annotations(self.core,m)
    def test_missing_historical_annotation_rejected(self):
        c=copy.deepcopy(self.core)
        c.remove(next(t for t in children(c,'text') if value(t[1]).startswith('IS2 CURRENT reconciliation:')))
        with self.assertRaisesRegex(ValueError,'historical FPGA annotation'):
            reconcile_current_allocation_annotations(c,self.metadata)
    def test_repeated_reconciliation_rejected(self):
        c,m=reconcile_current_allocation_annotations(self.core,self.metadata)
        with self.assertRaisesRegex(ValueError,'already reconciled'):
            reconcile_current_allocation_annotations(c,m)

if __name__=='__main__':unittest.main()
