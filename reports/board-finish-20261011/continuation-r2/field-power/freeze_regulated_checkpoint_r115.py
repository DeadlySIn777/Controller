"""Freeze only a stable constructor checkpoint with exact dependent objects."""
import pathlib,json,pickle,hashlib
H=pathlib.Path(__file__).resolve().parent;P=H/'regulated-quantized-inner-source-feeds-r114'
names=['checkpoint.json','proposed-discrete.pkl','proposed-zones.pkl','owned-new-return-updates.pkl']
data={f:(P/f).read_bytes() for f in names};assert all(data[f]==(P/f).read_bytes() for f in names),'Checkpoint changed during capture; retry.'
j=json.loads(data['checkpoint.json']);z=pickle.loads(data['proposed-zones.pkl']);d=pickle.loads(data['proposed-discrete.pkl']);assert len(j['rows'])==len(z);O=H/('regulated-r114-accepted-geometry-snapshot-'+str(len(z)));assert not O.exists();O.mkdir()
for f,v in data.items():(O/f).write_bytes(v)
def sha(f):return hashlib.sha256((O/f).read_bytes()).hexdigest()
r={'verdict':'CONSTRUCTIVE_HARD_SNAPSHOT_NOT_FINAL_SOURCE_OR_CURRENT_PROOF','base_R111_model_sha256':'722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8','captured_files':{f:sha(f) for f in names},'rows':j['rows'],'new_planes':len(z),'new_vias':len(d['vias']),'new_tracks':len(d['tracks']),'return_carves':j['owned_return_carves'],'native_jobs':0,'board_written':False,'joint_source_old_contact_reference_CURRENT_native_gates':'OPEN'}
(O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');print(json.dumps({'path':str(O),'receipt':sha('receipt.json'),'new_shape_ids':[q['uuid'] for q in z],'q':sha('proposed-zones.pkl'),'d':sha('proposed-discrete.pkl'),'updates':sha('owned-new-return-updates.pkl')}))
