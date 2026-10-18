"""Hold the two peer SOURCE_COM ground packets hard against the AO1 repair."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
OUT=H/'AO1-R20-two-ground-peer-packets-joint-new-Cu-r21'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def axis(t):return Point(t['x'],t['y'])if'd'in t else LineString([t['a'],t['b']])
def rad(t):return t['d']/2 if'd'in t else t['w']/2
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,w=None,prefix=None):
  p=Path(p);v=sha(p);assert w is None or v==w;assert prefix is None or v.startswith(prefix);pins[str(p.resolve())]=v;return p
 ar=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/receipt.json');r=json.loads(ar.read_bytes());ap=pin(r['packet_file'],'d35097754a50017d6d4b17d4388dbced44c63547b39fbddbcda31b8a78cf4181');ours=pickle.loads(ap.read_bytes());audit=pin(H/'AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20/receipt.json','8e1213a3a723bf7fd9c006183b9ba90d11e70420ea46bde4e0c268375fda8b58');a=json.loads(audit.read_bytes());mp=pin(a['host_model_file'],a['host_model_SHA256']);model=pickle.loads(mp.read_bytes());sources=[('R650',H/'AO1-COM-actual-SOURCE-to-U14623-9-B-Cu-finite-ground-bridge-r650/only-NEW-COM-B-Cu-ground-tracks-NOMINEE.pkl','148e8734'),('R652',H/'AO1-COM-actual-SOURCE-to-U14636-3-F-Cu-finite-ground-bridge-r652/only-NEW-COM-F-Cu-ground-tracks-NOMINEE.pkl','95661ff1')];peer=[];metadata=[]
 for label,path,prefix in sources:
  pp=pin(path,prefix=prefix);packet=pickle.loads(pp.read_bytes());assert isinstance(packet,dict);rows=packet['tracks'];assert not packet.get('vias',[])and not packet.get('deleted_original_chunks',{});assert all(t['w']==.2 and K.L.norm(t['net'])=='/motherboard_analog_output/AO1_COM'for t in rows);peer.extend({'packet':label,**t}for t in rows);metadata.append({'packet':label,'SHA256':sha(pp),'keys':list(packet),'tracks':len(rows),'bounds':[min(min(t['a'][0],t['b'][0])for t in rows),min(min(t['a'][1],t['b'][1])for t in rows),max(max(t['a'][0],t['b'][0])for t in rows),max(max(t['a'][1],t['b'][1])for t in rows)]})
 new=ours['tracks']+ours['vias'];assert len(new)==16;assert len({t['uuid']for t in new+peer})==len(new)+len(peer);dom=model['domains_normalized'];checks=[];bad=[]
 for t in new:
  for q in peer:
   layers=K.LAYERS if'd'in t else[t['layer']]
   if q['layer']not in layers or K.L.norm(t['net'])==K.L.norm(q['net']):continue
   distance=axis(t).distance(axis(q))-rad(t)-rad(q);required=(.15 if dom[K.L.norm(t['net'])]==dom[K.L.norm(q['net'])]else .6)+.025;row={'ours_UUID':t['uuid'],'peer_UUID':q['uuid'],'peer_packet':q['packet'],'layer':q['layer'],'ours_raw_net':t['net'],'peer_raw_net':q['net'],'true_capsular_Cu_gap_mm':distance,'required_with_planner_mm':required};checks.append(row)
   if distance<required:bad.append(row)
 put('peer-packet-input-schema-and-bounds.json',metadata);put('all-joint-new-foreign-Cu-body-pair-checks.json',checks);put('joint-new-foreign-Cu-errors.json',bad);result={'verdict':'ALL_OUR16_NEW_ITEMS_AND_EIGHT_PEER_GROUND_TRACKS_TRUE_NEW_NEW_CLEARANCE_PASS'if not bad else'JOINT_NEW_NEW_TRUE_Cu_CLEARANCE_REPAIR_REQUIRED','ours_new_items':len(new),'peer_ground_tracks':len(peer),'pair_checks':len(checks),'errors':len(bad),'minimum_true_gap_mm':min(q['true_capsular_Cu_gap_mm']for q in checks)if checks else None,'every_packet_schema_AND_sha_pinned':True,'GROUND_peers_source_contacts_old_reference_independent_audit':'OPEN with recoveryr3; this scope checks every foreign new-new pair only','native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
