"""Bounded new-capacitor placement refinement; no routing or source mutation."""
from collections import Counter
import copy
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_populate_motherboard_pcb as t

REPORT=Path(__file__).resolve().parent
PRIOR=REPORT/'populated-r02'
OUT=REPORT/'populated-r03'
SOURCE=REPORT/'frozen-source-r02/motherboard'
BASE=PRIOR/'source-inputs/local-signal-routing-v1-local-signal-routes-candidate.kicad_pcb'

def supply_ground(fp,target,functions):
    cap_nets={p.GetNetname() for p in fp.Pads() if t.copper_pad(p)}
    supply=[p for p in target.Pads() if t.copper_pad(p) and p.GetNetname() in cap_nets
            and functions.get(p.GetNumber(),{}).get('type')=='power_in'
            and re.search(r'^(?:VCC|VDD|VS$|VIN|V\+)',functions.get(p.GetNumber(),{}).get('name',''))]
    ground=[p for p in target.Pads() if t.copper_pad(p) and p.GetNetname() in cap_nets
            and re.search('GND',functions.get(p.GetNumber(),{}).get('name',''))]
    if not supply or not ground:raise ValueError('Missing real supply/ground target '+fp.GetReference())
    return supply,ground

def distances(fp,supply,ground):
    pairs=[(math.dist(t.mm(a.GetPosition()),t.mm(b.GetPosition())),a,b)
           for a in fp.Pads() for b in supply if t.copper_pad(a) and a.GetNetname()==b.GetNetname()]
    sd,cp,tp=min(pairs,key=lambda v:v[0])
    gd=min(math.dist(t.mm(a.GetPosition()),t.mm(b.GetPosition()))
           for a in fp.Pads() for b in ground if t.copper_pad(a) and a.GetNetname()==b.GetNetname())
    return sd,gd,tp

if OUT.exists():raise ValueError('r03 must be a new immutable candidate')
board=pcbnew.LoadBoard(str(PRIOR/'motherboard-populated-candidate.kicad_pcb'))
model=t.load(SOURCE/'design.json');mapping=t.load(SOURCE/'assembly-map.json')
_,nodes=t.native_parts_and_nets(SOURCE/'netlist.xml',model['components'])
functions=t.native_pin_functions(SOURCE/'netlist.xml')
placements=t.load(PRIOR/'placement-ledger.json');byref={r['reference']:r for r in placements}
fps={f.GetReference():f for f in board.GetFootprints()}
far={r['reference']for r in t.load(PRIOR/'report.json')['bypass_review']['targets_over_3mm']}
iso={r['reference']for r in placements if r.get('bypass_target') and
     model['components'][r['bypass_target']]['mpn']=='ISO1212DBQR'}
