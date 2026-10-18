"""Replay only the nominated five-micrometre HOST bend from clean R262."""
import hashlib,json,pickle,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pf=H/'HOST-two-new-segment-single-bend-minimal-drill-guard-nominations-r250/proposed-two-new-HOST-track-bend.pkl';assert sha(pf)=='aca742c3f82793e7520cc7304ae7d386983013a7dea1d8973f858203ecbfa39a'
src=H/'construct_U10003_HOST_shared_field_fresh_sparse_r246.py';code=src.read_text();needle='h=copy.deepcopy(hh);h[\'tracks\']='
assert code.count(needle)==1
insert="bendfile=H/'HOST-two-new-segment-single-bend-minimal-drill-guard-nominations-r250/proposed-two-new-HOST-track-bend.pkl';assert sha(bendfile)=='aca742c3f82793e7520cc7304ae7d386983013a7dea1d8973f858203ecbfa39a';bend=pickle.loads(bendfile.read_bytes());bendby={t['uuid']:t for t in bend['replace_tracks']}\nh=copy.deepcopy(hh);h['tracks']=[copy.deepcopy(bendby.get(t['uuid'],t))for t in h['tracks']];h['tracks']="
code=code.replace(needle,insert).replace('r246','r252').replace('R246','R252');target=H/'construct_U10003_HOST_single_bend_fresh_sparse_r252.py';assert not target.exists();compile(code,str(target),'exec');target.write_text(code)
der=H/'HOST-r250-exact-bend-rebuild-derivation-r252.json';assert not der.exists();der.write_text(json.dumps({'source_file':str(src.resolve()),'source_SHA256':sha(src),'derived_SHA256':sha(target),'bend_packet_SHA256':sha(pf),'changed_only_two_NEW_HOST_track_endpoints':True,'clean_R262_full_projection_recomputed':True,'native_adoption':False},indent=1)+'\n');runpy.run_path(str(target),run_name='__main__')
mp=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/model.pkl';assert mp.is_file();src2=H/'bind_U10003_joint_raw_precision_transition_r247.py';c=src2.read_text().replace('bound-r247','bound-r253').replace('diagnostic-r246','diagnostic-r252').replace('3d8f8d53fdcf4aa557814c7ad31e76937b8264b270d012d2f077db83091b7cb4',sha(mp)).replace('R247','R253');target2=H/'bind_U10003_single_bend_raw_precision_transition_r253.py';assert not target2.exists();compile(c,str(target2),'exec');target2.write_text(c);runpy.run_path(str(target2),run_name='__main__')
