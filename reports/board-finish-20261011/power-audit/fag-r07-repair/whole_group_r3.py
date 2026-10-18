"""Read-only fullgroup closure; preserves exact donor/native inherited evidence.

No board is emitted. Only a complete conservative geometry/contact closure
can authorize the separate staged constructor; native no-loss remains open.
"""
from pathlib import Path
import hashlib
import json
import sys
sys.dont_write_bytecode=True
import plan_repair as P
from shapely.geometry import Point
from shapely.strtree import STRtree

TARGET=P.S.ROOT/'recovery-composite/c06/four-path/r07-four-path.kicad_pcb'
TARGET_SHA='b4f56daf9d5d7579b155e1a76a0566f7d28c4892c78bdecf7edd3dd18f56ae60'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def parse_copper(uid,ch):
 kind=P.R.composition.pcbtext.chunk_kind(ch);net=P.S.norm(P.S.overlay_tool.netname(ch))
 if kind=='via':
  if b'(layers "F.Cu" "B.Cu")' not in ch or b'(via blind' in ch:raise ValueError('unmodeled via span')
  return {'uuid':uid,'kind':kind,'net':net,'at':P.S.overlay_tool.numbers(ch,'at'),
          'd':P.S.overlay_tool.scalar(ch,'size'),'drill':P.S.overlay_tool.scalar(ch,'drill')}
 if kind=='segment':return {'uuid':uid,'kind':kind,'net':net,'a':P.S.overlay_tool.numbers(ch,'start'),
                          'b':P.S.overlay_tool.numbers(ch,'end'),'width':P.S.overlay_tool.scalar(ch,'width'),
                          'layer':P.R.composition.pcbtext.chunk_layer(ch)}
 raise ValueError('unsupported new copper')

class ContactGraph:
 """Physical same-layer contacts; only verified plated vias join layers."""
 def __init__(self,records):
  self.records=records;self.parent=list(range(len(records)));self.bykey={};self.bylayer={}
  for i,r in enumerate(records):
   self.bykey.setdefault(r['key'],[]).append(i);self.bylayer.setdefault(r['layer'],[]).append(i)
  for key,ids in self.bykey.items():
   if records[ids[0]]['kind']=='via':
    for i in ids[1:]:self.join(ids[0],i)
  for layer,ids in self.bylayer.items():
   tree=STRtree([records[i]['shape'] for i in ids])
   for local,i in enumerate(ids):
    body=records[i]['shape']
    for j in tree.query(body.buffer(.000002),predicate='intersects'):
     other=ids[j]
     if i<other and body.distance(records[other]['shape'])<=.000002:self.join(i,other)
 def find(self,i):
  while self.parent[i]!=i:self.parent[i]=self.parent[self.parent[i]];i=self.parent[i]
  return i
 def join(self,a,b):self.parent[self.find(a)]=self.find(b)
 def roots(self,key):return {self.find(i) for i in self.bykey.get(key,[])}

def graph_records(rows,model,via_index):
 records=[]
 for r in rows:
  # New/retained donor vias use exact through spans established by parsing;
  # tracks have precisely one declared layer. XY projection never joins them.
  layers=model.g['copper_layers'] if r['kind']=='via' else [r['layer']]
  if r['kind']=='via' and r['uuid'] in via_index:
   v=via_index[r['uuid']]
   if v['span']!=['F.Cu','B.Cu'] or not set(v['flashed'])<=set(model.g['copper_layers']):raise ValueError('retained via layer geometry unsupported')
   layers=v['flashed']
  for layer in layers:records.append({'key':r['uuid'],'kind':r['kind'],'layer':layer,'shape':P.shape(r)})
 # Exact retained actualr07 FIELD pads/tracks/vias provide real old contacts;
 # fills are deliberately excluded from this source copper continuity proof.
 for layer,recs in model.records.items():
  for r in recs:
   if r['net']!=P.NET or r['kind'] not in('pad','track','via'):continue
   if r['kind']=='via':
    v=via_index.get(r['uuid'])
    if not v or v['span']!=['F.Cu','B.Cu'] or not set(v['flashed'])<=set(model.g['copper_layers']):
     raise ValueError('native via actual flashed/span evidence missing')
    if layer not in v['flashed']:continue
   key=('native-pad:'+r['pad_id']) if r['kind']=='pad' else ('native:'+r['uuid'])
   records.append({'key':key,'kind':r['kind'],'layer':layer,'shape':r['shape']})
 return records

