"""Report-only native proof for the actual staged two-bank POR/fast-CLR routes."""
import sys,json,hashlib,shutil,collections,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_populate_motherboard_pcb import pad_template,native_parts_and_nets
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved

BASE=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb')
LOCAL=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-bypass-poses-r434/motherboard-staged-Source27-local-bypass-candidate.kicad_pcb')
ROUTED=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-route-r454/debug.kicad_pcb')
ROUTE_ROWS=ROUTED.with_name('debug.json')
SOURCE=Path('reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/candidate/motherboard')
OUT=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r460')
assert not OUT.exists();OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[BASE,LOCAL,ROUTED,ROUTE_ROWS,SOURCE/'design.json',SOURCE/'netlist.xml',Path(__file__),Path('hardware/motherboard/design.json')]}
def lands(f):
 c=pcbnew.FOOTPRINT(f);c.SetPosition(pcbnew.VECTOR2I(0,0))
 if c.GetLayer()==pcbnew.B_Cu:c.Flip(c.GetPosition(),False)
 c.SetOrientationDegrees(0)
 return collections.Counter(pad_template(p)for p in c.Pads())
def group(b,p):return {p.m_Uuid.AsString()}|{q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T}
dest=OUT/'motherboard-staged-Source27-reset-routed-candidate.kicad_pcb'
shutil.copyfile(ROUTED,dest)
for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(LOCAL.with_suffix(e),dest.with_suffix(e))
for p in LOCAL.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,OUT/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,OUT/p.name)
b0=pcbnew.LoadBoard(str(BASE));b0.BuildConnectivity();b=pcbnew.LoadBoard(str(dest));print('FILL_START',flush=True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(dest),b);print('FILL_SAVED',sha(dest),flush=True)
b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();f0={f.GetReference():f for f in b0.GetFootprints()};fs={f.GetReference():f for f in b.GetFootprints()};extra=set(fs)-set(f0)
assert extra=={'U11035','U11036','U11037','U11038','C11089','C11090','C11091','C11092','R11082','R11083'}
assert len(fs)==2698
model=json.loads((SOURCE/'design.json').read_text());physical={r:v for r,v in model['components'].items()if v.get('physical')};native,nodes=native_parts_and_nets(SOURCE/'netlist.xml',physical)
allowed_values={'R2106','U11019','U11025','R11074','R11078'};remaps={('U11032','6'),('U11034','6')};old_pads={p.m_Uuid.AsString():p for p in b0.GetPads()};all_pads={p.m_Uuid.AsString():p for p in b.GetPads()};pin_deltas=[]
for r,f in f0.items():
 g=fs[r];assert (f.GetFPID().GetLibNickname(),f.GetFPID().GetLibItemName())==(g.GetFPID().GetLibNickname(),g.GetFPID().GetLibItemName()),('FPID',r)
 assert lands(f)==lands(g),('LANDS',r)
 assert (mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())==(mm(g.GetPosition()),g.GetOrientationDegrees(),g.GetLayer()),('POSE',r)
 if r in allowed_values:assert g.GetValue()==physical[r]['value'],('VALUE',r)
 else:assert f.GetValue()==g.GetValue(),('UNEXPECTED_VALUE',r)
 for p in f.Pads():
  q=all_pads[p.m_Uuid.AsString()];assert p.GetNumber()==q.GetNumber()
  if (r,p.GetNumber())in remaps:
   assert q.GetNetname()==nodes[r,p.GetNumber()]and p.GetNetname()!=q.GetNetname()
   pin_deltas.append(dict(ref=r,pin=p.GetNumber(),pad_uuid=q.m_Uuid.AsString(),before=p.GetNetname(),after=q.GetNetname()))
  else:assert pad_identity(p)==pad_identity(q),('OLD_PAD_CHANGED',r,p.GetNumber())
for r in extra:
 c=physical[r];f=fs[r];assert (f.GetFPID().GetLibNickname()+':'+f.GetFPID().GetLibItemName(),f.GetValue())==(c['footprint'],c['value']),('NEW_PART',r)
 for p in f.Pads():
  if p.GetNumber():assert p.GetNetname()==nodes[r,p.GetNumber()],('NEW_PIN',r,p.GetNumber())
