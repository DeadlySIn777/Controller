"""Disconnected four-resistor native fixture, not a motherboard route claim."""
from pathlib import Path
import json,sys,shutil,xml.etree.ElementTree as ET
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_selected_additive import sha,write,prepare,import_session
HERE=Path(__file__).resolve().parent
OUT=HERE/'native-fixture-r05'
def xy(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def main():
 OUT.mkdir(exist_ok=False);b=pcbnew.BOARD();b.SetCopperLayerCount(6);print('fixture board',flush=True)
 nets={}
 for i,name in enumerate(('/SIGNAL','/RETAINED_SIGNAL','/LOGIC_GND'),1):
  n=pcbnew.NETINFO_ITEM(b,name,i);b.Add(n);nets[name]=n
 fps={};model={'components':{}}
 for ref,x,y,name in [('R1',5,5,'/SIGNAL'),('R2',20,5,'/SIGNAL'),('R3',5,12,'/RETAINED_SIGNAL'),('R4',20,12,'/RETAINED_SIGNAL')]:
  fp=pcbnew.FootprintLoad('C:/Program Files/KiCad/10.0/share/kicad/footprints/Resistor_SMD.pretty','R_0603_1608Metric')
  fp.SetFPID(pcbnew.LIB_ID('Resistor_SMD','R_0603_1608Metric'));fp.SetReference(ref);fp.SetValue('10k');fp.SetPosition(xy(x,y))
  fp.Reference().SetLayer(pcbnew.F_Fab);fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
  b.Add(fp);fps[ref]=fp
  for p in fp.Pads():p.SetNet(nets[name if p.GetNumber()=='1' else '/LOGIC_GND'])
  model['components'][ref]={'footprint':'Resistor_SMD:R_0603_1608Metric','value':'10k','mnp':'TEST_ONLY_FIXTURE_R','pins':{'1':name,'2':'/LOGIC_GND'}}
 print('fixture four footprints',flush=True)
 def track(a,z,name):
  t=pcbnew.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetWidth(pcbnew.FromMM(.2));t.SetLayer(pcbnew.F_Cu);t.SetNet(nets[name]);b.Add(t)
 # Retained routes and ground stitches are literal base copper.
 for fp in fps.values():
  p=next(p for p in fp.Pads() if p.GetNumber()=='2');vpos=p.GetPosition()+xy(1,0);track(p.GetPosition(),vpos,'/LOGIC_GND')
  v=pcbnew.PCB_VIA(b);v.SetPosition(vpos);v.SetWidth(pcbnew.FromMM(.6));v.SetDrill(pcbnew.FromMM(.3));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(nets['/LOGIC_GND']);b.Add(v)
 p3=next(p for p in fps['R3'].Pads() if p.GetNumber()=='1').GetPosition();p4=next(p for p in fps['R4'].Pads() if p.GetNumber()=='1').GetPosition()
 for a,z in [(p3,xy(pcbnew.ToMM(p3.x),10)),(xy(pcbnew.ToMM(p3.x),10),xy(pcbnew.ToMM(p4.x),10)),(xy(pcbnew.ToMM(p4.x),10),p4)]:track(a,z,'/RETAINED_SIGNAL')
 for a,z in [(xy(0,0),xy(30,0)),(xy(30,0),xy(30,20)),(xy(30,20),xy(0,20)),(xy(0,20),xy(0,0))]:
  d=pcbnew.PCB_SHAPE();d.SetShape(pcbnew.SHAPE_T_SEGMENT);d.SetStart(a);d.SetEnd(z);d.SetLayer(pcbnew.Edge_Cuts);d.SetWidth(pcbnew.FromMM(.15));b.Add(d)
 zone=pcbnew.ZONE(b);zone.SetLayer(pcbnew.In1_Cu);zone.SetNet(nets['/LOGIC_GND']);zone.SetLocalClearance(pcbnew.FromMM(.15));zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
 zone.Outline().NewOutline()
 for x,y in [(1,1),(29,1),(29,19),(1,19)]:zone.Outline().Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
 b.Add(zone)
 # A real F.Cu ground fill away from the selected route exercises conversion
 # of actual filled copper (and holes) to interchange routing obstacles.
 outer=pcbnew.ZONE(b);outer.SetLayer(pcbnew.F_Cu);outer.SetNet(nets['/LOGIC_GND']);outer.SetLocalClearance(pcbnew.FromMM(.15));outer.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);outer.Outline().NewOutline()
 for x,y in [(4,11),(8,11),(8,19),(4,19)]:outer.Outline().Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
 b.Add(outer)
 board=OUT/'fixture.kicad_pcb';pcbnew.SaveBoard(str(board),b);print('fixture native saved before fill',flush=True)
 reference=ROOT/'hardware/board_review/revisions/20260930-23/motion-card-route-candidate.kicad_pro'
 shutil.copyfile(reference,board.with_suffix('.kicad_pro'))
 # CLI loads the saved project/design settings before filling; a raw unsaved
 # BOARD does not have the project state required by KiCad's ZONE_FILLER.
 import subprocess
 run=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--refill-zones','--save-board','--output',str(OUT/'fixture-initial-drc.json'),str(board)],capture_output=True,text=True,encoding='utf8')
 (OUT/'fixture-initial-drc.txt').write_text(run.stdout+run.stderr);print('fixture CLI filled',run.returncode,flush=True)
 # Source pins and population are an explicit native XML fixture, not a fake
 # controller export. It exists only to exercise source-bound routing guards.
 xml=ET.Element('export');comps=ET.SubElement(xml,'components');xnets=ET.SubElement(xml,'nets')
 for ref,c in model['components'].items():ET.SubElement(comps,'comp',ref=ref)
 for i,name in enumerate(nets,1):
  n=ET.SubElement(xnets,'net',code=str(i),name=name)
  for ref,c in model['components'].items():
   for pin,value in c['pins'].items():
    if value==name:ET.SubElement(n,'node',ref=ref,pin=pin,pintype='passive')
 ET.ElementTree(xml).write(OUT/'netlist.xml',encoding='utf-8',xml_declaration=True);write(OUT/'design.json',model)
 manifest={'schema_version':1,'electrical_review':'Disconnected native software-guard fixture only','board_sha256':sha(board),'project_sha256':sha(board.with_suffix('.kicad_pro')),'design_sha256':sha(OUT/'design.json'),'netlist_sha256':sha(OUT/'netlist.xml'),
  'nets':{'/SIGNAL':dict(type='ordinary_logic',controlled_impedance=False,maximum_voltage_v=3.6,width_mm=.2,clearance_mm=.15,layers=['F.Cu'],reference_layers={'F.Cu':'In1.Cu'},return_net='/LOGIC_GND',reference_corridor_margin_mm=.2,source_pins=[['R1','1'],['R2','1']],allow_vias=False)}}
 write(OUT/'manifest.json',manifest)
 prepare(board,OUT/'design.json',OUT/'netlist.xml',OUT/'manifest.json',OUT/'prepared')
 p1=next(p for p in fps['R1'].Pads() if p.GetNumber()=='1').GetPosition();p2=next(p for p in fps['R2'].Pads() if p.GetNumber()=='1').GetPosition()
 coords=[tuple(p1),tuple(xy(pcbnew.ToMM(p1.x),3)),tuple(xy(pcbnew.ToMM(p2.x),3)),tuple(p2)]
 points=' '.join(str(round(v/100)) for p in coords for v in (p[0],-p[1]))
 session=OUT/'synthetic-test-only.ses';session.write_text('(session "fixture" (base_design "selected") (placement (resolution um 10)) (routes (resolution um 10) (library_out) (network_out (net "/SIGNAL" (wire (path F.Cu 2000 '+points+'))))))\n',encoding='utf8')
 result=import_session(OUT/'prepared',session,OUT/'imported')
 write(OUT/'fixture-receipt.json',dict(test_only=True,source_or_live_PCB_mutated=False,handcrafted_SES_fixture=True,real_autorouter_run=False,actual_result=result))
 print(json.dumps(dict(added=result['added_items'],old=result['old_copper_items'],DRC=result['native_drc'],inventory=result['independent_connectivity'])))
if __name__=='__main__':main()
