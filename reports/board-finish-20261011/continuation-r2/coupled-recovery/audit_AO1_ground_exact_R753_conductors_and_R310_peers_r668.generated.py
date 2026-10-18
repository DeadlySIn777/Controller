"""Exact sparse current R753 conductor guard, including root's R310 peer."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
COM='/motherboard_analog_output/AO1_COM';OUT=H/'AO1-seven-ground-exact-R753-conductor-and-R310-peer-guard-r668'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def axis(t):return Point(t['x'],t['y'])if'd'in t else LineString([t['a'],t['b']])
def rad(t):return t['d']/2 if'd'in t else t['w']/2
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 gf=pin(H/'AO1-COM-seven-only-NEW-ground-tracks-local-inside-margin-repair-and-widths-r656/only-seven-NEW-COM-ground-tracks-inside-margin-repaired-widths-NOMINEE.pkl','cb36851a8df37c5e197cea6c8a4de7720ed7e8ec19543ba9a03a5c3b17f1b1b3');ground=pickle.loads(gf.read_bytes());pf=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/MON3-VREF-plus-exact-b177-5V-controlled-detour-NOMINEE.pkl','d35097754a50017d6d4b17d4388dbced44c63547b39fbddbcda31b8a78cf4181');peer=pickle.loads(pf.read_bytes());mp=pin(H/'AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20/AO1-only-sparse-prospective-normal-native-antipad-host-model.pkl','3605d85bb9c672bb2d8dc58b3a6d2c01b01c2e3412978c9941846ee5ad415b72');dom=pickle.loads(mp.read_bytes())['domains_normalized'];sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');chunks=K.C.inventory(sp.read_bytes())[3];con=[];retired=[]
 for uid,ch in chunks.items():
  if uid in peer['deleted_original_chunks']:
   assert ch==peer['deleted_original_chunks'][uid];retired.append(uid);continue
  if ch.lstrip().startswith((b'(segment',b'(via')):con.append((uid,ch,'retained_exact_R753'))
 assert len(retired)==4
 for uid,ch in peer['exact_new_chunks'].items():con.append((uid,ch,'exact_AO1_R19_peer_NEW'))
 rootp=pin(ROOT/'short-ESD-ground-and-watchdog-exact-current-native-add-only-r310/minimal-exact-ground-watchdog-native-add-manifest.json');root=json.loads(rootp.read_bytes());assert root['baseline_SHA256']==sha(sp)
 for op in root['operations']:
  assert op['action']=='add'and op['kind']=='segment';p=pin(op['file'],op['SHA256']);con.append((op['UUID'],p.read_bytes(),'R310_root_NEW_peer'))
 rows=[];hole=[]
 for uid,ch,origin in con:
  q=K.A.G.parse(uid,ch,{})
  if q['kind']=='segment':t={'uuid':uid,'net':q['net'],'layer':q['layer'],'a':q['a'],'b':q['b'],'w':q['w']};layers=[t['layer']]
  else:t={'uuid':uid,'net':q['net'],'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill']};layers=K.LAYERS;hole.append({'t':t,'axis':axis(t),'origin':origin})
  for ly in layers:rows.append({'t':t,'layer':ly,'axis':axis(t),'origin':origin})
 trees={ly:STRtree([r['axis'].buffer(rad(r['t']))for r in rows if r['layer']==ly])for ly in K.LAYERS};byly={ly:[r for r in rows if r['layer']==ly]for ly in K.LAYERS};ht=STRtree([r['axis'].buffer(r['t']['drill']/2)for r in hole]);checks=[];bad=[]
 for t in ground['tracks']:
  ax=axis(t);body=ax.buffer(rad(t));ly=t['layer']
  for i in trees[ly].query(body.buffer(1),predicate='intersects'):
   row=byly[ly][int(i)];q=row['t'];n=K.L.norm(q['net'])
   if n==COM:continue
   assert n in dom,n;req=(.15 if dom[n]==dom[COM]else .6)+.025;g=ax.distance(row['axis'])-rad(t)-rad(q);v={'kind':'current_exact_true_capsular_Cu','ground_UUID':t['uuid'],'other_UUID':q['uuid'],'net':q['net'],'origin':row['origin'],'true_gap_mm':g,'required_mm':req};checks.append(v)
   if g<req:bad.append(v)
  for i in ht.query(body.buffer(1),predicate='intersects'):
   row=hole[int(i)];q=row['t']
   if K.L.norm(q['net'])==COM:continue
   g=ax.distance(row['axis'])-rad(t)-q['drill']/2;v={'kind':'current_exact_via_hole','ground_UUID':t['uuid'],'other_UUID':q['uuid'],'origin':row['origin'],'true_gap_mm':g,'required_mm':.275};checks.append(v)
   if g<.275:bad.append(v)
 (OUT/'all-current-conductor-and-hole-checks.json').write_text(json.dumps(checks,indent=1)+'\n');(OUT/'raw-current-geometry-errors.json').write_text(json.dumps(bad,indent=1)+'\n')
 r={'verdict':'EXACT_R753_RETAINED_AND_SPARSE_AO1_R310_PEER_CONDUCTOR_GUARD_PASS'if not bad else'RAW_EXACT_CURRENT_CONDUCTOR_GUARD_FAIL','input_SHA256':pins,'controlled_retired_R753_UUIDs_ONLY_from_exact_AO1_peer':retired,'retained_R753_and_exact_NEW_peer_segment_via_records':len(con),'GROUND_tracks':7,'foreign_analytic_checks':len(checks),'geometry_errors':len(bad),'after_current_dict_not_overlaid':True,'pads_planes_rules_source_refs':'separate_R658_scope_plus_NATIVE_AFTER_gate','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n')
 for p,s in pins.items():assert sha(p)==s,p
 print('R668_COMPLETE',sha(OUT/'receipt.json'),r['verdict'],'checks',len(checks),'errors',len(bad),flush=True)
if __name__=='__main__':main()
