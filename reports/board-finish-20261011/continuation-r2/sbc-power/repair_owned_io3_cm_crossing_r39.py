"""Replace exactly two owned IO3 tracks crossing the retained CM clock.

All actual native-parent Cu and later proposed power Cu are obstacles. Old
zone outlines and the CM clock remain exact. Source/contact/native gates are
explicit, and no live board is changed.
"""
import copy,json,pickle,hashlib,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import core_inner_feed_r18 as I
import continuous_path_prepared_r2 as CP
L=I.L;p=I.p;P=I.P;Q=I.Q;C=I.C;G=I.G;R=I.R
OUT=L.OUT/'owned-io3-cm-crossing-repair-r39';NET='/IO_3V3'
REMOVE=('f40d2eaf-c69c-5163-bf36-1b97a3063419','b1e24199-3f81-528d-bf44-77fe8c8eb9a9')
KEEP='c966025c-6c22-5bcc-bcf8-3675df7a3301'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert len(sys.argv)==2;prior=Path(sys.argv[1]);assert not OUT.exists();OUT.mkdir()
    g,h,binding,zones,_=pickle.loads(prior.read_bytes());h=copy.deepcopy(h)
    native=L.OUT.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
    assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    sys.path.insert(0,str(L.OUT.parent));import native_pose_signal_contract as NC
    inv=NC.C.inventory(native.read_bytes());before=[next(q for q in h['tracks'] if q['uuid']==uid) for uid in REMOVE]
    clock=next(q for q in h['tracks'] if q['uuid']==KEEP);assert clock['net']=='/motherboard_compute/CM_CAN_SPI_SCLK'
    assert clock['a']==[125.05,162.85] and clock['b']==[128.252,165.95] and clock['w']==.385
    assert all(q['net']==NET and q['layer']=='F.Cu' and q['w']==.2 for q in before)
    oldrows=[]
    for q in before:
        chunk=inv[3][q['uuid']];f=OUT/(q['uuid']+'.old-exact-native-segment-chunk');f.write_bytes(chunk)
        oldrows.append({'uuid':q['uuid'],'kind':'segment','raw_net':q['net'],'geometry':q,'chunk_file':str(f.resolve()),'chunk_sha256':sha(f),
            'reason':'Native dc936 short/cross with exact retained CM SCLK; two earlier owned IO3 segments only','all_outside_shared_contacts_required':True})
    ledger=OUT/'owned-existing-Cu-removal-ledger.json';ledger.write_text(json.dumps({'parent_native_board_sha256':sha(native),'rows':oldrows,'exact_retained_CM_clock_uuid':KEEP,'clock_native_chunk_sha256':hashlib.sha256(inv[3][KEEP]).hexdigest()},indent=2)+'\n')
    h['tracks']=[q for q in h['tracks'] if q['uuid'] not in REMOVE];start=before[0]['a'];end=before[1]['b'];route=None
    outline=unary_union(p.base.polygons(g['outline'])).buffer(-.525)
    for margin in (3.,6.,12.,30.):
        win=box(min(start[0],end[0])-margin,min(start[1],end[1])-margin,max(start[0],end[0])+margin,max(start[1],end[1])+margin);p.WINDOW=win
        repour=tuple({p.norm(q['net']) for q in h['zones']})
        # Original F fills may retreat normally; ALL physical native parent
        # Cu and every new foreign proposal remain hard, including later CM.
        free=R.free_layer(h,NET,'F.Cu',win,repour,reference_guard=None,allow_own_via_connection=True).intersection(outline)
        extra=[z['shape'].buffer(max(G.gap(h,NET,z['net']),float(z.get('clearance_mm',.15)))+.025) for z in zones if z['layer']=='F.Cu' and p.norm(z['net'])!=NET and z['shape'].intersects(win.buffer(1))]
        free=set_precision(free.difference(unary_union(extra)),1e-6)
        for comp in p.hubs.components(set_precision(free.buffer(-.11),1e-6)):
            if not comp.covers(Point(start)) or not comp.covers(Point(end)):continue
            print('IO3_CM_EXACT_PARENT_DETOUR',margin,comp.area,flush=True);test=CP.path(comp,start,end,node_cap=500000)
            if test['verdict']!='HOST_PATH':continue
            points=[[round(x,6),round(y,6)] for x,y in test['points']]
            if not free.covers(LineString(points).buffer(.1)):continue
            route={**test,'points':points,'length_mm':LineString(points).length,'width_mm':.2,'exact_native_parent_all_Cu_hard':True};break
        if route:break
    assert route is not None,'No exact contained F detour; preserve failed receipt and construct an explicit ordinary layer change next'
    adds=[C.track('IO3-CM-clock-detour-r39-'+str(i),NET,'F.Cu',a,b,.2) for i,(a,b) in enumerate(zip(route['points'],route['points'][1:]))]
    assert all(not p.base.body(t).buffer(G.gap(h,NET,clock['net'])+.025).intersects(p.base.body(clock)) for t in adds),'Retained clock clearances mandatory'
    h['tracks']+=adds;binding.setdefault('existing_native_owned_Cu_removal_recipes',[]).append({'file':str(ledger.resolve()),'sha256':sha(ledger)})
    binding.update({'IO3_CM_crossing_native_error_file_sha256':sha(L.OUT.parent/'field-native-ordinary-errors-r1.json'),'IO3_CM_crossing_parent_model_sha256':sha(prior),
        'IO3_CM_crossing_old_owned_UUIDs':list(REMOVE),'IO3_CM_exact_retained_clock_UUID':KEEP,'IO3_CM_crossing_geometry_route':route,
        'IO3_CM_prior_obstacle_scope_failure':'IO3 planned before later root CM additions; native raw-Cu parity alone did not test physical clearance'})
    candidate,cuts=P.projected(g,h,zones);Q.NET=NET;groups,_,_=Q.groups(candidate,return_details=True);ids={q['uuid']:i for i,rr in enumerate(groups) for q in rr}
    r49=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11049','1'));source=next(q for q in h['pads'] if (q['ref'],q['num'])==('R18001','2'))
    assert ids[r49['uuid']]==ids[source['uuid']],'Repaired R49 IO3 path must reach actual post-shunt source'
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    (OUT/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    receipt={'verdict':'PASS_OWNED_IO3_DETOUR_RETAINED_CLOCK_AND_ACTUAL_IO3_SOURCE_FULL_CONTACT_NATIVE_PENDING','model_sha256':sha(model),
        'parent_model_sha256':sha(prior),'binding':binding,'old_owned_Cu_removals':oldrows,'new_tracks':adds,'route':route,
        'exact_retained_CM_clock_uuid':KEEP,'exact_retained_CM_clock_chunk_sha256':hashlib.sha256(inv[3][KEEP]).hexdigest(),
        'owned_removal_ledger_file':str(ledger.resolve()),'owned_removal_ledger_sha256':sha(ledger),'old_fill_retreats':cuts,
        'native_jobs':0,'board_written':False,'full_old_contacts_foreign_mutual_current_native_gates':'OPEN'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('IO3_CM_DETOUR_CONSTRUCTED_SOURCE_PASS',sha(model),len(adds),route['length_mm'],flush=True)
if __name__=='__main__':main()
