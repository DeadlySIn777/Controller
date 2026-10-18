"""Check conservative finite FAULT-preserving bent-stub nominations."""
from pathlib import Path
import sys,json,pickle,hashlib
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/C1024-manual-fault-detours-r144'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();cf=H/'sbc-power/C1024-local-native-bound-context-r141.json'
 c=json.loads(cf.read_bytes());via=Point(158.7,79.3);power='/CORE_1V2';fault='/fpga_core{slash}FPGA_INHIBIT_FAULT';removed='090b18c2-e356-4d70-94c8-ed7b92be4f98'
 starts=[[158.45,80.3],[158.35,80.35],[158.5,80.2]]
 fault_paths=[[[157.54,76.677],[158.,77.9],[159.8,78.5],[159.8,79.2],[159.4,79.9],[159.04,80.302]],[[157.54,76.677],[158.,77.9],[159.7,78.5],[159.7,79.2],[159.3,79.9],[159.04,80.302]],[[157.54,76.677],[158.1,78.1],[159.8,78.6],[159.8,79.3],[159.04,80.302]]]
 rows=[]
 for fp in fault_paths:
  for start in starts:
   pp=[start,[158.45,79.9],[158.7,79.6],[158.7,79.3]];fl=LineString(fp);pl=LineString(pp);errors=[]
   for raw,line,label in [(fault,fl,'FAULT'),(power,pl,'POWER')]:
    for p in c['pads']:
     if p['net']==raw:continue
     for s in C.poly(p['layers'].get('F.Cu',[])):
      d=line.distance(s)-.1
      if d<.17500002:errors.append([label,'pad',p['ref'],p['num'],d])
    for t in c['tracks_F']:
     if t['uuid']==removed or t['net']==raw:continue
     d=line.distance(LineString([t['a'],t['b']]))-.1-t['w']/2
     if d<.17500002:errors.append([label,'track',t['uuid'],t['net'],d])
    for v in c['vias_all_layers']:
     if v['net']==raw:continue
     pt=Point(v['x'],v['y'])
     d=line.distance(pt)-.1-v['d']/2 if 'F.Cu' in v['flashed'] else line.distance(pt)-.1-v['drill']/2
     req=.17500002 if 'F.Cu' in v['flashed'] else .27500002
     if d<req:errors.append([label,'via',v['uuid'],d])
    for rule in c['rules']:
     if rule.get('no_tracks') and 'F.Cu' in rule['layers']:
      if GP.bounded_buffer(line,.1).intersects(unary_union(C.poly(rule['outline']))):errors.append([label,'rule',rule['uuid']])
   if fl.distance(pl)-.2<.17500002:errors.append(['mutual_Cu',fl.distance(pl)-.2])
   # A true .25 mm reference halo on the outer FAULT route must avoid the
   # proposed positive all-layer annulus with the full .175 planning guard.
   if fl.distance(via)-.1-.25-.25<.17500002:errors.append(['FAULT_new_via_reference',fl.distance(via)-.6])
   rows.append({'FAULT_points_mm':fp,'POWER_points_mm':pp,'via_site_mm':list(via.coords[0]),'FAULT_length_mm':fl.length,'POWER_length_mm':pl.length,'errors':errors})
 (O/'receipt.json').write_text(json.dumps({'verdict':'FINITE_COUPLED_PATH_NOMINATIONS_ONLY','context_sha256':sha(cf),'rows':rows,'passing_rows':sum(not r['errors'] for r in rows),'exact_one_original_FAULT_track_deletion_nominated_only':removed,'native_source_shared_FAULT_contact_reference_oldfill_NEWplane_fullgeometry':'OPEN','board_written':False,'native_jobs':0},indent=1)+'\n')
 print('C1024_MANUAL_FAULT_PATHS',len(rows),'passing',sum(not r['errors'] for r in rows))
 for i,r in enumerate(rows):print(i,r['errors'][:6])
if __name__=='__main__':main()
