"""Stage exact source-only repaired donor and four-path composition after gates.

Does not run pcbnew/Fill/DRC/Save/native/GPU or change any source/live file.
"""
from pathlib import Path
import hashlib
import json
import uuid
import sys
sys.dont_write_bytecode=True
import whole_group_r3 as W
P=W.P
HERE=Path(__file__).resolve().parent
AUDIT=HERE/'whole-group-audit-r3.json'
AUDIT_SHA='6a278b93acd36bc7c6429fc6ba2b3429d44f01791640dafbb21d1505333a0cab'
EXPECTED_FOUR={
 'construction.json':'a79e4fcfef0b40ccbecd8963395ded978b7237f45a85a629f943fd356cb1c991',
 'audit.json':'d23415e0bad8a207579a201543fce95a2f05731026da674146129c7e5c7846db',
 'ready.json':'8efcc51bdb7162ad6aa90aa9909dddd49aacad11aee1ecb9e42f04814ebf521d'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def require_packet(packet):
 if packet['verdict']!='HOST_WHOLE_GROUP_PASS_NATIVE_OPEN' or packet['failing_items']:
  raise ValueError('complete whole-group geometry required')
 graph=packet['layer_correct_physical_contact_closure']
 if not graph['all_prior_retained_physical_relationships_preserved'] or graph['lost_physical_relationship_components'] or graph['fill_contacts_included']:
  raise ValueError('layer-correct physical closure required')
 if packet['new_copper_clearance_exceptions'] or packet['native_jobs'] or packet['board_emitted']:
  raise ValueError('unexpected qualification mutation or new-copper exception')
 if (packet['retained_vias'],packet['new_vias'],packet['replacement_segments'],packet['final_donor_copper_items'])!=(4,1,18,269):
  raise ValueError('owned item accounting differs')
 if packet['r07_sha256']!=P.R.R07_SHA or packet['combined_target_sha256']!=W.TARGET_SHA:
  raise ValueError('target identities differ')
 if len(packet['actual_native_FIELD_via_flashed_layers'])!=478 or packet['suppressed_annulus_vias']!=11:
  raise ValueError('actual native annulus evidence required')
 if len(packet['retained250_chunks_sha256'])!=250 or len(packet['removed11_owned_uuids'])!=11:
  raise ValueError('whole owned group membership differs')

def encode(row,uid):
 net='/motherboard_motors{slash}FIELD_GND'
 if row['net']!=P.NET:raise ValueError('replacement net differs')
 def number(v):
  if not isinstance(v,(float,int)) or not(-10000<v<10000):raise ValueError('invalid coordinate')
  return format(v,'.6f').rstrip('0').rstrip('.') or '0'
 if row['kind']=='via':
  if (row['d'],row['drill'],list(row['at']))!=(.6,.3,[357.05,201.25]):raise ValueError('new ordinary via geometry differs')
  body=f'\t(via\n\t\t(at {number(row["at"][0])} {number(row["at"][1])})\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n'
 elif row['kind']=='segment':
  if row['layer'] not in('F.Cu','In3.Cu') or row['width'] not in(.3,.8) or row['a']==row['b']:raise ValueError('replacement trace geometry differs')
  body=f'\t(segment\n\t\t(start {number(row["a"][0])} {number(row["a"][1])})\n\t\t(end {number(row["b"][0])} {number(row["b"][1])})\n\t\t(width {number(row["width"])})\n\t\t(layer "{row["layer"]}")\n'
 else:raise ValueError('unsupported replacement copper')
 return (body+f'\t\t(locked yes)\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n').encode()

def pure_add(target,additions):
 before=P.R.composition.inventory(target)
 if any(uid in before[3] for uid,_ in additions):raise ValueError('new UUID collides with old native item')
 result=before[0]+b''.join(before[1])+b''.join(ch for _,ch in additions)+before[2]
 after=P.R.composition.inventory(result)
 if after[0]!=before[0] or after[2]!=before[2] or after[5]!=before[5] or any(after[3].get(u)!=ch for u,ch in before[3].items()):
  raise ValueError('source addition changed original native bytes')
 if len(after[4])-len(before[4])!=len(additions):raise ValueError('source addition accounting differs')
 return result

def reconstruct(packet,audit_sha,r07,donor,four):
 require_packet(packet)
 if sha(r07)!=P.R.R07_SHA or sha(donor)!=packet['donor_sha256'] or sha(four)!=W.TARGET_SHA:raise ValueError('actual input byte identities differ')
 original=P.R.composition.inventory(donor)
 target=P.R.composition.inventory(four);live=P.R.composition.inventory(r07)
 if any(target[3].get(u)!=ch for u,ch in live[3].items()) or target[5]!=live[5] or target[0]!=live[0] or target[2]!=live[2]:raise ValueError('four-path is not exact pure-add r07')
 target_extra={u:ch for u,ch in target[4].items() if u not in live[4]}
 if {u:sha(ch) for u,ch in target_extra.items()}!=packet['target_additional_copper']:raise ValueError('four-path18 ownership differs')
 additions=[]
 for uid,digest in packet['retained250_chunks_sha256'].items():
  chunk=original[4].get(uid)
  if chunk is None or sha(chunk)!=digest:raise ValueError('retained donor chunk differs:'+uid)
  additions.append((uid,chunk))
 removed=set(packet['removed11_owned_uuids'])
 if removed & {u for u,_ in additions}:raise ValueError('removed owned blocker survives')
 generated=[]
 for row in packet['replacements']:
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'ROOT106-FAG-r07-repair:'+W.TARGET_SHA+':'+audit_sha+':'+row['uuid']))
  chunk=encode(row,uid);parsed=W.parse_copper(uid,chunk)
  if parsed['kind']!=row['kind'] or parsed['net']!=row['net']:raise ValueError('encoded native copper differs')
  for key in(('at','d','drill') if row['kind']=='via' else ('a','b','width','layer')):
   if parsed[key]!=row[key]:raise ValueError('encoded geometry differs:'+key)
  additions.append((uid,chunk));generated.append({'plan_id':row['uuid'],'uuid':uid,'sha256':sha(chunk),'geometry':row})
 if len(additions)!=269 or len({u for u,_ in additions})!=269:raise ValueError('269 owned item membership differs')
 donor_new=pure_add(r07,additions);combined=pure_add(four,additions)
 # Independently compare each owned copper body to every one of the frozen18
 # additions on every shared actual layer. Via halos conservatively includeall6.
 cross=[];minimum=float('inf')
 for uid,chunk in additions:
  row=W.parse_copper(uid,chunk);layers={'F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'} if row['kind']=='via' else {row['layer']}
  for other,old in target_extra.items():
   r=W.parse_copper(other,old);shared=layers & ({'F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'} if r['kind']=='via' else {r['layer']})
   if not shared:continue
   gap=P.shape(row).distance(P.shape(r));minimum=min(minimum,gap)
   if gap<.6+.025-1e-6:cross.append({'owned':uid,'four_path':other,'layers':sorted(shared),'gap_mm':gap})
 if cross:raise ValueError('combined owned copper cross-domain conflict')
 return donor_new,combined,additions,generated,minimum

