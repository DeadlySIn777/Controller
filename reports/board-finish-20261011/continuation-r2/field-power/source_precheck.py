"""Exact source object delta precheck and deliberate error rejection, host only."""
import json
from inventory import HERE,BASE,BOARD,sha
from stage_source import SOURCE,owned_groups,top_spans
from verify_source import parse,atom,child,verify_variant

def objects(text):
 root=parse(text);rows={};other=[];counts={}
 for n in root[1:]:
  if not isinstance(n,list):other.append(n);continue
  uid=atom(n,'uuid')
  if uid:
   counts[uid]=counts.get(uid,0)+1
   # Preserve pre-existing repeated wire/label UUID occurrences byte-for-byte.
   # Changed sheets have no such repetitions. No historical repair is folded in.
   key=uid if counts[uid]==1 else uid+'#duplicate-'+str(counts[uid])
   rows[key]=n
  else:other.append(n)
 return rows,other

def precheck(directory,overrides=None):
 receipt=json.loads((directory/next((n for n in ['receipt-r3.json','receipt-r2.json','receipt.json'] if (directory/n).exists()))).read_text(encoding='utf-8'))
 expected_by_sheet={};added={};changed=[];originals={}
 for p in SOURCE.glob('*.kicad_sch'):
  old=p.read_text(encoding='utf-8');originals[p.name]=old
  before,meta=objects(old)
  text=(overrides or {}).get(p.name,(directory/'source'/p.name).read_text(encoding='utf-8'))
  after,ameta=objects(text)
  if meta!=ameta:raise ValueError('Source/library/meta changed '+p.name)
  if set(before)-set(after):raise ValueError('Existing source objects removed '+p.name)
  expected={}
  for row in receipt['pin_net_changes']:
   if row['ref'] not in owned_groups(old):continue
   a,b=owned_groups(old)[row['ref']]
   for x,y in top_spans('(kicad_sch '+old[a:b]+')'):
    node=parse(('(kicad_sch '+old[a:b]+')')[x:y])
    if node[0] not in ('label','hierarchical_label'):continue
    oldname=row['from'].replace('{slash}','/').rsplit('/',1)[-1]
    if node[1]!=oldname:continue
    uid=atom(node,'uuid');newname=row['to'].replace('{slash}','/').rsplit('/',1)[-1]
    exp=list(node)
    if row['to'].lstrip('/').startswith('DOB_DO_'):
     exp[0]='global_label'
     if node[0]=='label':exp.insert(2,['shape','bidirectional'])
    exp[1]=newname
    if uid in expected and expected[uid]!=exp:raise ValueError('Conflicting change role')
    expected[uid]=exp
  actual={u for u,n in before.items() if n!=after[u]}
  if actual!=set(expected):raise ValueError('Unexpected or missing changed objects '+p.name)
  for uid,n in expected.items():
   if after[uid]!=n:raise ValueError('Change exceeds label net move '+p.name+':'+uid)
  changed.extend({'sheet':p.name,'uuid':u,'before':before[u],'after':after[u]} for u in sorted(actual))
  new={u:n for u,n in after.items() if u not in before}
  if new:
   if p.name!='motherboard_power_entry.kicad_sch':raise ValueError('Unapproved new objects sheet')
   groups=owned_groups(text)
   wanted={}
   for ref,part in receipt['new_components'].items():
    a,b=groups[ref]
    rows,_=objects('(kicad_sch '+text[a:b]+')')
    wanted.update(rows)
    symbol=next(n for n in rows.values() if n[0]=='symbol')
    props={n[1]:n[2] for n in symbol if isinstance(n,list) and n[0]=='property'}
    if props['Reference']!=ref or props['Footprint']!=part['footprint']:raise ValueError('New component identity mismatch')
    if 'value' in part and props['Value']!=part['value']:raise ValueError('New component value mismatch')
    if props.get('MPN')!=part['mpn']:raise ValueError('New component MPN mismatch '+ref)
   if wanted!=new:raise ValueError('New source objects outside approved new component groups')
  added[p.name]=len(new)
  expected_by_sheet[p.name]=len(expected)
 if len(changed)!=len(receipt['pin_net_changes']):raise ValueError('Pad-role/object change count mismatch')
 # Project rules, hierarchy, libraries and all unchanged schematic files are exact.
 for name,digest in receipt['files'].items():
  if overrides and name.rsplit('/',1)[-1] in overrides:continue
  if sha(directory/name)!=digest:raise ValueError('Frozen source hash changed '+name)
 return {'verdict':'PASS','existing_changed_label_objects':len(changed),'added_source_object_counts':{k:v for k,v in added.items() if v},'pin_net_changes':receipt['pin_net_changes'],'new_component_refs':sorted(receipt['new_components']),'unchanged_existing_component_attributes':True,'board_sha256':sha(BOARD),'native_export':'NOT_RUN','scope':'All27 source sheets and31 frozen project files; exactly authorized label objects and new component groups only.'}

def main():
 variants={}
 for name in ['a-prereg-source','ab-prereg-split-source']:
  d=HERE/name;variants[name]=precheck(d)
 d=HERE/'ab-prereg-split-source';pe='motherboard_power_entry.kicad_sch';do='motherboard_do.kicad_sch'
 txt=(d/'source'/pe).read_text(encoding='utf-8');dotxt=(d/'source'/do).read_text(encoding='utf-8')
 # Errors are applied in memory only, preserving every source byte on disk.
 controls={
  'wrong_A_input_rail':{pe:txt.replace('"FIELD_5V"','"FIELD_5V_WRONG"',1)},
  'wrong_existing_component_value':{pe:txt.replace('(property "Value" "TPS7A1633DGNR"','(property "Value" "WRONG_PART"',1)},
  'wrong_B_VDD_global_net':{do:dotxt.replace('"DOB_DO_FIELD_3V3"','"DOB_WRONG_3V3"',1)},
  'wrong_new_PG_net':{pe:txt.replace('(label "FB_PGOOD"','(label "FB_PGOOD_WRONG"',1)}}
 failures={}
 for name,over in controls.items():
  try:
   precheck(d,over)
   result=verify_variant(d,text_overrides=over)
   if result['verdict']!='FAIL':raise AssertionError('Control failed to inject/reject '+name)
   failures[name]={'rejected':True,'mechanism':'independent pin graph','details':result['failures']}
  except ValueError as exc:failures[name]={'rejected':True,'mechanism':'exact full-source object delta','reason':str(exc)}
 result={'variants':variants,'negative_controls':failures,'source_or_board_edits':0,'native_jobs':0}
 (HERE/'source-semantic-precheck-r1.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'variants':{k:v['existing_changed_label_objects'] for k,v in variants.items()},'negative_controls_rejected':len(failures)}))
if __name__=='__main__':main()
