"""One reviewed same-net AO1-outline retirement around the unchanged merger.

This report-local wrapper permits only the exact 14802936 outline already
physically unioned into ed959e66. The shared generic merger is not changed.
"""
from pathlib import Path
import sys,copy,json,hashlib,argparse
from decimal import Decimal
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_merge_bounded_pcb_delta as generic
import hardware_zone_motherboard_returns as z
E=generic
RETIRED='14802936-d0f8-465a-93cb-871f2ea664d9'
KEEPER='ed959e66-2592-4d75-8c2f-3bca0ccac426'
DOMAIN='/motherboard_analog_output/AO1_COM'
BEFORE=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
DONOR=Path('reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root74-corridor-r03/motherboard-AO1-SDO-corridor-candidate.kicad_pcb')
PROOF=DONOR.parent/'literal-zone-retirement-proof-r02.json'
LEDGER=[]
GLOBAL='8b732c21-51eb-4770-9ca0-6e82f46f9942'

def electrical_settings(node):
    return E.dump([q for q in node if not(isinstance(q,list)and q and q[0]in('uuid','name','polygon','filled_polygon'))])

def native_outline(node):
    """Native single-outline zone plus every serialized hole, no bbox proxy."""
    poly=pcbnew.SHAPE_POLY_SET();polygons=E.children(node,'polygon')
    if not polygons:raise ValueError('Actual native zone polygon absent')
    for index,p in enumerate(polygons):
        hole=poly.NewHole(0)if index else -1
        if not index:poly.NewOutline()
        for point in E.children(E.child(p,'pts'),'xy'):
            poly.Append(int(Decimal(point[1])*1000000),int(Decimal(point[2])*1000000),0,hole)
    return poly

def union_guard(retired,old_keeper,new_keeper):
    # Actual net/layer/priority/pour settings are checked before hashes, so a
    # valid-looking receipt cannot authorize deletion in another domain.
    for node in(retired,old_keeper,new_keeper):
        if E.value(E.child(node,'net')[1])!=DOMAIN or E.value(E.child(node,'layer')[1])!='In1.Cu' or E.child(node,'priority')[1]!='20':
            raise ValueError('Exact AO1/In1/priority20 identity is required')
    settings=electrical_settings(retired)
    if settings!=electrical_settings(old_keeper)or settings!=electrical_settings(new_keeper):
        raise ValueError('Same actual electrical pour settings are required')
    rp,old,new=map(native_outline,(retired,old_keeper,new_keeper))
    remaining=z.duplicate(rp);remaining.BooleanSubtract(new)
    lost=z.duplicate(old);lost.BooleanSubtract(new)
    if remaining.Area()!=0 or lost.Area()!=0:
        raise ValueError('Retired/previous keeper Source-own outline remains uncovered')
    union=z.duplicate(old);union.BooleanAdd(rp);union.Simplify()
    uncovered=z.duplicate(union);uncovered.BooleanSubtract(new)
    if uncovered.Area()!=0:raise ValueError('Actual old same-net union is not fully retained')
    return dict(passed=True,net=DOMAIN,layer='In1.Cu',priority=20,
                same_electrical_pour_settings_sha256=E.sha_text(settings),
                retired_outline_area_mm2=rp.Area()/1e12,
                previous_keeper_area_mm2=old.Area()/1e12,new_keeper_area_mm2=new.Area()/1e12,
                actual_native_retired_uncovered_mm2=remaining.Area()/1e12,
                actual_native_keeper_lost_mm2=lost.Area()/1e12,
                actual_native_union_uncovered_mm2=uncovered.Area()/1e12)

def polygon_nodes(poly):
    if poly.OutlineCount()!=1:raise ValueError('Exact composition must remain a single native outline with holes')
    def atom(v):
        whole=Decimal(v)/Decimal(1000000)
        return format(whole,'f')
    def chain_node(chain):
        return ['polygon',['pts']+[['xy',atom(chain.CPoint(i).x),atom(chain.CPoint(i).y)]for i in range(chain.PointCount())]]
    result=[chain_node(poly.COutline(0))]
    result.extend(chain_node(poly.CHole(0,i))for i in range(poly.HoleCount(0)))
    return result

