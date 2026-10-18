import sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_zone_motherboard_returns import LEGACY_ZONES
before=pcbnew.LoadBoard(str(Path.cwd()/'reports/motherboard-return-zoning-20261001/isolation-corrections-r03/motherboard-functional-isolation-corrected-candidate.kicad_pcb'))
after=pcbnew.LoadBoard(str(Path.cwd()/'reports/motherboard-return-zoning-20261001/per-side-reference-r03/motherboard-return-zones-candidate.kicad_pcb'))
nets={net for net,layer in LEGACY_ZONES.values()}
a=native_pad_clusters(before,nets);b=native_pad_clusters(after,nets)
pads={p.m_Uuid.AsString():dict(reference=f.GetReference(),pin=p.GetNumber(),net=p.GetNetname(),position_mm=[pcbnew.ToMM(x)for x in p.GetPosition()]) for f in after.GetFootprints()for p in f.Pads()if p.GetNumber()}
lost=[dict(old=old,old_pads=[pads[x]for x in old['pad_UUIDs']],new_fragments=[dict(new=new,pads=[pads[x]for x in new['pad_UUIDs']])for new in b if old['net']==new['net']and set(old['pad_UUIDs'])&set(new['pad_UUIDs'])])for old in a if not any(old['net']==new['net']and set(old['pad_UUIDs'])<=set(new['pad_UUIDs'])for new in b)]
d=json.load(open('reports/motherboard-return-zoning-20261001/per-side-reference-r03/drc.json'))
bad={x['items'][0]['uuid']for x in d['violations']if x['type']=='isolated_copper'}
zones=[dict(uuid=z.m_Uuid.AsString(),name=z.GetZoneName(),net=z.GetNetname(),layer=after.GetLayerName(z.GetLayer()),mode=z.GetIslandRemovalMode(),outline_area_mm2=z.Outline().Area()/1e12,fill_area_mm2=z.GetFilledPolysList(z.GetLayer()).Area()/1e12,filled_polygons=z.GetFilledPolysList(z.GetLayer()).OutlineCount())for z in after.Zones()if z.m_Uuid.AsString()in bad]
Path('reports/motherboard-return-zoning-20261001/per-side-reference-r03/actual-failure-analysis.json').write_text(json.dumps(dict(lost_clusters=lost,isolated_zones=zones,mode_constants=dict(always=pcbnew.ISLAND_REMOVAL_MODE_ALWAYS,never=pcbnew.ISLAND_REMOVAL_MODE_NEVER)),indent=2))
print(json.dumps(dict(lost_count=len(lost),lost_pad_counts=[(x['old']['net'],len(x['old_pads']),len(x['new_fragments']))for x in lost],isolated_zone_count=len(zones),modes=collections.Counter(x['mode']for x in zones),fill_area_sum=sum(x['fill_area_mm2']for x in zones)),indent=2))