allowed=far|iso
assert not allowed&{f.GetReference()for f in pcbnew.LoadBoard(str(BASE)).GetFootprints()}
retained={f.GetReference()for f in pcbnew.LoadBoard(str(BASE)).GetFootprints()}
bypass_caps={r['reference']for r in placements if 'supply_pad_distance_mm'in r}
approved_neighbor_moves=set()
approved_receiver_moves=set()
bounds={r:t.courtyard_relative(f)for r,f in fps.items()}
changes=[]
for ref in sorted(allowed):
    fp=fps[ref];item=byref[ref];target=fps[item['bypass_target']]
    supply,ground=supply_ground(fp,target,functions[item['bypass_target']])
    before=t.mm(fp.GetPosition());angle=fp.GetOrientationDegrees()
    old_sd,old_gd,_=distances(fp,supply,ground)
    # The ISO1212 drawing gives 2 mm; other families say close/low-inductance,
    # not a universal 3 mm acceptance limit. Optimize both real local-loop ends.
    limit=2. if ref in iso else 3.
    tx,ty=t.mm(target.GetPosition())
    neighborhood=[v for r,v in bounds.items()if r!=ref and
                  v[2]>tx-10 and v[0]<tx+10 and v[3]>ty-10 and v[1]<ty+10]
    candidates=[]
    for rotation in (0,90,180,270):
        fp.SetOrientationDegrees(rotation);fp.SetPosition(t.xy((0,0)))
        relative=t.courtyard_relative(fp)
        cps=[(t.mm(p.GetPosition()),p.GetNetname())for p in fp.Pads()if t.copper_pad(p)]
        for sx in range(round((tx-8)*10),round((tx+8)*10)+1):
            px=sx/10.
            for sy in range(round((ty-8)*10),round((ty+8)*10)+1):
                py=sy/10.
                sd=min(math.dist((p[0]+px,p[1]+py),t.mm(q.GetPosition()))
                       for p,n in cps for q in supply if n==q.GetNetname())
                if sd>limit:continue
                gd=min(math.dist((p[0]+px,p[1]+py),t.mm(q.GetPosition()))
                       for p,n in cps for q in ground if n==q.GetNetname())
                rect=tuple(relative[i]+(px if i%2==0 else py)for i in range(4))
                if not (0<rect[0]<rect[2]<t.WIDTH and 0<rect[1]<rect[3]<t.HEIGHT):continue
                score=2*sd*sd+.3*gd*gd+.0001*math.dist(before,(px,py))**2
                candidates.append((score,sd,gd,rotation,px,py,rect))
    candidates.sort();chosen=next((c for c in candidates if not any(t.intersects(c[-1],q,.1)for q in neighborhood)),None)
    if chosen is None:
        # Permit only explicitly recorded neighboring new passives to move.
        # Never move an IC, a retained item, or somebody else's bypass.
        options=[]
        for c in candidates:
            blockers=[r for r,v in bounds.items()if r!=ref and t.intersects(c[-1],v,.1)]
            if blockers and all(r[0]in 'RCD'and r not in retained|bypass_caps for r in blockers):
                options.append((len(blockers),c,blockers))
        options.sort(key=lambda q:(q[0],q[1][0]))
        for _,c,blockers in options:
            trial=[];local_bounds=copy.deepcopy(bounds)
            for r in blockers:
                rf=fps[r];origin=t.mm(rf.GetPosition());ab=local_bounds[r]
                rel=tuple(ab[i]-origin[i%2]for i in range(4));candidate_spots=[]
                for gx in range(round((origin[0]-8)*2),round((origin[0]+8)*2)+1):
                    for gy in range(round((origin[1]-8)*2),round((origin[1]+8)*2)+1):
                        p=(gx/2.,gy/2.);rb=tuple(rel[i]+p[i%2]for i in range(4))
                        if t.intersects(rb,c[-1],.1):continue
                        if any(t.intersects(rb,v,.1)for q,v in local_bounds.items()if q not in (r,ref)):continue
                        candidate_spots.append((math.dist(origin,p),p,rb))
                if not candidate_spots:break
                _,p,rb=min(candidate_spots);trial.append((r,origin,p,rb));local_bounds[r]=rb
            if len(trial)!=len(blockers):continue
            for r,origin,p,rb in trial:
                rf=fps[r];rf.SetPosition(t.xy(p));bounds[r]=rb;approved_neighbor_moves.add(r)
                changes.append(dict(reference=r,before_position_mm=list(origin),before_rotation_degrees=rf.GetOrientationDegrees(),
                                    after_position_mm=list(p),after_rotation_degrees=rf.GetOrientationDegrees(),
                                    exact_source_nets_pads_and_footprint_unchanged=True,
                                    reason='Neighboring new passive displaced to reserve the authentic bypass local loop'))
            chosen=c;break
        if chosen is None and item['bypass_target']not in retained:
            # Two motor-alarm receivers were boxed in by adjacent motor ICs.
            # Move only the new receiver and its cap as a bounded local pair.
            tr=item['bypass_target'];origin=t.mm(target.GetPosition());old_box=bounds[tr]
            target_relative=tuple(old_box[i]-origin[i%2]for i in range(4));pair_options=[]
            sign=1 if t.mm(supply[0].GetPosition())[0]>=origin[0]else-1
            cap_angle=0 if sign>0 else 180
            fp.SetOrientationDegrees(cap_angle);fp.SetPosition(t.xy((0,0)))
            cap_relative=t.courtyard_relative(fp)
            cp=next(p for p in fp.Pads()if p.GetNetname()==supply[0].GetNetname());cap_pad=t.mm(cp.GetPosition())
            supply_relative=tuple(t.mm(supply[0].GetPosition())[i]-origin[i]for i in range(2))
            rx,ry,rw,rh=t.region_boxes({ref:item['region']})[item['region']]
            nearby_bounds={r:v for r,v in bounds.items()if v[2]>rx and v[0]<rx+rw and v[3]>ry and v[1]<ry+rh}
            for gx in range(round((rx+4)*2),round((rx+rw-4)*2)+1):
                for gy in range(round((ry+4)*2),round((ry+rh-4)*2)+1):
                    tp=(gx/2.,gy/2.);tb=tuple(target_relative[i]+tp[i%2]for i in range(4))
                    sp=tuple(supply_relative[i]+tp[i]for i in range(2))
                    p=(sp[0]+sign*1.99-cap_pad[0],sp[1]-cap_pad[1]);cb=tuple(cap_relative[i]+p[i%2]for i in range(4))
                    if t.intersects(tb,cb,.1):continue
                    if any(t.intersects(tb,v,.1)or t.intersects(cb,v,.1)for r,v in nearby_bounds.items()if r not in (ref,tr)):continue
                    if not all(rx<b[0]<b[2]<rx+rw and ry<b[1]<b[3]<ry+rh for b in (tb,cb)):continue
                    if not all(0<b[0]<b[2]<t.WIDTH and 0<b[1]<b[3]<t.HEIGHT for b in (tb,cb)):continue
                    pair_options.append((math.dist(origin,tp),tp,tb,p,cb))
            if pair_options:
                _,tp,tb,p,cb=min(pair_options);target.SetPosition(t.xy(tp));bounds[tr]=tb;approved_receiver_moves.add(tr)
                changes.append(dict(reference=tr,before_position_mm=list(origin),before_rotation_degrees=target.GetOrientationDegrees(),
                                    after_position_mm=list(tp),after_rotation_degrees=target.GetOrientationDegrees(),
                                    exact_source_nets_pads_and_footprint_unchanged=True,
                                    reason='Bounded new IC relocation to permit its local supply bypass'))
                fp.SetPosition(t.xy(p));sd,gd,_=distances(fp,supply,ground)
                chosen=(0,sd,gd,cap_angle,p[0],p[1],cb)
        if chosen is None:raise ValueError('No source-preserving close bypass placement '+ref)
    _,sd,gd,rotation,px,py,rect=chosen
    fp.SetOrientationDegrees(rotation);fp.SetPosition(t.xy((px,py)));bounds[ref]=rect
    changes.append(dict(reference=ref,before_position_mm=list(before),before_rotation_degrees=angle,
                        after_position_mm=[px,py],after_rotation_degrees=rotation,
                        before_nearest_supply_pad_mm=old_sd,after_nearest_supply_pad_mm=sd,
                        before_nearest_ground_pad_mm=old_gd,after_nearest_ground_pad_mm=gd,
                        exact_source_nets_pads_and_footprint_unchanged=True))

