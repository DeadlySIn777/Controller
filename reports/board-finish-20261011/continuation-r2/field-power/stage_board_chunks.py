"""Reviewable exact field footprint/net chunks; never writes a complete board."""
import copy,hashlib,json,re,sys,uuid
from pathlib import Path
from inventory import HERE,BASE,BOARD,PARSER,sha
from contact_layout import O,S,norm,load
from stage_source import top_spans
from verify_source import parse,atom,children,child
sys.path.insert(0,str(BASE/'parity-repair'))
from host_parity import load_parser

OUT=HERE/'board-delta-r2'
def write(p,r):p.write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
def netpads(text,changes):
 spans=top_spans(text);count=0
 for a,b in reversed(spans):
  n=parse(text[a:b])
  if n[0]!='pad' or n[1] not in changes:continue
  wanted=changes[n[1]];old=atom(n,'net');part=text[a:b]
  if not old:raise ValueError('Changed pad has no old net')
  part,num=re.subn(r'\(net "'+re.escape(old)+r'"\)','(net "'+wanted+'")',part)
  if num!=1:raise ValueError('Ambiguous pad net')
  text=text[:a]+part+text[b:];count+=1
 if count!=len(changes):raise ValueError('Pad change count mismatch')
 return text
def main():
 if OUT.exists():raise ValueError('Refuse prior board-delta revision')
 OUT.mkdir();g,binding=load();inputsha=sha(BOARD);ledger=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'))
 local=json.loads((HERE/'new-LDO-local-fanout-r1.json').read_text(encoding='utf-8'))
 chosen=next(c for c in local['candidates'] if c['all_local_fanout_paths_found'])
 native=O.C.inventory(BOARD.read_bytes())[3];fp={}
 for uid,ch in native.items():
  if O.C.pcbtext.chunk_kind(ch)=='footprint':fp[S.overlay_tool.base.ref_of(ch)]=ch
 existing={};rows=[]
 for x in ledger['pin_net_changes']:existing.setdefault(x['ref'],{})[x['pin']]=x['to']
 for ref,changes in existing.items():
  before=fp[ref];text=netpads(before.decode('utf-8'),changes);after=text.encode('utf-8')
  a,b=parse(before.decode('utf-8')),parse(text)
  # Every other native object in the footprint is exact, including poses,
  # pad/parent UUIDs, geometry, masks, paste, paths, values and labels.
  for old,new in zip(a,b):
   if isinstance(old,list) and old[0]=='pad' and old[1] in changes:
    on=child(old,'net');nn=child(new,'net');clone=copy.deepcopy(new);child(clone,'net')[1]=on[1]
    assert clone==old and nn[1]==changes[old[1]]
   else:assert old==new
  path=OUT/(ref+'.footprint-chunk');path.write_bytes(after)
  rows.append({'ref':ref,'kind':'EXISTING_FOOTPRINT_PAD_NETS_ONLY','uuid':atom(a,'uuid'),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'path':str(path.resolve()),'pad_net_changes':changes})
 parser=load_parser(PARSER);fresh=parser['read_netlist'](HERE/'ab-prereg-split-source/source-export/fresh.net')
 newparts=[]
 for ref,part in ledger['new_components'].items():
  original=fp[part['clone']];text=original.decode('utf-8').replace(part['clone'],ref)
  oldroot=parse(text);oldpath=atom(oldroot,'path');newpaths=parser['expected_path'](fresh['components'][ref]);assert len(newpaths)==1;newpath=newpaths[0]
  text=text.replace('(path "'+oldpath+'")','(path "'+newpath+'")')
  ids=re.findall(r'\(uuid "([^"]+)"\)',text)
  for uid in ids:text=text.replace(uid,str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller-field-AB-board-r1/'+ref+'/'+uid)))
  xy=chosen['poses_mm'][ref]
  text,n=re.subn(r'\(at ([\d.eE+-]+) ([\d.eE+-]+) ([\d.eE+-]+)\)',lambda m:'(at '+format(xy[0],'.10g')+' '+format(xy[1],'.10g')+' '+m[3]+')',text,count=1)
  assert n==1
  changes={pin:(norm(net) if net is not None else next(name for (r,p),name in fresh['node_net'].items() if r==ref and p==pin)) for pin,net in part['pins'].items()}
  # Existing board spelling is retained for inherited named nets; fresh global
  # and new NC names are exact, without invented slash aliases.
  known={norm(p['net']):p['net'] for p in g['pads'] if p['net']}
  changes={pin:known.get(net,net) for pin,net in changes.items()}
  text=netpads(text,changes);root=parse(text)
  assert root[1]==part['footprint'] and atom(root,'path')==newpath
  named={p[1]:norm(atom(p,'net')) for p in children(root,'pad') if p[1]}
  assert named=={p:fresh['node_net'][(ref,p)] for p in part['pins']}
  props={p[1]:p[2] for p in children(root,'property')};assert props['Value']==fresh['components'][ref]['value'] and props['MPN']==part['mpn']
  path=OUT/(ref+'.footprint-chunk');path.write_bytes(text.encode('utf-8'))
  newparts.append({'ref':ref,'clone':part['clone'],'kind':'NEW_FOOTPRINT_EXACT_CLONE_GEOMETRY_WITH_NEW_IDENTITIES_POSE_AND_SOURCE_NETS','uuid':atom(root,'uuid'),'path':str(path.resolve()),'chunk_sha256':sha(path),'pose_mm':child(root,'at')[1:],'schematic_path':newpath,'pads':named,'MPN':part['mpn']})
 # Declare the new global and three new named NC nets in the same field domain.
 # The AB proof source is immutable; this is a separate proposed project delta.
 project=HERE/'ab-prereg-split-source/source/motherboard.kicad_pro';pro=json.loads(project.read_text(encoding='utf-8'));before=copy.deepcopy(pro)
 newnets=sorted({name for (ref,pin),name in fresh['node_net'].items() if ref in ledger['new_components'] and name not in known})
 assert newnets==['DOB_DO_FIELD_3V3','unconnected-(U11038-DELAY-Pad7)','unconnected-(U11038-DNC-Pad2)','unconnected-(U11038-NC-Pad6)']
 rules=[{'netclass':'DOM_FIELD_B','pattern':n} for n in newnets]
 pro['net_settings']['netclass_patterns'].extend(rules)
 revert=copy.deepcopy(pro);del revert['net_settings']['netclass_patterns'][-4:];assert revert==before
 write(OUT/'project-proposal.kicad_pro',pro)
 result={'verdict':'PASS_NATIVE_CHUNK_SOURCE_SEMANTIC_PRECHECK_ONLY','board_sha256':inputsha,'fresh_source_export_sha256':sha(HERE/'ab-prereg-split-source/source-export/fresh.net'),'exact_existing_pad_net_moves':14,'existing_footprint_chunks':rows,'new_footprint_chunks':newparts,'local_host_paths':chosen['local_fanout'],'new_netclass_patterns':rules,'old_project_sha256':sha(project),'project_proposal_sha256':sha(OUT/'project-proposal.kicad_pro'),'mandatory_old_contact_cuts':'changed-pad-contact-r1.json; no entire shared trunk deletions','eligible_private_retags':'private-DO-copper-r1.json exact native replay;51 private copper items;32 retained shared pads stay on old rail','whole_board_written':False,'native_jobs':0,'all_new_source_sinks_connected':False,'ready_for_native_integration':False,'remaining_required':['Apply exact owned old-pad cuts preserving shared contact intervals and unaffected old-source graph.','Join new input/PG/output/return spines and old private groups to the new source.','Regenerate fill voids with unchanged native clearances and prove field-B source return and affected foreign-reference continuity.','Native source/board parity, ERC, full uncapped DRC/continuity under root-reviewed combined source/C11061 correction.']}
 write(OUT/'receipt.json',result);assert sha(BOARD)==inputsha
 print(json.dumps({'existing_pad_net_moves':14,'existing_footprints':len(rows),'new_parts':len(newparts),'new_class_patterns':len(rules),'local_paths':len(chosen['local_fanout']),'poses':chosen['poses_mm'],'board_written':False,'receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
