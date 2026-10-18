"""Screen saved add-only routes against the genuine R299 full native state.

No native fill, source edit, forced flash, aperture expansion or adoption.
Only locally accepted route groups are emitted into a disposable candidate.
"""
import os, sys
sys.dont_write_bytecode = True
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
import psutil
proc = psutil.Process(); proc.cpu_affinity(list(range(16, 28))); proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib, json, math, pickle, shutil, time
from pathlib import Path
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OLD = PROJECT / 'reports/board-finish-20261011/continuation-r2'
for folder in (OLD, OLD/'field-power', OLD/'sbc-power', OLD/'coupled-recovery'):
    sys.path.insert(0, str(folder))
import R157_native_selected_actual_conversion_r673 as N
K = N.K; L = N.L
OUT = HERE / 'actual-R299-R310-R315-audit-and-candidate-r1'
P = PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
NF = OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full'
SOURCE = NF.parent/'copy/board.kicad_pcb'
GND = '/LOGIC_GND'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def put(name, value):
    (OUT/name).write_text(json.dumps(value, indent=1, allow_nan=False)+'\n', encoding='utf-8')

def info(shape):
    return {'EMPTY': shape.is_empty, 'type': shape.geom_type, 'area_mm2': shape.area,
            'length_mm': shape.length, 'bounds_mm': None if shape.is_empty else list(shape.bounds),
            'WKB_SHA256': hashlib.sha256(shape.wkb).hexdigest()}

def save(label, shape):
    row = info(shape)
    if not shape.is_empty:
        path = OUT/(label+'.wkb'); path.write_bytes(shape.wkb); row['file'] = str(path)
    return row

def body(track):
    return K.Z.bounded_buffer(LineString([track['a'], track['b']]), track['w']/2)

def native_chunk(track):
    fmt = lambda x: format(x, '.9f').rstrip('0').rstrip('.')
    text = ('\t(segment\n\t\t(start '+fmt(track['a'][0])+' '+fmt(track['a'][1])+')\n'
            '\t\t(end '+fmt(track['b'][0])+' '+fmt(track['b'][1])+')\n'
            '\t\t(width '+fmt(track['w'])+')\n\t\t(layer "'+track['layer']+'")\n'
            '\t\t(net "'+track['net']+'")\n\t\t(uuid "'+track['uuid']+'")\n\t)\n')
    return text.encode()

