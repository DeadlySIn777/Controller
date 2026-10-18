"""Fresh exact AO1_COM source/port binding for ENABLE and DAC-CS only."""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import R157_native_selected_actual_conversion_r673 as N
from shapely.ops import unary_union
OUT=H/'AO1-COM-actual-full-native-current-source-and-two-residual-port-binding-r622';COM='/motherboard_analog_output/AO1_COM';NETS=['/motherboard_analog_output/AO1_ENABLE_ISOLATED','/motherboard_analog_output/AO1_DAC_CS_N']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inf(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or v==s;pins[str(p.resolve())]=s;return p
 bp=pin(P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl','ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4');_,nh,_,_,nc=pickle.loads(bp.read_bytes());N.assert_R157_actual_before();gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');mf=pin(N.R157/'actual-full-refill-via-flashes.json','b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1');np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');ng=json.loads(gf.read_bytes());masks=json.loads(mf.read_bytes())['vias'];actual,ctx,ledger=N.convert_selected_actual(nh,nc,ng,masks,{COM},np);groups=K.physical(actual,COM,ctx)[1];root=K.root(groups,'U14619','7');assert any(r['kind']=='pad'and r['uuid']=='ba8a438e-2bdd-4f29-9cf0-fe1f66d3471e'for r in root);native_refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());cc=K.hole_context(c);current_groups=K.physical(c,COM,cc)[1];current_root=K.root(current_groups,'U14619','7');current_refs={ly:unary_union([r['shape']for r in current_root if r['kind']=='fill'and r['layer']==ly])for ly in native_refs};refs={ly:current_refs[ly].intersection(native_refs[ly])for ly in native_refs};ports={};bindings=[]
 for net in NETS:
  gs=K.physical(c,net,cc)[1];ports[net]=gs;pr=[]
  for group in gs:
   pads=[]
   for r in group:
    if r['kind']!='pad':continue
    p=next(p for p in h['pads']if p['uuid']==r['uuid']);n=next(p for p in ng['pads']if p['ref']==p['ref']and False)if False else None
    options=[n for n in ng['pads']if (n['ref'],str(n['num']),n['net'],n['at'])==(p['ref'],str(p['num']),p['net'],[p['x'],p['y']])];assert len(options)==1,(p['ref'],p['num']);row={'ref':p['ref'],'pin':str(p['num']),'UUID':p['uuid'],'at_mm':[p['x'],p['y']],'actual_native_layers':options[0]['layers']}
    if row not in pads:pads.append(row)
   if pads:pr.append(pads)
  bindings.append({'net':net,'current_host_pad_groups':pr,'all_endpoints_exact_actual_native_R157_pose_raw_net':True})
 vp=pin(H/'AO1-R19-VREF-only-four-chunk-current-requalification-handoff-r616/saved-VREF-only-add-stencil.json','4263f3b08ca71eda5c332bd62e759eb8f67c740da238bd33b0d6f918fba88eef');vr=json.loads(vp.read_bytes());peers=[]
 for uid,r in vr['exact_new_chunks'].items():
  p=pin(r['file'],r['SHA256']);parsed=K.A.G.parse(uid,p.read_bytes(),{});peers.append(parsed)
 f=OUT/'exact_actual_current_AO1_COM_source_and_ports_NOMINATION_ONLY.pkl';f.write_bytes(pickle.dumps({'native_root':root,'current_root':current_root,'native_refs':native_refs,'current_refs':current_refs,'references':refs,'port_groups':ports,'VREF_four_hard_peer_items':peers,'actual_pad_binding':ledger},protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'AO1_COM_ACTUAL_FULL_NATIVE_AND_CURRENT_SOURCE_TWO_RESIDUAL_PORTS_BOUND_NOMINATION_ONLY','input_SHA256':pins,'source_selector':['U14619','7','ba8a438e-2bdd-4f29-9cf0-fe1f66d3471e'],'native_source_nonfill_keys':len(K.keys(root)),'current_source_nonfill_keys':len(K.keys(current_root)),'reference_regions':{ly:inf(s)for ly,s in refs.items()},'two_original_residual_ports':bindings,'VREF_hard_peer_chunk_count':len(peers),'cached_source_port_file':str(f.resolve()),'cached_source_port_SHA256':sha(f),'native_jobs':0,'board_written':False,'adopted':False,'current_after_drilled_contacts_reference_current_native_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R622_COMPLETE',sha(OUT/'receipt.json'),len(K.keys(root)),flush=True)
if __name__=='__main__':main()