def contact_closure(original,retained,replacement,model,via_index):
 old=ContactGraph(graph_records(list(original.values()),model,via_index))
 new=ContactGraph(graph_records(list(retained.values())+replacement,model,via_index))
 surviving=set(old.bykey)&set(new.bykey)
 groups={}
 for key in surviving:
  for root in old.roots(key):groups.setdefault(root,set()).add(key)
 losses=[]
 for root,keys in groups.items():
  # A pad with no modelled plated link can appear on multiple layers; each old
  # physical component is checked by its real layer, avoiding dummy pad unions.
  mapped=set()
  for i,r in enumerate(old.records):
   if old.find(i)!=root or r['key'] not in surviving:continue
   matches=[j for j in new.bykey[r['key']] if new.records[j]['layer']==r['layer']]
   mapped.update(new.find(j) for j in matches)
  if len(mapped)>1:losses.append({'prior_component':root,'surviving_keys':sorted(keys),'after_components':len(mapped)})
 # All original retained contacts through removed items are therefore captured,
 # including broad copper overlaps and interior joins on every actual layer.
 return {'surviving_physical_keys':len(surviving),'old_component_count':len(groups),
         'lost_physical_relationship_components':losses,'all_prior_retained_physical_relationships_preserved':not losses,
         'old_node_count':len(old.records),'new_node_count':len(new.records),
         'fill_contacts_included':False,'layer_join_policy':'only verified plated through-via nodes'}

def inherited_hole_provenance(row,audit,base,donor,live,owned,proof):
 receipts=[]
 for f in audit['failures']:
  if f['kind'] not in('hole','owned_hole') or f.get('net',P.NET)!=P.NET:raise ValueError('not an inherited same-net hole contact')
  uid=f['uuid'];source=None;kind=None
  if uid in base[4] and donor[4].get(uid)==base[4][uid] and live[4].get(uid)==base[4][uid]:
   source=base[4][uid];kind='retained original through-via'
  elif uid in owned and owned[uid]['kind']=='via' and uid in donor[4]:
   source=donor[4][uid];kind='unchanged owned donor through-via'
  else:
   # Pads are children inside native footprint chunks. Pin the entire exact
   # footprint so no changed pose/copper/drill can inherit an earlier result.
   candidates=[ch for ch in base[1] if P.R.composition.pcbtext.chunk_kind(ch)=='footprint' and uid.encode() in ch]
   if len(candidates)==1 and candidates[0] in donor[1] and candidates[0] in live[1]:
    source=candidates[0];kind='unchanged native footprint containing exact same-net pad'
  if source is None:raise ValueError('hole geometry was not native inherited:'+uid)
  if uid in owned and owned[uid]['net']!=P.NET:raise ValueError('different-net owned hole')
  receipts.append({'item_uuid':row['uuid'],'item_chunk_sha256':row['chunk_sha256'],
                   'hole_uuid':uid,'hole_source_kind':kind,'hole_source_chunk_sha256':sha(source),
                   'exact_net':P.NET,'conservative_gap_mm':f['gap_mm'],'strict_minimum_mm':f['minimum_mm'],
                   'native_donor_sha256':proof['candidate_sha256'],'native_raw_drc_errors':proof['drc']['after']['errors'],
                   'scope':'Only this unchanged pair of native geometries; no new-copper/hole/domain waiver'})
 return receipts

