"""Freeze exact R25 nomination as a source-parent-bound discrete operation only."""
import sys,json,hashlib,pickle
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import audit_ao1_positive_operation_r4 as Q
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
def main():
 out=HERE/'c10036-coupled-wall-exact-recipe-r2.json';assert not out.exists()
 nomination_path=HERE/'c10036-coupled-wall-constructor-r1.json';r=json.loads(A.read(nomination_path));op=r['success'];assert op
 for p,pin in r['source_R25_hashes'].items():assert C.sha(Path(p).read_bytes())==pin,p
 source_path=HERE.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';raw=A.read(source_path);assert C.sha(raw)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=N.SourceNets(raw)
 g=pickle.loads(A.read(HERE.parent/'field-power/local-and-b5-return-audit-r25/discrete.pkl'));tracks={t['uuid']:t for t in g['tracks']};exact={}
 def chunk(uid):
  token=b'\n\t\t(uuid "'+uid.encode()+b'")';i=raw.index(token);assert raw.count(token)==1
  a=raw.rfind(b'\n\t(',0,i)+1;b=raw.find(b'\n\t(',i)+1
  if b==0:b=raw.rfind(b'\n)')+1
  ch=raw[a:b];assert C.pcbtext.chunk_uuid(ch)==uid and C.pcbtext.chunk_kind(ch)=='segment';return ch
 for u in r['removed_wall_UUIDs']:
  ch=chunk(u);p=G.parse(u,ch,{});t=tracks[u];assert p['kind']=='segment' and p['net']==S.norm(t['net']) and p['layer']==t['layer'] and p['w']==t['w'] and tuple(p['a'])==tuple(t['a']) and tuple(p['b'])==tuple(t['b']);exact[u]=ch.decode()
 new={};items=[]
 for label,net,key in [('C10036-ground','/motherboard_do/FIELD_B_0V','ground_route'),('DO12-gate','/motherboard_do/DO12_RCB_GATE','gate_route')]:
  route=op[key]
  for a,b in zip(route['points'],route['points'][1:]):
   u,ch=identity.serial_segment(net,'F.Cu',a,b,.2);assert u not in tracks;new[u]=ch.decode();items.append({'uuid':u,'kind':'segment','raw_net':identity.raw(net),'layer':'F.Cu','a':a,'b':b,'width_mm':.2,'role':label})
 u,ch=Q.serial_via(identity,'/motherboard_do/FIELD_B_0V',op['ground_via_at_mm']);assert all(v['uuid']!=u for v in g['vias']);new[u]=ch.decode();items.append({'uuid':u,'kind':'via','raw_net':identity.raw('/motherboard_do/FIELD_B_0V'),'at_mm':op['ground_via_at_mm'],'diameter_mm':.5,'drill_mm':.2,'role':'C10036-source-rooted-ground'})
 identity.assert_chunks({u:ch.encode() for u,ch in new.items()});policies={S.norm(n):q for n,q in json.loads(A.read(S.CONTROLLED))['nets'].items()};policy=policies.get('/motherboard_do/DO12_RCB_GATE');assert policy is None or policy.get('class')=='NONE'
 fresh=HERE.parent/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert C.sha(A.read(fresh))=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 report={'schema':'C10036-DO12-coupled-exact-source-operation-r2','verdict':'EXACT_FIVE_DELETE_FIVE_ADD_RECIPE_INDEPENDENT_AUDIT_PENDING','source_parent':str(source_path),'source_parent_sha256':C.sha(raw),'source_fresh_netlist':str(fresh),'source_fresh_netlist_sha256':C.sha(fresh.read_bytes()),'source_R25_nomination':str(nomination_path),'source_R25_nomination_sha256':C.sha(nomination_path.read_bytes()),'source_R25_bound_inputs':r['source_R25_hashes'],'exact_removed_chunks':exact,'exact_new_chunks':new,'removed_source_UUIDs':sorted(exact),'new_items':items,'source_root':'J11005.2','ground_pad_native_UUID':r['ground_pad_native_uuid'],'source_actual_gate_policy':policy,'normalized_raw_name_collisions':0,'proposed_zones':0,'footprint_changes':0,'all_native_refill_DRC_current_r06_r07_no_loss_reference_and_final_mutual_composition':'OPEN','board_emitted':False,'native_jobs':0,'gpu_jobs':0,'read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'sha256':C.sha(out.read_bytes()),'deletes':len(exact),'adds':len(new)}),flush=True)
if __name__=='__main__':main()
