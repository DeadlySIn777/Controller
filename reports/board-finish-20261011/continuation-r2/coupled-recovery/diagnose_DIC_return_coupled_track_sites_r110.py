"""Nominate exact small Cu ownership for a DIC terminal return site.

Immutable pads/holes/native barrels/power planes/rules stay hard. Only
ordinary sampled sites blocked exclusively by existing tracks can nominate
a later fully audited coupled reroute. No track is removed here.
"""
import sys,json,pickle,time,math,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
from shapely.geometry import Point
C=A.C;GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def main():
 started=time.monotonic();out=HERE/'DIC-return-coupled-track-site-diagnostic-r110.json';assert not out.exists();A.read(__file__);rp=HERE/'fresh-partial-annular-return-nomination-r108.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='dcd02247720ccd0c1194b1b691c506e252cefd853917876d6b2cf010df4457a9';raw=A.read(r['saved_geometry_file']);assert C.sha(raw)==r['saved_geometry_sha256'];cache=pickle.loads(raw);cur=cache['current'];h=cur['h'];g=cur['after'];domains=h['domains_normalized'];policy={L.norm(n):v for n,v in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();smd=[(p['uuid'],p['ref'],p['num'],q) for p in h['pads'] if p['smd'] for layer,rs in p['layers'].items() if layer in('F.Cu','B.Cu') for q in L.poly(rs)];holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h['vias']]+[(p['uuid'],q) for p in h['pads'] for q in L.poly(p.get('hole') or [])];planes=cache['planes'];marker=[q['signal_or_handoff_at_mm'] for q in r['queries'] if q['kind']=='DIC_CS_F_B_target_pair'];stats=collections.Counter();nominees=[];seen=set();tracks={q['uuid']:q for q in h['tracks']}
 for signal in marker:
  for radius in(.83,.875,.925,.975,1.):
   for k in range(144):
    a=2*math.pi*k/144;at=[round(signal[0]+radius*math.cos(a),6),round(signal[1]+radius*math.sin(a),6)];key=tuple(at)
    if key in seen:continue
    seen.add(key);point=Point(at);ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in planes.items()}
    if not all(x>.004 for x in contacts.values()):stats['finite_rooted_source_annulus_failure']+=1;continue
    if any(point.distance(sh)<.380 for u,ref,pin,sh in smd):stats['immutable_SMD_aperture_failure']+=1;continue
    if any(point.distance(sh)<.380 for u,sh in holes):stats['immutable_drill_edge_failure']+=1;continue
    if any(point.distance(Point(v['x'],v['y']))<.815 for v in h['vias']):stats['immutable_old_via_pitch_failure']+=1;continue
    blockers=[];hard=[]
    for layer in LAYERS:
     for i in trees[layer].query(point.buffer(.95),predicate='intersects'):
      q=rec[layer][int(i)];n=L.norm(q['net'])
      if n==GND:continue
      req=.25+(.15 if domains.get(n)==domains[GND] else .6)+.030;distance=point.distance(q['shape'])
      if distance>=req:continue
      row={'uuid':q['uuid'],'kind':q['kind'],'layer':layer,'raw_net':q['net'],'distance_center_to_Cu_mm':distance,'required_center_to_Cu_mm':req}
      if q['kind']=='track' or q['uuid'] in tracks:blockers.append(row)
      else:hard.append(row)
     for z in cur['zones']:
      n=L.norm(z['net'])
      if z['layer']!=layer or n==GND:continue
      req=.25+max(float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[GND] else .6)+.030
      if point.distance(z['shape'])<req:hard.append({'kind':'owned_power_plane_hard','UUID':z['uuid'],'layer':layer,'raw_net':z['net']})
     for z in g['zones']:
      n=L.norm(z['net'])
      if n==GND or domains.get(n)==domains[GND]:continue
      req=.25+max(float(z.get('clearance_mm',.15)),.6)+.030
      if any(point.distance(sh)<req for sh in L.poly(z['fills'].get(layer,[]))):hard.append({'kind':'cross_domain_native_fill_hard','UUID':z['uuid'],'layer':layer,'raw_net':z['net']})
     for q in h['rule_areas']:
      if layer in q['layers'] and q.get('no_vias') and any(point.distance(sh)<.275 for sh in L.poly(q['outline'])):hard.append({'kind':'native_no_vias','UUID':q['uuid']})
     for q in reserve['keepouts']:
      if layer in q['layers'] and GND not in exempt.get(q['name'],set()) and any(point.distance(sh)<.275 for sh in L.poly(q['outline'])):hard.append({'kind':'reservation','UUID':q['name']})
    if hard:stats['immutable_pad_barrel_rule_or_power_failure']+=1;continue
    ids=sorted({q['uuid'] for q in blockers});stats['track_only_ordinary_sites']+=1;nominees.append({'signal_via_at_mm':signal,'return_at_mm':at,'pair_distance_mm':math.dist(at,signal),'source_annular_contacts_mm2':contacts,'exact_track_blockers':blockers,'unique_track_count':len(ids),'track_deltas_to_construct':[{'uuid':u,'raw_net':tracks[u]['net'],'layer':tracks[u]['layer'],'a':tracks[u]['a'],'b':tracks[u]['b'],'w':tracks[u]['w'],'m':tracks[u].get('m'),'controlled_policy':policy.get(L.norm(tracks[u]['net']))} for u in ids]})
 nominees.sort(key=lambda q:(q['unique_track_count'],len({x['raw_net'] for x in q['exact_track_blockers']}),q['pair_distance_mm']));report={'verdict':'DIC_REAL_RETURN_MINIMAL_COUPLED_TRACK_OWNERSHIP_NOMINATED' if nominees else'DIC_TERMINAL_RETURN_SAMPLED_PHYSICAL_SITE_BLOCKERS_ACCOUNTED','R108_receipt_sha256':C.sha(A.read(rp)),'current_source_model_sha256':r['source_model_sha256'],'sampled_unique_sites':len(seen),'rejection_counts':dict(stats),'best_nominations':nominees[:16],'all_track_only_sites_count':len(nominees),'any_items_removed':0,'old_source_pads_drills_barrels_power_native_rules_hard':True,'new_coupled_full_reference_contacts_current_r06_r07_native_SI_gates':'OPEN','no_global_impossibility_claim':True,'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'counts':dict(stats),'best':nominees[:6]}),flush=True)
if __name__=='__main__':main()
