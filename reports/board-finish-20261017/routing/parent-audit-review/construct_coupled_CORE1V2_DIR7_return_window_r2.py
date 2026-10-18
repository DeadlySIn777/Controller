"""Real same-UUID CORE1V2 negative intents opening old LG return windows.

No ground fill is fabricated or credited. The native GND plane already has the
original intent; a real refill must restore the reference and prove every gate.
"""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,math,runpy
from pathlib import Path
from fractions import Fraction as Q
from shapely import from_wkb
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2';P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L
import audit_FIELD5_R453_literal_rational_line_membership_r189 as X
OUT=HERE/'coupled-CORE1V2-DIR7-return-window-candidate-r2'
SOURCE=OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/copy/board.kicad_pcb'
TARGETS=['69c62b44-c4ad-55f0-bf91-575b93a0b295']
WITNESSES=['6e8d51b6-4181-4dc1-bfc7-c0482d7736b9']
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def iu(v):
    n=round(v*1e6);assert n/1e6==v;return n
def integer_shape(sh):
    return Polygon([(iu(x),iu(y))for x,y in sh.exterior.coords], [[(iu(x),iu(y))for x,y in r.coords]for r in sh.interiors])
def parts(sh):
    if sh.is_empty:return []
    return [sh]if sh.geom_type=='Polygon'else[p for g in sh.geoms for p in parts(g)]
def info(sh):return {'type':sh.geom_type,'area_mm2':sh.area/1e12,'bounds_IU':None if sh.is_empty else list(sh.bounds),'WKB_SHA256':hashlib.sha256(sh.wkb).hexdigest()}
def polygon_spans(raw):
    spans=[];depth=0;start=None;quoted=False;escape=False
    for i,c in enumerate(raw):
        if quoted:
            if escape:escape=False
            elif c==92:escape=True
            elif c==34:quoted=False
            continue
        if c==34:quoted=True;continue
        if c==40:
            if depth==1:start=i
            depth+=1
        elif c==41:
            depth-=1
            if depth==1:
                token=raw[start+1:i].split(None,1)[0]
                if token in(b'polygon',b'filled_polygon',b'fill_segments'):spans.append((start,i+1,token))
    assert depth==0;return spans
def render_ring(ring):
    points=list(ring.coords)
    if points[0]==points[-1]:points.pop()
    assert all(int(x)==x and int(y)==y for x,y in points)
    return ('\t\t(polygon\n\t\t\t(pts\n'+''.join('\t\t\t\t(xy '+format(x/1e6,'.6f')+' '+format(y/1e6,'.6f')+')\n'for x,y in points)+'\t\t\t)\n\t\t)\n').encode()
def snap_native_negative(shape,before,cut):
    reserves=[]
    for iteration in range(6):
        result=[]
        for poly in parts(shape):
            def convert(raw):
                out=[]
                for x,y in raw.coords:
                    q=(round(x),round(y))
                    if before.covers(Point(q))and not cut.contains(Point(q)):out.append(q);continue
                    options=[]
                    for step in(1,2,4,8):
                        for dx in range(-step,step+1):
                            for dy in range(-step,step+1):
                                v=(q[0]+dx,q[1]+dy)
                                if before.covers(Point(v))and not cut.contains(Point(v)):options.append(v)
                        if options:break
                    assert options, 'No local native-IU inward-only vertex snap'
                    v=min(options,key=lambda v:(v[0]-x)**2+(v[1]-y)**2);out.append(v);reserves.append({'original_overlay_point_IU':[x,y],'explicit_inward_native_vertex_IU':v})
                return out
            q=Polygon(convert(poly.exterior),[convert(r)for r in poly.interiors]);assert q.is_valid
            result.append(q)
        final=unary_union(result);gain=final.difference(before)
        if gain.is_empty and final.relate(cut)[0]=='F':return final,reserves
        assert not gain.is_empty and cut.buffer(10000).covers(gain),'Refuse remote geometry change or swallowed cut interior'
        reserve=gain.buffer(100,quad_segs=8);reserves.append({'iteration':iteration,'explicit_local_negative_native_IU_buffer':100,'raw_gain':info(gain)});shape=final.difference(reserve)
    raise AssertionError('Exact zero-gain native construction did not converge')