def compose_disjoint_outline(old,new,current):
    if E.value(E.child(old,'uuid')[1])!=GLOBAL or any(electrical_settings(v)!=electrical_settings(old)for v in(new,current)):
        raise ValueError('Only same-settings literal global LOGIC outline can compose')
    if E.value(E.child(old,'net')[1])!='/LOGIC_GND'or E.value(E.child(old,'layer')[1])!='In1.Cu':raise ValueError('Exact LOGIC/In1 composition identity required')
    op,np,cp=map(native_outline,(old,new,current))
    removed=z.duplicate(op);removed.BooleanSubtract(np)
    added=z.duplicate(np);added.BooleanSubtract(op)
    concurrent_removed=z.duplicate(op);concurrent_removed.BooleanSubtract(cp)
    concurrent_added=z.duplicate(cp);concurrent_added.BooleanSubtract(op)
    donor_change=z.duplicate(removed);donor_change.BooleanAdd(added);donor_change.Simplify()
    target_change=z.duplicate(concurrent_removed);target_change.BooleanAdd(concurrent_added);target_change.Simplify()
    overlap=z.duplicate(donor_change);overlap.BooleanIntersection(target_change)
    if overlap.Area()!=0:raise ValueError('Concurrent LOGIC edit overlaps actual donor polygon delta')
    merged=z.duplicate(cp);merged.BooleanSubtract(removed);merged.BooleanAdd(added);merged.Simplify()
    # Every concurrent removal remains removed and every added target area
    # remains covered. Outside the literal donor delta the target is exact.
    lost=z.duplicate(cp);lost.BooleanSubtract(merged);lost.BooleanSubtract(removed)
    unexpected=z.duplicate(merged);unexpected.BooleanSubtract(cp);unexpected.BooleanSubtract(added)
    cut_lost=z.duplicate(concurrent_removed);cut_lost.BooleanIntersection(merged)
    added_lost=z.duplicate(concurrent_added);added_lost.BooleanSubtract(merged)
    if any(p.Area()!=0 for p in(lost,unexpected,cut_lost,added_lost)):raise ValueError('Concurrent native polygon edit was not retained exactly')
    out=copy.deepcopy(current)
    for node in list(E.children(out,'polygon')):out.remove(node)
    out.extend(polygon_nodes(merged))
    parsed=native_outline(out);a=z.duplicate(parsed);a.BooleanSubtract(merged);b=z.duplicate(merged);b.BooleanSubtract(parsed)
    if a.Area()!=0 or b.Area()!=0:raise ValueError('Exact composed polygon serialization differs')
    receipt=dict(passed=True,uuid=GLOBAL,before_definition_sha256=E.sha_text(E.zone_definition(old)),donor_definition_sha256=E.sha_text(E.zone_definition(new)),target_definition_sha256=E.sha_text(E.zone_definition(current)),composed_definition_sha256=E.sha_text(E.zone_definition(out)),donor_removed_area_mm2=removed.Area()/1e12,donor_added_area_mm2=added.Area()/1e12,concurrent_removed_area_mm2=concurrent_removed.Area()/1e12,concurrent_added_area_mm2=concurrent_added.Area()/1e12,actual_changed_area_intersection_mm2=overlap.Area()/1e12,all_concurrent_cuts_and_additions_retained=True,unrelated_target_polygon_area_changed_mm2=(lost.Area()+unexpected.Area())/1e12)
    return out,receipt

def validate_exact_retirement(before,donor,target,proof):
    old,new,current=[E.objects(t,'zone')for t in(before,donor,target)]
    missing=set(old)-set(new)
    if missing!={RETIRED}or RETIRED not in current or KEEPER not in old or KEEPER not in new or KEEPER not in current:
        raise ValueError('Only the exact present14802936 retirement into ed959e66 is accepted')
    physical=union_guard(old[RETIRED],old[KEEPER],new[KEEPER])
    for label,node in(('retired_before',old[RETIRED]),('keeper_before',old[KEEPER]),('keeper_after',new[KEEPER])):
        if E.sha_text(E.zone_definition(node))!=proof[label+'_definition_sha256']:
            raise ValueError('Exact reviewed native AO1 definition hash differs: '+label)
    if E.zone_definition(current[RETIRED])!=E.zone_definition(old[RETIRED])or E.zone_definition(current[KEEPER])!=E.zone_definition(old[KEEPER]):
        raise ValueError('Concurrent target AO1 outline/rules conflict')
    return physical

