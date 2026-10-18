"""Critical WIP import retaining authoritative objects across native serialization.

The DSN/SES placement grid can round some existing positions by one unit.
The complete session placement must equal native DSN placement. A separate
placement-only/no-route native import control must match every donor immutable
object. All donor immutable data is then discarded. The standard native CLI
refills on the authoritative original geometry; exact immutable and conductor
identity is checked afterward. No original geometry is normalized or waived.
"""
from pathlib import Path
import copy,json,sys,hashlib,re
from decimal import Decimal,ROUND_HALF_UP
import pcbnew
import hardware_route_critical_digital_wip_r04 as prior
engine=prior.prior.prior
FROZEN_WIP_R04_SHA='03d688036bcc44e7a6df7173c74a1f199a609cf6ef051830754e6e9c0bce79e1'
original_merge=engine.merge_tree
original_configure=prior.prior.configure
original_dump=engine.dump
LEDGER=[]

def dump_native_board(tree):
 # Preserve the exact parsed objects while preventing a 25+ MB one-line PCB.
 # KiCad's real parser rejects that generic schematic serialization.
 if isinstance(tree,list)and tree and tree[0]=='kicad_pcb':
  return '('+tree[0]+'\n'+'\n'.join(original_dump(n)if isinstance(n,list)else n for n in tree[1:])+')'
 return original_dump(tree)

def control(original_path,output):
 b=pcbnew.LoadBoard(str(original_path));pcbnew.SaveBoard(str(output),b)
 return engine.parse(output.read_text(encoding='utf8'))
def assert_control_matches(expected,actual):
 if engine.immutable_objects(expected)!=engine.immutable_objects(actual):
  raise ValueError('Donor/refill changed geometry beyond exact native serialization control')
def placement_inventory(tree):
 section=engine.child(tree,'placement');resolution=engine.child(section,'resolution')
 if resolution is None:resolution=engine.child(tree,'resolution')
 if engine.value(resolution[1])!='um':raise ValueError('Unreviewed native/session coordinate unit')
 # DSN uses its declared unit (um); SES stores integer grid coordinates at
 # resolution um 10. Native placement-only import below independently proves
 # this conversion for every actual footprint rather than tolerating shifts.
 scale=Decimal(resolution[2])if tree[0]=='session'else Decimal(1)
 if tree[0]=='pcb'and engine.dump(engine.child(tree,'unit'))!='(unit um)':
  raise ValueError('Unreviewed native DSN placement unit')
 result={}
 for component in engine.children(section,'component'):
  image=engine.value(component[1])
  # KiCad adds numeric image-cache suffixes for graphic/orientation variants;
  # SES writes the underlying FPID. These aliases are not physical footprints.
  # Exact native footprint/pad/graphic identity is separately control-checked.
  if tree[0]=='pcb':image=re.sub(r'::[0-9]+$','',image)
  for row in engine.children(component,'place'):
   ref=engine.value(row[1])
   if ref in result:raise ValueError('Duplicate session placement reference')
   xy=[Decimal(row[i])/scale for i in (2,3)];grid=Decimal(1)/Decimal(resolution[2])
   if tree[0]=='pcb':
    rounded=[v.quantize(grid,rounding=ROUND_HALF_UP)for v in xy]
    if any(abs(v-w)>Decimal('.001')for v,w in zip(xy,rounded)):
     raise ValueError('Native export quantization exceeds the exact one-nm bounded control')
    xy=rounded
   elif any(v/grid!=(v/grid).to_integral_value()for v in xy):
    raise ValueError('Session placement coordinate is outside its declared grid')
   angle=Decimal(row[5]);angle=(angle%360+360)%360
   result[ref]=(image,*xy,engine.value(row[4]),angle)
 return 'um',result
def assert_native_placement(native,session):
 if placement_inventory(native)!=placement_inventory(session):
  raise ValueError('Session changed the complete exact native-export placement inventory')
def restore_immutable(original,donor):
 result=copy.deepcopy(original)
 for kind in ('segment','via','arc'):
  for obj in list(engine.children(result,kind)):result.remove(obj)
  result.extend(copy.deepcopy(engine.children(donor,kind)))
 return result
