"""Attribute exact current XF endpoint failure before another route screen."""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point
OUT=H/'XF-current-bare-pad-exact-source-and-clearance-attribution-r612';NET='/motherboard_operator/XF_REQUEST_BUFFER';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());cf=pin(H/'XF-current-no-via-F-actual-J1-reference-path-r608/exact-current-source-and-hard-F-regions-NOMINATION_ONLY.pkl');cache=pickle.loads(cf.read_bytes());source=cache['source'];free=cache['free'];rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];holes,_=K.hole_context(h);rows=[]
 for uid in('a0011950-a497-4019-b265-c0ce2da0a4fe','d9a84fa6-7211-4e66-bbd7-bb0d180d00a8'):
  p=next(p for p in h['pads']if p['uuid']==uid);pt=Point(p['x'],p['y']);disk=pt.buffer(.105005,quad_segs=128);bad=[]
  for i in trees['F.Cu'].query(pt.buffer(1),predicate='intersects'):
   r=rec['F.Cu'][int(i)]
   if K.L.norm(r['net'])==NET:continue
   req=.15 if dom[K.L.norm(r['net'])]==dom[NET]else .6;distance=pt.distance(r['shape']);limit=req+.025+.105
   if distance<limit:bad.append({'kind':r['kind'],'UUID':r['uuid'],'net':r['net'],'point_distance_mm':distance,'planned_centre_requirement_mm':limit})
  nearholes=[{'point_distance_mm':pt.distance(sh),'requirement_mm':.380}for sh in holes if pt.distance(sh)<.380];missing=disk.difference(source);file=OUT/(p['ref']+'-'+str(p['num'])+'-actual-reference-disk-gap.wkb');file.write_bytes(missing.wkb);rows.append({'ref':p['ref'],'pin':str(p['num']),'UUID':uid,'at_mm':[p['x'],p['y']],'actual_current_SOURCE_In1_covers_point':source.covers(pt),'actual_current_SOURCE_In1_disk_gap':info(missing),'source_distance_mm':pt.distance(source),'R608_combined_legal_reference_F_covers_point':free.covers(pt),'hard_foreign_F_endpoint_clearance_blockers':bad,'drill_endpoint_blockers':nearholes,'raw_gap_file':str(file.resolve())});print('R612_PAD',p['ref'],p['num'],'sourcepoint',source.covers(pt),'gap',missing.area,'foreign',len(bad),'holes',len(nearholes),flush=True)
 (OUT/'receipt.json').write_text(json.dumps({'verdict':'EXACT_CURRENT_BARE_XF_ENDPOINT_FAILURE_ATTRIBUTED_NO_WAIVER','input_SHA256':pins,'rows':rows,'native_jobs':0,'old_copper_or_plane_changed':0,'adopted':False,'constructive_routing_source_native_current_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R612_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
