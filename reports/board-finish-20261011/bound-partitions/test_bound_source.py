"""Host/model controls only, with no pcbnew import or native operation."""
import copy
from types import SimpleNamespace
import unittest

import native_bound_partitions as producer


class FakeClass:
    def __init__(self, clearance=150000, name='Default'):
        self.name, self.clearance = name, clearance
    def GetName(self): return self.name
    def GetClearance(self): return self.clearance
    def GetTrackWidth(self): return 200000
    def GetViaDiameter(self): return 600000
    def GetViaDrill(self): return 300000


class StateControls(unittest.TestCase):
    def setUp(self):
        self.cls = FakeClass()
        self.rules = {field: 0.1 for field in producer.GLOBAL_FIELDS}
        self.rules['min_resolved_spokes'] = 2
        self.project = {'net_settings': {'classes': [{'name': 'Default', 'clearance': .15,
                         'track_width': .2, 'via_diameter': .6, 'via_drill': .3}]},
                        'board': {'design_settings': {'rules': self.rules}}}
        self.settings = SimpleNamespace(**{native: 100000 for native in producer.GLOBAL_FIELDS.values()},
                                        m_MinResolvedSpokes=2,
                                        m_NetSettings=SimpleNamespace(GetEffectiveNetClass=lambda name: self.cls))
        net = SimpleNamespace(GetNetname=lambda: '/ordinary', GetNetClassSlow=lambda: self.cls)
        self.board = SimpleNamespace(GetDesignSettings=lambda: self.settings,
                                     GetAllNetClasses=lambda: {'Default': self.cls},
                                     GetNetsByNetcode=lambda: {1: net})

    def test_exact_native_class_global_effective_state_passes(self):
        state = producer.effective_state(self.board, self.project)
        self.assertEqual(state['effective_classes_by_net']['/ordinary']['clearance'], 150000)

    def test_fallback_class_clearance_refused(self):
        self.cls.clearance = 200000
        with self.assertRaisesRegex(ValueError, 'native project class value differs'):
            producer.effective_state(self.board, self.project)

    def test_global_settings_fallback_refused(self):
        self.settings.m_CopperEdgeClearance = 500000
        with self.assertRaisesRegex(ValueError, 'native global rule value differs'):
            producer.effective_state(self.board, self.project)

    def test_native_board_project_effective_class_disagreement_refused(self):
        self.settings.m_NetSettings.GetEffectiveNetClass = lambda name: FakeClass(name='Wrong')
        with self.assertRaisesRegex(ValueError, 'effective classes disagree'):
            producer.effective_state(self.board, self.project)


class Pad:
    def __init__(self, uid, number, code=1):
        self.m_Uuid = SimpleNamespace(AsString=lambda: uid)
        self.number, self.code = number, code
    def GetNumber(self): return self.number
    def GetNetCode(self): return self.code
    def GetClass(self): return 'PAD'


class PartitionControls(unittest.TestCase):
    def fake_board(self, connected):
        pads = [Pad('a', '1'), Pad('b', '1'), Pad('c', '2')]
        net = SimpleNamespace(GetNetname=lambda: '/ordinary')
        footprint = SimpleNamespace(GetReference=lambda: 'J1', Pads=lambda: pads)
        conn = SimpleNamespace(GetConnectedItems=lambda pad: connected.get(pad.m_Uuid.AsString(), []),
                               GetUnconnectedCount=lambda exclude: 7)
        board = SimpleNamespace(BuildConnectivity=lambda: None, GetConnectivity=lambda: conn,
                                 GetFootprints=lambda: [footprint], GetNetsByNetcode=lambda: {1: net},
                                 GetTracks=lambda: [SimpleNamespace(GetClass=lambda: 'PCB_TRACK'),
                                                    SimpleNamespace(GetClass=lambda: 'PCB_VIA')])
        return board, pads

    def test_uncapped_split_and_repeated_pad_numbers_preserved(self):
        board, pads = self.fake_board({})
        result = producer.partitions(board)
        self.assertEqual(result['nets']['/ordinary'], [['J1.1#0'], ['J1.1#1'], ['J1.2#0']])
        self.assertEqual(result['pad_island_joins'], 2)
        self.assertEqual(result['api_unconnected_count'], 7)
        self.assertEqual((result['tracks'], result['vias']), (1, 1))

    def test_same_old_pad_id_traversal_groups_connected_pads(self):
        board, pads = self.fake_board({})
        board.GetConnectivity = lambda: SimpleNamespace(
            GetConnectedItems=lambda pad: pads[:2] if pad in pads[:2] else [],
            GetUnconnectedCount=lambda exclude: 7)
        result = producer.partitions(board)
        self.assertEqual(result['nets']['/ordinary'], [['J1.1#0', 'J1.1#1'], ['J1.2#0']])
        self.assertEqual(result['pad_island_joins'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
