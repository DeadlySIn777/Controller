"""Relative native power-geometry screen; never a rail ampacity/IR-drop proof.

The integrated U2002 is TPS62902RPJR with a 2 A source allocation. Preserve
the actual source neck, all 22 receiving feeds, every pre-existing sub-1 mm
feature and each separate surviving 1 mm backbone component. No CORE1V2 cut.
"""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_check_return_corridors import circle,covered
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_route_logic_return import identity,mm
ROOT=Path(__file__).resolve().parents[2]
FEEDS=ROOT/'reports/motherboard-power-entry-20261001/io3-positive-proof-r11/receipt.json'
SOURCE=ROOT/'hardware/motherboard/design.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def duplicate(poly):
 p=pcbnew.SHAPE_POLY_SET();p.Append(poly);return p

def intersection(a,b):
 p=duplicate(a);p.BooleanIntersection(b);p.Simplify();return p

def subtract(a,b):
 p=duplicate(a);p.BooleanSubtract(b);p.Simplify();return p

def box(x0,y0,x1,y1):
 p=pcbnew.SHAPE_POLY_SET();p.NewOutline()
 for x,y in((x0,y0),(x1,y0),(x1,y1),(x0,y1)):p.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
 return p

def symmetric_equal(a,b):
 return not subtract(a,b).OutlineCount()and not subtract(b,a).OutlineCount()

def backbone(before,after):
 if not before.OutlineCount()or not after.OutlineCount():raise ValueError('Empty IO3 native fill cannot supply a backbone proof')
 # 502um reserves1um native offset approximation plus1um boundary comparison;500um remains.
 old=duplicate(before);old.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
 new=duplicate(after);new.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
 if not old.OutlineCount()or not new.OutlineCount():raise ValueError('Empty erosion cannot receive power-capacity credit')
 opened=duplicate(old);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
 opened.BooleanIntersection(before)
 narrow=subtract(before,opened);removed=subtract(before,after)
 # Native contour/offset operations already carry a1um maximum error.
 # Bound only this relative boundary comparison to the same1um; no area
 # filters. The502um erosion separately reserves both1um error sources.
 # Source contacts, reference coverage and DRC retain their existing rules.
 assert pcbnew.FromMM(.000001)==1
 precision_after=duplicate(after)
 precision_after.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 escaped=subtract(narrow,precision_after)
 if escaped.OutlineCount():raise ValueError('New routing cuts a pre-existing sub-1mm power feature beyond1um declared native contour comparison precision')
 new_pieces=list(split_polygons(new));rows=[]
 for index,piece in enumerate(split_polygons(old)):
  surviving=intersection(piece,new)
  if not surviving.OutlineCount():raise ValueError('An entire prior power-backbone component was lost')
  owners=[i for i,p in enumerate(new_pieces)if covered(surviving,p)]
  if len(owners)!=1:raise ValueError('A prior power backbone is split or narrowed below the unchanged minimum')
  rows.append(dict(before_component=index,after_component=owners[0],all_surviving_prior_core_in_one_after_core=True))
 return dict(passed=True,minimum_screened_core_width_mm=1.,native_erosion_radius_mm=.502,native_maximum_offset_error_mm=.001,
   prior_backbone_components=len(rows),after_backbone_components=len(new_pieces),each_component=rows,
   preexisting_sub1mm_features_preserved_within_native_precision=True,maximum_native_boundary_comparison_uncertainty_um=1,no_area_based_exemptions=True,removed_copper_mm2=removed.Area()/1e12,
   added_copper_mm2=subtract(after,before).Area()/1e12,
   exact_removed_native_polygons=removed.Format(False),exact_added_native_polygons=subtract(after,before).Format(False),
   ampacity_IR_drop_or_thermal_qualification=False)

