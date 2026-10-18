"""Apply the bounded IO3 source correction to the routed 880-part snapshot.

Only reviewed local stubs/lands change. The public IO3 and GND planes retain
their identities; no global-net reassignment is allowed. This creates a
checked intermediate for additive population, not fabrication outputs.
"""
import argparse,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import ROOT,REPORT,CLI,sha,load,write,native_parts_and_nets
from hardware_route_logic_return import identity,pad_identity,xy,mm

BASE_SHA='5186e1b6578869505f19b17fee5e531ac132d14dec05eef8df1e09d5b785f5bb'
LOCAL='/mc_local_power/IO_3V3_REG_LOCAL'
LOCAL_TRACKS={
 '6de66f0f-d2dc-401a-9abe-4389982355e9',
 'df90da34-91fe-4017-aec0-41d3e5e4835e',
 'c06f90ac-ac39-469a-9ae4-069b5026ac34',
 '6d92c15b-4351-418f-8916-d50532c67a38'}
REMOVE={
 # VOS-to-public-plane escape: local VOS must sense before R18001.
 '208b7181-b684-4dd6-937e-bbf50e1f281f':'/IO_3V3',
 '42948703-9430-40e1-9314-dde1ee1bb5e1':'/IO_3V3',
 # R2069 now enters the real 698-ohm series resistor.
 'd186ff38-bf6d-45ce-bf17-3698b0d19810':'/IO_3V3',
 '68d953d9-9833-42c8-856e-0bb0c035f85a':'/IO_3V3',
 # MODE is now tied to VIN, not ground.
 '012ff836-e4b3-45dd-a707-84ed4124afcf':'/LOGIC_GND',
 '00cf2c11-ebf7-4850-8be0-734746be476a':'/LOGIC_GND',
 # Move the local 100-nF reservoir from the distant monitor to the regulator.
 'ef7b87de-2fb4-4778-a23d-270bd91447fe':'/IO_3V3',
 'a9f6120e-2a8b-4e9c-b9bc-447a3ca7b09e':'/IO_3V3',
 'bbd3e588-e7ae-40fd-9b69-c639dd33df93':'/LOGIC_GND',
 'd7bf5ebd-540e-4abd-a3d1-f6deedfa8899':'/LOGIC_GND'}
ENDPOINTS={
 **{(r,p):LOCAL for r,p in [('U2002','3'),('L2002','2'),('C2005','1'),('C2010','1')]},
 ('R2005','2'):'/mc_local_power/CORE_5V',
 ('R2069','1'):'/mc_local_power/IO_3V3_OV_SERIES_MC_R2069',
 **{(r,'1'):'/motherboard_motor_power/IO_3V3_OV_SERIES_MOTOR_'+r for r in ['R9007','R9017']}}
