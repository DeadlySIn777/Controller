"""Read-only exact new-path owner and original CORE wall source contacts."""
import sys,json,pickle,time
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
K=N.K;L=N.L;sha=N.sha
OUT=P/'CM-alternate-pose-only-new-ground-blocker-and-original-CORE233-binding-r447'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();e=P/'CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443/only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl';assert sha(e)=='7de6002db2fafc160769b86c6288a1184075051929dda14823e9d02ab3627bef';extra=pickle.loads(e.read_bytes());u='65f3a90e-a953-5caa-8493-4623cfc05f2f';owner=next(r for r in extra['new_DC_routes']if any(t['uuid']==u for t in r['tracks']));put('exact-ONLY_NEW-ground-blocker-owner-and-path.json',owner)
    bf=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-model.pkl';gf=bf.with_name('actual-full-R157-before-all-net-groups.pkl');assert sha(bf)=='dbeba66691d45ee12206f77e5060b4c845681014d19b3d9e633e9aed08a2b0c2';assert sha(gf)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a';before=pickle.loads(bf.read_bytes());groups=pickle.loads(gf.read_bytes());net='/mc_local_power/CORE_5V';assert isinstance(groups,dict)and net in groups;gg=groups[net];root=K.root(gg,'R11022','2');uid='233cfa24-bc17-4dfa-9617-321c8db03618';t=next(t for t in before['tracks']if t['uuid']==uid);assert t['layer']=='F.Cu'and t['w']==1.25 and t['a']==[148.65,90.65]and t['b']==[154.65,96.65];body=LineString([t['a'],t['b']]).buffer(.625,quad_segs=128);rec,trees=F.build(before,nets={net},layers={'F.Cu'});contacts=[]
    for jj in trees['F.Cu'].query(body.buffer(.000002),predicate='intersects'):
        r=rec['F.Cu'][int(jj)]
        if r['uuid']==uid or body.distance(r['shape'])>.000002:continue
        contact={k:r[k]for k in ('kind','uuid','net','ref','pin','layer')if k in r};contact['finite_body_overlap_mm2']=body.intersection(r['shape']).area;contact['distance_mm']=body.distance(r['shape']);contact['SOURCE_before']=('track',r['uuid'],'F.Cu')in K.keys(root)if r['kind']=='track'else any(x['uuid']==r['uuid']and x['layer']=='F.Cu'for x in root)
        if r['kind']=='track':contact['exact_current_native_original_geometry']=r['source']
        contacts.append(contact)
    membership=next(g for g in gg if any(r['kind']=='track'and r['uuid']==uid for r in g));scope={'original_segment':t,'actual_BEFORE_source_root_selector':['R11022','2'],'segment_is_actual_BEFORE_SOURCE':('track',uid,'F.Cu')in K.keys(root),'segment_group_discrete_layer_keys':len(K.keys(membership)),'SOURCE_before_layer_keys':len(K.keys(root)),'direct_same_net_native_F_contacts':contacts,'native_source_and_Cu_or_width_lock_edits':0,'candidate_CORE_wall_reroute':'NONE; current scope read-only contact/source binding','current_full_after_SOURCE_native_current':'OPEN'};put('original-CORE233-actual-BEFORE-SOURCE-direct-native-contact-scope.json',scope);put('receipt.json',{'status':'EXACT_ONLY_NEW_GROUND_OWNER_ORIGINAL_CORE233_SOURCE_CONTACT_BINDING_READ_ONLY','ONLY_NEW_ground_blocker_UUID':u,'ground_owner':[owner['ref'],owner['pin']],'original_CORE233_is_actual_BEFORE_SOURCE':scope['segment_is_actual_BEFORE_SOURCE'],'original_CORE233_same_net_F_contact_count':len(contacts),'R763_before_model_SHA256':sha(bf),'R763_allnetgroups_SHA256':sha(gf),'native_jobs_or_model_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R447_COMPLETE',sha(OUT/'receipt.json'),owner,scope,flush=True)
if __name__=='__main__':main()
