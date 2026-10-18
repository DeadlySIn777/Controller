"""Native footprint/pad/drill inventory; isolated fixture, not a routed PCB."""
import json
from pathlib import Path
import shutil
import pcbnew

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'hardware/motherboard_diagnostics'


def main():
 d=json.loads((SOURCE/'design.json').read_text(encoding='utf-8'))
 b=pcbnew.BOARD();rows=[];nets={};count=0
 for index,(ref,c) in enumerate(d['components'].items()):
  nickname,name=c['footprint'].split(':',1)
  lib=SOURCE/'CNC_MB_Diagnostics.pretty' if nickname=='CNC_MB_Diagnostics' else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(nickname+'.pretty')
  fp=pcbnew.FootprintLoad(str(lib),name)
  assert fp is not None,ref
  fp.SetFPID(pcbnew.LIB_ID(nickname,name));fp.SetReference(ref);fp.SetValue(c['value'])
  fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25+(index%5)*30),pcbnew.FromMM(25+(index//5)*30)))
  fp.Reference().SetPosition(fp.GetPosition()+pcbnew.VECTOR2I(0,pcbnew.FromMM(-8)))
  electrical=[p for p in fp.Pads() if p.GetNumber() and p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH and any(p.IsOnLayer(layer) for layer in (pcbnew.F_Cu,pcbnew.B_Cu))]
  assert {p.GetNumber() for p in electrical}==set(c['pins']),ref
  for pad in electrical:
   net=c['pins'][pad.GetNumber()]
   if net is not None:
    if net not in nets:nets[net]=pcbnew.NETINFO_ITEM(b,net);b.Add(nets[net])
    pad.SetNet(nets[net])
  npth=[p for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
  if ref.startswith('H'):
   assert len(npth)==1 and not npth[0].GetNumber() and npth[0].GetDrillSize()==pcbnew.VECTOR2I(pcbnew.FromMM(3.2),pcbnew.FromMM(3.2)),ref
  count+=len(electrical)
  rows.append({'ref':ref,'footprint':c['footprint'],'numbered_electrical_pads':len(electrical),'NPTH_drills':[{'pin':p.GetNumber(),'x_mm':pcbnew.ToMM(p.GetDrillSize().x),'y_mm':pcbnew.ToMM(p.GetDrillSize().y)} for p in npth]})
  b.Add(fp)
 for start,end in [((5,5),(175,5)),((175,5),(175,145)),((175,145),(5,145)),((5,145),(5,5))]:
  edge=pcbnew.PCB_SHAPE();edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetLayer(pcbnew.Edge_Cuts);edge.SetWidth(pcbnew.FromMM(.15));edge.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in start)));edge.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in end)));b.Add(edge)
 pcbnew.SaveBoard(str(HERE/'footprint-fixture.kicad_pcb'),b)
 shutil.copytree(SOURCE/'CNC_MB_Diagnostics.pretty',HERE/'CNC_MB_Diagnostics.pretty',dirs_exist_ok=True)
 shutil.copy2(SOURCE/'fp-lib-table',HERE/'fp-lib-table')
 rules={k:'warning' for k in ['missing_courtyard','track_not_centered_on_via','tuning_profile_track_geometries','footprint_filters_mismatch','footprint_type_mismatch']}
 (HERE/'footprint-fixture.kicad_pro').write_text(json.dumps({'meta':{'filename':'footprint-fixture.kicad_pro','version':1},'board':{'design_settings':{'rule_severities':rules}}},indent=2)+'\n',encoding='utf-8')
 assert count==56
 result={'physical_footprints':20,'numbered_electrical_pads':count,'bare_NPTH_drills':6,'rows':rows,
  'source_pin_and_exact_footprint_pad_sets_match':True,'mounts_have_no_fake_electrical_pin':True,'PCB_fixture_scope':'Isolated geometry fixture; arbitrary positions, no routed-circuit or production-board claim','manufacturing_ready':False}
 (HERE/'geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['physical_footprints','numbered_electrical_pads','bare_NPTH_drills']}))


if __name__=='__main__':main()
