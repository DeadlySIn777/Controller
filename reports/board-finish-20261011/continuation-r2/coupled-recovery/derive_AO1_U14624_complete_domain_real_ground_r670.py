"""Expand the saved finite F ground constructor; exact current peers held."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;p=H/'construct_AO1_COM_U14624_actual_minimum_F_ground_bridge_r640.py';s=p.read_text();start=s.index("vp=pin(H/'AO1-R19-VREF");end=s.index('win=box(351,140,363,149)',start)+len('win=box(351,140,363,149)')
replacement="""
 rp=pin(H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658/receipt.json','faa3a4649c2bf82849f135af651653eee9ccc27dc6ce9c35c48584371f10cc12');rr=json.loads(rp.read_bytes());cp=pin(rr['after_context_file'],'94ea2f68b967fac5c78a8085291b1f46de54b2f5b29a33de12253fe8119f7c23');h=pickle.loads(cp.read_bytes());c=h
 curp=pin(P/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');cur=K.C.inventory(curp.read_bytes())[3];peerp=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/MON3-VREF-plus-exact-b177-5V-controlled-detour-NOMINEE.pkl','d35097754a50017d6d4b17d4388dbced44c63547b39fbddbcda31b8a78cf4181');retired=pickle.loads(peerp.read_bytes())['deleted_original_chunks'];existing={r['uuid']for r in h['tracks']+h['vias']};heldtracks=[];heldvias=[]
 for uid,ch in cur.items():
  if uid in retired:assert ch==retired[uid];continue
  if uid in existing or not ch.lstrip().startswith((b'(segment',b'(via')):continue
  r=K.A.G.parse(uid,ch,{})
  if r['kind']=='segment':heldtracks.append({'uuid':uid,'net':r['net'],'layer':r['layer'],'a':r['a'],'b':r['b'],'w':r['w']})
  else:heldvias.append({'uuid':uid,'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'flashed':list(K.LAYERS)})
 ph={**h,'tracks':h['tracks']+heldtracks,'vias':h['vias']+heldvias};rec,trees=K.F.build({**ph,'zones':[]});win=box(332,102,390,172)"""
s=s[:start]+replacement+s[end:]
for a,b in [('AO1-COM-actual-SOURCE-to-U14624-3-F-Cu-finite-ground-bridge-r640','AO1-COM-U14624-3-complete-domain-F-ground-current-R20-R656-r670'),('R640_COMPLETE','R670_COMPLETE'),("req=gap(r['net'])+.025+radius","req=gap(r['net'])+.025+radius+(.005 if r['kind']=='pad'else 0.)")]:
 assert s.count(a)==1;(s:=s.replace(a,b))
out=H/'construct_AO1_COM_U14624_complete_domain_F_ground_r670.generated.py';assert not out.exists();out.write_text(s)
(H/'derive-AO1-ground-complete-F-r670.json').write_text(json.dumps({'source':str(p.resolve()),'source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated':str(out.resolve()),'generated_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'new_scope':'complete AO1 F domain, exact R20/R656 peers, exact additional R753 tracks/vias, actual old source finite contact; 5um pad bound included'},indent=1)+'\n')
