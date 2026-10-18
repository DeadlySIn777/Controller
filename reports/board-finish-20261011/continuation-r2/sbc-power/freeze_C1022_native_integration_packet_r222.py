"""Exact single additive C1022 feed and local physical node obligations."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import LineString
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
from verify_source import parse,atom
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/C1022-validated-native-integration-packet-r222'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(sh):return hashlib.sha256(sh.wkb).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin) for q in xs))
def main():
 assert not O.exists();O.mkdir();a=H/'sbc-power/C1022-zero-gap-source-feed-independent-r221';assert sha(a/'receipt.json')=='5e0cfb2c202c7551155d46f14b01e1c33b4f255a806c641016a5c1d8ba6dbf32';assert sha(a/'model.pkl')=='261f92035b05f1346bc805d43df3f7b67a2c0c638892ee43c01856d57196182a'
 g,h,b,z,c=pickle.loads((a/'model.pkl').read_bytes());base=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(base/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';bg,bh,bb,bz,bc=pickle.loads((base/'model.pkl').read_bytes());assert g==bg
 tracks=pickle.loads((a/'proposed-tracks.pkl').read_bytes());assert len(tracks)==1;t=tracks[0];assert t['uuid']=='952d1350-fb0a-5422-b8b6-c2ee31a55c2d';assert h['pads']==bh['pads'] and h['vias']==bh['vias'] and h['footprints']==bh['footprints'];assert h['tracks']==bh['tracks']+[t]
 native=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 assert t['uuid'] not in native.read_text(encoding='utf-8')
 chunk='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*t['a'],*t['b'],t['w'],json.dumps(t['layer']),json.dumps(t['net']),json.dumps(t['uuid']))
 ast=parse(chunk);assert atom(ast,'net')==t['net'] and atom(ast,'uuid')==t['uuid'] and atom(ast,'layer')==t['layer'];cf=O/(t['uuid']+'.segment-chunk');cf.write_text(chunk,encoding='utf-8',newline='')
 groups=pickle.loads((a/'groups.pkl').read_bytes());oldgroups=pickle.loads((base/'groups.pkl').read_bytes());io=root(groups['/IO_3V3'],'R18001','2');oldio=root(oldgroups['/IO_3V3'],'R18001','2');lg=root(groups['/LOGIC_GND'],'J11001','2');pad1=next(p for p in h['pads'] if(p['ref'],p['num'])==('C1022','1'));pad2=next(p for p in h['pads'] if(p['ref'],p['num'])==('C1022','2'));port=next(p for p in h['pads'] if p['uuid']=='9b93b76a-9a4b-4062-bbf3-37dbcacaed42');assert pad1['net']==port['net']==t['net'] and pad2['net']=='/LOGIC_GND'
 actual={q['uuid'] for q in io if q['kind']=='pad'};grounds={q['uuid'] for q in lg if q['kind']=='pad'};assert pad1['uuid'] in actual and port['uuid'] in actual;gndrooted=pad2['uuid'] in grounds
 old_count=len({q['uuid'] for q in oldio if q['kind']=='pad'and q['pin']});new_count=len({q['uuid'] for q in io if q['kind']=='pad'and q['pin']});assert(old_count,new_count)==(593,594)
 body=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);bf=O/'exact-new-track-full-reference-body.wkb';bf.write_bytes(body.wkb)
 changes=[];prior={q['uuid']:q for q in bz};newq=[]
 for q in z:
  p=prior[q['uuid']]
  if all(q[role].wkb==p[role].wkb for role in ('shape','zone_outline_shape')):continue
  row={'UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'roles':{}}
  for role in ('shape','zone_outline_shape'):row['roles'][role]={'exact_old_WKB_sha256':digest(p[role]),'exact_new_WKB_sha256':digest(q[role])}
  changes.append(row);newq.append(q)
 qf=O/'exact-owned-zone-deltas.pkl';qf.write_bytes(pickle.dumps(newq,protocol=5));df=O/'exact-additive-discrete.pkl';df.write_bytes(pickle.dumps({'tracks':tracks,'vias':[]},protocol=5))
 local={'positive_R214_parent_sha256':sha(base/'model.pkl'),'C1022_1_exact_pad':pad1,'C1022_2_exact_pad':pad2,'actual_existing_source_landing_pad':port,'actual_IO3_source':'R18001.2','actual_GND_source':'J11001.2','C1022_1_actual_source_joined':True,'landing_pad_actual_source_joined':True,'C1022_2_actual_ground_source_joined':gndrooted,'IO3_named_source_pad_UUIDs_before':593,'IO3_named_source_pad_UUIDs_after':594,'full_IO3_budget_A':2.0,'leaf_current_ripple_cap_loop_source_return_potential_noise_native_and_thermal':'OPEN','not_a_0p30mm_2A_physical_rating':True}
 put(O/'exact-local-source-and-cap-ground-nodes.json',local)
 put(O/'receipt.json',{'verdict':'EXACT_C1022_SINGLE_ADDITIVE_NATIVE_PACKET_WITH_INCREMENTAL_HOST_PASS','positive_R214_parent_file':str((base/'model.pkl').resolve()),'positive_R214_parent_sha256':sha(base/'model.pkl'),'host_pass_file':str((a/'receipt.json').resolve()),'host_pass_sha256':sha(a/'receipt.json'),'current_host_model_file':str((a/'model.pkl').resolve()),'current_host_model_sha256':sha(a/'model.pkl'),'native_base_file':str(native.resolve()),'native_base_sha256':sha(native),'delete_rows':[],'footprint_replacement_rows':[],'add_rows':[{'kind':'segment','uuid':t['uuid'],'raw_net':t['net'],'geometry':t,'chunk_path':str(cf.resolve()),'chunk_sha256':sha(cf)}],'exact_additive_discrete_file':str(df.resolve()),'exact_additive_discrete_sha256':sha(df),'owned_new_zone_replacement_rows':changes,'owned_new_zone_replacements_file':str(qf.resolve()),'owned_new_zone_replacements_sha256':sha(qf),'local_source_ground_node_file':str((O/'exact-local-source-and-cap-ground-nodes.json').resolve()),'local_source_ground_node_sha256':sha(O/'exact-local-source-and-cap-ground-nodes.json'),'exact_full_reference_body_file':str(bf.resolve()),'exact_full_reference_body_sha256':sha(bf),'C1022_2_actual_ground_source_joined':gndrooted,'source_count_before':593,'source_count_after':594,'other_five_R220_return_gap_nominations_excluded':True,'all_current_full_IO3_2A_and_local_branch_loop_native_current_qualification':'OPEN','known_ROOT42_raw_reference_failure_unmodified_NOT_WAIVED':True,'all_supply_rooted':False,'adopted':False,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R222_COMPLETE',sha(O/'receipt.json'),'C1022_GND',gndrooted,'source_port',port['ref'],port['num'],'owned_q_changes',len(changes),flush=True)
if __name__=='__main__':main()
