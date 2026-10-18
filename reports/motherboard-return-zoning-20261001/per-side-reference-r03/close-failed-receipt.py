import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_build_assembly import parse,children,child,value,dump
from hardware_map_motherboard_domains import sha,write
from hardware_merge_bounded_pcb_delta import zone_definition
from hardware_zone_motherboard_returns import LEGACY_ZONES
folder=Path('reports/motherboard-return-zoning-20261001/per-side-reference-r03')
base=folder/'inputs/motherboard-functional-isolation-corrected-candidate.kicad_pcb'
candidate=folder/'motherboard-return-zones-candidate.kicad_pcb'
before={value(child(z,'uuid')[1]):z for z in children(parse(base.read_text(encoding='utf-8')),'zone')}
after={value(child(z,'uuid')[1]):z for z in children(parse(candidate.read_text(encoding='utf-8')),'zone')}
rows=[]
for uid,(net,layer)in LEGACY_ZONES.items():
    a,b=zone_definition(before[uid]),zone_definition(after[uid])
    rows.append(dict(uuid=uid,net=net,layer=layer,changed_keys=['polygon'],before_raw_definition=a,after_raw_definition=b,
        before_definition_sha256=hashlib.sha256(a.encode()).hexdigest(),after_definition_sha256=hashlib.sha256(b.encode()).hexdigest(),
        electrical_outline_correction_reason='Remove actual foreign field/package/floating-domain projections from inherited logic/power plane; this first candidate is rejected until physical cluster continuity and fill anchors are corrected.'))
write(folder/'old-five-zone-outline-ledger.json',rows)
d=json.load(open(folder/'drc.json'));analysis=json.load(open(folder/'actual-failure-analysis.json'));anchors=json.load(open(folder/'physical-reference-anchors.json'))
b=pcbnew.LoadBoard(str(candidate));b.BuildConnectivity()
write(folder/'receipt.json',dict(passed=False,board_sha256=sha(candidate),source_stage='r24-2688-probe-topology-staged',
    footprint_count=len(b.GetFootprints()),track_via_count=len(b.GetTracks()),zone_objects=len(b.Zones()),uncapped_unconnected=b.GetConnectivity().GetUnconnectedCount(False),
    native_DRC_errors=sum(x.get('severity')=='error'for x in d['violations']),native_DRC_warning_count=sum(x.get('severity')=='warning'for x in d['violations']),native_DRC_ignored=d['ignored_checks'],
    old_source_pad_clusters_preserved=False,lost_old_cluster_count=len(analysis['lost_clusters']),physical_reference_anchor_passed=False,unanchored_reference_piece_count=len(anchors['unanchored_components']),
    status='failed_plane_candidate_preserved_as_exact_engineering_evidence',manufacturing_ready=False,physical_qualification=False))
print('Failed candidate receipt and exact five-zone definition ledger recorded; no board changed.')
