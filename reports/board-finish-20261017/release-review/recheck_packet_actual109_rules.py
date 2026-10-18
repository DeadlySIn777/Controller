"""Replace cached seed rule/source outlines with the actual native export.

Recompute finite-source owned apertures, save exact geometries, and recheck
every candidate body against all109 native rule polygons/current DRU.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
import hashlib,json,math,pickle,re,sys
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import shapely
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
from shapely import STRtree,from_wkb
import find_paired_return_sites as F
H=Path(__file__).resolve().parent;RUN=H/sys.argv[1];OUT=RUN/'actual109-native-source-rule-recheck';OUT.mkdir()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def native_poly(rows):return [Polygon(r[0],r[1:]) for r in rows]
def save(name,s):
    f=OUT/(name+'.wkb');f.write_bytes(s.wkb)
    return {'file':str(f),'SHA256':sha(f),'area_mm2':s.area,'bounds':list(s.bounds) if not s.is_empty else None}
native=F.OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/actual-full-refill-geometry.json'
binding=F.ROOT/'reports/board-finish-20261017/routing/parent-audit-review/native-rule-actual-export-seed-binding-r1/receipt.json'
api=F.ROOT/'reports/board-finish-20261017/routing/parent-audit-review/read-only-native-R299-rule-areas-r2/exact-native-rule-areas.json'
model=F.CACHE/'actual-combined-full-after-model.pkl';graph=F.CACHE/'actual-combined-full-after-all-net-groups.pkl'
spatial=H/'owned-cap-body-bridges-r4/exact-host-spatial-records.pkl';cachebind=H/'owned-cap-body-bridges-r4/spatial-record-cache-binding.json'
reviewed=RUN/'independent-current-source-verification/exact-reviewed-additive-packet.json'
dru=F.CURRENT/'native/board.kicad_dru';board=F.CURRENT/'native/board.kicad_pcb'
paths=[native,binding,api,model,graph,spatial,cachebind,reviewed,dru,board,Path(__file__),Path(F.__file__)]
pins={str(f):sha(f) for f in paths}
assert pins[str(native)]=='9567a5c5a3c4e055a7ae989e0832a152fa21c09b8df6250fbb495b2c07c42b3f'
assert pins[str(api)]=='cb75ef228a2ae66b280de84fb469cc9dae32c26fbe46675de5dbb4ec93535806'
assert pins[str(board)]=='758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad'
assert json.loads(binding.read_text())['actual_rule_count']==109
cb=json.loads(cachebind.read_text());assert pins[str(spatial)]==cb['SHA256'] and pins[str(model)]==cb['actual_model_SHA256'] and pins[str(board)]==cb['current_peer_SHA256']
g=json.loads(native.read_text());h=pickle.loads(model.read_bytes());groups=pickle.loads(graph.read_bytes());records,holes=pickle.loads(spatial.read_bytes())
assert len(g['rule_areas'])==109
rules=[{**r,'shapes':native_poly(r['outline'])} for r in g['rule_areas']];zones={z['uuid']:z for z in g['zones']}
native_disallow=[]
for condition in re.findall(r'\(condition "([^"\n]*)"\)\s*\(constraint disallow track via zone\)',dru.read_text()):
    names=re.findall(r"A\.intersectsArea\('([^']+)'\)",condition);assert names
    ex={F.norm(n) for n in re.findall(r"A\.NetName != '([^']+)'",condition)}
    native_disallow.extend((r,ex) for r in rules if r['name'] in names)
trees={ly:STRtree([r['shape'] for r in rr]) for ly,rr in records.items()};ht=STRtree([r['shape'] for r in holes]);hv={v['uuid']:v for v in h['vias']}
roots={'DOM_LOGIC':('/LOGIC_GND','J11001','2'),'DOM_FIELD_A':('/motherboard_motors/FIELD_GND','J11003','2'),'DOM_FIELD_B':('/motherboard_do/FIELD_B_0V','J11005','2')}
root={d:next(q for q in groups[n] if any(r['kind']=='pad' and r['ref']==ref and str(r['pin'])==pin for r in q)) for d,(n,ref,pin) in roots.items()}
inner={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'}
packet=json.loads(reviewed.read_text());assert packet['inputs_unchanged'];results=[];eligible=[];ops=[]
for q in packet['eligible_new_nonredundant_packets']:
    net=q['net'];domain=h['domains_normalized'][net];ly=q['layer'];refly=inner[ly];gnd=roots[domain][0]
    wf=Path(q['body_WKB_file']);pins[str(wf)]=sha(wf);whole=from_wkb(wf.read_bytes());errors=[];tested=[]
    for r in rules:
        if ly in r['layers'] and r.get('no_tracks'):
            distance=min((whole.distance(s) for s in r['shapes']),default=math.inf);tested.append({'rule_UUID':r['uuid'],'name':r['name'],'kind':'actual109_no_tracks','gap_mm':distance})
            if distance<.025:errors.append({'kind':'actual109_no_tracks','rule_UUID':r['uuid'],'gap_mm':distance})
    for r,ex in native_disallow:
        if ly in r['layers'] and net not in ex:
            distance=min((whole.distance(s) for s in r['shapes']),default=math.inf);tested.append({'rule_UUID':r['uuid'],'name':r['name'],'kind':'current_DRU_track_disallow','gap_mm':distance})
            if distance<.025:errors.append({'kind':'current_DRU_track_disallow','rule_UUID':r['uuid'],'gap_mm':distance})
    roi=whole.buffer(1.7)
    literal=unary_union([r['shape'].intersection(roi) for r in root[domain] if r['kind']=='fill' and r['layer']==refly and r['shape'].intersects(roi)])
    caps=[];cap_rows=[]
    for j,c in enumerate(q.get('qualified_inherited_unchanged_owner_apertures',[])):
        uid=c['signal_UUID'];v=hv[uid];center=Point(v['x'],v['y']);radius=v['d']/2+.275
        assert radius==c['immutable_owned_radius_mm'] and c['radius_expansion_mm']==0
        disc=center.buffer(radius,quad_segs=256)
        owners={r['uuid'] for r in root[domain] if r['kind']=='fill' and r['layer']==refly and r['shape'].distance(disc)<.8}
        assert all(u in zones and F.norm(zones[u]['net'])==gnd for u in owners)
        design=unary_union([s for u in owners for s in native_poly(zones[u]['outline'])]);allowed=disc.intersection(design);cuts=[]
        for i in trees[refly].query(disc.buffer(1.0)):
            rr=records[refly][int(i)]
            if rr['uuid']==uid or rr['net']==gnd:continue
            gap=.15 if h['domains_normalized'].get(rr['net'])==domain else .6
            cuts.append(F.outer(rr['shape'].intersection(disc.buffer(1.0)),max(.25,gap,rr['local'])+.025+rr['error']))
        for i in ht.query(disc):
            hole=holes[int(i)]
            if hole['uuid']!=uid:cuts.append(F.outer(hole['shape'],.005+hole['error']))
        for rr in rules:
            if refly in rr['layers'] and rr.get('no_fill'):
                cuts.extend(F.outer(s,.025) for s in rr['shapes'] if s.distance(disc)<.025)
        for rr,ex in native_disallow:
            if refly in rr['layers'] and gnd not in ex:
                cuts.extend(F.outer(s,.025) for s in rr['shapes'] if s.distance(disc)<.025)
        allowed=allowed.difference(unary_union(cuts));parts=list(allowed.geoms) if hasattr(allowed,'geoms') else [allowed]
        allowed=unary_union([part for part in parts if part.intersection(literal).area>.000001])
        actual_contact=allowed.intersection(literal).area
        # Native export supplies source-zone outlines; cached seed outlines
        # are deliberately absent from this replacement source/reference gate.
        cap_rows.append({'signal_UUID':uid,'old_track_UUID':c['existing_track_UUID'],'unchanged_radius_mm':radius,'actual_native_source_zone_UUIDs':sorted(owners),
                         'actual_root_fill_contact_mm2':actual_contact,'actual109_native_source_clipped_aperture':save(str(q['candidate_index'])+'-cap'+str(j),allowed)})
        if not allowed.is_empty:caps.append(allowed)
    final=whole.difference(unary_union([literal,*caps]));gap=save(str(q['candidate_index'])+'-actual109-reference-gap',final)
    if not final.is_empty:errors.append({'kind':'actual109_actual_native_zone_source_reference_gap','gap':gap})
    result={'candidate_index':q['candidate_index'],'net':net,'layer':ly,'actual109_native_track_rule_checks':tested,'actual_native_source_caps':cap_rows,'reference_gap':gap,'errors':errors,'PASS':not errors}
    results.append(result)
    if not errors:eligible.append(q);ops.extend(q['operations'])
out={'status':'ACTUAL109_NATIVE_RULES_AND_ACTUAL_NATIVE_SOURCE_OUTLINES_REPLACE_SEED_RULE_GATE','actual_native_rules':109,'cached_seed_rule_gate_superseded':True,
     'eligible_packets_after_actual_rule_and_source_recheck':eligible,'exact_additive_operations':ops,'results':results,'new_bridges':len(eligible),'new_nets':len({q['net'] for q in eligible}),'new_tracks':len(ops),
     'all_input_SHA256':pins,'inputs_unchanged':all(sha(Path(f))==v for f,v in pins.items()),'native_fill_calls':0,'native_save_calls':0,'PCB_written':False,'adopted':False,
     'full_joint_native_source_parity_uncapped_old_relationship_reference_current_SI':'OPEN_REQUIRED','manufacturing_ready':False}
put('exact-reviewed-additive-packet.json',out)
print(json.dumps({k:out[k] for k in ('new_bridges','new_nets','new_tracks','inputs_unchanged')}))
