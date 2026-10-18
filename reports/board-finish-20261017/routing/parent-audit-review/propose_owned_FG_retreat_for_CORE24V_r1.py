"""Real negative owned-FG prototype; no LG cache substitution or waiver."""
import os,sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,math,time,gc
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2';P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
B=OLD/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
for d in (OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
from emit_logic_zones_r1 import ring as render_ring
K=N.K;L=N.L;FG='/motherboard_motors/FIELD_GND';UID='ff5ffe1e-111b-5951-957a-dfd8894ca90c'
SOURCE=OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/copy/board.kicad_pcb'
OUT=HERE/'owned-FG-negative-CORE24V-prototypes-r1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()

def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def save(label,s):
    r=info(s);f=OUT/(label+'.wkb');f.write_bytes(s.wkb);r['file']=str(f);return r
def integer_replay(shape):
    pieces=[]
    for p in K.RF.parts(shape):
        convert=lambda r:[(round(x*1e6)/1e6,round(y*1e6)/1e6)for x,y in r.coords]
        q=Polygon(convert(p.exterior),[convert(r)for r in p.interiors]);assert q.is_valid
        pieces.append(q)
    return unary_union(pieces)
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

def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    h=pickle.loads((P/'actual-combined-full-after-model.pkl').read_bytes())
    graphs=pickle.loads((P/'actual-combined-full-after-all-net-groups.pkl').read_bytes());prior=graphs[FG];priorroot=K.root(prior,'J11003','2');del graphs;gc.collect()
    sourceprior=K.keys(priorroot);ctx=K.hole_context(h)
    zone=next(z for z in h['zones']if z['uuid']==UID);assert L.norm(zone['net'])==FG and zone['layers']==['In1.Cu']
    intended=unary_union(L.poly(N.O.polys(zone['outline'])));physical=unary_union(L.poly(zone['fills']['In1.Cu']))
    assert intended.geom_type=='Polygon'
    files=[P/('oldref-'+u+'.wkb')for u in('942659fe-dca8-4a36-af79-d5a05f611887','028ef3d3-2b43-440e-a40f-06eeffe3d727')]
    required=unary_union([from_wkb(f.read_bytes())for f in files]);save('required-prior-LG-reference-bodies-raw-retained',required)
    raw=SOURCE.read_bytes();inventory=K.C.inventory(raw);oldchunk=inventory[3][UID];(OUT/'exact-before-ff5ffe.zone-chunk').write_bytes(oldchunk)
    trials=[]
    for guard in(.600001,.625001):
        label='guard-'+str(round(guard*1e6));cut=K.Z.bounded_buffer(required,guard);shape=intended.difference(cut);reserves=[]
        for iteration in range(8):
            final=integer_replay(shape);gain=final.difference(intended)
            if gain.is_empty:break
            reserve=K.Z.bounded_buffer(gain,.0001);reserves.append({'iteration':iteration,'raw_serialize_gain':save(label+'-serialize-gain-'+str(iteration),gain),'explicit_additional_negative':save(label+'-extra-negative-'+str(iteration),reserve)})
            shape=final.difference(reserve)
        else:raise AssertionError('No zero-gain native integer construction')
        assert final.difference(intended).is_empty and final.geom_type=='Polygon'
        negative=intended.difference(final);projected=physical.difference(negative)
        assert projected.difference(physical).is_empty
        # This source-planning model is explicitly not an actual native refill.
        zones=[]
        for z in h['zones']:
            if z['uuid']!=UID:zones.append(z);continue
            z={**z,'fills':dict(z['fills'])};z['fills']['In1.Cu']=[[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in K.RF.parts(projected)];zones.append(z)
        candidate={**h,'zones':zones};_,groups=K.physical(candidate,FG,ctx);root=K.root(groups,'J11003','2')
        keys_lost=sorted(sourceprior-K.keys(root));relationships,bad=K.contact_losses(prior,groups)
        # Every current actual direct same-net fill contact is retained.
        fillbefore=[r for g in prior for r in g if r['kind']=='fill'and r['layer']=='In1.Cu'];fillafter=[r for g in groups for r in g if r['kind']=='fill'and r['layer']=='In1.Cu']
        tb=STRtree([r['shape']for r in fillbefore]);ta=STRtree([r['shape']for r in fillafter]);direct=[]
        metal={}
        for g in prior:
            for r in g:
                if r['kind']!='fill'and r['layer']=='In1.Cu':metal.setdefault((r['kind'],r['uuid'],r['layer']),[]).append(r['shape'])
        for key,ss in metal.items():
            body=unary_union(ss)
            if body.distance(negative)>.000002:continue
            was=any(body.distance(fillbefore[int(i)]['shape'])<=.000002 for i in tb.query(body.buffer(.000002),predicate='intersects'))
            if not was:continue
            now=any(body.distance(fillafter[int(i)]['shape'])<=.000002 for i in ta.query(body.buffer(.000002),predicate='intersects'))
            direct.append({'old_key':list(key),'current_fill_touch':was,'prototype_fill_touch':now})
        # Preserve current actual FG source support on all local retained bodies.
        local=negative.envelope.buffer(.01)
        oldref=unary_union([r['shape']for r in priorroot if r['kind']=='fill'and r['layer']=='In1.Cu'and r['shape'].intersects(local)])
        newref=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']=='In1.Cu'and r['shape'].intersects(local)])
        ref_losses=[]
        for t in h['tracks']:
            if t['layer']not in('F.Cu','In2.Cu')or L.norm(t['net'])==FG or h['domains_normalized'].get(L.norm(t['net']))!=h['domains_normalized'][FG]:continue
            bb=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2)
            if not bb.intersects(local):continue
            body=K.A.shape({'kind':'segment',**t})if not t.get('m')else L.body(t)
            loss=body.intersection(oldref).difference(newref)
            if not loss.is_empty:ref_losses.append({'track_UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'loss':save(label+'-FG-ref-loss-'+t['uuid'],loss)})
        # Canonical native integer outline replaces polygon children only.
        spans=polygon_spans(oldchunk);assert spans and all(kind==b'polygon'for _,_,kind in spans)
        insertion=(render_ring(final.exterior)+''.join(render_ring(r)for r in final.interiors)).encode()
        first=spans[0][0];updated=oldchunk
        for a,b,kind in reversed(spans):updated=updated[:a]+updated[b:]
        updated=updated[:first]+insertion+updated[first:]
        assert K.C.pcbtext.chunk_uuid(updated)==UID and K.C.pcbtext.chunk_kind(updated)=='zone'
        chunk=OUT/(label+'-same-UUID-negative-only.zone-chunk');chunk.write_bytes(updated)
        error=bool(keys_lost or bad or any(not r['prototype_fill_touch']for r in direct)or ref_losses)
        trial={'guard_mm':guard,'status':'HOST_FG_RETENTION_PASS_NATIVE_LG_REFILL_AND_CURRENT_OPEN'if not error else'HOST_FG_RETENTION_FAIL_REPAIR_NOT_COMPOSABLE','current_owned_zone_UUID':UID,'same_original_native_profile_and_UUID':True,'zero_intended_Cu_gained':final.difference(intended).is_empty,'after_intended':save(label+'-after-intended',final),'explicit_negative':save(label+'-negative',negative),'current_physical_FG_removed':save(label+'-physical-FG-removed',physical.intersection(negative)),'serialization_extra_negative_reserves':reserves,'source_layer_keys_lost':[list(k)for k in keys_lost],'old_actual_FG_relationship_losses':bad,'near_negative_old_direct_contacts':direct,'strict_current_FG_reference_losses':ref_losses,'chunk_file':str(chunk),'chunk_SHA256':sha(chunk),'no_LG_proposed_fill_or_cap_substitution':True,'actual_fresh_native_LG_refill_required':True,'field_signed_return_current_minwidth_thermal_barrel':'OPEN'}
        trials.append(trial);put('trial-progress.json',trials);print('FG_RETREAT_TRIAL',guard,'keys',len(keys_lost),'groups',len(bad),'direct',sum(not r['prototype_fill_touch']for r in direct),'refs',len(ref_losses),flush=True)
    put('receipt.json',{'status':'REAL_OWNED_FG_NEGATIVE_PROTOTYPES_SCREENED_ALL_RAW_FAILURES_HELD','trials':trials,'no_existing_Cu_chunks_holes_pads_source_or_adopted_files_changed':True,'no_actual_LG_refill_performed_or_claimed':True,'native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,P/'actual-graph-cache-receipt.json',P/'actual-combined-full-after-model.pkl',P/'actual-combined-full-after-all-net-groups.pkl',*files)},'elapsed_seconds':time.monotonic()-st})
    print('FG_RETREAT_COMPLETE',sha(OUT/'receipt.json'),flush=True)

if __name__=='__main__':main()
