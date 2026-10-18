"""Exact rational, dimension-complete classification of six R562 witnesses.

No shape, precision, source or threshold changes. Every literal before/after
and individual cutter/reserve polygon is bound; no GEOS union is used for
membership. The old raw Boolean FAIL remains independently preserved.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time
from fractions import Fraction as Q
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_FIELD5_R453_literal_rational_line_membership_r189 as X
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely import from_wkb
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DIC-R562-literal-subtraction-scope-arrangement-r564'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def edges(ps):return[(a,b)for rings in ps for ring in rings for a,b in zip(ring,ring[1:])if a!=b]
def bounds(ps):
 c=[x for rings in ps for ring in rings for x in ring]
 return tuple(min(x[k]for x in c)for k in(0,1)),tuple(max(x[k]for x in c)for k in(0,1))
def disjoint(lo,hi,ll,hh):return any(hi[k]<ll[k]or lo[k]>hh[k]for k in(0,1))
def boxedge(a,b,lo,hi):return not disjoint(tuple(min(a[k],b[k])for k in(0,1)),tuple(max(a[k],b[k])for k in(0,1)),lo,hi)
def parts(w):
 if w.is_empty:return[]
 if w.geom_type in('Polygon','LineString','Point'):return[w]
 return [p for x in w.geoms for p in parts(x)]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();inputs={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;(inputs.update({str(p.resolve()):v}));return p
 rp=pin(H/'DIC-policy-coupled-actual-current-independent-r562/receipt.json','ae47a082e0813041706a153fcfc6fc1f2c4e2de101f55e8580be3c1a104cb776');rr=json.loads(rp.read_bytes());assert not rr['strict_raw_old_reference_losses']and not rr['new_body_reference_errors'];raw=rr['raw_extra_negative_outside_scoped_cuts_or_declared_local_reserves'];assert len(raw)==6
 mp=pin(H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/exact-retired-NEW55ab-only-cache-restoration-INTERMEDIATE_NOT_ADOPTED.pkl','fe1e8dfb04083ffb2084f37da0702280a654011cc090f3bd7b4bc9de93e7af85');g,h,b,q,before=pickle.loads(mp.read_bytes());byzone={z['uuid']:z for z in before['zones']}
 lp=pin(H/'DIC-retired-cutter-policy-coupled-current-r556/incremental-immutable-current-native-filled-cut-ledger.json');ledger=json.loads(lp.read_bytes());lookup={(r['zone_UUID'],r['layer']):r for r in ledger};reports=[];bad=[];memo={}
 pin(Path(__file__));pin(Path(X.__file__))
 for ri,row in enumerate(raw):
  uid,ly,i=row['zone_UUID'],row['layer'],row['record'];auth=lookup[uid,ly];step=auth['immutable_per_record_proof']['per_original_record_operations'][i];assert step['record']==i;part=K.L.poly(byzone[uid]['fills'][ly])[i];assert hashlib.sha256(part.wkb).hexdigest()==step['before_WKB_sha256'];bf=OUT/(uid+'-'+ly+'-'+str(i)+'-exact-BEFORE.wkb');bf.write_bytes(part.wkb);pin(bf)
  af=pin(step['actual_final_record_file'],step['after_WKB_sha256']);wp=pin(row['file'],row['raw_extra_negative_not_in_any_new_primitive_or_local_gain_reserve']['WKB_SHA256']);w=from_wkb(wp.read_bytes());polys={'before':X.read_polys(part),'after':X.read_polys(from_wkb(af.read_bytes()))};authority=[]
  for ci,cut in enumerate(auth['cutters']):
   f=pin(cut['exact_cutter_file'],cut['exact_cutter_SHA256']);k='cut_'+str(ci);polys[k]=X.read_polys(from_wkb(f.read_bytes()));authority.append({'kind':'new_primitive','name':k,'file':str(f),'sha256':sha(f),'new_UUID':cut['new_UUID'],'analytic_radius_mm':cut['analytic_radius_mm']})
  for ci,res in enumerate(step['reserves']):
   f=pin(res['reserve_file'],res['reserve_sha256']);k='reserve_'+str(ci);polys[k]=X.read_polys(from_wkb(f.read_bytes()));authority.append({'kind':'explicit_local_negative_reserve','name':k,'file':str(f),'sha256':sha(f)})
  fingerprint=tuple(hashlib.sha256(repr(polys[k]).encode()).hexdigest()for k in polys)+(sha(wp),)
  if fingerprint in memo:
   old=memo[fingerprint];reports.append({'zone_UUID':uid,'layer':ly,'record':i,'exact_all_primitive_and_witness_identity_to_previously_classified_row':old,'literal_outside_scope_count':reports[old]['literal_outside_scope_count'],'closed_boundary_and_open_face_checks_reused_only_by_exact_identity':True});continue
  memo[fingerprint]=len(reports);componentreports=[];rowbad=[]
  for wi,component in enumerate(parts(w)):
   witnesspoly=X.read_polys(component)if component.geom_type=='Polygon'else[]
   wc=[x for rings in witnesspoly for ring in rings for x in ring]if witnesspoly else[X.point(x)for x in component.coords];lo=tuple(min(p[k]for p in wc)for k in(0,1));hi=tuple(max(p[k]for p in wc)for k in(0,1));local={};omitted=[]
   for name,pp in polys.items():
    kept=[]
    for pi,p in enumerate(pp):
     ll,hh=bounds([p])
     if disjoint(lo,hi,ll,hh):omitted.append({'primitive':name,'polygon':pi,'exact_envelope_disjoint':True})
     else:kept.append(p)
    local[name]=kept
   if witnesspoly:local['witness']=witnesspoly
   def onw(p):
    if witnesspoly:return X.location(p,witnesspoly)!='EXTERIOR'
    return any(X.cross(X.sub(bb,aa),X.sub(p,aa))==0 and all(min(aa[k],bb[k])<=p[k]<=max(aa[k],bb[k])for k in(0,1))for aa,bb in zip(wc,wc[1:])) if len(wc)>1 else p==wc[0]
   seen=set();counts={'boundary_vertices':0,'open_interval_midpoints':0,'adjacent_face_points':0};failure=[]
   def check(p,kind):
    if p in seen:return
    seen.add(p);counts[kind]+=1
    if not onw(p):return
    loc={k:X.location(p,v)for k,v in local.items()if k!='witness'};covered={k:v!='EXTERIOR'for k,v in loc.items()};lost=covered['before']and not covered['after']and not any(v for k,v in covered.items()if k.startswith(('cut_','reserve_')))
    if lost:failure.append({'kind':kind,'point_exact':[str(x)for x in p],'point_mm_approx':[float(x)for x in p],'locations':loc,'literal_before_AND_NOT_after_AND_NOT_individual_authority':True})
   sources=[e for ps in local.values()for e in edges(ps)if boxedge(*e,lo,hi)]
   if component.geom_type=='Polygon':work=edges(witnesspoly)+sources
   elif component.geom_type=='LineString':work=[(a,bb)for a,bb in zip(wc,wc[1:])if a!=bb]
   else:work=[];check(wc[0],'boundary_vertices')
   splitps={'all_local_boundaries':[[[a,bb,a]]for a,bb in sources]}
   for a,bb in work:
    ts=X.split_parameters(a,bb,splitps)
    for t in ts:check(X.along(a,bb,t),'boundary_vertices')
    for t,u in zip(ts,ts[1:]):
     if t==u:continue
     m=X.along(a,bb,(t+u)/2);check(m,'open_interval_midpoints')
     if not witnesspoly:continue
     delta=X.sub(bb,a);normal=(-delta[1],delta[0]);scale=max(abs(x)for x in normal)
     for sign in(-1,1):
      end=(m[0]+sign*normal[0]/scale/1000,m[1]+sign*normal[1]/scale/1000);crossings=X.split_parameters(m,end,splitps);positive=[x for x in crossings if x>0];s=min(positive)/2 if positive else Q(1);check(X.along(m,end,s),'adjacent_face_points')
   result={'witness_component':wi,'type':component.geom_type,'all_source_authority_parts_exhaustively_bound':True,'omitted_only_by_exact_disjoint_vertex_envelope':omitted,'counts':counts,'literal_outside_scope':failure};componentreports.append(result);rowbad+=failure
  r={'zone_UUID':uid,'layer':ly,'record':i,'witness_file':str(wp),'witness_SHA256':sha(wp),'before_file':str(bf),'before_SHA256':sha(bf),'after_file':str(af),'after_SHA256':sha(af),'individual_cut_and_reserve_authority':authority,'components':componentreports,'literal_outside_scope_count':len(rowbad)};reports.append(r);bad+=rowbad;print('R564_ROW',ri,uid,ly,i,'literal_outside',len(rowbad),'points',sum(sum(c['counts'].values())for c in componentreports),flush=True)
 result={'verdict':'EXACT_LITERAL_SCOPE_WITNESSES_ALL_COVERED_BY_AFTER_OR_DECLARED_NEGATIVE_AUTHORITY'if not bad else'EXACT_LITERAL_SCOPE_WITNESS_REAL_UNDECLARED_NEGATIVE_REQUIRES_REPAIR','raw_R562_six_GE0S_failures_retained':raw,'prior_R562_receipt_SHA256':sha(rp),'method':'Literal binary64 WKB interpreted as Fraction; every open witness edge interval split at exact individual before/after/cutter/reserve boundaries; all endpoints and midpoints classified; polygon components include both adjacent arrangement faces and zero-dimensional boundaries. No GEOS Boolean membership, rounding, area/length/tolerance waiver.','literal_outside_scope_count':len(bad),'reports':reports,'all_current_geometry_source_rules_profiles_precision_fills_unmodified':True,'inputs_SHA256':inputs,'full_native_SI_current_manufacturing_adoption_gate':'OPEN; inherited raw FAIL retained','adopted':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',result);print('R564_COMPLETE',sha(OUT/'receipt.json'),result['verdict'],len(bad),flush=True)
if __name__=='__main__':main()
