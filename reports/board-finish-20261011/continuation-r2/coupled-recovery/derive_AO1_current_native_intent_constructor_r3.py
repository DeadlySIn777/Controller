"""Preserve R2 reader failure and bind current intended roles in a fresh R3."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
old=H/'construct_AO1_VREF_ONLY_NEW_current_ports_r2.py'
text=old.read_text();out=H/'AO1-VREF-ONLY-NEW-current-port-continuous-constructor-r2'
assert out.exists()and not(out/'receipt.json').exists()
(out/'reader-failure.json').write_text(json.dumps({'status':'FAILED_AFTER_CONTINUOUS_REGIONS_BEFORE_PACKET_EMISSION','reason':'Task source filename was guessed as board.kicad_pcb; exact root-supplied R753 filename is FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','only_new_path_attempt_count':len(json.loads((out/'bounded-exact-current-port-path-attempts.json').read_text())),'native_jobs':0,'adopted':False},indent=1)+'\n')
text=text.replace('AO1-VREF-ONLY-NEW-current-port-continuous-constructor-r2','AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r3').replace('AO1_R2_','AO1_R3_')
text=text.replace('import tri_route as T','import tri_route as T\nfrom verify_source import parse,children,child,atom\nfrom shapely.geometry import Polygon')
before=" free={};regions={};hard=[]"
insert=""" sourcefile=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');sourcebytes=sourcefile.read_bytes();currentnative=K.C.inventory(sourcebytes)[3]
 oldnativefile=pin(ROOT/'R155-known-reference-native-diagnostic-r157/measure/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');oldnative=K.C.inventory(oldnativefile.read_bytes())[3];currentroles=[];intentledger=[]
 for uid,ch in currentnative.items():
  if K.C.pcbtext.chunk_kind(ch)!='zone' or currentnative.get(uid)==oldnative.get(uid):continue
  a=parse(ch.decode());net=atom(a,'net');ly=atom(a,'layer');rings=[[(float(p[1]),float(p[2]))for p in child(q,'pts')[1:]]for q in children(a,'polygon')]
  if not rings or not net or ly not in K.LAYERS:continue
  shape=Polygon(rings[0],rings[1:]);assert shape.is_valid
  if shape.envelope.disjoint(win.buffer(1)):continue
  local=float(atom(child(a,'connect_pads'),'clearance'));row={'uuid':uid,'net':net,'layer':ly,'clearance_mm':local,'shape':shape,'native_chunk_SHA256':hashlib.sha256(ch).hexdigest()};currentroles.append(row);intentledger.append({k:v for k,v in row.items()if k!='shape'}|{'intended_shape':info(shape)})
 put('current-R753-overlapping-changed-owned-native-intents.json',intentledger)
 free={};regions={};hard=[]"""
assert before in text;text=text.replace(before,insert)
before="   for rule in c['rule_areas']:"
insert="""   for z in currentroles:
    if z['layer']!=ly or K.L.norm(z['net'])==net:continue
    gap=max(z['clearance_mm'],req(net,z['net']))+.025+.000005
    trackobs.append(K.Z.bounded_buffer(z['shape'].intersection(win.buffer(1)),gap+.100005));viaobs.append(K.Z.bounded_buffer(z['shape'].intersection(win.buffer(1)),gap+.255));hard.append({'net':net,'layer':ly,'kind':'CURRENT_CHANGED_OWNED_NATIVE_INTENDED_OUTLINE_HARD','UUID':z['uuid'],'other_net':z['net']})
   for rule in c['rule_areas']:"""
assert before in text;text=text.replace(before,insert)
before=" sourcefile=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/board.kicad_pcb');identity=K.A.N.SourceNets(sourcefile.read_bytes());native=K.C.inventory(sourcefile.read_bytes())[3]"
assert before in text;text=text.replace(before," identity=K.A.N.SourceNets(sourcebytes);native=currentnative")
dest=H/'construct_AO1_VREF_ONLY_NEW_native_intent_r3.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-constructor-r3-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'failure_preserved':str(out/'reader-failure.json'),'new_schema':'Exact changed current native intended zones all hard in ROI, no whole model overlay'},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
