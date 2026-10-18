"""Prove actual own-T1 return and ordinary off-pad CDONE producer sites."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from verify_source import parse,children,child,atom
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
OUT=H/'FPGA-CDONE-own-T1-native-ground-dogbone-and-ordinary-offpad-port-screen-r27'
NET='/fpga_core/FPGA_CDONE';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,w=None):
  p=Path(p);v=sha(p);assert w is None or w==v;pins[str(p.resolve())]=v;return p
 rp=pin(H/'FPGA-CDONE-actual-native-courtyard-current-anchor-return-census-r24/receipt.json');r=json.loads(rp.read_bytes());cf=pin(r['cache_file'],r['cache_SHA256']);d=pickle.loads(cf.read_bytes());c=d['full_before'];local=d['local_current'];producer=d['producer'];court=d['courtyard'];refs=d['source_refs'];src=pin(d['current_native_source'],'7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');raw=src.read_bytes();native=K.C.inventory(raw)[3];fpuid='7030f6e9-2789-4c89-8505-1134463a5736';fp=parse(native[fpuid].decode());fpat=child(fp,'at');origin=[float(x)for x in fpat[1:3]];assert len(fpat)<4 or float(fpat[3])==0;circle={}
 for p in children(fp,'pad'):
  if p[2]=='smd'and p[3]=='circle':
   at=child(p,'at');size=child(p,'size');assert float(size[1])==float(size[2]);circle[atom(p,'uuid')]={'at':[origin[0]+float(at[1]),origin[1]+float(at[2])],'radius':float(size[1])/2}
 ret=next(v for v in local['vias']if v['uuid']=='b1e1485b-fbb0-48dd-a58a-2262fbd55ce3');pad=next(p for p in local['pads']if p['ref']=='U1001'and str(p['num'])=='T1');assert K.L.norm(pad['net'])==LG and K.L.norm(ret['net'])==LG;pt=[pad['x'],pad['y']];vt=[ret['x'],ret['y']];stub=[t for t in local['tracks']if t['layer']=='F.Cu'and K.L.norm(t['net'])==LG and(min(math.dist(t['a'],pt)+math.dist(t['b'],vt),math.dist(t['b'],pt)+math.dist(t['a'],vt))<=.000004)];assert len(stub)==1;stub=stub[0];assert stub['uuid']in native;parsed=K.A.G.parse(stub['uuid'],native[stub['uuid']],{});assert parsed['net']==LG and parsed['w']==stub['w'];ann=Point(vt).buffer(ret['d']/2,quad_segs=128).difference(Point(vt).buffer(ret['drill']/2,quad_segs=128));pshape=unary_union(K.L.poly(pad['layers']['F.Cu']));sbody=K.L.body(stub);a=sbody.intersection(pshape);b=sbody.intersection(ann);sourcekeys=K.keys(d['ground_SOURCE']);assert not a.is_empty and a.area>0 and not b.is_empty and b.area>0 and all(('via',ret['uuid'],ly)in sourcekeys for ly in('In1.Cu','In4.Cu'))and all(ly in ret['flashed']for ly in('In1.Cu','In4.Cu'));own={'same_part':'U1001','real_ground_ball':'T1','ground_pad_UUID':pad['uuid'],'return_via':ret,'exact_owned_F_dogbone_track':stub,'native_owned_F_stub_SHA256':hashlib.sha256(native[stub['uuid']]).hexdigest(),'finite_pad_stub_contact':info(a),'finite_stub_via_annulus_contact':info(b),'actual_full_before_SOURCE_In1_In4_annular_area_mm2':{ly:ann.intersection(refs[ly]).area for ly in refs},'D4_samepart_ownership_proven_by_retained_native_dogbone':True};put('actual-T1-private-native-F-dogbone-return-ownership-and-SOURCE-annuli.json',own)
 rec,trees=K.F.build(local);dom=c['domains_normalized'];gap=lambda n:.15 if dom[K.L.norm(n)]==dom[NET]else .6;holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in local['vias']]+[(p['uuid'],s)for p in local['pads']for s in K.L.poly(p.get('hole')or[])];smd=[(p,ly,s)for p in local['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)];reservation,exempt=K.A.reservations();proposals=[];at0=[producer['x']-.4,producer['y']-.4];points=[at0]
 for dx in(-1.2,-1.0,-.8,-.65,-.4,.4):
  for dy in(-.8,-.65,-.4,0,.4):
   at=[round(producer['x']+dx,6),round(producer['y']+dy,6)]
   if all(math.dist(at,q)>.01 for q in points):points.append(at)
 for at in points:
  centre=Point(at);sgdist=math.dist(at,vt);errs=[];checks=[]
  if not court.covers(centre):continue
  if sgdist>1.2:continue
  for ly in K.LAYERS:
   for i in trees[ly].query(centre.buffer(1),predicate='intersects'):
    row=rec[ly][int(i)]
    if K.L.norm(row['net'])==NET:continue
    if row['kind']=='via':v=row['source'];distance=centre.distance(Point(v['x'],v['y']))-.25-v['d']/2
    elif row['kind']=='track':t=row['source'];distance=centre.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
    elif row['kind']=='pad'and row['uuid']in circle:z=circle[row['uuid']];distance=centre.distance(Point(z['at']))-.25-z['radius']
    else:distance=centre.distance(row['shape'])-.25-(.005 if row['kind']=='pad'else 0)
    req=gap(row['net'])+.025;check={'kind':'new_ordinary_via_true_Cu','other_UUID':row['uuid'],'layer':ly,'gap_mm':distance,'required_mm':req};checks.append(check)
    if distance<req:errs.append(check)
  for p,ly,s in smd:
   distance=centre.distance(Point(circle[p['uuid']]['at']))-circle[p['uuid']]['radius']-.1 if p['uuid']in circle else centre.distance(s)-.1-.005
   if distance<.275:errs.append({'kind':'ALL_SMD_ordinary_drill_including_OWN_ball','other_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'gap_mm':distance,'required_mm':.275})
  for uid,s in holes:
   distance=centre.distance(s)-.1
   if distance<.275:errs.append({'kind':'all_existing_physical_holes','other_UUID':uid,'gap_mm':distance,'required_mm':.275})
  # D4 uses true same/cross-domain DRC clearance for pitch in the real FPGA
  # courtyard; the generic 0.8 mm centre rule is explicitly inapplicable.
  for rule in c['rule_areas']:
   if rule.get('no_vias')and any(centre.distance(s)-.25<.025 for s in K.L.poly(rule['outline'])):errs.append({'kind':'native_no_via_rule','UUID':rule['uuid']})
  for rule in reservation['keepouts']:
   if NET not in exempt.get(rule['name'],set())and any(centre.distance(s)-.25<.025 for s in K.L.poly(rule['outline'])):errs.append({'kind':'registered_keepout','name':rule['name']})
  axis=LineString([[producer['x'],producer['y']],at]);body=K.Z.bounded_buffer(axis,.1);owncap=centre.buffer(.525,quad_segs=256);refgap=body.difference(owncap).difference(refs['In1.Cu'])
  if not refgap.is_empty:errs.append({'kind':'new_F_whole_body_actual_SOURCE_In1_reference','raw_gap':info(refgap)})
  for i in trees['F.Cu'].query(body.buffer(.8),predicate='intersects'):
   row=rec['F.Cu'][int(i)]
   if K.L.norm(row['net'])==NET:continue
   if row['kind']=='via':v=row['source'];distance=axis.distance(Point(v['x'],v['y']))-.1-v['d']/2
   elif row['kind']=='track':t=row['source'];distance=axis.distance(LineString([t['a'],t['b']]))-.1-t['w']/2
   elif row['kind']=='pad'and row['uuid']in circle:z=circle[row['uuid']];distance=axis.distance(Point(z['at']))-.1-z['radius']
   else:distance=axis.distance(row['shape'])-.1-(.005 if row['kind']=='pad'else 0)
   req=gap(row['net'])+.025
   if distance<req:errs.append({'kind':'new_F_escape_true_Cu','other_UUID':row['uuid'],'gap_mm':distance,'required_mm':req})
  proposals.append({'signal_at_mm':at,'F_escape_points_mm':[[producer['x'],producer['y']],at],'F_width_mm':.2,'D4_source_T1_return_UUID':ret['uuid'],'signal_return_distance_mm':sgdist,'ordinary_via_diameter_drill_mm':[.5,.2],'new_via_on_SMD_land_or_new_VIPPO_location':False,'D4_generic_centre_pitch_rule_replaced_by_actual_DRC_only_in_real_courtyard':True,'errors':errs,'checked_Cu_pairs':checks,'pass':not errs})
 put('ordinary-offpad-producer-via-and-F-escape-discrete-source-screens.json',proposals);accepted=[p for p in proposals if p['pass']];cache=OUT/'owned-T1-source-return-and-ordinary-CDONE-ports-screen.pkl';cache.write_bytes(pickle.dumps({'base_census':d,'own_T1_return':own,'accepted':accepted,'all_trials':proposals,'actual_FPGA_circle_pad_math':circle},protocol=5));result={'verdict':'OWN_T1_GROUND_SOURCE_AND_ORDINARY_OFFPAD_CDONE_SITE_SCREEN_PASS_FULL_ANTIPAD_BCHANNEL_NATIVE_OPEN'if accepted else'OWN_T1_GROUND_SOURCE_PROVEN_ORDINARY_OFFPAD_SCREEN_BOUNDED_INCOMPLETE','T1_owned_native_ground_stub_UUID':stub['uuid'],'screened_sites':len(proposals),'accepted_sites':len(accepted),'first_accepted':{k:v for k,v in accepted[0].items()if k not in('checked_Cu_pairs','errors')}if accepted else None,'no_new_VIPPO_or_own_land_exception_location':True,'current_foreign_native_role_intent_and_normal_antipads_B_source_oldcontacts_refs_necks_masks':'OPEN before any qualified candidate','cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','T1_owned_native_ground_stub_UUID','screened_sites','accepted_sites','first_accepted','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
