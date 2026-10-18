"""Bounded source promotion checks, including physical net-partition mutations."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_apply_motherboard_fpga_allocation import (
    apply_base_allocation,actual_pin_coordinates,child,children,dump,erc_summary,
    apply_slow_enable_allocation,SLOW_ENABLE_RECEIPT,
    FIELD_ALIASES,fpga_sheet,parse,point,q,verify_native,value)
from hardware_apply_motherboard_fpga_allocation import (
    apply_obsolete_home_deallocation,audit_obsolete_home_copper,
    verify_obsolete_home_native,HOME_DEALLOC_PINS)
from hardware_apply_motherboard_fpga_allocation import (
    apply_reserved_health_reconciliation,audit_reserved_health_copper,
    verify_reserved_health_native,RESERVED_HEALTH_PINS)

REPORT=ROOT/'reports/motherboard-fpga-source-20260930'
SOURCE=REPORT/'inputs/motherboard'
CANDIDATE=REPORT/'candidate-r03'


class MotherboardFPGAAllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=parse((SOURCE/'motherboard.kicad_sch').read_text(encoding='utf8'))
        cls.core=parse((SOURCE/'fpga_core.kicad_sch').read_text(encoding='utf8'))
        cls.proposal=json.loads((SOURCE/'fpga-allocation-proposal.json').read_text(encoding='utf8'))
        cls.before=ET.parse(SOURCE/'netlist.xml')
        cls.new_root,cls.new_core,cls.metadata=apply_base_allocation(
            cls.root,cls.core,cls.proposal,cls.before)
        cls.promotions=[r for r in cls.proposal['candidates']['base_preserve_all_current']['signals']
                        if r['allocation_state']=='proposed_NC_to_named_signal']

    def apply(self,root=None,core=None,proposal=None):
        return apply_base_allocation(root or self.root,core or self.core,proposal or self.proposal,self.before)

    def mutated_proposal(self):return copy.deepcopy(self.proposal)

    def native_check(self,tree):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'after.xml';tree.write(path,encoding='utf8')
            return verify_native(SOURCE/'netlist.xml',path,copy.deepcopy(self.metadata))

    def test_transformation_does_not_mutate_either_input_tree(self):
        r=copy.deepcopy(self.root);c=copy.deepcopy(self.core)
        nr,nc,m=self.apply(r,c)
        self.assertEqual(r,self.root);self.assertEqual(c,self.core)
        self.assertIsNot(nr,r);self.assertIsNot(nc,c)
        self.assertEqual(64,m['promoted_nc_pin_count'])

    def test_two_slow_enables_preserve_the_exact_base64_and_inputs(self):
        r,c,m=copy.deepcopy(self.new_root),copy.deepcopy(self.new_core),copy.deepcopy(self.metadata)
        nr,nc,nm=apply_slow_enable_allocation(r,c,m)
        self.assertEqual(r,self.new_root);self.assertEqual(c,self.new_core);self.assertEqual(m,self.metadata)
        self.assertEqual(nm['exact_pin_rename_ledger'][:64],self.metadata['exact_pin_rename_ledger'])
        self.assertEqual([(v['signal'],v['pin'],v['direction']) for v in nm['slow_enable_pin_rename_ledger']],
                         [('FAST_PORTS_ENABLE','M4','output'),('XF_POWER_ENABLE','M6','output')])
        self.assertEqual((163,20,66),(nm['assigned_user_pins'],nm['free_user_gpio'],nm['promoted_nc_pin_count']))
        self.assertEqual(22,len(children(nc,'no_connect')))
        self.assertEqual(136,len(children(fpga_sheet(nr),'pin')))
        self.assertFalse(nm['vendor_fit']);self.assertFalse(nm['slow_enable_gateware_implemented'])

    def test_slow_enable_changed_bank_ball_pull_or_signal_rejected(self):
        for key,new in [('bank','BANK3B'),('ball','M5'),('external_low_default_ohm',100000),
                        ('signal','UNREVIEWED_ENABLE'),('direction','input')]:
            with self.subTest(key=key):
                receipt=json.loads(SLOW_ENABLE_RECEIPT.read_text(encoding='utf8'));receipt['signals'][0][key]=new
                with self.assertRaisesRegex(ValueError,'exact frozen primary receipt'):
                    apply_slow_enable_allocation(self.new_root,self.new_core,self.metadata,receipt)

    def test_slow_enable_rejects_missing_nc_cross_and_occupied_pin(self):
        for ball in ('M4','M6'):
            with self.subTest(ball=ball):
                c=copy.deepcopy(self.new_core);xy=actual_pin_coordinates(c)[ball]['coordinate']
                c.remove(next(n for n in children(c,'no_connect') if point(child(n,'at'))==xy))
                with self.assertRaisesRegex(ValueError,'actual free NC cross'):
                    apply_slow_enable_allocation(self.new_root,c,self.metadata)

    def test_slow_enable_rejects_repeat_transform_and_non_base_metadata(self):
        r,c,m=apply_slow_enable_allocation(self.new_root,self.new_core,self.metadata)
        with self.assertRaisesRegex(ValueError,'unreused BASE161/64'):
            apply_slow_enable_allocation(r,c,m)
        bad=copy.deepcopy(self.metadata);bad['optional_five_reuse_applied']=True
        with self.assertRaisesRegex(ValueError,'unreused BASE161/64'):
            apply_slow_enable_allocation(self.new_root,self.new_core,bad)

    def test_slow_enable_actual_ports_are_output_and_exact_names(self):
        r,c,m=apply_slow_enable_allocation(self.new_root,self.new_core,self.metadata)
        for n in ('FAST_PORTS_ENABLE','XF_POWER_ENABLE'):
            label=next(l for l in children(c,'hierarchical_label') if value(l[1])==n)
            self.assertEqual('output',child(label,'shape')[1])
            port=next(p for p in children(fpga_sheet(r),'pin') if value(p[1])==n)
            self.assertEqual('output',port[2]);self.assertEqual('fpga_core/'+n,m['root_sheet_port_map'][n])

    def test_exactly_64_actual_NC_crosses_become_ports_and_24_NCs_remain(self):
        self.assertEqual(88,len(children(self.core,'no_connect')))
        self.assertEqual(24,len(children(self.new_core,'no_connect')))
        self.assertEqual(134,len(children(fpga_sheet(self.new_root),'pin')))
        self.assertEqual(161,self.metadata['assigned_user_pins'])
        self.assertEqual(22,self.metadata['free_user_gpio'])
        coords=actual_pin_coordinates(self.new_core)
        actual_nc={point(child(n,'at')) for n in children(self.new_core,'no_connect')}
        self.assertIn(coords['R2']['coordinate'],actual_nc)
        self.assertFalse(self.metadata['optional_five_reuse_applied'])

    def test_manufacturer_symbol_and_local_library_are_preserved(self):
        self.assertEqual(child(self.core,'lib_symbols'),child(self.new_core,'lib_symbols'))
        self.assertEqual((SOURCE/'fpga_core.kicad_sym').read_bytes(),(CANDIDATE/'fpga_core.kicad_sym').read_bytes())
        self.assertEqual(256,len(actual_pin_coordinates(self.new_core)))

    def test_existing_semantic_aliases_preserve_the_physical_local_endpoints(self):
        for alias,(ball,old) in FIELD_ALIASES.items():
            self.assertEqual([l for l in children(self.core,'label') if value(l[1])==old],
                             [l for l in children(self.new_core,'label') if value(l[1])==old])
            item=next(r for r in self.metadata['semantic_alias_exports'] if r['signal']==alias)
            self.assertEqual(ball,item['ball']);self.assertIsNone(item['hierarchy_port'])
            self.assertFalse(item['hierarchy_export_applied'])
        self.assertFalse(self.metadata['vendor_fit']);self.assertFalse(self.metadata['manufacturing_ready'])

    def test_duplicate_promotion_ball_is_rejected(self):
        p=self.mutated_proposal();a=[r for r in p['candidates']['base_preserve_all_current']['signals']
                                  if r['allocation_state']=='proposed_NC_to_named_signal']
        a[1]['ball']=a[0]['ball']
        with self.assertRaisesRegex(ValueError,'Duplicate promotion ball'):self.apply(proposal=p)

    def test_wrong_official_bank_and_manufacturer_row_are_rejected(self):
        for field,new in [('bank','BANK4A'),('worksheet_row',999)]:
            with self.subTest(field=field):
                p=self.mutated_proposal();p['candidates']['base_preserve_all_current']['signals'][0][field]=new
                with self.assertRaisesRegex(ValueError,'official workbook'):self.apply(proposal=p)

    def test_5V_IO_or_a_different_function_ledger_is_rejected(self):
        for field,new,message in [('vccio_nominal_v',5,'Unsupported user voltage'),
                                  ('signal','STEP0_ALTERED','exact reviewed candidate')]:
            with self.subTest(field=field):
                p=self.mutated_proposal();p['candidates']['base_preserve_all_current']['signals'][0][field]=new
                with self.assertRaisesRegex(ValueError,message):self.apply(proposal=p)

    def test_LVDS_as_GPIO_output_is_outside_this_reviewed_candidate(self):
        p=self.mutated_proposal();r=next(r for r in p['candidates']['base_preserve_all_current']['signals']
                                        if r['mode']=='LVDS_as_GPIO');r['direction']='output'
        with self.assertRaisesRegex(ValueError,'LVDS GPIO as inputs only'):self.apply(proposal=p)

    def test_optional_existing_pin_reuse_and_vendor_fit_claim_are_rejected(self):
        p=self.mutated_proposal();p['candidates']['base_preserve_all_current']['existing_ball_repurposes']=[{'ball':'K14'}]
        with self.assertRaisesRegex(ValueError,'not authorized'):self.apply(proposal=p)
        p=self.mutated_proposal();p['vendor_fit']=True
        with self.assertRaisesRegex(ValueError,'readiness boundary'):self.apply(proposal=p)

    def test_actual_missing_NC_cross_is_not_silently_treated_as_available(self):
        c=copy.deepcopy(self.core);xy=actual_pin_coordinates(c)[self.promotions[0]['ball']]['coordinate']
        c.remove(next(n for n in children(c,'no_connect') if point(child(n,'at'))==xy))
        with self.assertRaisesRegex(ValueError,'actual NC cross'):self.apply(core=c)

    def test_an_existing_label_on_the_new_pin_is_not_silently_overwritten(self):
        c=copy.deepcopy(self.core);xy=actual_pin_coordinates(c)[self.promotions[0]['ball']]['coordinate']
        c.append(['label',q('OCCUPIED'),['at',str(xy[0]),str(xy[1]),'0']])
        with self.assertRaisesRegex(ValueError,'already labelled'):self.apply(core=c)

    def test_wrong_embedded_manufacturer_pin_name_is_rejected(self):
        c=copy.deepcopy(self.core);coordinates=actual_pin_coordinates(c)
        child(coordinates[self.promotions[0]['ball']]['pin'],'name')[1]=q('INCORRECT_PIN')
        with self.assertRaisesRegex(ValueError,'Manufacturer FPGA pin-name mismatch'):self.apply(core=c)

    def test_unreviewed_FPGA_rotation_is_rejected(self):
        c=copy.deepcopy(self.core);u=next(s for s in children(c,'symbol')
                                        if any(p[1]==q('Reference') and p[2]==q('U1001') for p in children(s,'property')))
        child(u,'at')[3]='90'
        with self.assertRaisesRegex(ValueError,'Rotated FPGA'):self.apply(core=c)

    def test_branched_root_stub_is_not_erased_by_repacking(self):
        r=copy.deepcopy(self.root);xy=point(child(children(fpga_sheet(r),'pin')[0],'at'))
        r.append(['wire',['pts',['xy',str(xy[0]),str(xy[1])],['xy',str(xy[0]),str(xy[1]+5.08)]],
                  ['stroke',['width','0'],['type','default']],['uuid',q('e3ff3a56-43e6-44da-83a7-07f6e28f21d9')]])
        with self.assertRaisesRegex(ValueError,'one root stub'):self.apply(root=r)

    def test_native_export_agrees_for_all_3173_pins_and_exact_64_renames(self):
        result=verify_native(SOURCE/'netlist.xml',CANDIDATE/'netlist.xml',copy.deepcopy(self.metadata))
        self.assertTrue(result['ok'],result['errors']);self.assertEqual(3173,result['source_native_pin_count'])
        self.assertEqual(3173,result['candidate_native_pin_count']);self.assertEqual(3109,result['untouched_existing_native_pins'])
        self.assertEqual(64,len(result['verified_pin_changes']))

    def test_duplicate_readable_net_name_cannot_hide_a_split_physical_connection(self):
        t=ET.parse(CANDIDATE/'netlist.xml');nets=t.find('.//nets')
        original=next(n for n in nets if len(n.findall('node'))>1)
        node=original.findall('node')[-1];original.remove(node)
        split=ET.SubElement(nets,'net',{'code':'99999','name':original.attrib['name']});split.append(node)
        result=self.native_check(t)
        self.assertFalse(result['ok']);self.assertTrue(any('Duplicate native net name' in e for e in result['errors']))

    def test_an_unapproved_retained_motor_net_rename_is_rejected(self):
        t=ET.parse(CANDIDATE/'netlist.xml');net=next(n for n in t.findall('.//nets/net')
                                                 if n.find("node[@ref='U1001'][@pin='P2']") is not None)
        net.attrib['name']='/ALTERED_STEP0'
        self.assertTrue(any('Unapproved native rename' in e for e in self.native_check(t)['errors']))

    def test_an_extra_NC_promotion_outside_the_64_pin_ledger_is_rejected(self):
        t=ET.parse(CANDIDATE/'netlist.xml');net=next(n for n in t.findall('.//nets/net')
                                                 if n.attrib['name'].startswith('unconnected-(U1001-'))
        net.attrib['name']='/UNAPPROVED_SIGNAL'
        self.assertFalse(self.native_check(t)['ok'])

    def test_clear_and_watchdog_trip_polarity_and_OPI_fanout_remain_explicit(self):
        obligations={r['signal']:r for r in self.metadata['parent_endpoint_obligations']}
        self.assertEqual(['OPI_REARM_TX','OPI_REARM_BOE'],obligations['OPI_REARM_M']['target_nets'])
        self.assertEqual(['WD_REARM_M','WD_REARM_O'],obligations['WATCHDOG_TRIP_CLEAR']['target_nets'])
        self.assertIn('ACTIVE HIGH',obligations['WATCHDOG_TRIP_CLEAR']['polarity'])
        self.assertIn('must never be driven by FPGA',obligations['WATCHDOG_TRIP_CLEAR']['polarity'])
        for n in ('WATCHDOG_TRIP_M','WATCHDOG_TRIP_O'):
            self.assertIn('ACTIVE LOW',obligations[n]['polarity'])
        self.assertFalse(any(r['implemented_connection'] for r in obligations.values()))

    def test_clear_command_destination_is_a_native_input_and_never_a_driven_output(self):
        libs={(p.attrib['lib'],p.attrib['part']):{n.attrib['num']:n.attrib['type'] for n in p.findall('./pins/pin')}
              for p in self.before.findall('.//libparts/libpart')}
        def kind(ref,pin):
            comp=next(c for c in self.before.findall('.//components/comp') if c.attrib['ref']==ref)
            source=comp.find('libsource').attrib
            return libs[source['lib'],source['part']][pin]
        actual={}
        for net in self.before.findall('.//nets/net'):
            for node in net.findall('node'):actual[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
        for pin,name in [('1','WD_REARM_M'),('3','WD_REARM_O')]:
            self.assertEqual('input',kind('U4018',pin));self.assertEqual('/mc_permission/'+name,actual['U4018',pin])
        for pin,name in [('7','WD_M_TRIP_CLEAR_N'),('3','WD_O_TRIP_CLEAR_N')]:
            self.assertEqual('output',kind('U4019',pin));self.assertEqual('/mc_permission/'+name,actual['U4019',pin])
        targets=next(r['target_nets'] for r in self.metadata['parent_endpoint_obligations'] if r['signal']=='WATCHDOG_TRIP_CLEAR')
        self.assertEqual(['WD_REARM_M','WD_REARM_O'],targets)

    def test_ERC_warnings_are_counted_and_never_reported_as_clean(self):
        result=erc_summary(CANDIDATE/'erc.json');baseline=erc_summary(REPORT/'baseline-erc.json')
        self.assertEqual(0,result['errors']);self.assertEqual(158,result['warnings'])
        self.assertEqual(122,result['warnings']-baseline['warnings'])
        self.assertEqual([],result['ignored_checks']);self.assertFalse(result['clean'])


class ObsoleteHomeDeallocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage=REPORT/'home-deallocation-r01';src=cls.stage/'inputs'
        cls.root=parse((src/'motherboard.kicad_sch').read_text());cls.core=parse((src/'fpga_core.kicad_sch').read_text())
        cls.before=ET.parse(src/'netlist.xml');cls.meta=json.loads((src/'fpga-allocation-applied.json').read_text())
        cls.meta['exact_pin_rename_ledger']=json.loads((src/'assembly-map.json').read_text())['native_net_renames_allowed']
        cls.meta.update(assigned_user_pins=163,free_user_gpio=20,promoted_nc_pin_count=66)
        cls.evidence=json.loads((cls.stage/'copper-zero-evidence.json').read_text())
        cls.after=ET.parse(cls.stage/'candidate/netlist.xml');cls.applied=json.loads((cls.stage/'candidate-metadata.json').read_text())
    def apply(self,root=None,core=None,meta=None,before=None,evidence=None):
        return apply_obsolete_home_deallocation(root or self.root,core or self.core,meta or self.meta,before or self.before,evidence or self.evidence)
    def test_actual24_NC_delta_preserves_inputs_all_other_gpio_and_bounded_counts(self):
        r,c,m=copy.deepcopy(self.root),copy.deepcopy(self.core),copy.deepcopy(self.meta)
        nr,nc,nm=self.apply(r,c,m)
        self.assertEqual(r,self.root);self.assertEqual(c,self.core);self.assertEqual(m,self.meta);self.assertEqual(nr,self.root)
        self.assertEqual((151,32,66,12),(nm['assigned_user_pins'],nm['free_user_gpio'],nm['promoted_nc_pin_count'],nm['deallocated_user_pin_count']))
        self.assertEqual(24,len(children(nc,'no_connect'))-len(children(c,'no_connect')))
        self.assertEqual(m['exact_pin_rename_ledger'],nm['exact_pin_rename_ledger'][:66])
        self.assertEqual(12,len(nm['home_deallocation_pin_rename_ledger']));self.assertEqual(12,len(nm['home_boundary_nc_ledger']))
    def test_obsolete_HOMEs_cannot_include_active_probe_or_EXT_balls(self):
        self.assertFalse({'G12','G15','G16'}&{r[1] for r in HOME_DEALLOC_PINS})
        nr,nc,nm=self.apply()
        for name in ['PROBE_FPGA','TOOLSETTER_FPGA','PROTECTIVE_STATUS_FPGA']:
            self.assertEqual([l for l in children(self.core,'label') if value(l[1])==name],[l for l in children(nc,'label') if value(l[1])==name])
        r=verify_obsolete_home_native(self.stage/'inputs/netlist.xml',self.stage/'candidate/netlist.xml',self.applied)
        self.assertTrue(r['ok'],r['errors']);self.assertEqual((7422,7422),(r['native_pins_before'],r['native_pins_after']))
    def test_actual_CAD23_copper_proof_is_hash_anchored_and_zero_on_all12(self):
        r=audit_obsolete_home_copper(self.evidence['board_path']);self.assertEqual(r,self.evidence)
        self.assertEqual('54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5',r['board_sha256'])
        self.assertTrue(all((x['segment'],x['via'],x['zone'])==(0,0,0) for x in r['rows']));self.assertFalse(r['J1007_physical_footprint_present'])
    def test_copper_evidence_cannot_hide_routing_or_stale_board(self):
        for change in ['count','hash']:
            e=copy.deepcopy(self.evidence)
            if change=='count':e['rows'][0]['segment']=1
            else:e['board_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'stale, incomplete or modified'):self.apply(evidence=e)
    def test_an_extra_actual_HOME_endpoint_prevents_silent_deallocation(self):
        t=copy.deepcopy(self.before);net=next(n for n in t.findall('./nets/net') if n.attrib['name']=='/fpga_core/HOME0_FPGA');ET.SubElement(net,'node',{'ref':'FAKE_PHYSICAL','pin':'1'})
        with self.assertRaisesRegex(ValueError,'two obsolete endpoints'):self.apply(before=t)
    def test_J1007_cannot_silently_become_a_physical_header(self):
        c=copy.deepcopy(self.core);h=next(s for s in children(c,'symbol') if any(value(p[1])=='Reference' and value(p[2])=='J1007' for p in children(s,'property')))
        prop=next(p for p in children(h,'property') if value(p[1])=='Footprint');prop[2]=q('Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical')
        with self.assertRaisesRegex(ValueError,'physical'):self.apply(core=c)
    def test_changed_HOME_stub_or_prior_NC_is_rejected(self):
        c=copy.deepcopy(self.core);l=next(l for l in children(c,'label') if value(l[1])=='HOME0_FPGA');l[1]=q('HOME_NEW_UNREVIEWED')
        with self.assertRaisesRegex(ValueError,'simple local stubs'):self.apply(core=c)
    def test_exact66_prerequisite_and_prior_application_are_not_guessed(self):
        for k,v in [('assigned_user_pins',162),('home_deallocation_applied',True),('manufacturing_ready',True)]:
            m=copy.deepcopy(self.meta);m[k]=v
            with self.assertRaises(ValueError):self.apply(meta=m)
        m=copy.deepcopy(self.meta);m['exact_pin_rename_ledger'][-1]['pin']='M5'
        with self.assertRaisesRegex(ValueError,'prerequisite'):self.apply(meta=m)
    def test_whole_native_check_rejects_unrelated_probe_net_change(self):
        t=copy.deepcopy(self.after);n=next(n for n in t.findall('./nets/net') if any(p.attrib['ref']=='U1001' and p.attrib['pin']=='G12' for p in n.findall('node')));n.attrib['name']='/UNREVIEWED_PROBE'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mutated.xml';t.write(p,encoding='utf-8');r=verify_obsolete_home_native(self.stage/'inputs/netlist.xml',p,self.applied);self.assertFalse(r['ok']);self.assertTrue(any('preserved probe/EXT' in x for x in r['errors']))
    def test_literal_named_to_NC_ledger_cannot_allow_wildcard_or_wrong_ball(self):
        m=copy.deepcopy(self.applied);m['home_deallocation_pin_rename_ledger'][0]['new_native_net']='unconnected-*'
        r=verify_obsolete_home_native(self.stage/'inputs/netlist.xml',self.stage/'candidate/netlist.xml',m);self.assertFalse(r['ok'])
    def test_before_after_ERC_retains_real_warnings_and_no_new_violations(self):
        a=erc_summary(self.stage/'erc-before.json');b=erc_summary(self.stage/'erc-after-r02.json')
        self.assertEqual((0,80,[]),(a['errors'],a['warnings'],a['ignored_checks']));self.assertEqual((0,80,[]),(b['errors'],b['warnings'],b['ignored_checks']));self.assertFalse(b['clean'])


class ReservedHealthReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage=REPORT/'reserved-health-reconciliation-r01';src=cls.stage/'inputs'
        cls.root=parse((src/'motherboard.kicad_sch').read_text(encoding='utf8'))
        cls.core=parse((src/'fpga_core.kicad_sch').read_text(encoding='utf8'))
        cls.before=ET.parse(src/'netlist.xml');cls.meta=json.loads((src/'fpga-allocation-parent.json').read_text())
        cls.evidence=json.loads((cls.stage/'copper-zero-evidence.json').read_text())
        cls.after=ET.parse(cls.stage/'candidate/netlist.xml');cls.applied=json.loads((cls.stage/'candidate-metadata.json').read_text())
    def apply(self,root=None,core=None,meta=None,before=None,evidence=None):
        return apply_reserved_health_reconciliation(root or self.root,core or self.core,meta or self.meta,before or self.before,evidence or self.evidence)
    def test_only_nine_NCs_and_one_real_rail_bridge_preserve_inputs(self):
        nr,nc,nm=self.apply()
        self.assertEqual((151,32),(self.meta['assigned_user_pins'],self.meta['free_user_gpio']))
        self.assertEqual((142,41,66,21),(nm['assigned_user_pins'],nm['free_user_gpio'],nm['promoted_nc_pin_count'],nm['deallocated_user_pin_count']))
        self.assertEqual(9,len(children(nc,'no_connect'))-len(children(self.core,'no_connect')))
        self.assertEqual(9,len(children(fpga_sheet(self.root),'pin'))-len(children(fpga_sheet(nr),'pin')))
        self.assertEqual(6,len(nm['XS_future_resource_reservations']));self.assertFalse(nm['XS_interface_implemented'])
        self.assertEqual('/FPGA_CRESET_N',nm['RAILS_OK_FPGA_actual_source']);self.assertEqual('U2006.4',nm['RAILS_OK_FPGA_source_pin'])
    def test_complete_native_inventory_and_all_unrelated_functions_preserved(self):
        r=verify_reserved_health_native(self.stage/'inputs/netlist.xml',self.stage/'candidate/netlist.xml',self.applied)
        self.assertTrue(r['ok'],r['errors']);self.assertEqual((10832,10832),(r['native_pins_before'],r['native_pins_after']))
        after={}
        for net in self.after.findall('./nets/net'):
            for n in net.findall('node'):after[n.attrib['ref'],n.attrib['pin']]=net.attrib['name']
        self.assertEqual(after['U2006','4'],after['U1001','P4'])
    def test_single_pad_ghost_evidence_is_exact_zero_copper_on_CAD23(self):
        evidence=audit_reserved_health_copper(self.evidence['board_path'])
        self.assertEqual(evidence,self.evidence);self.assertEqual(10,len(evidence['rows']))
        self.assertTrue(all((r['segment'],r['via'],r['zone'])==(0,0,0) for r in evidence['rows']))
        self.assertEqual('54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5',evidence['board_sha256'])
    def test_extra_actual_endpoint_cannot_be_removed_as_a_ghost(self):
        t=copy.deepcopy(self.before);net=next(n for n in t.findall('./nets/net') if n.attrib['name']=='/fpga_core/XS_MISO')
        ET.SubElement(net,'node',{'ref':'REAL_MODULE_INPUT','pin':'1'})
        with self.assertRaisesRegex(ValueError,'exactly one FPGA pad'):self.apply(before=t)
    def test_actual_rail_driver_cannot_be_a_constant_wrong_part_or_wrong_voltage(self):
        t=copy.deepcopy(self.before);c=next(c for c in t.findall('./components/comp') if c.attrib['ref']=='U2006')
        c.find("./fields/field[@name='MPN']").text='FAKE_HEALTH'
        with self.assertRaisesRegex(ValueError,'actual part differs'):self.apply(before=t)
        t=copy.deepcopy(self.before);net=next(n for n in t.findall('./nets/net') if n.attrib['name']=='/IO_3V3');net.remove(next(n for n in net.findall('node') if n.attrib['ref']=='U2006'))
        with self.assertRaisesRegex(ValueError,'qualified3.3V'):self.apply(before=t)
    def test_root_or_core_port_mismatch_rejected(self):
        for which in ['core','root']:
            r,c=copy.deepcopy(self.root),copy.deepcopy(self.core)
            if which=='core':next(l for l in children(c,'hierarchical_label') if value(l[1])=='HEALTH_SR_CLK')[1]=q('UNREVIEWED_HEALTH')
            else:next(p for p in children(fpga_sheet(r),'pin') if value(p[1])=='HEALTH_SR_CLK')[1]=q('UNREVIEWED_HEALTH')
            with self.assertRaisesRegex(ValueError,'exact bounded stubs'):self.apply(root=r,core=c)
    def test_source_partially_renamed_prior_NC_or_repeated_adoption_rejected(self):
        c=copy.deepcopy(self.core);xy=actual_pin_coordinates(c)['T3']['coordinate'];c.append(['no_connect',['at',str(xy[0]),str(xy[1])],['uuid',q('1b15c8aa-7815-4f15-9ad4-5d921013c69c')]])
        with self.assertRaisesRegex(ValueError,'already NC'):self.apply(core=c)
        for key,val in [('reserved_health_reconciliation_applied',True),('assigned_user_pins',150),('manufacturing_ready',True)]:
            m=copy.deepcopy(self.meta);m[key]=val
            with self.assertRaises(ValueError):self.apply(meta=m)
    def test_copper_proof_cannot_hide_one_route_or_modified_board(self):
        e=copy.deepcopy(self.evidence);e['rows'][2]['via']=1
        with self.assertRaisesRegex(ValueError,'stale, incomplete or modified'):self.apply(evidence=e)
        e=copy.deepcopy(self.evidence);e['board_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'stale, incomplete or modified'):self.apply(evidence=e)
    def test_literal_ledger_never_admits_a_wildcard_or_missing_row(self):
        for change in ['wildcard','missing']:
            m=copy.deepcopy(self.applied)
            if change=='wildcard':m['reserved_health_pin_rename_ledger'][0]['new_native_net']='unconnected-*'
            else:m['reserved_health_pin_rename_ledger'].pop()
            r=verify_reserved_health_native(self.stage/'inputs/netlist.xml',self.stage/'candidate/netlist.xml',m)
            self.assertFalse(r['ok'])
    def test_native_detector_rejects_lost_GPIO_and_fake_rail(self):
        for signal in ['PROBE_FPGA','FPGA_CRESET_N']:
            t=copy.deepcopy(self.after);net=next(n for n in t.findall('./nets/net') if n.attrib['name'].endswith('/'+signal));net.attrib['name']='/FAKE_'+signal
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'bad.xml';t.write(p,encoding='utf-8')
                self.assertFalse(verify_reserved_health_native(self.stage/'inputs/netlist.xml',p,self.applied)['ok'])
    def test_required_rail_cannot_be_reconfigured_as_FPGA_output(self):
        m=copy.deepcopy(self.meta);m['desired_directions']['RAILS_OK_FPGA']='output'
        with self.assertRaisesRegex(ValueError,'direction changed'):self.apply(meta=m)
    def test_a_branched_root_wire_cannot_be_erased(self):
        r=copy.deepcopy(self.root);pin=next(p for p in children(fpga_sheet(r),'pin') if value(p[1])=='XS_MOSI');xy=point(child(pin,'at'))
        w=next(w for w in children(r,'wire') if xy in [point(p) for p in children(child(w,'pts'),'xy')]);pts=[point(p) for p in children(child(w,'pts'),'xy')];end=next(p for p in pts if p!=xy)
        r.append(['wire',['pts',['xy',str(end[0]),str(end[1])],['xy',str(end[0]+5.08),str(end[1])]],['stroke',['width','0'],['type','default']],['uuid',q('1b15c8aa-7815-4f15-9ad4-5d921013c69d')]])
        with self.assertRaisesRegex(ValueError,'root stub is branched'):self.apply(root=r)
    def test_optional_reserved_port_cannot_silently_be_claimed_implemented(self):
        for key,val in [('XS_interface_implemented',True),('target_health_runtime_verified',True),('free_user_gpio',40)]:
            m=copy.deepcopy(self.applied);m[key]=val
            self.assertFalse(verify_reserved_health_native(self.stage/'inputs/netlist.xml',self.stage/'candidate/netlist.xml',m)['ok'])
    def test_three_rack_acquisition_and_six_reserved_resources_are_distinguished(self):
        self.assertEqual((3,6,1),tuple(sum(r[5]==kind for r in RESERVED_HEALTH_PINS) for kind in ['obsolete_rack_acquisition','future_reserved_no_base_interface','required_existing_qualified_rail_bridge']))
        self.assertFalse({'G12','G15','G16','M4','M6'}&{p[1] for p in RESERVED_HEALTH_PINS})


if __name__=='__main__':unittest.main()
