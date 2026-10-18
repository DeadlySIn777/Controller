import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,uuid,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
R=H/'U11025-exact-health-loop-ground-escape-r320';B=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';O=H/'U11025-coupled-open-pocket-ordinary-barrel-r322';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];NET='/motherboard_motors/FIELD_GND'
def main():
 assert not O.exists();O.mkdir();g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());pad=next(q for q in h['pads'] if(q['ref'],q['num'])==('U11025','2'));root=next(xs for xs in pickle.loads((B/'groups.pkl').read_bytes())[NET] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));sources={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS};rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};holes=[s for q in h['pads'] for s in C.poly(q.get('hole') or [])];hole_tree=STRtree(holes);smd=[s for q in h['pads'] if q['smd'] for rs in q['layers'].values() for s in C.poly(rs)];smd_tree=STRtree(smd);peers=pickle.loads((H/'REG7-native-support-minimal-current-delta-r312/new-REG7-zones.pkl').read_bytes());attempts=[];valid=[]
 for x in [310.2,310.15,310.25,310.1,310.3,310.0]:
  for y in [152.3,152.4,152.5,152.6,152.7,152.8,152.9,153.0]:
   point=Point(x,y);bad=[]
   for l in LAYERS:
    for i in trees[l].query(point.buffer(.88),predicate='intersects'):
     q=rec[l][int(i)]
     if q['net']==pad['net']:continue
     req=G.gap(h,pad['net'],q['net'])+.025;gap=point.distance(q['shape'])-.25
     if q['kind']=='track':t=tm[q['uuid']];gap=point.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
     elif q['kind']=='via':v=vm[q['uuid']];gap=point.distance(Point(v['x'],v['y']))-.25-v['d']/2
     if gap+1e-10<req:bad.append({'kind':'actual_'+q['kind'],'UUID':q['uuid'],'layer':l,'required_mm':req,'actual_mm':gap})
    for q in z+peers:
     if q['layer']!=l or q['net']==pad['net']:continue
     req=max(G.gap(h,pad['net'],q['net']),q.get('clearance_mm',.15))+.025;gap=point.distance(q['shape'])-.25
     if gap+1e-10<req:bad.append({'kind':'foreign_owned_or_REG_nominee_plane','UUID':q['uuid'],'layer':l,'required_mm':req,'actual_mm':gap})
   for v in h['vias']:
    gap=point.distance(Point(v['x'],v['y']))-.1-v['drill']/2
    if gap<.275+.00002:bad.append({'kind':'hole_to_actual_drilled_via','UUID':v['uuid'],'required_mm':.275+.00002,'actual_mm':gap})
   for i in hole_tree.query(point.buffer(.38),predicate='intersects'):
    gap=point.distance(holes[int(i)])-.1
    if gap<.275+.00002:bad.append({'kind':'hole_to_pad_hole','required_mm':.275+.00002,'actual_mm':gap})
   for i in smd_tree.query(point.buffer(.38),predicate='intersects'):
    gap=point.distance(smd[int(i)])-.1
    if gap<.275+.00002:bad.append({'kind':'hole_to_every_SMD','required_mm':.275+.00002,'actual_mm':gap})
   for a in h['rule_areas']:
    if not a.get('no_vias'):continue
    if any(point.buffer(.25,quad_segs=256).intersects(s) for s in C.poly(a['outline'])):bad.append({'kind':'hard_rule_area_no_vias','UUID':a.get('uuid',a.get('name'))})
   ann=point.buffer(.25,quad_segs=256).difference(point.buffer(.1,quad_segs=256));overlaps={l:ann.intersection(sources[l]).area for l in LAYERS[1:-1]};row={'site_mm':[x,y],'errors':bad,'actual_J3_source_annuli_mm2':overlaps};attempts.append(row)
   if not bad and max(overlaps.values())>.01:valid.append(row)
 chosen=min(valid,key=lambda r:Point(*r['site_mm']).distance(Point(pad['x'],pad['y']))) if valid else None;new={'tracks':[],'vias':[]}
 if chosen:
  x,y=chosen['site_mm'];via={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U11025-r322-ordinary-'+repr((x,y)))),'net':pad['net'],'x':x,'y':y,'d':.5,'drill':.2,'span':LAYERS,'flashed':LAYERS,'prospective_not_native':True};new['vias']=[via];h['vias'].append(via);c['vias'].append(via)
 (O/'proposed-incremental-discrete.pkl').write_bytes(pickle.dumps(new,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));out={'verdict':'COUPLED_OPEN_POCKET_ORDINARY_BARREL_NOMINATION_PASS_SOURCE_NATIVE_PROJECTION_OPEN' if chosen else 'COUPLED_OPEN_POCKET_ORDINARY_BARREL_SEARCH_NO_LEGAL_SITE','parent_R320_receipt_SHA256':sha(R/'receipt.json'),'parent_ROOT112_model_SHA256':sha(B/'model.pkl'),'attempts':attempts,'chosen':chosen,'new_ordinary_vias':len(new['vias']),'model_SHA256':sha(O/'model.pkl'),'incremental_discrete_SHA256':sha(O/'proposed-incremental-discrete.pkl'),'normal_native_foreign_zone_antipads_required':True,'source_contact_current_reference_native':'OPEN','board_written':False,'native_jobs':0,'adopted':False};(O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'valid':len(valid),'chosen':chosen}),flush=True)
if __name__=='__main__':main()