# Re-measure every target against authentic same-net supply and ground pads.
for item in placements:
    fp=fps[item['reference']]
    item.update(position_mm=list(t.mm(fp.GetPosition())),rotation_degrees=fp.GetOrientationDegrees(),
                courtyard_mm=list(t.courtyard_relative(fp)))
    if 'supply_pad_distance_mm'not in item:continue
    target=fps[item['bypass_target']]
    try:
        supply,ground=supply_ground(fp,target,functions[item['bypass_target']])
    except ValueError:
        # Existing gated-enable output bulk is VOUT, rather than power_in.
        supply=[p for p in target.Pads()if p.GetNumber()==item['supply_pin'].split('.')[-1]]
        ground=[p for p in target.Pads()if t.copper_pad(p)and re.search('GND',functions[item['bypass_target']].get(p.GetNumber(),{}).get('name',''))]
    sd,gd,tp=distances(fp,supply,ground)
    item.update(supply_pin=target.GetReference()+'.'+tp.GetNumber(),
                supply_pin_function=functions[item['bypass_target']][tp.GetNumber()]['name'],
                supply_pad_distance_mm=sd,closest_same_net_ground_pad_distance_mm=gd,
                target_distance_mm=math.dist(t.mm(fp.GetPosition()),t.mm(target.GetPosition())),
                bypass_copper_routed=False)

