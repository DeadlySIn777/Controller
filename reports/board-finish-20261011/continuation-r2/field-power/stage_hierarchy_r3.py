"""Restore retained B rail child port without changing any electrical node."""
import copy,json,re,shutil
from pathlib import Path
from inventory import HERE,sha
from verify_source import parse,children,atom,child,verify_variant,sheet_graph,baseline_maps,resolve_label
from stage_source import top_spans
from source_precheck import objects,precheck
from compose_source import sym

BASE=HERE/'combined-power-source-r2';OUT=HERE/'combined-power-source-r3-hierarchy'
UID='9878256d-6e85-5b47-8e55-7dbf2c161d50'
PARENT_UID='3ff24e07-99b7-5d36-a463-5b8b29c52846'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def locate(text,uid):
 rows=[]
 for a,b in top_spans(text):
  n=parse(text[a:b])
  if atom(n,'uuid')==uid:rows.append((a,b,n,text[a:b]))
 assert len(rows)==1
 return rows[0]
def inherited_contract(directory,r,undo_do):
 p=directory/'source/motherboard_power_entry.kicad_sch';s=p.read_text(encoding='utf-8')
 for row in r['allowed_existing_component_property_changes']:
  _,(a,b,t,n)=sym(s,row['ref'])
  for prop,v in row['exact_property_changes'].items():
   t,c=re.subn(r'\(property "'+prop+r'" "'+re.escape(v['to'])+r'"','(property "'+prop+'" "'+v['from']+'"',t);assert c==1
  s=s[:a]+t+s[b:]
 return precheck(directory,{'motherboard_power_entry.kicad_sch':s,'motherboard_do.kicad_sch':undo_do})
def main():
 assert not OUT.exists();r=copy.deepcopy(json.loads((BASE/'receipt.json').read_text(encoding='utf-8')))
 for name,digest in r['files'].items():
  assert sha(BASE/name)==digest;p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/name,p)
 name='motherboard_do.kicad_sch';p=OUT/'source'/name;old=p.read_text(encoding='utf-8');a,b,n,oldchunk=locate(old,UID)
 assert n[0]=='label' and n[1]=='DOB_FIELD_3V3' and child(n,'at')==['at','807.72','1112.52','0']
 expected=copy.deepcopy(n);expected[0]='hierarchical_label';expected.insert(2,['shape','bidirectional'])
 newchunk=oldchunk.replace('(label ', '(hierarchical_label ',1).replace('(at ','(shape bidirectional) (at ',1)
 assert parse(newchunk)==expected;new=old[:a]+newchunk+old[b:];p.write_text(new,encoding='utf-8',newline='')
 before,meta=objects(old);after,ameta=objects(new)
 assert meta==ameta and set(before)==set(after) and {k for k in before if before[k]!=after[k]}=={UID}
 root=parse((OUT/'source/motherboard.kicad_sch').read_text(encoding='utf-8'))
 parent=[pin for sh in children(root,'sheet') for pin in children(sh,'pin') if atom(pin,'uuid')==PARENT_UID]
 assert len(parent)==1 and parent[0][1:3]==['DOB_FIELD_3V3','bidirectional']
 h=[h for h in children(parse(new),'hierarchical_label') if h[1]=='DOB_FIELD_3V3'];assert len(h)==1 and atom(h[0],'uuid')==UID
 _,maps,_=baseline_maps()
 def resolved(t):
  return {ref:{pin:sorted({resolve_label(maps,name,kind,label) for kind,label in labels},key=str) for pin,labels in pins.items()} for ref,pins in sheet_graph(t).items()}
 assert resolved(old)==resolved(new)
 r.update(schema='root106-combined-power-owned-source-r3-hierarchy',variant=OUT.name,supersedes_combined_source_receipt_sha256=sha(BASE/'receipt.json'),supersedes_combined_native_export_sha256=sha(BASE/'source-export/fresh.net'),hierarchy_correction={'sheet':name,'existing_object_uuid':UID,'parent_sheet_pin_uuid':PARENT_UID,'kind_from':'label','kind_to':'hierarchical_label','net_text':'DOB_FIELD_3V3','shape':'bidirectional','anchor_mm':[807.72,1112.52],'retained_pin':'J10004.3','same_text_UUID_position_effects_wire_and_electrical_membership':True,'existing_or_new_pad_net_moves_relative_to_r2':0,'before':n,'after':expected,'before_chunk':oldchunk,'after_chunk':newchunk},correction='Restore the old B rail child port on its retained J10004.3 net; the separate DO global rail and all14 original moves/6 new parts/2 BOM pairs remain exact.')
 r['files']={name:sha(OUT/name) for name in r['files']};write(OUT/'receipt.json',r)
 inherited=inherited_contract(OUT,r,old);v=verify_variant(OUT,r);assert inherited['verdict']==v['verdict']=='PASS'
 write(OUT/'host-precheck.json',{'verdict':'PASS','exact_r2_to_r3_changed_objects':1,'exact_changed_UUID':UID,'unchanged_full27_sheets_except_one_label_kind_and_shape':True,'no_electrical_membership_change':True,'retained_root_child_hierarchy_match':True,'old_source_contract_after_undo_one_hierarchy_object':inherited,'independent_current_pin_graph':v,'native_export':'PENDING','ERC':'PENDING_PARENT_REPLAY','board_saved':False})
 print(json.dumps({'variant':str(OUT),'receipt_sha256':sha(OUT/'receipt.json'),'host':'PASS','pin_graph':'PASS','changed_existing_hierarchy_objects':1,'pad_net_changes_from_r2':0}))
if __name__=='__main__':main()
