"""Canonical scoped C1024 ordinary escape and exact one-FAULT-track ledger.

This freezes a nomination only. Full projection/source/reference/shared
contacts and all native gates must pass before board emission or adoption.
"""
from pathlib import Path
import sys,pickle,json,hashlib,copy
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import local_copper_r2 as LC
import guarded_declared_settings_projection_r58 as GP
import fast_contacts as F
from verify_source import parse,atom
O=H/'sbc-power/C1024-FAULT-preserving-full-geometry-nominee-r153'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl'
 assert sha(mp)=='729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca';g,h,b,z,c=pickle.loads(mp.read_bytes())
 rf=H/'sbc-power/C1024-manual-fault-detours-r144/receipt.json';nom=json.loads(rf.read_bytes())['rows'][0];assert not nom['errors']
 power='/CORE_1V2';fault='/fpga_core{slash}FPGA_INHIBIT_FAULT';uid='090b18c2-e356-4d70-94c8-ed7b92be4f98';deleted=next(t for t in h['tracks'] if t['uuid']==uid)
 assert deleted['net']==fault and deleted['a']==[159.04,80.302] and deleted['b']==[157.54,76.677]
 via=LC.via('C1024-FAULT-preserving-r153-positive-via',power,[158.7,79.3]);via.update(d=.5,drill=.2)
 ts=[]
 for label,raw,points in [('FAULT',fault,nom['FAULT_points_mm']),('POWER',power,nom['POWER_points_mm'])]:
  for i,(a,bb) in enumerate(zip(points,points[1:])):ts.append(LC.track('C1024-FAULT-preserving-r153-'+label+'-'+str(i),raw,'F.Cu',a,bb,.20))
 assert len(ts)==8 and ts[0]['a']==deleted['b'] and ts[4]['b']==deleted['a']
 # Preserve exact native source bytes; ownership of the one removed object
 # is reviewable independently of any all-board serialization.
 native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 _,chunks,_=C.O.C.pcbtext.split(native.read_bytes());chunk=next(ch for ch in chunks if C.O.C.pcbtext.chunk_uuid(ch)==uid);assert C.O.C.pcbtext.chunk_kind(chunk)=='segment' and atom(parse(chunk.decode()),'net')==fault
 cp=O/(uid+'.delete-original-segment-chunk');cp.write_bytes(chunk)
 # All exact later parent copper, plus separately pinned peer nominees.
 hard={**h,'vias':list(h['vias']),'tracks':[t for t in h['tracks'] if t['uuid']!=uid]};peerz=[];peerbind=[]
 for folder in ['safe-logic-five-and-fag-margin-r22','field-power/regulated-four-retained-hard-snapshot-r127','field-power/regulated-reference-safe-source-replacements-r121']:
  qf=H/folder/'proposed-zones.pkl';qs=pickle.loads(qf.read_bytes());peerz+=qs;peerbind.append({'zones_file':str(qf.resolve()),'zones_sha256':sha(qf)})
  df=H/folder/'proposed-discrete.pkl'
  if df.exists():
   dd=pickle.loads(df.read_bytes())
   for key in ('tracks','vias'):
    ids={q['uuid']:q for q in hard[key]}
    for q in dd[key]:
     if q['uuid'] in ids:assert q==ids[q['uuid']]
     else:hard[key].append(q)
   peerbind[-1].update(discrete_file=str(df.resolve()),discrete_sha256=sha(df))
 nv=[via];nt=ts;hh={**hard,'vias':hard['vias']+nv,'tracks':hard['tracks']+nt};errors=[];counts={};cuts=[]
 def check(gate,q,other,gap,required,**extra):
  counts[gate]=counts.get(gate,0)+1
  if gap<required:errors.append({'gate':gate,'UUID':q['uuid'],'other_UUID':other['uuid'],'actual_gap_mm':gap,'required_mm':required,**extra})
 for q in nv+nt:
  isvia='d' in q;raw=q['net'];pt=Point(q['x'],q['y']) if isvia else None;line=None if isvia else LineString([q['a'],q['b']]);center=pt if isvia else line;radius=q['d']/2 if isvia else q['w']/2;near=center.buffer(2);layers=h['copper_layers'] if isvia else [q['layer']]
  for p in hh['pads']:
   for layer,ps in p['layers'].items():
    for s in C.poly(ps):
     if not near.intersects(s):continue
     if isvia and p['smd']:check('hole_every_SMD',q,p,pt.distance(s)-q['drill']/2,.275,layer=layer)
     if layer in layers and p['net']!=raw:check('true_Cu_pad',q,p,center.distance(s)-radius,GP.G.gap(hh,raw,p['net'])+.025,layer=layer)
   for s in C.poly(p.get('hole') or []):
    if near.intersects(s) and (isvia or p['net']!=raw):check('every_pad_hole',q,p,center.distance(s)-(q['drill']/2 if isvia else radius),.275)
  for v in hh['vias']:
   if v['uuid']==q['uuid']:continue
   vp=Point(v['x'],v['y'])
   if not near.covers(vp):continue
   if isvia:check('hole_every_drill',q,v,pt.distance(vp)-(q['drill']+v['drill'])/2,.275)
   if v['net']!=raw:
    for layer in layers:
     if layer in v['flashed']:check('actual_annulus_Cu',q,v,center.distance(vp)-radius-v['d']/2,GP.G.gap(hh,raw,v['net'])+.025,layer=layer)
     elif not isvia:check('track_unflashed_drill',q,v,center.distance(vp)-radius-v['drill']/2,.275,layer=layer)
  for t in hh['tracks']:
   if t['uuid']==q['uuid'] or t['net']==raw or t['layer'] not in layers:continue
   if max(t['a'][0],t['b'][0])+t['w']/2+2<center.bounds[0] or min(t['a'][0],t['b'][0])-t['w']/2-2>center.bounds[2] or max(t['a'][1],t['b'][1])+t['w']/2+2<center.bounds[1] or min(t['a'][1],t['b'][1])-t['w']/2-2>center.bounds[3]:continue
   check('true_track_caps',q,t,center.distance(LineString([t['a'],t['b']]))-radius-t['w']/2,GP.G.gap(hh,raw,t['net'])+.025,layer=t['layer'])
  for plane in z+peerz:
   if plane['layer'] not in layers or plane['net']==raw or not near.intersects(plane['shape']):continue
   clear=max(GP.G.gap(hh,raw,plane['net']),float(plane.get('clearance_mm',.15)))+.025
   if center.distance(plane['shape'])-radius<clear:
    cutter=GP.bounded_buffer(center,radius+clear+.000020)
    cuts.append({'new_Cu_UUID':q['uuid'],'owned_NEW_zone_UUID':plane['uuid'],'raw_net':plane['net'],'layer':plane['layer'],'physical_removed_area_mm2':plane['shape'].intersection(cutter).area,'cutter_WKB_sha256':hashlib.sha256(cutter.wkb).hexdigest(),'declared_owned_NEW_carve_requires_source_contact_current_reference_requalification':True})
  for rule in h['rule_areas']:
   if not set(layers)&set(rule['layers']):continue
   if (isvia and rule.get('no_vias')) or (not isvia and rule.get('no_tracks')):
    for sh in C.poly(rule['outline']):
     if GP.bounded_buffer(center,radius).intersects(sh):errors.append({'gate':'native_rule_area','UUID':q['uuid'],'rule_UUID':rule['uuid']})
  if not unary_union(C.poly(h['outline'])).buffer(-.525).covers(GP.bounded_buffer(center,radius)):errors.append({'gate':'board_outline','UUID':q['uuid']})
 # Exact actual pre-existing own-net contacts beyond the removed segment.
 rec,trees=F.build(h,nets={C.norm(fault)},layers={'F.Cu'});oldbody=GP.bounded_buffer(LineString([deleted['a'],deleted['b']]),deleted['w']/2);contacts=C.contacts(rec,trees,oldbody,'F.Cu',omit=uid,tolerance=0)
 oldown=unary_union([s for zz in c['zones'] if zz['net']==power for s in C.poly(zz['fills'].get('In3.Cu',[]))]);ann=Point(via['x'],via['y']).buffer(.25,quad_segs=128).difference(Point(via['x'],via['y']).buffer(.1,quad_segs=128));overlap=ann.intersection(oldown).area
 pf=O/'proposed-discrete.pkl';pf.write_bytes(pickle.dumps({'vias':nv,'tracks':nt},protocol=5))
 delete_row={'kind':'segment','uuid':uid,'raw_net':fault,'expected_geometry':deleted,'chunk_path':str(cp.resolve()),'exact_original_chunk_sha256':sha(cp),'all_outside_shared_contacts_must_be_restored':True}
 receipt={'verdict':'PASS_SCOPED_FULL_INVENTORY_DISCRETE_NOMINEE_CONTACT_REFERENCE_SOURCE_CARVE_NATIVE_OPEN' if not errors else 'FAIL_FULL_INVENTORY_DISCRETE_NOMINEE','parent_model_file':str(mp.resolve()),'parent_model_sha256':sha(mp),'native_parent_sha256':sha(native),'delete_rows':[delete_row],'new_vias':1,'new_segments':8,'all_segments_width_mm':.20,'via_diameter_drill_mm':[.5,.2],'proposed_discrete_sha256':sha(pf),'peer_bindings':peerbind,'analytic_counts':counts,'analytic_errors':errors,'owned_NEW_plane_carve_obligations':cuts,'old_exact_FAULT_contacts':contacts,'old_FAULT_net_and_all_other_fault_Cu_preserved':True,'new_via_own_CORE1V2_In3_annular_overlap_mm2':overlap,'actual_source_L2001_2_after_full_projection':'OPEN','full_FAULT_shared_contact_reference_LOGIC_source_original198b_dc936_gates':'OPEN','native_required_new_via_flashes':['F.Cu','In3.Cu'],'all6_new_native_annuli_and_ordinary_SMD_mask_drill_gate':'OPEN','native_jobs':0,'board_written':False,'adopted':False}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('C1024_FULL_INVENTORY_NOMINEE',len(errors),'cuts',len(cuts),'contacts',len(contacts),'In3ann',overlap,sha(O/'receipt.json'),flush=True);print(errors[:5])
if __name__=='__main__':main()
