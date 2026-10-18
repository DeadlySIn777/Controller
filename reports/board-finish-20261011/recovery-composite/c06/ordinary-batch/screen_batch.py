"""Modest source-only zero-via digital batch on actual r07, keeping two paths."""
import hashlib,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE.parent/'alternate-r07'))
import screen_r07 as R
import screen_c06 as S
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree

def source_refs(model,g,old,current):
    changed=set(current[4])-{uid for uid,ch in old[4].items() if current[4].get(uid)==ch}
    changed_plane=[uid for uid in changed if R.composition.pcbtext.chunk_kind(current[4][uid]) in ('segment','arc')
                   and R.composition.pcbtext.chunk_layer(current[4][uid]) in ('In1.Cu','In4.Cu')]
    if changed_plane:raise ValueError('Newchangedplane-trackcuttersrequired')
    foreign=[v for v in g['vias'] if v['uuid'] in changed and S.norm(v['net'])!='/LOGIC_GND']
    cuts=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+(.15 if g['domains_normalized'].get(S.norm(v['net']))=='DOM_LOGIC' else .6)+.025) for v in foreign])
    result={}
    for layer in ('In1.Cu','In4.Cu'):
        fills=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']=='/LOGIC_GND'])
        safe=fills.difference(cuts)
        own=[r['shape'] for r in model.records[layer] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','via','track')]
        conductive=unary_union([safe]+own);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][layer]))
        parts=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms)
        result[layer]=safe.intersection(unary_union([part for part in parts if part.intersects(anchor)]))
    return result,{'changed_plane_tracks_or_arcs':changed_plane,'foreign_via_cutters':len(foreign),'source_anchor':'J11001.2#0'}

