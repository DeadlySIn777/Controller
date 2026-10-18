"""Read exact native stackup chunk, compare lexical tokens, preserve R142 failure."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'check_DI15_exact_same_plane_source_r142.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r142','r144').replace('R142','R144')
s=s.replace('import sys,json,pickle,time,math','import sys,json,pickle,time,math,re')
old="stackchunk=stack['source_stackup'].encode();assert source.count(stackchunk)==1"
new="""savedstack=stack['source_stackup'];offset=source.index(b'(stackup');level=0;quoted=False;escaped=False;finish=None
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
 assert finish is not None;stackchunk=source[offset:finish];tokens=lambda text:re.findall(r'\"(?:\\\\.|[^\"\\\\])*\"|[()]|[^\\s()]+',text);assert tokens(stackchunk.decode())==tokens(savedstack);assert source.count(stackchunk)==1"""
assert old in s;s=s.replace(old,new)
s=s.replace("'native_stackup_exact_serialized_parent_occurrences':1","'native_stackup_exact_serialized_parent_occurrences':1,'saved_native_stackup_lexical_tokens_identical':True,'saved_stackup_format_is_not_raw_native_authority':True")
dst=H/'check_DI15_exact_same_plane_source_r144.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI15-same-plane-native-stackup-r144.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R142 stopped at saved serialized stackup formatting comparison. R144 extracts exact balanced native source chunk, binds its exact raw hash, and requires complete lexical token equality to frozen saved stackup. No geometric predicate or policy changed.'},indent=1)+'\n');print(sha(dst.read_bytes()))
