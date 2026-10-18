"""Bounded width-aware source geometry plan, retaining r07 and250 donor chunks.

No board emission, pcbnew, fill, DRC, Save, GUI or GPU. The complete donor
group is screened; partial successes cannot be presented as a usable donor.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import sys
import time
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import inspect_owned as I
R,S=I.R,I.S
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree

NET=I.NET
DOMAIN='DOM_FIELD_A'
MARGIN=.025
REMOVED_VIAS={
 '4f29b93f-ac4b-4b33-94d6-f6e4eb736f5f':'48bb17dc-e15c-4500-87b2-9784faa6bd96',
 'a85503c0-dd27-44a1-8dc9-57e9123bc63f':'48bb17dc-e15c-4500-87b2-9784faa6bd96',
 'dfcddb57-0806-44fb-8f3b-f97718d7965f':'cdb3618a-92a8-464f-b748-d76db21e7598',
 'f1f6706d-fc73-472a-b3f4-71fcddc45372':'cdb3618a-92a8-464f-b748-d76db21e7598',
}
NETWORKS=[
 {'id':'fault-upper','remove':['0921ba5d-8a1a-42f4-843b-845be32970a4'],
  'anchors':[(353.4,221.4),(359.4,215.8)]},
 {'id':'fault-lower','remove':['4d3903f2-269c-44cd-b493-37f3b83f9fe2','4df1fdfc-5a5f-4816-bf7b-4f196e3f07a2'],
  'anchors':[(358.8,203),(353.3,203.2)]},
 {'id':'logic-upper','remove':['272d7a4c-bcd5-4515-8b40-b46e71518375','8c14d795-e80f-4f9b-9a62-f340fa495a35','f76b2f4b-8e19-4c08-bea9-09dcc11488b2'],
  'anchors':[(377,205.6),(383,203.2),(380.2,199.6)]},
 {'id':'logic-lower','remove':['6f1ad4ab-179e-43b0-a5c7-2851832af907'],
  'anchors':[(367.8,209.8),(364.4,206.2)]},
]

def centre(row):
 return Point(row['at']) if row['kind']=='via' else LineString([row['a'],row['b']])

def radius(row):return row['d']/2 if row['kind']=='via' else row['width']/2

def shape(row):return centre(row).buffer(radius(row))

def exemptions():
 reservations=json.loads(S.read(R.HERE/'reserved-r07.json'))
 rules=S.read(R.HERE/'reserve/board.kicad_dru').decode()
 exempt={}
 for line in rules.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exempt[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 return reservations,exempt

def hole_contact(row,hole,via_index,own_vias):
 """Only geometrically contacted, verified same-net plated via annuli exempt.

 Same-net NPTH/PTH holes are not exempted; neither are nearby uncontacted vias.
 Every accepted exemption is recorded by item and exact existing/owned UUID.
 """
 via=via_index.get(hole.get('uuid')) or own_vias.get(hole.get('uuid'))
 if not via or S.norm(via['net'])!=NET:return False
 at=(via['x'],via['y'])
 if row['kind']=='via' and row['uuid']==via['uuid']:return True
 return shape(row).intersects(Point(at).buffer(via['d']/2))

def audit_row(row,model,via_index,own_vias,barriers):
 line=centre(row);rad=radius(row);body=shape(row);fails=[];contacts=[]
 layers=model.g['copper_layers'] if row['kind']=='via' else [row['layer']]
 for layer in layers:
  for index in model.trees[layer].query(body.buffer(.7+MARGIN)):
   rec=model.records[layer][index]
   if rec['kind']=='hole':
    if hole_contact(row,rec,via_index,own_vias):
     contacts.append({'layer':layer,'hole_uuid':rec['uuid'],'exact_net':NET,
                      'policy':'verified same-net plated annulus contact'})
     continue
    gap=.25
   else:
    if rec['net']==NET:continue
    gap=.15 if rec.get('domain')==DOMAIN else .6
   distance=line.distance(rec['shape'])-rad
   if distance<gap+MARGIN-1e-6:
    fails.append({'layer':layer,'kind':rec['kind'],'uuid':rec.get('uuid'),'net':rec['net'],
                  'gap_mm':distance,'minimum_mm':gap+MARGIN})
  for hard in model.hard.get(layer,[]):
   if NET not in hard['exempt'] and body.buffer(MARGIN).intersects(hard['shape']):
    fails.append({'layer':layer,'kind':hard['kind'],'name':hard['name']})
 if not model.outline.buffer(-.5-MARGIN).covers(body):fails.append({'kind':'outline','minimum_mm':.5+MARGIN})
 if row['kind']=='via':
  for via in list(via_index.values())+list(own_vias.values()):
   if via['uuid']==row['uuid']:continue
   distance=line.distance(Point(via['x'],via['y']))
   if distance<.8-1e-6:fails.append({'kind':'via_spacing','uuid':via['uuid'],'centre_mm':distance,'minimum_mm':.8})
  for area in model.g['rule_areas']:
   if area.get('no_vias') and any(body.buffer(MARGIN).intersects(p) for p in S.poly(area['outline'])):
    fails.append({'kind':'native_no_vias','name':area['name']})
  for foot in model.g['footprints']:
   if foot['ref'] in barriers and any(body.buffer(.6+MARGIN).intersects(p)
      for polygons in foot['courtyard'].values() for p in S.poly(polygons)):
    fails.append({'kind':'barrier_courtyard','ref':foot['ref']})
 # Newly retained through holes also obstruct foreign and uncontacted copper;
 # own annulus contacts are explicit, not a blanket same-net-hole exemption.
 for via in own_vias.values():
  hole={'kind':'hole','uuid':via['uuid']}
  if hole_contact(row,hole,via_index,own_vias):continue
  gap=line.distance(Point(via['x'],via['y']).buffer(via['drill']/2))-rad
  if gap<.25+MARGIN-1e-6:fails.append({'kind':'owned_hole','uuid':via['uuid'],'gap_mm':gap,'minimum_mm':.25+MARGIN})
 return {'uuid':row['uuid'],'kind':row['kind'],'failures':fails,'intentional_plated_contacts':contacts}

def free(model,width,window,via_index,own_vias,allowed_vias):
 """Keep other-net bodies, all unrelated holes, hard barriers and reservations."""
 obstacles=[]
 for i in model.trees['In3.Cu'].query(window.buffer(2),predicate='intersects'):
  rec=model.records['In3.Cu'][i]
  if rec['kind']=='hole':
   if rec.get('uuid') in allowed_vias:
    via=via_index.get(rec['uuid']) or own_vias.get(rec['uuid'])
    if not via or S.norm(via['net'])!=NET:raise ValueError('invalid exact hole attachment')
    continue
   gap=.25
  else:
   if rec['net']==NET:continue
   gap=.15 if rec.get('domain')==DOMAIN else .6
  obstacles.append(rec['shape'].buffer(gap+width/2+MARGIN))
 for via in own_vias.values():
  if via['uuid'] not in allowed_vias:
   obstacles.append(Point(via['x'],via['y']).buffer(via['drill']/2+.25+width/2+MARGIN))
 for hard in model.hard.get('In3.Cu',[]):
  if NET not in hard['exempt']:obstacles.append(hard['shape'].buffer(width/2+MARGIN))
 return window.intersection(model.outline.buffer(-.5-width/2-MARGIN)).difference(unary_union(obstacles))

def exact_path(model,a,b,width,via_index,own_vias,allowed_vias,window):
 f=free(model,width,window,via_index,own_vias,allowed_vias)
 if f.covers(LineString([a,b])):return {'points_mm':[list(a),list(b)]},{'reason':'exact direct line','nodes':0}
 records=[{'uuid':'boundary:'+str(p),'kind':'exact boundary anchor'} for p in (a,b)]
 return S.astar(f,[(tuple(a),records[0])],[(tuple(b),records[1])],time.monotonic()+14,node_cap=40000)

def external_contacts(network,rows,kept):
 """Account retained donor contacts including interior branches, not just ends."""
 removed_lines=[centre(rows[u]) for u in network['remove']]
 blocked=unary_union(removed_lines)
 contacts=[]
 for uid,row in kept.items():
  if row['kind']=='via' or row.get('layer')!='In3.Cu':continue
  line=centre(row)
  # Centreline topology is unambiguous for intended same-net joins. Nearby
  # overlapping wide copper is additionally preserved by whole-group graph.
  if blocked.distance(line)<.000002:
   intersection=blocked.intersection(line.buffer(.000002))
   anchor_ids=[i for i,p in enumerate(network['anchors']) if intersection.distance(Point(p))<.000005]
   contacts.append({'uuid':uid,'centreline_contact_bounds':list(intersection.bounds),
                    'boundary_anchor_indices':anchor_ids})
 return contacts

def connected_boundary_audit(rows,kept,new_rows,networks,removed_vias,via_index):
 """Physical copper graph retains all old owned endpoint relationships."""
 all_rows=list(kept.values())+new_rows
 bodies=[shape(r) for r in all_rows]
 # Retained target annuli are concrete existing nodes; no plane reach claimed.
 targets=sorted(set(removed_vias.values()))
 for uid in targets:
  v=via_index[uid];bodies.append(Point(v['x'],v['y']).buffer(v['d']/2))
 parent=list(range(len(bodies)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 tree=STRtree(bodies)
 for i,body in enumerate(bodies):
  for j in tree.query(body.buffer(.000002),predicate='intersects'):
   if i<j and body.distance(bodies[j])<.000002:parent[find(i)]=find(j)
 def roots_at(p):return {find(i) for i in tree.query(Point(p).buffer(.000002),predicate='intersects')}
 result=[]
 for n in networks:
  roots=[roots_at(p) for p in n['anchors']]
  common=set.intersection(*roots) if roots else set()
  result.append({'id':n['id'],'anchors':n['anchors'],'all_boundary_anchors_connected':bool(common)})
 for uid,target in removed_vias.items():
  at=rows[uid]['at'];v=via_index[target];common=roots_at(at)&roots_at((v['x'],v['y']))
  result.append({'removed_via':uid,'retained_target':target,'old_via_site_connected_to_target':bool(common)})
 return result

def main():
 destination=HERE/'repair-plan.json'
 if destination.exists():raise ValueError('Use a distinct immutable result name for a repeated plan')
 for p in (Path(__file__),Path(I.__file__),Path(R.__file__),Path(S.__file__),
           Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),
           Path(R.composition.__file__),Path(R.composition.pcbtext.__file__),R.PRO,R.DRU,
           HERE.parent/'fag-r06/final-proof.json',HERE.parent/'fag-r07-repair-independent-vias.json'):
  S.read(p)
 rows,screen=I.own_additions();g,_,overlay=R.overlay_and_targets()
 reservations,exempt=exemptions();print('MODEL_START',flush=True)
 model=S.Model(g,reservations,exempt);print('MODEL_READY',flush=True)
 via_index={v['uuid']:v for v in g['vias']}
 removed=set(REMOVED_VIAS)|{u for n in NETWORKS for u in n['remove']}
 failed={r['uuid'] for r in screen['rows'] if r['failures']}
 if len(removed)!=11 or failed!=removed:raise ValueError('11 exact owned failure identities differ')
 kept={u:r for u,r in rows.items() if u not in removed}
 if len(kept)!=250:raise ValueError('Retained donor group count differs')
 own_vias={u:{'uuid':u,'net':NET,'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill']} for u,r in kept.items() if r['kind']=='via'}
 barriers={r['refdes'] for r in json.loads(S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
 new_rows=[];plans=[];contacts=[]
 for uid,target in REMOVED_VIAS.items():
  v=via_index[target]
  if S.norm(v['net'])!=NET or v['d']!=.6 or v['drill']!=.3:raise ValueError('via reuse identity/geometry differs')
  a=rows[uid]['at'];b=(v['x'],v['y']);window=LineString([a,b]).envelope.buffer(2,cap_style=3).envelope
  path,search=exact_path(model,a,b,.8,via_index,own_vias,{target},window)
  record={'id':'reuse-'+uid,'remove_via':uid,'retained_via':target,'retained_via_at':b,
          'retained_diameter_mm':v['d'],'retained_drill_mm':v['drill'],'window':list(window.bounds),
          'width_mm':.8,'layer':'In3.Cu','path':path,'search':search}
  plans.append(record)
  if path:
   for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
    new_rows.append({'uuid':'PLAN:'+record['id']+':'+str(i),'kind':'segment','net':NET,'layer':'In3.Cu','width':.8,'a':a,'b':b})
  print(record['id'],search,flush=True)
 for network in NETWORKS:
  boundary=external_contacts(network,rows,kept);contacts.append({'id':network['id'],'retained_contacts':boundary})
  omitted=[r for r in boundary if not r['boundary_anchor_indices']]
  window=unary_union([centre(rows[u]) for u in network['remove']]).envelope.buffer(8,cap_style=3).envelope
  record={**network,'window':list(window.bounds),'width_mm':.3,'layer':'In3.Cu','paths':[],
          'omitted_boundary_contacts':omitted}
  # No silently discarded interior unblocked branch is permissible.
  if not omitted:
   for endpoint in network['anchors'][1:]:
    path,search=exact_path(model,network['anchors'][0],endpoint,.3,via_index,own_vias,set(),window)
    record['paths'].append({'path':path,'search':search})
    if path:
     pi=len(record['paths'])-1
     for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
      new_rows.append({'uuid':'PLAN:'+network['id']+':'+str(pi)+':'+str(i),'kind':'segment','net':NET,'layer':'In3.Cu','width':.3,'a':a,'b':b})
  plans.append(record);print(network['id'],record.get('omitted_boundary_contacts'),[p['search'] for p in record['paths']],flush=True)
 audit=[audit_row(r,model,via_index,own_vias,barriers) for r in list(kept.values())+new_rows]
 boundary_audit=connected_boundary_audit(rows,kept,new_rows,NETWORKS,REMOVED_VIAS,via_index)
 complete=all(r.get('path') is not None for r in plans[:4]) and all(
  not r['omitted_boundary_contacts'] and len(r['paths'])==len(r['anchors'])-1 and all(p['path'] for p in r['paths']) for r in plans[4:])
 bad=[r for r in audit if r['failures']]
 connected=all(r.get('all_boundary_anchors_connected',r.get('old_via_site_connected_to_target',False)) for r in boundary_audit)
 for p,sha in S.READS.items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha:raise ValueError('Input changed:'+p)
 report={'schema':'fag-r07-owned-repair-plan-v1','scope':'Partial96mA FIELD_A return; full field model OPEN',
         'verdict':'HOST_WHOLE_GROUP_GEOMETRY_PASS_NATIVE_OPEN' if complete and not bad and connected else 'HOST_WHOLE_GROUP_WITHHELD',
         'r07_sha256':R.R07_SHA,'donor_sha256':screen['donor_sha256'],'overlay':overlay,
         'removed_owned_uuids':sorted(removed),'retained250_sha256':{u:r['chunk_sha256'] for u,r in kept.items()},
         'all_r07_copper_preserved':True,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,
         'new_vias':0,'retained_new_vias':len(own_vias),'new_segment_count':len(new_rows),
         'all_paths_found':complete,'all_boundary_relationships_preserved':connected,
         'failing_item_count':len(bad),'plans':plans,'new_segments':new_rows,
         'boundary_contacts':contacts,'boundary_audit':boundary_audit,'whole_group_audit':audit,
         'source_files_sha256':S.READS,'limits':[
          'No board is composed; every partial search result is withheld unless the entire group passes',
          'Retained r06 foreign refilled geometry conservatively overlays exact actual r07 tracks/vias/poses',
          'No fresh r07 fill or rooted plane equivalence is claimed',
          'Exact verified same-net plated via annulus contacts are logged; all other hole clearance uses0.25mm+0.025margin',
          'Cross-domain0.6mm+0.025margin; same-domain0.15mm+0.025margin; via centre spacing0.8mm',
          'Existing barriers, reserved corridors and native rule areas retained',
          '0.1mm grid,40000node/14sec bounded search; no-path does not establish global impossibility',
          'Native r07 no-loss/DRC/refill/source-anchored return and full current/sharing/thermal/fault proof remain OPEN']}
 destination.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'verdict':report['verdict'],'complete':complete,'failing_items':len(bad),'connected':connected,'new_segments':len(new_rows),
                   'failures':[r for r in bad]},indent=1),flush=True)

if __name__=='__main__':main()
