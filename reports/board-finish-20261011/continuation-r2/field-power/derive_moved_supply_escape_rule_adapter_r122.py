"""Exact three-rule source synchronization; isolated proposal, no native write."""
import json,sys,re,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent.parent;sys.path.insert(0,str(R/'parity-repair'))
from host_parity import load_parser
from inventory import sha
P=load_parser(R/'parity-repair/root106/tools/netlist_parity.py')
O=H/'moved-supply-escape-rule-adapter-r122'
SPEC={'RESERVE_KEEPOUT_ESC_U11017_F':'/motherboard_power_entry{slash}FIELD_5V','RESERVE_KEEPOUT_ESC_U10017_F':'DOB_DO_FIELD_3V3','RESERVE_KEEPOUT_ESC_U10022_B':'DOB_DO_FIELD_3V3'}
def digest(data):return hashlib.sha256(data).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def ast(text):return P['sexpr_parse']('(root\n'+'\n'.join(x for x in text.splitlines() if not x.lstrip().startswith('#'))+'\n)')
def transform(data):
 result=data;rows=[]
 for name,net in SPEC.items():
  matches=[x for x in data.splitlines(keepends=True) if x.startswith(('(rule "'+name+'" ').encode())];assert len(matches)==1,name;old=matches[0];a=P['sexpr_parse'](old.decode());assert a[0]=='rule' and a[1]==name and a[3:]==[['constraint','disallow','track','via']];condition=a[2][1];assert net not in re.findall(r"A.NetName != '([^']*)'",condition)
  suffix=b'") (constraint disallow track via))';assert old.count(suffix)==1;new=old.replace(suffix,(" && A.NetName != '"+net+"'").encode()+suffix);aa=P['sexpr_parse'](new.decode());assert aa[:2]==a[:2] and aa[3:]==a[3:] and aa[2]==['condition',condition+" && A.NetName != '"+net+"'"]
  rows.append({'rule':name,'added_exact_raw_token':net,'before_text':old.decode(),'after_text':new.decode(),'before_sha256':digest(old),'after_sha256':digest(new),'before_AST':a,'after_AST':aa});assert result.count(old)==1;result=result.replace(old,new)
 return result,rows
def verify(before,after):
 expected,rows=transform(before);assert after==expected,'unexpected byte delta';a0=ast(before.decode());a1=ast(after.decode());assert len(a0)==len(a1)
 for x,y in zip(a0[1:],a1[1:]):
  if x[0]=='rule' and x[1] in SPEC:
   row=next(r for r in rows if r['rule']==x[1]);assert x==row['before_AST'] and y==row['after_AST']
  else:assert x==y,'unrelated AST changed'
 return rows
def main():
 assert not O.exists();O.mkdir();original=R/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru';before=original.read_bytes();after,rows=transform(before);verify(before,after)
 source=H/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';export=P['sexpr_parse'](source.read_text(encoding='utf-8'));nodes={}
 for n in P['children'](P['child'](export,'nets'),'net'):
  net=P['atom'](n,'name')
  for q in P['children'](n,'node'):
   key=(P['atom'](q,'ref'),P['atom'](q,'pin'));assert key not in nodes;nodes[key]=net
 proof=H/'ab-prereg-split-source/source-export/receipt-r2.json';pr=json.loads(proof.read_text());moves=pr['host_object_precheck']['pin_net_changes'];assert len(moves)==14 and all(nodes[(x['ref'],x['pin'])]==x['to'] for x in moves)
 assert nodes[('U11017','5')]==nodes[('U11017','8')]==SPEC['RESERVE_KEEPOUT_ESC_U11017_F'];assert nodes[('U10017','4')]==nodes[('U10022','4')]=='DOB_DO_FIELD_3V3'
 negative=[]
 mutations={'unrelated_version':after.replace(b'(version 1)',b'(version 2)',1),'constraint_or_width':after.replace(b'(constraint disallow track via)',b'(constraint track_width (min 0.15mm))',1),'area_name':after.replace(b"A.intersectsArea('RESERVE_KEEPOUT_ESC_U11017_F')",b"A.intersectsArea('OTHER_AREA')",1),'extra_allowed_token':after.replace(b" && A.NetName != 'DOB_DO_FIELD_3V3'",b" && A.NetName != 'DOB_DO_FIELD_3V3' && A.NetName != 'OTHER_SUPPLY'",1),'raw_alias':after.replace(b" && A.NetName != '/motherboard_power_entry{slash}FIELD_5V'",b" && A.NetName != '/motherboard_power_entry/FIELD_5V'",1)}
 for label,bad in mutations.items():
  assert bad!=after
  try:verify(before,bad)
  except AssertionError:negative.append({'case':label,'rejected':True})
  else:raise AssertionError('negative case accepted '+label)
 (O/'proposed.kicad_dru').write_bytes(after)
 for row in rows:
  for kind in ('before','after'):
   f=O/(row['rule']+'.'+kind+'.rule');f.write_bytes(row[kind+'_text'].encode());row[kind+'_file']=str(f.resolve());assert sha(f)==row[kind+'_sha256']
 write(O/'negative-checks.json',negative);write(O/'source-fourteen-pad-moves.json',moves);write(O/'owned-rule-replacement-recipe.json',{'kind':'EXACT_THREE_EXISTING_DRU_RULE_REPLACEMENTS','original_file':str(original.resolve()),'original_sha256':sha(original),'proposed_file':str((O/'proposed.kicad_dru').resolve()),'proposed_sha256':sha(O/'proposed.kicad_dru'),'operations':rows,'no_board_area_geometry_change':True,'no_track_width_clearance_or_other_constraint_change':True,'exact_native_raw_tokens_no_alias':True,'requires_exact_before_chunk_and_all_unrelated_byte_preservation':True})
 write(O/'receipt.json',{'verdict':'PASS_EXACT_SOURCE_RULE_SYNCHRONIZATION_PROPOSAL','recipe_sha256':sha(O/'owned-rule-replacement-recipe.json'),'original_DRU_sha256':sha(original),'proposed_DRU_sha256':sha(O/'proposed.kicad_dru'),'source_native_export_sha256':sha(source),'original_14_pad_proof_sha256':sha(proof),'all_14_existing_pad_assignments_exact_in_current_source':True,'fourteen_moves_sha256':sha(O/'source-fourteen-pad-moves.json'),'changed_existing_rules':list(SPEC),'added_allowed_tokens':SPEC,'original_area_inventory_sha256':sha(R/'recovery-composite/c06/alternate-r07/reserved-r07.json'),'all_areas_native_geometry_unchanged':True,'all_old_allowed_tokens_and_constraints_preserved':True,'all_unrelated_rule_and_comment_bytes_preserved':True,'negative_geometry_width_extra_token_alias_unrelated_checks':negative,'negative_checks_sha256':sha(O/'negative-checks.json'),'native_rule_parse_source_DRC_current_reference_gates':'OPEN','board_written':False,'native_jobs':0});print('R122',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
