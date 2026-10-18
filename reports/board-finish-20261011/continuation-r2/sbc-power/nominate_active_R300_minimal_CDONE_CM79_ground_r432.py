"""Active baseline only: one moved original CDONE and one ordinary LG return.

Helper ESC reservation is retained as a raw diagnostic failure, never waived.
Current Cu and all native intent outlines are bound; fills remain BEFORE only.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-minimal-CDONE-move-r425.py').read_text(encoding='utf-8')
s=s.replace('CM79-minimal-real-CDONE-move-ordinary-source-return-r425','CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r432')
a=s.index(" assert sha(BASE)");b=s.index(" source,_=",a)
s=s[:a]+''' prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());pf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(pf)==rr['packet_SHA256'];packet=pickle.loads(pf.read_bytes());actual=packet['current_Cu_and_local_native_pads'];h=packet['actual_BEFORE_model'];domain=h['domains_normalized'];beforeUIDs={z['uuid']for z in h['zones']};allq=packet['all_current_native_intents'];nativeRules=packet['all_current_native_rule_areas'];q=[z for z in allq if z['uuid']not in beforeUIDs or domain.get(L.norm(z['net']))!=domain.get(NET)];cm={'tracks':[],'vias':[]};native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());rec,trees=F.build(actual)
''' +s[b:]
# All current native rules replace any older model rule area. Helper reservation
# is tested separately, not made authority to alter native geometry.
s=s.replace("[(h['rule_areas'],False),(reserve['keepouts'],True)]","[(nativeRules,False)]")
a=s.index(" savedPath=");b=s.index(" # F transport",a)
s=s[:a]+s[b:]
a=s.index(' returns=[]');b=s.index(' def viaScreen',a)
s=s[:a]+''' returns=[]
 rv={'uuid':'31a0cdf9-98e1-5e65-8573-5a1327438cda','net':NET,'x':117.164998,'y':199.28645,'d':.5,'drill':.2,'span':K.LAYERS,'flashed':K.LAYERS,'locked':False,'mask_provenance':'PROSPECTIVE ordinary via, actual native masks OPEN'}
 assert rv['uuid']not in {v['uuid']for v in actual['vias']}
 rp=Point(rv['x'],rv['y']);ann=rp.buffer(.25,quad_segs=128).difference(rp.buffer(.1,quad_segs=128));over={ly:ann.intersection(refPlanes[ly]).area for ly in refPlanes};assert all(x>0 for x in over.values());returns.append({'via':rv,'ann':ann,'before_actual_J1_source_plane_annulus_overlap_mm2':over,'native_SOURCE_before':False})
''' +s[b:]
# Signal owned stubs may alter only original native same-domain fills inside
# their exact moved-terminal owncap. Other original/source reference masks
# are held by viaScreen and eventual all-native physical gates.
needle="   local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;cuts.append"
s=s.replace(needle,"   if r['kind']=='fill'and r['uuid']in beforeUIDs and domain.get(L.norm(r['net']))==domain.get(SIG):continue\n"+needle)
s=s.replace("vectors=sorted([(round(i*.025,6),round(j*.025,6))for i in range(-18,19)for j in range(-18,19)if 0<math.hypot(i*.025,j*.025)<=.45],key=lambda d:(math.hypot(*d),d[1],d[0]))","vectors=[(.25,-.025)]")
s=s.replace("stubObstacle=stubBody.buffer(.175005,quad_segs=64)","stubObstacle=stubBody.buffer(.275005,quad_segs=64)")
s=s.replace("'ground_return_unchanged':True","'ground_return_unchanged':False,'only_new_ground_via':rv,'all_current_native_intents_binding':rr,'helper_reservation_policy':'RAW_FAIL_RETAINED_PENDING_NARROW_SCOPE_REVIEW'")
s=s.replace("'CM79-R425-","'CM79-R432-")
# Check prospective ground return independently with actual current Cu,
# holes, native intents, SMDs and old foreign references. DC ground is not
# screened as a fast signal which must shadow itself.
a=s.index(' stubFreeSpace=')
extra=''' groundBad=[];groundOps=[];groundRawRefs=[]
 for ly in K.LAYERS:
  for j in trees[ly].query(rp.buffer(1.2),predicate='intersects'):
   r=rec[ly][int(j)];n=L.norm(r['net'])
   if n==NET or r['uuid']==uid:continue
   local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;req=max(local,gap(n))+.025
   if r['kind']=='fill'and r['uuid']in beforeUIDs and domain.get(n)==domain.get(NET):
    if rp.distance(r['shape'])-.25<req:groundOps.append({'UUID':r['uuid'],'layer':ly,'native_normal_same_domain_antipad_radius_mm':.25+local,'outline_unchanged':True})
    continue
   if rp.distance(r['shape'])-.25<req:groundBad.append({'kind':'ground_return_actual_foreign_Cu','UUID':r['uuid'],'layer':ly,'net':r['net']})
  for z in q:
   if z['layer']==ly and L.norm(z['net'])!=NET and rp.distance(z['shape'])-.25<max(gap(z['net']),z['clearance_mm'])+.025:groundBad.append({'kind':'ground_return_current_foreign_intent','UUID':z['uuid'],'layer':ly})
 for j in ht.query(rp.buffer(.6),predicate='intersects'):
  u,sh=holes[int(j)]
  if u!=uid and rp.distance(sh)-.1<.28:groundBad.append({'kind':'ground_return_drill','UUID':u})
 for j in st.query(rp.buffer(.4),predicate='intersects'):
  u,sh=smds[int(j)]
  if rp.distance(sh)-.1<.28:groundBad.append({'kind':'ground_return_SMD_drill','UUID':u})
 for j in vt.query(rp.buffer(.82),predicate='intersects'):
  u=actual['vias'][int(j)]['uuid']
  if u!=uid and rp.distance(vp[int(j)])<.815:groundBad.append({'kind':'ground_return_pitch','UUID':u})
 for rule in nativeRules:
  if rule['no_vias']and any(rp.distance(sh)<.275 for sh in L.poly(rule['outline'])):groundBad.append({'kind':'ground_return_native_rule','UUID':rule['uuid']})
 for ly in refPlanes:
  for j in mt[ly].query(rp.buffer(.525,quad_segs=128),predicate='intersects'):
   r=masks[ly][int(j)];hit=rp.buffer(.525,quad_segs=128).intersection(r['shape'])
   if hit.is_empty:continue
   sr=next((rr for ll in ('F.Cu','In2.Cu','B.Cu','In3.Cu')for rr in rec[ll]if rr['uuid']==r['UUID']),None);n=L.norm(sr['net'])if sr else None
   row={'UUID':r['UUID'],'layer':ly,'kind':r['kind'],'hit_mm2':hit.area,'own_original_signal_terminal':r['UUID']in ownTracks|{uid},'DC_ground_shadow_only':n==NET};groundRawRefs.append(row)
   if not row['own_original_signal_terminal']and not row['DC_ground_shadow_only']:groundBad.append({'kind':'ground_return_nonLG_old_source_reference_mask','UUID':r['UUID'],'layer':ly,'hit_mm2':hit.area})
 put('one-new-ground-return-current-guards-and-raw-old-reference-hits.json',{'ground_return':rv,'deficits':groundBad,'normal_native_fill_operations':groundOps,'raw_old_reference_hits':groundRawRefs,'before_actual_J1_source_annuli_mm2':over,'no_current_AFTER_SOURCE_claim':True})
 helperRaw=[]
 for rule in reserve['keepouts']:
  if SIG in exempt.get(rule['name'],set()):continue
  for sh in L.poly(rule['outline']):
   hit=LineString([[117.45,200.05],[117.7,200.025]]).buffer(.1,quad_segs=128).intersection(sh)
   if not hit.is_empty:helperRaw.append({'name':rule['name'],'owned_F_stub_overlap_mm2':hit.area,'rule_conditional_disallow_tracks_vias':True,'native_authority_applicability':'OPEN_design_intent_review'})
 put('helper-escape-reservation-raw-FAIL-preserved.json',helperRaw)
'''
s=s[:a]+extra+s[a:]
s=s.replace("  if bad:results.append(row);continue","  if bad or groundBad:row['ground_return_deficits']=groundBad;results.append(row);continue")
s=s.replace("print('R425_COMPLETE'","print('R432_COMPLETE'")
s=s.replace("'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json')","'active_R300_native_intent_binding':rr,'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json')")
s=s.replace("'ordinary90to100_return_no_D4_or_radius_waiver':True","'ordinary90to100_return_no_D4_or_radius_waiver':True,'helper_raw_FAIL_preserved_count':len(helperRaw),'one_new_ground_return_deficit_count':len(groundBad),'all49_prospective_CM_EXCLUDED':True,'ground_to_SIGNAL_stub_axis_extra_buffer_mm':.275005")
E=P/'exact-expanded-active-R300-CDONE-CM79-ground-r432.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
