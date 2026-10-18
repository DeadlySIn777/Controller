"""Only exact R201/R195 deltas on positive R73; minimal required same-net unions."""
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import restore_SAFE_generated_precision_states_r168 as PS
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as AT
O=H/'sbc-power/positive-monitor-wider-IO3-U10017-minimal-joint-r211'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ds(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
settings=('clearance_mm','min_thickness_mm','pad_connect_mode','priority','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def canonical(s):
 ps=[]
 for part in GP.p.hubs.components(set_precision(s,1e-6)):
  rr=[[(int(round(x*1e6))/1e6,int(round(y*1e6))/1e6) for x,y in list(r.coords)[:-1]] for r in [part.exterior]+list(part.interiors)]
  q=Polygon(rr[0],rr[1:]);assert q.is_valid;ps.append(q)
 return ps[0] if len(ps)==1 else MultiPolygon(ps) if ps else GeometryCollection()
def main():
 assert not O.exists();O.mkdir();mp=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';assert sha(mp)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011'
 g,h,b,z,c=pickle.loads(mp.read_bytes());base_h=copy.deepcopy(h);base_z=copy.deepcopy(z);headers={q['uuid']:q for q in c['zones'] if q.get('prospective_not_native')}
 # Restore only the36 bound original canonical roles, then explicitly bind
 # ROOT55/ROOT73 constructor roles with unchanged WKB and source receipts.
 known=[q for q in z if q['uuid'] in set(b['restored_generated_grid_UUIDs'])];assert len(known)==36;PS.restore_bound_generated_precision_states(b,known)
 extra=[]
 for q in z:
  if q['uuid'] in set(b['restored_generated_grid_UUIDs']):continue
  assert q['uuid'] in {'ec99314b-c244-5748-bb67-de032c66ee3c','93bd9369-a6ff-537a-8678-5c84db255e75'}
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==raw;extra.append({'UUID':q['uuid'],'role':role,'grid_mm':1e-6,'unchanged_WKB_SHA256':ds(q[role]),'constructor':'ROOT55' if q['uuid'].startswith('ec993') else 'ROOT73'})
 packet=H/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201/receipt.json';assert sha(packet)=='cee3eacedd73ba63788decafd0a3b169afee6a0fbfa76f76e5acc60e8cc83e2d';pr=json.loads(packet.read_bytes());row=pr['only_one_owned_host_group_replacement'][0]
 qf=Path(pr['replacement_objects_file']);assert sha(qf)==pr['replacement_objects_sha256'];wide=pickle.loads(qf.read_bytes());assert len(wide)==1
 old=next(q for q in z if q['uuid']==row['old_UUID'])
 for role in ('shape','zone_outline_shape'):
  assert ds(old[role])==row['roles'][role]['old_sha256'] and ds(wide[0][role])==row['roles'][role]['new_sha256']
  raw=wide[0][role].wkb;wide[0][role]=set_precision(wide[0][role],1e-6,mode='pointwise');assert wide[0][role].wkb==raw
 z=[wide[0] if q['uuid']==old['uuid'] else q for q in z];headers[wide[0]['uuid']]=headers.pop(old['uuid'])|{'uuid':wide[0]['uuid']}
 # Exact field owned Cu/plane, never the stale whole R195 h or z.
 fd=H/'field-power/U10017-wider-on-exact-IO3-audit-r195';assert sha(fd/'receipt.json')=='cba38d79c9f7fdb74343b2253ae33e7356ab0d1e00af57c22acfd77e629f4a56'
 fg,fh,fb,fz,fc=pickle.loads((fd/'model.pkl').read_bytes());d=pickle.loads((fd/'proposed-discrete.pkl').read_bytes());nq=pickle.loads((fd/'new-owned-zones.pkl').read_bytes());assert len(d['vias'])==1 and len(d['tracks'])==3 and len(nq)==1
 removed='5c6ebac9-c76a-41f1-8cb8-45e2321f2e89';oldtrack=next(t for t in h['tracks'] if t['uuid']==removed)
 original=next(t for t in pickle.loads((H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183/model.pkl').read_bytes())[1]['tracks'] if t['uuid']==removed);assert oldtrack==original
 assert not{q['uuid'] for q in d['vias']} & {q['uuid'] for q in h['vias']}and not{q['uuid'] for q in d['tracks']} & {q['uuid'] for q in h['tracks']}
 h=copy.deepcopy(h);h['tracks']=[t for t in h['tracks'] if t['uuid']!=removed]+d['tracks'];h['vias']+=d['vias']
 before_owned={q['uuid']:copy.deepcopy(q) for q in z};z,vg=GP.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,tg,_=AT.normalize_owned_track_guards({**h,'tracks':d['tracks']},z)
 field_states=[r for r in fb['generated_precision_state_ledger'] if r['new_generated_UUID']==nq[0]['uuid']]
 assert len(field_states)==2
 for r in field_states:
  q=nq[0];role=r['role'];assert ds(q[role])==r['unchanged_WKB_SHA256'];raw=q[role].wkb;q[role]=set_precision(q[role],r['grid_mm'],mode=r['mode']);assert q[role].wkb==raw
 z+=nq;headers[nq[0]['uuid']]=next(q for q in fc['zones'] if q['uuid']==nq[0]['uuid'])
 settings_resolution=[]
 for q in z:
  profile=headers[q['uuid']]
  for name in settings:
   assert name in profile,('missing_frozen_declared_setting',q['uuid'],name)
   if name in q:assert q[name]==profile[name],('own_vs_frozen_effective_profile_difference',q['uuid'],name)
   else:q[name]=profile[name];settings_resolution.append({'UUID':q['uuid'],'field':name,'value':profile[name],'authority':'exact frozen projected prospective-zone header','header_parent_sha256':sha(fd/'model.pkl') if q['uuid']==nq[0]['uuid'] else sha(mp)})
 def key(q):return (q['net'],q['layer'])+tuple(q[name] for name in settings)
 # Form only touching equal-profile groups. Differing-profile contact is a
 # declared conflict, including C local.25/priority125; no silent flattening.
 neighbors={q['uuid']:set() for q in z};by={q['uuid']:q for q in z};conflicts=[]
 for i,q in enumerate(z):
  for p in z[i+1:]:
   if(q['net'],q['layer'])!=(p['net'],p['layer']):continue
   if not q['zone_outline_shape'].intersects(p['zone_outline_shape']):continue
   if key(q)!=key(p):conflicts.append({'A':q['uuid'],'B':p['uuid'],'A_key':key(q),'B_key':key(p)});continue
   neighbors[q['uuid']].add(p['uuid']);neighbors[p['uuid']].add(q['uuid'])
 assert not conflicts,conflicts
 seen=set();out=[];unions=[]
 for q in z:
  if q['uuid'] in seen:continue
  todo=[q['uuid']];memberids=[]
  while todo:
   u=todo.pop()
   if u in seen:continue
   seen.add(u);memberids.append(u);todo.extend(neighbors[u]-seen)
  if len(memberids)==1:out.append(q);continue
  members=[by[u] for u in sorted(memberids)];uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/minimal-R73-R201-R195-equal-profile-union/'+ '|'.join(sorted(memberids))));merged=copy.deepcopy(members[0]);merged['uuid']=uid;merged['label']='Minimal touching equal-profile source union '+uid;merged['constituent_proposal_UUIDs']=sorted({u for a in members for u in [a['uuid']]+a.get('constituent_proposal_UUIDs',[])})
  record={'UUID':uid,'key':key(q),'members':memberids,'roles':{}}
  for role in ('shape','zone_outline_shape'):
   original_union=unary_union([a[role] for a in members]);merged[role]=canonical(original_union);record['roles'][role]={'input_union_WKB_sha256':ds(original_union),'output_WKB_sha256':ds(merged[role]),'integer_added_mm2':merged[role].difference(original_union).area,'integer_removed_mm2':original_union.difference(merged[role]).area}
  unions.append(record);out.append(merged)
 precision=[]
 for q in out:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==raw;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':ds(q[role])})
 changed=[];unchanged=[]
 for q in out:
  prior=next((p for p in base_z if p['uuid']==q['uuid']),None)
  if prior and all(q[role].wkb==prior[role].wkb for role in ('shape','zone_outline_shape')):unchanged.append(q['uuid'])
  else:changed.append({'UUID':q['uuid'],'net':q['net'],'layer':q['layer'],'physical_sha256':ds(q['shape']),'outline_sha256':ds(q['zone_outline_shape'])})
 lf=O/'minimal-delta-cutter-profile-and-union-ledger.json';put(lf,{'R201_only_In3_replacement':row,'exact_field_existing_track_delete':oldtrack,'exact_field_discrete_sha256':sha(fd/'proposed-discrete.pkl'),'exact_field_new_plane_sha256':sha(fd/'new-owned-zones.pkl'),'only_field_new_via_replay':vg,'only_field_three_track_replay':tg,'ROOT55_ROOT73_extra_unchanged_precision_roles':extra,'explicit_native_header_setting_resolution':settings_resolution,'touching_equal_all9_profile_unions_only':unions,'unchanged_owned_geometry_UUIDs':unchanged,'changed_or_added_owned_geometry_rows':changed,'different_settings_contacts_rejected':True})
 b=copy.deepcopy(b);b.update({'generated_precision_state_ledger':precision,'restored_generated_grid_UUIDs':[q['uuid'] for q in out],'joint_R73_R201_R195_minimal_ledger_file':str(lf.resolve()),'joint_R73_R201_R195_minimal_ledger_sha256':sha(lf),'root_monitor_R73_independent_contact_receipt_sha256':sha(H/'sbc-power/ROOT-R73-independent-all76-five-sources-strict-refs-r208/receipt.json'),'root_monitor_native_rotation_receipt_sha256':sha(H/'field-monitor-native-R9026-rotation-r68/receipt.json'),'root_monitor_owned_operation_file':str((H/'SAFE-native-monitor-rotation-composition-r69/owned-operation.pkl').resolve()),'root_monitor_owned_operation_sha256':sha(H/'SAFE-native-monitor-rotation-composition-r69/owned-operation.pkl'),'IO3_wider_R201_recipe_file':str(packet.resolve()),'IO3_wider_R201_recipe_sha256':sha(packet),'U10017_current_exact_native_recipe_file':str((H/'field-power/SAFE-U10017-wider-native-owned-recipe-r183/receipt.json').resolve()),'U10017_current_exact_native_recipe_sha256':sha(H/'field-power/SAFE-U10017-wider-native-owned-recipe-r183/receipt.json'),'host_all_supply_rooted':False,'root_failed_R74_CORE_source_regression_not_included':True,'inherited_ROOT42_raw_source_reference_and_PDN_gates_NOT_WAIVED':True})
 for name,value in fb.items():
  if name.startswith('U10017_reference_safe_wider_source_bypass'):b[name]=copy.deepcopy(value)
 candidate,cuts=GP.projected(g,h,out);mf=O/'model.pkl';mf.write_bytes(pickle.dumps((g,h,b,out,candidate),protocol=5));(O/'exact-U10017-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5));put(O/'receipt.json',{'verdict':'MINIMAL_POSITIVE_ROOT73_R201_R195_COMPOSITION_FROZEN_FULL_GATES_REQUIRED','model_sha256':sha(mf),'baseline_root_R73_sha256':sha(mp),'input_owned_zones':len(z),'output_owned_zones':len(out),'minimal_required_same_all9_profile_union_count':len(unions),'unchanged_owned_geometry_count':len(unchanged),'ledger_sha256':sha(lf),'field_existing_track_delete_count':1,'field_new_tracks':3,'field_new_vias':1,'no_OTHER_footprint_source_or_original_zone_definition_changes':True,'full_original_contact_all76_source_current_oldref_newUV_native_gates':'REQUIRED_AFTER_THIS_COMPOSITION','old_fill_retreats':cuts,'no_area_waiver':True,'host_all_supply_rooted':False,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)});print('R211_COMPLETE',sha(mf),sha(O/'receipt.json'),'owned',len(out),'unions',len(unions),flush=True)
if __name__=='__main__':main()
