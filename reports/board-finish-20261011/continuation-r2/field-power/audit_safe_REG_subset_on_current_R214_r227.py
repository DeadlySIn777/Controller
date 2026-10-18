"""Replay only six corrected regulated proposals on the exact current host head."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_REG_rebuilt_B3_on_wider_IO3_r209.py').read_text(encoding='utf-8')
s=s.replace('REG-rebuilt-B3-on-wider-IO3-full-audit-r209','REG-safe-subset-on-current-R214-full-audit-r227')
s=s.replace("baseline=H/'U10017-wider-on-exact-IO3-audit-r195';assert sha(baseline/'model.pkl')=='103f9dbba8ac50bd90a913d4a7004cd94c3a06ed07d7ab5262c84de6c358f8ab'","baseline=H/'R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(baseline/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'")
start=s.index(" W=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201'")
end=s.index(" R=H/'SAFE-regulated-u17-u10017-paired-regional-audit-r171'",start)
s=s[:start]+" print('R227 exact current R214 baseline',flush=True);before,basecuts=P.projected(g,h,z);oldgroups={net:F.graph(before,net) for net in sorted({C.norm(q['net']) for q in before['zones']})}\n"+s[end:]
s=s.replace("'tracks':[t for t in reg['tracks'] if C.norm(t['net'])=='/motherboard_power_entry/FIELD_5V']","'tracks':[t for t in reg['tracks'] if t['uuid'] not in {'21cfaa39-440a-5788-898c-147152921e7a','18008563-f6e6-5172-9f62-6d9aff0561b4','f7771804-1031-58d5-b67f-e44f3ded6f0a'}]")
s=s.replace("'e8ec0287-e6d1-597d-8ad8-c4ab74280f6c')];assert len(newq)==5","'e8ec0287-e6d1-597d-8ad8-c4ab74280f6c','938b9038-0f65-5de2-99ed-d6781afcb116')];assert len(newq)==4")
s=s.replace("assert len(newq)==7 and", "assert len(newq)==6 and")
marker=" current={q['uuid']:q for q in z};base_owned=copy.deepcopy(current);replays=[]"
correction=" corrected=H/'B3-literal-eligible-LOGIC-reference-correction-r224';assert sha(corrected/'receipt.json')=='59ba702354f6824d1618700ad4e0d0581cb462353ec4c8beaf9cacfb570c390e';cq=pickle.loads((corrected/'proposed-corrected-zone.pkl').read_bytes())[0];newq=[cq if q['uuid']==cq['uuid'] else q for q in newq]\n"
assert marker in s;s=s.replace(marker,correction+marker)
s=s.replace("b['generated_precision_state_ledger']=precision;", "b['generated_precision_state_ledger']=precision;b['restored_generated_grid_UUIDs']=sorted({q['uuid'] for q in z});")
s=s.replace(",('U9002','10'),('R11053','1')",'').replace(",('U10013','4')",'')
s=s.replace("'exact_IO3_R201_one_q_replay_and_wide_U10017_R195':True", "'current_R214_actual_native_R54_and_monitor_peer_head':True")
s=s.replace('REG_REBUILT_B3_WIDER_IO3_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS','SAFE_REG_SUBSET_CURRENT_R214_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS').replace('REG_REBUILT_B3_WIDER_IO3_REPAIR_REQUIRED','SAFE_REG_SUBSET_CURRENT_R214_REPAIR_REQUIRED')
s=s.replace("'all_device_and_output_limits_current_fault_native_GATES':'OPEN'", "'all_device_and_output_limits_current_fault_native_GATES':'OPEN','failed_FIELD5_938_withdrawn':True,'corrected_B3_reference_clip_sha256':sha(corrected/'receipt.json')")
# Append source census to explicitly retain incomplete FIELD5/A3/BDO endpoints.
extra=r''' from regulated_outer_joins_r51 import PORTS
 rail_census=[]
 for bank,net,ref,pin,policy in PORTS:
  groups=F.graph(after,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));keys=F.discrete_keys(root);unrooted=[]
  for xs in groups:
   pads=[{k:q[k] for k in ('ref','pin','uuid','net','layer')} for q in xs if q['kind']=='pad']
   if pads and not F.discrete_keys(xs).issubset(keys):unrooted.append({'pads':pads,'physical_contact_count':len(F.discrete_keys(xs))})
  rail_census.append({'bank':bank,'source':ref+'.'+pin,'source_named_pad_count':len({q['uuid'] for q in root if q['kind']=='pad'}),'remaining_unrooted_named_groups':unrooted,'policy_a':policy})
 write(O/'actual-all-regulated-rail-source-census.json',rail_census)
'''
transform="\ns=s.replace("+repr(" b['REG_rebuilt_B3_exact_R206_on_wider_IO3_R209']")+","+repr(extra+" b['REG_rebuilt_B3_exact_R206_on_wider_IO3_R209']")+")\n"
s=s.replace('exec(compile(s,',transform+'exec(compile(s,')
exec(compile(s,str(H/'audit_REG_rebuilt_B3_on_wider_IO3_r209.py'),'exec'))
