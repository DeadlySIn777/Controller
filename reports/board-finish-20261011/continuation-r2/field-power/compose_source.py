"""Exact owned-entity source composition; all individual proofs are preserved."""
import copy,json,re,hashlib
from inventory import HERE,BASE,BOARD,NET,PARSER,load,sha
from stage_source import SOURCE,top_spans,owned_groups
from source_precheck import objects,precheck
from verify_source import parse,atom,children,child,verify_variant
OUT=HERE/'combined-power-source-r1'
AB=HERE/'ab-local-bypass-source';SBC=BASE/'continuation-r2/sbc-power/source-proposal-r2/motherboard_power_entry.kicad_sch';COR=BASE/'electrical-correction/c11061-v2/native/motherboard_power_entry.kicad_sch'
PE='motherboard_power_entry.kicad_sch'
def indexed(text):
 out={}
 for a,b in top_spans(text):
  n=parse(text[a:b]);u=atom(n,'uuid')
  if u:
   if u in out:raise ValueError('Changed-sheet duplicate UUID')
   out[u]=(a,b,text[a:b],n)
 return out
def sym(text,ref):
 for u,(a,b,t,n) in indexed(text).items():
  if n[0]=='symbol' and any(p[1:3]==['Reference',ref] for p in children(n,'property')):return u,(a,b,t,n)
 raise ValueError('Missing symbol '+ref)
