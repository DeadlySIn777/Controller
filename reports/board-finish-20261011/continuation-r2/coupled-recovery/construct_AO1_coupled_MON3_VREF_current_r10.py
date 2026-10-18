"""Construct real MON continuity around the R9 VREF counterfactual.

The three exact original locked MON segments are explicit controlled
replacements. No SDI/5V/other original copper is removed or relocated.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-VREF-plus-three-locked-MON-owned-detour-current-constructor-r10'
MON='/motherboard_analog_output/AO1_MON_12V';VREF='/motherboard_analog_output/AO1_VREF';COM='/motherboard_analog_output/AO1_COM'
DELS={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in parts(g)]if hasattr(s,'geoms')else[]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rr=pin(H/'AO1-MON-three-locked-segment-counterfactual-VREF-port-r9/receipt.json');r=json.loads(rr.read_bytes());assert r['selected'];pf=pin(r['packet_file'],r['packet_SHA256']);vp=pickle.loads(pf.read_bytes());assert vp['diagnostic_only_original_MON3_omitted_from_guard_context']==sorted(DELS);assert not vp['deleted_original_chunks']
 cp=pin(H/'AO1-saved-four-add-exact-current-native-screen-r1/pinned-current-local-Cu-native-before-source-only-screen.pkl','0349ddad81a9dc6dd0ef106c3a65ce03e0ff44ae3d04244e882bbe0475590a2e');ctx=pickle.loads(cp.read_bytes());local=ctx['current'];c=ctx['full_before'];win=ctx['win'];refs=ctx['source_refs'];dom=c['domains_normalized'];req=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else .6
 local={**local,'tracks':[t for t in local['tracks']if t['uuid']not in DELS]+vp['tracks'],'vias':local['vias']+vp['vias'],'zones':[]};rec,trees=K.F.build(local);ob=[];hard=[]
 for row in rec['F.Cu']:
  if K.L.norm(row['net'])==MON:continue
  gap=req(MON,row['net'])+.025+.000005;ob.append(K.Z.bounded_buffer(row['shape'],gap+.100005));hard.append({'kind':row['kind'],'UUID':row['uuid'],'raw_net':row['net']})
 for z in c['zones']:
  if K.L.norm(z['net'])==MON or req(MON,z['net'])==.15:continue
  for s in K.L.poly(z['fills'].get('F.Cu',[])):
   if not s.envelope.disjoint(win.buffer(1)):ob.append(K.Z.bounded_buffer(s.intersection(win.buffer(1)),max(z['clearance_mm'],req(MON,z['net']))+.125010));hard.append({'kind':'actual-cross-domain-F-fill','UUID':z['uuid'],'raw_net':z['net']})
 reserve,exempt=K.A.reservations()
 for rule in c['rule_areas']:
  if 'F.Cu'in rule['layers']and rule.get('no_tracks'):
   ob.extend(K.Z.bounded_buffer(s,.130)for s in K.L.poly(rule['outline'])if not s.envelope.disjoint(win.buffer(1)))
 for rule in reserve['keepouts']:
  if 'F.Cu'in rule['layers']and MON not in exempt.get(rule['name'],set()):ob.extend(K.Z.bounded_buffer(s,.130)for s in K.L.poly(rule['outline'])if not s.envelope.disjoint(win.buffer(1)))
 ob.extend(K.Z.bounded_disk(v,v['drill']/2+.375005)for v in local['vias']if K.L.norm(v['net'])!=MON)
 ob.extend(K.Z.bounded_buffer(s,.375005)for p in local['pads']for s in K.L.poly(p.get('hole')or[])if K.L.norm(p['net'])!=MON or p['npth'])
 start=[369.35,125.15];end=[374.55,130.049999];sg=next(v for v in vp['vias']if K.L.norm(v['net'])==VREF);ret=next(v for v in vp['vias']if K.L.norm(v['net'])==COM);actualsource=refs['In1.Cu'].difference(K.Z.bounded_disk(sg,.525)).difference(K.Z.bounded_disk(ret,.1));native_endpoints=[];caps=[]
 for label,at in(('start',start),('end',end)):
  own=[v for v in ctx['current_vias']if K.L.norm(v['net'])==MON and math.dist(at,[v['x'],v['y']])<.000002]
  native_endpoints.append({'label':label,'at_mm':at,'actual_existing_MON_vias':own,'own_transition_credit':'OPEN; must separately rebind real SOURCE annuli, native void and policy return'});
  for v in own:caps.append(Point(v['x'],v['y']).buffer(v['d']/2+.275,quad_segs=128))
 sourceallowed=actualsource.union(unary_union(caps));fr=win.difference(unary_union(ob)).intersection(sourceallowed.buffer(-.100005));cc=[s for s in parts(fr)if s.covers(Point(start))and s.covers(Point(end))];put('MON-exact-retained-endpoint-current-via-context.json',native_endpoints);put('MON-detour-source-guard-summary.json',{'start_supported':fr.covers(Point(start)),'end_supported':fr.covers(Point(end)),'common_components':len(cc),'free':info(fr),'no_borrowed_new_VREF_hole_cap':True});(OUT/'MON-source-and-Cu-free-centres.wkb').write_bytes(fr.wkb);paths=[];selected=None
 if cc:
  pts,search=T.route(cc[0],start,end);pts=[[round(x,6),round(y,6)]for x,y in pts]
  if len(pts)>1 and cc[0].covers(LineString(pts)):selected={'layer':'F.Cu','points_mm':pts,'width_mm':.2,'locked_yes':True,'search':search,'length_mm':LineString(pts).length}
 sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');raw=sp.read_bytes();ident=K.A.N.SourceNets(raw);native=K.C.inventory(raw)[3];deleted={u:native[u]for u in sorted(DELS)}
 for uid,ch in deleted.items():
  p=K.A.G.parse(uid,ch,{});assert p['net']==MON and p['layer']=='F.Cu'and p['w']==.2 and b'(locked yes)'in ch
 chunks=dict(vp['exact_new_chunks']);nt=list(vp['tracks']);nv=vp['vias']
 if selected:
  for a,b in zip(selected['points_mm'],selected['points_mm'][1:]):
   uid,ch=ident.serial_segment(MON,'F.Cu',a,b,.2);assert b'(locked yes)'not in ch;ch=ch.replace(b'\t\t(width 0.200000000)',b'\t\t(width 0.200000000)\n\t\t(locked yes)')if b'\t\t(width 0.200000000)'in ch else ch.replace(b'\t\t(layer ',b'\t\t(locked yes)\n\t\t(layer ');assert b'(locked yes)'in ch;chunks[uid]=ch;nt.append({'uuid':uid,'net':ident.raw(MON),'layer':'F.Cu','a':a,'b':b,'w':.2,'locked_yes':True})
 ident.assert_chunks(chunks);assert set(chunks).isdisjoint(native)
 packet=OUT/'VREF-ONLY-NEW-and-minimal-owned-locked-MON3-detour-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':nt if selected else [],'vias':nv if selected else [],'exact_new_chunks':chunks if selected else {},'deleted_original_chunks':deleted if selected else {},'MON_detour':selected,'VREF_routes':r['selected'],'final_qualification':'OPEN; current sparse candidate only, no native/current/analog/SI promotion'},protocol=5))
 ledger=[]
 for uid,ch in deleted.items():
  path=OUT/(uid+'.exact-current-before-locked-MON-chunk');path.write_bytes(ch);ledger.append({'UUID':uid,'native_before_chunk_SHA256':sha(path),'file':str(path.resolve()),'original_locked_yes':True,'only_explicit_owned_reroute':True})
 put('only-three-original-locked-MON-current-controlled-replacement-ledger.json',ledger);put('MON-detour-all-hard-current-discrete-reference-roles.json',hard)
 result={'verdict':'CONSTRUCTIVE_VREF_AND_MON3_LOCKED_ENDPOINT_PRESERVING_COUPLED_NOMINEE_ALL_GATES_OPEN'if selected else'BOUND_MON3_DETOUR_CANNOT_COMPLETE_WITH_R9_VREF_PORT_WITHIN_CURRENT_Cu_SOURCE','MON_detour':selected,'new_track_count':len(nt)if selected else 0,'new_via_count':len(nv)if selected else 0,'only_owned_original_MON3_replaced':sorted(DELS)if selected else [],'all_original_SDI_5V_and_other_Cu_preserved':True,'packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'native_jobs':0,'source_changed':False,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','MON_detour','new_track_count','new_via_count','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