def review(before_board,after_board):
 model=json.loads(SOURCE.read_text());u=model['components']['U2002']
 assert u['mpn']=='TPS62902RPJR'and u['io3_source_current_allocation_a']==2
 before_board.BuildConnectivity();after_board.BuildConnectivity()
 bf=collect_native_reference_fills(before_board,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu])
 af=collect_native_reference_fills(after_board,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu])
 b=bf['/IO_3V3',pcbnew.In2_Cu];a=af['/IO_3V3',pcbnew.In2_Cu]
 if not symmetric_equal(bf['/CORE_1V2',pcbnew.In3_Cu],af['/CORE_1V2',pcbnew.In3_Cu]):raise ValueError('CORE1V2 filled power copper changed')
 geometry=backbone(b,a)
 bp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in before_board.GetPads()}
 ap={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in after_board.GetPads()}
 before_cu={t.m_Uuid.AsString():t for t in before_board.GetTracks()};after_cu={t.m_Uuid.AsString():t for t in after_board.GetTracks()}
 rails={'/IO_3V3','/CORE_1V2',bp['U2002','3'].GetNetname()}
 if any(u not in after_cu or identity(t)!=identity(after_cu[u])for u,t in before_cu.items()if t.GetNetname()in rails):raise ValueError('Old exact rail traces/barrels changed')
 regions=[]
 # Explicitly protect source-side fine features, all original source-array
 # vias and the actual 4mm transition between original and extended IO3 fill.
 points=[mm(bp[r,p].GetPosition())for r,p in(('U2002','3'),('L2002','2'),('R18001','1'),('R18001','2'),('C2005','1'),('C2010','1'))]
 regions.append(('regulator and damper neck',box(min(x for x,y in points)-3,min(y for x,y in points)-3,max(x for x,y in points)+3,max(y for x,y in points)+3)))
 regions.append(('nine source vias',box(59.5,22.2,63.3,26.)))
 regions.append(('four millimetre source seam',box(57.6,96.,63.6,104.)))
 frozen_feeds=json.loads(FEEDS.read_text());assert len(frozen_feeds['actual_receiving_via_checks'])==22
 co=after_board.GetConnectivity();source=ap['R18001','2'];peers={x.m_Uuid.AsString()for x in co.GetConnectedItems(source)}|{source.m_Uuid.AsString()}
 endpoints=[];contacts=[]
 for row in frozen_feeds['actual_source_endpoint_checks']:
  pad=ap[row['reference'],row['pin']];assert pad.GetNetname()=='/IO_3V3'and pad.m_Uuid.AsString()in peers
  endpoints.append(dict(reference=row['reference'],pin=row['pin'],actual_source_connected=True))
 assert len(endpoints)==44
 for row in frozen_feeds['actual_receiving_via_checks']:
  uid=row['via_uuid'];old=before_cu[uid];via=after_cu[uid]
  assert old.Type()==via.Type()==pcbnew.PCB_VIA_T and identity(old)==identity(via)
  assert via.GetNetname()=='/IO_3V3'and uid in peers and physical_reference_contact(via,pcbnew.In2_Cu,co)
  point=tuple(via.GetPosition());region=circle(point,pcbnew.FromMM(1.))
  regions.append((row['reference']+' receiving via/corridor',region))
  assert covered(circle(point,via.GetWidth(pcbnew.In2_Cu)//2-pcbnew.FromMM(.01)),a)
  contacts.append(dict(reference=row['reference'],via_uuid=uid,actual_inner_annulus_and_source_path_retained=True))
 for name,region in regions:
  if not symmetric_equal(intersection(b,region),intersection(a,region)):raise ValueError('Actual native IO3 copper changed in protected '+name)
 return dict(passed=True,actual_integrated_source_mpn=u['mpn'],source_allocation_a=2,
  actual_source_input_sha256={str(SOURCE):sha(SOURCE),str(FEEDS):sha(FEEDS),str(Path(__file__)):sha(__file__)},
  CORE1V2_exact_filled_geometry_preserved=True,old_exact_rail_copper_preserved=True,
  backbone=geometry,protected_power_regions=[name for name,region in regions],actual44_receiver_endpoints=endpoints,actual22_receiving_annuli=contacts,
  relative_geometric_preservation_only=True,unresolved_full_load_drop_thermal_budget=True,physical_qualification=False,manufacturing_ready=False)