def main():
 destination=P.HERE/'whole-group-audit-r3.json'
 if destination.exists():raise ValueError('distinct immutable receipt required')
 for p in(Path(__file__),Path(P.__file__),Path(P.I.__file__),Path(P.R.__file__),Path(P.S.__file__),
          Path(P.S.overlay_tool.__file__),Path(P.S.overlay_tool.base.__file__),Path(P.R.composition.__file__),
          Path(P.R.composition.pcbtext.__file__),P.R.PRO,P.R.DRU):P.S.read(p)
 first=json.loads(P.S.read(P.HERE/'repair-plan.json'));alternate=json.loads(P.S.read(P.HERE/'alternate-lower.json'))
 terminal=json.loads(P.S.read(P.HERE/'terminal-fix.json'))
 if terminal['selected'] is None or terminal['all_new_copper_clearance_exceptions']:
  raise ValueError('strict terminal fix absent')
 # Pin and validate each producer's exact live read set, including failedr1.
 for receipt in(first,alternate,terminal):
  for path,expected in receipt['source_files_sha256'].items():
   if sha(P.S.read(path))!=expected:raise ValueError('producer source differs:'+path)
 rows,screen=P.I.own_additions();g,_,overlay=P.R.overlay_and_targets()
 base=P.R.composition.inventory(P.S.read(P.S.overlay_tool.base.BASE));donor=P.R.composition.inventory(P.S.read(P.I.DONOR))
 live=P.R.composition.inventory(P.S.read(P.R.R07));targetraw=P.S.read(TARGET)
 # The obstacle overlay deliberately overprojects through-via annuli for
 # clearance. The contact graph requires actual native FlashLayer evidence.
 native_geometry=json.loads(P.S.read(P.S.overlay_tool.base.GEOM))
 native_field_vias={v['uuid']:v for v in native_geometry['vias'] if P.S.norm(v['net'])==P.NET}
 actual_via_layers={}
 for via in g['vias']:
  if P.S.norm(via['net'])!=P.NET:continue
  uid=via['uuid'];observed=native_field_vias.get(uid)
  if not observed or live[4].get(uid)!=base[4].get(uid) or uid not in base[4]:
   raise ValueError('native FIELD via not byte-exact inherited geometry:'+uid)
  if observed['span']!=g['copper_layers'] or observed['type']!=4 or not observed['flashed'] or not set(observed['flashed'])<=set(g['copper_layers']):
   raise ValueError('invalid native FIELD span/flash evidence:'+uid)
  if any(via[k]!=observed[k] for k in('x','y','d','drill')):raise ValueError('native FIELD via coordinates differ:'+uid)
  via['flashed']=observed['flashed'];actual_via_layers[uid]=observed['flashed']
 if len(actual_via_layers)!=len(native_field_vias):raise ValueError('inherited FIELD via set differs')
 if sha(targetraw)!=TARGET_SHA:raise ValueError('four-path target identity differs')
 target=P.R.composition.inventory(targetraw)
 if target[0]!=live[0] or target[2]!=live[2] or target[5]!=live[5] or any(target[3].get(u)!=ch for u,ch in live[3].items()):raise ValueError('four-path target is not exact pure-add r07')
 targetadd={u:ch for u,ch in target[4].items() if u not in live[4]}
 if len(targetadd)!=18:raise ValueError('four-path target delta differs')
 targetrows=[parse_copper(u,ch) for u,ch in targetadd.items()]
 for r in targetrows:
  if r['kind']=='via':
   g['vias'].append({'uuid':r['uuid'],'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],
                    'span':['F.Cu','B.Cu'],'flashed':g['copper_layers']})
  else:g['tracks'].append({'uuid':r['uuid'],'net':r['net'],'a':r['a'],'b':r['b'],'w':r['width'],'layer':r['layer']})
 for name in('construction.json','audit.json'):P.S.read(TARGET.parent/name)
 proofpath=P.HERE.parent/'fag-r06/final-proof.json';proof=json.loads(P.S.read(proofpath))
 if proof['native_drc_connectivity_verdict']!='PASS' or proof['candidate_sha256']!=screen['donor_sha256'] or proof['drc']['after']['errors']!=0 or proof['drc']['after']['kicad']!='10.0.4':raise ValueError('native inherited proof invalid')
 rawpath=P.HERE.parent/'fag-r06/measure/drc.json';raw=P.S.read(rawpath)
 if proof['evidence_sha256'].get(str(rawpath.resolve()))!=sha(raw):raise ValueError('raw inherited DRC identity differs')
 rawdrc=json.loads(raw)
 if any(r.get('severity')=='error' for r in rawdrc['violations']):raise ValueError('raw inherited DRC has error')
 for name,p in(('board.kicad_pro',P.R.PRO),('board.kicad_dru',P.R.DRU)):
  if sha(P.S.read(p))!=proof['project_manifests']['after'][name]['sha256']:raise ValueError('rules/project differ from native inherited proof')
 removed=set(P.REMOVED_VIAS)|{u for n in P.NETWORKS for u in n['remove']}
 kept={u:r for u,r in rows.items() if u not in removed}
 if len(kept)!=250 or len(removed)!=11 or set(first['removed_owned_uuids'])!=removed:raise ValueError('owned250/11 delta differs')
 replacements=list(first['new_segments'])
 # Failed first353.3 ties are omitted: their original retained .8mm stub has
 # verified physical contact to48bb; this adds no new geometry or waiver.
 selected={**alternate['selected'],'segments':[alternate['selected']['segments'][0],terminal['selected']]}
 if selected is None or selected['new_vias']!=1 or selected['layer_segments']!=3:raise ValueError('bounded alternate not found')
 replacements.append(selected['new_via'])
 for pi,path in enumerate(selected['segments']):
  for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
   replacements.append({'uuid':'PLAN:alternate:'+str(pi)+':'+str(i),'kind':'segment','net':P.NET,
                        'layer':path['layer'],'width':path['width_mm'],'a':a,'b':b})
 if len({r['uuid'] for r in replacements})!=len(replacements):raise ValueError('duplicate plan identities')
 reservations,exempt=P.exemptions();print('MODEL_START',flush=True)
 model=P.S.Model(g,reservations,exempt);print('MODEL_READY',flush=True)
 via_index={v['uuid']:v for v in g['vias']}
 own_vias={r['uuid']:{'uuid':r['uuid'],'net':P.NET,'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill']}
           for r in list(kept.values())+replacements if r['kind']=='via'}
 barriers={r['refdes'] for r in json.loads(P.S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
 audit=[];inherited=[];bad=[]
 for r in list(kept.values())+replacements:
  a=P.audit_row(r,model,via_index,own_vias,barriers)
  if a['failures']:
   if r['uuid'] in kept:
    try:provenance=inherited_hole_provenance(r,a,base,donor,live,rows,proof)
    except ValueError:bad.append(a)
    else:inherited+=provenance;a['inherited_same_net_native_provenance']=provenance
   else:bad.append(a)
  audit.append(a)
 graph=contact_closure(rows,kept,replacements,model,via_index)
 passed=not bad and graph['all_prior_retained_physical_relationships_preserved']
 for path,expected in P.S.READS.items():
  if sha(Path(path).read_bytes())!=expected:raise ValueError('input changed:'+path)
 output={'schema':'fag-r07-repaired-whole-group-v3','verdict':'HOST_WHOLE_GROUP_PASS_NATIVE_OPEN' if passed else 'HOST_WHOLE_GROUP_WITHHELD',
         'scope':'Partial0.096A FIELD_A return only; full field current/load/sharing/thermal/fault OPEN',
         'r07_sha256':P.R.R07_SHA,'combined_target_sha256':TARGET_SHA,'combined_target_path':str(TARGET),
         'donor_sha256':screen['donor_sha256'],'overlay':overlay,'preserve_all_target_items_exact':True,
         'target_additional_copper':{u:sha(ch) for u,ch in targetadd.items()},
         'retained250_chunks_sha256':{u:r['chunk_sha256'] for u,r in kept.items()},'removed11_owned_uuids':sorted(removed),
         'retained_vias':4,'new_vias':1,'replacement_segments':18,'final_donor_copper_items':len(kept)+len(replacements),
         'replacements':replacements,'audit':audit,'inherited_same_net_provenance':inherited,
         'layer_correct_physical_contact_closure':graph,'actual_native_FIELD_via_flashed_layers':actual_via_layers,
         'suppressed_annulus_vias':sum(len(layers)!=len(g['copper_layers']) for layers in actual_via_layers.values()),'failing_items':bad,
         'new_copper_clearance_exceptions':False,'source_files_sha256':P.S.READS,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,
         'adopted':False,'manufacturing_ready':False,
         'limits':['Strict new copper:0.25mm hole/.6mm cross-domain/.15mm same-domain plus.025margin;0.8mmvia spacing',
                   'Inherited same-net hole proximity accepted only for exact unchanged native DRC0 geometry pairs and rules',
                   'No new copper inherits a clearance/domain/spacing exception',
                   'All original r07 and four-path target copper retained exactly; all250 other donor chunks remain exact',
                   'One dive-return; one new throughvia plus one exact retained.6/.3throughvia; no repeated switches',
                   'Layer-specific graph uses only copper bodies and plated via joins, no plane-fill contacts',
                   'Fresh native combined no-loss/DRC/refill/pad-net/source-root/current/thermal/fault gates still required',
                   'Original r06+3/-0 does not establish gains on r07/four-path target; expected native outcomes remain OPEN']}
 destination.write_text(json.dumps(output,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'verdict':output['verdict'],'items':output['final_donor_copper_items'],
                   'inherited_pairs':len(inherited),'failing_items':bad,'contact_closure':graph},indent=1),flush=True)

if __name__=='__main__':main()
