"""Source-only single dive/return screen. No board saving or native job.

Every proposed signal via needs an existing same-domain return via touching both
conservative reference fills within 1mm. Source anchoring/final refill remain
explicitly unproved; consequently no candidate board is emitted by this script.
"""
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode=True
import screen_c06 as S
from shapely.geometry import Point, LineString, Polygon, box, mapping
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep

HERE=S.HERE
NEW_VIA_RADIUS=.3


def components(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    return [p for p in g.geoms if p.geom_type=='Polygon' and not p.is_empty]


def via_free(model,target,window):
    net=S.norm(target['net']); domain=target['domain']; blockers=[]; classes={}
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=model.records[layer][i]
            if r['kind']=='hole': gap=.25+.15
            elif r['kind']=='pad' and r['net']==net:
                # Keep new ordinary through-vias outside every SMD land plus
                # 0.1mm web; existing intentional VIPPO is untouched.
                gap=.1+NEW_VIA_RADIUS
            elif r['net']==net: continue
            elif r['kind']=='fill' and layer in ('In1.Cu','In2.Cu','In4.Cu') and r.get('domain')==domain:
                # Existing router convention: same-domain plane antipads are
                # prospective refill changes, never claimed no-loss here.
                continue
            else: gap=(.15 if r.get('domain')==domain else .6)+NEW_VIA_RADIUS
            blockers.append(r['shape'].buffer(gap+S.MARGIN)); classes[r['kind']]=classes.get(r['kind'],0)+1
        if layer in model.hard_trees:
            for i in model.hard_trees[layer].query(window.buffer(2),predicate='intersects'):
                r=model.hard[layer][i]
                if net not in r['exempt']:
                    blockers.append(r['shape'].buffer(NEW_VIA_RADIUS+S.MARGIN)); classes[r['kind']]=classes.get(r['kind'],0)+1
    # D4 is not invoked: every new via obeys general0.8mm spacing. This may
    # withhold a legitimate dense escape, but never extends the D4 exception.
    for via in model.g['vias']:
        if window.buffer(2).covers(Point(via['x'],via['y'])):
            blockers.append(Point(via['x'],via['y']).buffer(.8+S.MARGIN))
    ref1=model.reference(target['domain'],'F.Cu',window)
    ref4=model.reference(target['domain'],'In3.Cu',window)
    own_reference=ref1.intersection(ref4)
    free=window.intersection(model.outline.buffer(-.5-.3-S.MARGIN)).intersection(own_reference).difference(unary_union(blockers))
    return free,classes


def return_regions(model,target,window):
    ref=S.REF_NET[target['domain']]
    planes={layer:unary_union([r['shape'].intersection(window.buffer(2)) for r in model.records[layer]
               if r['kind']=='fill' and r['net']==ref and r['shape'].intersects(window.buffer(2))]) for layer in ('In1.Cu','In4.Cu')}
    returns=[]
    for v in model.g['vias']:
        if S.norm(v['net'])!=ref: continue
        p=Point(v['x'],v['y'])
        if not window.buffer(2).covers(p): continue
        # Exact retained native copper annulus must touch both retained fill
        # planes; merely being inside a zone outline is insufficient.
        contact=p.buffer(v['d']/2+.000002)
        if all(planes[layer].intersects(contact) for layer in planes):
            returns.append({'uuid':v['uuid'],'x':v['x'],'y':v['y'],'diameter':v['d'],
                            'return_net':ref,'source_anchor_proven':False})
    return returns


def reachable_part(free,seeds):
    out=[]
    for part in components(free):
        if any(part.covers(Point(p)) for p,r in seeds): out.append(part)
    return unary_union(out)


def sample_landings(landing,returns,component,layer,desired,max_sites=12):
    points=[]
    allowed=prep(landing)
    for rv in returns:
        for dx in range(-10,11):
            for dy in range(-10,11):
                x=round(rv['x']*10)/10+dx*.1; y=round(rv['y']*10)/10+dy*.1
                d=math.dist((x,y),(rv['x'],rv['y']))
                if d>1.0+1e-10 or d<.8+S.MARGIN: continue
                p=(round(x,6),round(y,6))
                if allowed.covers(Point(p)):
                    points.append((math.dist(p,desired),p,rv))
    unique={p:(score,p,rv) for score,p,rv in points}
    selected=[]
    for score,p,rv in sorted(unique.values()):
        if all(math.dist(p,q[1])>=.3 for q in selected): selected.append((score,p,rv))
        if len(selected)>=max_sites: break
    return [{'point_mm':list(p),'return_via':rv,'return_distance_mm':math.dist(p,(rv['x'],rv['y'])),
             'contact_layer':layer} for score,p,rv in selected], len(unique)


def main():
    targets=json.loads(S.read(HERE/'target-inventory.json'))
    for role,record in targets['source_files'].items():
        if hashlib.sha256(S.read(record['path'])).hexdigest()!=record['sha256']: raise ValueError('input changed:'+role)
    controlled={S.norm(n):v for n,v in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    S.overlay_tool.WINDOW=box(95,40,390,180)
    g,overlay=S.overlay_tool.overlay(); S.READS.update(S.overlay_tool.READS)
    reservations=json.loads(S.read(S.POWER/'sbc-c05-source-proposal/reserved-c05.json'))
    dru=S.read(S.POWER/'sbc-c05-source-proposal/reserve/board.kicad_dru').decode()
    exemptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m: exemptions[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    S.read(S.EXT/'tools/verify/return_path.py'); S.read(Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md'))
    print('DIVE_MODEL_START',flush=True); model=S.Model(g,reservations,exemptions); print('DIVE_MODEL_READY',flush=True)
    results=[]
    for target in targets['targets']:
        net=target['net']; record={'net':net,'domain':target['domain'],'width_mm':S.WIDTH,
             'native_lost_relationship':target['lost_relationships'][0],'landings':[], 'paths':[]}
        spec=controlled.get(S.norm(net))
        if spec and spec.get('class') not in (None,'NONE'):
            record.update(verdict='WITHHELD_CONTROLLED_GEOMETRY',reason='Missing effective per-layer IMP_50 geometry',controlled_spec=spec)
            results.append(record); continue
        try: groups=model.contact_groups(target)
        except ValueError as error:
            record.update(verdict='WITHHELD_COMPONENT_MODEL',reason=str(error)); results.append(record); continue
        record['physical_component_pad_ids']=[group['pad_ids'] for group in groups]
        a=unary_union([r['shape'] for r in groups[0]['records'] if r['layer'] in S.LAYERS])
        b=unary_union([r['shape'] for r in groups[1]['records'] if r['layer'] in S.LAYERS])
        pa,pb=nearest_points(a,b); desired=[tuple(pb.coords[0]),tuple(pa.coords[0])]
        window=LineString([pa,pb]).envelope.buffer(8,cap_style=3).envelope
        record['window_mm']=list(window.bounds); deadline=time.monotonic()+30
        vf,via_blockers=via_free(model,target,window); returns=return_regions(model,target,window)
        record['via_clearance_blocker_classes']=via_blockers; record['existing_reference_return_via_count']=len(returns)
        record['via_landing_area_mm2']=vf.area
        free_in3,blockers=model.free(target,'In3.Cu',window)
        ref_in3=model.reference(target['domain'],'In3.Cu',window)
        middle=free_in3.intersection(ref_in3)
        possible=[[],[]]; outer_free={}
        for gi,group in enumerate(groups):
            for layer in ('F.Cu','B.Cu'):
                if layer not in group['layers']:
                    record['landings'].append({'component':gi,'layer':layer,'reason':'no existing outer contact layer','sampled_sites':0}); continue
                free,block=model.free(target,layer,window)
                free=free.intersection(model.reference(target['domain'],layer,window))
                seeds=S.seed_sites(group,layer,free,window)
                reachable=reachable_part(free,seeds)
                landing=vf.intersection(reachable).intersection(middle)
                sites,seen=sample_landings(landing,returns,group,layer,desired[gi])
                detail={'component':gi,'layer':layer,'start_seeds':len(seeds),'sampled_sites':seen,'selected_sites':len(sites),
                        'reachable_via_landing_area_mm2':landing.area,'sites':sites}
                if not sites: detail['reason']='no source-component reachable through-via site with both reference fills and existing return<=1mm survives all-layer copper/hole/reservation constraints'
                record['landings'].append(detail)
                outer_free[(gi,layer)]=(free,seeds)
                possible[gi] += [(site,layer) for site in sites]
        pairs=sorted(((math.dist(sa['point_mm'],sb['point_mm']),sa,la,sb,lb)
                      for sa,la in possible[0] for sb,lb in possible[1]
                      if math.dist(sa['point_mm'],sb['point_mm']) >= .8+S.MARGIN),
                     key=lambda row:(row[0],row[1]['point_mm'],row[2],row[3]['point_mm'],row[4]))
        record['landing_pairs']=len(pairs)
        for _,sa,la,sb,lb in pairs[:8]:
            if time.monotonic()>deadline: break
            if math.dist(sa['point_mm'],sb['point_mm'])<.8+S.MARGIN: continue
            fake_a={'uuid':'NEW_SIGNAL_VIA_A','kind':'new_via'}; fake_b={'uuid':'NEW_SIGNAL_VIA_B','kind':'new_via'}
            mid,search=S.astar(middle,[(tuple(sa['point_mm']),fake_a)],[(tuple(sb['point_mm']),fake_b)],deadline,node_cap=70000)
            record.setdefault('middle_searches',[]).append(search)
            if not mid: continue
            fa,seeda=outer_free[(0,la)]; fb,seedb=outer_free[(1,lb)]
            start,searcha=S.astar(fa,seeda,[(tuple(sa['point_mm']),fake_a)],deadline,node_cap=25000)
            end,searchb=S.astar(fb,[(tuple(sb['point_mm']),fake_b)],seedb,deadline,node_cap=25000)
            if not start or not end: continue
            record['paths'].append({'segments':[dict(start,layer=la,width_mm=S.WIDTH),dict(mid,layer='In3.Cu',width_mm=S.WIDTH),dict(end,layer=lb,width_mm=S.WIDTH)],
                 'new_signal_vias':[dict(sa,size_mm=.6,drill_mm=.3),dict(sb,size_mm=.6,drill_mm=.3)],'new_return_vias':[],
                 'source_anchor_proven':False,'fresh_c05_refill_proven':False,'source_anchor_requirement':'same-domain physical source, not merely largest pad component',
                 'plane_change_policy':'No plane-outline edits; native refill/census must reject piece splits/islands or loss beyond ledgered via+return bounds. IO_3V3 pair neck allowance<=0.005mm2 inside pair hull+0.2mm only',
                 'qualified':False})
            break
        record['verdict']='HOST_DIVE_PATH_RETURN_SOURCE_UNPROVED' if record['paths'] else 'NO_BOUNDED_SINGLE_DIVE_RETURN_PATH'
        results.append(record)
        (HERE/'dive-progress.json').write_text(json.dumps({'results':results},indent=1)+'\n')
        print(net,record['verdict'], 'via_area',round(vf.area,3),'return',len(returns),'landing_pairs',len(pairs),flush=True)
    for p in (Path(__file__),Path(S.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__)): S.read(p)
    for path,expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected: raise ValueError('input changed:'+path)
    report={'schema':'c06-bounded-single-dive-screen-v1','evidence_class':'Host source geometry only; not native/electrical proof',
      'source_board_sha256':S.overlay_tool.C05_SHA,'overlay':overlay,'source_files_sha256':S.READS,'results':results,
      'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,
      'limits':['0.1mm grid;30sec and70000nodes per net; at most8 sampled landing pairs;8mm window expansion',
       '0.2mm traces,0.6/0.3mm ordinary vias;.15same/.6foreign/.25hole+.025geometry margin;general0.8via spacing, no D4 waiver',
       'Via lands outside all SMD pads; candidate plane penetrations limited to same-domain fills, preserved foreign planes',
       'Existing return via must touch both reference fills<=1mm; actual source anchoring and c05 freshfill remain unproved',
       'No additions are promoted; controlled IMP clock withheld; analog separation and independent signal/current/critical review open',
       'No bounded path is not global impossibility; same-domain plane antipad/island/loss behavior requires native census']}
    output=HERE/'single-dive-screen.json'; output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(output),'paths':sum(bool(r['paths']) for r in results),'targets':len(results)}),flush=True)


if __name__=='__main__':main()
