"""Fault-focused native PCB population and output-ownership mutations."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_populate_motherboard_pcb as tool

REPORT=Path(__file__).resolve().parent
ACCEPTED=REPORT/'populated-r03'
SOURCE=ACCEPTED/'source-inputs'
BASE=SOURCE/'local-signal-routing-v1-local-signal-routes-candidate.kicad_pcb'
BOARD=ACCEPTED/'motherboard-populated-candidate.kicad_pcb'


def tuples(v):return tuple(tuples(x) for x in v) if isinstance(v,list) else v


class PCBPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=tool.load(SOURCE/'motherboard-design.json')
        cls.mapping=tool.load(SOURCE/'motherboard-assembly-map.json')
        cls.ledger=cls.mapping['native_net_renames_allowed']
        cls.native,cls.nodes=tool.native_parts_and_nets(SOURCE/'motherboard-netlist.xml',cls.model['components'])
        base=pcbnew.LoadBoard(str(BASE))
        cls.old_tracks={t.m_Uuid.AsString():tool.identity(t) for t in base.GetTracks()}
        cls.old_pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):tool.pad_identity(p) for p in base.GetPads() if tool.copper_pad(p)}
        cls.old_fps={f.GetReference():(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),tool.footprint_name(f))
                     for f in base.GetFootprints()}
        cls.templates={r:[tuples(v) for v in rows] for r,rows in tool.load(ACCEPTED/'exact-source-pad-templates.json').items()}

    def setUp(self):self.board=pcbnew.LoadBoard(str(BOARD))
    def footprint(self,ref):return next(f for f in self.board.GetFootprints() if f.GetReference()==ref)
    def check(self):return tool.verify_population(self.board,self.model,self.nodes,self.old_tracks,self.old_pads,self.old_fps,self.ledger,self.templates)

    def mutate_native(self,callback):
        tree=tool.parse(BOARD.read_text(encoding='utf8'));callback(tree)
        self.temp=tempfile.TemporaryDirectory();path=Path(self.temp.name)/'mutation.kicad_pcb'
        path.write_text(tool.dump(tree)+'\n',encoding='utf8');self.board=pcbnew.LoadBoard(str(path))

    def native_footprint(self,tree,ref):
        return next(f for f in tool.children(tree,'footprint') if any(tool.value(p[1])=='Reference' and tool.value(p[2])==ref
                    for p in tool.children(f,'property')))

    def test_complete_actual_source_population_and_paste_inventory_agree(self):
        result=self.check();self.assertTrue(result['ok'],result['errors'])
        self.assertEqual(880,result['physical_footprints']);self.assertEqual(878,result['fitted_footprints'])
        self.assertEqual(3317,result['native_numbered_copper_nodes']);self.assertEqual(228,result['stencil_only_unnumbered_apertures'])
        self.assertEqual(64,len(result['bounded_retained_FPGA_pad_renames']))

    def test_all_eighteen_iso1212_bypasses_meet_manufacturer_two_mm_placement_target(self):
        functions=tool.native_pin_functions(SOURCE/'motherboard-netlist.xml')
        rows=tool.load(ACCEPTED/'placement-ledger.json')
        found=[]
        for row in rows:
            target=row.get('bypass_target')
            if target and self.model['components'][target]['mpn']=='ISO1212DBQR':
                found.append(row)
                self.assertEqual(target+'.2',row['supply_pin'])
                self.assertEqual('VCC1',functions[target]['2']['name'])
                self.assertLessEqual(row['supply_pad_distance_mm'],2)
                self.assertFalse(row['bypass_copper_routed'])
        self.assertEqual(18,len(found))

    def test_r03_changes_only_exact_bounded_new_capacitors_and_neighbors(self):
        report=tool.load(ACCEPTED/'report.json')
        refs=set(report['bounded_new_capacitor_references']+report['bounded_neighbor_passive_references']+report['bounded_receiver_references'])
        self.assertEqual(refs,set(report['actual_native_changed_footprints']))
        self.assertFalse(refs&set(self.old_fps))
        old=tool.raw_items(REPORT/'populated-r02/motherboard-populated-candidate.kicad_pcb','footprint')
        new=tool.raw_items(BOARD,'footprint')
        actual={f.GetReference()for f in self.board.GetFootprints()if old[f.m_Uuid.AsString()]!=new[f.m_Uuid.AsString()]}
        self.assertEqual(refs,actual)
        for key in ('zone','segment','via','gr_text','gr_line'):
            self.assertEqual(tool.raw_items(REPORT/'populated-r02/motherboard-populated-candidate.kicad_pcb',key),tool.raw_items(BOARD,key))

    def test_previous_ten_over_three_mm_targets_now_have_authentic_close_supply_pads(self):
        prior=tool.load(REPORT/'populated-r02/report.json')
        refs={r['reference']for r in prior['bypass_review']['targets_over_3mm']}
        rows={r['reference']:r for r in tool.load(ACCEPTED/'placement-ledger.json')}
        self.assertEqual(10,len(refs))
        for ref in refs:
            row=rows[ref];target,pin=row['supply_pin'].split('.')
            cp=next(p for p in self.footprint(ref).Pads()if p.GetNetname()==self.nodes[target,pin])
            tp=next(p for p in self.footprint(target).Pads()if p.GetNumber()==pin)
            self.assertAlmostEqual(__import__('math').dist(tool.mm(cp.GetPosition()),tool.mm(tp.GetPosition())),row['supply_pad_distance_mm'],places=5)
            self.assertLessEqual(row['supply_pad_distance_mm'],3)
            self.assertFalse(row['bypass_copper_routed'])

    def test_all_retained_native_footprint_copper_and_plane_fields_survive(self):
        result=tool.native_retained_objects(BASE,BOARD,self.ledger)
        self.assertTrue(result['ok'],result['errors']);self.assertEqual(327,result['retained_full_native_footprints'])
        self.assertEqual(64,result['exactly_bounded_pad_net_changes'])

    def test_missing_real_footprint_cannot_be_hidden_by_full_part_count_claim(self):
        self.mutate_native(lambda tree:tree.remove(self.native_footprint(tree,'U8001')))
        self.assertFalse(self.check()['ok'])

    def test_duplicate_physical_reference_is_rejected(self):
        self.footprint('U8002').SetReference('U8001')
        self.assertIn('Duplicate physical reference on board',self.check()['errors'])

    def test_numbered_source_pin_and_net_are_checked_independently(self):
        pad=next(p for p in self.footprint('R8001').Pads() if p.GetNumber()=='1')
        pad.SetNet(self.board.FindNet('/LOGIC_GND'));self.assertFalse(self.check()['ok'])

    def test_missing_unnumbered_paste_aperture_is_not_ignored(self):
        def remove(tree):
            fp=self.native_footprint(tree,'U10004');pad=next(p for p in tool.children(fp,'pad') if tool.value(p[1])=='')
            fp.remove(pad)
        self.mutate_native(remove)
        self.assertTrue(any('pad/stencil geometry' in e for e in self.check()['errors']))

    def test_changed_paste_only_aperture_geometry_is_rejected(self):
        pad=next(p for p in self.footprint('U10004').Pads() if not p.GetNumber() and p.IsOnLayer(pcbnew.F_Paste))
        pad.SetSize(tool.xy((.1,.1)));self.assertFalse(self.check()['ok'])

    def test_wrong_package_assignment_is_rejected(self):
        self.footprint('U8001').SetFPID(pcbnew.LIB_ID('Package_SO','SOIC-16_3.9x9.9mm_P1.27mm'))
        self.assertFalse(self.check()['ok'])

    def test_retained_motor_signal_cannot_be_renamed_by_a_wildcard(self):
        p=next(p for p in self.footprint('U1001').Pads() if p.GetNumber()=='P2')
        p.SetNet(self.board.FindNet('/LOGIC_GND'))
        self.assertTrue(any('Unapproved retained pad rename' in e for e in self.check()['errors']))

    def test_retained_routed_copper_cannot_be_adjusted_by_population(self):
        t=next(t for t in self.board.GetTracks() if not isinstance(t,pcbnew.PCB_VIA))
        t.SetWidth(t.GetWidth()+10000)
        self.assertFalse(self.check()['ok'])

    def test_retained_full_native_annotation_cannot_be_silently_removed(self):
        fp=self.footprint('U1001');fp.Value().SetText('ALTERED_ORIGINAL_VALUE')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'mutated.kicad_pcb';pcbnew.SaveBoard(str(path),self.board)
            self.assertFalse(tool.native_retained_objects(BASE,path,self.ledger)['ok'])

    def test_retained_filled_zone_or_clearance_cannot_be_silently_changed(self):
        self.board.Zones()[0].SetLocalClearance(pcbnew.FromMM(.25))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'mutated.kicad_pcb';pcbnew.SaveBoard(str(path),self.board)
            self.assertFalse(tool.native_retained_objects(BASE,path,self.ledger)['ok'])

    def test_corrected_watchdog_command_owns_inputs_with_default_low(self):
        self.assertTrue(tool.watchdog_clear_source_check(self.model,self.nodes)['ok'])

    def test_original_output_contention_source_is_rejected(self):
        s=REPORT/'populated-r01/source-inputs';m=tool.load(s/'motherboard-design.json')
        parts,nodes=tool.native_parts_and_nets(s/'motherboard-netlist.xml',m['components'])
        result=tool.watchdog_clear_source_check(m,nodes)
        self.assertFalse(result['ok']);self.assertTrue(any('driven clear OUTPUT' in e for e in result['errors']))

    def test_an_active_high_clear_cannot_default_high(self):
        model=copy.deepcopy(self.model);model['components']['R12006']['resistance_ohm']=47000
        nodes=dict(self.nodes);nodes['R12006','2']='/IO_3V3'
        self.assertFalse(tool.watchdog_clear_source_check(model,nodes)['ok'])

    def test_each_DI_pair_region_contains_exactly_one_ISO_receiver(self):
        placements=tool.load(ACCEPTED/'placement-ledger.json')
        for i in range(12):
            refs=[p['reference'] for p in placements if p['region']=='DI-pair-'+str(i)]
            self.assertEqual(['U'+str(8001+i)],sorted(r for r in refs if r.startswith('U')))
            self.assertIn('C'+str(8101+i),refs)

    def test_DI_bypass_is_measured_to_actual_VCC1_pin_not_the_enable_pin(self):
        placements={p['reference']:p for p in tool.load(ACCEPTED/'placement-ledger.json')}
        for i in range(12):
            cap=placements['C'+str(8101+i)]
            self.assertEqual('U'+str(8001+i)+'.2',cap['supply_pin'])
            self.assertEqual('VCC1',cap['supply_pin_function'])
            self.assertLess(cap['supply_pad_distance_mm'],3.)
            self.assertFalse(cap['bypass_copper_routed'])


if __name__=='__main__':unittest.main(verbosity=2)

