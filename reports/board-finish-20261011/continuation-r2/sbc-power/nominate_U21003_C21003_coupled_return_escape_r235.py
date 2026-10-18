"""Minimal capacitor translation opens the real paired return aperture.

Preserves source nets, local bypass value and every original track/via.
This is an owned geometry nomination; native/full source/reference gates follow.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
prior=P/'nominate_U21003_paired_ordinary_return_r228.py';s=prior.read_text()
s=s.replace('import hashlib,json,pickle,sys,math,traceback,uuid','import hashlib,json,pickle,sys,math,traceback,uuid,copy')
s=s.replace('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString\nfrom shapely import set_precision\nfrom shapely.affinity import translate')
s=s.replace('U21003-ordinary-source-paired-return-nominees-r228','U21003-C21003-translated-paired-return-nominees-r235').replace('U21003-paired-return-r228:','U21003-coupled-return-r235:').replace('R228_','R235_')
mark=";groups=pickle.loads((base/'groups.pkl').read_bytes())"
# The preserved R228 file uses a single explicit source-model read.
mark=" g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z);oldv="
assert mark in s
insert=""" g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z);h=copy.deepcopy(h);dx=.525;dy=0.;poses=[];bridge=[]
 for pad in h['pads']:
  if pad['ref']!='C21003':continue
  old=copy.deepcopy(pad);pad['x']=round(pad['x']+dx,6);pad['y']=round(pad['y']+dy,6);assert pad.get('hole')is None
  pad['layers']={l:GP.G.records(set_precision(translate(unary_union(C.poly(rs)),dx,dy),1e-6,mode='pointwise'))for l,rs in pad['layers'].items()}
  poses.append({'kind':'pad','UUID':pad['uuid'],'ref':'C21003','pin':pad['num'],'raw_net':pad['net'],'original':old,'replacement':copy.deepcopy(pad)})
  bridge.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'C21003-R235-own-pad-contact:'+pad['num'])),'net':pad['net'],'layer':'B.Cu','w':.3,'a':[old['x'],old['y']],'b':[pad['x'],pad['y']]})
 fp=next(q for q in h['footprints']if q['ref']=='C21003');oldfp=copy.deepcopy(fp);fp['x']=round(fp['x']+dx,6);fp['y']=round(fp['y']+dy,6);fp['courtyard']={side:GP.G.records(set_precision(translate(unary_union(C.poly(rs)),dx,dy),1e-6,mode='pointwise'))for side,rs in fp['courtyard'].items()};poses.append({'kind':'footprint','ref':'C21003','original':oldfp,'replacement':copy.deepcopy(fp),'translation_mm':[dx,dy]});assert len(poses)==3
 nom=H/'sbc-power/remaining-original-IO3-monotone-direct-source-nominees-r220';assert sha(nom/'receipt.json')=='058c220326717e0643436e9b51f41a884c337bb1578e7c270e85a02a8582647a';row=next(r for r in json.loads((nom/'receipt.json').read_text())['accepted_source_nominations']if r['ref']=='U21003');feed=[t for t in pickle.loads((nom/'proposed-tracks.pkl').read_bytes())if t['uuid']in row['new_track_UUIDs']];assert len(feed)==2
 adds=bridge+feed;assert not{t['uuid']for t in adds}&{t['uuid']for t in h['tracks']};h['tracks']+=adds;put(O/'explicit-C21003-root-translation-and-pad-contact-bridges.json',{'poses':poses,'exact_new_B_bridges':bridge,'exact_new_F_source_feed':feed,'original_tracks_vias_source_rules_changed':False,'no_CAP_value_or_net_change':True,'native_root_at_only_FP_replacement_contract_required':True});(O/'owned-cap-translation-host-checkpoint.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));(O/'new-track-objects.pkl').write_bytes(pickle.dumps(adds,protocol=5))
 oldv="""
s=s.replace(mark,insert)
# Current source c/h are not substituted by an older wholesale geometry.
# R228 uses cached R221 groups for explicit prior native-return witnesses.
tag=" put(O/'attempts.json',attempts);"
assert tag in s
s=s.replace(tag," put(O/'all-owned-cap-and-feed-operation-summary.json',{'translation_mm':[dx,dy],'exact_new_tracks':adds,'new_ground_return_nominees':accepted,'no_existing_track_or_via_removed_or_changed':True,'every_original_cap_shared_contact_and_native_parent_FP_root_AST_required':'OPEN'});"+tag)
exec(compile(s,str(__file__),'exec'))
