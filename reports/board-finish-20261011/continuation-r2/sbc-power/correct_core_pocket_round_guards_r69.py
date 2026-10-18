"""Correct only R64's new CORE plane with analytic outward round cutters."""
import copy,json,pickle,hashlib
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import core_inner_feed_r18 as I
import guarded_declared_settings_projection_r58 as GP
L=I.L;p=I.p;G=I.G;Q=I.Q
OUT=L.OUT/'core-pocket-outward-round-guards-r69'
UID='ed372ffe-f7a5-51ad-b9bd-458e63935267'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def keep(name,s):
    f=OUT/(name+'.wkb');f.write_bytes(s.wkb)
    return {'file':str(f.resolve()),'sha256':sha(f),'area_mm2':s.area}
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes())
    parent=L.OUT/'remaining-core-reachable-ordinary-pockets-r64/model.pkl'
    assert sha(parent)=='b64dcb07508abee53cd4d1935a3894d21fe78bc5908cab5ebb0f3b183adade87'
    g,h,b,z,oldc=pickle.loads(parent.read_bytes());b=copy.deepcopy(b);q=next(a for a in z if a['uuid']==UID)
    physical=q['shape'];outline=q.get('zone_outline_shape',physical);rows=[]
    def add(kind,uid,net,cut,details):
        if outline.intersects(cut):rows.append({'kind':kind,'uuid':uid,'raw_net':net,'shape':cut,**details})
    for t in h['tracks']:
        if t['layer']!=q['layer'] or t['net']==q['net']:continue
        clear=max(G.gap(h,q['net'],t['net']),float(q.get('clearance_mm',.15)))+.025
        cut=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear)
        add('analytic_track_centerline_cap',t['uuid'],t['net'],cut,{'track_width_mm':t['w'],'analytic_radius_mm':t['w']/2+clear,'required_guard_mm':clear})
    for v in h['vias']:
        if v['net']==q['net']:continue
        clear=max(G.gap(h,q['net'],v['net']),float(q.get('clearance_mm',.15)))+.025
        radius=v['drill']/2+.275
        if q['layer'] in v['flashed']:radius=max(radius,v['d']/2+clear)
        add('analytic_via_circle',v['uuid'],v['net'],GP.bounded_disk(v,radius),{'analytic_radius_mm':radius,'required_guard_mm':clear,'flashed_on_plane_layer':q['layer'] in v['flashed']})
    for pad in h['pads']:
        if pad['net']==q['net']:continue
        clear=max(G.gap(h,q['net'],pad['net']),float(q.get('clearance_mm',.15)))+.025
        for s in p.base.polygons(pad['layers'].get(q['layer'],[])):
            add('actual_native_pad_polygon',pad['uuid'],pad['net'],GP.bounded_buffer(s,clear),{'required_guard_mm':clear})
        for s in p.base.polygons(pad.get('hole') or []):
            add('actual_native_foreign_pad_hole',pad['uuid'],pad['net'],GP.bounded_buffer(s,.275),{'required_guard_mm':.275})
    cutter=unary_union([r['shape'] for r in rows]);after=set_precision(set_precision(physical,1e-6).difference(cutter),1e-6);oa=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6)
    qq={**q,'shape':after,'zone_outline_shape':oa};zz=[qq if a['uuid']==UID else a for a in z]
    assert all(a['shape'].wkb==aa['shape'].wkb and a.get('zone_outline_shape',a['shape']).wkb==aa.get('zone_outline_shape',aa['shape']).wkb for a,aa in zip(z,zz) if a['uuid']!=UID)
    ledger={'zone_uuid':UID,'raw_net':q['net'],'layer':q['layer'],'files':{n:keep(n,s) for n,s in [('physical-before',physical),('physical-after',after),('outline-before',outline),('outline-after',oa),('cutter-union',cutter)]},'physical_removed_area_mm2':physical.difference(after).area,'physical_quantization_added_area_mm2':after.difference(physical).area,'outline_removed_area_mm2':outline.difference(oa).area,'outline_quantization_added_area_mm2':oa.difference(outline).area,'cutters':[{**{k:v for k,v in r.items() if k!='shape'},'WKB_SHA256':hashlib.sha256(r['shape'].wkb).hexdigest()} for r in rows],'every_other_owned_shape_exact_WKB_unchanged':True}
    write(OUT/'exact-round-cutter-ledger.json',ledger)
    b.update({'R64_outward_round_correction_parent_sha256':sha(parent),'R69_scoped_plane_guard_ledger_sha256':sha(OUT/'exact-round-cutter-ledger.json'),'R69_guarded_projector_sha256':sha(Path(GP.__file__))})
    b['restored_generated_grid_UUIDs']=sorted(set(b.get('restored_generated_grid_UUIDs',[]))|{UID})
    df=OUT/'proposed-discrete.pkl';df.write_bytes((parent.parent/'proposed-discrete.pkl').read_bytes());nf=OUT/'new-CORE-zones.pkl';nf.write_bytes(pickle.dumps([qq],protocol=5));zf=OUT/'all-zones.pkl';zf.write_bytes(pickle.dumps(zz,protocol=5))
    cp=OUT/'owned-correction-checkpoint.pkl';cp.write_bytes(pickle.dumps((g,h,b,zz,None),protocol=5));print('R69_CHECKPOINT',sha(cp),after.area,flush=True)
    candidate,cuts=GP.projected(g,h,zz);Q.NET=I.NET;groups,_,_=Q.groups(candidate,return_details=True);lookup={a['uuid']:i for i,rs in enumerate(groups) for a in rs};sp=next(a for a in h['pads'] if (a['ref'],a['num'])==('R11022','2'));root=lookup[sp['uuid']]
    missing=[{'group':i,'pads':[a for a in rs if not a['ref'].startswith('@')]} for i,rs in enumerate(groups) if i!=root and any(not a['ref'].startswith('@') for a in rs)]
    assert {(a['ref'],a['pad']) for rs in missing for a in rs['pads']}=={('R17031','1')},missing
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,zz,candidate),protocol=5));write(OUT/'old-fill-outward-projection-ledger.json',cuts)
    write(OUT/'receipt.json',{'verdict':'SCOPED_OUTWARD_PLANE_CORRECTION_ACTUAL_CORE_SOURCE_PASS_ANALYTIC_GATE_PENDING','model_sha256':sha(model),'new_discrete_sha256':sha(df),'new_CORE_zone_sha256':sha(nf),'parent_sha256':sha(parent),'guard_ledger_sha256':sha(OUT/'exact-round-cutter-ledger.json'),'CORE_source':'R11022.2','CORE_remaining':missing,'exact_two_vias_seven_tracks_unchanged':True,'all_other_owned_shapes_exact_WKB_unchanged':True,'all_retained_foreign_current_native_refill_DRC_gates':'OPEN','native_jobs':0,'board_written':False})
    print('R69_SOURCE_PASS',sha(model),sha(nf),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
