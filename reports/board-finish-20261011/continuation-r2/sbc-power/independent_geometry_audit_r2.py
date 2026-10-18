"""Independent physical-clearance audit of quantized cross-agent geometry."""
import json,math,hashlib
from pathlib import Path
from shapely.geometry import Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
import complete_geometry_r2 as G
L=G.L;p=G.p
def main():
    g,h,tail,binding,zones=G.model();oldt={q['uuid'] for q in g['tracks']};oldv={q['uuid'] for q in g['vias']};newt=[q for q in h['tracks'] if q['uuid'] not in oldt];newv=[q for q in h['vias'] if q['uuid'] not in oldv];layers=h['copper_layers'];items={k:[] for k in layers};fail=[];checks=0
    for q in h['pads']:
        for lay,rs in q['layers'].items():
            for sh in p.base.polygons(rs):items[lay].append((sh,{'kind':'pad','uuid':q['uuid'],'ref':q['ref'],'pad':q['num'],'net':q['net'],'smd':q['smd']}))
    for t in h['tracks']:items[t['layer']].append((p.base.body(t),{'kind':'track','uuid':t['uuid'],'net':t['net']}))
    for v in h['vias']:
        for lay in v['flashed']:items[lay].append((Point(v['x'],v['y']).buffer(v['d']/2),{'kind':'via','uuid':v['uuid'],'net':v['net']}))
    for q in h['shapes']:
        if q['layer'] in items:
            for sh in p.base.polygons(q['poly']):items[q['layer']].append((sh,{'kind':'graphic','uuid':q['uuid'],'net':q.get('net','')}))
    trees={k:STRtree([s for s,_ in rows]) for k,rows in items.items()};minimum={};seen=set()
    def compare(uid,net,layer,shape,kind):
        nonlocal checks
        for i in trees[layer].query(shape.buffer(.65)):
            other,meta=items[layer][int(i)]
            if meta['uuid']==uid or p.norm(meta['net'])==p.norm(net):continue
            key=(layer,*sorted((uid,meta['uuid'])))
            if key in seen:continue
            seen.add(key);checks+=1;gap=shape.distance(other);req=G.gap(h,net,meta['net']);minimum[kind]=min(minimum.get(kind,1e6),gap-req)
            if gap<req-1e-6:fail.append({'kind':kind,'uuid':uid,'layer':layer,'net':net,'other':meta,'gap_mm':gap,'required_mm':req})
    for t in newt:compare(t['uuid'],t['net'],t['layer'],p.base.body(t),'new_track')
    for v in newv:
        pt=Point(v['x'],v['y']);disc=pt.buffer(v['d']/2)
        for lay in v['flashed']:
            compare(v['uuid'],v['net'],lay,disc,'new_via')
            for i in trees[lay].query(pt.buffer(v['drill']/2+.26)):
                sh,meta=items[lay][int(i)]
                if meta['kind']!='pad' or not meta['smd']:continue
                checks+=1;gap=pt.distance(sh)-v['drill']/2
                if gap<.25-1e-6:fail.append({'kind':'ordinary_SMD_drill_Cu_aperture','uuid':v['uuid'],'layer':lay,'other':meta,'gap_mm':gap,'required_mm':.25})
    for q in zones:compare(q['uuid'],q['net'],q['layer'],q['shape'],'new_plane')
    for i,a in enumerate(zones):
        for b in zones[i+1:]:
            if a['layer']!=b['layer'] or p.norm(a['net'])==p.norm(b['net']):continue
            req=G.gap(h,a['net'],b['net']);gap=a['shape'].distance(b['shape']);checks+=1
            if gap<req-1e-6:fail.append({'kind':'new_plane_pair','uuid':a['uuid'],'other_uuid':b['uuid'],'layer':a['layer'],'gap_mm':gap,'required_mm':req})
    vt=STRtree([Point(v['x'],v['y']).buffer(v['drill']/2) for v in h['vias']]);vv=h['vias']
    for v in newv:
        sh=Point(v['x'],v['y']).buffer(v['drill']/2)
        for i in vt.query(sh.buffer(.255)):
            o=vv[int(i)]
            if o['uuid']==v['uuid']:continue
            gap=math.dist((v['x'],v['y']),(o['x'],o['y']))-(v['drill']+o['drill'])/2;checks+=1
            if gap<.25-1e-6:fail.append({'kind':'drill_pair','uuid':v['uuid'],'other_uuid':o['uuid'],'gap_mm':gap,'required_mm':.25})
    result={'exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'checks':checks,'new_track_count':len(newt),'new_via_count':len(newv),'prospective_plane_count':len(zones),'all_physical_clearance_checks_pass':not fail,'failures':fail,'minimum_margin_mm_by_kind':minimum,'source_pad_aperture_mask_paste_native_body_and_effective_rule_gates_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'independent-geometry-audit-r2.json').write_text(json.dumps(result,indent=2)+'\n');print('INDEPENDENT_AUDIT',checks,len(fail),len(newt),len(newv),flush=True);print(json.dumps(fail[:12]))
if __name__=='__main__':main()
