"""Canonical recheck of frozen native export; numeric net IDs are ephemeral."""
import json
from inventory import HERE,NET,PARSER,sha
from export_ab_native import canonical_component,write,load_parser,source_identity
from export_combined_native_r2 import semantic_contract
from stage_hierarchy_r3 import OUT as DIR,BASE
from export_hierarchy_native_r3 import raw_net_names
def main():
 out=DIR/'source-export';assert not (out/'receipt-r2.json').exists();first=json.loads((out/'receipt.json').read_text(encoding='utf-8'));status=json.loads((out/'status.json').read_text(encoding='utf-8'))
 # Inputs were frozen in the queued status; completion status intentionally
 # contains no hashes, so recover the exact pinned invocation from source
 # receipt plus prior native source without modifying the first FAIL receipt.
 assert first['native_exit_code']==0 and first['verdict']=='FAIL' and 'same_full_net_memberships' in first['reason']
 r=json.loads((DIR/'receipt.json').read_text(encoding='utf-8'));assert all(sha(DIR/name)==v for name,v in r['files'].items())
 p=load_parser(PARSER);original=p['read_netlist'](NET);a=p['read_netlist'](BASE/'source-export/fresh.net');b=p['read_netlist'](out/'fresh.net')
 def cnet(n):return {k:v for k,v in n.items() if k!='code'}
 zero={'verdict':'PASS','same_component_refs':set(a['components'])==set(b['components']),'canonical_component_differences':[ref for ref in a['components'] if canonical_component(a['components'][ref])!=canonical_component(b['components'][ref])],'same_full_pin_net_assignments':a['node_net']==b['node_net'],'canonical_net_differences':[n for n in a['nets'] if cnet(a['nets'][n])!=cnet(b['nets'][n])],'same_exact_raw_native_net_tokens':raw_net_names(BASE/'source-export/fresh.net')==raw_net_names(out/'fresh.net'),'ephemeral_numeric_net_code_changes':sum(a['nets'][n]['code']!=b['nets'][n]['code'] for n in a['nets']),'numeric_net_code_is_not_electrical_membership':True,'single_exact_hierarchy_object':r['hierarchy_correction']}
 assert zero['same_component_refs'] and not zero['canonical_component_differences'] and zero['same_full_pin_net_assignments'] and not zero['canonical_net_differences'] and zero['same_exact_raw_native_net_tokens'];sem=semantic_contract(original,b,r);identity=source_identity(DIR/'source',b,p);assert sem['verdict']==identity['verdict']=='PASS'
 write(out/'hierarchy-zero-electrical-delta-r2.json',zero);write(out/'semantic-delta-r2.json',sem);write(out/'source-identity-r2.json',identity)
 result={'verdict':'PASS','first_failure_receipt_preserved_sha256':sha(out/'receipt.json'),'recheck_reason':'First comparison included ephemeral numeric net code. All named net attributes, exact raw spelling, complete node membership and canonical components are identical. No source or export bytes changed.','native_exit_code':0,'fresh_export_sha256':sha(out/'fresh.net'),'source_receipt_sha256':sha(DIR/'receipt.json'),'prior_combined_export_sha256':sha(BASE/'source-export/fresh.net'),'counts':{'components':len(b['components']),'nodes':len(b['node_net']),'nets':len(b['nets'])},'hierarchy_zero_electrical_delta':'PASS','semantic_verdict':sem['verdict'],'semantic_defect_counts':sem['counts'],'source_identity_verdict':identity['verdict'],'native_jobs_in_recheck':0,'board_saved':False,'ERC':False,'DRC':False,'adopted':False}
 write(out/'receipt-r2.json',result);print(json.dumps(result))
if __name__=='__main__':main()