def build_proof():
    before=E.parse(E.without_generated_fills(BEFORE.read_text()));donor=E.parse(E.without_generated_fills(DONOR.read_text()))
    old,new=E.objects(before,'zone'),E.objects(donor,'zone')
    physical=union_guard(old[RETIRED],old[KEEPER],new[KEEPER])
    native_before=pcbnew.LoadBoard(str(BEFORE));native_after=pcbnew.LoadBoard(str(DONOR))
    actual_old={q.m_Uuid.AsString():q for q in native_before.Zones()};actual_new={q.m_Uuid.AsString():q for q in native_after.Zones()}
    # Independent native serialization interpretation check for outer/holes.
    for uid,node in((RETIRED,old[RETIRED]),(KEEPER,old[KEEPER]),(KEEPER,new[KEEPER])):
        actual=actual_new[uid]if node is new[KEEPER]else actual_old[uid]
        parsed=native_outline(node);a=z.duplicate(parsed);a.BooleanSubtract(actual.Outline());b=z.duplicate(actual.Outline());b.BooleanSubtract(parsed)
        if a.Area()!=0 or b.Area()!=0:raise ValueError('Parsed native outer/hole geometry differs from actual KiCad outline '+uid+' '+str((a.Area(),b.Area(),parsed.Area(),actual.Outline().Area())))
    proof=dict(passed=True,scope='Only literal14802936 retirement after exact same-domain union into ed959e66',before_board_sha256=E.sha(BEFORE),donor_board_sha256=E.sha(DONOR),generic_merger_sha256=E.sha(generic.__file__),retired_uuid=RETIRED,keeper_uuid=KEEPER,retired_before_definition_sha256=E.sha_text(E.zone_definition(old[RETIRED])),keeper_before_definition_sha256=E.sha_text(E.zone_definition(old[KEEPER])),keeper_after_definition_sha256=E.sha_text(E.zone_definition(new[KEEPER])),native_physical_union_inclusion=physical,actual_native_outline_and_hole_equality=True,manufacturing_ready=False)
    positive=validate_exact_retirement(before,donor,before,proof)
    negatives=[]
    wrong=copy.deepcopy(before);E.child(E.objects(wrong,'zone')[RETIRED],'net')[1]=E.value('"/LOGIC_GND"');E.child(E.objects(wrong,'zone')[RETIRED],'net')[1]='"/LOGIC_GND"'
    try:validate_exact_retirement(wrong,donor,wrong,proof)
    except ValueError as exc:negatives.append(dict(control='Actual retired Source zone changed to foreign LOGIC net',rejected=True,reason=str(exc)))
    else:raise ValueError('Actual wrong-domain zone deletion negative was accepted')
    uncovered=copy.deepcopy(donor);keeper=E.objects(uncovered,'zone')[KEEPER]
    # Replace the new keeper with its original pre-corridor polygon. The old
    # separately anchored retired region is then genuinely uncovered.
    for p in list(E.children(keeper,'polygon')):keeper.remove(p)
    keeper.extend(copy.deepcopy(E.children(old[KEEPER],'polygon')))
    try:validate_exact_retirement(before,uncovered,before,proof)
    except ValueError as exc:negatives.append(dict(control='Actual keeper lacks the retired physical polygon',rejected=True,reason=str(exc)))
    else:raise ValueError('Actual uncovered-area zone deletion negative was accepted')
    missing=copy.deepcopy(before);missing.remove(E.objects(missing,'zone')[RETIRED])
    try:validate_exact_retirement(before,donor,missing,proof)
    except ValueError as exc:negatives.append(dict(control='Exact retired Source zone missing in actual target',rejected=True,reason=str(exc)))
    else:raise ValueError('Actual absent-zone deletion negative was accepted')
    # A literal disjoint native cut retains its complete area when composed;
    # an overlapping actual donor removal is rejected before serialization.
    current=copy.deepcopy(old[GLOBAL]);cp=native_outline(current)
    cut=z.rectangle((125.0,172.0,125.2,172.2),0);cp.BooleanSubtract(cut);cp.Simplify()
    for node in list(E.children(current,'polygon')):current.remove(node)
    current.extend(polygon_nodes(cp))
    composed,composition=compose_disjoint_outline(old[GLOBAL],new[GLOBAL],current)
    attack=copy.deepcopy(old[GLOBAL]);removed=native_outline(old[GLOBAL]);removed.BooleanSubtract(native_outline(new[GLOBAL]))
    attacked=native_outline(old[GLOBAL]);attacked.BooleanSubtract(removed)
    for node in list(E.children(attack,'polygon')):attack.remove(node)
    attack.extend(polygon_nodes(attacked))
    try:compose_disjoint_outline(old[GLOBAL],new[GLOBAL],attack)
    except ValueError as exc:negatives.append(dict(control='Actual concurrent LOGIC cut overlaps literal donor removal',rejected=True,reason=str(exc)))
    else:raise ValueError('Actual overlapping composition negative accepted')
    proof.update(actual_native_positive=positive,actual_native_disjoint_composition=composition,actual_native_negatives=negatives,tool_sha256=E.sha(__file__))
    E.write(PROOF,proof);print(json.dumps(dict(passed=True,actual_negative_controls=len(negatives),literal_retired_zone=RETIRED)),flush=True)
    return proof

