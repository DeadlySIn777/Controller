"""Freeze two isolated source deltas. Originals and measured board are never written."""
import json,re,uuid
from pathlib import Path
from inventory import HERE,BASE,NET,PARSER,BOARD,sha,load

SOURCE=BASE/'parity-repair/root106/source'
A_UUIDS={'19731823-b85a-580c-8594-16dc80506eba':('U11017','5'),'293PLACEHOLDER':('U11017','8'),'cecf9c31-043c-552d-b7e6-c43d1965d82f':('C11074','1')}
B_REFS={'U10016':'16','U10017':'4','U10022':'4','R10032':'2','R10034':'2','C10026':'1','C10028':'1','C10029':'1','C10037':'1','C10038':'1'}
NEW_NET='DOB_DO_FIELD_3V3'
def top_spans(s):
 depth=0;quoted=False;escaped=False;start=None;out=[]
 for i,c in enumerate(s):
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
   continue
  if c=='"':quoted=True;continue
  if c=='(':
   if depth==1:start=i
   depth+=1
  elif c==')':
   depth-=1
   if depth==1 and start is not None:out.append((start,i+1));start=None
   if depth<0:raise ValueError('Malformed source')
 if depth or quoted:raise ValueError('Unbalanced source')
 return out
def owned_groups(s):
 spans=top_spans(s);starts=[]
 for a,b in spans:
  t=s[a:b]
  if t.startswith('(symbol (lib_id '):
   m=re.search(r'\(property "Reference" "([^"]+)"',t)
   if m:starts.append((a,m[1]))
 groups={}
 for i,(a,r) in enumerate(starts):groups[r]=(a,starts[i+1][0] if i+1<len(starts) else s.rfind(')'))
 return groups
def replace_owned_label(s,ref,old,new,global_type=False,expected=1):
 a,b=owned_groups(s)[ref];t=s[a:b]
 pattern=re.compile(r'\((hierarchical_label|label) "'+re.escape(old)+r'"')
 matches=list(pattern.finditer(t))
 if len(matches)!=expected:raise ValueError(f'{ref}: expected{expected} owned labels, got{len(matches)}')
 def rep(m):
  if not global_type:return '('+m[1]+' "'+new+'"'
  return '(global_label "'+new+'"'+(' (shape bidirectional)' if m[1]=='label' else '')
 t=pattern.sub(rep,t)
 return s[:a]+t+s[b:]
def fresh_uuid(old,role):return str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller-ROOT106-field-r2/'+role+'/'+old))
def clone_group(s,ref,newref,x,y):
 a,b=owned_groups(s)[ref];t=s[a:b]
 loc=re.search(r'\(symbol \(lib_id "[^"]+"\) \(at ([\d.eE+-]+) ([\d.eE+-]+)',t)
 dx,dy=x-float(loc[1]),y-float(loc[2])
 t=t.replace('"'+ref+'"','"'+newref+'"')
 ids=re.findall(r'\(uuid "([^"]+)"\)',t)
 for old in ids:t=t.replace(old,fresh_uuid(old,newref))
 # The instance path embeds the symbol UUID without a uuid tag.
 old_symbol=re.search(r'\(uuid "([^"]+)"',s[a:b])[1]
 t=t.replace(old_symbol,fresh_uuid(old_symbol,newref))
 def xy(m):return '('+m[1]+' '+format(float(m[2])+dx,'.10g')+' '+format(float(m[3])+dy,'.10g')
 t=re.sub(r'\((at|xy) ([\d.eE+-]+) ([\d.eE+-]+)',xy,t)
 return t
def changed_sheets(original,modified):
 return {name:{'before_sha256':sha(SOURCE/name),'after_sha256':__import__('hashlib').sha256(text.encode('utf-8')).hexdigest()} for name,text in modified.items() if original[name]!=text}
def write_variant(name,modified,changes,added=None):
 out=HERE/name
 if out.exists():raise ValueError('Refuse existing variant '+str(out))
 out.mkdir();dest=out/'source';dest.mkdir()
 for p in sorted(SOURCE.glob('*.kicad_sch')):
  if p.name in modified:(dest/p.name).write_text(modified[p.name],encoding='utf-8',newline='')
  else:(dest/p.name).write_bytes(p.read_bytes())
 for file in ['motherboard.kicad_pro','motherboard.kicad_dru','sym-lib-table','fp-lib-table']:(dest/file).write_bytes((SOURCE/file).read_bytes())
 manifest={str(p.relative_to(out)):sha(p) for p in sorted(dest.iterdir())}
 rec={'schema':'root106-field-prereg-source-delta-r2','variant':name,'original_source_root':str(SOURCE.resolve()),'original_board_sha256':sha(BOARD),'pin_net_changes':changes,'new_components':added or {},'files':manifest,'native_export':'PENDING_ROOT_REVIEW','ERC':'NOT_RUN','source_board_parity':'PENDING_BOARD_DELTA','board_saved':False,'adopted':False,'manufacturing_ready':False,'original_netlist_intentionally_not_copied':'Every changedvariant requires its own fresh nativeexport; no stale netlist is presented ascurrent.'}
 (out/'receipt.json').write_text(json.dumps(rec,indent=1)+'\n',encoding='utf-8')
 return rec
