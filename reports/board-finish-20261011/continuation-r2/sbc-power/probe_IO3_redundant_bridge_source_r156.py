"""Fresh exact IO3 source graph after withdrawing only the overlapping NEW bridge.

No proof for foreign contacts or native refill is inferred from this probe.
"""
from pathlib import Path
import sys,pickle,json,hashlib,copy
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'sbc-power'));sys.path.insert(0,str(H/'field-power'))
import guarded_declared_settings_projection_r58 as GP
import io3_contact_restore_r2 as Q
O=H/'sbc-power/IO3-overlapping-owned-bridge-withdrawal-source-probe-r156'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def graph(c):
 Q.NET='/IO_3V3';gs,parts,assign=Q.groups(c,return_details=True);root=next(i for i,xs in enumerate(gs) if any((q['ref'],q['pad'])==('R18001','2') for q in xs));keys={q['uuid'] for q in gs[root]};return gs,parts,assign,root,keys
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/safe-ROOT22-CORE1V2-composition-r148/unprojected-model.pkl';assert sha(mp)=='6cb9583d5a37a0e4041419da9672011dad6c52f8fd4a9178797d43d9278df7d1';g,h,b,z,_=pickle.loads(mp.read_bytes())
 removed='04d140c5-3a78-5a5f-96d3-fbe2978c8eee';q=next(q for q in z if q['uuid']==removed);assert q['net']=='/IO_3V3' and q['layer']=='In1.Cu'
 # Restore ONLY the independently documented root d5 precision tag; exact
 # coordinate/WKB identity is asserted rather than altering source geometry.
 prec=[]
 for zz in z:
  if zz['uuid']=='d5e1a664-0428-5fe4-aaa9-7887f79adfe7':
   for key in ('shape','zone_outline_shape'):
    if key in zz:
     before=zz[key].wkb;zz[key]=set_precision(zz[key],1e-6,mode='pointwise');assert zz[key].wkb==before;prec.append({'UUID':zz['uuid'],'role':key,'grid_mm':1e-6,'mode':'pointwise','WKB_unchanged_sha256':hashlib.sha256(before).hexdigest()})
 hs={**h,'zones':[q for q in h['zones'] if q['net']=='/IO_3V3']};print('IO3_R156_SCOPED_BASELINE_PROJECT',flush=True);before,_=GP.projected(g,hs,z);bgs,bparts,ba,br,bkeys=graph(before)
 remain=[q for q in z if q['uuid']!=removed];print('IO3_R156_SCOPED_WITHDRAWAL_PROJECT',flush=True);after,cuts=GP.projected(g,hs,remain);gs,parts,a,root,keys=graph(after)
 target=next(p for p in h['pads'] if (p['ref'],p['num'])==('R11049','1'));via=next(v for v in h['vias'] if v['uuid']=='4df659b6-9ab2-5de3-9644-896efcd79c7c') if any(v['uuid']=='4df659b6-9ab2-5de3-9644-896efcd79c7c' for v in h['vias']) else next(v for v in h['vias'] if v['uuid'].startswith('4df659b6'))
 newlookup={q['uuid']:i for i,xs in enumerate(gs) for q in xs};lost=sorted(bkeys-keys)
 (O/'source-cache.pkl').write_bytes(pickle.dumps({'before_groups':bgs,'before_parts':bparts,'before_assign':ba,'after_groups':gs,'after_parts':parts,'after_assign':a,'after_scoped_model':after},protocol=5))
 r={'verdict':'OWNED_BRIDGE_REDUNDANT_SOURCE_SCOPE_PASS_FULL_CONTACT_NATIVE_REQUIRED' if not lost and target['uuid'] in keys and via['uuid'] in keys else 'OWNED_BRIDGE_STILL_REQUIRED_REROUTE_NEEDED','parent_model_sha256':sha(mp),'withdrawn_owned_NEW_zone_UUID':removed,'source_ref_pin':['R18001','2'],'target_R11049_pad_UUID':target['uuid'],'target_source_rooted_without_bridge':target['uuid'] in keys,'via_record':via,'via_source_rooted_without_bridge':via['uuid'] in keys,'prior_source_keys_lost_without_bridge':lost,'before_source_key_count':len(bkeys),'after_source_key_count':len(keys),'source_rooted_named_pad_count':sum(not r['ref'].startswith('@') for r in gs[root]),'source_group':root,'target_group':newlookup.get(target['uuid']),'explicit_restored_precision_states':prec,'source_cache_sha256':sha(O/'source-cache.pkl'),'full_foreign_retained_contacts_reference_native_flash_current':'OPEN','board_written':False,'native_jobs':0}
 (O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('IO3_R156_SOURCE',r['verdict'],'lost',len(lost),'target',r['target_source_rooted_without_bridge'],'via',r['via_source_rooted_without_bridge'],sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
