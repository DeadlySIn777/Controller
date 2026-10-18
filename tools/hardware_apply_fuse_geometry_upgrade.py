"""Bounded three-holder source/PCB correction from Keystone primary drawing.

Published metric mounting nominal 9.74 mm is used without claiming tolerance;
the same drawing's .383 inch gives 9.7282 mm, a documented rounding difference.
Manufacturer recommended finished holes 1.70 mm. Exact factory hole/lead
tolerances and assembled insertion remain qualification gates.
"""
from pathlib import Path
import copy,hashlib,json
from hardware_build_assembly import children,child,value,parse,dump,q as qt
ROOT=Path(__file__).resolve().parents[1]
REFS={'F11001','F11002','F11003'}
OLD='Fuse:Fuseholder_Blade_Mini_Keystone_3568'
NEW='CNC_MB_Fuse:Keystone_3568_M55'
PRIMARY=ROOT/'reports/motherboard-power-entry-20261001/distribution-sources-r01/keystone-M55-prod09.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply_fuse_geometry(tree,model):
 t,m=copy.deepcopy(tree),copy.deepcopy(model);seen=[]
 parts=m['components'];items=parts.items()if isinstance(parts,dict)else((c['ref'],c)for c in parts)
 for ref,c in items:
  if ref not in REFS:continue
  assert c['mpn']=='3568'and c['footprint']==OLD,c;c['footprint']=NEW;seen.append(ref)
 assert set(seen)==REFS
 native=[]
 for sym in children(t,'symbol'):
  props={value(p[1]):p for p in children(sym,'property')}
  if value(props.get('Reference',['','',''])[2])not in REFS:continue
  assert value(props['Footprint'][2])==OLD;props['Footprint'][2]=qt(NEW);native.append(value(props['Reference'][2]))
 assert set(native)==REFS
 return t,m,dict(refs=sorted(REFS),old=OLD,new=NEW,part_count_unchanged=True,MPN_pin_net_unchanged=True,primary_sha256=sha(PRIMARY),mounting_pitch_metric_mm=9.74,mounting_pitch_imperial_mm=.383*25.4,pitch_rounding_difference_mm=9.74-.383*25.4,finished_hole_nominal_mm=1.70,transverse_pitch_mm=3.40,manufacturer_dimension_tolerances_supplied=False,physical_mating_qualified=False)
def patch_native_tree(tree):
 t=copy.deepcopy(tree);seen=[]
 for f in children(t,'footprint'):
  ps={value(p[1]):p for p in children(f,'property')};r=value(ps['Reference'][2])
  if r not in REFS:continue
  assert value(f[1])==OLD;f[1]=qt(NEW)
  if 'Footprint'in ps:ps['Footprint'][2]=qt(NEW)
  pads=children(f,'pad');assert len(pads)==4
  for p in pads:
   num=value(p[1]);a=child(p,'at');d=child(p,'drill');assert num in ['1','2']and float(d[1])==1.78
   assert float(a[1])==(0 if num=='1' else 9.92)and float(a[2])in [0,3.4]
   if num=='2':a[1]='9.74'
   d[1]='1.70'
  # Body centre follows the corrected mounting centre; lands/UUIDs/nets stay.
  for k in ['fp_line','fp_text','property']:
   for v in children(f,k):
    if k=='fp_line':
     for tag in ['start','end']:
      a=child(v,tag);a[1]=str(round(float(a[1])-.09,6))
    elif child(v,'at')is not None:
     a=child(v,'at');a[1]=str(round(float(a[1])-.09,6))
  for v in list(children(f,'model')):f.remove(v)
  seen.append(r)
 assert set(seen)==REFS;return t
def make_library(out):
 source=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/Fuse.pretty/Fuseholder_Blade_Mini_Keystone_3568.kicad_mod');t=parse(source.read_text());t[1]=qt('Keystone_3568_M55');child(t,'descr')[1]=qt('Keystone 3568, official M55 page36 mounting nominal9.74x3.40mm; four1.70mm finished holes; metric/imperial rounding documented. Body16.00x6.73x7.37mm. https://www.keyelco.com/pdfs/M55-prod09.pdf')
 for p in children(t,'pad'):
  if value(p[1])=='2':child(p,'at')[1]='9.74'
  child(p,'drill')[1]='1.70'
 for k in ['fp_line','fp_text','property']:
  for v in children(t,k):
   for tag in ['start','end']if k=='fp_line'else['at']:
    a=child(v,tag)
    if a is not None:a[1]=str(round(float(a[1])-.09,6))
 for v in list(children(t,'model')):t.remove(v)
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(dump(t)+'\n');return out
if __name__=='__main__':
 out=ROOT/'hardware/motherboard_fuse_geometry/CNC_MB_Fuse.pretty/Keystone_3568_M55.kicad_mod';make_library(out);print(out)
