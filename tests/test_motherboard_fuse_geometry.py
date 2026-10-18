import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_apply_fuse_geometry_upgrade import apply_fuse_geometry,OLD,NEW,REFS,parse,children,child,value
def inputs():
 prior=ROOT/'reports/motherboard-fuse-geometry-20261001/prior-source-r04b'
 return parse((prior/'motherboard_power_entry.kicad_sch').read_text()),json.loads((prior/'design.json').read_text())
def test_exact_three_MPN_count_pin_net_preservation():
 t,m=inputs();before=copy.deepcopy(m);tt,mm,r=apply_fuse_geometry(t,m)
 assert m==before and len(mm['components'])==len(m['components'])
 for ref,a in m['components'].items():
  b=mm['components'][ref];c=copy.deepcopy(b)
  if ref in REFS:assert b['footprint']==NEW;c['footprint']=OLD
  assert c==a
 assert r['mounting_pitch_metric_mm']==9.74 and r['finished_hole_nominal_mm']==1.70
 assert r['mounting_pitch_imperial_mm']==pytest.approx(9.7282)
def test_all_four_exact_manufacturer_hole_centres():
 t=parse((ROOT/'hardware/motherboard_fuse_geometry/CNC_MB_Fuse.pretty/Keystone_3568_M55.kicad_mod').read_text());pads=children(t,'pad')
 assert [(value(p[1]),float(child(p,'at')[1]),float(child(p,'at')[2]),float(child(p,'drill')[1]))for p in pads]==[('1',0,0,1.7),('1',0,3.4,1.7),('2',9.74,0,1.7),('2',9.74,3.4,1.7)]
 assert all([float(x)for x in child(p,'size')[1:3]]==[2.78,2.78]for p in pads)
def test_no_claimed_stock_3D_geometry():
 t=parse((ROOT/'hardware/motherboard_fuse_geometry/CNC_MB_Fuse.pretty/Keystone_3568_M55.kicad_mod').read_text());assert not children(t,'model')
@pytest.mark.parametrize('field,bad',[('mpn','3568-10'),('footprint',NEW)])
def test_changed_native_candidate_is_rejected(field,bad):
 t,m=inputs();m['components']['F11002'][field]=bad
 with pytest.raises(AssertionError):apply_fuse_geometry(t,m)
def test_missing_holder_not_silently_partial():
 t,m=inputs();del m['components']['F11003']
 with pytest.raises(AssertionError):apply_fuse_geometry(t,m)
def test_wrong_schematic_footprint_rejected():
 t,m=inputs()
 for s in children(t,'symbol'):
  ps={value(p[1]):p for p in children(s,'property')}
  if 'Reference'in ps and value(ps['Reference'][2])=='F11001':ps['Footprint'][2]='"Fuse:other"';break
 with pytest.raises(AssertionError):apply_fuse_geometry(t,m)
