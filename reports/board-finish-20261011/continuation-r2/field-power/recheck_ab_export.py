"""Recheck preserved native export against corrected explicit global-net ledger."""
import json
from inventory import HERE,NET,PARSER,sha
from export_ab_native import DIR,OUT,compare,load_parser,source_identity,write
from source_precheck import precheck
def main():
 oldreceipt=json.loads((OUT/'receipt.json').read_text(encoding='utf-8'))
 ledger=DIR/'receipt-r3.json';r=json.loads(ledger.read_text(encoding='utf-8'))
 # The native export runner pinned original input hashes; helper/check reports
 # subsequently changed only to correct receipt spelling, not source/export.
 inputs={str(DIR/name):sha(DIR/name) for name in r['files']}
 for name,digest in r['files'].items():assert inputs[str(DIR/name)]==digest
 assert sha(OUT/'fresh.net')==oldreceipt['fresh_export_sha256']
 host=precheck(DIR);parser=load_parser(PARSER)
 old=parser['read_netlist'](NET);new=parser['read_netlist'](OUT/'fresh.net')
 result=compare(old,new,r);identity=source_identity(DIR/'source',new,parser)
 assert result['verdict']=='PASS',result
 assert identity['verdict']=='PASS',identity
 write(OUT/'semantic-delta-r2.json',result)
 rec={'verdict':'PASS','native_source_export':'PRESERVED_EXISTING_EXPORT_NO_NEW_JOB','fresh_export_sha256':sha(OUT/'fresh.net'),'original_export_sha256':sha(NET),'ledger_sha256':sha(ledger),'preserved_failed_receipt_sha256':sha(OUT/'receipt.json'),'source_identity_verdict':identity['verdict'],'host_object_precheck':host,'semantic_delta':result,'inputs_before':inputs,'inputs_after':{p:sha(p) for p in inputs},'canonical_global_net':'DOB_DO_FIELD_3V3','alias_normalisation_for_global':'NONE','ERC':False,'DRC':False,'board_saved':False,'adopted':False,'manufacturing_ready':False}
 assert rec['inputs_before']==rec['inputs_after'];write(OUT/'receipt-r2.json',rec)
 print(json.dumps({'verdict':'PASS','existing_moves':len(result['existing_pin_net_moves']),'new_parts':result['new_components'],'nodes':[result['before_nodes'],result['after_nodes']],'nets':[result['before_nets'],result['after_nets']],'receipt_sha256':sha(OUT/'receipt-r2.json')}))
if __name__=='__main__':main()