def merge_tree(base,donor,rows):
 out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 prepared=Path(sys.argv[sys.argv.index('--prepared')+1]).resolve()
 session=engine.parse((out/'session.ses').read_text(encoding='utf8'))
 native=engine.parse((prepared/'native.dsn').read_text(encoding='utf8'))
 assert_native_placement(native,session)
 no_route=copy.deepcopy(session);routes=engine.child(no_route,'routes')
 network=engine.child(routes,'network_out')
 if network is None:raise ValueError('Actual session has no route network')
 routes.remove(network);routes.append(['network_out'])
 spath=out/'native-placement-only-control.ses';spath.write_text(engine.dump(no_route)+'\n',encoding='utf8')
 path=out/'native-placement-only-control.kicad_pcb'
 board=pcbnew.LoadBoard(str(out/'base.kicad_pcb'))
 if not pcbnew.ImportSpecctraSES(board,str(spath)):raise ValueError('Native placement-only import control failed')
 pcbnew.SaveBoard(str(path),board);canonical=engine.parse(path.read_text(encoding='utf8'))
 assert_control_matches(canonical,donor)
 restored=restore_immutable(base,donor)
 if engine.immutable_objects(base)!=engine.immutable_objects(restored):
  raise ValueError('Authoritative immutable object restoration failed')
 LEDGER.append(dict(stage='SES import',serialization_control_sha256=engine.sha(path),
  placement_only_control_session_sha256=engine.sha(spath),
  full_session_placement_equals_original_native_export=True,
  donor_immutable_objects_equal_exact_native_control=True,
  every_donor_immutable_object_discarded=True,authoritative_original_objects_retained=True))
 return original_merge(base,restored,rows)

def fill_authoritative(path,out,name):
 before=engine.parse(Path(path).read_text(encoding='utf8'))
 cpath=out/(name+'-serialization-control.kicad_pcb');canonical=control(path,cpath)
 b=pcbnew.LoadBoard(str(path));assigned={t.m_Uuid.AsString():t.GetNetname()for t in b.GetTracks()}
 pcbnew.ZONE_FILLER(b).Fill(b.Zones())
 if assigned!={t.m_Uuid.AsString():t.GetNetname()for t in b.GetTracks()}:
  raise ValueError('Native fill inferred a different exact conductor net')
 temp=out/(name+'-native-filled-donor.kicad_pcb');pcbnew.SaveBoard(str(temp),b)
 filled=engine.parse(temp.read_text(encoding='utf8'));assert_control_matches(canonical,filled)
 route_objects=lambda tree:{engine.value(engine.child(t,'uuid')[1]):engine.dump(t)
  for k in ('segment','via','arc')for t in engine.children(tree,k)}
 if route_objects(canonical)!=route_objects(filled):
  raise ValueError('Native fill changed an actual serialized conductor')
 zones={engine.value(engine.child(z,'uuid')[1]):z for z in engine.children(filled,'zone')}
 result=copy.deepcopy(before)
 for z in engine.children(result,'zone'):
  ident=engine.value(engine.child(z,'uuid')[1])
  for kind in ('filled_polygon','fill_segments'):
   for generated in list(engine.children(z,kind)):z.remove(generated)
   z.extend(copy.deepcopy(engine.children(zones[ident],kind)))
 if engine.immutable_objects(before)!=engine.immutable_objects(result)or route_objects(before)!=route_objects(result):
  raise ValueError('Generated-fill-only restoration changed authoritative objects')
 Path(path).write_text(engine.dump(result)+'\n',encoding='utf8')
 LEDGER.append(dict(stage=name,serialization_control_sha256=engine.sha(cpath),
  filled_native_donor_sha256=engine.sha(temp),native_fill_used_original_exact_geometry=True,
  only_generated_zone_fill_objects_copied=True,all_original_lands_poses_nets_copper_retained=True))

def configure(disposition,manifest):
 d=original_configure(disposition,manifest);gate=engine.native_drc
 def native_drc(board,out,name,refill=False):
  before=engine.parse(Path(board).read_text(encoding='utf8'))if refill else None
  result=gate(board,out,name,refill)
  if refill:
   after=engine.parse(Path(board).read_text(encoding='utf8'))
   if engine.immutable_objects(before)!=engine.immutable_objects(after):
    raise ValueError('Native CLI refill changed authoritative immutable objects')
   tracks=lambda tree:{engine.value(engine.child(t,'uuid')[1]):engine.dump(t)for k in ('segment','via','arc')for t in engine.children(tree,k)}
   if tracks(before)!=tracks(after):raise ValueError('Native CLI refill changed authoritative conductors')
   LEDGER.append(dict(stage=name,actual_native_CLI_refill=True,
    all_original_immutable_objects_and_conductors_exactly_preserved=True))
  return result
 engine.native_drc=native_drc
 return d
def main():
 if hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()!=FROZEN_WIP_R04_SHA:
  raise ValueError('Frozen scoped critical WIP executor changed')
 prior.prior.configure=configure;engine.merge_tree=merge_tree;engine.dump=dump_native_board
 prior.main()
 out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 target=out/('prepare.json'if sys.argv[1]=='prepare'else'receipt.json')
 r=engine.read(target);r.update(effective_authoritative_critical_executor_sha256=engine.sha(__file__),
  native_serialization_control_ledger=LEDGER,authoritative_objects_never_normalized=True,manufacturing_ready=False)
 engine.write(target,r)
if __name__=='__main__':main()
