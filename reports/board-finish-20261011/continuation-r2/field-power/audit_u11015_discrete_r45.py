"""Independent all-discrete clearance/aperture check for scoped R32 proposal."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
P=Path(__file__).resolve().parent;OUT=P/'u11015-r44-independent-discrete-audit-r45'
def main():
 assert not OUT.exists();OUT.mkdir();bp=P/'local-and-b5-return-audit-r25';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'discrete.pkl')==br['discrete_sha256'];h=pickle.loads((bp/'discrete.pkl').read_bytes());q=P/'u11015-reverse-companion-repair-r44';r=json.loads((q/'receipt.json').read_text());assert sha(q/'proposed-discrete.pkl')==r['proposed_discrete_sha256'];d=pickle.loads((q/'proposed-discrete.pkl').read_bytes());remove={t['uuid'] for t in r['owned_original_track_removals']};h={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in remove]+d['tracks'],'vias':h['vias']+d['vias']};rec,trees=F.build({**h,'zones':[]});smd=[unary_union(C.poly(rs)) for p0 in h['pads'] if p0['smd'] for l,rs in p0['layers'].items() if l in('F.Cu','B.Cu')];st=STRtree(smd);ph=[sh for p0 in h['pads'] for sh in C.poly(p0.get('hole') or [])];ht=STRtree(ph);fail=[]
 for v in d['vias']:
  p0=Point(v['x'],v['y']);disk=p0.buffer(v['d']/2,quad_segs=32)
  for j in st.query(p0.buffer(v['drill']/2+.276),predicate='intersects'):
   dist=p0.distance(smd[int(j)])-v['drill']/2
   if dist<.275-1e-9:fail.append({'kind':'SMD_APERTURE','uuid':v['uuid'],'gap_mm':dist})
  for j in ht.query(p0.buffer(v['drill']/2+.276),predicate='intersects'):
   dist=p0.distance(ph[int(j)])-v['drill']/2
   if dist<.275-1e-9:fail.append({'kind':'PAD_HOLE','uuid':v['uuid'],'gap_mm':dist})
  for w in h['vias']:
   if w['uuid']==v['uuid']:continue
   dist=math.hypot(v['x']-w['x'],v['y']-w['y'])-(v['drill']+w['drill'])/2
   if dist<.275-1e-9:fail.append({'kind':'VIA_DRILL','uuid':v['uuid'],'other_UUID':w['uuid'],'gap_mm':dist})
  for l in v['flashed']:
   for j in trees[l].query(disk.buffer(.626),predicate='intersects'):
    w=rec[l][int(j)]
    if w['net']==v['net']:continue
    req=(.15 if w['domain']==h['domains_normalized'][C.norm(v['net'])] else .6)+.025;dist=disk.distance(w['shape'])
    if dist<req-1e-7:fail.append({'kind':'VIA_CU','uuid':v['uuid'],'layer':l,'other_UUID':w['uuid'],'other_raw_net':w['net'],'gap_mm':dist,'required_mm':req})
 for t in d['tracks']:
  sh=C.body(t);l=t['layer'];dom=h['domains_normalized'][C.norm(t['net'])]
  for j in trees[l].query(sh.buffer(.626),predicate='intersects'):
   w=rec[l][int(j)]
   if w['net']==t['net']:continue
   req=(.15 if w['domain']==dom else .6)+.025;dist=sh.distance(w['shape'])
   if dist<req-1e-7:fail.append({'kind':'SEGMENT_CU','uuid':t['uuid'],'layer':l,'other_UUID':w['uuid'],'other_raw_net':w['net'],'gap_mm':dist,'required_mm':req})
 receipt={'verdict':'PASS_DISCRETE_ONLY_OTHER_GATES_OPEN' if not fail else 'REJECT_DISCRETE_CLEARANCE','violations':fail,'input_r25_receipt_SHA256':sha(bp/'receipt.json'),'input_R44_receipt_SHA256':sha(q/'receipt.json'),'new_vias':len(d['vias']),'new_tracks':len(d['tracks']),'explicit_owned_removed_original_tracks':sorted(remove),'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=1))
if __name__=='__main__':main()
