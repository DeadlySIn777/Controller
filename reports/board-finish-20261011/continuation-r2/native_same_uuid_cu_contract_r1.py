"""Attest the two explicit U19008 neighbour Cu translations in native bytes.

Only one inherited LOGIC_GND via position and its sole stub end may change.
Via padstack, flash policy, raw net, UUID and all other serialized bytes stay
exact. Required actual fresh-fill annuli are exported as separate obligations.
"""
import hashlib,json,re,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
from verify_source import parse,child,atom
AUTHOR='1d012f2eb0b92b3dac83bab686c1506f1783251a19ff3536f361915f39e29003'
EXPECTED={'58446867-9078-4bf3-93c2-2c613644426e':('via','at'),'01cebc00-28c8-46b8-850d-a04411bc34af':('segment','end')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def xy(a):return [round(float(v)*1000000)for v in a[1:3]]
def native_geometry(a,r):
 assert a[0]==r['kind'] and atom(a,'uuid')==r['uuid'] and atom(a,'net')==r['raw_net']=='/LOGIC_GND'
 q=r['expected_original_geometry'] if r.get('_old') else r['expected_replacement_geometry']
 assert q['uuid']==r['uuid'] and q['net']==r['raw_net']
 iu=lambda v:round(float(v)*1000000)
 if a[0]=='via':
  assert xy(child(a,'at'))==[iu(q['x']),iu(q['y'])]
  assert iu(atom(a,'size'))==iu(q['d'])==500000 and iu(atom(a,'drill'))==iu(q['drill'])==200000
 else:
  assert xy(child(a,'start'))==list(map(iu,q['a'])) and xy(child(a,'end'))==list(map(iu,q['b']))
  assert iu(atom(a,'width'))==iu(q['w'])==200000 and atom(a,'layer')==q['layer']=='F.Cu'
def collect(rows,inventory):
 result={};pins={};flashes=[]
 if not rows:return result,pins,flashes
 assert {r['uuid']for r in rows}==set(EXPECTED) and len(rows)==2
 for r in rows:
  uid=r['uuid'];kind,field=EXPECTED[uid]
  assert uid not in result and r['kind']==kind and r['exact_native_changed_fields']==[field]
  old=Path(r['original_chunk_file']);new=Path(r['replacement_chunk_file']);author=Path(r['authorizing_recipe_file'])
  assert sha(old)==r['original_chunk_sha256'] and sha(new)==r['replacement_chunk_sha256']
  assert sha(author)==r['authorizing_recipe_sha256']==AUTHOR
  auth=json.loads(author.read_bytes());bound={q['uuid']:q for q in auth['exact_original_replacements']}
  assert uid in bound and bound[uid]['replacement_geometry']==r['expected_replacement_geometry']
  assert bound[uid]['original_chunk_sha256']==sha(old) and bound[uid]['replacement_chunk_sha256']==sha(new)
  ob=old.read_bytes();nb=new.read_bytes();assert inventory[4].get(uid)==ob
  a,b=parse(ob.decode()),parse(nb.decode());native_geometry(a,{**r,'_old':True});native_geometry(b,r)
  assert child(a,field)!=child(b,field)
  assert [n for n in a if not(isinstance(n,list)and n and n[0]==field)]==[n for n in b if not(isinstance(n,list)and n and n[0]==field)]
  pattern=rb'\('+field.encode()+rb'\s+[^()]+\)'
  oa=list(re.finditer(pattern,ob));na=list(re.finditer(pattern,nb));assert len(oa)==len(na)==1
  assert ob[:oa[0].start()]==nb[:na[0].start()] and ob[oa[0].end():]==nb[na[0].end():]
  assert r['same_existing_UUID_replacement_not_addition'] and r['every_other_AST_node_and_serialized_byte_unchanged']
  prior=xy(child(a,field));after=xy(child(b,field));assert prior==[65495000,111800000] and after==[65620000,111800000]
  if kind=='via':
   assert r['original_actual_native_flash_mask']==r['required_post_refill_retained_flash_mask']==['F.Cu','In1.Cu','In4.Cu']
   assert atom(a,'remove_unused_layers')==atom(b,'remove_unused_layers')=='yes'
   assert atom(a,'keep_end_layers')==atom(b,'keep_end_layers')=='no'
   flashes.append({'uuid':uid,'raw_net':r['raw_net'],'at_IU':after,'diameter_IU':500000,'drill_IU':200000,'required_actual_fresh_refill_flashes':r['required_post_refill_retained_flash_mask'],'original_actual_native_flashes':r['original_actual_native_flash_mask'],'no_extra_layer_credit_without_actual_native_refill':True,'same_existing_UUID_not_new_ordinary_via':True})
  result[uid]=nb
  for p in(old,new,author):pins[str(p.resolve())]=sha(p)
 return result,pins,flashes
