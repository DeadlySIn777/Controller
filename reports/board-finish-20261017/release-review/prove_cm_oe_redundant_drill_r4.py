"""Targeted cached-native deletion test for one unregistered in-pad drill.

This tests retirement, not an ordinary-via destination qualification. It
preserves all remaining source polygons/holes literally and relies on no fill
restoration for its alternative retained-contact connectivity witness.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
import collections,csv,hashlib,itertools,json,math,pickle,sys,xml.etree.ElementTree as ET
from decimal import Decimal
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from shapely.geometry import Point
from shapely import STRtree,from_wkb
import find_paired_return_sites as F
H=Path(__file__).resolve().parent;OUT=H/'cm-oe-redundant-drill-r4';OUT.mkdir()
NET='/motherboard_compute/CM_COMMS_OE_N';BAD='62d197e4-26de-4dff-8333-aa65243b2975';SURVIVE='10beb872-f88a-4534-b30a-f2ece1ffc801'
CANDIDATES=[BAD,'883fedb9-88f9-4d91-b8ff-5e28f273b0ac','78b7d1ca-c577-4c99-9da0-2cee2c6a4373']
graph=F.CACHE/'actual-combined-full-after-all-net-groups.pkl';model=F.CACHE/'actual-combined-full-after-model.pkl'
CURRENT2=F.ROOT/'reports/board-finish-20261017/combined-route-stage-r2'
board=CURRENT2/'native/board.kicad_pcb';ledger=CURRENT2/'all-copper-expected.json';xml=H/'R299-fresh-source.xml'
peer=H/'owned-cap-body-bridges-r5/actual109-native-source-rule-recheck/exact-reviewed-additive-packet.json'
rules=F.OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/actual-full-refill-geometry.json'
native_masks=rules.with_name('actual-full-refill-via-flashes.json')
assembly=F.ROOT/'reports/board-finish-20261017/power-review/native-warning-assembly-review-r2/actual-native-via-drill-SMD-Cu-intersections.csv'
assembly_receipt=assembly.with_name('review-receipt.json')
registry=Path('Z:/pcb-runs/fab-check/assembly/vippo.csv');registry106=Path('Z:/pcb-runs/claude-finish/relayout/checks/vippo-root106.json')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
files=[graph,model,board,ledger,xml,peer,rules,native_masks,assembly,assembly_receipt,registry,registry106,Path(__file__),CURRENT2/'construction-receipt.json',CURRENT2/'native/motherboard_compute.kicad_sch',F.BASE.with_name('motherboard_compute.kicad_sch')]
pins={str(f):sha(f) for f in files};assert pins[str(board)]=='9f075604a881b1e0d8cafe869e7389e246025ffbd37ec4dabb7cc5c1a7db225a'
assert pins[str(CURRENT2/'native/motherboard_compute.kicad_sch')]==pins[str(F.BASE.with_name('motherboard_compute.kicad_sch'))]
gg=pickle.loads(graph.read_bytes())[NET];h=pickle.loads(model.read_bytes());vv={v['uuid']:v for v in h['vias']};v=vv[BAD]
g=json.loads(rules.read_text());assert len(g['rule_areas'])==109
masks=json.loads(native_masks.read_text())['vias']
assembly_rows=list(csv.DictReader(assembly.open()))
candidate_assembly={u:[r for r in assembly_rows if r['via_uuid']==u] for u in CANDIDATES}
for uid in CANDIDATES:
    assert masks[uid]==vv[uid]['flashed']==list(F.K.LAYERS)
    assert candidate_assembly[uid]
    assert all(r['old_291_registry_uuid_hit']=='False' and r['ROOT106_present_uuid_hit']=='False' and r['native_filling']!='yes' and r['native_capping']!='yes' for r in candidate_assembly[uid])
ids=[i for i,q in enumerate(gg) if any(r['kind']=='via' and r['uuid']==BAD for r in q)];assert len(ids)==1
gi=ids[0];rows=gg[gi];keep={r['uuid'] for r in rows};assert SURVIVE in keep
def key(r):return tuple(r['key'])
class UF:
    def __init__(self):self.p={}
    def find(self,k):
        self.p.setdefault(k,k)
        while self.p[k]!=k:self.p[k]=self.p[self.p[k]];k=self.p[k]
        return k
    def join(self,a,b):self.p[self.find(a)]=self.find(b)
def contacts(retired=()):
    retired=set(retired); rr=[r for r in rows if r['uuid'] not in retired];uf=UF();adj=collections.defaultdict(set);finite=[];tolerance=[]
    for r in rr:uf.find(key(r))
    for ly in F.K.LAYERS:
        ll=[r for r in rr if r['layer']==ly];tree=STRtree([r['shape'] for r in ll])
        for i,a in enumerate(ll):
            for j in tree.query(a['shape'].buffer(.000002)):
                j=int(j)
                if i>=j:continue
                b=ll[j];distance=a['shape'].distance(b['shape'])
                if distance>.000002:continue
                area=a['shape'].intersection(b['shape']).area
                uf.join(key(a),key(b));adj[key(a)].add(key(b));adj[key(b)].add(key(a))
                row={'a':list(key(a)),'b':list(key(b)),'layer':ly,'finite_overlap_mm2':area,'gap_mm':distance}
                (finite if area>.00000001 else tolerance).append(row)
    groups=collections.defaultdict(set)
    for k in uf.p:groups[uf.find(k)].add(k)
    return uf,adj,list(groups.values()),finite,tolerance
before,oldadj,before_groups,oldfinite,oldtolerance=contacts();assert len(before_groups)==1
# Remove the in-pad barrel and peel only B-side track tails which end at the
# retired branch, stopping at pads/vias/zone anchors or connected junctions.
retired=set();steps=[];joint_trials=[];byuid=collections.defaultdict(list)
for r in rows:byuid[r['uuid']].append(r)
# Exhaust all seven nonempty barrel subsets jointly. Only conductor-only B
# tails may accompany a candidate; no required pad, retained via or fill is
# discarded to make a deletion pass.
possibilities=[]
for count in range(1,len(CANDIDATES)+1):
    for subset in itertools.combinations(CANDIDATES,count):
        trial=set(subset);uf,adj,components,finite,tolerance=contacts(trial);root_component=next(cc for cc in components if ('via',SURVIVE) in cc)
        extra=[];block=[]
        for cc in components:
            if cc is root_component:continue
            group_rows=[r for r in rows if key(r) in cc]
            if all(r['kind']=='track' and r['layer']=='B.Cu' for r in group_rows):extra.extend(r['uuid'] for r in group_rows)
            else:block.append({'required_named_pads':sorted({(r['ref'],str(r['pin'])) for r in group_rows if r['kind']=='pad'}),'remaining_barrels':sorted({r['uuid'] for r in group_rows if r['kind']=='via'}),'layers':sorted({r['layer'] for r in group_rows}),'retained_keys':len(cc)})
        trial.update(extra);uf2,adj2,cc2,finite2,tolerance2=contacts(trial)
        passed=not block and len(cc2)==1
        joint_trials.append({'proposed_retired_vias':list(subset),'proposed_orphan_B_tail_UUIDs':sorted(set(extra)),'remaining_native_key_components':len(cc2),'blocking_components':block,'accepted_as_joint_possibility':passed})
        if passed:possibilities.append((len(subset),-len(trial),sorted(trial)))
assert possibilities
retired=set(max(possibilities)[2])
queue=[]
for edge in oldfinite:
    a,b=tuple(edge['a']),tuple(edge['b'])
    if a[1] in retired and b[0]=='track' and b[2]=='B.Cu':queue.append(b[1])
    if b[1] in retired and a[0]=='track' and a[2]=='B.Cu':queue.append(a[1])
while queue:
    uid=queue.pop(0)
    if uid in retired:continue
    parts=byuid[uid]
    if not parts or any(r['kind']!='track' or r['layer']!='B.Cu' for r in parts):continue
    track=parts[0]['source'];endpoint_contacts=[]
    for at in (track['a'],track['b']):
        pt=Point(at);neighbors=[]
        for r in rows:
            if r['layer']!='B.Cu' or r['uuid'] in retired|{uid}:continue
            if r['shape'].distance(pt)<=track['w']/2+.000002:neighbors.append(r)
            elif r['kind']=='via' and pt.distance(Point(vv[r['uuid']]['x'],vv[r['uuid']]['y']))<=.000002 and any(part['shape'].intersection(r['shape']).area>.00000001 for part in parts):neighbors.append(r)
        endpoint_contacts.append(neighbors)
    if all(endpoint_contacts):continue
    trial=retired|{uid};uf,adj,components,finite,tolerance=contacts(trial)
    if len(components)!=1:continue
    retired.add(uid);steps.append({'retired_track_UUID':uid,'source':track,'retained_endpoint_neighbor_UUIDs':sorted({r['uuid'] for nn in endpoint_contacts for r in nn}),'cached_native_retained_key_components':1})
    for nn in endpoint_contacts:
        queue.extend(r['uuid'] for r in nn if r['kind']=='track')
after,adj,components,finite,tolerance=contacts(retired);assert len(components)==1
strict_adj=collections.defaultdict(set)
for edge in finite:
    a,b=tuple(edge['a']),tuple(edge['b']);strict_adj[a].add(b);strict_adj[b].add(a)
target=after.find(('via',SURVIVE))
# Preserve each old finite boundary contact through a path in actual retained
# copper pieces. No contact is inferred from a net-name or a future refill.
boundary=[];paths=[]
for edge in oldfinite:
    a,b=tuple(edge['a']),tuple(edge['b']);ar=a[1] in retired;br=b[1] in retired
    if ar==br:continue
    remaining=b if ar else a;gone=a if ar else b
    assert after.find(remaining)==target
    todo=[remaining];prev={remaining:None};goal=('via',SURVIVE)
    for node in todo:
        if node==goal:break
        for nxt in strict_adj[node]:
            if nxt not in prev:prev[nxt]=node;todo.append(nxt)
    assert goal in prev
    path=[];node=goal
    while node is not None:path.append(list(node));node=prev[node]
    path.reverse();paths.append({'retired_key':list(gone),'retained_boundary_key':list(remaining),'old_finite_overlap_mm2':edge['finite_overlap_mm2'],'layer':edge['layer'],'alternative_retained_actual_native_piece_path':path})
    boundary.append(edge)
# Stronger finite-area-only graph control, independent of the 2nm baseline
# contact tolerance used by the already-native-bound graph cache.
strict=UF()
for r in rows:
    if r['uuid'] not in retired:strict.find(key(r))
for e in finite:strict.join(tuple(e['a']),tuple(e['b']))
strict_components=len({strict.find(k) for k in strict.p});assert strict_components==1
current_ledger=json.loads(ledger.read_text())['copper']
def iu(v):
    d=Decimal(str(v))*1000000;assert d==d.to_integral_value();return int(d)
layer_proof=[];hp={r['uuid']:r for r in h['pads']};actual_pcb=F.BASE.read_bytes().decode();current_pcb=board.read_bytes().decode()
def native_fp(txt,uid):
    at=txt.index('"'+uid+'"');start=txt.rfind('\n\t(footprint ',0,at)+2;assert start>1;return F.chunk_at(txt,start)
for r in rows:
    if r['uuid'] in retired:continue
    uid=r['uuid']
    if r['kind']=='track':
        t=r['source'];cur=current_ledger[uid]
        assert cur['kind']=='segment' and cur['start_IU']==[iu(v) for v in t['a']] and cur['end_IU']==[iu(v) for v in t['b']] and cur['width_IU']==iu(t['w']) and cur['layer']==r['layer'] and F.norm(cur['raw_net'])==NET
    elif r['kind']=='via':
        v0=vv[uid];cur=current_ledger[uid]
        assert cur['at_IU']==[iu(v0['x']),iu(v0['y'])] and cur['drill_IU']==iu(v0['drill']) and set(cur['diameters_IU'].values())=={iu(v0['d'])} and masks[uid]==v0['flashed']
    elif r['kind']=='pad':assert native_fp(actual_pcb,uid)==native_fp(current_pcb,uid)
    else:raise AssertionError('Unexpected control-net conductor '+r['kind'])
    layer_proof.append({'kind':r['kind'],'UUID':uid,'layer':r['layer'],'native_piece_key':list(key(r)),'actual_native_piece_WKB_SHA256':hashlib.sha256(r['shape'].wkb).hexdigest(),'source_geometry_retained_exact':True})
put('all-retained-native-layer-piece-ledger.json',layer_proof)
rootxml=ET.parse(xml).getroot();components_xml={r.get('ref'):r for r in rootxml.find('components')}
netnode=next(n for n in rootxml.find('nets') if F.norm(n.get('name'))==NET)
nodes=[{**r.attrib,'component_value':components_xml[r.get('ref')].findtext('value'),'footprint':components_xml[r.get('ref')].findtext('footprint')} for r in netnode.findall('node')]
source={'nodes':nodes,'non_power_pin_types_only':all(not r.get('pintype','').startswith('power_') for r in nodes)};assert source['non_power_pin_types_only']
raw=board.read_bytes();iv=F.K.C.inventory(raw);e=json.loads(ledger.read_text())['copper'];operations=[]
for uid in sorted(retired):
    ch=iv[3][uid];assert hashlib.sha256(ch).hexdigest()==e[uid]['chunk_sha256'] and raw.count(ch)==1
    f=OUT/(uid+'.remove-exact-native-chunk');f.write_bytes(ch)
    operations.append({'action':'remove_exact_native_object','UUID':uid,'kind':e[uid]['kind'],'file':str(f),'SHA256':sha(f)})
    raw=raw.replace(ch,b'')
counter=F.K.C.inventory(raw)
assert set(counter[3])==set(iv[3])-retired and all(counter[3][u]==ch for u,ch in iv[3].items() if u not in retired)
peerchecks=[]
for q in json.loads(peer.read_text())['eligible_packets_after_actual_rule_and_source_recheck']:
    bf=Path(q['body_WKB_file']);pins[str(bf)]=sha(bf);s=from_wkb(bf.read_bytes())
    distances=[]
    for uid in retired:
        for r in byuid[uid]:distances.append(r['shape'].distance(s))
    peerchecks.append({'peer_net':q['net'],'distance_to_all_retired_native_pieces_mm':min(distances)})
assert all(c['distance_to_all_retired_native_pieces_mm']>3 for c in peerchecks)
put('finite-boundary-contact-substitution-paths.json',paths)
retired_vias=sorted(set(CANDIDATES)&retired)
used_barrels={k[1] for r in paths for k in r['alternative_retained_actual_native_piece_path'] if k[0]=='via'}
surviving=[]
for uid in sorted(used_barrels):
    assert uid not in retired and uid in vv and masks[uid]==vv[uid]['flashed']
    contacts_by_layer=collections.defaultdict(list)
    for edge in finite:
        if tuple(edge['a'])==('via',uid) or tuple(edge['b'])==('via',uid):contacts_by_layer[edge['layer']].append(edge)
    assert set(contacts_by_layer)<=set(masks[uid])
    surviving.append({'via_UUID':uid,'observed_actual_native_masks':masks[uid],'retained_native_source_geometry':vv[uid],'finite_external_contacts_by_layer':dict(contacts_by_layer),'new_layer_entries':False,'ordinary_destination_process_qualification_claimed':False})
put('surviving-actual-barrel-contact-and-mask-ledger.json',surviving)
out={'status':'REVIEWABLE_JOINT_REDUNDANT_ORDINARY_DRILL_RETIREMENT_NATIVE_CURRENT_ASSEMBLY_GATES_OPEN','native_current_parent_SHA256':pins[str(board)],'retired_via_UUIDs':retired_vias,
     'joint_sequential_deletion_controls':joint_trials,'final_whole_batch_simultaneously_proved':True,
     'retired_existing_via_actual_flashed_layers':{u:masks[u] for u in retired_vias},'mask_ledger_delta':[{'action':'retire_via_UUID','UUID':u,'retained_via_masks_unchanged':True,'physical_Cu_drill_union_equivalence_claimed':False} for u in retired_vias],
     'operations':operations,'retired_B_track_tail_steps':steps,'new_vias':0,'new_Cu':0,'new_plane_definitions':0,'new_footprints':0,'old_finite_boundary_contacts':boundary,
     'old_affected_group_native_keys':len({key(r) for r in rows}),'retained_native_keys':len(after.p),'retained_key_components_at_bound_native_tolerance':len(components),
     'retained_key_components_using_finite_overlap_only':strict_components,'source_role':source,'source_all_other_groups_retained_literal':True,
     'old_GND_or_power_reference_Cu_removed':False,'prospective_new_fill_not_used_for_connectivity_proof':True,'all109_rules_native_reference_file':str(rules),
     'rule_or_pad_Cu_Mask_Paste_source_geometry_modified':False,'all_unchanged_source_objects_literal':True,'counterfactual_source_SHA256_without_writing_PCB':hashlib.sha256(raw).hexdigest(),
     'frozen_9_track_peer_separation':peerchecks,'no_new_or_reclassified_VIPPO':True,'new_ordinary_destination_qualification_claimed':False,
     'retained_survivor_ordinary_annulus_SMD_gap_registration':'OPEN_SEPARATE_EXISTING_SITE_REVIEW; survivor is existing alternate-copper connectivity witness only',
     'removed_unregistered_nominal_SMD_drill_pairs':[r for u in retired_vias for r in candidate_assembly[u]],'retained_named_source_pads':sorted({(r['ref'],str(r['pin'])) for r in rows if r['kind']=='pad'}),
     'removed_signal_parallel_loop_geometry_not_claimed_identical':True,'no_new_required_layer_transition_or_return':True,'all_required_transfers_use_existing_finite_contact_barrels':True,
     'actual_native_retained_layer_pieces':len(layer_proof),'retained_current_source_geometry_rebound_to_stage2':True,
     'actual_named_pad_groups_before':[[sorted({(r['ref'],str(r['pin'])) for r in q if r['kind']=='pad'})] for q in gg],
     'native_AFTER_uncapped_relationships_all_old_reference_current_watchdog_SI_assembly_registration':'OPEN_REQUIRED','input_SHA256':pins,'inputs_unchanged':all(sha(Path(f))==v for f,v in pins.items()),'PCB_written':False,'adopted':False,'manufacturing_ready':False}
put('reviewable-retirement-packet.json',out)
print(json.dumps({'removed_vias':len(retired_vias),'removed_tracks':len(retired)-len(retired_vias),'actual_retained_components':len(components),'finite_only_components':strict_components,'inputs_unchanged':out['inputs_unchanged']}))