def main():
 folder=HERE/'staged'
 if folder.exists():raise ValueError('new distinct staging folder required')
 packetraw=P.S.read(AUDIT);packet=json.loads(packetraw);audit_sha=sha(packetraw)
 if audit_sha!=AUDIT_SHA:raise ValueError('frozen complete whole-group audit identity differs')
 require_packet(packet)
 for path,expected in packet['source_files_sha256'].items():
  if sha(P.S.read(path))!=expected:raise ValueError('whole-group input changed:'+path)
 for name,digest in EXPECTED_FOUR.items():
  if sha(P.S.read(W.TARGET.parent/name))!=digest:raise ValueError('four-path frozen evidence differs:'+name)
 for p in(Path(__file__),Path(W.__file__),Path(P.__file__)):P.S.read(p)
 donor,combined,items,generated,gap=reconstruct(packet,audit_sha,P.S.read(P.R.R07),P.S.read(P.I.DONOR),P.S.read(W.TARGET))
 for path,expected in P.S.READS.items():
  if sha(Path(path).read_bytes())!=expected:raise ValueError('source changed:'+path)
 folder.mkdir()
 out_donor=folder/'r07-fag-repaired.kicad_pcb';out_combined=folder/'r07-four-path-fag-repaired.kicad_pcb'
 out_donor.write_bytes(donor);out_combined.write_bytes(combined)
 if out_donor.read_bytes()!=donor or out_combined.read_bytes()!=combined:raise ValueError('written board differs')
 # Project/rules copies bind exact native contexts without changing originals.
 for stem in(out_donor.stem,out_combined.stem):
  for suffix,source in(('.kicad_pro',P.R.PRO),('.kicad_dru',P.R.DRU)):
   (folder/(stem+suffix)).write_bytes(P.S.read(source))
 receipt={'schema':'fag-r07-repaired-source-construction-v1','verdict':'PASS_SOURCE_ONLY_NATIVE_OPEN',
          'scope_A':.096,'whole_group_audit_sha256':audit_sha,'source_files_sha256':P.S.READS,
          'actual_r07_sha256':P.R.R07_SHA,'four_path_sha256':W.TARGET_SHA,
          'donor_path':str(out_donor),'donor_sha256':sha(donor),
          'combined_path':str(out_combined),'combined_sha256':sha(combined),
          'retained250_items_exact':True,'removed11_owned_uuids':packet['removed11_owned_uuids'],
          'owned269':{uid:sha(ch) for uid,ch in items},'new_generated19':generated,
          'r07_old_items_all_retained':True,'four_path18_all_retained_exact':True,
          'minimum_owned_to_four_path_shared_layer_gap_mm':gap,
          'all_field_via_mask_to_signal_copper_gap_exceeds_0_625mm':gap>.625,
          'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,
          'required':['fresh combined refill/uncapped native pad partitions and actualr07 lost0/APIguard',
                      'nativeDRC0/domain/pad-net/return/plane/ordinaryvia gates',
                      'prospective all-via signal reference/return masks; source/root/current96mA qualification only',
                      'historicalr06 regression reported separately; cannot adopt regressions invisibly',
                      'full field load/currentsharing/thermal/fault/transient proof remainsOPEN']}
 (folder/'construction.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({k:receipt[k] for k in('verdict','donor_path','donor_sha256','combined_path','combined_sha256','minimum_owned_to_four_path_shared_layer_gap_mm')},indent=1),flush=True)

if __name__=='__main__':main()
