"""Validate only an explicitly authorized R17031 root translation.

Local pad, text, courtyard, source identity and all other AST nodes stay exact.
No native board is loaded, edited or saved here.
"""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
from verify_source import parse,child,atom
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def collect(rows,inventory):
 result={};pins={};poses=[];masks=[]
 for r in rows:
  uid=r['uuid'];assert uid not in result and r['ref']=='R17031'
  old=Path(r['original_chunk_file']);new=Path(r['replacement_chunk_file']);author=Path(r['authorizing_recipe_file'])
  assert sha(old)==r['original_chunk_sha256'] and sha(new)==r['replacement_chunk_sha256'] and sha(author)==r['authorizing_recipe_sha256']
  ob=old.read_bytes();nb=new.read_bytes();assert inventory[3].get(uid)==ob
  a,b=parse(ob.decode()),parse(nb.decode());assert a[0]==b[0]=='footprint' and atom(a,'uuid')==atom(b,'uuid')==uid
  assert child(a,'at')!=child(b,'at') and atom(a,'layer')==atom(b,'layer')=='F.Cu'
  assert [n for n in a if not(isinstance(n,list)and n and n[0]=='at')]==[n for n in b if not(isinstance(n,list)and n and n[0]=='at')]
  prior=[float(x)for x in child(a,'at')[1:]];later=[float(x)for x in child(b,'at')[1:]]
  assert len(prior)==len(later)==3 and prior[2]==later[2]==0
  assert prior==r['original_root_pose_mm_deg'] and later==r['replacement_root_pose_mm_deg']
  ref=next(n for n in a if isinstance(n,list)and n[:2]==['property','Reference']);assert ref[2]=='R17031'
  pose=r['native_pose_row'];mask=r['native_mask_and_text_row']
  assert pose['ref']==mask['ref']=='R17031' and pose['native_footprint_uuid']==uid and pose['root_pose_mm_deg']==later and pose['layer']=='F.Cu'
  assert pose['chunk_sha256']==sha(new) and Path(pose['chunk_path']).resolve()==new.resolve()
  assert {x['pad_uuid']for x in pose['pads']}=={x['physical_pad_UUID']for x in mask['pads']}
  assert all(x['actual_original_clone_native_flashes']==['F.Cu']for x in pose['pads'])
  result[uid]=nb;poses.append(pose);masks.append(mask)
  for p in(old,new,author):pins[str(p.resolve())]=sha(p)
 assert len(result)<=1
 return result,pins,poses,masks
