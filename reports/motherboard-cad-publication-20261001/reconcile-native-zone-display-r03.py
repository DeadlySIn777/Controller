"""Correct only WIP display labels/counts from actual native zone types and fill."""
from pathlib import Path
import json,sys,copy,collections
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
root=Path('hardware/board_review');revision=root/'revisions/20261001-26'
board=revision/'motherboard-native-candidate.kicad_pcb';b=pcbnew.LoadBoard(str(board))
assert sha(board)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
zones=list(b.Zones());rows=[dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),layer=b.GetLayerName(z.GetLayer()),rule_area=z.GetIsRuleArea(),filled_flag=z.IsFilled(),actual_filled_area_mm2=z.GetFilledArea()/1e12)for z in zones]
rule=sum(r['rule_area']for r in rows);positive=sum(not r['rule_area']and r['actual_filled_area_mm2']>0 for r in rows)
out=Path('reports/motherboard-cad-publication-20261001/ROOT101-native-zone-display-r03');assert not out.exists();out.mkdir()
changed=[]
for i,p in enumerate([revision/'board-view.json',root/'board-view.json']):
 d=json.loads(p.read_text());assert d['current_revision']=='20261001-26';before=copy.deepcopy(d)
 write(out/('before-'+str(i)+'.json'),before)
 v=d['boards'][0];assert len(v['copper_zones'])==len(rows)
 v['summary']=f'2688 actual source footprints, 11635 tracks/vias, {len(rows)-rule} copper-zone definitions and {rule} rule areas. 3528 copper joins remain.'
 v['stats']['copper_zones']=len(rows)-rule;v['stats']['filled_copper_zones']=positive;v['stats']['native_rule_areas']=rule;v['stats']['total_native_zones_and_rule_areas']=len(rows)
 for r,s in zip(rows,v['copper_zones']):
  assert r['net']==s['net'] and r['layer']==s['layer']
  s['rule_area']=r['rule_area'];s['actual_positive_filled_copper']=not r['rule_area']and r['actual_filled_area_mm2']>0
 # All circuit geometry, parts, copper, net data and prior evidence remain exact.
 for key in ['components','tracks','native_edge_cuts','source_hashes','evidence','board_file']:assert v[key]==before['boards'][0][key]
 oldsha=sha(p);write(p,d);changed.append(dict(path=str(p),before_sha256=oldsha,after_sha256=sha(p)))
write(out/'receipt.json',dict(passed=True,board_sha256=sha(board),native_copper_zone_definitions=len(rows)-rule,native_rule_areas=rule,positive_filled_copper_zone_definitions=positive,rows=rows,changed_files=changed,only_display_metadata_changed=True,manufacturing_ready=False))
print(dict(copper_zone_definitions=len(rows)-rule,rule_areas=rule,positive_filled_zones=positive))
