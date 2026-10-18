"""Distinct explicitly bound refill producer. Source only until separately authorized.

This preserves the existing uncapped pad partition algorithm. Project/class/global
state checks are mandatory. A non-null project or matching class state alone does
not establish custom-rule engine equivalence; that remains an explicit open gate.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

CLASS_FIELDS = {'clearance': 'GetClearance', 'track_width': 'GetTrackWidth',
                'via_diameter': 'GetViaDiameter', 'via_drill': 'GetViaDrill'}
GLOBAL_FIELDS = {'min_clearance': 'm_MinClearance', 'min_track_width': 'm_TrackMinWidth',
                 'min_via_annular_width': 'm_ViasMinAnnularWidth', 'min_via_diameter': 'm_ViasMinSize',
                 'min_through_hole_diameter': 'm_MinThroughDrill', 'min_copper_edge_clearance': 'm_CopperEdgeClearance',
                 'min_hole_clearance': 'm_HoleClearance', 'min_hole_to_hole': 'm_HoleToHoleMin',
                 'min_microvia_diameter': 'm_MicroViasMinSize', 'min_microvia_drill': 'm_MicroViasMinDrill',
                 'min_silk_clearance': 'm_SilkClearance', 'min_text_height': 'm_MinSilkTextHeight',
                 'min_text_thickness': 'm_MinSilkTextThickness', 'max_error': 'm_MaxError'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_hashes(directory):
    directory = Path(directory).resolve()
    return {str(path.relative_to(directory)): sha(path.read_bytes())
            for path in sorted(directory.rglob('*')) if path.is_file()}


def netclass_state(netclass):
    return {'name': str(netclass.GetName()),
            **{field: int(getattr(netclass, method)()) for field, method in CLASS_FIELDS.items()}}


def effective_state(board, project_json):
    settings = board.GetDesignSettings()
    classes = {str(name): netclass_state(value) for name, value in board.GetAllNetClasses().items()}
    definitions = project_json['net_settings']['classes']
    require(set(classes) == {item['name'] for item in definitions}, 'native class inventory differs from frozen project')
    for item in definitions:
        for field in CLASS_FIELDS:
            if field in item:
                require(classes[item['name']][field] == round(item[field] * 1000000),
                        'native project class value differs: ' + item['name'] + '/' + field)
    source_globals = project_json['board']['design_settings']['rules']
    globals_actual = {field: int(getattr(settings, native)) for field, native in GLOBAL_FIELDS.items()}
    for field, actual in globals_actual.items():
        if field in source_globals:
            require(actual == round(source_globals[field] * 1000000), 'native global rule value differs: ' + field)
    require(int(settings.m_MinResolvedSpokes) == source_globals['min_resolved_spokes'], 'resolved spoke setting differs')
    effective = {}
    for code, net in board.GetNetsByNetcode().items():
        if code > 0:
            name = str(net.GetNetname())
            resolved = netclass_state(net.GetNetClassSlow())
            require(resolved == netclass_state(settings.m_NetSettings.GetEffectiveNetClass(name)),
                    'board and native project effective classes disagree: ' + name)
            effective[name] = resolved
    return {'classes': classes, 'global_dimensions_nm': globals_actual,
            'min_resolved_spokes': int(settings.m_MinResolvedSpokes), 'effective_classes_by_net': effective}


def partitions(board):
    """Exact old-tool pad names/traversal/count semantics; every net is uncapped."""
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    pads_by_net, pad_name = collections.defaultdict(list), {}
    for footprint in board.GetFootprints():
        seen_num = collections.Counter()
        for pad in footprint.Pads():
            number = str(pad.GetNumber())
            pad_name[pad.m_Uuid.AsString()] = f'{footprint.GetReference()}.{number}#{seen_num[number]}'
            seen_num[number] += 1
            if pad.GetNetCode() > 0:
                pads_by_net[pad.GetNetCode()].append(pad)
    names = {code: str(net.GetNetname()) for code, net in board.GetNetsByNetcode().items()}
    nets, missing = {}, 0
    for code, pads in pads_by_net.items():
        if len(pads) < 2:
            continue
        seen, groups = set(), []
        for pad in pads:
            uid = pad.m_Uuid.AsString()
            if uid in seen:
                continue
            seen.add(uid)
            group, queue = [pad_name[uid]], [pad]
            while queue:
                current = queue.pop()
                for other in conn.GetConnectedItems(current):
                    if other.GetClass() != 'PAD' or other.GetNetCode() != code:
                        continue
                    other_uid = other.m_Uuid.AsString()
                    if other_uid not in seen:
                        seen.add(other_uid)
                        group.append(pad_name[other_uid])
                        queue.append(other)
            groups.append(sorted(group))
        nets[names[code]] = sorted(groups)
        missing += len(groups) - 1
    return {'api_unconnected_count': int(conn.GetUnconnectedCount(False)), 'pad_island_joins': missing,
            'tracks': sum(1 for item in board.GetTracks() if item.GetClass() != 'PCB_VIA'),
            'vias': sum(1 for item in board.GetTracks() if item.GetClass() == 'PCB_VIA'), 'nets': nets}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--refill', action='store_true', required=True)
    args = parser.parse_args()
    board_path = args.board.resolve()
    project_path = board_path.with_suffix('.kicad_pro')
    manifest_raw = args.manifest.read_bytes()
    require(sha(manifest_raw) == args.manifest_sha256, 'immutable run manifest changed')
    inputs = json.loads(manifest_raw)
    require(file_hashes(board_path.parent) == inputs['clone_files'], 'project clone identity changed before native load')
    require(sha(board_path.read_bytes()) == inputs['source_board_sha256'], 'board clone differs from source')
    project_json = json.loads(project_path.read_bytes())
    import pcbnew
    manager = pcbnew.GetSettingsManager()
    require(manager is not None and manager.LoadProject(str(project_path), False), 'explicit native LoadProject failed')
    project = manager.GetProject(str(project_path))
    require(project is not None, 'explicit native project handle unavailable')
    board = None
    try:
        # KiCad10.0.4 LoadBoard itself binds sibling project and initializes sibling
        # custom rules. Same-project rebind must be independently reviewed before use.
        board = pcbnew.LoadBoard(str(board_path))
        require(board is not None and board.GetProject() is not None, 'automatic project binding unavailable')
        before = effective_state(board, project_json)
        board.SetProject(project)
        require(board.GetProject() is not None and board.GetProject().this == project.this, 'explicit project handle differs')
        after = effective_state(board, project_json)
        require(before == after, 'explicit same-project rebind changed effective settings')
        # This prospective producer is deliberately source-only. Even if authorized,
        # its result labels engine equivalence open; native classes cannot prove it.
        filled = pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        require(filled is True, 'native zone refill did not confirm success')
        result = {'board': str(board_path), 'sha256': inputs['source_board_sha256'], 'refilled': True,
                  **partitions(board), 'project_settings_binding': {
                      'settings_manager_load_project': True, 'explicit_board_set_project': True,
                      'effective_state_before': before, 'effective_state_after': after,
                      'state_unchanged_by_explicit_rebind': True,
                      'custom_rule_engine_full_equivalence': 'NOT_VERIFIED',
                      'old_loader_auto_initialization': 'Official10.0.4 source confirmed; actual rule sentinels still required'},
                  'project_sha256': sha(project_path.read_bytes()), 'manifest_sha256': args.manifest_sha256,
                  'native_version': str(pcbnew.GetBuildVersion()), 'saved_board_or_project': False,
                  'evidence_class': 'Explicit project/class/global bound native refill and uncapped partitions; full custom-rule equivalence open'}
        require(file_hashes(board_path.parent) == inputs['clone_files'], 'project clone changed during refill')
        require(sha(args.manifest.read_bytes()) == args.manifest_sha256, 'run manifest changed during refill')
        require(not args.out.exists(), 'partition output must be fresh')
        args.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
        print(json.dumps({key: result[key] for key in ('sha256', 'refilled', 'api_unconnected_count', 'pad_island_joins')}))
    finally:
        if board is not None:
            board.ClearProject()
        manager.UnloadProject(project, False)
        require(file_hashes(board_path.parent) == inputs['clone_files'], 'project clone changed during cleanup')


if __name__ == '__main__':
    main()
