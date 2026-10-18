"""Pin exactly three native protected stubs and four new FIELD5 segments."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely.geometry import LineString
import contact_layout as C
import fast_contacts as F
from inventory import sha
from verify_source import parse,atom,child
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'));import guarded_power_projection_r44 as P
O=H/'u11017-dead-spur-native-owned-recipe-r138'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();rp=H/'u11017-dead-spur-local-join-nominee-r132';assert sha(rp/'receipt.json')=='8e50d383a5d99468901f09c40c7e9e3e9487d7c71b3d26d5ad58790b1b534906';old=pickle.loads((rp/'exact-old-owned-track-records.pkl').read_bytes());tracks=pickle.loads((rp/'proposed-tracks.pkl').read_bytes());assert len(old)==3 and len(tracks)==4;board=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';_,chunks,_=C.O.C.pcbtext.split(board.read_bytes());byid={C.O.C.pcbtext.chunk_uuid(c):c for c in chunks if C.O.C.pcbtext.chunk_uuid(c)};deletes=[];adds=[]
 for t in old:
  ch=byid[t['uuid']];assert C.O.C.pcbtext.chunk_kind(ch)=='segment';ast=parse(ch.decode());assert atom(ast,'net')==t['net'] and atom(ast,'layer')==t['layer'];assert [float(v) for v in child(ast,'start')[1:]]==t['a'] and [float(v) for v in child(ast,'end')[1:]]==t['b'] and float(atom(ast,'width'))==t['w'];path=O/(t['uuid']+'.delete-original-segment-chunk');path.write_bytes(ch);deletes.append({'kind':'segment','uuid':t['uuid'],'raw_net':t['net'],'chunk_path':str(path.resolve()),'exact_original_chunk_sha256':sha(path),'expected_geometry':t})
 for t in tracks:
  assert t['uuid'] not in byid and t['w']==.25 and t['net']=='/motherboard_power_entry{slash}FIELD_5V';text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*t['a'],*t['b'],t['w'],t['layer'],t['net'],t['uuid']);ch=text.encode();assert C.O.C.pcbtext.chunk_uuid(ch)==t['uuid'] and atom(parse(text),'net')==t['net'];path=O/(t['uuid']+'.segment-chunk');path.write_bytes(ch);adds.append({'kind':'segment','uuid':t['uuid'],'raw_net':t['net'],'geometry':t,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 _,h,_,_,_=pickle.loads((H/'safe-root22-regulated-source-contact-audit-r130/model.pkl').read_bytes());rec,trees=F.build({**h,'zones':[]},layers={'F.Cu'});removed={t['uuid'] for t in old};outside=[]
 for t in old:
  body=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);contacts=[]
  for idx in trees['F.Cu'].query(body,predicate='intersects'):
   a=rec['F.Cu'][int(idx)]
   if a['uuid'] in removed or a['net']!=t['net']:continue
   contacts.append({'kind':a['kind'],'uuid':a['uuid'],'raw_net':a['net'],'ref':a.get('ref'),'pin':a.get('pin'),'body_overlap_mm2':body.intersection(a['shape']).area})
  outside.append({'removed_original_segment':t['uuid'],'distinct_retained_contacts':contacts})
 write(O/'exact-outside-contact-ledger.json',outside);(O/'proposed-tracks.pkl').write_bytes((rp/'proposed-tracks.pkl').read_bytes());source=H/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';write(O/'remove-only-recipe.json',{'native_base_board':str(board.resolve()),'native_base_board_sha256':sha(board),'delete_rows':deletes,'add_rows':[],'scope':'Only explicit obsolete native U11017 protected source stubs; retained outside contacts mandatory'});write(O/'receipt.json',{'verdict':'FROZEN_U11017_3_DELETE_4_ADD_RECIPE_FULL_CONTACT_REFERENCE_CURRENT_NATIVE_PENDING','native_base_board':str(board.resolve()),'native_base_board_sha256':sha(board),'fresh_native_source_export_sha256':sha(source),'R132_nominee_receipt_sha256':sha(rp/'receipt.json'),'delete_rows':deletes,'add_rows':adds,'exact_removed_original_segments':3,'new_segments':4,'new_vias':0,'new_zones':0,'proposed_tracks_sha256':sha(O/'proposed-tracks.pkl'),'outside_contact_ledger_sha256':sha(O/'exact-outside-contact-ledger.json'),'remove_only_recipe_sha256':sha(O/'remove-only-recipe.json'),'actual_source_same_raw_pins':['U11017.8','U11017.5'],'full_source_native_contact_aperture_reference_current_guards':'MANDATORY_OPEN','all_unowned_original_chunks_unchanged_by_recipe':True,'raw_aliases_introduced':False,'native_jobs':0,'board_written':False});print('R138',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
