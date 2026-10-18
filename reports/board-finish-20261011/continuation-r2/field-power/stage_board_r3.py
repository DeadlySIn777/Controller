"""Five field-added footprints and concrete local tracks, exact native raw nets."""
import json,re,copy,uuid,hashlib,math
from inventory import HERE,BOARD,PARSER,sha
from contact_layout import O,S,load,norm
from stage_board_chunks import netpads,load_parser
from verify_source import parse,atom,child,children
OUT=HERE/'board-delta-r3';SRC=HERE/'combined-power-source-r2'
def main():
 if OUT.exists():raise ValueError('Frozen board chunks exist')
 r=json.loads((HERE/'board-delta-r2/receipt.json').read_text(encoding='utf-8'));source=json.loads((SRC/'receipt.json').read_text(encoding='utf-8'));export=json.loads((SRC/'source-export/receipt.json').read_text(encoding='utf-8'));assert export['verdict']=='PASS'
 before=sha(BOARD);g,b=load();native=O.C.inventory(BOARD.read_bytes())[3];fps={S.overlay_tool.base.ref_of(ch):ch for ch in native.values() if O.C.pcbtext.chunk_kind(ch)=='footprint'};raws={}
 for net in set(re.findall(rb'\(net "([^"\r\n]+)"\)',BOARD.read_bytes())):
  s=net.decode('utf-8');key=norm(s)
  if key in raws and raws[key]!=s:raise ValueError('Raw native net-name collision')
  raws[key]=s
 OUT.mkdir()
 for p in (HERE/'board-delta-r2').glob('*.footprint-chunk'):(OUT/p.name).write_bytes(p.read_bytes())
 (OUT/'project-proposal.kicad_pro').write_bytes((HERE/'board-delta-r2/project-proposal.kicad_pro').read_bytes())
 local=json.loads((HERE/'new-local-bypass-r2.json').read_text(encoding='utf-8'));pose=next(x for x in local['candidates'] if x['local_all_paths_found']);ref='C11095';part=source['new_components'][ref];parser=load_parser(PARSER);fresh=parser['read_netlist'](SRC/'source-export/fresh.net');text=fps[part['clone']].decode('utf-8');old=parse(text);oldpose=child(old,'at');oldpath=atom(old,'path');paths=parser['expected_path'](fresh['components'][ref]);assert len(paths)==1
 text=text.replace(part['clone'],ref).replace('(path "'+oldpath+'")','(path "'+paths[0]+'")')
 for k in ['Value','MPN']:
  wanted=part['value'] if k=='Value' else part['mpn'];text,c=re.subn(r'\(property "'+k+r'" "[^"]*"','(property "'+k+'" "'+wanted+'"',text);assert c==1
 for uid in re.findall(r'\(uuid "([^"]+)"\)',text):text=text.replace(uid,str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller-field-C95-board-r2/'+uid)))
 xy=pose['pose_mm'];rot=pose['rotation_deg'];delta=rot-float(oldpose[3]);text,c=re.subn(r'\(at [\d.eE+-]+ [\d.eE+-]+ [\d.eE+-]+\)','(at '+str(xy[0])+' '+str(xy[1])+' '+str(rot)+')',text,count=1);assert c==1
 # Native pad angles are absolute, while their XY coordinates are relative
 # to the footprint. Rotate each new pad angle with the parent.
 for a,b in reversed(O.C.pcbtext.child_spans(text.encode('utf-8')) if hasattr(O.C.pcbtext,'child_spans') else []):pass
 from stage_source import top_spans
 for a,b in reversed(top_spans(text)):
  n=parse(text[a:b])
  if n[0]!='pad':continue
  p=text[a:b];p,c=re.subn(r'\(at ([\d.eE+-]+) ([\d.eE+-]+) ([\d.eE+-]+)\)',lambda m:'(at '+m[1]+' '+m[2]+' '+str(float(m[3])+delta)+')',p,count=1);assert c==1;text=text[:a]+p+text[b:]
 text=netpads(text,{pin:raws.get(norm(net),net) for pin,net in part['pins'].items()});root=parse(text);pads={p[1]:norm(atom(p,'net')) for p in children(root,'pad')};assert pads=={p:fresh['node_net'][(ref,p)] for p in part['pins']};props={p[1]:p[2] for p in children(root,'property')};assert props['Value']==fresh['components'][ref]['value'] and props['MPN']==part['mpn']
 padpos={}
 for p in children(root,'pad'):
  at=child(p,'at');x,y=map(float,at[1:3]);theta=math.radians(-rot);xx=xy[0]+x*math.cos(theta)-y*math.sin(theta);yy=xy[1]+x*math.sin(theta)+y*math.cos(theta);wanted=pose['new_pad_positions'][p[1]]['at'];assert math.dist((xx,yy),wanted)<1e-8;assert float(at[3])==rot;padpos[p[1]]=[xx,yy]
 cap=OUT/(ref+'.footprint-chunk');cap.write_bytes(text.encode('utf-8'));extra={'ref':ref,'clone':part['clone'],'kind':'NEW_C95_CLONE_GEOMETRY_EXPLICIT_BOM_POSE_PATH_IDENTITIES_AND_NETS','uuid':atom(root,'uuid'),'path':str(cap.resolve()),'chunk_sha256':sha(cap),'pose_mm':child(root,'at')[1:],'schematic_path':paths[0],'pads':pads,'pad_absolute_mm':padpos,'MPN':part['mpn'],'C95_BOM_qualification_source_sha256':sha(HERE/'new-local-bypass-r2.json')}
 fan=json.loads((HERE/'new-LDO-local-fanout-r1.json').read_text(encoding='utf-8'));chosen=next(x for x in fan['candidates'] if x['all_local_fanout_paths_found']);paths=chosen['local_fanout']+pose['paths'];chunks=[];raws['DOB_DO_FIELD_3V3']='DOB_DO_FIELD_3V3'
 for i,row in enumerate(paths):
  pts=row['path']['points_mm'];net=raws[norm(row['net'])];w=row['width_mm']
  for j,(a,b) in enumerate(zip(pts,pts[1:])):
   if math.dist(a,b)<1e-9:continue
   uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller-field-local-r3/'+str(i)+'/'+str(j)));t='(segment (start '+format(a[0],'.10g')+' '+format(a[1],'.10g')+') (end '+format(b[0],'.10g')+' '+format(b[1],'.10g')+') (width '+str(w)+') (layer "F.Cu") (net "'+net+'") (uuid "'+uid+'"))\n';p=OUT/(uid+'.segment-chunk');p.write_text(t,encoding='utf-8');chunks.append({'uuid':uid,'path':str(p.resolve()),'sha256':sha(p),'net_raw':net,'width_mm':w,'from_mm':a,'to_mm':b,'local_path_index':i})
 for p in OUT.glob('*.footprint-chunk'):
  for n in re.findall(r'\(net "([^"]+)"\)',p.read_text(encoding='utf-8')):
   assert n==raws.get(norm(n),n) and (norm(n) in raws or n.startswith('unconnected-(U11038-'))
 r=copy.deepcopy(r);r.update(schema='field-board-delta-r3-source-bound14moves5fieldparts-localpaths',supersedes_board_delta_receipt_sha256=sha(HERE/'board-delta-r2/receipt.json'),combined_native_source_sha256=sha(SRC/'source-export/fresh.net'),combined_native_source_receipt_sha256=sha(SRC/'source-export/receipt.json'),combined_source_counts=export['counts'],field_new_components=5,other_combined_source_owner={'C11094':'SBC','L11001_Value_MPN':'SBC','C11061_Value_MPN':'root'},local_tracks=chunks,local_host_paths=paths,raw_net_collision_count=0,all11_local_paths_emitted=True,whole_board_written=False,native_jobs=0,ready_for_native_integration=False)
 r['new_footprint_chunks'].append(extra)
 for row in r['existing_footprint_chunks']+r['new_footprint_chunks']:
  p=OUT/(row['ref']+'.footprint-chunk');row['path']=str(p.resolve());row['chunk_sha256']=sha(p)
 (OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');assert sha(BOARD)==before;print(json.dumps({'old_pad_net_moves':14,'new_field_parts':5,'local_paths':len(paths),'local_segment_chunks':len(chunks),'C95_pad_positions':padpos,'source_bound_to_fresh_combined':True,'receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