def main():
    if '--build-proof'in sys.argv:
        if PROOF.exists():raise ValueError('Existing immutable retirement proof cannot be overwritten')
        build_proof();return
    args=list(sys.argv);proof=json.loads(PROOF.read_text())
    for key,path in(('--before',BEFORE),('--donor',DONOR)):
        supplied=Path(args[args.index(key)+1])
        if supplied.resolve()!=path.resolve()or E.sha(supplied)!=proof[('before'if key=='--before'else'donor')+'_board_sha256']:
            raise ValueError('Only exact reviewed AO1 donor/before boards accepted')
    if E.sha(generic.__file__)!=proof['generic_merger_sha256']:raise ValueError('Frozen generic shared merger changed')
    original=generic.merge_reviewed_existing_zone_outlines
    def literal_wrapper(before,donor,target,reviews):
        physical=validate_exact_retirement(before,donor,target,proof)
        target.remove(E.objects(target,'zone')[RETIRED])
        narrowed=copy.deepcopy(before);narrowed.remove(E.objects(narrowed,'zone')[RETIRED])
        derived_donor=copy.deepcopy(donor);derived_reviews=copy.deepcopy(reviews)
        old,new,current=[E.objects(t,'zone')for t in(narrowed,derived_donor,target)]
        composition=None
        if E.zone_definition(current[GLOBAL])!=E.zone_definition(old[GLOBAL]):
            composed,composition=compose_disjoint_outline(old[GLOBAL],new[GLOBAL],current[GLOBAL])
            derived_donor[derived_donor.index(new[GLOBAL])]=composed
            narrowed[narrowed.index(old[GLOBAL])]=copy.deepcopy(current[GLOBAL])
            review=next(r for r in derived_reviews if r['uuid']==GLOBAL)
            if review['before_definition_sha256']!=E.sha_text(E.zone_definition(old[GLOBAL]))or review['after_definition_sha256']!=E.sha_text(E.zone_definition(new[GLOBAL])):
                raise ValueError('Original bounded LOGIC review hashes changed')
            review.update(before_definition_sha256=E.sha_text(E.zone_definition(current[GLOBAL])),after_definition_sha256=E.sha_text(E.zone_definition(composed)),electrical_outline_correction_reason=review['electrical_outline_correction_reason']+'; exact native disjoint composition retains concurrent Source return cut')
        result=original(narrowed,derived_donor,target,derived_reviews)
        LEDGER.append(dict(retired_uuid=RETIRED,keeper_uuid=KEEPER,proof_sha256=E.sha(PROOF),actual_native_union_proof=physical,exact_disjoint_LOGIC_composition=composition))
        return result
    generic.merge_reviewed_existing_zone_outlines=literal_wrapper
    generic.main()
    out=Path(args[args.index('--out')+1]);r=json.loads((out/'receipt.json').read_text())
    r.update(exact_literal_same_net_AO1_retirement=LEDGER,generic_shared_merger_unchanged=True,generic_shared_merger_sha256=E.sha(generic.__file__),retirement_wrapper_sha256=E.sha(__file__))
    E.write(out/'receipt.json',r)
if __name__=='__main__':main()