shutil.copytree(PRIOR,OUT)
for name in ('report.json','board-review.pdf','board-review.png','drc.json','drc-command.txt'):
    if (OUT/name).exists():(OUT/name).unlink()
dest=OUT/'motherboard-populated-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),board)
t.write(OUT/'placement-ledger.json',placements);t.write(OUT/'bounded-placement-changes.json',changes)
cmd=[str(t.CLI),'pcb','drc','--format','json','--output',str(OUT/'drc.json'),str(dest)]
result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace')
(OUT/'drc-command.txt').write_text(result.stdout+result.stderr,encoding='utf8')

before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity()
old_tracks={v.m_Uuid.AsString():t.identity(v)for v in before.GetTracks()}
old_pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):t.pad_identity(p)for p in before.GetPads()if t.copper_pad(p)}
old_fps={f.GetReference():(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),t.footprint_name(f))for f in before.GetFootprints()}
def tuples(v):return tuple(tuples(x)for x in v)if isinstance(v,list)else v
templates={r:[tuples(v)for v in rows]for r,rows in t.load(OUT/'exact-source-pad-templates.json').items()}
verification=t.verify_population(after,model,nodes,old_tracks,old_pads,old_fps,mapping['native_net_renames_allowed'],templates)
verification['native_object_retention']=t.native_retained_objects(BASE,dest,mapping['native_net_renames_allowed'])
assert verification['ok']and verification['native_object_retention']['ok'],verification
# A full r02->r03 object comparison bounds the placement changes to these caps.
prior_raw=t.raw_items(PRIOR/'motherboard-populated-candidate.kicad_pcb','footprint')
new_raw=t.raw_items(dest,'footprint');changed=[]
for f in after.GetFootprints():
    if prior_raw[f.m_Uuid.AsString()]!=new_raw[f.m_Uuid.AsString()]:changed.append(f.GetReference())
assert set(changed)<=allowed|approved_neighbor_moves|approved_receiver_moves,(changed,allowed|approved_neighbor_moves|approved_receiver_moves)
for key in ('zone','segment','via','gr_text','gr_line'):
    assert t.raw_items(PRIOR/'motherboard-populated-candidate.kicad_pcb',key)==t.raw_items(dest,key),key
drc=t.load(OUT/'drc.json');assert not drc['violations']and not drc.get('ignored_checks'),drc['violations']
report=copy.deepcopy(t.load(PRIOR/'report.json'))
bypass=[r for r in placements if 'supply_pad_distance_mm'in r]
report.update(revision='populated-r03',candidate_board_sha256=t.sha(dest),population=verification,
              uncapped_native_missing_joins=after.GetConnectivity().GetUnconnectedCount(False),
              native_drc=dict(regular_violations=0,ignored_checks=[],capped_unconnected_items=len(drc['unconnected_items']),report='drc.json'),
              bounded_new_capacitor_references=sorted(allowed),bounded_neighbor_passive_references=sorted(approved_neighbor_moves),
              bounded_receiver_references=sorted(approved_receiver_moves),actual_native_changed_footprints=sorted(changed),
              retained_r02_remaining_footprints_unchanged=True,
              bypass_review=dict(actual_named_supply_pad_targets=len(bypass),
                                 supply_pad_distance_max_mm=max(r['supply_pad_distance_mm']for r in bypass),
                                 targets_over_3mm=[r for r in bypass if r['supply_pad_distance_mm']>3],
                                 iso1212_targets=18,iso1212_center_to_VCC_pad_limit_mm=2,
                                 iso1212_targets_within_2mm=all(r['supply_pad_distance_mm']<=2 for r in bypass if r['reference']in iso),
                                 copper_routed=False,return_path_and_full_domain_decoupling_qualified=False),
              report_repair=None,tests=dict(native_mutation_tests='pending r03 run'),
              placement_refinement='Exact capacitor-only revision. Uses nearest authentic supply pads, and local ground-pad proximity. Numeric center distances are placement checks, not routed-loop qualification.')
t.write(OUT/'report.json',report)
print(report['bypass_review']);print('Changed new capacitors:',changed)
