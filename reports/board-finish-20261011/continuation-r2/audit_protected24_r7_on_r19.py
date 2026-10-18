"""Independent completed protected24 recipe audit on exact corrected R19 only."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import collections,hashlib,json,math,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import zone_projection_r1 as N
from audit_field_io3_crossings_r15e import losses
OUT=H/'protected24-r7-independent-r19-audit-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists()
    rp=H/'protected24-dogbones-r7';rr=read(rp/'receipt.json')
    bp=H/'field-power/repaired-local-return-audit-r19';br=read(bp/'receipt.json')
    assert br['verdict'].startswith('PASS_')
    assert sha(bp/'geometry.pkl')=='38882eeb997cfe1836314af74532bc497704548af8c8e9b1851607c2a92fff1c'
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),rp/'receipt.json',rp/'proposed-discrete.pkl',rp/'proposed-zones.pkl',rp/'owned-new-return-zone-updates.pkl',bp/'receipt.json',bp/'geometry.pkl',bp/'discrete.pkl',bp/'groups.pkl',bp/'proposed-zones.pkl',H/'sbc-power/io3-field-crossings-r15/model.pkl',Path(F.__file__),Path(N.__file__),Path(C.__file__))}
    for key,name in [('proposed_discrete_sha256','proposed-discrete.pkl'),('proposed_zones_sha256','proposed-zones.pkl'),('owned_return_zone_updates_sha256','owned-new-return-zone-updates.pkl')]:assert sha(rp/name)==rr[key]
    prior=pickle.loads((bp/'geometry.pkl').read_bytes());discrete=pickle.loads((bp/'discrete.pkl').read_bytes());beforegroups=pickle.loads((bp/'groups.pkl').read_bytes());zones=pickle.loads((bp/'proposed-zones.pkl').read_bytes());new=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());addedzones=pickle.loads((rp/'proposed-zones.pkl').read_bytes());updates=pickle.loads((rp/'owned-new-return-zone-updates.pkl').read_bytes())
    old=pickle.loads((H/'sbc-power/io3-field-crossings-r15/model.pkl').read_bytes())[0]
    byid={q['uuid']:q for q in zones};updated={q['uuid']:q for q in updates};ownership=[]
    for q in updates:
        b=byid[q['uuid']]
        assert q['net']==b['net'] and q['layer']==b['layer'] and q['layer'] in ('In1.Cu','In2.Cu','In4.Cu')
        assert C.norm(q['net']) in ('/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V')
        chain=[x for x in rr['owned_return_carve_ledger'] if x['owned_new_return_uuid']==q['uuid']]
        assert chain and hashlib.sha256(b['shape'].wkb).hexdigest()==chain[0]['old_shape_sha256']
        for i,row in enumerate(chain):
            assert sha(row['removed_file'])==row['removed_file_sha256'] and sha(row['quantization_added_file'])==row['quantization_added_file_sha256']
            if i:assert row['old_shape_sha256']==chain[i-1]['new_shape_sha256']
            assert row['exact_grid_mm']==1e-6
        assert hashlib.sha256(q['shape'].wkb).hexdigest()==chain[-1]['new_shape_sha256']
        ownership.append({'uuid':q['uuid'],'carve_steps':len(chain),'removed_area_mm2':b['shape'].difference(q['shape']).area,'quantization_added_area_mm2':q['shape'].difference(b['shape']).area})
    zones=[updated.get(q['uuid'],q) for q in zones]+addedzones
    precision_ids={q['uuid'] for q in zones if q.get('label')=='CORE-main-In2' or q.get('label','').startswith('IO3-r15-field-crossing-') or q.get('field_return_proposal') and q['layer']=='In2.Cu'}
    assert len(precision_ids)==9
    zones=[{**q,'shape':set_precision(q['shape'],1e-6)} if q['uuid'] in precision_ids else q for q in zones]
    h={**discrete,'tracks':discrete['tracks']+new['tracks'],'vias':discrete['vias']+new['vias']}
    ids=[q['uuid'] for key in ('tracks','vias','pads') for q in h[key]];assert len(ids)==len(set(ids))
    OUT.mkdir();errors=[];apertures=[]
    smd=[unary_union(C.poly(ps)) for q in h['pads'] if q['smd'] for layer,ps in q['layers'].items() if layer in ('F.Cu','B.Cu')];st=STRtree(smd)
    padholes=[s for q in h['pads'] for s in C.poly(q.get('hole') or [])];ht=STRtree(padholes)
    for v in new['vias']:
        pt=Point(v['x'],v['y']);gaps=[]
        for i in st.query(pt.buffer(v['drill']/2+.7),predicate='intersects'):
            gap=pt.distance(smd[int(i)])-v['drill']/2
            if gap<.275-1e-9:gaps.append({'kind':'SMD','edge_gap_mm':gap})
        for w in h['vias']:
            if w['uuid']==v['uuid']:continue
            gap=math.hypot(v['x']-w['x'],v['y']-w['y'])-(v['drill']+w['drill'])/2
            if gap<.275-1e-9:gaps.append({'kind':'via_drill','uuid':w['uuid'],'edge_gap_mm':gap})
        for i in ht.query(pt.buffer(v['drill']/2+.7),predicate='intersects'):
            gap=pt.distance(padholes[int(i)])-v['drill']/2
            if gap<.275-1e-9:gaps.append({'kind':'pad_drill','edge_gap_mm':gap})
        apertures.append({'uuid':v['uuid'],'violations':gaps})
        errors.extend({'via_uuid':v['uuid'],**x} for x in gaps)
    errors.extend({'kind':'track_width','uuid':q['uuid'],'width_mm':q['w']} for q in new['tracks'] if q['w']<.2-1e-9)
    # Check actual old/new pads, segments and every explicitly flashed annulus
    # independently of the constructor's route-window obstacle cache.
    physical,trees=F.build({**h,'zones':[]});new_ids={q['uuid'] for kind in ('tracks','vias') for q in new[kind]};physical_errors=[]
    def check_body(uid,raw,layer,shape,kind):
        for j in trees[layer].query(shape.buffer(.7),predicate='intersects'):
            q=physical[layer][int(j)]
            if q['net']==raw:continue
            gap=.15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(q['net'])] else .6
            d=shape.distance(q['shape'])
            if d<gap+.024:physical_errors.append({'kind':kind,'uuid':uid,'other_uuid':q['uuid'],'layer':layer,'raw_net':raw,'other_raw_net':q['net'],'distance_mm':d,'required_mm':gap+.024})
    for layer,records in physical.items():
        for q in records:
            if q['uuid'] in new_ids:check_body(q['uuid'],q['net'],layer,q['shape'],'new_discrete_Cu')
    for q in addedzones:check_body(q['uuid'],q['net'],q['layer'],q['shape'],'new_positive_zone')
    collision=[]
    for i,a in enumerate(zones):
        for b in zones[i+1:]:
            if a['layer']!=b['layer'] or a['net']==b['net']:continue
            gap=.15 if h['domains_normalized'][C.norm(a['net'])]==h['domains_normalized'][C.norm(b['net'])] else .6
            d=a['shape'].distance(b['shape'])
            if d<gap+.024:collision.append({'a':a['uuid'],'b':b['uuid'],'distance_mm':d,'required_mm':gap+.024})
    print('projecting complete original fill and',len(zones),'proposed components',flush=True)
    after,cuts=N.projected(old,h,zones)
    nets=sorted(set(beforegroups)|{C.norm(q['net']) for q in zones}|{C.norm(q['net_raw']) for q in cuts});rows=[];graphs={}
    for net in nets:
        a=beforegroups.get(net)
        if a is None:a=F.graph(prior,net)
        b=F.graph(after,net);graphs[net]=b;lost=losses(a,b)
        row={'net':net,'old_groups':len(a),'new_groups':len(b),'lost_retained_discrete_relationships':lost,'verdict':'PASS' if not lost else 'FAIL'};rows.append(row)
        write(OUT/'checkpoint.json',rows);print(net,row['verdict'],len(lost),flush=True)
    roots=[]
    for net,ref,pin in [('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17')]:
        gs=graphs[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,pin) for q in xs))
        roots.append({'net':net,'actual_source':ref+'.'+pin,'rooted_named_physical_pads':len({q['uuid'] for q in gs[ri] if q['kind']=='pad' and q['pin']}),'unrooted_named_pad_groups':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]})
    assert all(sha(p)==v for p,v in pins.items())
    for name,data in [('geometry.pkl',after),('discrete.pkl',h),('proposed-zones.pkl',zones),('groups.pkl',graphs)]:(OUT/name).write_bytes(pickle.dumps(data,protocol=5))
    passed=not errors and not physical_errors and not collision and all(x['verdict']=='PASS' for x in rows)
    receipt={'verdict':'PASS_PROTECTED24_ON_R19_HOST_CONTACTS_APERTURES_NATIVE_CURRENT_OPEN' if passed else 'FAIL_PROTECTED24_ON_R19_HOST_MUTUAL_GATE','input_sha256':pins,'rows':rows,'source_root_status':roots,'apertures':apertures,'aperture_or_width_errors':errors,'independent_new_Cu_against_all_physical_Cu_errors':physical_errors,'foreign_proposed_zone_collisions':collision,'owned_new_return_carve_ownership':ownership,'restored_exact_precision_UUIDs':sorted(precision_ids),'complete_original_fill_retreat_ledger':cuts,'geometry_sha256':sha(OUT/'geometry.pkl'),'discrete_sha256':sha(OUT/'discrete.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'scope':'Completed R7 on exact R19 only. Later R23 ground/CORE/B5/analog excluded. Original198b/current native continuity and final composition remain independent gates.','signed_current_mesh_barrel_drop_thermal_all6_native_flashes_refill_and_DRC':'OPEN','native_jobs':0,'board_written':False,'adopted':False}
    write(OUT/'receipt.json',receipt);print(json.dumps({'verdict':receipt['verdict'],'loss_nets':[r['net'] for r in rows if r['verdict']=='FAIL'],'aperture_errors':len(errors),'physical_Cu_errors':len(physical_errors),'foreign_zone_collisions':len(collision)}))
if __name__=='__main__':main()
