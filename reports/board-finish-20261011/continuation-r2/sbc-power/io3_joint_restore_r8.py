"""Restore every original IO3 physical contact group in the coupled proposal."""
import json,hashlib,math,pickle,time
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import io3_contact_restore_r2 as Q
import continuous_path_r2 as CP
L=G.L;p=G.p;R=G.B.J.R;NET='/IO_3V3'
def main():
    g,h,tail,binding,zones=G.model(True,True,'r7');candidate,cuts=G.projected(g,h,zones);Q.NET=NET;before,bparts,bassign=Q.groups(g,return_details=True);after,aparts,aassign=Q.groups(candidate,return_details=True);ai={r['uuid']:i for i,group in enumerate(after) for r in group};mainold=max(before,key=lambda xs:sum(not r['ref'].startswith('@') for r in xs));oldids={q['uuid'] for q in mainold};counts={i:sum(r['uuid'] in oldids for r in group) for i,group in enumerate(after)};root=max(counts,key=counts.get);detached=sorted(i for i,n in counts.items() if n and i!=root);print('IO3_COUPLED_PARTITIONS',root,len(detached),[(i,counts[i]) for i in detached],flush=True)
    source=unary_union([q for q,j in zip(aparts['In2.Cu'],aassign['In2.Cu']) if j==root]);out=L.OUT/'coupled-power-geometry-frozen-r8';out.mkdir(exist_ok=True);core=next(q['shape'] for q in zones if q['label']=='CORE-main-In2');fingers=[];fail=[];p.WINDOW=box(.526,.526,449.474,229.474);free=R.free_layer(candidate,NET,'In2.Cu',p.WINDOW,(L.stage.caps.CORE,),reference_guard=None,allow_own_via_connection=True)
    for group in detached:
        target=unary_union([q for q,j in zip(aparts['In2.Cu'],aassign['In2.Cu']) if j==group]);found=None
        for width in (1.25,1.,.75,.5,.35):
            centre=free.buffer(-width/2);options=[]
            for part in p.hubs.components(centre):
                a=part.intersection(source);b=part.intersection(target)
                if a.is_empty or b.is_empty:continue
                aa,bb=nearest_points(a,b);options.append((aa.distance(bb),part,aa.coords[0],bb.coords[0]))
            if not options:continue
            for _,part,aa,bb in sorted(options,key=lambda q:q[0]):
                route=CP.path(part,aa,bb,node_cap=250000)
                if route['verdict']!='HOST_PATH':continue
                sh=set_precision(LineString(route['points']).buffer(width/2).intersection(free),1e-6)
                if sh.intersection(source).is_empty or sh.intersection(target).is_empty:continue
                found=width,route,sh;break
            if found:break
        if not found:fail.append({'candidate_group':group,'contacts':[q for q in after[group] if q['uuid'] in oldids]});print('IO3_COUPLED_NO_PATH',group,flush=True);continue
        width,route,sh=found;f=out/('IO3-joint-restoration-'+str(group)+'.wkb');f.write_bytes(sh.wkb);fingers.append({'candidate_group':group,'old_contacts':[q for q in after[group] if q['uuid'] in oldids],'width_mm':width,'route':route,'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':sh.area});source=source.union(sh).union(target);core=core.difference(sh.buffer(.175));print('IO3_COUPLED_RESTORED',group,width,route['length_mm'],flush=True)
    # Retain all original micro-copper, including plane-only branches, when the
    # newly drawn CORE layer changes around a restored finger.
    micros=[]
    for z in g['zones']:
        if p.norm(z['net'])!=NET:continue
        for poly in p.base.polygons(z['fills'].get('In2.Cu',[])):
            for sh in p.hubs.components(poly):
                if sh.area<=.05 and sh.intersects(core):micros.append(sh)
    core=set_precision(core.difference(unary_union(micros).buffer(.2)),1e-6);rows=[]
    for z in zones:
        sh=core if z['label']=='CORE-main-In2' else z['shape'];f=out/(z['label']+'.wkb');f.write_bytes(sh.wkb);rows.append({'label':z['label'],'uuid':z['uuid'],'net_raw':z['net'],'layer':z['layer'],'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':sh.area,'field_return_proposal':bool(z.get('field_return_proposal'))})
    for i,row in enumerate(fingers):rows.append({'label':'IO3-joint-restoration-'+str(row['candidate_group']),'uuid':'prospective-IO3-joint-restoration-'+str(row['candidate_group']),'net_raw':NET,'layer':'In2.Cu',**{k:row[k] for k in ('geometry_file','sha256','area_mm2')}})
    result={'verdict':'COUPLED_IO3_RESTORATION_CONSTRUCTION_ONLY' if not fail else 'COUPLED_IO3_RESTORATION_INCOMPLETE','exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'zones':rows,'IO3_restoration_fingers':fingers,'IO3_unresolved_contact_groups':fail,'baseline_main_original_contacts':len(mainold),'initial_detached_contact_groups':detached,'all_original_IO3_pad_track_barrel_and_plane_native_guards_required':True,'full_current_reference_and_native_gates_open':True,'native_jobs':0,'board_written':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('IO3_COUPLED_RECIPE',len(fingers),len(fail),flush=True)
if __name__=='__main__':main()
