"""Bounded pure-add feasibility on actual live r07, no native/GPU/board output."""
import hashlib
import json
import math
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import screen_c06 as S
import screen_dive_c06 as D
import compose_additions as composition
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points

EXT=S.EXT
R07=EXT/'integrate/revs/r07-ripup-signals-1.kicad_pcb'
R07_SHA='0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
R06_PART=EXT/'integrate/measure/r06-stitch-plane-pads-2/partitions.json'
R07_PART=EXT/'integrate/measure/r07-ripup-signals-1/partitions.json'
PRO=EXT/'integrate/board.kicad_pro.good'
DRU=EXT/'integrate/board.kicad_dru'
RESERVER=EXT/'tools/reserve_corridors.py'
READS=S.READS


def overlay_and_targets():
    original=S.read(S.overlay_tool.base.BASE); current=S.read(R07)
    if hashlib.sha256(original).hexdigest()!=S.overlay_tool.base.BASE_SHA or hashlib.sha256(current).hexdigest()!=R07_SHA:
        raise ValueError('Frozen actual source differs')
    g=json.loads(S.read(S.overlay_tool.base.GEOM))
    if g['sha256']!=S.overlay_tool.base.BASE_SHA or not g['refilled'] or g['api_errors']:
        raise ValueError('Invalid conservative native geometry')
    before,after=composition.inventory(original),composition.inventory(current)
    arcs={r['uuid']:r for r in g['tracks'] if r.get('kind')=='arc'}
    tracks=[];vias=[]
    for uid,ch in after[4].items():
        kind=composition.pcbtext.chunk_kind(ch)
        if kind=='segment':
            tracks.append({'uuid':uid,'net':S.overlay_tool.netname(ch),'a':S.overlay_tool.numbers(ch,'start'),
                           'b':S.overlay_tool.numbers(ch,'end'),'w':S.overlay_tool.scalar(ch,'width'),
                           'layer':composition.pcbtext.chunk_layer(ch),'locked':b'(locked yes)' in ch})
        elif kind=='via':
            if b'(layers "F.Cu" "B.Cu")' not in ch or b'(via blind' in ch: raise ValueError('Unsupported via')
            x,y=S.overlay_tool.numbers(ch,'at')
            vias.append({'uuid':uid,'net':S.overlay_tool.netname(ch),'x':x,'y':y,'d':S.overlay_tool.scalar(ch,'size'),
                         'drill':S.overlay_tool.scalar(ch,'drill'),'flashed':g['copper_layers'],'span':['F.Cu','B.Cu']})
        elif uid in arcs and before[4].get(uid)==ch: tracks.append(arcs[uid])
        else: raise ValueError('Unmodeled/changed arc')
    # Exact footprint local copper + pose, zone/rule-area definitions, setup and
    # all other non-copper chunks must agree with the trusted r06 geometry.
    if before[0]!=after[0] or before[2]!=after[2] or before[5]!=after[5]:
        raise ValueError('r07 noncopper or setup differs from r06 geometry; cannot overlay conservatively')
    g['tracks'],g['vias']=tracks,vias
    g['board'],g['sha256'],g['refilled']=str(R07),R07_SHA,False
    g['domains_normalized']={S.norm(n):d for n,d in g['nets'].items()}
    old=json.loads(S.read(R06_PART)); new=json.loads(S.read(R07_PART))
    if old['sha256']!=S.overlay_tool.base.BASE_SHA or new['sha256']!=R07_SHA: raise ValueError('Native partition source differs')
    counts=Counter();pads={}
    for p in g['pads']:
        key=p['ref']+'.'+p['num']; pid=key+'#'+str(counts[key]); counts[key]+=1; pads[pid]=p
    targets=[]
    for net,groups in old['nets'].items():
        relationships=[]
        for group in groups:
            touched=[t for t in new['nets'][net] if set(t)&set(group)]
            if len(touched)>1: relationships.append({'r07_connected_pad_ids':group,'c05_split_groups':touched})
        if relationships:
            targets.append({'net':net,'domain':g['nets'][net], 'c05_groups':new['nets'][net],
               'lost_relationships':relationships,'r06_groups':groups,
               'physical_pads':[{k:pads[pid][k] for k in ('uuid','ref','num','net','x','y','smd')}
                        | {'pad_id':pid,'layers':list(pads[pid]['layers'])}
                        for group in new['nets'][net] for pid in group]})
    if len(targets)!=17 or any(len(t['lost_relationships'])!=1 or len(t['lost_relationships'][0]['c05_split_groups'])!=2 for t in targets):
        raise ValueError('Expected17 single split native relationships differs')
    return g,targets,{'native_r07_tracks':len(tracks),'native_r07_vias':len(vias),'noncopper_definitions_exact_r06':True,
        'fill_policy':'Pinned refilled r06 foreign fills, exact actual r07 copper; no current r07 fill export claimed',
        'footprints_pads_poses_unchanged_r06':True}


