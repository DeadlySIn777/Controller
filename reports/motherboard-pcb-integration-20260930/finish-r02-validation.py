"""Close r02 report after correcting KiCad10's name-only pad-net parser.

The native PCB/placement/DRC bytes are preserved. This repairs report generation
only; a previous parser exception occurred after native DRC already completed.
"""
from collections import Counter
import datetime
from pathlib import Path
import sys
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_populate_motherboard_pcb as tool

REPORT=Path(__file__).resolve().parent
OUT=REPORT/'populated-r02'
SOURCE=REPORT/'frozen-source-r02/motherboard'
BASE=OUT/'source-inputs/local-signal-routing-v1-local-signal-routes-candidate.kicad_pcb'
DEST=OUT/'motherboard-populated-candidate.kicad_pcb'


def tuples(v):return tuple(tuples(x) for x in v) if isinstance(v,list) else v


before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(DEST));after.BuildConnectivity()
model=tool.load(SOURCE/'design.json');mapping=tool.load(SOURCE/'assembly-map.json')
native,nodes=tool.native_parts_and_nets(SOURCE/'netlist.xml',model['components'])
ledger=mapping['native_net_renames_allowed']
old_tracks={t.m_Uuid.AsString():tool.identity(t) for t in before.GetTracks()}
old_pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):tool.pad_identity(p) for p in before.GetPads() if tool.copper_pad(p)}
old_fps={f.GetReference():(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),tool.footprint_name(f))
         for f in before.GetFootprints()}
templates={r:[tuples(v) for v in rows] for r,rows in tool.load(OUT/'exact-source-pad-templates.json').items()}
verification=tool.verify_population(after,model,nodes,old_tracks,old_pads,old_fps,ledger,templates)
verification['native_object_retention']=tool.native_retained_objects(BASE,DEST,ledger)
verification['retained_zone_native_definitions_unchanged']=tool.raw_items(BASE,'zone')==tool.raw_items(DEST,'zone')
frozen=REPORT/'frozen-source-r02';snapshots=tool.load(frozen/'snapshot-sha256.json')
verification['source_inputs_unchanged']=all(tool.sha(frozen/n)==h for n,h in snapshots.items())
if not verification['native_object_retention']['ok']:
    verification['errors']+=verification['native_object_retention']['errors'];verification['ok']=False
if not verification['source_inputs_unchanged'] or not verification['retained_zone_native_definitions_unchanged']:
    verification['errors'].append('Frozen input/zone retention failed');verification['ok']=False
exact_footprint_sources={};source_pad_templates_agree=True
for ref,c in model['components'].items():
    if ref in old_fps:continue
    fp,file=tool.load_exact_footprint(c['footprint'],SOURCE,BASE)
    exact_footprint_sources[str(file.relative_to(ROOT)) if file.is_relative_to(ROOT) else str(file)]=tool.sha(file)
    source_pad_templates_agree &= Counter(tool.pad_template(p) for p in fp.Pads())==Counter(templates[ref])
verification['all_added_pad_and_stencil_templates_match_exact_source_library']=source_pad_templates_agree
assert source_pad_templates_agree
clear=tool.watchdog_clear_source_check(model,nodes);assert clear['ok']
for suffix in ('.kicad_pro','.kicad_dru'):
    assert tool.sha(BASE.with_suffix(suffix))==tool.sha(DEST.with_suffix(suffix))
data=tool.load(OUT/'drc.json');violations=data['violations'];placements=tool.load(OUT/'placement-ledger.json')
bypass=[p for p in placements if 'supply_pad_distance_mm' in p]
far=[p for p in bypass if p['supply_pad_distance_mm']>3]
report=dict(schema_version=1,revision='populated-r02',date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_board_sha256=tool.sha(BASE),candidate_board_sha256=tool.sha(DEST),
    source_inputs_sha256=snapshots,frozen_source_files=len(snapshots),exact_footprint_inputs_sha256=exact_footprint_sources,
    population=verification,added_footprints=len(model['components'])-len(old_fps),retained_footprints=len(old_fps),
    layers=after.GetCopperLayerCount(),thickness_mm=pcbnew.ToMM(after.GetDesignSettings().GetBoardThickness()),
    dimensions_mm=[tool.WIDTH,tool.HEIGHT],final_outline=False,
    retained_filled_zones=len(after.Zones()),new_field_or_full_board_planes_added=False,
    native_drc=dict(regular_violations=len(violations),types=dict(Counter(v['type'] for v in violations)),
                    severities=dict(Counter(v['severity'] for v in violations)),ignored_checks=data.get('ignored_checks',[]),
                    capped_unconnected_items=len(data.get('unconnected_items',[])),report='drc.json'),
    uncapped_native_missing_joins=after.GetConnectivity().GetUnconnectedCount(False),
    authentic_native_NC_pads=sum(n.startswith('unconnected-') for n in nodes.values()),
    source_circuit_blocks=dict(Counter(c.get('source_block') for c in model['components'].values())),
    watchdog_clear_source_check=clear,
    bypass_review=dict(actual_named_supply_pad_targets=len(bypass),supply_pad_distance_max_mm=max(p['supply_pad_distance_mm'] for p in bypass),
                       targets_over_3mm=far,copper_routed=False,return_path_and_full_domain_decoupling_qualified=False),
    complete_source_pad_and_stencil_library_check=True,project_rules_unchanged=True,
    purchased_module_footprints_added=False,mechanical_reservations=tool.load(OUT/'mechanical-reservations.json'),
    final_placement=False,routing_complete=False,manufacturing_ready=False,physical_qualification=False,
    tests=dict(native_mutation_tests=17,passed=17,report='../test-errors-r02-second.txt'),
    report_repair='Native geometry unchanged; parser corrected to accept KiCad10 name-only pad-net records after its initial report-generation exception.',
    scope='All 880 actual-source footprints populated and exact 64 former NC FPGA pads reconciled. New regions remain unrouted. Purchased modules/terminals are reservations, not fitted connectors.')
tool.write(OUT/'report.json',report)
assert verification['ok'],verification['errors']
print({k:report[k] for k in ('added_footprints','retained_footprints','native_drc','uncapped_native_missing_joins','bypass_review')})
