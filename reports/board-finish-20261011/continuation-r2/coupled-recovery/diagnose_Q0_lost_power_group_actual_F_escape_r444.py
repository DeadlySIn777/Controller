"""Nominate a real power contact from the lost group, retaining all peer paths."""
from pathlib import Path
import pickle,json,hashlib
H=Path(__file__).resolve().parent
base=H/'Q0-actual-right-power-feed-strong-SENSE-r440-derived-constructor.py'
code=base.read_text().split('powerWithout7bb=')[0].replace('Q0-actual-right-power-feed-strong-SENSE-r440','Q0-lost-power-group-actual-F-escape-r444')
ns={'__file__':str(base),'__name__':'__main__'};exec(compile(code,str(base),'exec'),ns)
globals().update(ns)
POWER='/motherboard_do/DOA_FIELD_3V3'
powerWithout7bb={**current,'tracks':[t for t in current['tracks']if t['uuid']!='7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff']}
_,pg=K.physical(powerWithout7bb,POWER,K.hole_context(powerWithout7bb));pr=K.root(pg,'U11017','1');lost=next(xs for xs in pg if any(r['kind']=='pad'and(r['ref'],str(r['pin']))==('U10004','4')for r in xs));assert K.keys(lost).isdisjoint(K.keys(pr))
attach=unary_union([r['shape']for r in lost if r['layer']=='F.Cu']);target=unary_union([r['shape']for r in pr if r['layer']=='F.Cu'and r['kind']!='fill'])
nom=pickle.loads((H/'Q0-SENSE-In2-Q0-In3-coupled-r426/sparse-nomination.pkl').read_bytes());peer=[t for t in nom['tracks']if K.L.norm(t['net'])!=POWER];tracks.clear();chunks.clear();pathrows.clear()
fr=free(POWER,'F.Cu',refs['In1.Cu'],peer)
for name,sh in [('lost-F-contact',attach),('root-F-contact',target),('POWER-F-free-with-all-owned-signal-peers',fr),('lost-F-legal-centre-contact',attach.buffer(-.04,quad_segs=128).intersection(fr))]:(out/(name+'.wkb')).write_bytes(sh.wkb)
point=Point(229.45,159.35);local=[]
for j in trees['F.Cu'].query(point.buffer(2),predicate='intersects'):
 r=discrete['F.Cu'][int(j)]
 if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==POWER:continue
 local.append({'UUID':r['uuid'],'kind':r['kind'],'raw_net':r['net'],'ref':r.get('ref'),'pin':r.get('pin'),'point_distance_to_Cu_mm':point.distance(r['shape']),'required_center_margin_mm':req(POWER,r['net'])+.030+.105})
for v in newvias:
 if K.L.norm(v['net'])!=POWER:local.append({'UUID':v['uuid'],'kind':'new-via','raw_net':v['net'],'point_distance_to_Cu_mm':point.distance(Point(v['x'],v['y']))-.25,'required_center_margin_mm':req(POWER,v['net'])+.030+.105})
put(out/'actual-right-endpoint-nearest-foreign-Cu-ledger.json',sorted(local,key=lambda r:r['point_distance_to_Cu_mm']))
ok=route_attachments('POWER-real-lost-U10004.4-group-to-actual-retained-source-F',POWER,'F.Cu',refs['In1.Cu'],attach.buffer(-.04,quad_segs=128),target.buffer(-.02,quad_segs=128),peer)
for uid,ch in chunks.items():(out/(uid+'.segment-chunk')).write_bytes(ch)
put(out/'actual-power-contact-selector-ledger.json',{'source':['U11017','1'],'lost_pad':['U10004','4'],'lost_keys':sorted(K.keys(lost)),'lost_F_body_bounds':attach.bounds,'legal_attachment_mm2':attach.buffer(-.04,quad_segs=128).intersection(fr).area,'right_feed_reference_distance_mm':point.distance(refs['In1.Cu']),'right_feed_reference_eroded_contains':refs['In1.Cu'].buffer(-.105,quad_segs=128).covers(point),'right_feed_free_distance_mm':point.distance(fr)})
(out/'only-power-path-nomination.pkl').write_bytes(pickle.dumps({'tracks':tracks,'lost_keys':sorted(K.keys(lost))},protocol=5));put(out/'path-nominations.json',pathrows)
put(out/'receipt.json',{'verdict':'ACTUAL_LOST_POWER_F_SOURCE_PATH_NOMINATED_FULL_GATES_OPEN'if ok else'ACTUAL_LOST_POWER_F_ATTACHMENTS_INCOMPLETE','lost_group_contact_source_path_nomination':ok,'model_sha256':sha(model),'source_sha256':sha(source),'R426_all_other_tracks_held_sha256':sha(H/'Q0-SENSE-In2-Q0-In3-coupled-r426/sparse-nomination.pkl'),'new_power_track_count':len(tracks),'retained_outside_source_keys_mandatory':True,'native_jobs':0,'adopted':False});print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'power_path':ok,'tracks':len(tracks)}),flush=True)