def main():
 if OUT.exists():raise ValueError('Refuse prior composition')
 inputs=[AB/'receipt.json',AB/'host-precheck.json',SBC,SBC.parent/'host-verification.json',SBC.parent/'integrated-power-source.json',COR,COR.parent.parent/'receipt.json',BOARD,NET,PARSER]+list((AB/'source').iterdir());before={str(p):sha(p) for p in inputs}
 r=json.loads((AB/'receipt.json').read_text(encoding='utf-8'));original=(SOURCE/PE).read_text(encoding='utf-8');text=(AB/'source'/PE).read_text(encoding='utf-8');sbc=SBC.read_text(encoding='utf-8');cor=COR.read_text(encoding='utf-8');original_ix=indexed(original);sbc_ix=indexed(sbc)
 sbc_delta={u for u in original_ix if original_ix[u][3]!=sbc_ix[u][3]};li_u,_=sym(original,'L11001');assert sbc_delta=={li_u};newobjs={u:v for u,v in sbc_ix.items() if u not in original_ix};assert len(newobjs)==5
 attrs={'L11001':{'Value':('4.7uH 20%','6.8uH 20%'),'MPN':('XAL1010-472MED','XAL1010-682MED')},'C11061':{'Value':('4.7uF 16V X7R','4.7uF 25V X7R'),'MPN':('C2012X7R1C475K125AB','C2012X7R1E475K125AB')}};changes=[]
 for ref,pairs in attrs.items():
  uid,(a,b,t,n)=sym(text,ref);old_u,(_,_,oldt,oldn)=sym(original,ref);new_u,(_,_,newt,newn)=sym(sbc if ref=='L11001' else cor,ref);assert uid==old_u==new_u and n==oldn
  clone=copy.deepcopy(newn)
  for prop in children(clone,'property'):
   if prop[1] in pairs:
    old,new=pairs[prop[1]];assert prop[2]==new;prop[2]=old
  assert clone==oldn,(ref,'Changes outside authorized Value/MPN')
  text=text[:a]+newt+text[b:];changes.append({'ref':ref,'symbol_uuid':uid,'exact_property_changes':{p:{'from':v[0],'to':v[1]} for p,v in pairs.items()},'all_other_symbol_attributes_exact':True,'source_owner':'SBC source-proposal-r2' if ref=='L11001' else 'Root C11061 v2'})
 # Copy only the exact five added C11094 records from the separately verified
 # source. No schematic metadata, source hierarchy or unrelated source moves.
 c94nodes=' '.join(v[2] for u,v in newobjs.items());assert len([n for n in parse('(kicad_sch '+c94nodes+')') if isinstance(n,list) and n[0]=='symbol'])==1
 text=text[:text.rfind(')')]+c94nodes+'\n'+text[text.rfind(')'):]
 OUT.mkdir();dest=OUT/'source';dest.mkdir()
 for p in (AB/'source').iterdir():(dest/p.name).write_bytes(p.read_bytes())
 (dest/PE).write_text(text,encoding='utf-8',newline='')
 r=copy.deepcopy(r);r.update(schema='root106-combined-power-owned-source-r1',variant=OUT.name,allowed_existing_component_property_changes=changes,individual_source_proofs={'AB14plus4':str((HERE/'ab-prereg-split-source/source-export/receipt-r2.json').resolve()),'AB14plus5_host':str((AB/'host-precheck.json').resolve()),'SBC':str((SBC.parent/'host-verification.json').resolve()),'C11061_native_v2':str((COR.parent.parent/'receipt.json').resolve())},native_export='PENDING_FRESH_COMBINED_NATIVE_EXPORT',expected_native_counts={'components':2723,'nodes':9609,'nets':2388,'existing_pin_net_moves':14,'new_parts':6,'existing_value_MPN_changes':2})
 sbmanifest=json.loads((SBC.parent/'integrated-power-source.json').read_text(encoding='utf-8'));c94=sbmanifest['power_entry_components']['C11094'];r['new_components']['C11094']={'clone':'C11088','mpn':c94['fields']['MPN'],'value':c94['value'],'footprint':c94['footprint'],'pins':c94['pins']};r['files']={str(p.relative_to(OUT)):sha(p) for p in sorted(dest.iterdir())};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
 # Independently check exact14 labels +6 groups after undoing only the two
 # explicitly authorized component property changes in memory.
 undone=text
 for ref,pairs in attrs.items():
  uid,(a,b,t,n)=sym(undone,ref)
  for p,(old,new) in pairs.items():
   t,c=re.subn(r'\(property "'+re.escape(p)+r'" "'+re.escape(new)+r'"','(property "'+p+'" "'+old+'"',t);assert c==1
  undone=undone[:a]+t+undone[b:]
 object_gate=precheck(OUT,{PE:undone});pin_gate=verify_variant(OUT);assert object_gate['verdict']==pin_gate['verdict']=='PASS',pin_gate
 oldrefs=set().union(*(set(owned_groups(p.read_text(encoding='utf-8'))) for p in SOURCE.glob('*.kicad_sch')));newrefs=set();seen={};duplicates=[]
 for p in dest.glob('*.kicad_sch'):
  for ref in owned_groups(p.read_text(encoding='utf-8')):
   if ref in seen:duplicates.append((ref,seen[ref],p.name))
   seen[ref]=p.name;newrefs.add(ref)
 assert not duplicates and newrefs==oldrefs|set(r['new_components']) and not oldrefs&set(r['new_components'])
 checks={'verdict':'PASS_HOST_OWNED_ENTITY_COMPOSITION_FRESH_NATIVE_OPEN','exact14_net_move_plus6_new_groups_gate':object_gate,'independent_pin_wire_graph':pin_gate,'two_existing_component_attributes':changes,'full27_source_reference_census':{'original_all_source_instances_including_power_flags':len(oldrefs),'combined_instances':len(newrefs),'added_refs':sorted(newrefs-oldrefs),'duplicates':duplicates,'physical_native_expected_components':2723},'prior_source_hashes_before':before,'prior_source_hashes_after':{p:sha(p) for p in before},'native_jobs':0,'board_written':False,'combined_current_model':'FIELD model normal-model-r2 plus C95 10uA reservation; SBC independent source-correction-r2 7.882A case. Device limits/normal output contracts unchanged.'};assert checks['prior_source_hashes_before']==checks['prior_source_hashes_after'];(OUT/'host-precheck.json').write_text(json.dumps(checks,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'existing_net_moves':14,'new_parts':sorted(r['new_components']),'existing_attr_changes':sorted(attrs),'full_source_census':checks['full27_source_reference_census'],'pin_graph':pin_gate['verdict'],'source_receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
