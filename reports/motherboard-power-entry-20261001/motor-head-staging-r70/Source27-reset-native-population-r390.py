import sys,json,shutil,hashlib,copy,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import native_parts_and_nets,load_exact_footprint,uid,copper_pad,footprint_name,pad_template
from hardware_route_logic_return import mm,xy,identity
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
B=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb');S=Path('reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/candidate/motherboard');O=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-population-r390');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
model=json.loads((S/'design.json').read_text());physical={r:v for r,v in model['components'].items()if v.get('physical')};native,nodes=native_parts_and_nets(S/'netlist.xml',physical);b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()};extra=set(physical)-set(fs);assert extra=={'U11035','U11036','U11037','U11038','C11089','C11090','C11091','C11092','R11082','R11083'};frozen={str(p):sha(p)for p in[B,S/'design.json',S/'netlist.xml',Path(__file__)]}
nets={n:b.FindNet(n)for n in set(nodes.values())}
for n,x in list(nets.items()):
 if x is None:
  x=pcbnew.NETINFO_ITEM(b,n);b.Add(x);nets[n]=x
changes=[]
for ref in ['R2106','U11019','U11025','R11074','R11078']:
 old=fs[ref].GetValue();fs[ref].SetValue(physical[ref]['value']);changes.append(dict(ref=ref,old_value=old,new_value=fs[ref].GetValue(),exact_staged_MPN=physical[ref]['mpn']))
remap=[]
for ref in ['U11032','U11034']:
 p=next(p for p in fs[ref].Pads()if p.GetNumber()=='6');old=p.GetNetname();p.SetNet(nets[nodes[ref,'6']]);remap.append(dict(reference=ref,pin='6',old_net=old,new_net=p.GetNetname(),physical_old_CLR_terminal_Cu_retirement_required=True))
# Fixed first physical poses are report-only candidates; all bypass/CLR routes
# are intentionally still pending. Exact staged Source/netlist is used.
poses={'U11035':([261.5,201.5],0,'B.Cu'),'U11036':([262.,206.],0,'B.Cu'),'C11089':([258.5,201.5],90,'B.Cu'),'C11090':([259.,206.],90,'B.Cu'),'R11082':([266.,206.],0,'B.Cu'),'U11037':([257.5,153.],0,'B.Cu'),'U11038':([260.5,155.75],0,'B.Cu'),'C11091':([254.5,153.],90,'B.Cu'),'C11092':([260.5,159.],0,'B.Cu'),'R11083':([264.7,156.],0,'B.Cu')};files=[];added={}
for ref in sorted(extra):
 c=physical[ref];f,p=load_exact_footprint(c['footprint'],S,B);files.append(dict(path=str(p),sha256=sha(p)));f.SetReference(ref);f.SetValue(c['value']);f.Value().SetVisible(False);f.Reference().SetLayer(pcbnew.F_Fab);f.Reference().SetTextSize(xy((.65,.65)));f.Reference().SetTextThickness(pcbnew.FromMM(.1));path=native[ref].find('sheetpath').attrib['tstamps']+native[ref].findtext('tstamps');f.SetPath(pcbnew.KIID_PATH(path));b.Add(f)
 for p in f.Pads():
  if copper_pad(p):p.SetNet(nets[nodes[ref,p.GetNumber()]])
 pt,angle,side=poses[ref]
 if side=='B.Cu':f.Flip(f.GetPosition(),False)
 f.SetPosition(xy(pt));f.SetOrientationDegrees(angle);added[ref]=f
clashes=[]
for ref,f in added.items():
 for q in b.GetFootprints():
  if q.GetReference()!=ref and q.GetLayer()==f.GetLayer()and intersects(side_box(f),side_box(q),0):clashes.append([ref,q.GetReference()])
dest=O/'motherboard-staged-Source27-reset-unrouted-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for parent in[B.parent,S]:
 for x in parent.iterdir():
  if x.is_dir()and(x.suffix=='.pretty'or x.name=='3dmodels')and not(O/x.name).exists():shutil.copytree(x,O/x.name)
shutil.copyfile(S/'fp-lib-table',O/'fp-lib-table')
assert all(sha(Path(p))==h for p,h in frozen.items());(O/'staging.json').write_text(json.dumps(dict(physical_parts=len(b.GetFootprints()),expected_staged_parts=len(physical),Source27_adopted=False,input_hashes=frozen,exact_value_only_part_updates=changes,exact_old_two_pin_remaps=remap,exact_new_ten_references=sorted(extra),actual_new_poses=poses,new_footprint_source_hashes=files,courtyard_clashes=clashes,physical_old_CLR_terminal_Cu_retirement_pending=True,new_actual_thirty_pin_routing_pending=True,board_sha256=sha(dest),manufacturing_ready=False),indent=2));print('POPULATION',len(b.GetFootprints()),'COURTYARD',clashes,flush=True)
