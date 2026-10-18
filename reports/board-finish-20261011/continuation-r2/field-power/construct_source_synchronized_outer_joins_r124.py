"""Retry only seven bare REG pads with exact source-bound escape adapter."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_fresh_regulated_outer_joins_r117.py').read_text().replace('regulated-fresh-short-outer-source-joins-r117','regulated-source-synchronized-outer-joins-r124').replace('regulated-source-contact-reference-audit-r116','regulated-indexed-reference-wall-repair-base-r123').replace('controller-regulated-outer-r117/','controller-regulated-outer-r124/')
hook="exec(compile(s,str(p/'regulated_outer_joins_r51.py'),'exec'))"
inject='''
s=s.replace("br['R114_delta_receipt_sha256']","sha(HERE/'regulated-quantized-inner-source-feeds-r114/receipt.json')")
s=s.replace("dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text()","adapterpath=HERE/'moved-supply-escape-rule-adapter-r122/proposed.kicad_dru';assert sha(adapterpath)=='7a26abd1177cef82d70116f48bc1cff4210c39e75970e043e50e57767425c360';dru=adapterpath.read_text()")
s=s.replace("if gi in connected or not any(q['kind']=='pad' and q['pin'] for q in xs):continue","if gi in connected or not any(q['kind']=='pad' and q['uuid'] in {'f5938721-05c3-4465-a74c-ca3da51e6358','bc6cc164-9d11-471d-b4a4-7f847f99f6a1','6c2b253d-b5d8-4b22-b8c0-121ad2706400','d5d768c7-541b-481d-b077-4d20cefb22d4','c9edacd8-6803-4330-aad4-ed8204d87c27','3d4d251e-988b-439c-9dfc-a64f3c03ca4f','fe4a7ff6-4e8f-4213-9fa2-0d4b96205e12'} for q in xs):continue")
s=s.replace("'native_jobs':0","'exact_R122_source_rule_adapter_receipt_SHA256':sha(HERE/'moved-supply-escape-rule-adapter-r122/receipt.json'),'adapter_is_isolated_proposal_native_rule_parse_pending':True,'native_jobs':0")
'''
assert s.count(hook)==1;s=s.replace(hook,inject+'\n'+hook)
exec(compile(s,str(p/'construct_fresh_regulated_outer_joins_r117.py'),'exec'))
