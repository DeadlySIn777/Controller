"""Independent actual eight-channel ISO1212 topology and local-layout checks.

TI ISO1212 SLLSEY7G page31 Figures8-17/18: the external RTHR pad stays
at least4mm from protected device/CIN/RSENSE pads; its internal pad feeds
SENSE before RSENSE bridges SENSE/IN. The logic bypass belongs on the device
side within2mm of VCC. This is source/layout inspection, not EMC qualification.
"""
import argparse,json,math
from pathlib import Path
import pcbnew

CHANNELS=(
 ('U14031','R14069','R14070','R14071',None,16,15,14,13,4),
 ('U14031','R14072','R14073','R14074',None,11,10,9,12,5),
 ('U19001','R19001','R19002','R19003','C19001',16,15,14,13,4),
 ('U19001','R19004','R19005','R19006','C19002',11,10,9,12,5),
 ('U19002','R19007','R19008','R19009','C19004',16,15,14,13,4),
 ('U19002','R19010','R19011','R19012','C19005',11,10,9,12,5),
 ('U19003','R19013','R19014','R19015','C19007',16,15,14,13,4),
 ('U19003','R19016','R19017','R19018','C19008',11,10,9,12,5))
BYPASS=(('U14031','C14058'),('U19001','C19003'),('U19002','C19006'),('U19003','C19009'))
def bbox(p):
 b=p.GetBoundingBox();return [pcbnew.ToMM(x)for x in (b.GetLeft(),b.GetTop(),b.GetRight(),b.GetBottom())]
def gap(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def check(board):
 errors=[];rows=[];fps={f.GetReference():f for f in board.GetFootprints()};subs=[]
 def pad(ref,pin):return next(p for p in fps[ref].Pads()if p.GetNumber()==str(pin))
 def ck(ok,message):
  if not ok:errors.append(message)
 def field_x(u,p):
  c=fps[u].GetPosition();a=math.radians(fps[u].GetOrientationDegrees());v=p.GetPosition()-c
  return v.x*math.cos(a)-v.y*math.sin(a)
 for u,thr,rs,bias,cin,sense,inp,fg,sub,out in CHANNELS:
  ps=pad(u,sense);pi=pad(u,inp);logic=pad(u,1);field=pad(u,fg)
  ck(pad(thr,2).GetNetCode()==ps.GetNetCode(),'RTHR must feed SENSE '+thr)
  ck({pad(rs,1).GetNetCode(),pad(rs,2).GetNetCode()}=={ps.GetNetCode(),pi.GetNetCode()},'RSENSE must bridge SENSE/IN '+rs)
  ck(pad(bias,1).GetNetCode()==pad(u,out).GetNetCode()and pad(bias,2).GetNetCode()==logic.GetNetCode(),'Actual output bias topology '+bias)
  ck(logic.GetNetCode()!=field.GetNetCode(),'Field and logic returns must stay distinct '+u)
  ck(pad(u,9).GetNetCode()==pad(u,14).GetNetCode(),'Paired own field returns '+u)
  ck(pad(u,1).GetNetCode()==pad(u,8).GetNetCode(),'Paired own logic returns '+u)
  refs=[u,rs]+([cin]if cin else [])
  minimum=min((gap(bbox(pad(thr,1)),bbox(p)),ref,p.GetNumber())for ref in refs for p in fps[ref].Pads()if p.GetNumber())
  ck(minimum[0]>=4.,'Actual external RTHR pad needs4mm protected spacing '+thr)
  ck(all(field_x(u,p)>0 for p in fps[rs].Pads()if p.GetNumber()),'RSENSE must remain on own field side '+rs)
  ck(all(field_x(u,p)<0 for p in fps[bias].Pads()if p.GetNumber()),'Output bias must remain on own logic side '+bias)
  if cin:
   ck(pad(cin,1).GetNetCode()==ps.GetNetCode()and pad(cin,2).GetNetCode()==field.GetNetCode(),'CIN must return to own field domain '+cin)
   ck(all(field_x(u,p)>0 for p in fps[cin].Pads()if p.GetNumber()),'CIN must remain on own field side '+cin)
  subs.append(pad(u,sub).GetNetCode())
  rows.append(dict(IC=u,RTHR=thr,RSENSE=rs,CIN=cin,external_to_protected_pad_gap_mm=minimum[0]))
 ck(len(set(subs))==8,'Eight independent floating SUB thermal islands must not join')
 bypass=[]
 for u,c in BYPASS:
  cp=pad(c,1);vp=pad(u,2);ground=pad(c,2)
  ck(cp.GetNetCode()==vp.GetNetCode()and ground.GetNetCode()==pad(u,1).GetNetCode(),'Exact own VCC/return bypass topology '+c)
  d=(cp.GetPosition()-vp.GetPosition()).EuclideanNorm()/1e6
  ck(d<=2.,'Actual VCC bypass terminal needs2mm maximum '+c)
  ck(fps[u].GetLayer()==fps[c].GetLayer(),'VCC bypass must be on its own IC side '+c)
  bypass.append(dict(IC=u,bypass=c,actual_positive_to_VCC2_mm=d,same_device_side=fps[u].GetLayer()==fps[c].GetLayer()))
 return dict(ok=not errors,errors=errors,channels=rows,bypasses=bypass,
  source_inspection=True,native_DRC_run_by_this_check=False,return_continuity_qualified=False,
  physical_EMC_timing_thresholds_qualified=False,manufacturing_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 r=check(pcbnew.LoadBoard(str(a.board)));a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(ok=r['ok'],errors=r['errors'],channels=8,bypasses=4)));raise SystemExit(not r['ok'])
