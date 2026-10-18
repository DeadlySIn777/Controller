"""Independent protected recipe mutual/no-loss audit on a later power model."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import hashlib,json,math,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def main():
    assert len(sys.argv)==4,'baseline_model.pkl joint_model.pkl fresh_output_directory'
    basefile,jointfile,out=map(lambda x:Path(x).resolve(),sys.argv[1:]);assert out.is_relative_to(H) and not out.exists()
    old,bh,binding,bz,prior=pickle.loads(basefile.read_bytes());g,h,bb,zones,after=pickle.loads(jointfile.read_bytes());assert binding==bb
    rp=H/'protected24-dogbones-r7';rr=json.loads((rp/'receipt.json').read_bytes());new=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());added=pickle.loads((rp/'proposed-zones.pkl').read_bytes())
    assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'] and sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256']
    out.mkdir();errors=[];physical_errors=[];zone_errors=[]
    smd=[unary_union(C.poly(ps)) for p in h['pads'] if p['smd'] for layer,ps in p['layers'].items() if layer in ('F.Cu','B.Cu')];st=STRtree(smd)
    holes=[s for p in h['pads'] for s in C.poly(p.get('hole') or [])];ht=STRtree(holes)
    for v in new['vias']:
        pt=Point(v['x'],v['y'])
        for i in st.query(pt.buffer(v['drill']/2+.7),predicate='intersects'):
            d=pt.distance(smd[int(i)])-v['drill']/2
            if d<.275-1e-9:errors.append({'kind':'SMD_drill','uuid':v['uuid'],'edge_gap_mm':d})
        for w in h['vias']:
            if w['uuid']==v['uuid']:continue
            d=math.hypot(v['x']-w['x'],v['y']-w['y'])-(v['drill']+w['drill'])/2
            if d<.275-1e-9:errors.append({'kind':'via_drill','uuid':v['uuid'],'other_uuid':w['uuid'],'edge_gap_mm':d})
        for i in ht.query(pt.buffer(v['drill']/2+.7),predicate='intersects'):
            d=pt.distance(holes[int(i)])-v['drill']/2
            if d<.275-1e-9:errors.append({'kind':'pad_drill','uuid':v['uuid'],'edge_gap_mm':d})
    errors += [{'kind':'trace_floor','uuid':t['uuid'],'width_mm':t['w']} for t in new['tracks'] if t['w']<.2-1e-9]
    physical,trees=F.build({**h,'zones':[]});newids={q['uuid'] for kind in ('tracks','vias') for q in new[kind]}
    def clearance(raw,other):return .15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(other)] else .6
    bodies=[]
    for layer,rs in physical.items():
        bodies.extend((q['uuid'],q['net'],layer,q['shape'],'protected_new_discrete') for q in rs if q['uuid'] in newids)
    bodies.extend((q['uuid'],q['net'],q['layer'],q['shape'],'protected_new_plane') for q in added)
    for uid,raw,layer,shape,kind in bodies:
        for i in trees[layer].query(shape.buffer(.7),predicate='intersects'):
            q=physical[layer][int(i)]
            if q['net']==raw:continue
            d=shape.distance(q['shape']);need=clearance(raw,q['net'])+.024
            if d<need:physical_errors.append({'kind':kind,'uuid':uid,'other_uuid':q['uuid'],'layer':layer,'distance_mm':d,'required_mm':need})
        for q in zones:
            if q['net']==raw or q['layer']!=layer:continue
            d=shape.distance(q['shape']);need=clearance(raw,q['net'])+.024
            if d<need:physical_errors.append({'kind':kind+'_vs_new_zone','uuid':uid,'other_uuid':q['uuid'],'layer':layer,'distance_mm':d,'required_mm':need})
    for i,a in enumerate(zones):
        for b in zones[i+1:]:
            if a['layer']!=b['layer'] or a['net']==b['net']:continue
            d=a['shape'].distance(b['shape']);need=clearance(a['net'],b['net'])+.024
            if d<need:zone_errors.append({'a':a['uuid'],'b':b['uuid'],'layer':a['layer'],'distance_mm':d,'required_mm':need})
    nets=sorted({C.norm(q['net']) for q in bz+zones}|{C.norm(q['net']) for kind in ('tracks','vias') for q in new[kind]})
    rows=[];graphs={}
    for net in nets:
        before=F.graph(prior,net);now=F.graph(after,net);lost=losses(before,now);graphs[net]=now
        row={'net':net,'old_groups':len(before),'new_groups':len(now),'lost_retained_discrete_relationships':lost,'verdict':'PASS' if not lost else 'FAIL'};rows.append(row)
        write(out/'checkpoint.json',rows);print('JOINT',net,row['verdict'],len(lost),flush=True)
    roots=[]
    for net,ref,pin in [('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17')]:
        groups=graphs[net];root=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,pin) for q in xs))
        roots.append({'net':net,'actual_source':ref+'.'+pin,'rooted_named_physical_pads':len({q['uuid'] for q in groups[root] if q['kind']=='pad' and q['pin']}),'unrooted_named_groups':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(groups) if i!=root and any(q['kind']=='pad' and q['pin'] for q in xs)]})
    (out/'groups.pkl').write_bytes(pickle.dumps(graphs,protocol=5))
    passed=not errors and not physical_errors and not zone_errors and all(q['verdict']=='PASS' for q in rows)
    report={'verdict':'PASS_PROTECTED_LATEST_MODEL_MUTUAL_CONTACT_NATIVE_CURRENT_OPEN' if passed else 'FAIL_PROTECTED_LATEST_MODEL_MUTUAL_CONTACT','input_sha256':{str(p):sha(p) for p in (Path(__file__).resolve(),basefile,jointfile,rp/'receipt.json',rp/'proposed-discrete.pkl',rp/'proposed-zones.pkl',Path(F.__file__).resolve(),Path(C.__file__).resolve())},'aperture_or_width_errors':errors,'new_protected_all_physical_Cu_errors':physical_errors,'foreign_proposed_zone_collisions':zone_errors,'rows':rows,'source_root_status':roots,'groups_sha256':sha(out/'groups.pkl'),'original198b_and_native_dc936_full_source_obligations':'SEPARATE_OPEN','signed_current_mesh_drop_barrel_thermal_native_flashes_refill_and_DRC':'OPEN','board_written':False,'native_jobs':0,'adopted':False}
    write(out/'receipt.json',report);print(json.dumps({'verdict':report['verdict'],'aperture_errors':len(errors),'physical_errors':len(physical_errors),'foreign_zone_errors':len(zone_errors),'loss_nets':[q['net'] for q in rows if q['verdict']=='FAIL']}),flush=True)
if __name__=='__main__':main()