VALUE_REFS={'U2002','R2005','R2008','R2061','R2069','R9005','R9015','R9007','R9017'}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--board',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 a=p.parse_args();base=a.board.resolve();source=a.source.resolve();out=a.out.resolve()
 if out.exists() or not out.is_relative_to(REPORT):raise ValueError('Fresh owned report directory required')
 if sha(base)!=BASE_SHA:raise ValueError('Unknown routed baseline: no wildcard copper edits')
 model=load(source/'design.json');parts=model['components'];_,nodes=native_parts_and_nets(source/'netlist.xml',parts)
 inputs={str(f):sha(f) for f in [base,source/'design.json',source/'netlist.xml',Path(__file__)]}
 b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
 old_tracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
 old_pads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in b.GetPads() if q.GetNumber() and q.IsOnCopperLayer()}
 old_zones={z.m_Uuid.AsString():(z.GetNetname(),z.GetLayer(),z.Outline().Format()) for z in b.Zones()}
 nets={str(n.GetNetname()):n for n in b.GetNetsByName().values()};code=max(n.GetNetCode() for n in nets.values())+1
 for name in sorted(set(ENDPOINTS.values())-set(nets)):
  n=pcbnew.NETINFO_ITEM(b,name,code);b.Add(n);nets[name]=n;code+=1
 edits=[]
 for key,wanted in ENDPOINTS.items():
  if nodes.get(key)!=wanted:raise ValueError('Native source power topology differs '+repr(key))
  pad=next(q for q in fps[key[0]].Pads() if q.GetNumber()==key[1]);old=pad.GetNetname()
  expected='/LOGIC_GND' if key==('R2005','2') else '/IO_3V3'
  if old!=expected:raise ValueError('Unexpected original power pad '+repr(key))
  edits.append(dict(reference=key[0],pin=key[1],old_native_net=old,new_native_net=wanted))
  pad.SetNet(nets[wanted])
 tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
 if not LOCAL_TRACKS|set(REMOVE)<=set(tracks):raise ValueError('Reviewed power copper missing')
 copper_edits=[]
 for uid in LOCAL_TRACKS:
  t=tracks[uid]
  if t.GetNetname()!='/IO_3V3' or isinstance(t,pcbnew.PCB_VIA):raise ValueError('Unexpected local reservoir item')
  copper_edits.append(dict(uuid=uid,before=old_tracks[uid],action='reassign existing local copper to upstream regulator node'))
  t.SetNet(nets[LOCAL])
 for uid,name in REMOVE.items():
  if tracks[uid].GetNetname()!=name:raise ValueError('Unexpected dedicated old stub '+uid)
  copper_edits.append(dict(uuid=uid,before=old_tracks[uid],action='remove obsolete dedicated escape; no shared branch removed'))
  b.Remove(tracks[uid])
 # The original fitted cap belongs to the local reservoir, not the downstream
 # distributed plane. Preserve its footprint/pads/UUID, move it next to C2005.
 cap=fps['C2010'];before_position=mm(cap.GetPosition());cap.SetPosition(xy((43.3,24.5)))
 for ref in VALUE_REFS:fps[ref].SetValue(parts[ref]['value'])
 def track(points,net,width):
  for start,end in zip(points,points[1:]):
   t=pcbnew.PCB_TRACK(b);t.SetNet(nets[net]);t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(start));t.SetEnd(xy(end));t.SetWidth(pcbnew.FromMM(width));b.Add(t)
 track([(42.525,24.5),(42.525,22.55),(40.5,22.55)],LOCAL,.3)
 track([(44.075,24.5),(44.825,24.5)],'/LOGIC_GND',.3)
 v=pcbnew.PCB_VIA(b);v.SetPosition(xy((44.825,24.5)));v.SetNet(nets['/LOGIC_GND']);v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(True);b.Add(v)
 out.mkdir(parents=True);dest=out/'power-reconciled-880.kicad_pcb'
 for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
 for folder in base.parent.iterdir():
  if folder.is_dir() and (folder.name.endswith('.pretty') or folder.name=='3dmodels'):shutil.copytree(folder,out/folder.name)
 if (base.parent/'fp-lib-table').is_file():shutil.copyfile(base.parent/'fp-lib-table',out/'fp-lib-table')
 pcbnew.SaveBoard(str(dest),b)
 run=subprocess.run([str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
 (out/'drc-command.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native DRC process failed')
 data=load(out/'drc.json');r=pcbnew.LoadBoard(str(dest));r.BuildConnectivity()
 after_tracks={t.m_Uuid.AsString():identity(t) for t in r.GetTracks()}
 after_pads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in r.GetPads() if q.GetNumber() and q.IsOnCopperLayer()}
 errors=[]
 for uid,before in old_tracks.items():
  if uid in REMOVE:
   if uid in after_tracks:errors.append('Obsolete dedicated copper retained '+uid)
  elif uid in LOCAL_TRACKS:
   if after_tracks.get(uid)!=tuple([before[0],LOCAL,*before[2:]]):errors.append('Local copper geometry differs '+uid)
  elif after_tracks.get(uid)!=before:errors.append('Unrelated retained copper changed '+uid)
 for key,before in old_pads.items():
  after=after_pads[key]
  if key[0]=='C2010':continue
  wanted=tuple([ENDPOINTS.get(key,before[0]),*before[1:]])
  if after!=wanted:errors.append('Unrelated retained pad changed '+repr(key))
 if {z.m_Uuid.AsString():(z.GetNetname(),z.GetLayer(),z.Outline().Format()) for z in r.Zones()}!=old_zones:errors.append('Retained public plane outline/net changed')
 for f in r.GetFootprints():
  if f.GetReference() in VALUE_REFS and f.GetValue()!=parts[f.GetReference()]['value']:errors.append('Power value did not reconcile')
 # No public pad may share an actual electrical cluster with the upstream
 # node while R18001 is absent from this intermediate.
 fpmap={f.GetReference():f for f in r.GetFootprints()}
 sense=next(q for q in fpmap['U2002'].Pads() if q.GetNumber()=='3')
 upstream={t.m_Uuid.AsString() for t in r.GetConnectivity().GetConnectedItems(sense)}
 public=[q for q in r.GetPads() if q.GetNetname()=='/IO_3V3']
 if any(q.m_Uuid.AsString() in upstream for q in public):errors.append('Upstream IO3 bypassed into public plane')
 if data['violations'] or data.get('ignored_checks'):errors.append('Native geometry DRC not clean')
 if any(sha(Path(f))!=h for f,h in inputs.items()):errors.append('Source changed during reconciliation')
 receipt=dict(ok=not errors,errors=errors,source_hashes=inputs,board_sha256=sha(dest),
  exact_power_pad_changes=edits,exact_copper_edits=copper_edits,
  cap_relocation=dict(reference='C2010',before_mm=before_position,after_mm=[43.3,24.5],reason='actual local regulator reservoir'),
  component_value_updates={ref:parts[ref]['value'] for ref in sorted(VALUE_REFS)},
  retained_copper_items=len(old_tracks)-len(REMOVE),total_track_via_items=len(after_tracks),
  regular_drc_violations=len(data['violations']),ignored_checks=data.get('ignored_checks',[]),
  uncapped_missing_joins=r.GetConnectivity().GetUnconnectedCount(False),upstream_public_plane_bypass=False,
  manufacturing_ready=False,scope='Bounded local IO3 copper correction; damping/FB/window parts populated next; full power/return/current qualification remains')
 write(out/'receipt.json',receipt);print(json.dumps({k:receipt[k] for k in ['ok','errors','regular_drc_violations','total_track_via_items','uncapped_missing_joins']}))
 if errors:raise ValueError('Power copper reconciliation checks failed')

if __name__=='__main__':main()
