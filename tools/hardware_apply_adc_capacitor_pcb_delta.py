"""Apply only the three adopted ADC capacitor identities/one land-size change.

This preserves their current poses for a separate reviewed ADC-cell layout.
Every other footprint and all existing copper remain exact. Required local
connections remain explicit until that cell is physically routed.
"""
import argparse,collections,copy,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value,q
from hardware_populate_motherboard_pcb import ROOT,sha,write,pad_template,load_exact_footprint,footprint_name,native_parts_and_nets
from hardware_route_logic_return import identity
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
EXPECTED={'C14744':('885012206052','Capacitor_SMD:C_0603_1608Metric'),'C14745':('885012206052','Capacitor_SMD:C_0603_1608Metric'),'C14746':('GRM21BR71A106MA73L','Capacitor_SMD:C_0805_2012Metric')}
def ref(f):return value(next(p[2]for p in children(f,'property')if value(p[1])=='Reference'))
def source_clusters(b,excluded):
 b.BuildConnectivity();pads={p.m_Uuid.AsString():p for f in b.GetFootprints()if f.GetReference()not in excluded for p in f.Pads()if p.GetNumber()}
 return {u:sorted({u}|{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T and v.m_Uuid.AsString()in pads})for u,p in pads.items()}
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('board','child-receipt','source','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 record=json.loads(a.child_receipt.read_text());rows={r['reference']:r for r in record['exact_changes']}
 if not record['passed']or set(rows)!=set(EXPECTED):raise ValueError('Exact frozen three-cap child correction required')
 model=json.loads((a.source/'design.json').read_text());parts=model['components']
 native,nodes=native_parts_and_nets(a.source/'netlist.xml',parts)
 frozen={str(p.resolve()):sha(p)for p in (a.board,a.child_receipt,a.source/'design.json',a.source/'netlist.xml',Path(__file__))}
 for name,h in record['after_source_hashes'].items():
  path=Path(name)
  if path.name in ('design.json','netlist.xml','bom.csv')and sha(path)!=h:raise ValueError('Frozen child source changed '+name)
 b=pcbnew.LoadBoard(str(a.board));fps={f.GetReference():f for f in b.GetFootprints()}
 if set(fps)!=set(parts):raise ValueError('Complete actual source footprint population differs')
 for r,c in parts.items():
  for p in fps[r].Pads():
   if p.GetNumber()and p.IsOnCopperLayer()and p.GetNetname()!=nodes[r,p.GetNumber()]:raise ValueError('Native pin/net identity differs '+r+'.'+p.GetNumber())
  if r not in EXPECTED and footprint_name(fps[r])!=c['footprint']:raise ValueError('Unrelated exact source footprint differs '+r)
 oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};clusters=source_clusters(b,set(EXPECTED))
 tree=parse(a.board.read_text());raw={ref(f):f for f in children(tree,'footprint')};original={r:dump(f)for r,f in raw.items()}
 lands={r:collections.Counter(pad_template(p)for p in f.Pads())for r,f in fps.items()};changes=[];libraries={}
 a.out.mkdir(parents=True)
 for r,(mpn,fpname)in EXPECTED.items():
  first,last=rows[r]['before'],rows[r]['after'];c=parts[r];f=fps[r]
  if (last['mpn'],last['footprint'])!=(mpn,fpname)or any(c[k]!=last[k]for k in ('mpn','footprint','value','capacitance_f','voltage_rating_v','pins')):raise ValueError('Integrated parent has not adopted exact child '+r)
  if first['pins']!=last['pins']or f.GetValue()!=first['value']or footprint_name(f)!=first['footprint']:raise ValueError('Old actual capacitor/source identity differs '+r)
  wanted=copy.deepcopy(raw[r])
  if first['footprint']!=last['footprint']:
   nf,file=load_exact_footprint(fpname,a.source,a.board);libraries[str(file)]=sha(file)
   temp=pcbnew.BOARD();temp.SetCopperLayerCount(b.GetCopperLayerCount());nf.SetReference(r);nf.SetValue(last['value']);nf.SetPosition(f.GetPosition());nf.SetOrientationDegrees(f.GetOrientationDegrees());nf.SetPath(f.GetPath());temp.Add(nf)
   if f.GetLayer()!=nf.GetLayer():nf.Flip(nf.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
   beforepads={p.GetNumber():p for p in f.Pads()if p.GetNumber()};afterpads={p.GetNumber():p for p in nf.Pads()if p.GetNumber()}
   if set(beforepads)!=set(afterpads)or set(afterpads)!={'1','2'}:raise ValueError('Exact manufacturer numbered capacitor lands differ')
   nets={}
   for num,pad in afterpads.items():
    old=beforepads[num];name=str(old.GetNetname())
    if name not in nets:nets[name]=pcbnew.NETINFO_ITEM(temp,name);temp.Add(nets[name])
    pad.SetNet(nets[name])
   nf.SetDNP(f.IsDNP());scratch=a.out/'manufacturer-land-donor.kicad_pcb';pcbnew.SaveBoard(str(scratch),temp)
   wanted=children(parse(scratch.read_text()),'footprint')[0]
   child(wanted,'uuid')[1]=child(raw[r],'uuid')[1]
   oldrawpads={value(p[1]):p for p in children(raw[r],'pad')}
   for p in children(wanted,'pad'):
    child(p,'uuid')[1]=child(oldrawpads[value(p[1])],'uuid')[1]
   # Preserve source/reference fields and ancestry while adopting the actual
   # manufacturer's larger body, copper, paste, mask and courtyard geometry.
   for p in list(children(wanted,'property')):wanted.remove(p)
   wanted.extend(copy.deepcopy(p)for p in children(raw[r],'property'))
   lands[r]=collections.Counter(pad_template(p)for p in nf.Pads())
  for p in children(wanted,'property'):
   if value(p[1])=='Value':p[2]=q(last['value'])
   elif value(p[1])=='MPN':p[2]=q(last['mpn'])
  tree[tree.index(raw[r])]=wanted;changes.append(dict(reference=r,before_MPN=first['mpn'],after_MPN=last['mpn'],before_footprint=first['footprint'],after_footprint=last['footprint'],pose_unchanged=True,numbered_source_pad_UUIDs_preserved=True))
 dest=a.out/'motherboard-adc-source-reconciled-candidate.kicad_pcb';dest.write_text(dump(tree)+'\n')
 for ext in ('.kicad_pro','.kicad_dru'):shutil.copy2(a.board.with_suffix(ext),dest.with_suffix(ext))
 for p in a.board.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
  elif p.name=='fp-lib-table':shutil.copy2(p,a.out/p.name)
 run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);(a.out/'drc.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native DRC did not execute')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();newfps={f.GetReference():f for f in fresh.GetFootprints()};actualcu={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
 if actualcu!=oldcu:raise ValueError('Existing copper/net assignment changed during source patch')
 if source_clusters(fresh,set(EXPECTED))!=clusters:raise ValueError('Stationary source-pad clusters changed')
 for r,f in newfps.items():
  if collections.Counter(pad_template(p)for p in f.Pads())!=lands[r]:raise ValueError('Actual physical manufacturer lands differ '+r)
  if (tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())!=(tuple(fps[r].GetPosition()),fps[r].GetOrientationDegrees(),fps[r].GetLayer()):raise ValueError('Component pose changed '+r)
  if {(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in f.Pads()}!={(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in fps[r].Pads()}:raise ValueError('Exact source pad UUID/net identity changed '+r)
 finalraw={ref(f):f for f in children(parse(dest.read_text()),'footprint')}
 if any(dump(finalraw[r])!=s for r,s in original.items()if r not in EXPECTED):raise ValueError('Unrelated native footprint changed')
 if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Patch input changed')
 drc=json.loads((a.out/'drc.json').read_text())
 if drc.get('ignored_checks')or any(v['severity']=='error'for v in drc['violations']):raise ValueError('Native ADC patch geometry has an unresolved error')
 write(a.out/'receipt.json',dict(passed=True,input_sha256=frozen,exact_manufacturer_footprint_sources=libraries,board_sha256=sha(dest),exact_three_component_changes=changes,all_other_source_lands_poses_UUIDs_nets_copper_and_stationary_pad_clusters_preserved=True,native_DRC_errors=0,native_DRC_regular=len(drc['violations']),native_DRC_types=dict(collections.Counter(v['type']for v in drc['violations'])),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),seven_capacitor_ADC_cell_still_required=True,manufacturing_ready=False))
 print(dict(passed=True,source_parts=len(newfps),changed_capacitors=3,uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),board_sha256=sha(dest)))
if __name__=='__main__':main()
