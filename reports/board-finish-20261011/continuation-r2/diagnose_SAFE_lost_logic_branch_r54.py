"""Exact lost-root4 physical identities and owned In4 spine changes."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
from shapely.geometry import Point,box
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bp=H/'logic-two-reference-safe-return-restoration-r42/model.pkl';mp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';ar=H/'SAFE-full-root42-retention-r50/receipt.json'
assert sha(mp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'and sha(ar)=='6ee956571dc162306ed1d5bcced1cf8cb05f3c8af1fabd7c672e773a5acbd68c'
g,h,b,z,current=pickle.loads(mp.read_bytes());bg,bh,bb,bz,before=pickle.loads(bp.read_bytes());lost=json.loads(ar.read_bytes())['sources'][0]['lost_prior_source_keys'];padids={uid for kind,uid in lost if kind=='pad'};vids={uid for kind,uid in lost if kind=='via'};tids={uid for kind,uid in lost if kind=='track'}
rows={'pads':[{k:p[k]for k in('uuid','ref','num','net','x','y')}for p in h['pads']if p['uuid']in padids],'vias':[v for v in h['vias']if v['uuid']in vids],'tracks':[t for t in h['tracks']if t['uuid']in tids]};q=next(q for q in bz if q['uuid'].startswith('f0b2956a'));original=q['shape'];new=unary_union([q['shape']for q in z if C.norm(q['net'])=='/LOGIC_GND'and q['layer']=='In4.Cu']);v=next(v for v in h['vias']if v['uuid'].startswith('35f6d361'));win=Point(v['x'],v['y']).buffer(4).envelope
out=H/'SAFE-lost-logic-four-pad-branch-diagnosis-r54';assert not out.exists();out.mkdir();(out/'original-LG-In4-spine.wkb').write_bytes(original.wkb);(out/'remaining-owned-LG-In4-local.wkb').write_bytes(new.intersection(win).wkb);(out/'removed-owned-LG-spine-area.wkb').write_bytes(original.difference(new).wkb)
rows.update({'original_owned_spine_uuid':q['uuid'],'original_spine_bounds_mm':list(original.bounds),'original_spine_area_mm2':original.area,'removed_original_spine_area_mm2':original.difference(new).area,'spine_landing_via':v,'owned_shapes_near_spine':[{'uuid':p['uuid'],'net_raw':p['net'],'layer':p['layer'],'label':p.get('label'),'bounds':list(p['shape'].bounds),'actual_distance_to_original_spine_mm':p['shape'].distance(original)}for p in z if p['shape'].intersects(win)],'nearby_native_pads':[{k:p[k]for k in('uuid','ref','num','net','x','y')}for p in h['pads']if win.covers(Point(p['x'],p['y']))]})
(out/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_EXACT_FOUR_PAD_LOST_LOGIC_SOURCE_BRANCH_DIAGNOSIS','rows':rows,'model_sha256':sha(mp),'parent_model_sha256':sha(bp),'root50_failed_audit_sha256':sha(ar),'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n')
print('R54_PADS',rows['pads']);print('R54_SPINE',q['uuid'],original.bounds,original.area,'removed',original.difference(new).area,'via',v);print('R54_NEAR',[ (p['uuid'],p['net_raw'],p['layer'],p['actual_distance_to_original_spine_mm'])for p in rows['owned_shapes_near_spine']])