def main():
    HERE.mkdir(exist_ok=True)
    for p in (Path(__file__),Path(S.__file__),Path(R.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),
              S.EXT/'tools/power_widths.json',R.PRO,R.DRU,S.CONTROLLED):S.read(p)
    controlled={S.norm(n):v for n,v in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    power={S.norm(n) for n in json.loads(S.read(S.EXT/'tools/power_widths.json'))}
    g,_,overlay=R.overlay_and_targets();parts=json.loads(S.read(R.R07_PART))
    old=R.composition.inventory(S.read(S.overlay_tool.base.BASE));current=R.composition.inventory(S.read(R.R07))
    two=json.loads(S.read(HERE.parent/'two-zero-via/audit.json'))
    if two['verdict']!='HOST_PASS_NATIVE_OPEN':raise ValueError('Prior2preflightnotpassed')
    taken={S.norm(row['net']) for row in two['rows']}
    for row in two['rows']:
        for route in row['segments']:
            for i,(a,b) in enumerate(zip(route['points_mm'],route['points_mm'][1:])):
                g['tracks'].append({'uuid':'FROZEN_TWO_'+S.norm(row['net'])+'_'+str(i),'net':row['net'],'a':a,'b':b,'w':.2,'layer':'B.Cu'})
    reserved=json.loads(S.read(HERE.parent/'alternate-r07/reserved-r07.json'))
    dru=S.read(HERE.parent/'alternate-r07/reserve/board.kicad_dru').decode();exemptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exemptions[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    print('BATCH_MODEL_START',flush=True);model=S.Model(g,reserved,exemptions)
    refs,refaudit=source_refs(model,g,old,current);print('BATCH_SOURCE_REF_READY',flush=True)
    candidates=[];excluded={}
    clock=re.compile(r'(CLK|SCLK|SCK|XTAL|OSC|USB|HDMI|MDI|_SW$|PHASE|BOOT|VREF|DVDT|ILIM|AGND|_COM$)',re.I)
    for net,groups in parts['nets'].items():
        n=S.norm(net);spec=controlled.get(n)
        if len(groups)<2 or n in taken:continue
        if g['domains_normalized'].get(n)!='DOM_LOGIC':continue
        if n in power or spec is None or spec.get('class')!='NONE' or clock.search(n):continue
        if not any(p.get('pintype') in ('input','output','bidirectional','open_collector','open_emitter','tri_state') for p in spec.get('end_parts',[])):continue
        group_shapes=[]
        for group in groups:
            group_shapes.append(unary_union([poly for pid in group for layer in ('F.Cu','B.Cu')
                  for poly in S.poly(model.pads[pid]['layers'].get(layer,[]))]))
        best=min((a.distance(b),i,j) for i,a in enumerate(group_shapes) for j,b in enumerate(group_shapes) if i<j)
        if best[0]<=12:candidates.append((best[0],net,best[1],best[2]))
    candidates=sorted(candidates)[:32];results=[];accepted=[];batch_deadline=time.monotonic()+120
    for distance,net,gi,gj in candidates:
        if time.monotonic()>batch_deadline:break
        native_groups=parts['nets'][net]
        target={'net':net,'domain':'DOM_LOGIC','c05_groups':native_groups,
           'lost_relationships':[{'r07_connected_pad_ids':native_groups[gi]+native_groups[gj]}]}
        record={'net':net,'pad_group_distance_mm':distance,'native_before_groups':[native_groups[gi],native_groups[gj]],'paths':[],'layers':[]}
        try:groups=model.contact_groups(target)
        except ValueError as error:
            record.update(verdict='WITHHELD_PHYSICAL_MODEL',reason=str(error));results.append(record);continue
        for layer in ('F.Cu','B.Cu'):
            if any(layer not in group['layers'] for group in groups):continue
            a=unary_union([r['shape'] for r in groups[0]['records'] if r['layer']==layer]);b=unary_union([r['shape'] for r in groups[1]['records'] if r['layer']==layer]);pa,pb=nearest_points(a,b)
            window=LineString([pa,pb]).envelope.buffer(3,cap_style=3).envelope
            free,blockers=model.free(target,layer,window);free=free.intersection(refs['In1.Cu']).intersection(refs['In4.Cu'])
            seeds=[S.seed_sites(group,layer,free,window) for group in groups]
            path,search=S.astar(free,seeds[0],seeds[1],min(batch_deadline,time.monotonic()+3),node_cap=10000) if all(seeds) else (None,{'reason':'no exact source-ref covered endpoint','nodes':0})
            record['layers'].append({'layer':layer,'window_mm':list(window.bounds),'seed_counts':[len(s) for s in seeds],'search':search})
            if not path:continue
            path.update(layer=layer,width_mm=.2,new_vias=[],source_anchor_host_both_planes=True,fresh_native_return_proven=False)
            record['paths'].append(path)
            # Every next net sees all already-kept new copper. Earlier source
            # paths remain immutable, and source reservation policy stays fixed.
            for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
                rec={'uuid':'BATCH_NEW_'+net+'_'+str(i),'net':S.norm(net),'domain':'DOM_LOGIC','kind':'track',
                    'shape':LineString([a,b]).buffer(.1),'layer':layer,'key':('t','BATCH_NEW_'+net+'_'+str(i)),'sites':[a,b]}
                model.records[layer].append(rec)
            model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]])
            accepted.append(record);taken.add(S.norm(net));break
        record['verdict']='HOST_PATH_NATIVE_OPEN' if record['paths'] else 'NO_BOUNDED_ZERO_VIA_PATH'
        results.append(record);print(net,record['verdict'],flush=True)
        if len(accepted)>=8:break
    for path,expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('Batchinputchanged:'+path)
    output={'schema':'ordinary-digital-r07-zero-via-batch-v1','source_board_sha256':R.R07_SHA,'source_files_sha256':S.READS,
        'reference_source_audit':refaudit,'overlay':overlay,'results':results,'accepted_count':len(accepted),'initial_candidate_count':len(candidates),
        'frozen_two_paths_present_as_obstacles':True,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,
        'limits':['Atmost32 shortest candidates<=12mm;120sec batch;3sec/10000nodes per layer;3mm window;max8 newpaths',
          'OnlyDOM_LOGIC,classNONE,active digital pin, no power/analog/clock/external unclassified net',
          'Zero vias/plane edits; fullsource-anchored conservative In1/In4 reference, margin and reservations',
          'Eachaccepted path obstructs laternets; source freeze and freshindependent/native checks still required']}
    (HERE/'feasibility.json').write_text(json.dumps(output,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(HERE/'feasibility.json'),'accepted':len(accepted),'examined':len(results)}),flush=True)

if __name__=='__main__':main()