def reservations(g):
    compat={'pads':[],'tracks':[],'keepouts':[],'vias':[],'zones':[]}
    for p in g['pads']:
        layers=list(p['layers'])
        compat['pads'].append({k:p[k] for k in ('ref','num','net','x','y','smd')}
              | {'layers':layers,'poly':p['layers'][layers[0]] if layers else []})
    compat['tracks']=[{k:t[k] for k in ('net','layer','w','a','b')} for t in g['tracks'] if t.get('kind')!='arc']
    compat_path=HERE/'compat-r07.json'; output=HERE/'reserved-r07.json'; out_dir=HERE/'reserve'
    compat_path.write_text(json.dumps(compat),encoding='utf-8'); S.read(compat_path)
    completed=subprocess.run([sys.executable,str(RESERVER),str(compat_path),str(R07_PART),str(DRU),str(output),str(out_dir)],capture_output=True,text=True)
    (HERE/'reserve-host.log').write_text(completed.stdout+completed.stderr,encoding='utf-8')
    if completed.returncode: raise ValueError('Actual r07 reservation generation failed')
    reserved=json.loads(S.read(output)); dru=S.read(out_dir/'board.kicad_dru').decode(); S.read(out_dir/'reservations.json')
    exemptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m: exemptions[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    return reserved,exemptions




def strict_via_free(model,target,window):
    net=S.norm(target['net']); domain=target['domain']; blockers=[]; classes={}
    radius=.25
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=model.records[layer][i]
            if r['kind']=='hole': gap=.25+radius
            elif r['kind']=='pad' and r['net']==net: gap=.1+radius
            elif r['net']==net: continue
            elif r['kind']=='fill' and layer in ('In1.Cu','In2.Cu','In4.Cu') and r.get('domain')==domain: continue
            else: gap=(.15 if r.get('domain')==domain else .6)+radius
            blockers.append(r['shape'].buffer(gap+S.MARGIN)); classes[r['kind']]=classes.get(r['kind'],0)+1
        if layer in model.hard_trees:
            for i in model.hard_trees[layer].query(window.buffer(2),predicate='intersects'):
                r=model.hard[layer][i]
                if net not in r['exempt']:
                    blockers.append(r['shape'].buffer(radius+S.MARGIN));classes[r['kind']]=classes.get(r['kind'],0)+1
    for via in model.g['vias']:
        if window.buffer(2).covers(Point(via['x'],via['y'])):
            blockers.append(Point(via['x'],via['y']).buffer(.8+S.MARGIN))
    ref1=model.reference(target['domain'],'F.Cu',window);ref4=model.reference(target['domain'],'In3.Cu',window)
    free=window.intersection(model.outline.buffer(-.5-radius-S.MARGIN)).intersection(ref1.intersection(ref4)).difference(unary_union(blockers))
    return free,classes


def main():
    HERE.mkdir(exist_ok=True)
    # Capture every executed/local policy source BEFORE interpreting it, then
    # recheck the whole read set before publishing the host receipt.
    for p in (Path(__file__),Path(S.__file__),Path(D.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),
              Path(S.overlay_tool.hubs.__file__),Path(composition.__file__),Path(composition.pcbtext.__file__),
              S.ROOT/'reconcile_dfm.py',PRO,DRU,RESERVER,EXT/'tools/pairs.json',EXT/'tools/fix/power_reinforce_spec.json',
              EXT/'tools/verify/return_path.py',Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md')):S.read(p)
    controlled={S.norm(n):v for n,v in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    power={S.norm(n) for n in json.loads(S.read(EXT/'tools/power_widths.json'))}
    rules=S.read(DRU).decode()
    if '(constraint hole_size (min 0.20mm))' not in rules or '(constraint annular_width (min 0.15mm))' not in rules:
        raise ValueError('Small-via drill/annular project permission not established')
    print('ACTUAL_R07_OVERLAY_START',flush=True)
    g,targets,overlay=overlay_and_targets()
    inventory={'schema':'alternate-r07-native-targets-v1','before':S.overlay_tool.base.BASE_SHA,'after':R07_SHA,
        'target_count':17,'targets':[{k:v for k,v in t.items() if k not in ('c05_groups','lost_relationships')}
            | {'r07_groups':t['c05_groups'],'r06_connected_pad_ids':t['lost_relationships'][0]['r07_connected_pad_ids'],
               'r07_split_groups':t['lost_relationships'][0]['c05_split_groups']} for t in targets]}
    (HERE/'target-inventory.json').write_text(json.dumps(inventory,indent=1)+'\n',encoding='utf-8')
    reserved,exemptions=reservations(g)
    print('ACTUAL_R07_RESERVATIONS',len(reserved['keepouts']),flush=True)
    model=S.Model(g,reserved,exemptions); print('ACTUAL_R07_MODEL_READY',flush=True)
    results=[]
    for target in targets:
        net=target['net']; spec=controlled.get(S.norm(net)); record={'net':net,'domain':target['domain'],
           'r06_connected_pad_ids':target['lost_relationships'][0]['r07_connected_pad_ids'],
           'r07_split_groups':target['lost_relationships'][0]['c05_split_groups'],'width_mm':S.WIDTH,
           'zero_via_layers':[],'dive_landings':[],'paths':[]}
        if S.norm(net) in power:
            record.update(verdict='WITHHELD_POWER_NET',reason='Small ordinary signal-via trial excludes every power_widths rail')
            results.append(record); continue
        if spec and spec.get('class') not in (None,'NONE'):
            record.update(verdict='WITHHELD_CONTROLLED_GEOMETRY',controlled_spec=spec,
                          reason='Current sibling project has no effective IMP class/layer geometry; generic0.2mm withheld')
            results.append(record); print(net,record['verdict'],flush=True); continue
        # AO1_VREF is not treated as a digital signal merely because it lacks
        # a CI class. Analog reference noise/current routing must be explicit.
        if S.norm(net).endswith('/AO1_VREF'):
            record.update(verdict='WITHHELD_ANALOG_REFERENCE',reason='Quiet DAC analog VREF requires dedicated noise/current/return review; no generic signal bypass')
            results.append(record); print(net,record['verdict'],flush=True); continue
        try: groups=model.contact_groups(target)
        except ValueError as error:
            record.update(verdict='WITHHELD_PHYSICAL_MODEL',reason=str(error)); results.append(record); print(net,record['verdict'],flush=True);continue
        record['physical_r07_component_pad_ids']=[group['pad_ids'] for group in groups]
        a=unary_union([r['shape'] for r in groups[0]['records'] if r['layer'] in S.LAYERS]); b=unary_union([r['shape'] for r in groups[1]['records'] if r['layer'] in S.LAYERS])
        pa,pb=nearest_points(a,b); window=LineString([pa,pb]).envelope.buffer(8,cap_style=3).envelope
        record['window_mm']=list(window.bounds); deadline=time.monotonic()+24
        for layer in S.LAYERS:
            if layer not in groups[0]['layers'] or layer not in groups[1]['layers']:
                record['zero_via_layers'].append({'layer':layer,'reason':'no pre-existing contact layer for both components'});continue
            free,blockers=model.free(target,layer,window); reference=model.reference(target['domain'],layer,window); free=free.intersection(reference)
            seeds=[S.seed_sites(group,layer,free,window) for group in groups]
            path,search=S.astar(free,seeds[0],seeds[1],deadline) if all(seeds) else (None,{'reason':'no strict reference-covered physical attachment','nodes':0})
            record['zero_via_layers'].append({'layer':layer,'attachment_counts':[len(s) for s in seeds],'search':search,'blockers':blockers})
            if path:
                record['paths'].append({'segments':[dict(path,layer=layer,width_mm=S.WIDTH)],'new_signal_vias':[],
                  'reference_net':S.REF_NET[target['domain']],'source_anchor_proven':False,'fresh_r07_refill_proven':False,'qualified':False});break
        if not record['paths'] and time.monotonic()<deadline:
            vf,classes=strict_via_free(model,target,window); returns=D.return_regions(model,target,window)
            record['via_landing_area_mm2']=vf.area; record['via_blocker_classes']=classes; record['existing_return_via_count']=len(returns)
            middle=model.free(target,'In3.Cu',window)[0].intersection(model.reference(target['domain'],'In3.Cu',window))
            outer_free={}; possible=[[],[]]; desired=[tuple(pb.coords[0]),tuple(pa.coords[0])]
            for gi,group in enumerate(groups):
                for layer in ('F.Cu','B.Cu'):
                    if layer not in group['layers']:continue
                    free=model.free(target,layer,window)[0].intersection(model.reference(target['domain'],layer,window))
                    seeds=S.seed_sites(group,layer,free,window); reachable=D.reachable_part(free,seeds)
                    landing=vf.intersection(reachable).intersection(middle)
                    sites,seen=D.sample_landings(landing,returns,group,layer,desired[gi],max_sites=10)
                    record['dive_landings'].append({'component':gi,'layer':layer,'physical_seed_count':len(seeds),
                        'reachable_via_landing_area_mm2':landing.area,'sampled_sites':seen,'selected_sites':sites})
                    possible[gi]+=[(site,layer) for site in sites]; outer_free[(gi,layer)]=(free,seeds)
            pairs=sorted(((math.dist(sa['point_mm'],sb['point_mm']),sa,la,sb,lb)
                 for sa,la in possible[0] for sb,lb in possible[1] if math.dist(sa['point_mm'],sb['point_mm'])>=.8+S.MARGIN),
                 key=lambda row:(row[0],row[1]['point_mm'],row[2],row[3]['point_mm'],row[4]))
            record['sampled_landing_pairs']=len(pairs)
            for _,sa,la,sb,lb in pairs[:6]:
                if time.monotonic()>deadline:break
                va={'kind':'new_via','uuid':'NEW_SIGNAL_VIA_A'};vb={'kind':'new_via','uuid':'NEW_SIGNAL_VIA_B'}
                mid,search=S.astar(middle,[(tuple(sa['point_mm']),va)],[(tuple(sb['point_mm']),vb)],deadline,node_cap=50000)
                record.setdefault('middle_searches',[]).append(search)
                if not mid:continue
                fa,seed_a=outer_free[(0,la)];fb,seed_b=outer_free[(1,lb)]
                start,search_a=S.astar(fa,seed_a,[(tuple(sa['point_mm']),va)],deadline,node_cap=20000)
                end,search_b=S.astar(fb,[(tuple(sb['point_mm']),vb)],seed_b,deadline,node_cap=20000)
                if start and end:
                    record['paths'].append({'segments':[dict(start,layer=la,width_mm=S.WIDTH),dict(mid,layer='In3.Cu',width_mm=S.WIDTH),dict(end,layer=lb,width_mm=S.WIDTH)],
                     'new_signal_vias':[dict(sa,size_mm=.5,drill_mm=.2),dict(sb,size_mm=.5,drill_mm=.2)],'new_return_vias':[],
                     'reference_net':S.REF_NET[target['domain']],'source_anchor_proven':False,'fresh_r07_refill_proven':False,'qualified':False});break
        record['verdict']='HOST_PATH_SOURCE_RETURN_UNPROVED' if record['paths'] else 'NO_BOUNDED_ADDITIVE_PATH'
        results.append(record)
        (HERE/'progress.json').write_text(json.dumps({'results':results},indent=1)+'\n',encoding='utf-8')
        print(net,record['verdict'],'landing_pairs',record.get('sampled_landing_pairs',0),flush=True)
    for path,expected in READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('Source/tool changed during screen:'+path)
    report={'schema':'alternate-r07-bounded-additive-small-via-screen-v1','source_board_sha256':R07_SHA,'baseline_board_sha256':S.overlay_tool.base.BASE_SHA,
      'evidence_class':'Host source geometry only; native electrical/source anchored return not run','overlay':overlay,
      'source_files_sha256':READS,'results':results,'adopted':False,'board_emitted':False,'manufacturing_ready':False,'native_jobs':0,'gpu_jobs':0,
      'retained_live_r07_copper_policy':'Every native r07 item must be preserved byte-exact in any later composition',
      'limits':['24sec per target;0.1mm grid;70000zero-via or50000middle nodes;8mm local-window growth;6 landing pairs',
       'General .2mm signals only; controlled routes missing effective geometry withheld; quiet analog reference separately withheld',
       'All actual r07 copper, original pads/poses, conservative r06 foreign fills, original power/pair/escape/return reservations retained',
       'No new VIPPO/D4 exceptions; .5/.2via,.8spacing,.15same/.6foreign/.25hole plus .025mm margin',
       'Existing same-domain return via must geometrically touch In1/In4 refs<=1mm; physical source anchor not proven',
       'Any native composition still requires zero-loss vsr06 AND r07, rawDRC, plane/island/neck ledger, return/current/critical/analog/controlled gates']}
    output=HERE/'feasibility.json';output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(output),'paths':sum(bool(r['paths']) for r in results),'targets':len(results),'composed':False}),flush=True)


if __name__=='__main__':main()