def main():
    started=time.monotonic()
    assert not OUT.exists(), 'Preserve prior audit; use a separately versioned output'
    parent_receipt=P/'actual-graph-cache-receipt.json'
    assert parent_receipt.is_file(), 'Finish root R763 actual full AFTER graph first'
    OUT.mkdir(parents=True)
    parent=json.loads(parent_receipt.read_bytes())
    assert parent['native_candidate_SHA256']=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
    model_file=P/'actual-combined-full-after-model.pkl'; graph_file=P/'actual-combined-full-after-all-net-groups.pkl'
    assert sha(model_file)==parent['after_actual_model_SHA256'] and sha(graph_file)==parent['after_actual_groups_SHA256']
    h=pickle.loads(model_file.read_bytes()); groups=pickle.loads(graph_file.read_bytes())
    source=K.root(groups[GND], 'J11001', '2'); sourcekeys=K.keys(source)
    assert sha(SOURCE)==parent['native_candidate_SHA256']
    native_receipt=json.loads((NF/'receipt.json').read_bytes())
    assert not native_receipt['discrete_Cu_errors'] and not native_receipt['old_actual_or_NEW_ordinary_mask_errors']
    actual_flash=json.loads((NF/'actual-full-refill-via-flashes.json').read_bytes())['vias']
    raw=SOURCE.read_bytes(); iv=K.C.inventory(raw); netidentity=K.A.N.SourceNets(raw)
    rec, trees=K.F.build({**h, 'zones': []})
    fills={ly:[] for ly in K.LAYERS}
    for z in h['zones']:
        for ly, rs in z['fills'].items():
            for shape in L.poly(rs):
                fills[ly].append({'uuid':z['uuid'], 'net':z['net'], 'local':float(z['clearance_mm']), 'shape':shape})
    ftrees={ly:STRtree([r['shape'] for r in rows]) for ly, rows in fills.items()}
    holes=[(v['uuid'], Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h['vias']]
    holes += [(p['uuid'], sh) for p in h['pads'] for sh in L.poly(p.get('hole') or [])]
    ht=STRtree([r[1] for r in holes]); domains=h['domains_normalized']
    gap=lambda a,b: .15 if domains.get(L.norm(a))==domains.get(L.norm(b)) else .6
    reserve, exempt=K.A.reservations(); outline=unary_union(L.poly(h['outline'])).buffer(-.525)
    source_fill={ly:unary_union([r['shape'] for r in source if r['kind']=='fill' and r['layer']==ly]) for ly in K.LAYERS}
    source_all={ly:unary_union([r['shape'] for r in source if r['layer']==ly]) for ly in K.LAYERS}
    via_by={v['uuid']:v for v in h['vias']}; zone_by={z['uuid']:z for z in h['zones']}
    packet=OLD/'current-R753-short-logic-no-hole-surface-construction-r307/ONLY_NEW-short-surface-physical-nominees-NOT_MODEL.pkl'
    assert sha(packet)=='ad00b11785d328664c575c90a895f0495eafffdf8681851f780808d5d81fee9d'
    short=[r for r in pickle.loads(packet.read_bytes()) if r['index'] in (1,13)]
    routes=[{'name':'R310-'+str(r['index']), 'tracks':r['tracks'], 'endpoints':r['endpoints'], 'old_ports':[]} for r in short]
    pairfile=OLD/'existing-old-In3-port-current-physical-r315-pair0/only-new-SDO-B-tracks-physical-nominee-NOT_MODEL.pkl'
    assert sha(pairfile)=='cf8ffddeb984dbc3cdf4e4ef8826388d24c0e8cf431e9eb9772177f7af20eb8e'
    pair=pickle.loads(pairfile.read_bytes()); assert len(pair)==1
    ports=['948d8358-b797-42b2-8bba-9dc679de42ca','3ed57587-ddf5-416c-906f-85e99ba3db27']
    routes.append({'name':'R315-pair0', 'tracks':pair[0]['tracks'], 'endpoints':ports, 'old_ports':ports})
    checks=[]; rows=[]; selected=[]; return_rows=[]
    for route in routes:
        errors=[]; nt=route['tracks']; net=L.norm(nt[0]['net']); ly=nt[0]['layer']; whole=unary_union([body(t) for t in nt])
        for t in nt:
            assert t['uuid'] not in iv[3] and netidentity.raw(net)==t['net'] and t['w']==.2
            axis=LineString([t['a'],t['b']]); radius=t['w']/2; sh=body(t)
            assert t['layer']==ly and L.norm(t['net'])==net
            if not outline.covers(sh):errors.append({'kind':'board_edge','UUID':t['uuid']})
            for j in trees[ly].query(sh.buffer(.85),predicate='intersects'):
                old=rec[ly][int(j)]
                if L.norm(old['net'])==net:continue
                if old['kind']=='via':v=old['source'];distance=axis.distance(Point(v['x'],v['y']))-radius-v['d']/2
                elif old['kind']=='track' and not old['source'].get('m'):
                    oldt=old['source'];distance=axis.distance(LineString([oldt['a'],oldt['b']]))-radius-oldt['w']/2
                else:distance=axis.distance(old['shape'])-radius
                required=gap(net,old['net'])+.025+(.005 if old['kind']=='pad' else 0)
                row={'kind':'actual_discrete_'+old['kind'],'new_UUID':t['uuid'],'other_UUID':old['uuid'],'layer':ly,'gap_mm':distance,'required_mm':required}
                checks.append(row)
                if distance<required:errors.append(row)
            for j in ftrees[ly].query(sh.buffer(.85),predicate='intersects'):
                old=fills[ly][int(j)]
                if L.norm(old['net'])==net:continue
                distance=axis.distance(old['shape'])-radius;required=max(old['local'],gap(net,old['net']))+.025
                row={'kind':'actual_FULL_R299_foreign_fill_hard','new_UUID':t['uuid'],'other_UUID':old['uuid'],'raw_net':old['net'],'layer':ly,'gap_mm':distance,'required_mm':required}
                checks.append(row)
                if distance<required:errors.append(row)
            for j in ht.query(sh.buffer(.285),predicate='intersects'):
                uid, hole=holes[int(j)]
                if uid in route['endpoints']:continue
                distance=axis.distance(hole)-radius-.005
                row={'kind':'every_other_actual_drill','new_UUID':t['uuid'],'other_UUID':uid,'gap_mm':distance,'required_mm':.275}
                checks.append(row)
                if distance<.275:errors.append(row)
            for rule in h['rule_areas']:
                if ly in rule['layers'] and rule.get('no_tracks') and any(sh.distance(s)<.025 for s in L.poly(rule['outline'])):
                    errors.append({'kind':'native_no_tracks','new_UUID':t['uuid'],'rule_UUID':rule['uuid']})
            for rule in reserve['keepouts']:
                if ly in rule['layers'] and net not in exempt.get(rule['name'],set()) and any(sh.distance(s)<.025 for s in L.poly(rule['outline'])):
                    errors.append({'kind':'frozen_reservation','new_UUID':t['uuid'],'rule':rule['name']})
        inner=K.MAP[ly]; raw_gap=whole.difference(source_fill[inner]); allowance=[]; own_ledgers=[]
        for uid in route['old_ports']:
            sig=via_by[uid]; assert actual_flash[uid]==sig['flashed'] and sig['d']==.6 and sig['drill']==.3
            assert K.C.sha(iv[3][uid]) in ('1a4bc876b5ba5f59eac22cdddb9bce0c074d07c776010aa7f385d4a40e7d72c6','7db3d1267a0210d99e09f92487a09319675afba8cb663b62e3c04b02de1ee89e')
            axis=Point(sig['x'],sig['y']); own=axis.buffer(.575,quad_segs=256)
            owners={r['uuid'] for r in source if r['kind']=='fill' and r['layer']==inner and r['shape'].distance(own)<.8}
            design=unary_union([sh for zid in owners for sh in L.poly(N.O.polys(zone_by[zid]['outline']))])
            allowed=own.intersection(design); cuts=[]
            for j in trees[inner].query(own.buffer(1),predicate='intersects'):
                old=rec[inner][int(j)]
                if old['uuid']==uid or L.norm(old['net'])==GND:continue
                cuts.append(K.Z.bounded_buffer(old['shape'],max(.25,gap(GND,old['net']))+.025))
            for j in ht.query(own,predicate='intersects'):
                other,hole=holes[int(j)]
                if other!=uid:cuts.append(K.Z.bounded_buffer(hole,.005))
            for r in fills[inner]:
                if L.norm(r['net'])!=GND and r['shape'].distance(own)<1:
                    cuts.append(K.Z.bounded_buffer(r['shape'],max(.25,r['local'],gap(GND,r['net']))+.025))
            for rule in h['rule_areas']:
                if inner in rule['layers'] and rule.get('no_zones'):
                    cuts.extend(K.Z.bounded_buffer(sh,.025) for sh in L.poly(rule['outline']) if sh.distance(own)<.025)
            allowed=allowed.difference(unary_union(cuts)); transfers=[]
            signal_annulus=axis.buffer(sig['d']/2,quad_segs=128).difference(axis.buffer(sig['drill']/2,quad_segs=128))
            signal_annulus=signal_annulus.difference(unary_union([holes[int(j)][1] for j in ht.query(signal_annulus,predicate='intersects')]))
            inherited_layer_use=[]
            for j in trees[ly].query(signal_annulus,predicate='intersects'):
                old=rec[ly][int(j)]
                if old['kind']!='track' or L.norm(old['net'])!=net:continue
                hit=old['shape'].intersection(signal_annulus)
                if hit.is_empty or hit.area<=0:continue
                inherited_layer_use.append({'track_UUID':old['uuid'],'native_chunk_SHA256':K.C.sha(iv[3][old['uuid']]),'actual_existing_layer':ly,'finite_current_track_to_actual_unchanged_port_annulus':info(hit)})
            for ret in h['vias']:
                if L.norm(ret['net'])!=GND:continue
                dist=math.dist((sig['x'],sig['y']),(ret['x'],ret['y']))
                if not .9<=dist<1.:continue
                ann=Point(ret['x'],ret['y']).buffer(ret['d']/2,quad_segs=128).difference(Point(ret['x'],ret['y']).buffer(ret['drill']/2,quad_segs=128))
                areas={plane:ann.intersection(source_fill[plane].buffer(-.075,quad_segs=128)).area for plane in ('In1.Cu','In4.Cu')}
                rooted=all(('via',ret['uuid'],plane) in sourcekeys and plane in actual_flash[ret['uuid']] for plane in areas)
                transfers.append({'return_UUID':ret['uuid'],'distance_mm':dist,'actual_In1_In4_source_keys_and_observed_flash':rooted,'interior_annular_contact_mm2':areas,'PASS':rooted and all(a>.004 for a in areas.values())})
            passed=any(row['PASS'] for row in transfers)
            inherited=bool(inherited_layer_use) and ly in actual_flash[uid]
            return_rows.append({'signal_UUID':uid,'exact_unchanged_old_geometry':True,'no_new_hole_or_layer_mask':True,'transfer_candidates':transfers,'actual_return_transfer_PASS':passed,'literal_existing_same_signal_layer_track_annular_contacts':inherited_layer_use,'same_layer_extension_of_existing_native_transition':inherited})
            own_ledgers.append({'signal_UUID':uid,'exact_own_radius_mm':.575,'radius_expansion_mm':0,'actual_source_zone_owners':sorted(owners),'allowed_own_aperture':save(uid+'-source-supported-own-aperture',allowed),'return_transfer_PASS':passed,'same_layer_extension_of_existing_native_transition':inherited})
            if passed or inherited:allowance.append(allowed)
            else:errors.append({'kind':'existing_signal_via_needs_actual_same_domain_return_transfer','signal_UUID':uid})
        final_gap=whole.difference(unary_union([source_fill[inner],*allowance]))
        if not final_gap.is_empty:errors.append({'kind':'strict_actual_SOURCE_full_body_reference_gap','gap':save(route['name']+'-strict-reference-gap',final_gap)})
        contact=whole.intersection(source_all[ly]) if net==GND else Point().buffer(0)
        if net==GND and (contact.is_empty or contact.area<=0):errors.append({'kind':'ground_route_lacks_finite_same_layer_actual_J1_SOURCE_contact'})
        touched=[]
        for i, group in enumerate(groups[net]):
            if any(q['kind']!='fill' and q['layer']==ly and q['shape'].distance(whole)<=.000002 for q in group):touched.append(i)
        if len(touched)<2:errors.append({'kind':'route_does_not_touch_two_actual_full_native_groups','groups':touched})
        rows.append({'name':route['name'],'net':net,'layer':ly,'tracks':len(nt),'actual_NATIVE_R299_groups_touched':touched,'raw_actual_source_reference_gap':save(route['name']+'-raw-reference-gap',raw_gap),'qualified_own_apertures':own_ledgers,'strict_final_reference_gap':info(final_gap),'finite_ground_actual_J1_contact':info(contact),'errors':errors,'host_gate':'PASS' if not errors else 'FAIL','native_AFTER_current_ESD_watchdog_SI':'OPEN'})
        if not errors:selected.extend(nt)
        print('ROUTING_GROUP',route['name'],len(errors),flush=True)
    # All selected routes must coexist under the same conservative guards.
    for i,a in enumerate(selected):
        for b in selected[i+1:]:
            if a['layer']!=b['layer'] or L.norm(a['net'])==L.norm(b['net']):continue
            distance=LineString([a['a'],a['b']]).distance(LineString([b['a'],b['b']]))-a['w']/2-b['w']/2
            assert distance>=gap(a['net'],b['net'])+.025, 'Selected route groups mutually conflict'
    put('all-true-geometry-checks.json',checks);put('route-group-audit.json',rows);put('old-signal-via-actual-return-transfers.json',return_rows)
    adds={t['uuid']:native_chunk(t) for t in selected};netidentity.assert_chunks(adds)
    for uid,ch in adds.items():
        parsed=K.A.G.parse(uid,ch,{})
        t=next(t for t in selected if t['uuid']==uid)
        assert (parsed['net'],parsed['layer'],parsed['w'],list(parsed['a']),list(parsed['b']))==(L.norm(t['net']),t['layer'],t['w'],list(t['a']),list(t['b']))
        (OUT/('add-'+uid+'.native-chunk')).write_bytes(ch)
    candidate=None
    if adds:
        at=raw.rfind(b')');addition=b''.join(adds.values());result=raw[:at]+addition+raw[at:];observed=K.C.inventory(result)
        assert set(observed[3])==set(iv[3])|set(adds) and all(observed[3][uid]==ch for uid,ch in iv[3].items())
        assert result[:at]+result[at+len(addition):]==raw
        candidate=OUT/'candidate';candidate.mkdir();board=candidate/'board.kicad_pcb';board.write_bytes(result)
        for sidecar in SOURCE.parent.iterdir():
            if sidecar.name=='board.kicad_pcb' or sidecar.name.endswith('.lck'):continue
            if sidecar.is_dir():shutil.copytree(sidecar,candidate/sidecar.name)
            else:shutil.copy2(sidecar,candidate/sidecar.name)
        assert all(sha(p)==sha(candidate/p.name) for p in SOURCE.parent.iterdir() if p.is_file() and p.name!='board.kicad_pcb' and not p.name.endswith('.lck'))
        put('copied-project-source-sidecars.json',{'source_directory':str(SOURCE.parent),'files':[{ 'relative_path':str(p.relative_to(SOURCE.parent)), 'source_SHA256':sha(p), 'copy_SHA256':sha(candidate/p.relative_to(SOURCE.parent))} for p in SOURCE.parent.rglob('*') if p.is_file() and p.name!='board.kicad_pcb' and not p.name.endswith('.lck')]})
    operations=[{'action':'add','UUID':u,'kind':'segment','file':str(OUT/('add-'+u+'.native-chunk')),'SHA256':hashlib.sha256(ch).hexdigest()} for u,ch in adds.items()]
    put('native-add-only-manifest.json',{'baseline_file':str(SOURCE),'baseline_SHA256':sha(SOURCE),'operations':operations,'all_unlisted_native_chunks_header_tail_literal':True,'new_vias':0,'deletions':0,'native_AFTER':'OPEN'})
    pins=[Path(__file__),parent_receipt,model_file,graph_file,NF/'receipt.json',NF/'actual-full-refill-via-flashes.json',SOURCE,SOURCE.with_suffix('.kicad_pro'),SOURCE.with_suffix('.kicad_dru'),packet,pairfile]
    put('receipt.json',{'status':'ACTUAL_R299_HOST_SCREEN_COMPLETE_NATIVE_AFTER_OPEN','route_groups':[{k:r[k] for k in ('name','tracks','host_gate')} for r in rows],'selected_new_tracks':len(adds),'candidate_file':None if candidate is None else str(candidate/'board.kicad_pcb'),'candidate_SHA256':None if candidate is None else sha(candidate/'board.kicad_pcb'),'all_original_native_chunks_literal_count':len(iv[3]),'parent_R763_graph_status':parent['status'],'parent_R763_contact_reference_current_gates':'PENDING_SEPARATE_NOT_PROMOTED_BY_GRAPH_CACHE','input_SHA256':{str(p):sha(p) for p in pins},'runtime':sys.executable,'CPU_affinity':proc.cpu_affinity(),'numeric_threads':2,'native_jobs':0,'source_live_adopted_or_original_files_modified':False,'manufacturing_ready':False,'adopted':False,'native_after_fullfill_source_oldrefs_DRC_current_ESD_timing_SI':'OPEN','elapsed_seconds':time.monotonic()-started})
    print('ROUTING_COMPLETE',len(adds),sha(OUT/'receipt.json'),flush=True)

if __name__=='__main__':main()
