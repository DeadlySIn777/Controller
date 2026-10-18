"""Preserve R23/R24 and derive one scoped ground-barrel/ILIM companion repair."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'remaining_field_ground_feeds_r23.py').read_text()
s=s.replace("OUT=HERE/'remaining-field-ground-feeds-r23'", "OUT=HERE/'u11015-ilim-barrel-repair-r26'")
start=s.index(" assert not OUT.exists();OUT.mkdir();bp=")
end=s.index(" smd=[",start)
setup=''' assert not OUT.exists();OUT.mkdir();bp=HERE/'local-and-b5-return-audit-r25';br=json.loads((bp/'receipt.json').read_text());assert br['verdict']=='PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING';assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());assert sha(bp/'proposed-zones.pkl')==br['proposed_zones_sha256'];planes=pickle.loads((bp/'proposed-zones.pkl').read_bytes());prior=HERE/'u11015-ilim-wall-repair-r24';pr=json.loads((prior/'receipt.json').read_text());owned=pr['owned_original_track_removals'];removed={q['uuid'] for q in owned};assert len(removed)==4
 for t in owned:assert next(q for q in g['tracks'] if q['uuid']==t['uuid'])==t
 g={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};rec,trees=F.build({**g,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\\(rule "(RESERVE_KEEPOUT_[^"]+)" \\(condition "(.*)"\\) \\(constraint disallow track via\\)\\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\\.NetName != '([^']*)'",m[2])}
 ilim='/motherboard_power_entry/AUX24_A_ILIM';ip0=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','7'));ip1=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('R11056','1'));iraw=ip0['net'];assert iraw==ip1['net'];idom=g['domains_normalized'][ilim]
 def igap(other):return .15 if g['domains_normalized'].get(C.norm(other))==idom else .6
 io=[q['shape'].buffer(igap(q['net'])+.025) for q in rec['B.Cu'] if C.norm(q['net'])!=ilim]+[q['shape'].buffer(igap(q['net'])+.025) for q in planes if q['layer']=='B.Cu' and C.norm(q['net'])!=ilim]
 for rule in g['rule_areas']:
  if rule.get('no_tracks') and 'B.Cu' in rule['layers']:io.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
 for rule in res['keepouts']:
  if ilim not in exceptions.get(rule['name'],set()) and 'B.Cu' in rule['layers']:io.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
 it=STRtree(io)
 def restore_ilim(groundbody,disk):
  a,b=nearest_points(ip0['shape'],ip1['shape']);width=.2
  for margin in(3.,8.,16.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=it.query(win,predicate='intersects');legal=win.difference(unary_union([io[int(j)] for j in ii]+[groundbody.buffer(.175),disk.buffer(.175)]));options=[]
   for part in polys(legal.buffer(-width/2-.005)):
    aa=part.buffer(-.00002).intersection(ip0['shape'].buffer(width/2-.025));bb=part.buffer(-.00002).intersection(ip1['shape'].buffer(width/2-.025))
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   if not options:continue
   _,part,aa,bb=min(options,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
   try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
   except(AssertionError,ValueError):continue
   pts=[[round(x,6),round(y,6)] for x,y in points]
   if len(set(tuple(p) for p in pts))<2:continue
   line=LineString(pts);body=line.buffer(width/2,quad_segs=32)
   if not legal.buffer(.000001).covers(body) or body.intersection(ip0['shape']).area<.001 or body.intersection(ip1['shape']).area<.001:continue
   return{'points':pts,'length_mm':line.length,'width_mm':width,'search':search,'body':body}
  return None
'''
s=s[:start]+setup+s[end:]
s=s.replace("[('FB','/motherboard_do/FIELD_B_0V','J11005'),('FA','/motherboard_motors/FIELD_GND','J11003')]", "[('FA','/motherboard_motors/FIELD_GND','J11003')]")
s=s.replace("wanted=[(i,xs) for i,xs in enumerate(groups) if xs is not root and any(q['kind']=='pad' and q['pin'] for q in xs)]", "wanted=[(i,xs) for i,xs in enumerate(groups) if xs is not root and any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','6') for q in xs)];assert len(wanted)==1")
s=s.replace("inner,bridgebody,nativeoutline,bridgeinfo=bridge(disk,hole)", "ir=restore_ilim(rr['body'],disk)\n         if ir is None:continue\n         inner,bridgebody,nativeoutline,bridgeinfo=bridge(disk,hole)")
s=s.replace("controller-field-remaining-r23/", "controller-U11015-ILIM-barrel-r26/")
needle="         (OUT/(uid+'.via-chunk')).write_text"
i=s.index(needle)
s=s[:i]+'''         irids=[]
         for j,(aa,bb) in enumerate(zip(ir['points'],ir['points'][1:])):
          if aa==bb:continue
          sid=str(uuid.uuid5(uuid.UUID(uid),'ILIM-companion'+str(j)));tt={'uuid':sid,'net':iraw,'layer':'B.Cu','a':aa,'b':bb,'w':.2,'prospective_not_native':True};newtracks.append(tt);irids.append(sid);newcu.append({'uuid':sid,'net':iraw,'layer':'B.Cu','shape':C.body(tt)})
          (OUT/(sid+'.segment-chunk')).write_text('\\t(segment\\n\\t\\t(start %.6f %.6f)\\n\\t\\t(end %.6f %.6f)\\n\\t\\t(width %.2f)\\n\\t\\t(layer "B.Cu")\\n\\t\\t(net "%s")\\n\\t\\t(uuid "%s")\\n\\t)\\n'%(*aa,*bb,.2,iraw,sid),encoding='utf-8',newline='')
''' +s[i:]
s=s.replace("'new_segment_UUIDs':uids};break", "'new_segment_UUIDs':uids,'ILIM_restore_route':{k:v for k,v in ir.items() if k!='body'},'ILIM_restore_segment_UUIDs':irids};break")
s=s.replace("'parent_r19_receipt_sha256':sha(bp/'receipt.json')", "'parent_r25_receipt_sha256':sha(bp/'receipt.json'),'scoped_r24_failed_receipt_sha256':sha(prior/'receipt.json'),'owned_original_track_removals':owned,'exact_outside_contact_ledger':pr['exact_outside_contact_ledger'],'source_components_BOM_node_roles_limits_unchanged':True,'RTN_pins_remain_distinct_from_GND6':True")
(P/'repair_u11015_ilim_barrel_r26.py').write_text(s,encoding='utf-8')
compile(s,'repair_u11015_ilim_barrel_r26.py','exec')
print('derived',len(s))
