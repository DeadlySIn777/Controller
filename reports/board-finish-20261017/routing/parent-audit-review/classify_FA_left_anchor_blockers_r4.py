"""Identify the exact extra historical versus current constraints on FA anchors."""
import sys,os
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json,pickle,hashlib,runpy,math
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;ROOT=H.parents[3];PRIOR=H/'FA-existing-In3-no-new-hole-source-floor-route-r3';OUT=H/'FA-left-anchor-blocker-classification-r4';T=runpy.run_path(str(H/'triage_reference_current_causal_geometry_r1.py'));NET='/motherboard_power_entry/FA_SHDN_CONTACT';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();mf=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-model.pkl';h=pickle.loads(mf.read_bytes());rec,trees=T['build'](h,{r['UUID']for r in json.loads(T['NPTH'].read_bytes())if r['IsNPTHWithNoCopper']});domain=h['domains_normalized'][NET];floors=[from_wkb((PRIOR/(n+'-actual-source-FG-In4-floor.wkb')).read_bytes())for n in('R157','R299')];old=next(t for t in h['tracks']if t['uuid']=='1f10d7d8-3a00-47cf-8498-260c300495d6');axis=LineString([old['a'],old['b']]);rows=[]
 for i in range(1,40):
  q=axis.interpolate(i/40,normalized=True);body=q.buffer(.100002/math.cos(math.pi/(4*512)),quad_segs=512);bad=[]
  for j in trees['In3.Cu'].query(q.buffer(1)):
   r=rec['In3.Cu'][int(j)]
   if T['norm'](r['raw_net'])==NET:continue
   gap=q.distance(r['shape'])-r['radius']-.1-(.005 if r['kind']=='pad'else 0);req=max(.175 if h['domains_normalized'].get(T['norm'](r['raw_net']))==domain else .625,float(r['data'].get('clearance_mm',0))+.025)
   if gap<req:bad.append({'kind':r['kind'],'UUID':r['UUID'],'raw_net':r['raw_net'],'gap_mm':gap,'required_mm':req})
  rows.append({'fraction':i/40,'point_mm':[q.x,q.y],'R157_old_FG_full_new_outward_cap_covered':floors[0].covers(body),'R299_actual_current_FG_full_new_outward_cap_covered':floors[1].covers(body),'foreign_Cu_guard_errors':bad})
 (OUT/'all39-left-anchor-probes.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8');print(json.dumps({'R157_covered':sum(r['R157_old_FG_full_new_outward_cap_covered']for r in rows),'R299_covered':sum(r['R299_actual_current_FG_full_new_outward_cap_covered']for r in rows),'current_and_Cu_clear':sum(r['R299_actual_current_FG_full_new_outward_cap_covered']and not r['foreign_Cu_guard_errors']for r in rows),'input_SHA256':{str(f):sha(f)for f in(Path(__file__),mf,PRIOR/'R157-actual-source-FG-In4-floor.wkb',PRIOR/'R299-actual-source-FG-In4-floor.wkb')}}))
if __name__=='__main__':main()
