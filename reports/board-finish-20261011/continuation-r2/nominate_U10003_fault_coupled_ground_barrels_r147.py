"""Exact ordinary barrel screen after restoring the frozen fault on In2.

This is only nomination; actual new reference strips, old native fill cuts,
every source/contact/reference/current and native gate remain independent.
"""
import hashlib,json,pickle,sys,re,math,uuid
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
OUT=H/'U10003-fault-coupled-ordinary-ground-barrel-nominees-r147'
NET='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,full=pickle.loads(mp.read_bytes());r=json.loads((H/'U10003-unqualified-physical-fault-detour-r130/receipt.json').read_bytes());ids=set(r['removed_exact_old_track_UUIDs']);hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in ids]+r['repair']['tracks']};records,trees=F.build({**hard,'zones':[]});groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups[NET]if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));refs={l:unary_union([q['shape']for q in root if q['layer']==l and q['kind']=='fill'])for l in('In1.Cu','In4.Cu')};foot=next(f for f in h['footprints']if f['ref']=='U10003');court=unary_union([s for rs in foot['courtyard'].values()for s in C.poly(rs)])
 reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];dru=(reserved/'reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n)for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 sites=[(216.05,142.9945),(218.8,141.45),(218.35,141.25),(219.05,141.65),(213.45,141.85),(213.0,141.75),(213.85,141.75),(216.35,143.0),(216.05,142.75)]
 for v in r['repair']['existing_native_barrels']:
  for radius in(.8,1.0,1.2):
   for angle in range(0,360,45):sites.append((round(v['x']+radius*math.cos(math.radians(angle)),6),round(v['y']+radius*math.sin(math.radians(angle)),6)))
 rows=[];accepted=[]
 for x,y in dict.fromkeys(sites):
  pt=Point(x,y);disk=pt.buffer(.25,quad_segs=256);ann=disk.difference(pt.buffer(.1,quad_segs=256));bad=[]
  for l in h['copper_layers']:
   for j in trees[l].query(disk.buffer(.627),predicate='intersects'):
    q=records[l][int(j)]
    if C.norm(q['net'])==NET:continue
    req=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6)+.025+.000020;actual=disk.distance(q['shape'])
    if actual<req:bad.append({'kind':q['kind'],'UUID':q['uuid'],'net':q['net'],'layer':l,'actual':actual,'required':req})
  for q in z:
   if C.norm(q['net'])==NET:continue
   req=max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6,float(q.get('clearance_mm',.15)))+.025+.000020;actual=disk.distance(q['shape'])
   if actual<req:bad.append({'kind':'OWNED_ROLE','UUID':q['uuid'],'net':q['net'],'layer':q['layer'],'actual':actual,'required':req})
  for p in h['pads']:
   for sh in C.poly(p.get('hole')or[]):
    actual=pt.distance(sh)-.1
    if actual<.275+.000020:bad.append({'kind':'PAD_HOLE','UUID':p['uuid'],'actual':actual})
   if p['smd']:
    for l,rs in p['layers'].items():
     actual=pt.distance(unary_union(C.poly(rs)))-.1
     if actual<.275+.000020:bad.append({'kind':'SMD_HOLE','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':l,'actual':actual})
  for v in h['vias']:
   actual=pt.distance(Point(v['x'],v['y']))-(.2+v['drill'])/2
   if actual<.275+.000020:bad.append({'kind':'VIA_HOLE_PITCH','UUID':v['uuid'],'actual':actual})
  for a in h['rule_areas']:
   if a['no_vias']and any(disk.intersects(s.buffer(.025))for s in C.poly(a['outline'])):bad.append({'kind':'NATIVE_NO_VIA','UUID':a['uuid'],'name':a['name']})
  for a in areas:
   if NET not in exceptions.get(a['name'],set())and any(disk.intersects(s.buffer(.025))for s in C.poly(a['outline'])):bad.append({'kind':'ROUTER_RESERVATION','name':a['name']})
  if disk.distance(court)<.025:bad.append({'kind':'LITERAL_OWN_COURTYARD_PLUS25UM'})
  row={'site_mm':[x,y],'ordinary_diameter_drill_mm':[.5,.2],'actual_prior_FG_source_annuli_mm2':{l:ann.intersection(sh).area for l,sh in refs.items()},'guard_failures':bad};rows.append(row)
  if not bad:accepted.append(row);print('R147_SITE',json.dumps(row),flush=True)
 (OUT/'rows.json').write_text(json.dumps(rows,indent=1)+'\n');receipt={'verdict':'COUPLED_FAULT_RESTORE_ORDINARY_GROUND_BARREL_NOMINATION_ONLY_ALL_FILLED_SOURCE_CURRENT_NATIVE_OPEN','model_sha256':sha(mp),'exact_three_fault_deletes':sorted(ids),'frozen_two_fault_restoration_tracks':[t['uuid']for t in r['repair']['tracks']],'sites_examined':len(rows),'sites_true_discrete_owned_hole_SMD_courtyard_native_and217_reservation_pass':accepted,'rows_sha256':sha(OUT/'rows.json'),'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R147',len(accepted),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
