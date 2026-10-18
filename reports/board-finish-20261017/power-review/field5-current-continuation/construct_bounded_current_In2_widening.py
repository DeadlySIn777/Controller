"""Widen only the actual R543 regional FIELD5 branch; no new drilled items.

All discrete copper and all foreign non-FG copper/intents are hard. Only exact
same-domain FG/In2 negative intent edits may be nominated, with all gates open.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import hashlib,json,math,pickle,re,sys,time
import shapely
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
OUT=HERE/'bounded-current-In2-widening-construction-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
FG='/motherboard_motors/FIELD_GND';LY='In2.Cu';ZID='5655cb90-5071-5499-8df8-2b73c23dc1fa'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def summary(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def outlines(z):return unary_union(K.L.poly([[r[0],r[1:]]for r in z['outline']]))
def covercircle(v,r):return Point(v['x'],v['y']).buffer((r+1e-8)/math.cos(math.pi/512),quad_segs=128)

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    drufile=CONT/'combined-R753-one-full-native-fill-cached-DRC-r299/copy/board.kicad_dru'
    files=[ACTUAL/'actual-combined-full-after-model.pkl',HERE/'actual-source-paths-r1/actual-native-source-contained-physical-sheet.wkb',HERE/'actual-source-paths-r1/actual-In2-gain-vs-full-R157.wkb',HERE/'actual-native-sheet-two-level-r1/actual-full-source-rooted-In2-sheet.wkb',drufile,Path(__file__),Path(K.__file__),Path(RF.__file__)]
    inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());regional,gain,source=[shapely.from_wkb(p.read_bytes())for p in files[1:4]];branch=gain.intersection(regional);assert branch.area>40;scope=branch.buffer(.151);domain=g['domains_normalized'][T.NET];fieldzone=next(z for z in g['zones']if z['uuid']==ZID);oldintent=outlines(fieldzone);oldCu=unary_union(K.L.poly(fieldzone['fills'][LY]));rec,trees=K.F.build(g,layers={LY});hard=[];constraints=[];vias={v['uuid']:v for v in g['vias']}
    for j in trees[LY].query(scope.buffer(2)):
        q=rec[LY][int(j)];net=K.L.norm(q['net'])
        if net==T.NET or(q['kind']=='fill'and net==FG):continue
        shape=q['shape'];gap=.15 if q['domain']==domain else.6
        if q['kind']=='via':shape=covercircle(vias[q['uuid']],vias[q['uuid']]['d']/2)
        if q['kind']=='fill':gap=max(gap,float(next(z for z in g['zones']if z['uuid']==q['uuid'])['clearance_mm']))
        hard.append(shape.buffer(gap+.0251,quad_segs=128));constraints.append(T.describe(q)|{'net':net,'required_Cu_guard_mm':gap+.0251})
    # Preserve original non-FG power/ground intent as well as actual Cu; this
    # intentionally makes the first nominee conservative about future repours.
    for z in g['zones']:
        net=K.L.norm(z['net'])
        if LY not in z['layers']or net in(T.NET,FG):continue
        shape=outlines(z)
        if shape.distance(scope)>2:continue
        gap=max(float(z['clearance_mm']),.15 if z['domain']==domain else.6)+.0251;hard.append(shape.buffer(gap,quad_segs=128));constraints.append({'kind':'foreign_native_literal_intent','uuid':z['uuid'],'net':net,'required_Cu_guard_mm':gap})
    for v in g['vias']:
        if Point(v['x'],v['y']).distance(scope)>2 or(K.L.norm(v['net'])==T.NET and LY in v['flashed']):continue
        gap=max(.275,.6 if v['net']and g['domains_normalized'].get(K.L.norm(v['net']))!=domain else.205)+.0251;hard.append(covercircle(v,v['drill']/2).buffer(gap,quad_segs=128));constraints.append({'kind':'drill','uuid':v['uuid'],'required_Cu_guard_mm':gap})
    for p in g['pads']:
        if K.L.norm(p['net'])==T.NET:continue
        for hole in K.L.poly(p.get('hole')or[]):
            if hole.distance(scope)>2:continue
            gap=max(.275,.6 if p['net']and g['domains_normalized'].get(K.L.norm(p['net']))!=domain else.205)+.0251;hard.append(hole.buffer(.005+gap,quad_segs=128));constraints.append({'kind':'pad_hole','uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'native_hole_approximation_reservation_mm':.005,'required_Cu_guard_mm':gap})
    forbidden=[r for r in g['rule_areas']if r['no_zones']];raw=fieldzone['net']
    for name,condition,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)',drufile.read_text()):
        if'zone'not in what.split()or raw in re.findall(r"A.NetName != '([^']+)'",condition):continue
        names=re.findall(r"A.intersectsArea\('([^']+)'\)",condition);assert len(names)==1;forbidden.append(next(r for r in g['rule_areas']if r['name']==names[0]))
    for r in forbidden:
        if LY not in r['layers']:continue
        for area in K.L.poly(r['outline']):
            if area.distance(scope)>2:continue
            hard.append(area.buffer(.0251,quad_segs=128));constraints.append({'kind':'no_zone_rule_or_custom_disallow','uuid':r['uuid'],'name':r['name']})
    blocked=unary_union(hard);allowed=unary_union(K.L.poly(g['outline'])).buffer(-.525).difference(blocked);put('exact-hard-geometry-constraints.json',constraints);rows=[];proposals=[]
    for amount in(.05,.10,.15):
        extension=branch.buffer(amount,quad_segs=128).intersection(allowed).difference(oldintent);extension=extension.buffer(-.000002,quad_segs=128);addition=set_precision(extension,1e-6,mode='valid_output');assert addition.difference(allowed).is_empty;assert addition.difference(branch.buffer(amount,quad_segs=128)).is_empty
        # Only pieces making positive finite contact with the current source Cu
        # boundary may be attached to the merged role; isolated slivers are held.
        pieces=RF.parts(addition);attached=[p for p in pieces if p.distance(source)<.00001 and p.length>.001];positive=unary_union(attached);newintent=oldintent.union(positive)
        # Union gains against an existing boundary should be checked literally;
        # if numerical erosion separates a piece, retain it as a held nominee.
        cuts=[]
        for z in g['zones']:
            if LY not in z['fills']or K.L.norm(z['net'])!=FG:continue
            gap=max(float(fieldzone['clearance_mm']),float(z['clearance_mm']),.15)+.0251;mask=positive.buffer(gap,quad_segs=128);nativeCu=unary_union(K.L.poly(z['fills'][LY]));cut=nativeCu.intersection(mask)
            if cut.is_empty:continue
            cuts.append({'uuid':z['uuid'],'native_Cu_removed':summary(cut),'literal_intent_removed':summary(outlines(z).intersection(mask)),'guarded_gap_mm':gap})
        name=str(round(amount*1000))+'um';(OUT/(name+'-new-only-In2-positive.wkb')).write_bytes(positive.wkb);(OUT/(name+'-full-In2-proposed-intent.wkb')).write_bytes(newintent.wkb);proposals.append((amount,positive,newintent))
        row={'maximum_lateral_growth_mm':amount,'new_positive':summary(positive),'all_unattached_raw_pieces_count':len(pieces)-len(attached),'proposed_full_field_intent':summary(newintent),'only_eligible_FG_In2_negative_cuts':cuts,'all_hard_geometry_preserved':True,'source_old_contacts_full_graph_reference_current_native':'OPEN'};rows.append(row);put('checkpoint.json',rows);print(json.dumps({'growth':amount,'positive_mm2':positive.area,'FG_Cu_cut_mm2':sum(r['native_Cu_removed']['area_mm2']for r in cuts),'parts':len(attached)}),flush=True)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'BOUNDED_ACTUAL_CURRENT_In2_BRANCH_WIDENING_CONSTRUCTOR_ONLY_NO_ADOPTION','input_sha256':inputs,'original_merged_FIELD5_zone_UUID':ZID,'exact_actual_R543_regional_new_branch':summary(branch),'rows':rows,'non_FG_foreign_native_Cu_and_literal_intents_hard':True,'new_drills':0,'ordinary_VIPPO_locations_added':0,'native_jobs':0,'board_written':False,'sparse_packet_frozen':False,'all_simultaneous_loads_and_limits_preserved':True,'FG_current_capacity_source_contacts_reference_and_new_native_fill':'OPEN','adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result)

if __name__=='__main__':main()
