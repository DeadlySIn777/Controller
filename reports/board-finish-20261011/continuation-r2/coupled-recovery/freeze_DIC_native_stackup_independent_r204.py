"""Freeze R202 successor with exact source native stackup binding only."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'audit_DIC_In2_supported_independent_r202.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r202','r204').replace('R202','R204')
needle="identity=A.N.SourceNets(source);inv=C.inventory(source);A.read(__file__)"
insert="""identity=A.N.SourceNets(source);inv=C.inventory(source);A.read(__file__)
 # Native stackup authority is the exact balanced source chunk; saved JSON
 # must match all lexical tokens, while its formatting carries no authority.
 stackproof=json.loads(A.read(H/'DI15-exact-same-plane-source-r144.json'));assert C.sha(A.read(H/'DI15-exact-same-plane-source-r144.json'))=='274e72a14d0768b0afa7dfe9ac1c72089f9c6e86b6c0918e53f67e559e9e2aa2';assert stackproof['source_parent_sha256']==C.sha(source)
 offset=source.index(b'(stackup');level=0;quoted=False;escaped=False;finish=None
 for i in range(offset,len(source)):
  ch=source[i]
  if quoted:
   if escaped:escaped=False
   elif ch==92:escaped=True
   elif ch==34:quoted=False
  elif ch==34:quoted=True
  elif ch==40:level+=1
  elif ch==41:
   level-=1
   if level==0:finish=i+1;break
 assert finish is not None;stackchunk=source[offset:finish];assert C.sha(stackchunk)==stackproof['native_stackup_chunk_sha256']=='b6a7d439873402fb9922aa64dd93191683af1ba4515e8abc5501c14d28c52100';assert source.count(stackchunk)==1
 stackfile=H.parents[1]/'controlled-geometry/stackup.json';stack=json.loads(A.read(stackfile));tokens=lambda text:re.findall(r'\"(?:\\\\.|[^\"\\\\])*\"|[()]|[^\\s()]+',text);assert tokens(stackchunk.decode())==tokens(stack['source_stackup']);copper=[q for q in stack['layers'] if q['type']=='copper'];assert [q['name'] for q in copper]==['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];assert all(q['thickness']==.035 for q in copper);assert [q['thickness'] for q in stack['layers'] if q['type'] in('core','prepreg')]==[.22,.33,.22,.33,.22]
 signallegs=[q['layer'] for q in recipe['attempts'][-1]['routes'] if L.norm(q['raw_net'])==NET];assert signallegs==['F.Cu','In2.Cu','F.Cu'];assert recipe['no_SAME_PLANE_policy_exception'];stackbinding={'exact_native_source_stackup_chunk_sha256':C.sha(stackchunk),'exact_native_chunk_occurrences':1,'saved_lexical_tokens_match':True,'actual_Cu_order':[q['name'] for q in copper],'DIC_signal_leg_layers':signallegs,'max_three_signal_leg_limit_retained':True,'F_and_In2_actual_adjacent_reference':'In1.Cu','CMD_B_actual_adjacent_reference':'In4.Cu','actual_paired_returns_required':True,'SAME_PLANE_exception_used':False,'native_refill_flash_and_SI':'OPEN'}"""
assert needle in s;s=s.replace(needle,insert)
needle2="'all_untouched_current_Cu_pad_rule_metadata_exact':True"
assert needle2 in s;s=s.replace(needle2,"'native_stackup_and_signal_leg_binding':stackbinding,"+needle2)
dst=H/'audit_DIC_In2_supported_independent_r204.py';assert not dst.exists();dst.write_text(s,newline='\n')
out=H/'freeze-DIC-native-stackup-independent-r204.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R202 remains preserved unrun. Adds exact native source stackup extraction/hash/token comparison, six actual Cu order/dielectric binding, explicit F/In2/F max3 leg and actual paired-return requirement; no geometry/contact/reference/mutual predicate changed. No native jobs or board writes.'},indent=1)+'\n');print(sha(dst.read_bytes()))
