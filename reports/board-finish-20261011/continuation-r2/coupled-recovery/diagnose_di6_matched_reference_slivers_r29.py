"""Localize the exact three R27 matched-native residuals without waiver."""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import physical_reference_losses_r2 as RF
from shapely.geometry import Point
from shapely.ops import unary_union
C=A.C
def main():
 started=time.monotonic();out=HERE/'di6-matched-native-sliver-diagnostic-r29.json';assert not out.exists();A.read(__file__);rpath=HERE/'di6-matched-actual-native-independent-r27.json';r=json.loads(A.read(rpath));assert C.sha(A.read(rpath))=='c56ae1566e40cd7d385ba790873d24645bd4b36719900dc5ca3ddec320acd8b8';raw=A.read(r['saved_matched_actual_model']);assert C.sha(raw)==r['saved_matched_actual_model_sha256'];m=pickle.loads(raw);before=m['before'];after=m['after'];br=m['before_refs'];ar=m['after_refs'];native={}
 for key,d in [('before','di6-matched-native-baseline-r1'),('after','di6-native-diagnostic-r1')]:
  p=HERE.parent/d/'scoped-native-fill/geometry.json';native[key]=json.loads(A.read(p))
 pieces={l:RF.parts(br[l].difference(ar[l])) for l in br};folder=HERE/'di6-matched-native-r29-slivers';folder.mkdir();rows=[]
 newids={q['UUID'] for q in json.loads(A.read(HERE/'di6-actual-native-reference-independent-r19.json'))['exact_new_native_discrete']};newvia=[v for v in after['vias'] if v['uuid'] in newids];newtrack=[t for t in after['tracks'] if t['uuid'] in newids]
 for loss in r['all_retained_neighbor_reference_losses']:
  t=next(t for t in before['tracks'] if t['uuid']==loss['uuid']);l=t['layer'];plane='In1.Cu' if l=='F.Cu' else'In4.Cu';body=A.shape({'kind':'segment',**t});delta=unary_union([p for p in pieces[l] if p.intersects(body.envelope.buffer(1e-9))]);gap=body.intersection(delta);assert abs(gap.area-loss['prior_source_reference_lost_mm2'])<1e-18;gp=folder/(t['uuid']+'.wkb');gp.write_bytes(gap.wkb);local=gap.envelope.buffer(.01);zg={}
  for key,ng in native.items():
   zs=[z for z in ng['zones'] if L.norm(z['net'])=='/LOGIC_GND'];parts=[];selected=[]
   for z in zs:
    for sh in L.poly(A.polys(z['fills'].get(plane,[]))):
     if sh.intersects(local):parts.append(sh.intersection(local));selected.append(z['uuid'])
   zg[key]={'shape':unary_union(parts),'zone_UUIDs':sorted(set(selected))}
  native_loss=zg['before']['shape'].difference(zg['after']['shape']);native_gain=zg['after']['shape'].difference(zg['before']['shape']);row={**loss,'exact_track':t,'reference_plane':plane,'loss_bounds_mm':gap.bounds,'loss_WKB_path':str(gp),'loss_WKB_sha256':C.sha(gap.wkb),'loss_max_bbox_dimension_mm':max(gap.bounds[2]-gap.bounds[0],gap.bounds[3]-gap.bounds[1]),'nearest_new_via_distance_mm':min(gap.distance(Point(v['x'],v['y'])) for v in newvia),'nearest_new_track_body_distance_mm':min(gap.distance(A.shape({'kind':'segment',**t})) for t in newtrack),'matched_native_local_fill_UUIDs_before':zg['before']['zone_UUIDs'],'matched_native_local_fill_UUIDs_after':zg['after']['zone_UUIDs'],'matched_native_direct_unrooted_local_fill_loss_mm2':native_loss.area,'matched_native_direct_unrooted_local_fill_gain_mm2':native_gain.area,'full_loss_within_direct_native_polygon_loss':gap.difference(native_loss).area<=1e-18,'matching_old_drill_geometries':[]}
  for v in before['vias']:
   dist=gap.distance(Point(v['x'],v['y']));
   if dist<=v['d']/2+.7:row['matching_old_drill_geometries'].append({'UUID':v['uuid'],'at':[v['x'],v['y']],'net':v['net'],'d':v['d'],'drill':v['drill'],'gap_distance_to_center_mm':dist})
  rows.append(row)
 report={'verdict':'MATCHED_NATIVE_REFERENCE_SLIVERS_EXACT_LOCAL_DIAGNOSTIC_NOT_WAIVED','R27_sha256':C.sha(A.read(rpath)),'rows':rows,'all_complete_delta_piece_areas_and_bounds':{l:[{'area_mm2':p.area,'bounds_mm':p.bounds,'WKB_sha256':C.sha(p.wkb)} for p in ps] for l,ps in pieces.items()},'native_reference_source_root_gate':'R27 root connectivity retained; this local polygon diagnosis does not grant a new source qualification or threshold waiver','read_files_sha256':A.READS,'native_jobs':0,'board_written':False,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'rows':rows}),flush=True)
if __name__=='__main__':main()