old_cu={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};new_cu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};routes=json.loads(ROUTE_ROWS.read_text());ret=set(routes['retired']);added={q['uuid']for q in routes['new_Cu']}
assert set(old_cu)-set(new_cu)==ret and set(new_cu)-set(old_cu)==added
assert all(old_cu[u]==new_cu[u]for u in set(old_cu)&set(new_cu)), 'Retained Cu modified or native net reassigned'
omit={x['pad_uuid']for x in pin_deltas};old_groups=[g-omit for g in source_clusters(b0)];old_groups=[g for g in old_groups if g]
source_error=None
try:prior=clusters_preserved(old_groups,b)
except Exception as e:prior=None;source_error=repr(e)
pp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};endpoints=[];missing=[]
for bank,por,sch,cap0,cap1,pd,raw,slow,latch in [('A','U11035','U11036','C11089','C11090','R11082','C11083','C11082','U11032'),('B','U11037','U11038','C11091','C11092','R11083','C11086','C11085','U11034')]:
 for r,p,target,tp in [(por,'3',raw,'1'),(por,'5',raw,'1'),(por,'6',raw,'1'),(sch,'5',raw,'1'),(cap0,'1',raw,'1'),(cap1,'1',raw,'1'),(por,'2',raw,'2'),(sch,'3',raw,'2'),(cap0,'2',raw,'2'),(cap1,'2',raw,'2'),(pd,'2',raw,'2'),(por,'1',slow,'1'),(sch,'2',slow,'1'),(sch,'4',latch,'6'),(pd,'1',latch,'6')]:
  a,c=pp[r,p],pp[target,tp];ok=c.m_Uuid.AsString()in group(b,a);row=dict(bank=bank,actual_endpoint=[r,p],target=[target,tp],passed=ok)
  endpoints.append(row)
  if not ok:missing.append(row)
drill_rows=[];drill_fail=[]
for t in b.GetTracks():
 if t.m_Uuid.AsString()not in added or not isinstance(t,pcbnew.PCB_VIA):continue
 shape=pcbnew.SHAPE_CIRCLE(t.GetPosition(),t.GetDrillValue()//2+pcbnew.FromMM(.15)+1);hits=[]
 for p in b.GetPads():
  if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
   if p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(shape,0):hits.append([p.GetParentFootprint().GetReference(),p.GetNumber(),b.GetLayerName(l)])
 row=dict(uuid=t.m_Uuid.AsString(),position_mm=mm(t.GetPosition()),native_shape_registration_150um_passed=not hits,hits=hits);drill_rows.append(row)
 if hits:drill_fail.append(row)
run=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(OUT/'drc.json'),str(dest)],capture_output=True,text=True);(OUT/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr);assert run.returncode==0
d=json.loads((OUT/'drc.json').read_text());new_viol=[v for v in d['violations']if not(v['type']=='via_dangling'and {i['uuid']for i in v['items']}=={'4b393b84-561e-44d7-a13c-f7dd8ec81ce5'})]
assert all(sha(Path(p))==h for p,h in inputs.items())
result=dict(passed=not(source_error or missing or drill_fail or new_viol),input_hashes=inputs,board_sha256=sha(dest),physical_parts=2698,exact_ten_new_refs=sorted(extra),original2688_lands_pads_poses_and_Cu_preserved_except_exact_authorized_pin_value_retirement=True,exact_old_two_pin_remaps=pin_deltas,exact_old_value_update_refs=sorted(allowed_values),exact_retired_Cu=sorted(ret),exact_new_Cu=sorted(added),all_prior_Source_clusters_except_only_two_remapped_CLR_pads=prior,Source_error=source_error,actual_thirty_connected_new_endpoints=endpoints,missing_endpoints=missing,intentional_NC_new_pins=[['U11035','4'],['U11036','1'],['U11037','4'],['U11038','1']],new_drill_shape_registration=drill_rows,new_violations=new_viol,all_native_violations=d['violations'],native_unconnected_count=len(d.get('unconnected_items',[])),reference_current_timing_and_full_power_qualification_pending=True,Source27_adopted=False,manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(result,indent=2));print('NATIVE_SCOPE',result['passed'],'new_violations',len(new_viol),'missing',len(missing),'Source',source_error,flush=True)