def exact_subset_boundary_proof(before,after):
    assert before.geom_type=='Polygon'and not before.interiors
    raw=[[[tuple(Q(int(v))for v in xy)for xy in before.exterior.coords]]];source_edges={(a,b)for a,b in zip(raw[0][0],raw[0][0][1:])}
    count=0;unchanged=0
    for poly in parts(after):
        for ring in[poly.exterior,*poly.interiors]:
            points=[tuple(Q(int(v))for v in xy)for xy in ring.coords]
            for a,b in zip(points,points[1:]):
                if(a,b)in source_edges or(b,a)in source_edges:unchanged+=1;continue
                ts=X.split_parameters(a,b,{'before':raw})
                for t in ts+[(t+u)/2 for t,u in zip(ts,ts[1:])if t!=u]:
                    point=X.along(a,b,t);assert X.location(point,raw)!='EXTERIOR';count+=1
        p=poly.representative_point();assert X.location(X.point((p.x,p.y)),raw)=='INTERIOR'
    return {'before_single_polygon_has_no_holes':True,'all_unchanged_native_edges_literal':unchanged,'all_new_native_boundary_breakpoints_and_open_intervals_exactly_inside_closed_before':count,'interior_component_point_exactly_before_interior':True,'method':'Native-IU vertices as exact rationals; boundary split at every original edge; no area or distance tolerance'}
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir();mf=P/'actual-combined-full-after-model.pkl';h=pickle.loads(mf.read_bytes())
    proof=HERE/'CORE1V2-conservative-whole-record-retention-r1/receipt.json';prior=json.loads(proof.read_bytes());assert all(t['status'].startswith('STRONGER_WHOLE_RECORD_REMOVAL_HOST_RETENTION_PASS')for t in prior['trials'])
    assert prior['input_SHA256'][str(mf)]==sha(mf)
    lg=next(z for z in h['zones']if z['uuid']=='c1d27fa1-452b-4e27-985d-5ad23644d800');assert lg['clearance_mm']==.25 and lg['min_thickness_mm']==.2
    # Exact source-backed lower bound: .25 actual source clearance + .1 half
    # actual LG minimum fill width + unchanged .025 planning guard +1nm.
    guard=375001;cutters=[];witnessfiles=[];descriptors=[]
    for uid in WITNESSES:
        f=P/('oldref-'+uid+'.wkb');witnessfiles.append(f);sh=from_wkb(f.read_bytes())
        for i,part in enumerate(parts(sh)):
            b=part.bounds;bounds=[math.floor(Q(b[0])*1e6)-guard,math.floor(Q(b[1])*1e6)-guard,math.ceil(Q(b[2])*1e6)+guard,math.ceil(Q(b[3])*1e6)+guard];cutters.append(box(*bounds));descriptors.append({'track_UUID':uid,'component':i,'raw_witness_SHA256':sha(f),'raw_component_bounds_mm':list(b),'exact_outward_native_IU_cut_bounds':bounds,'guard_IU':guard})
    cut=unary_union(cutters);(OUT/'exact-native-IU-negative-window-cutters.wkb').write_bytes(cut.wkb)
    raw=SOURCE.read_bytes();assert sha(SOURCE)=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2';iv=K.C.inventory(raw);replacements={};rows=[]
    for uid in TARGETS:
        z=next(z for z in h['zones']if z['uuid']==uid);assert L.norm(z['net'])=='/CORE_1V2'and z['layers']==['In4.Cu']
        oldparts=L.poly(N.O.polys(z['outline']));assert len(oldparts)==1
        before=integer_shape(oldparts[0]);planned=before.difference(cut);after,snaps=snap_native_negative(planned,before,cut)
        if after.geom_type!='Polygon':
            put('disconnected-owned-intent-parts-held.json',{'UUID':uid,'after':info(after),'parts':[info(p)for p in parts(after)],'no_extra_fragment_dropped_or_emitted':True});raise AssertionError('Native intent split requires explicit fragment/source-role review')
        assert after.difference(before).is_empty and after.relate(cut)[0]=='F'
        exact=exact_subset_boundary_proof(before,after);old=iv[3][uid];spans=polygon_spans(old);assert spans and all(kind==b'polygon'for a,b,kind in spans)
        new=old
        for a,b,kind in reversed(spans):new=new[:a]+new[b:]
        insertion=render_ring(after.exterior)+b''.join(render_ring(r)for r in after.interiors);new=new[:spans[0][0]]+insertion+new[spans[0][0]:]
        assert K.C.pcbtext.chunk_uuid(new)==uid and K.C.pcbtext.chunk_kind(new)=='zone';replacements[uid]=new
        oldfile=OUT/(uid+'-exact-before.zone-chunk');newfile=OUT/(uid+'-guarded-negative.zone-chunk');oldfile.write_bytes(old);newfile.write_bytes(new)
        removed=before.difference(after);(OUT/(uid+'-explicit-owned-negative-native-IU.wkb')).write_bytes(removed.wkb)
        rows.append({'UUID':uid,'raw_net':z['net'],'layer':'In4.Cu','same_UUID_and_all_original_native_profile_fields':True,'before':info(before),'after':info(after),'explicit_owned_native_intent_removed':info(removed),'exact_native_IU_rational_subset_proof':exact,'explicit_inward_serialization_snaps_or_reserves':snaps,'no_Cu_added_to_existing_intent':True,'native_full_guard_window_interiors_free_of_owned_CORE_intent':True,'old_chunk_file':str(oldfile),'old_chunk_SHA256':sha(oldfile),'new_chunk_file':str(newfile),'new_chunk_SHA256':sha(newfile)})
    output=raw
    for uid,new in replacements.items():assert output.count(iv[3][uid])==1;output=output.replace(iv[3][uid],new,1)
    inventory=K.C.inventory(output);assert set(inventory[3])==set(iv[3]);assert all(inventory[3][u]==c for u,c in iv[3].items()if u not in replacements);assert iv[0]==inventory[0]and iv[2]==inventory[2]
    (OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(output)
    put('native-same-UUID-negative-manifest.json',{'baseline':str(SOURCE),'baseline_SHA256':sha(SOURCE),'operations':rows,'all_other_native_chunks_header_tail_exact':True,'unchanged_chunk_count':len(iv[3])-len(rows),'candidate_file':str(board),'candidate_SHA256':sha(board)})
    put('receipt.json',{'status':'REAL_NATIVE_COUPLED_CORE1V2_NEGATIVE_WINDOWS_HOST_RETENTION_PRECHECK_PASS_ACTUAL_REFILL_CURRENT_OPEN','native_cut_guard_IU':guard,'source_backed_guard_terms_IU':{'actual_LG_source_zone_clearance':250000,'half_actual_LG_source_minimum_fill_width':100000,'unchanged_planning_margin':25000,'native_IU_construction_guard':1},'window_cutters':descriptors,'operations':rows,'unchanged_actual_LG_In4_source_intent_and_profile':True,'no_new_GND_fill_or_cap_or_return_authority_fabricated':True,'CORE_current_source_relationship_and_directcontact_proof':'Stronger removal of entire immutable current actual target fill records passes; all non-target copper fixed','stronger_CORE_retention_receipt_SHA256':sha(proof),'candidate_SHA256':sha(board),'native_source_CPP_refill_and_all9source_keys_contacts_allbanks_oldbody_positivepour_and_signal_fullbody':'OPEN_REQUIRED','CORE_signed_load_mesh_minwidth_voltage_drop_thermal_barrel_current':'OPEN_REQUIRED','all433_parent_reference_losses':'HELD_NO_CLOSURE_CLAIM','coverage':'Only DIR7 component0 causal CORE69 shadow; CORE60 components and all other failures remain open','previous_four_conflict_FG_packet':'INDEPENDENT_HELD_NOT_INCLUDED','native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,mf,proof,*witnessfiles,Path(X.__file__))},'elapsed_seconds':time.monotonic()-st})
    print('CORE_COUPLED_NATIVE_CANDIDATE',sha(board),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
