"""Compose exact field chunks/returns and prospective clearance voids for routing."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,pickle,json,hashlib,uuid
from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union
from contact_layout import HERE,BOARD,load,build,poly,norm,O,identity
from inventory import sha
from verify_source import parse,children,child,atom
from power_groups import graph,N,ROOTS
OUT=HERE/'composed-field-geometry-r3'

def polygons(sh):
 ps=[sh] if sh.geom_type=='Polygon' else [q for q in getattr(sh,'geoms',[]) if q.geom_type=='Polygon']
 return [[list(p.exterior.coords),[list(r.coords) for r in p.interiors]] for p in ps]

def main():
 if OUT.exists():raise ValueError('Frozen composed geometry exists')
 OUT.mkdir();original,b=load();g=pickle.loads((HERE/'owned-pad-cuts-r1/prospective-geometry.pkl').read_bytes());recipe=json.loads((HERE/'candidate-recipe-r1/receipt.json').read_text(encoding='utf-8'));rreturn=json.loads((HERE/'triangulated-return-r2/receipt.json').read_text(encoding='utf-8'));native=O.C.inventory(BOARD.read_bytes())[3];oldfps={O.S.overlay_tool.base.ref_of(q):q for q in native.values() if O.C.pcbtext.chunk_kind(q)=='footprint'};changedCu=[];moved={(r['ref'],p) for r in recipe['existing_footprint_replacements'] for p in r['pad_net_changes']}
 for p in g['pads']:
  if (p['ref'],p['num']) in moved:
   for layer,ps in p['layers'].items():changedCu.append({'shape':unary_union(poly(ps)),'layer':layer,'net':p['net'],'domain':g['domains_normalized'][norm(p['net'])] if norm(p['net']) in g['domains_normalized'] else 'DOM_FIELD_B','kind':'changed_pad','uuid':p['uuid']})
 for row in recipe['new_field_footprint_additions']:
  ref=row['ref'];clone=row['clone'];newast=parse((HERE/('board-delta-r4-c92-pose' if ref=='C11092' else 'board-delta-r3')/(ref+'.footprint-chunk')).read_text(encoding='utf-8'));oldast=parse(oldfps[clone].decode('utf-8'));newpos=list(map(float,child(newast,'at')[1:4]));oldpos=list(map(float,child(oldast,'at')[1:4]));newpos += [0.0] if len(newpos)==2 else [];oldpos += [0.0] if len(oldpos)==2 else [];delta=newpos[2]-oldpos[2]
  def transform(sh):return affinity.translate(affinity.rotate(sh,-delta,origin=tuple(oldpos[:2])),xoff=newpos[0]-oldpos[0],yoff=newpos[1]-oldpos[1])
  padmap={atom(a,'uuid'):b for a,b in zip(children(oldast,'pad'),children(newast,'pad'))}
  added=[]
  for old in [p for p in original['pads'] if p['ref']==clone]:
   p=copy.deepcopy(old);na=padmap[p['uuid']];p['ref']=ref;p['uuid']=atom(na,'uuid');p['net']=atom(na,'net') or '';p['x'],p['y']=transform(Point(p['x'],p['y'])).coords[0];p['layers']={l:polygons(transform(unary_union(poly(ps)))) for l,ps in p['layers'].items()};p['hole']=polygons(transform(unary_union(poly(p['hole'])))) if p['hole'] else None;g['pads'].append(p);added.append(p)
   if p['net']:g['domains_normalized'][norm(p['net'])]='DOM_FIELD_B'
   for layer,ps in p['layers'].items():changedCu.append({'shape':unary_union(poly(ps)),'layer':layer,'net':p['net'],'domain':'DOM_FIELD_B','kind':'new_pad','uuid':p['uuid']})
  oldf=next(f for f in original['footprints'] if f['ref']==clone);newf=copy.deepcopy(oldf);newf.update(ref=ref,value=next(q[2] for q in children(newast,'property') if q[1]=='Value'),x=newpos[0],y=newpos[1]);newf['courtyard']={s:polygons(transform(unary_union(poly(ps)))) for s,ps in oldf['courtyard'].items()};g['footprints'].append(newf)
  # Independent source-bound board chunk positions were previously checked;
  # here ensure the geometry has the same new numbered native pad membership.
  assert {p['num']:norm(p['net']) for p in added if p['num']}==row['pads']
 for row in recipe['new_local_segment_additions']:
  ast=parse(open(row['path'],encoding='utf-8').read());t={'uuid':atom(ast,'uuid'),'net':atom(ast,'net'),'layer':atom(ast,'layer'),'a':list(map(float,child(ast,'start')[1:])),'b':list(map(float,child(ast,'end')[1:])),'w':float(atom(ast,'width'))};g['tracks'].append(t);changedCu.append({'shape':O.S.overlay_tool.base.body(t),'net':t['net'],'layer':t['layer'],'domain':g['domains_normalized'][norm(t['net'])],'kind':'new_track','uuid':t['uuid']})
 # Existing private tracks/vias now have a new net; original foreign fills
 # must clear those geometries too instead of retaining old cached contacts.
 retags={r['uuid'] for r in recipe['private_net_only_replacements']}
 records,_=build(g)
 for layer,rs in records.items():
  for q in rs:
   if q['uuid'] in retags:changedCu.append(q)
 returns=pickle.loads((HERE/'variable-return-r2/prospective-copper.pkl').read_bytes())+pickle.loads((HERE/'triangulated-return-r2/prospective-copper.pkl').read_bytes());changedCu.extend(returns)
 mutual=[]
 for i,a in enumerate(returns):
  for bb in returns[i+1:]:
   if a['layer']!=bb['layer'] or norm(a['net'])==norm(bb['net']):continue
   d=a['shape'].distance(bb['shape']);mutual.append({'a':a['uuid'],'b':bb['uuid'],'layer':a['layer'],'distance_mm':d,'required_mm':.6,'pass':d>=.6+.025-.000001})
 assert all(x['pass'] for x in mutual)
 # This is a prospective vector model, never a saved native-filled board.
 # Each original filled contour loses only an explicit local clearance void.
 # Native filler may differ and every retained relationship is a later gate.
 bylayer={}
 for q in changedCu:bylayer.setdefault(q['layer'],[]).append(q)
 trees={l:O.STRtree([q['shape'] for q in rs]) for l,rs in bylayer.items()};voidrows=[]
 for z in g['zones']:
  for layer,ps in list(z['fills'].items()):
   if layer not in trees:continue
   old=unary_union(poly(ps));voids=[];contacts=[]
   for i in trees[layer].query(old.buffer(.65),predicate='intersects'):
    q=bylayer[layer][i]
    if norm(q['net'])==norm(z['net']):continue
    gap=.15 if q['domain']==g['domains_normalized'][norm(z['net'])] else .6;cut=q['shape'].buffer(gap+.030);area=old.intersection(cut).area
    if area>1e-8:voids.append(cut);contacts.append(identity(q)|{'clearance_mm':gap,'planned_cut_area_mm2':area})
   if not voids:continue
   after=old.difference(unary_union(voids));z['fills'][layer]=polygons(after);voidrows.append({'zone_uuid':z['uuid'],'net_raw':z['net'],'layer':layer,'old_area_mm2':old.area,'new_prospective_area_mm2':after.area,'cut_contacts':contacts,'old_zone_outline_unchanged':True})
 for q in returns:
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller-field-prospective-return-zone-r1/'+q['uuid']));g['zones'].append({'uuid':uid,'net':q['net'],'fills':{q['layer']:polygons(q['shape'])},'outline':polygons(q['shape']),'prospective_not_native':True})
 g['refilled']=False;g['prospective_not_saved_native']=True;g['source_export_sha256']=sha(HERE/'combined-power-source-r3-hierarchy/source-export/fresh.net');g['hierarchy_zero_delta_receipt_sha256']=sha(HERE/'combined-power-source-r3-hierarchy/source-export/receipt-r2.json')
 ground={};cache={}
 for bank in ['FAG','FBG']:
  groups=graph(g,N[bank]);cache[bank]=groups;root=next(i for i,xs in enumerate(groups) if any(x['kind']=='pad' and (x['ref'],x['pin'])==ROOTS[bank] for x in xs));rows=[]
  for i,xs in enumerate(groups):rows.append({'group':i,'rooted':i==root,'pads':sorted([list(q) for q in {(x['ref'],x['pin']) for x in xs if x['kind']=='pad'}]),'layers':sorted({x['layer'] for x in xs})})
  ground[bank]={'real_source':list(ROOTS[bank]),'source_group':root,'groups':rows,'rooted_pads':len(rows[root]['pads']),'remaining_unrooted_pad_groups':sum(bool(x['pads']) and not x['rooted'] for x in rows)};print(bank,'rooted',ground[bank]['rooted_pads'],'unrooted',ground[bank]['remaining_unrooted_pad_groups'],flush=True)
 inputs={'original_geometry_binding':b,'C92_corrected_pose_ledger_sha256':sha(HERE/'board-delta-r4-c92-pose/native-pose-ledger.json'),'hierarchy_zero_delta_receipt_sha256':g['hierarchy_zero_delta_receipt_sha256'],'owned_pad_cuts_sha256':sha(HERE/'owned-pad-cuts-r1/receipt.json'),'field_recipe_sha256':sha(HERE/'candidate-recipe-r1/receipt.json'),'main_A_return_receipt_sha256':sha(HERE/'triangulated-return-r2/receipt.json')};raw=pickle.dumps(g,protocol=5);(OUT/'geometry.pkl').write_bytes(raw);(OUT/'ground-groups.pkl').write_bytes(pickle.dumps(cache,protocol=5));result={'inputs':inputs,'geometry_sha256':hashlib.sha256(raw).hexdigest(),'source_export_sha256':g['source_export_sha256'],'native_jobs':0,'board_written':False,'native_filled_evidence':False,'prospective_foreign_clearance_voids':voidrows,'ground_graph':ground,'mutual_return_clearance_checks':mutual,'original_zone_definitions_preserved':True,'retained_foreign_named_pad_continuity_gate':'PENDING_FULL_GRAPH_AND_NATIVE_REFILL; prospective voids do not prove source loss-free integration','all_source_sinks_connected':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'geometry_sha256':result['geometry_sha256'],'voided_zone_layers':len(voidrows),'new_return_zones':len(returns),'receipt_sha256':sha(OUT/'receipt.json')}))

if __name__=='__main__':main()
