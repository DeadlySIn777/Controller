"""Replace only one canonical In3 IO3 group; retain every other primitive exactly."""
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import restore_SAFE_generated_precision_states_r168 as PS
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as AT
import owned_native_pad_guards_r98 as AP
import SAFE_native_hole_mutual_guards_r159 as HM
O=H/'sbc-power/IO3-group6-wider-minimal-canonical-union-r196'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ds(s):return hashlib.sha256(s.wkb).hexdigest()
def rings(s):return [[[(int(round(x*1e6)),int(round(y*1e6))) for x,y in list(r.coords)[:-1]] for r in [p.exterior]+list(p.interiors)] for p in GP.p.hubs.components(s)]
def canonical(s):
 out=[]
 for rr in rings(set_precision(s,1e-6)):
  p=Polygon([(x/1e6,y/1e6) for x,y in rr[0]],[[(x/1e6,y/1e6) for x,y in r] for r in rr[1:]]);assert p.is_valid;out.append(p)
 return out[0] if len(out)==1 else MultiPolygon(out) if out else GeometryCollection()
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183/model.pkl';assert sha(mp)=='6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5'
 g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z)
 bp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';bg,bh,bb,bz,bc=pickle.loads(bp.read_bytes());assert g==bg and h==bh;PS.restore_bound_generated_precision_states(bb,bz)
 qf=H/'sbc-power/original-IO3-r172-positive-snapshot-8/proposed-zones.pkl';assert sha(qf)=='d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c'
 wf=H/'sbc-power/IO3-group6-wider-existing-port-r193/accepted-zones.pkl';assert sha(wf)=='01952e9a9374ac67da080769154bc828cfd6689bff207cb412d9a33d551e4362'
 old=next(q for q in z if(q['net'],q['layer'])==('/IO_3V3','In3.Cu'));base=next(q for q in bz if(q['net'],q['layer'])==('/IO_3V3','In3.Cu'))
 held=[q for q in pickle.loads(qf.read_bytes()) if q['layer']=='In3.Cu' and q['uuid']!='e1ca93bf-40e7-5ec0-8482-bcd115ce3838'];wide=pickle.loads(wf.read_bytes());assert len(held)==3 and len(wide)==1;members=[base]+held+wide
 for q in members:
  for role in ('shape','zone_outline_shape'):
   before=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==before
 uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/IO3-In3-group6-wider-r196/'+ '|'.join(sorted(q['uuid'] for q in members))))
 nq=copy.deepcopy(old);nq['uuid']=uid;nq['label']='IO3 In3 canonical union with >=.30 group6 branch';nq['constituent_proposal_UUIDs']=sorted({u for q in members for u in [q['uuid']]+q.get('constituent_proposal_UUIDs',[])})
 for role in ('shape','zone_outline_shape'):nq[role]=canonical(unary_union([q[role] for q in members]))
 nq,vl=GP.normalize_owned_via_guards(h,[nq]);nq,tl,_=AT.normalize_owned_track_guards(h,nq);nq,pl,_=AP.normalize_owned_pad_guards(h,nq);nq,hl=HM.native_pad_hole_guards(h,nq);nq=nq[0]
 allq=[nq if q['uuid']==old['uuid'] else copy.deepcopy(q) for q in z]
 assert len(allq)==36
 unchanged=[]
 for q in allq:
  if q['uuid']==uid:continue
  prior=next(a for a in z if a['uuid']==q['uuid']);assert q['shape'].wkb==prior['shape'].wkb and q['zone_outline_shape'].wkb==prior['zone_outline_shape'].wkb
  unchanged.append({'UUID':q['uuid'],'physical_sha256':ds(q['shape']),'outline_sha256':ds(q['zone_outline_shape'])})
 precision=[]
 for q in allq:
  for role in ('shape','zone_outline_shape'):
   before=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==before
   precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':ds(q[role])})
 nq['integer_nm_physical_rings']=rings(nq['shape']);nq['integer_nm_native_outline_rings']=rings(nq['zone_outline_shape'])
 ledger={'only_owned_canonical_replacement':{'old_UUID':old['uuid'],'new_UUID':uid,'raw_net':'/IO_3V3','layer':'In3.Cu','withdraw_previous_unadopted_branch_UUID':'e1ca93bf-40e7-5ec0-8482-bcd115ce3838','new_branch_UUID':wide[0]['uuid'],'roles':{}},'exact35_unchanged_group_rows':unchanged,'via_guard':vl,'track_guard':tl,'pad_guard':pl,'hole_guard':hl,'member_UUIDs':[q['uuid'] for q in members]}
 for role in ('shape','zone_outline_shape'):
  af=O/(old['uuid']+'.'+role+'.old.wkb');nf=O/(uid+'.'+role+'.new.wkb');af.write_bytes(old[role].wkb);nf.write_bytes(nq[role].wkb)
  ledger['only_owned_canonical_replacement']['roles'][role]={'old_file':str(af.resolve()),'old_sha256':sha(af),'new_file':str(nf.resolve()),'new_sha256':sha(nf),'removed_mm2':old[role].difference(nq[role]).area,'added_mm2':nq[role].difference(old[role]).area}
 lf=O/'one-group-wider-replacement-ledger.json';lf.write_text(json.dumps(ledger,indent=1)+'\n')
 b=copy.deepcopy(b);b.update({'generated_precision_state_ledger':precision,'restored_generated_grid_UUIDs':[q['uuid'] for q in allq],'IO3_group6_wider_replacement_ledger_file':str(lf.resolve()),'IO3_group6_wider_replacement_ledger_sha256':sha(lf),'IO3_group6_wider_constructor_receipt_file':str((wf.parent/'receipt.json').resolve()),'IO3_group6_wider_constructor_receipt_sha256':sha(wf.parent/'receipt.json'),'IO3_all_593_source_contacts_after_wider_union':'REQUIRED','host_all_supply_rooted':False})
 candidate,cuts=GP.projected(g,h,allq);mf=O/'model.pkl';mf.write_bytes(pickle.dumps((g,h,b,allq,candidate),protocol=5))
 (O/'receipt.json').write_text(json.dumps({'verdict':'ONE_IO3_CANONICAL_WIDER_BRANCH_REPLACEMENT_FROZEN_FRESH_FULL_GATES_REQUIRED','model_sha256':sha(mf),'parent_R183_sha256':sha(mp),'changed_owned_group_count':1,'unchanged_owned_group_count':35,'ledger_sha256':sha(lf),'old_fill_retreats':cuts,'old_original_discrete_source_definition_changes':0,'no_area_waiver':True,'host_all_supply_rooted':False,'new_feed_current_return_native_still_open':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)},indent=1)+'\n')
 print('R196_COMPLETE',sha(mf),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
