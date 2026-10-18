"""Exact local ordinary-hole nominations; no edits or source acceptance."""
from pathlib import Path
import sys,pickle,json,hashlib
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/C1024-fault-preserving-sites-r143'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl'
 assert sha(mp)=='729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca'
 old,h,b,z,current=pickle.loads(mp.read_bytes());win=box(151,75,167,87)
 raw='/CORE_1V2';fault='/fpga_core{slash}FPGA_INHIBIT_FAULT';uid='090b18c2-e356-4d70-94c8-ed7b92be4f98'
 t=next(q for q in h['tracks'] if q['uuid']==uid);assert t['net']==fault and t['layer']=='F.Cu' and t['w']==.2
 pads=[p for p in h['pads'] if abs(p['x']-159)<10 and abs(p['y']-81)<10]
 tracks=[q for q in h['tracks'] if LineString([q['a'],q['b']]).intersects(win.buffer(2))]
 vias=[q for q in h['vias'] if win.buffer(2).covers(Point(q['x'],q['y']))]
 local_planes=[q for q in z if q['shape'].intersects(win.buffer(2))]
 rows=[]
 for x in (158.4,158.5,158.6,158.7,158.8,158.9,159.,159.1,159.2,159.3,159.4):
  for y in (78.8,78.9,79.,79.1,79.2,79.3,79.4,79.5,79.6):
   pt=Point(x,y);errors=[];carves=[]
   for p in pads:
    for layer,ps in p['layers'].items():
     for s in C.poly(ps):
      if p['smd'] and pt.distance(s)-.1<.27500002:errors.append(('hole_SMD',p['uuid'],p['ref'],pt.distance(s)-.1))
      if p['net']!=raw and pt.distance(s)-.25<GP.G.gap(h,raw,p['net'])+.02500002:errors.append(('pad_Cu',p['uuid'],p['ref'],layer,pt.distance(s)-.25))
    for s in C.poly(p.get('hole') or []):
     if pt.distance(s)-.1<.27500002:errors.append(('pad_hole',p['uuid']))
   for v in vias:
    d=pt.distance(Point(v['x'],v['y']))
    if d-.1-v['drill']/2<.27500002:errors.append(('via_drill',v['uuid'],d-.1-v['drill']/2))
    if v['net']!=raw and d-.25-v['d']/2<GP.G.gap(h,raw,v['net'])+.02500002:errors.append(('via_Cu',v['uuid'],d-.25-v['d']/2))
   for q in tracks:
    if q['uuid']==uid or q['net']==raw:continue
    d=pt.distance(LineString([q['a'],q['b']]))-.25-q['w']/2
    if d<GP.G.gap(h,raw,q['net'])+.02500002:errors.append(('track_Cu',q['uuid'],q['net'],q['layer'],d))
   for q in local_planes:
    if q['net']==raw:continue
    clear=max(GP.G.gap(h,raw,q['net']),float(q.get('clearance_mm',.15)))+.025
    cut=GP.bounded_disk({'x':x,'y':y},.25+clear+.000020)
    if q['shape'].intersects(cut):carves.append({'zone_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'removed_area_mm2':q['shape'].intersection(cut).area})
   rows.append({'site_mm':[x,y],'errors':errors,'owned_NEW_plane_cut_obligations':carves,'one_fault_segment_removal_nominated_only':uid})
 good=[r for r in rows if not r['errors']]
 receipt={'verdict':'LOCAL_ORDINARY_VIA_NOMINATIONS_NO_PATH_OR_EDIT_ACCEPTANCE','parent_model_file':str(mp.resolve()),'parent_model_sha256':sha(mp),'candidate_fault_segment':t,'rows':rows,'ordinary_discrete_passing_sites':good,'hole_to_all_SMD_and_drills_mm':.275,'Cu_domain_gap_plus_planning_mm':.025,'additional_construction_reserve_nm':20,'full_reference_shared_fault_contacts_source_old_fill_peer_carves_native_current':'OPEN','native_jobs':0,'board_written':False}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n')
 print('C1024_FAULT_PRESERVING_ORDINARY_SITES',len(good));print(json.dumps(good,indent=1))
if __name__=='__main__':main()