def main():
 original={p.name:p.read_text(encoding='utf-8') for p in SOURCE.glob('*.kicad_sch')};inputs={str(p):sha(p) for p in SOURCE.iterdir() if p.is_file()};inputs[str(BOARD)]=sha(BOARD)
 s=original['motherboard_power_entry.kicad_sch'];s=replace_owned_label(s,'U11017','FIELD_A_24V_PROTECTED','FIELD_5V',expected=2);s=replace_owned_label(s,'C11074','FIELD_A_24V_PROTECTED','FIELD_5V')
 a_changes=[{'ref':r,'pin':p,'from':'/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED','to':'/motherboard_power_entry{slash}FIELD_5V'} for r,p in [('U11017','5'),('U11017','8'),('C11074','1')]]
 a=write_variant('a-prereg-source',{'motherboard_power_entry.kicad_sch':s},a_changes)
 # C11076 remains on24V in originalROOT106 after the B-LDO IN/EN change.
 # Move its owned local input bypass to the actual5Vpre rail in this derivative.
 s=replace_owned_label(s,'C11076','FIELD_B_24V_PROTECTED','FIELD_B_5V_PRE')
 do=original['motherboard_do.kicad_sch']
 for ref in B_REFS:do=replace_owned_label(do,ref,'DOB_FIELD_3V3',NEW_NET,global_type=True)
 additions=[]
 for old,new,x,y in [('U11018','U11038',950,3190),('C11076','C11092',750,3310),('C11077','C11093',850,3310),('R11065','R11088',1050,3310)]:
  t=clone_group(s,old,new,x,y)
  if old=='U11018':
   # Replace only the owned PG no-connect (pin3 of the cloned symbol).
   top=top_spans('(kicad_sch '+t+')');nc=[t2 for a2,b2 in top if (t2:=('(kicad_sch '+t+')')[a2:b2]).startswith('(no_connect ')]
   # Clone pin3 is second left no-connect, originallyU11018.3 at690.88,1115.06.
   px,py=950-20.32,3190-5.08
   pattern=re.compile(r'\(no_connect \(at '+re.escape(format(px,'.10g'))+' '+re.escape(format(py,'.10g'))+r'\) \(uuid "[^"]+"\)\)')
   wire=f'(wire (pts (xy {px:g} {py:g}) (xy {px-30.48:g} {py:g})) (stroke (width 0) (type default)) (uuid "{fresh_uuid("PGwire",new)}")) (label "FB_PGOOD" (at {px-30.48:g} {py:g} 0) (effects (font (size 0.7 0.7)) (justify left bottom)) (uuid "{fresh_uuid("PGlabel",new)}"))'
   t,n=pattern.subn(wire,t);assert n==1
  # Apply own rail label replacements within the cloned group by temporary root.
  tmp='(kicad_sch '+t+')'
  if old in ['U11018','C11077','R11065']:tmp=replace_owned_label(tmp,new,'DOB_FIELD_3V3',NEW_NET,global_type=True)
  t=tmp[len('(kicad_sch '):-1];additions.append(t)
 s=s[:s.rfind(')')]+''.join(additions)+s[s.rfind(')'):]
 parts,_,_=load()
 added={'U11038':{'clone':'U11018','mpn':'TPS7A1633DGNR','footprint':'CNC_MB_Entry:TPS7A16_DGN8_TI','pins':{'1':'/'+NEW_NET,'2':None,'3':'/motherboard_power_entry{slash}FB_PGOOD','4':'/motherboard_do{slash}FIELD_B_0V','5':'/motherboard_safety_sensor{slash}FIELD_B_5V_PRE','6':None,'7':None,'8':'/motherboard_safety_sensor{slash}FIELD_B_5V_PRE','9':'/motherboard_do{slash}FIELD_B_0V'}},
  'C11092':{'clone':'C11076','mpn':'CGA5L3X7S2A225K160AB','footprint':'Capacitor_SMD:C_1206_3216Metric','value':'2.2uF 100V X7S','pins':{'1':'/motherboard_safety_sensor{slash}FIELD_B_5V_PRE','2':'/motherboard_do{slash}FIELD_B_0V'}},
  'C11093':{'clone':'C11077','mpn':'GCM31CR71A226KE02L','footprint':'Capacitor_SMD:C_1206_3216Metric','value':'22uF 10V X7R','pins':{'1':'/'+NEW_NET,'2':'/motherboard_do{slash}FIELD_B_0V'}},
  'R11088':{'clone':'R11065','mpn':'CRCW060310K0FKEA','footprint':'Resistor_SMD:R_0603_1608Metric','value':'10000R 1%','pins':{'1':'/'+NEW_NET,'2':'/motherboard_do{slash}FIELD_B_0V'}}}
 assert not set(added)&set(parts)
 bchanges=a_changes+[{'ref':'C11076','pin':'1','from':'/motherboard_power_entry{slash}FIELD_B_24V_PROTECTED','to':'/motherboard_safety_sensor{slash}FIELD_B_5V_PRE'}]+[{'ref':r,'pin':p,'from':'/motherboard_do{slash}DOB_FIELD_3V3','to':'/'+NEW_NET} for r,p in B_REFS.items()]
 b=write_variant('ab-prereg-split-source',{'motherboard_power_entry.kicad_sch':s,'motherboard_do.kicad_sch':do},bchanges,added)
 assert inputs=={p:sha(p) for p in inputs}
 result={'A':a,'AB':b,'originals_before':inputs,'originals_after':{p:sha(p) for p in inputs},'source_changes_staged_only':True,'native_jobs':0}
 (HERE/'source-staging-receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'A_changed_pad_roles':len(a_changes),'AB_changed_pad_roles':len(bchanges),'added_refs':list(added),'originals_unchanged':True,'native_export':'PENDING'}))
if __name__=='__main__':main()
