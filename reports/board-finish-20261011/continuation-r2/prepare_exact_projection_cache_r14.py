"""Memoize repeated identical cutter buffers inside one exact GP58 projection."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'sbc-power/guarded_declared_settings_projection_r58.py';o=H/'sbc-power/guarded_declared_settings_projection_cached_r14.py';assert not o.exists()
s=p.read_text();a='    changed=changed_ids(g,h);cache={};ledger=[];result=[]'
b='''    changed=changed_ids(g,h);cache={};ledger=[];result=[]
    for kind in ('tracks','vias','pads'):
        assert len({q['uuid']for q in h[kind]})==len(h[kind])
    assert len({q['uuid']for q in zones})==len(zones)
    memo={}
    def cached(kind,uid,part,shape,distance):
        key=(kind,uid,part,distance)
        if key not in memo:memo[key]=bounded_buffer(shape,distance)
        return memo[key]
'''
assert s.count(a)==1;s=s.replace(a,b)
replacements={"bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear+.025)":"cached('track',t['uuid'],0,LineString([t['a'],t['b']]),t['w']/2+clear+.025)","bounded_disk(v,radius),'changed_via_outward_Cu_and_hole'":"cached('via',v['uuid'],0,Point(v['x'],v['y']),radius),'changed_via_outward_Cu_and_hole'","for sh in p.base.polygons(q['layers'].get(layer,[])):rows.append((q['uuid'],bounded_buffer(sh,clear+.025)":"for part,sh in enumerate(p.base.polygons(q['layers'].get(layer,[]))):rows.append((q['uuid'],cached('pad-'+layer,q['uuid'],part,sh,clear+.025)","bounded_buffer(q['shape'],clear+.025),'new_zone_outward_polygon'":"cached('zone',q['uuid'],0,q['shape'],clear+.025),'new_zone_outward_polygon'"}
for a,b in replacements.items():assert s.count(a)==1,a;s=s.replace(a,b)
compile(s,str(o),'exec');o.write_text(s)
(H/'exact-projection-cache-r14-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'only_per_call_exact_operator_memoization_by_unique_source_kind_UUID_part_and_actual_buffer_distance':True,'unchanged_outward_2nm_256edge_bounded_buffer_1nm_precision_and_union_row_order':True,'unchanged_native_original_zone_outlines_and_perzone_settings':True,'equivalence_actual_source_geometry_and_full_retreat_ledger':'REQUIRES_INDEPENDENT_CHECK_BEFORE_USE','native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'script':str(o),'sha256':sha(o)}))
