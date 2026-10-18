"""Find source-floor-supported anchors anywhere on the two retained FA branches."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import pickle,json,hashlib,runpy,time,math,gc
from shapely import from_wkb
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';OLD=ROOT/'reports/board-finish-20261011/continuation-r2';OUT=H/'FA-all-retained-In3-branch-anchors-r8';PRIOR=H/'FA-existing-In3-full-source-component-route-r7';CHAIN=ROOT/'reports/board-finish-20261017/power-review/field5-current-continuation/complete-existing-FA-via-to-via-F-chain-r14/receipt.json'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;NET='/motherboard_power_entry/FA_SHDN_CONTACT';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
 t=time.monotonic();assert not OUT.exists();OUT.mkdir();mf=P/'actual-combined-full-after-model.pkl';h=pickle.loads(mf.read_bytes());ch=json.loads(CHAIN.read_bytes());retired={r.get('UUID',r.get('uuid'))for r in ch['exact_retirement_operations']};h={**h,'tracks':[t for t in h['tracks']if t['uuid']not in retired]};uf,groups=K.physical(h,NET,K.hole_context(h));free=from_wkb((PRIOR/'search-only-free-centerline-area.wkb').read_bytes());pieces=[free]if free.geom_type=='Polygon'else list(free.geoms);bytrack={t['uuid']:t for t in h['tracks']};results=[]
 for gi,g in enumerate(groups):
  trackids={r['uuid']for r in g if r['kind']=='track'};anchors=[]
  for uid in sorted(trackids):
   tr=bytrack[uid]
   if tr['layer']!='In3.Cu'or tr.get('m'):continue
   axis=LineString([tr['a'],tr['b']])
   for i in range(1,40):
    q=axis.interpolate(i/40,normalized=True);pt=(round(q.x,6),round(q.y,6))
    for ci,piece in enumerate(pieces):
     if piece.contains(Point(pt)):anchors.append({'existing_track_UUID':uid,'point_mm':pt,'free_component':ci});break
  results.append({'group':gi,'layer_keys':len(K.keys(g)),'pads':sorted({(r['ref'],str(r['pin']))for r in g if r['kind']=='pad'}),'all_tracks_by_layer':{ly:sorted(uid for uid in trackids if bytrack[uid]['layer']==ly)for ly in K.LAYERS},'all_source_supported_guarded_In3_anchor_points':anchors})
 (OUT/'all-retained-branch-anchors.json').write_text(json.dumps(results,indent=1)+'\n',encoding='utf-8');matches=[]
 for a in results:
  for b in results:
   if a['group']>=b['group']or not a['pads']or not b['pads']:continue
   for x in a['all_source_supported_guarded_In3_anchor_points']:
    for y in b['all_source_supported_guarded_In3_anchor_points']:
     if x['free_component']==y['free_component']:matches.append({'a_group':a['group'],'b_group':b['group'],'a':x,'b':y,'straight_distance_mm':math.dist(x['point_mm'],y['point_mm'])})
 matches.sort(key=lambda r:r['straight_distance_mm']);(OUT/'same-continuous-free-component-anchor-pairs.json').write_text(json.dumps(matches[:100],indent=1)+'\n',encoding='utf-8');rec={'status':'RETAINED_FA_BRANCHES_HAVE_COMMON_GUARDED_SOURCE_FLOOR_COMPONENT_ANCHORS'if matches else'HELD_NO_RETAINED_FA_BRANCH_ANCHORS_SHARE_COMPLETE_CURRENT_SOURCE_FLOOR_FREE_COMPONENT','physical_after_F_retirement_groups':len(groups),'branches':[{'group':r['group'],'keys':r['layer_keys'],'pads':r['pads'],'In3_track_count':len(r['all_tracks_by_layer']['In3.Cu']),'F_track_count':len(r['all_tracks_by_layer']['F.Cu']),'B_track_count':len(r['all_tracks_by_layer']['B.Cu']),'In2_track_count':len(r['all_tracks_by_layer']['In2.Cu']),'guarded_In3_anchor_count':len(r['all_source_supported_guarded_In3_anchor_points']),'free_components':sorted({a['free_component']for a in r['all_source_supported_guarded_In3_anchor_points']})}for r in results],'matching_anchor_pairs':len(matches),'minwidth_and_return_reference_not_weakened':True,'native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),mf,CHAIN,PRIOR/'search-only-free-centerline-area.wkb')},'elapsed_seconds':time.monotonic()-t};(OUT/'receipt.json').write_text(json.dumps(rec,indent=1)+'\n',encoding='utf-8');print(json.dumps(rec))
if __name__=='__main__':main()
