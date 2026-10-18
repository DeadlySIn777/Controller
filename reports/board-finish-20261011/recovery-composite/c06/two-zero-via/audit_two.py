"""Independent direct-distance/physical-reference checks for two r07 additions."""
import hashlib,json,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE.parent/'alternate-r07'))
import screen_r07 as R
import screen_c06 as S
from shapely.geometry import Point,LineString
from shapely.ops import unary_union

SELECT={'/motherboard_io_control/DIC_NRST_N','/motherboard_acc_control/AI_POWER_GOOD_HOST'}


def main():
    HERE.mkdir(exist_ok=True)
    source_report=json.loads(S.read(HERE.parent/'alternate-r07/feasibility.json'))
    for path,expected in source_report['source_files_sha256'].items():
        if hashlib.sha256(S.read(path)).hexdigest()!=expected:raise ValueError('Frozen screen input changed:'+path)
    for p in (Path(__file__),Path(R.__file__),Path(S.__file__)):S.read(p)
    g,targets,overlay=R.overlay_and_targets()
    reserved=json.loads(S.read(HERE.parent/'alternate-r07/reserved-r07.json'))
    dru=S.read(HERE.parent/'alternate-r07/reserve/board.kicad_dru').decode()
    import re
    exemptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exemptions[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    print('TWO_MODEL_START',flush=True);model=S.Model(g,reserved,exemptions);print('TWO_MODEL_READY',flush=True)
    refs={};witnesses={}
    old=R.composition.inventory(S.read(S.overlay_tool.base.BASE)); current=R.composition.inventory(S.read(R.R07))
    changed=set(current[4])-{uid for uid,ch in old[4].items() if current[4].get(uid)==ch}
    new_foreign=[v for v in g['vias'] if v['uuid'] in changed and S.norm(v['net'])!='/LOGIC_GND']
    for layer in ('In1.Cu','In4.Cu'):
        fills=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']=='/LOGIC_GND'])
        # R07 new foreign barrels can alter old fill. Remove their whole copper
        # envelope +actual domain clearance+.025mm; retained old antipads stay.
        cutters=[Point(v['x'],v['y']).buffer(v['d']/2+(.15 if g['domains_normalized'].get(S.norm(v['net']))=='DOM_LOGIC' else .6)+.025) for v in new_foreign]
        safe=fills.difference(unary_union(cutters))
        own=[r['shape'] for r in model.records[layer] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','via','track')]
        conductive=unary_union([safe]+own)
        anchor=model.pads['J11001.2#0']
        anchor_poly=unary_union(S.poly(anchor['layers'][layer]))
        parts=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms)
        anchored=[part for part in parts if part.intersects(anchor_poly)]
        refs[layer]=safe.intersection(unary_union(anchored))
        witnesses[layer]={'source_anchor_pad_id':'J11001.2#0','source_anchor_uuid':anchor['uuid'],
          'source_anchor_xy_mm':[anchor['x'],anchor['y']], 'anchored_component_count':len(anchored),
          'new_r07_foreign_via_antipads_removed':len(new_foreign),'candidate_new_vias':0,
          'evidence':'Conservative r06 fill minus exact r07 new foreign barrels, physically joined through retained own ground copper to actual input0V pad. Fresh native return proof still required'}
    barrier_refs={x['refdes'] for x in json.loads(S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
    rows=[]
    for record in source_report['results']:
        if S.norm(record['net']) not in SELECT:continue
        target=next(t for t in targets if t['net']==record['net']);groups=model.contact_groups(target)
        path=record['paths'][0]
        if path['new_signal_vias'] or len(path['segments'])!=1:raise ValueError('Onlyzero-via single-layer paths')
        segment=path['segments'][0]
        if segment['layer']!='B.Cu' or segment['width_mm']!=.2:raise ValueError('Unexpectedgeometry')
        points=segment['points_mm'];line=LineString(points);net=S.norm(record['net']);fail=[];minimum={}
        for endpoint,group,uid in [(points[0],groups[0],segment['source_uuid']),(points[-1],groups[1],segment['target_uuid'])]:
            owner=[r for r in group['records'] if r['uuid']==uid and r['layer']=='B.Cu']
            if not owner or not any(r['shape'].covers(Point(endpoint)) for r in owner):fail.append('Exact conductive endpoint/UUID mismatch')
        for r in model.records['B.Cu']:
            if r['net']==net:continue
            gap=.25 if r['kind']=='hole' else .15 if r.get('domain')=='DOM_LOGIC' else .6
            distance=line.distance(r['shape'])-.1
            minimum[r['kind']]=min(minimum.get(r['kind'],999),distance)
            if distance<gap+.025-.000001:fail.append({'kind':r['kind'],'uuid':r.get('uuid'),'net':r['net'],'copper_gap_mm':distance,'required_mm':gap+.025})
        for r in model.hard['B.Cu']:
            if net not in r['exempt'] and line.buffer(.125).intersects(r['shape']):fail.append({'kind':r['kind'],'name':r['name']})
        for foot in g['footprints']:
            if foot['ref'] in barrier_refs:
                for polys in foot['courtyard'].values():
                    for shape in S.poly(polys):
                        if line.buffer(.125).intersects(shape.buffer(.6)):fail.append({'kind':'barrier_courtyard','ref':foot['ref']})
        reference={layer:refs[layer].covers(line) for layer in refs}
        if not all(reference.values()):fail.append({'kind':'source_anchored_reference_screen','both_planes':reference})
        rows.append({'net':record['net'],'physical_pad_groups':record['physical_r07_component_pad_ids'],'segments':[segment],
          'new_vias':[],'new_stitches':[],'minimum_gap_by_object_kind_mm':minimum,
          'reference_source_connected_both_planes':reference,'failures':fail,'verdict':'HOST_PASS_NATIVE_OPEN' if not fail else 'FAIL'})
        print(record['net'],rows[-1]['verdict'],reference,flush=True)
    if len(rows)!=2:raise ValueError('Expectedtwo paths')
    for path,expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('Auditinputchanged:'+path)
    report={'schema':'r07-two-zero-via-direct-audit-v1','verdict':'HOST_PASS_NATIVE_OPEN' if all(r['verdict']=='HOST_PASS_NATIVE_OPEN' for r in rows) else 'FAIL',
      'source_board_sha256':R.R07_SHA,'before_r06_sha256':S.overlay_tool.base.BASE_SHA,'rows':rows,'reference_witnesses':witnesses,
      'source_files_sha256':S.READS,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,
      'limits':['Source/host exact geometry evidence, no fresh current r07 filled export',
        'Native DRC, both native baseline partitions, physical-source return, whole-board electrical/SI/critical gates still required',
        'No netclass/rule/component/copper/plane changes to baseline; two newB.Cu0.2mm paths only']}
    (HERE/'audit.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'audit':str(HERE/'audit.json'),'verdict':report['verdict']}),flush=True)


if __name__=='__main__':main()
