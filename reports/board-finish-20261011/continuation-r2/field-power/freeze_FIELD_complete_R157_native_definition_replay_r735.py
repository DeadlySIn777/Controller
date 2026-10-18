"""Pinned definition-only FIELD replay. Does not stage a board or emit fill caches."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,uuid,time
from pathlib import Path
from decimal import Decimal
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in (H,ROOT,ROOT/'sbc-power',ROOT/'coupled-recovery'):sys.path.insert(0,str(d))
import ordinary_routes as O
from verify_source import parse,children,child,atom
from emit_logic_zones_r1 import render
from shapely.geometry import Polygon
OUT=H/'FIELD-complete-exact-R157-native-definition-only-replay-r735'
BASE=ROOT/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
FINAL=H/'R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r687/model.pkl'
SOURCE=ROOT/'R155-known-reference-native-diagnostic-r157/measure/copy/board.kicad_pcb'
LAND=H/'R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665'
NOTCH=H/'original-IO3-TMR-exact-local-two-notch-negative-outline-nominee-r573'
R687=FINAL.parent
R731=H/'R715-one-barrel-one-B-stub-exact-native-dependency-and-conditional-comparison-r731'
R733=H/'FIELD-current-R157-to-R687-exact-native-definition-dependency-inventory-r733'
PEER=ROOT/'U10003-HOST-R157-exact-sparse-native-API-clone-r271'
PROFILE=('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(v):return hashlib.sha256(v.wkb).hexdigest()
def artifact(p):return {'file':str(Path(p).resolve()),'SHA256':sha(p)}
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def nm(x):
    v=Decimal(str(x))*1000000;assert v==v.to_integral_value(),('non_integer_nm',x);return int(v)
def ring(r):return [[nm(x),nm(y)] for x,y in list(r.coords)[:-1]]
def parts(q):
    s=q['zone_outline_shape'];return sorted(list(s.geoms) if s.geom_type=='MultiPolygon' else [s],key=lambda x:(-x.area,x.bounds))
def ids(q):return [q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'separate-native-outer-'+str(i))) for i,_ in enumerate(parts(q))]
def poly_ast(a):
    rr=[[(float(v[1]),float(v[2])) for v in child(c,'pts')[1:]] for c in children(a,'polygon')]
    return Polygon(rr[0],rr[1:])
def profile_ast(a):
    cp=child(a,'connect_pads');f=child(a,'fill')
    return {'priority':int(atom(a,'priority') or 0),'clearance_mm':float(atom(cp,'clearance')),
        'min_thickness_mm':float(atom(a,'min_thickness')),'pad_connect_mode':'FULL_SOLID' if 'yes' in cp[1:] else 'UNBOUND',
        'island_removal_mode':int(atom(f,'island_removal_mode')),'thermal_gap_mm':float(atom(f,'thermal_gap')),
        'thermal_bridge_width_mm':float(atom(f,'thermal_bridge_width'))}
def draw(q,uid,part,template=None):
    prof={k:q[k] for k in PROFILE};assert prof['pad_connect_mode']=='FULL_SOLID'
    text=render(uid,q['net'],q['layer'],part)
    for before,after in [('(priority 20)','(priority %d)'%prof['priority']),('(clearance 0.15)','(clearance %.6f)'%prof['clearance_mm']),
        ('(min_thickness 0.15)','(min_thickness %.6f)'%prof['min_thickness_mm']),('(thermal_gap 0.15)','(thermal_gap %.6f)'%prof['thermal_gap_mm']),
        ('(thermal_bridge_width 0.3)','(thermal_bridge_width %.6f)'%prof['thermal_bridge_width_mm']),('(island_removal_mode 1)','(island_removal_mode %d)'%prof['island_removal_mode'])]:text=text.replace(before,after)
    text=text.replace('Retained LOGIC_GND return repair','Exact current FIELD native union')
    if template is not None:
        # Replace only polygon children. Every other native AST field is retained literally.
        a=parse(template.decode());oldpolys=children(a,'polygon');r=parse(text);newpolys=children(r,'polygon')
        assert profile_ast(a)==prof and atom(a,'net')==q['net'] and atom(a,'layer')==q['layer']
        marker=b'\t\t(polygon\n';start=template.index(marker);end=template.rfind(b'\t)')
        assert not children(a,'filled_polygon') and not children(a,'fill_segments')
        newraw=text.encode();s=newraw.index(marker);e=newraw.rfind(b'\t)')
        result=template[:start]+newraw[s:e]+template[end:]
        assert [x for x in a[1:] if x[0]!='polygon']==[x for x in parse(result.decode())[1:] if x[0]!='polygon']
    else:result=text.encode()
    a=parse(result.decode());assert atom(a,'uuid')==uid and atom(a,'net')==q['net'] and atom(a,'layer')==q['layer']
    assert profile_ast(a)==prof
    expected=[ring(part.exterior)]+[ring(r) for r in part.interiors]
    actual=[[[nm(float(v[1])),nm(float(v[2]))] for v in child(c,'pts')[1:]] for c in children(a,'polygon')]
    assert actual==expected and poly_ast(a).equals(part) and part.is_valid
    assert not children(a,'filled_polygon') and not children(a,'fill_segments')
    return result,expected
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    assert sha(FINAL)=='3449baef41f8da4cdd7458cb120e906017e2e0c488c061aee9343e4b09022ee0'
    assert sha(SOURCE)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
    assert sha(R733/'receipt.json')=='d1411d63969d314ba25a17aee468f4c27e9dc4b2d2eaf00343616e7c7596bc8e'
    assert sha(R731/'minimal-native-addition-recipe.json')=='1839c92fbfeb2260765c0d8e03e380755104546118df8f310388b372b1971349'
    assert sha(LAND/'only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl')=='4d7f1ea367403ac47c214970e5dd637f8672917fb8cd2360cc5eb18c325885d5'
    assert sha(NOTCH/'only-one-original-IO3-zone-outline-negative-replacement.pkl')=='f1d5b9c1550d996890ee8dba37c9fb19cd5337853df6778629541a82f2e252e6'
    g0,h0,b0,qs0,c0=pickle.loads(BASE.read_bytes());g,h,b,qs,c=pickle.loads(FINAL.read_bytes())
    before={q['uuid']:q for q in qs0};after={q['uuid']:q for q in qs}
    raw=SOURCE.read_bytes();head,chunks,tail=O.C.pcbtext.split(raw);assert head+b''.join(chunks)+tail==raw
    native={O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if O.C.pcbtext.chunk_uuid(ch)}
    nz={uid:ch for uid,ch in native.items() if O.C.pcbtext.chunk_kind(ch)=='zone'}
    net_tokens={atom(parse(ch.decode()),'net') for ch in nz.values() if atom(parse(ch.decode()),'net')}
    header_identity={k:pickle.dumps(h0.get(k),protocol=5)==pickle.dumps(h.get(k),protocol=5) for k in ('tracks','vias','pads','shapes','footprints','outline','rule_areas')};assert all(header_identity.values())
    removed=sorted(set(before)-set(after));new=sorted(set(after)-set(before));changed=[];unchanged=[]
    for uid in sorted(set(before)&set(after)):
        o=before[uid];n=after[uid]
        if any(o[k].wkb!=n[k].wkb for k in ('shape','zone_outline_shape')) or any(o.get(k)!=n.get(k) for k in PROFILE):changed.append(uid)
        else:unchanged.append(uid)
    assert len(removed)==12 and len(new)==4 and len(changed)==3 and len(unchanged)==33
    rows=[];same_parts=[];role_rows=[];modified_native=set()
    for uid in removed:
        for index,puid in enumerate(ids(before[uid])):
            ch=nz[puid];file=OUT/(puid+'.exact-before-delete-zone-chunk');file.write_bytes(ch);modified_native.add(puid)
            rows.append({'action':'delete','kind':'zone','uuid':puid,'proposal_UUID':uid,'part_index':index,'exact_before':artifact(file),'original_native_definition':False,'reason':'Retired owned member of exact current four unions'})
    b3manifest=json.loads((R687/'native-owner-profile-and-exact-IU-distinct-outer-chunk-rows.json').read_bytes())['rows']
    for uid in changed+new:
        q=after[uid];assert q['net'] in net_tokens;assert all(k in q for k in PROFILE)
        oldids=set(ids(before[uid])) if uid in before else set();newids=ids(q)
        role_rows.append({'proposal_UUID':uid,'raw_net':q['net'],'layer':q['layer'],'physical_WKB_SHA256':hs(q['shape']),
            'intended_WKB_SHA256':hs(q['zone_outline_shape']),'current_native_profiles':{k:q[k] for k in PROFILE},
            'constituent_proposal_UUIDs':q.get('constituent_proposal_UUIDs'),'old_native_UUIDs':sorted(oldids),'new_native_UUIDs':newids})
        for index,(puid,part) in enumerate(zip(newids,parts(q))):
            oldch=nz[puid] if puid in oldids else None
            if uid=='f595cb04-2945-5e6a-9b86-f7c7c6e1b0c1':
                br=next(r for r in b3manifest if r['UUID']==puid);ch=Path(br['chunk_file']).read_bytes();assert hashlib.sha256(ch).hexdigest()==br['chunk_SHA256']
                a=parse(ch.decode());assert poly_ast(a).equals(part) and profile_ast(a)=={k:q[k] for k in PROFILE}
                rings=[ring(part.exterior)]+[ring(r) for r in part.interiors]
            else:ch,rings=draw(q,puid,part,oldch)
            file=OUT/(puid+'.current-owned-zone-chunk');file.write_bytes(ch)
            row={'action':'replace' if oldch is not None else 'add','kind':'zone','uuid':puid,'proposal_UUID':uid,'part_index':index,
                'after':artifact(file),'raw_net':q['net'],'layer':q['layer'],'native_profile':{k:q[k] for k in PROFILE},
                'intended_part_WKB_SHA256':hs(part),'integer_ring_count':len(rings),'original_native_definition':False}
            if oldch is not None:
                oldfile=OUT/(puid+'.exact-before-replace-zone-chunk');oldfile.write_bytes(oldch);row['exact_before']=artifact(oldfile);modified_native.add(puid)
                a=parse(oldch.decode());na=parse(ch.decode());assert [x for x in a[1:] if x[0]!='polygon']==[x for x in na[1:] if x[0]!='polygon']
                row['every_non_polygon_native_AST_field_literal_equal']=True
            else:assert puid not in native
            rows.append(row)
        for puid in sorted(oldids-set(newids)):
            file=OUT/(puid+'.exact-before-delete-zone-chunk');file.write_bytes(nz[puid]);modified_native.add(puid)
            rows.append({'action':'delete','kind':'zone','uuid':puid,'proposal_UUID':uid,'exact_before':artifact(file),'original_native_definition':False,'reason':'Current component count/order owned replacement'})
    # Original native IO3 definition: use the exact frozen before/after pair, not filled polygons.
    ouid='54921f4b-0308-4821-9549-ff9360bf05ca';old=NOTCH/'exact-original-zone-before.chunk';newfile=NOTCH/'exact-original-zone-after-outline-only.chunk'
    assert sha(old)=='11aab152bdc7623a733ed7afa5cd7bbbbbd6c7310a9774907968b7b6a92041d3' and nz[ouid]==old.read_bytes()
    assert sha(newfile)=='81cfcfce4456d3a3df89a995eae8f4e81caf443c27e9aad6d51413aa442c7f81'
    oa=parse(old.read_text());na=parse(newfile.read_text());assert [x for x in oa[1:] if x[0]!='polygon']==[x for x in na[1:] if x[0]!='polygon']
    assert not children(na,'filled_polygon') and not children(na,'fill_segments');modified_native.add(ouid)
    rows.append({'action':'replace','kind':'zone','uuid':ouid,'exact_before':artifact(old),'after':artifact(newfile),
        'original_native_definition':True,'reason':'R573 two scoped negative outer notches against actual TMR no-zone area',
        'every_non_polygon_native_AST_field_literal_equal':True,'no_manual_native_filled_polygon_edit':True,'owner_receipt':artifact(NOTCH/'receipt.json')})
    # Positive local landing definitions are independently frozen; never force an old barrel layer flag.
    landmanifest=json.loads((LAND/'native-exact-local-zone-chunk-rows.json').read_bytes());lr=landmanifest.get('rows',landmanifest) if isinstance(landmanifest,dict) else landmanifest
    for row in lr:
        puid=row.get('UUID',row.get('uuid'));path=Path(row.get('chunk_file',row.get('file')))
        if not path.is_absolute():path=LAND/path
        ch=path.read_bytes();assert puid not in native and O.C.pcbtext.chunk_uuid(ch)==puid
        a=parse(ch.decode());assert not children(a,'filled_polygon') and not children(a,'fill_segments')
        rows.append({'action':'add','kind':'zone','uuid':puid,'after':artifact(path),'raw_net':atom(a,'net'),'layer':atom(a,'layer'),
            'native_profile':profile_ast(a),'reason':'R665 source-rooted old-barrel local positive landing; actual native flash remains required','owner_receipt':artifact(LAND/'receipt.json')})
    assert len(lr)==23
    add_recipe=json.loads((R731/'minimal-native-addition-recipe.json').read_bytes())
    for row in add_recipe['add_rows']:
        assert row['uuid'] not in native;rows.append({'action':'add','kind':row['kind'],'uuid':row['uuid'],'after':{'file':row['chunk_file'],'SHA256':row['chunk_SHA256']},'raw_net':row['raw_net'],'reason':'R731 conditional signed-current parallel ordinary reinforcement; native all6/contact/current/thermal OPEN'})
    # Retained native definitions are literal identity. Preserve existing native profiles for missing host fields.
    for uid in unchanged:
        for puid in ids(after[uid]):
            ch=nz[puid];a=parse(ch.decode());same_parts.append({'proposal_UUID':uid,'native_UUID':puid,'chunk_SHA256':hashlib.sha256(ch).hexdigest(),
                'raw_net':atom(a,'net'),'layer':atom(a,'layer'),'native_profile_authority':profile_ast(a),
                'host_missing_profile_fields':[k for k in PROFILE if k not in after[uid]],'unchanged_native_bytes_retained':True})
    touched=[r['uuid'] for r in rows];assert len(touched)==len(set(touched)), 'Two operations own same native UUID'
    # Compare ROOT native two positive FG bodies with current field intents, physically and as definitions.
    peerraw=(PEER/'copy/board.kicad_pcb').read_bytes();assert hashlib.sha256(peerraw).hexdigest()=='deee57788a5ba62ede98730231377069936d5474bb527e6dbed0b832ae6c8d38'
    ph,pc,pt=O.C.pcbtext.split(peerraw);peernative={O.C.pcbtext.chunk_uuid(ch):ch for ch in pc if O.C.pcbtext.chunk_uuid(ch)}
    roots=['9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-8315-5464-b6dc-8a911c251c38']
    # Native API is authoritative for the full second UUID rather than assumed spelling.
    api=json.loads((PEER/'expected-native-API.json').read_bytes());roots=[r['uuid'] for r in api['zones']];assert len(roots)==2
    conflicts=[];peeridentity=[]
    landing_objects=pickle.loads((LAND/'only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl').read_bytes())
    if isinstance(landing_objects,dict):landing_objects=landing_objects.get('proposals',landing_objects.get('zones',landing_objects))
    # Native chunk geometry drives overlap evidence, including every existing original or owned current role.
    target_parts=[]
    for q in qs:
        for puid,part in zip(ids(q),parts(q)):target_parts.append({'uuid':puid,'proposal_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'shape':part,'profile':{k:q[k] for k in PROFILE if k in q},'physical':q['shape']})
    for r in lr:
        puid=r.get('UUID',r.get('uuid'));path=Path(r.get('chunk_file',r.get('file')));a=parse(path.read_text());target_parts.append({'uuid':puid,'proposal_UUID':puid,'raw_net':atom(a,'net'),'layer':atom(a,'layer'),'shape':poly_ast(a),'profile':profile_ast(a),'physical':None})
    for uid in roots:
        ch=peernative[uid];a=parse(ch.decode());shape=poly_ast(a);profile=profile_ast(a);rawnet=atom(a,'net');layer=atom(a,'layer')
        saved=OUT/(uid+'.ROOT-exact-positive-zone-chunk');saved.write_bytes(ch)
        peeridentity.append({'uuid':uid,'chunk':artifact(saved),'raw_net':rawnet,'layer':layer,'native_profile':profile,'intended_WKB_SHA256':hs(shape),'bounds_mm':list(shape.bounds)})
        assert uid not in touched
        for r in target_parts:
            if r['layer']!=layer or not shape.intersects(r['shape']):continue
            intersection=shape.intersection(r['shape']);f=OUT/(uid+'--'+r['uuid']+'.intended-overlap.wkb');f.write_bytes(intersection.wkb)
            conflicts.append({'ROOT_uuid':uid,'FIELD_native_uuid':r['uuid'],'FIELD_proposal_UUID':r['proposal_UUID'],'same_raw_net':r['raw_net']==rawnet,
                'same_complete_native_profile':r['profile']==profile,'intersection_geom_type':intersection.geom_type,'intersection_area_mm2':intersection.area,
                'intersection_length_mm':intersection.length,'intersection_bounds_mm':list(intersection.bounds),'overlap':artifact(f),
                'FIELD_intended_WKB_SHA256':hs(r['shape']),'FIELD_physical_WKB_SHA256':hs(r['physical']) if r['physical'] is not None else None,
                'native_equal_settings_same_net_overlap_requires_explicit_union_or_partition_before_DRC':True})
    put(OUT/'native-zone-definition-operations.json',rows)
    put(OUT/'owned-role-native-mapping-and-current-profiles.json',role_rows)
    put(OUT/'literal-unchanged-owned-native-part-profile-authority.json',same_parts)
    put(OUT/'ROOT-R271-two-positive-FG-zone-overlap-and-UUID-conflicts.json',{'ROOT_positive_zone_identity':peeridentity,'conflicts':conflicts,'no_native_UUID_collision':True,'no_geometry_union_or_peer_overlay_applied':True})
    retained_native={uid:hashlib.sha256(ch).hexdigest() for uid,ch in native.items() if uid not in modified_native}
    put(OUT/'all-other-native-chunk-identity.json',retained_native)
    recipe={'status':'PINNED_DEFINITION_ONLY_FIELD_REPLAY_FOR_ONE_FUTURE_ALL_NET_DIAGNOSTIC_NO_STAGE_NO_ADOPTION',
        'native_parent':artifact(SOURCE),'baseline_host_model':artifact(BASE),'current_field_host_model':artifact(FINAL),
        'actual_source_reference_and_contact_identity_receipt':artifact(H/'native-same-settings-four-unions-explicit-corner-additions-qualified-r645/receipt.json') if (H/'native-same-settings-four-unions-explicit-corner-additions-qualified-r645/receipt.json').exists() else {'R645_receipt_SHA256':'a290ae014dc4844446ad9ae392f3d3c86f36b98eb1a9e87d2e7a1feaa3cfa064','scope':'Incremental actual physical roles/source/direct/oldreferences, never complete current/native qualification'},
        'operations':artifact(OUT/'native-zone-definition-operations.json'),'unchanged_native_chunks':artifact(OUT/'all-other-native-chunk-identity.json'),
        'profile_and_role_mapping':artifact(OUT/'owned-role-native-mapping-and-current-profiles.json'),'existing_native_profile_identity':artifact(OUT/'literal-unchanged-owned-native-part-profile-authority.json'),
        'ROOT_peer_overlap_conflicts':artifact(OUT/'ROOT-R271-two-positive-FG-zone-overlap-and-UUID-conflicts.json'),
        'superseded_owned_roles':removed,'current_union_roles':new,'shared_owned_role_changes':changed,
        'original_native_outline_changes':[ouid],'original_native_FP_tracks_vias_pad_masks_holes_ruleareas_rules_no_changes':True,
        'FIELD5_U25_REG312_already_present_in_R157_NATIVE_header_no_duplicate_additions':True,
        'all_header_identity_before_current':header_identity,'no_filled_polygon_arrays_serialized_edited_or_injected':True,
        'ROOT_two_positive_zones_remain_separate_peer_authority_no_blanket_merge':True,
        'other_shared_scope_conflicts':['Q0 FA 7ef and FG e2fe scopes require exact sparse negative replay against these current shapes','SBC CM79 FB In2 q053 coupled local removal remains separately current/source gated','ROOT R271 FG In1 9fe may overlap current FG In1 union; see exact overlap ledger','SBC/ROOT native original549 ordinary antipads are CPP-derived, not original outline replacements'],
        'required_fresh_native_full_state':'All-net candidate fill; old original masks exact, all new ordinary all6/annular contacts/source groups and raw native profiles/DRC checked independently',
        'preserved_failures':['R669 selected-cache old-reference/source-array changes unqualified against full-before; no comparison waiver','R695/R703 failed full numeric matrices; R729 numerical subset conditional only','Inherited CORE full-body/drop/current/thermal failures OPEN','Prior native 8 same-net/profile overlaps remain failed until exact future composition','R157 22 old-mask contract differences remain unresolved; local landings require actual native contact','R721 inscribed graph cap mismatch and raw In4 new ground-stub shadow gap remain explicitly held'],
        'FA_FB_positive_plus_return_drop_policy_V':.48,'FIELD5_drop_budget_NOT_qualified':True,
        'signed_current_loop_barrel_plating_hot_current_temperature_rise_transients_physical_device_ratings':'OPEN',
        'jobs_started':0,'board_written':False,'adopted':False}
    put(OUT/'complete-field-native-definition-only-replay.json',recipe)
    put(OUT/'receipt.json',{'status':recipe['status'],'recipe_SHA256':sha(OUT/'complete-field-native-definition-only-replay.json'),
        'zone_operations':{a:sum(r['kind']=='zone' and r['action']==a for r in rows) for a in ('delete','replace','add')},
        'new_segments':sum(r['kind']=='segment' for r in rows),'new_vias':sum(r['kind']=='via' for r in rows),
        'ROOT_peer_overlap_pairs':len(conflicts),'all_other_native_chunks_retained':len(retained_native),'current_owned_roles':len(qs),
        'header_identity':header_identity,'integer_ring_native_AST_roundtrip':True,'only_declared_original_outline_UUID':ouid,
        'no_native_fill_or_stage_or_cache_edit':True,'adopted':False,'elapsed_seconds':time.monotonic()-started})
    print('R735_COMPLETE',sha(OUT/'receipt.json'),'recipe',sha(OUT/'complete-field-native-definition-only-replay.json'),'operations',len(rows),'peer_overlaps',len(conflicts),flush=True)
if __name__=='__main__':main()
