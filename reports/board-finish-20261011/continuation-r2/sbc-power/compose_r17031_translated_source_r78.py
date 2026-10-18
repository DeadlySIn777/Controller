"""Explicit R17031 layout delta with analytic cuts and shared-contact check."""
import copy,json,pickle,hashlib
from pathlib import Path
from shapely import set_precision
from shapely.affinity import translate
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import core_inner_feed_r18 as I
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as TG
L=I.L;p=I.p;G=I.G;Q=I.Q;OUT=L.OUT/'r17031-translated-source-composition-r78'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def keep(f,s):f.write_bytes(s.wkb);return {'file':str(f.resolve()),'sha256':sha(f),'area_mm2':s.area}
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes())
    mf=L.OUT/'core-pocket-outward-round-guards-r69/model.pkl';assert sha(mf)=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff';g,h,b,z,oldc=pickle.loads(mf.read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b)
    nd=L.OUT/'r17031-coupled-native-mask-nominations-r74';nr=nd/'receipt.json';assert sha(nr)=='2bdfbb31ba0a99f9a90fdbae1128674f2e982a9e42f426bc87041a3021208c31';row=json.loads(nr.read_text())['rows'][0];d=pickle.loads((nd/'proposed-discrete.pkl').read_bytes());nz=pickle.loads((nd/'new-CORE-zones.pkl').read_bytes());assert len(d['vias'])==1 and len(d['tracks'])==5 and len(nz)==1
    dx,dy=row['translation_mm'];pose=[]
    for q in h['pads']:
        if q['ref']!='R17031':continue
        prior=copy.deepcopy(q);q['x']=round(q['x']+dx,6);q['y']=round(q['y']+dy,6);q['layers']={l:G.records(set_precision(translate(unary_union(p.base.polygons(rs)),dx,dy),1e-6)) for l,rs in q['layers'].items()};assert q['hole'] is None
        pose.append({'kind':'pad','uuid':q['uuid'],'raw_net':q['net'],'original_geometry':prior,'replacement_geometry':copy.deepcopy(q)})
    fp=next(q for q in h['footprints'] if q['ref']=='R17031');priorfp=copy.deepcopy(fp);fp['x']=row['target_FP_pose'][0];fp['y']=row['target_FP_pose'][1];fp['courtyard']={side:G.records(set_precision(translate(unary_union(p.base.polygons(rs)),dx,dy),1e-6)) for side,rs in fp['courtyard'].items()};pose.append({'kind':'footprint','ref':'R17031','original_geometry':priorfp,'replacement_geometry':copy.deepcopy(fp),'translation_mm':[dx,dy],'native_angle_deg_unchanged':0.})
    for kind in ('vias','tracks'):assert not {q['uuid'] for q in h[kind]}&{q['uuid'] for q in d[kind]};h[kind]+=d[kind]
    # First correct the new bridge's old/new foreign barrels and actual round
    # track endcaps. Every mutation gets its own geometry and round-cut ledger.
    vn,vl=GP.normalize_owned_via_guards(h,nz);nn,tl,tgeo=TG.normalize_owned_track_guards(h,vn)
    for ledger,before,after,name in [(vl,nz,vn,'new-plane-via'),(tl,vn,nn,'new-plane-track')]:
        by={q['uuid']:q for q in before};ay={q['uuid']:q for q in after}
        for rr in ledger:
            q=by[rr['zone_uuid']];a=ay[q['uuid']];rr['geometry_files']={n:keep(OUT/(q['uuid']+'.'+name+'-'+n+'.wkb'),s) for n,s in [('physical-before',q['shape']),('physical-after',a['shape']),('outline-before',q.get('zone_outline_shape',q['shape'])),('outline-after',a['zone_outline_shape'])]}
        write(OUT/(name+'-ledger.json'),ledger)
    # Explicit new-barrel cuts on all prior owned foreign shapes, with current
    # geometry (no stale replacement of the existing field-return proposals).
    zold=copy.deepcopy(z);z,oldvl=GP.normalize_owned_via_guards(h,z)
    by={q['uuid']:q for q in zold};ay={q['uuid']:q for q in z}
    for rr in oldvl:
        q=by[rr['zone_uuid']];a=ay[q['uuid']];rr['geometry_files']={n:keep(OUT/(q['uuid']+'.prior-via-'+n+'.wkb'),s) for n,s in [('physical-before',q['shape']),('physical-after',a['shape']),('outline-before',q.get('zone_outline_shape',q['shape'])),('outline-after',a['zone_outline_shape'])]}
    write(OUT/'prior-owned-plane-new-barrel-cut-ledger.json',oldvl);z+=nn
    write(OUT/'exact-host-footprint-translation-ledger.json',pose)
    rf=L.OUT.parent/'protected-field-return-r4-snapshot-4/proposed-zones.pkl';rz=pickle.loads(rf.read_bytes());rooterrors=[]
    for q in rz:
        for v in d['vias']:
            if v['net']!=q['net']:
                actual=Point(v['x'],v['y']).distance(q['shape'])-v['d']/2;required=max(G.gap(h,v['net'],q['net']),float(q.get('clearance_mm',.15)))+.025
                if actual<required:rooterrors.append({'kind':'new_via_root_spine','via':v['uuid'],'root_zone':q['uuid'],'actual':actual,'required':required})
        for t in d['tracks']:
            if t['layer']==q['layer'] and t['net']!=q['net']:
                actual=LineString([t['a'],t['b']]).distance(q['shape'])-t['w']/2;required=max(G.gap(h,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025
                if actual<required:rooterrors.append({'kind':'new_track_root_spine','track':t['uuid'],'root_zone':q['uuid'],'actual':actual,'required':required})
        for a in nn:
            if a['layer']==q['layer'] and a['net']!=q['net']:
                actual=a['shape'].distance(q['shape']);required=max(G.gap(h,a['net'],q['net']),float(a.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025
                if actual<required:rooterrors.append({'kind':'new_CORE_plane_root_spine','zone':a['uuid'],'root_zone':q['uuid'],'actual':actual,'required':required})
    write(OUT/'root-four-spine-screen.json',{'root_snapshot_file':str(rf.resolve()),'root_snapshot_sha256':sha(rf),'errors':rooterrors,'source_credit_added':False});assert not rooterrors,rooterrors
    b.update({'R17031_nominee_recipe_file':str(nr.resolve()),'R17031_nominee_recipe_sha256':sha(nr),'R17031_exact_host_pose_ledger_file':str((OUT/'exact-host-footprint-translation-ledger.json').resolve()),'R17031_exact_host_pose_ledger_sha256':sha(OUT/'exact-host-footprint-translation-ledger.json'),'R17031_source_parent_model_sha256':sha(mf),'R17031_root_four_spine_screen_sha256':sha(OUT/'root-four-spine-screen.json'),'existing_R17031_native_FP_replacement_contract_required':True})
    b['restored_generated_grid_UUIDs']=sorted(set(b.get('restored_generated_grid_UUIDs',[]))|{q['uuid'] for q in nn}|{q['zone_uuid'] for q in oldvl})
    cp=OUT/'owned-translation-checkpoint.pkl';cp.write_bytes(pickle.dumps((g,h,b,z,None),protocol=5));(OUT/'proposed-discrete.pkl').write_bytes((nd/'proposed-discrete.pkl').read_bytes());(OUT/'new-CORE-zones.pkl').write_bytes(pickle.dumps(nn,protocol=5));write(OUT/'checkpoint-receipt.json',{'verdict':'EXACT_POSE_CU_ROUND_CUTS_ROOT_SPINE_SCOPED_SCREEN_FROZEN_SOURCE_PENDING','checkpoint_sha256':sha(cp),'pose_ledger_sha256':sha(OUT/'exact-host-footprint-translation-ledger.json'),'native_jobs':0,'board_written':False});print('R78_CHECKPOINT',sha(cp),len(oldvl),sha(rf),flush=True)
    candidate,cuts=GP.projected(g,h,z);write(OUT/'old-fill-outward-projection-ledger.json',cuts)
    Q.NET=I.NET;groups,_,_=Q.groups(candidate,return_details=True);lookup={a['uuid']:i for i,rs in enumerate(groups) for a in rs};sp=next(a for a in h['pads'] if (a['ref'],a['num'])==('R11022','2'));root=lookup[sp['uuid']];missing=[{'group':i,'pads':[a for a in rs if not a['ref'].startswith('@')]} for i,rs in enumerate(groups) if i!=root and any(not a['ref'].startswith('@') for a in rs)];assert not missing,missing
    Q.NET=I.p.norm('/motherboard_status/OBS15_A');before=Q.groups(oldc,return_details=True)[0];after=Q.groups(candidate,return_details=True)[0];post={a['uuid']:i for i,rs in enumerate(after) for a in rs};lost=[]
    for i,rs in enumerate(before):
        split={post.get(a['uuid'],'missing:'+a['uuid']) for a in rs}
        if len(split)>1 or any(str(x).startswith('missing:') for x in split):lost.append({'old_group':i,'new_groups':sorted(split,key=str),'items':rs})
    assert not lost,lost
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,z,candidate),protocol=5));write(OUT/'receipt.json',{'verdict':'ALL_CORE_NAMED_PADS_SOURCE_ROOTED_OBS_RETAINED_SHARED_CONTACTS_PASS_GEOMETRY_NATIVE_CURRENT_PENDING','model_sha256':sha(model),'parent_model_sha256':sha(mf),'checkpoint_sha256':sha(cp),'CORE_source':'R11022.2','CORE_bare_named_groups':missing,'OBS15_all_prior_physical_pad_track_via_layer_relationships_retained':True,'OBS15_before_group_count':len(before),'OBS15_after_group_count':len(after),'exact_FP_host_pose_ledger_sha256':sha(OUT/'exact-host-footprint-translation-ledger.json'),'root_four_spines_screen_sha256':sha(OUT/'root-four-spine-screen.json'),'all_retained_foreign_original198b_and_native_baseline_power_current_and_native_gates':'OPEN','native_jobs':0,'board_written':False});print('R78_ALL_CORE_OBS_PASS',sha(model),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
