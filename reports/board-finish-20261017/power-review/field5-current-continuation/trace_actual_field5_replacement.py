"""Trace genuine full-native FIELD5 source/load topology and its In2 replacement.

Only evidence is written. The cut is a host diagnostic that removes newly gained
FIELD5 In2 copper; it is never exported as a board or proposed manufacturing edit.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from collections import Counter,defaultdict,deque
import hashlib,importlib.util,json,pickle,sys
from datetime import datetime,timezone
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in (CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=HERE/'actual-source-paths-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
OLD=CONT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
R551=CONT/'field-power/FIELD5-R543-actual-source-Cu-finite-target-annulus-contained-sheet-r551'
NET='/motherboard_power_entry/FIELD_5V'
T1='0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'
T2='e19f5a4a-8797-4ce8-a00d-4c884cc46739'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda n:n.replace('{slash}','/')

def summary(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else [],'wkb_sha256':hashlib.sha256(s.wkb).hexdigest()}
def records(s):
    if s.is_empty:return[]
    if s.geom_type=='Polygon':return[[list(s.exterior.coords),[list(r.coords)for r in s.interiors]]]
    return[r for g in s.geoms for r in records(g)]
def pads(group):return sorted({f"{q['ref']}.{q['pin']}"for q in group if q['kind']=='pad'})
def describe(q):return{k:q[k]for k in ('kind','uuid','layer','ref','pin','contour')if k in q}

def finite_path(group,source,target):
    """Finite same-layer overlap plus actual same-pad/barrel cross-layer links."""
    graph=defaultdict(list);keys=defaultdict(list)
    for i,q in enumerate(group):keys[q['key']].append(i)
    for indices in keys.values():
        for i in indices:
            for j in indices:
                if i<j:graph[i].append((j,{'kind':'same_actual_physical_pad_or_barrel'}));graph[j].append((i,{'kind':'same_actual_physical_pad_or_barrel'}))
    for ly in K.LAYERS:
        ids=[i for i,q in enumerate(group)if q['layer']==ly];shapes=[group[i]['shape']for i in ids];tree=STRtree(shapes)
        for k,i in enumerate(ids):
            for z in tree.query(shapes[k],predicate='intersects'):
                j=ids[int(z)]
                if i>=j:continue
                area=shapes[k].intersection(group[j]['shape']).area
                if area>1e-10:
                    edge={'kind':'finite_actual_same_layer_Cu_overlap','layer':ly,'area_mm2':area}
                    graph[i].append((j,edge));graph[j].append((i,edge))
    starts=[i for i,q in enumerate(group)if source(q)];goals={i for i,q in enumerate(group)if target(q)}
    queue=deque(starts);seen={i:(None,None)for i in starts};goal=None
    while queue:
        i=queue.popleft()
        if i in goals:goal=i;break
        for j,edge in graph[i]:
            if j not in seen:seen[j]=(i,edge);queue.append(j)
    assert goal is not None,'No finite-overlap physical source path found'
    path=[]
    while goal is not None:
        previous,edge=seen[goal];path.append({'entity':describe(group[goal]),'incoming':edge});goal=previous
    return list(reversed(path))

def main():
    assert not OUT.exists();OUT.mkdir()
    files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',ACTUAL/'actual-graph-cache-receipt.json',OLD/'actual-full-R157-before-model.pkl',CONT/'field-power/normal-model-r3.json',CONT/'field-power/FIELD5-R543-same-real-annuli-contained-mesh-refinement-r579/receipt.json',R551/'receipt.json',R551/'exact-physical-sheet.wkb',R551/'actual-parent-source-all-contacts.wkb',R551/'actual-parent-source-goal-contact.wkb',Path(__file__)]
    inputs={str(p):sha(p)for p in files};after=pickle.loads(files[0].read_bytes());groups=pickle.loads(files[1].read_bytes());before=pickle.loads(files[3].read_bytes());planning=json.loads(files[4].read_text())
    assert inputs[str(files[0])]=='c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806'
    root=K.root(groups[NET],'L11003','2');paths={}
    for uid in (T1,T2):paths[uid]=finite_path(root,lambda q:q['kind']=='pad'and(q['ref'],q['pin'])==('L11003','2'),lambda q:q['kind']=='via'and q['uuid']==uid and q['layer']=='In2.Cu')
    after_in2=unary_union([s for z in after['zones']if norm(z['net'])==NET for s in K.L.poly(z['fills'].get('In2.Cu',[]))]);before_in2=unary_union([s for z in before['zones']if norm(z['net'])==NET for s in K.L.poly(z['fills'].get('In2.Cu',[]))]);gained=after_in2.difference(before_in2);lost=before_in2.difference(after_in2)
    (OUT/'actual-In2-gain-vs-full-R157.wkb').write_bytes(gained.wkb)
    # Remove only newly gained In2 copper, preserving all current pre-existing
    # conductors/crops. This diagnoses which loads actually require the new branch.
    zones=[]
    for z in after['zones']:
        if norm(z['net'])!=NET or 'In2.Cu'not in z['fills']:zones.append(z);continue
        fills={**z['fills'],'In2.Cu':[r for s in K.L.poly(z['fills']['In2.Cu'])for r in records(s.difference(gained))]};zones.append({**z,'fills':fills})
    diagnostic={**after,'zones':zones};cutgroups=K.physical(diagnostic,NET,K.hole_context(diagnostic))[1];cutroot=K.root(cutgroups,'L11003','2');targetcut=next(xs for xs in cutgroups if any(q['kind']=='via'and q['uuid']==T1 for q in xs))
    source_group_In2=unary_union([q['shape']for q in root if q['kind']=='fill'and q['layer']=='In2.Cu']);old_sheet=shapely.from_wkb(files[7].read_bytes());physical_sheet=old_sheet.intersection(source_group_In2);source_all=shapely.from_wkb(files[8].read_bytes()).intersection(physical_sheet);source_goal=shapely.from_wkb(files[9].read_bytes()).intersection(physical_sheet)
    target=unary_union([q['shape']for q in root if q['kind']=='via'and q['uuid']==T1 and q['layer']=='In2.Cu']).intersection(physical_sheet)
    assert physical_sheet.area>60 and source_all.area>20 and source_goal.area>.09 and target.area>.06
    shapes={'actual-native-source-contained-physical-sheet':physical_sheet,'actual-native-upstream-source-all-contacts':source_all,'actual-native-upstream-source-goal-contact':source_goal,'actual-native-0901-finite-target-contact':target}
    for name,s in shapes.items():(OUT/(name+'.wkb')).write_bytes(s.wkb)
    contacts={}
    for uid in (T1,T2):
        contacts[uid]=[]
        for q in root:
            if q['kind']=='via'and q['uuid']==uid:
                touching=[{'zone_UUID':f['uuid'],'layer':q['layer'],'finite_overlap_mm2':q['shape'].intersection(f['shape']).area}for f in root if f['kind']=='fill'and f['layer']==q['layer']and q['shape'].intersection(f['shape']).area>1e-10]
                contacts[uid].extend(touching)
    assert not any(q['layer']=='In4.Cu'for a in contacts.values()for q in a)
    assert all(any(q['layer']=='In2.Cu'for q in a)for a in contacts.values())
    # Source export matches the current electrical hierarchy (the later grid move
    # has separately proven zero semantic delta).
    helper=HERE.parent/'audit_shutdown_header_correction.py';inputs[str(helper)]=sha(helper);spec=importlib.util.spec_from_file_location('netlist',helper);N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N);netfile=HERE.parent/'late-power-schematic-grid-r3/after.net';inputs[str(netfile)]=sha(netfile);tree=N.parse(netfile)
    pin_nets={}
    for net in N.children(N.child(tree,'nets'),'net'):
        for node in N.children(net,'node'):
            ref=N.atom(node,'ref')
            if ref in('U11009','L11003','U11013','U11014','U11017'):
                pin_nets[f"{ref}.{N.atom(node,'pin')}"]={'net':N.atom(net,'name'),'pinfunction':N.atom(node,'pinfunction')if N.children(node,'pinfunction')else ''}
    upstream={k:v for k,v in pin_nets.items()if k.startswith('U11009.')or k.startswith('L11003.')}
    result={'utc':datetime.now(timezone.utc).isoformat(),'verdict':'ACTUAL_NATIVE_IN2_REPLACEMENT_SOURCE_PATH_EXISTS_CURRENT_QUALIFICATION_OPEN','input_sha256':inputs,'actual_source':'L11003.2','converter_inductor_source_chain':upstream,'actual_source_rooted_named_pads':pads(root),'actual_FIELD5_unrooted_named_pad_groups':[pads(xs)for xs in groups[NET]if xs is not root and pads(xs)],'finite_physical_source_paths':paths,'two_old_vias_current_finite_fill_contacts':contacts,'all_original_actual_via_flashes':'Retained separately by genuine R299 native receipt; no forced layer flags or tiny zones added.','actual_In2_Cu_change':{'new_gain':summary(gained),'actual_loss':summary(lost)},'diagnostic_only_new_gain_removed':{'source_named_pads':pads(cutroot),'0901_target_named_pads':pads(targetcut),'0901_same_source_without_new_In2_gain':targetcut is cutroot,'e19f_remains_source_without_new_In2_gain':any(q['kind']=='via'and q['uuid']==T2 for q in cutroot)},'current_sheet_binding':{n:summary(s)for n,s in shapes.items()},'old_R579_sheet_not_wholly_current_native':summary(old_sheet.difference(physical_sheet)),'planning_current_a':planning['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'],'retained_routing_reservation_a':planning['routing_local_targets_a']['FIELD5V_after_A_prereg'],'all12_motor_aux5_loads_retained':True,'normal_planning_material_mixed_mode_inrush_return_thermal_and_voltage_budget':'OPEN; fresh actual regional mesh follows, not a guaranteed full-loop/current bound.','board_or_source_written':False,'new_geometry_or_annular_count_patch_proposed':False,'adopted':False,'manufacturing_ready':False}
    assert all(sha(Path(p))==h for p,h in inputs.items())
    (OUT/'source-path-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'verdict':result['verdict'],'source_pad_count':len(pads(root)),'cut_source_pad_count':len(pads(cutroot)),'cut_target_pads':pads(targetcut),'unrooted':result['actual_FIELD5_unrooted_named_pad_groups'],'actual_sheet_mm2':physical_sheet.area}))

if __name__=='__main__':main()
