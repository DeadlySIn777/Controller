"""Independent actual scoped COM refill reference/contact check; no native jobs."""
import sys,json,math,time,copy
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
def native_mm(v):return float((Decimal(str(v))*Decimal(1000000)).to_integral_value(rounding=ROUND_HALF_UP)/Decimal(1000000))
def native_at(v):return tuple(native_mm(x) for x in v)
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_reference_coupled_mon_r4 as R
from shapely.geometry import Point
from shapely.ops import unary_union
A,P,G,S,C,F,N=R.A,R.P,R.G,R.S,R.C,R.F,R.N
Q=R.Q;COM,VREF,SDI=Q.COM,Q.VREF,Q.SDI
def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for x in sh.geoms for p in vertices(x)]
def main():
 start=time.monotonic();out=HERE/'ao1-native-com-reference-independent-r2.json';assert not out.exists()
 d=HERE.parent/'ao1-native-diagnostic-r1/scoped-native-fill';rr=json.loads(A.read(d/'receipt.json'));ngraw=A.read(d/'geometry.json');flashraw=A.read(d/'actual-via-flashes.json')
 assert C.sha(ngraw)==rr['geometry_sha256']=='5405473a4b6f55dda52f03f2328cfa282bc57784d18530d010bb135d2dcde15c'
 assert C.sha(flashraw)==rr['actual_via_flashes_sha256']=='eb9bbc9f6a29e8179704b425cb9826093be97e9af7cae23ecd1f536e8372e82d'
 for p,pin in rr['input_sha256'].items():assert C.sha(A.read(p))==pin,p
 ng=json.loads(ngraw);nf=json.loads(flashraw);nm={u:set(ls) for u,ls in nf['vias'].items()}
 rec=json.loads(A.read(HERE/'ao1-reference-coupled-r18.json'));host=json.loads(A.read(HERE/'ao1-reference-coupled-r18-independent-mon-r4.json'))
 assert C.sha(A.read(HERE/'ao1-reference-coupled-r18.json'))=='dec4321581a1d9e3cdab41f556804e45469ff3a82850f772a5e22a98362e206f'
 assert C.sha(A.read(HERE/'ao1-reference-coupled-r18-independent-mon-r4.json'))=='e06e6692d3c03be118a741205fe691fe929ae91c5ee4c8e467fba48660d120f9'
 for p,pin in host['read_files_sha256'].items():assert C.sha(Path(p).read_bytes())==pin,p
 raw=A.read(G.SOURCE);assert C.sha(raw)==A.SOURCE_SHA;now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));ident=N.SourceNets(raw)
 native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
 sm={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
 new={u:ch.encode() for u,ch in rec['exact_new_chunks'].items()};removed=set(rec['removed_owned_items']);chunks={u:ch for u,ch in now[4].items() if u not in removed};chunks.update(new);ident.assert_chunks(chunks)
 parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};preserved=host['independent_preserved_source_MON_piece']['uuid'];signals={z['net']:z for z in parsed.values() if z['kind']=='via' and z['net'] in(VREF,SDI)}
 g=ident.geometry(chunks,template);gv={v['uuid']:v for v in g['vias']};nt={t['uuid']:t for t in ng['tracks']};nv={v['uuid']:v for v in ng['vias']}
 native_discrete=[]
 for u,z in parsed.items():
  n=nv[u] if z['kind']=='via' else nt[u]
  assert n['net']==ident.raw(z['net']),u
  if z['kind']=='via':
   assert tuple(n['at'])==tuple(z['at']) and(n['w'],n['drill'])==(z['d'],z['drill']) and nm[u]==set(g['copper_layers']),u
   sm[u]=nm[u]
  else:
   assert tuple(n['s'])==native_at(z['a']) and tuple(n['e'])==native_at(z['b']) and n['w']==z['w'] and n['layer']==z['layer'],u
   z['a'],z['b']=list(n['s']),list(n['e'])
   target=next(t for t in g['tracks'] if t['uuid']==u);target['a'],target['b']=list(n['s']),list(n['e'])
  native_discrete.append({'uuid':u,'kind':z['kind'],'exact_raw_native_geometry_and_declared_1nm_lattice':True,'actual_flash_layers':sorted(nm[u]) if z['kind']=='via' else None})
 # Every actual COM discrete entity must be the exact source entity or one of
 # the two registered new returns; native source parity already binds pad UUID.
 compads=[p for p in g['pads'] if S.norm(p['net'])==COM];actualpads=[p for p in ng['pads'] if S.norm(p['net'])==COM]
 assert len(compads)==len(actualpads)
 lookup={(p['ref'],p['num']):p for p in actualpads};assert len(lookup)==len(actualpads)
 for p in compads:
  n=lookup[p['ref'],p['num']];assert p['net']==n['net'] and math.dist((p['x'],p['y']),n['at'])<.000001 and set(p['layers'])==set(n['layers'])
  if n['layers']:p['layers'][n['layers'][0]]=A.polys(n['poly'])
 comvias={u:v for u,v in gv.items() if S.norm(v['net'])==COM};assert set(comvias)=={u for u,v in nv.items() if S.norm(v['net'])==COM}
 for u,v in comvias.items():
  n=nv[u];assert ident.raw(v['net'])==n['net'] and(v['x'],v['y'],v['d'],v['drill'])==(n['at'][0],n['at'][1],n['w'],n['drill']);sm[u]=nm[u]
 comtracks={t['uuid']:t for t in g['tracks'] if S.norm(t['net'])==COM};assert set(comtracks)=={u for u,t in nt.items() if S.norm(t['net'])==COM}
 for u,t in comtracks.items():
  n=nt[u];assert ident.raw(t['net'])==n['net'] and tuple(t['a'])==tuple(n['s']) and tuple(t['b'])==tuple(n['e']) and t['w']==n['w'] and t['layer']==n['layer']
 zones={z['uuid']:z for z in ng['zones'] if S.norm(z['net'])==COM};assert set(zones)==set(rr['selected_zone_UUIDs'])
 assert set(zones)=={z['uuid'] for z in g['zones'] if S.norm(z['net'])==COM}
 for z in g['zones']:
  if z['uuid'] in zones:
   n=zones[z['uuid']];assert z['net']==n['net'] and z['layers']==n['layers'];z['fills']={l:A.polys(rs) for l,rs in n['fills'].items()}
 reserve,exempt=A.reservations();print('NATIVE_COM_EXACT_SOURCE_MODEL',flush=True)
 base=F.Model(ident.geometry(now[4],template),reserve,exempt,native['vias'],{u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()})
 print('NATIVE_COM_FRESH_EXACT_REFERENCE_MODEL',flush=True)
 sourcevias=[v for v in native['vias'] if v['uuid'] not in removed]+[nv[u] for u,z in parsed.items() if z['kind']=='via']
 final=F.Model(g,reserve,exempt,sourcevias,sm)
 refs,witness,uf,rows=Q.rooted_reference(final,sm,ident.raw(COM));oldrefs,oldw,olduf,oldrows=Q.rooted_reference(base,{u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()},ident.raw(COM))
 gaps=Q.zone_gaps(now);reference=[];errors=[];gapdir=HERE/'ao1-native-com-reference-independent-r2-gaps';gapdir.mkdir()
 for u,z in parsed.items():
  if z['kind']!='segment' or u==preserved:continue
  v=signals.get(z['net']);plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';required=max([.15]+[gaps[r['uuid']] for r in base.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].distance(Point(v['at']).buffer(.25) if v else A.shape(z))<=max(.15,gaps[r['uuid']])+.025])
  radius=.25+required+.025 if v else 0.;uncovered=A.shape(z).difference(Point(v['at']).buffer(radius,resolution=128) if v else Point().buffer(0)).difference(refs[z['layer']]);pts=vertices(uncovered)
  analytic=bool(v and pts and max(math.dist(p[:2],v['at']) for p in pts)<=radius)
  row={'uuid':u,'net':z['net'],'layer':z['layer'],'own_transition_uuid':v['uuid'] if v else None,'own_unchanged_void_radius_mm':radius,'actual_native_full_body_uncovered_mm2':uncovered.area,'bounds_mm':list(uncovered.bounds) if pts else [],'all_gap_vertices_inside_exact_own_analytic_disk':analytic,'reference_pass':uncovered.area<=1e-9 or analytic}
  if not row['reference_pass']:
   p=gapdir/(u+'.wkb');p.write_bytes(uncovered.wkb);row.update(gap_WKB_path=str(p),gap_WKB_SHA256=C.sha(uncovered.wkb));errors.append(row)
  reference.append(row)
 retained=[];neighborloss=[];sclk=[]
 for l,xs in base.records.items():
  if l not in refs:continue
  for r in xs:
   if r['kind']!='track' or r['uuid'] in removed or r.get('domain')!=base.domains[COM] or r['net']==COM:continue
   lost=r['shape'].intersection(oldrefs[l]).difference(refs[l]);row={'uuid':r['uuid'],'net':r['net'],'layer':l,'previously_source_rooted_reference_lost_mm2':lost.area,'original_uncovered_mm2':r['shape'].difference(oldrefs[l]).area,'actual_final_uncovered_mm2':r['shape'].difference(refs[l]).area}
   if lost.area>1e-9:neighborloss.append(row)
   if 'AO1_DAC_SCLK' in r['net']:sclk.append(row)
 pbody=A.shape(parsed[preserved]);lost=pbody.intersection(oldrefs['F.Cu']).difference(refs['F.Cu']);retained={'uuid':preserved,'actual_final_uncovered_mm2':pbody.difference(refs['F.Cu']).area,'previously_source_rooted_reference_lost_mm2':lost.area,'baseline_unreferenced_MON_preserved':True}
 returns=[]
 for net,sig in signals.items():
  choices=[]
  for u,v in comvias.items():
   dist=math.dist(sig['at'],(v['x'],v['y']))
   if not .81-1e-9<=dist<=1.+1e-9 or not {'In1.Cu','In4.Cu'}<=nm[u]:continue
   p=Point(v['x'],v['y']);ann=p.buffer(v['d']/2,resolution=128).difference(p.buffer(v['drill']/2,resolution=128));areas={l:refs[l].buffer(-.075).intersection(ann).area for l in('F.Cu','B.Cu')}
   choices.append({'uuid':u,'at_mm':[v['x'],v['y']],'distance_mm':dist,'actual_native_flash_layers':sorted(nm[u]),'source_rooted_finite_annular_interior_mm2':areas,'pass':all(x>=.004 for x in areas.values())})
  returns.append({'net':net,'signal_uuid':sig['uuid'],'choices':choices,'pass':any(c['pass'] for c in choices)})
 # Complete retained source COM pad/Cu relationships, using distinct physical
 # fill keys and drill-subtracted annuli. Holes receive no connectivity credit.
 oldroot=olduf.find(('p',Q.ANCHOR));newroot=uf.find(('p',Q.ANCHOR));missing=[]
 for l,xs in oldrows.items():
  for r in xs:
   if r['kind']=='fill' or olduf.find(r['key'])!=oldroot:continue
   if uf.find(r['key'])!=newroot:missing.append({'layer':l,'key':list(r['key']),'uuid':r['uuid']})
 passed=not(errors or neighborloss or missing) and lost.area<=1e-9 and all(r['pass'] for r in returns)
 report={'verdict':'INDEPENDENT_NATIVE_SCOPED_COM_REFERENCE_RETURN_AND_RETAINED_CONTACT_PASS' if passed else 'INDEPENDENT_NATIVE_SCOPED_COM_REFERENCE_INCOMPLETE','native_scope':'Only eight actual AO1_COM zones freshly filled; no other stored zone refill credit','native_candidate_sha256':rr['candidate_sha256'],'fresh_native_geometry_sha256':C.sha(ngraw),'fresh_native_actual_flash_sha256':C.sha(flashraw),'all20_exact_new_native_geometry':native_discrete,'all_actual_COM_discrete_bound':{'pads':len(compads),'vias':len(comvias),'tracks':len(comtracks)},'functional_source_root_witness':witness,'new_signal_reference':reference,'reference_errors':errors,'unchanged_reference_losses':neighborloss,'unchanged_SCLK_reference':sclk,'preserved_MON':retained,'paired_returns':returns,'lost_prior_source_rooted_COM_discrete_contacts':missing,'reference_PASS':passed,'whole_board_no_loss_DRC_SI_analog_PDN_thermal_final_power':'OPEN','adopted':False,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-start}
 for p,pin in A.READS.items():assert C.sha(Path(p).read_bytes())==pin,p
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'reference_errors':len(errors),'unchanged_reference_losses':len(neighborloss),'contact_losses':len(missing),'returns':[r['pass'] for r in returns],'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
